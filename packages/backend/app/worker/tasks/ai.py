import asyncio
from typing import Dict, List, Any, Optional
from celery import Task
from datetime import datetime
import json
import boto3
from botocore.exceptions import ClientError

from app.worker.celery_app import celery_app
from app.core.config import settings
from app.core.database import get_db
from app.models.email import ProcessedEmail
from app.models.task import Task as TaskModel
from app.models.history import AISupport
from app.crud.crud_email import crud_email
from app.crud.crud_task import crud_task
from app.schemas.task import TaskCreate
from app.services.openai_service import OpenAIService
from app.services.bedrock_service import BedrockService


class AIAnalysisTask(Task):
    """Base class for AI analysis tasks"""
    autoretry_for = (ClientError,)
    retry_kwargs = {'max_retries': 3, 'countdown': 30}
    retry_backoff = True


class BedrockClient:
    """AWS Bedrock client wrapper"""
    
    def __init__(self):
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
    
    async def invoke_model(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Invoke Bedrock model
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens in response
            
        Returns:
            Model response text
        """
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "top_p": 0.9
        })
        
        try:
            response = self.client.invoke_model(
                body=body,
                modelId=settings.BEDROCK_MODEL_ID,
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response["body"].read())
            return response_body["content"][0]["text"]
            
        except ClientError as e:
            raise Exception(f"Bedrock API error: {str(e)}")


@celery_app.task(bind=True, base=AIAnalysisTask, name="app.worker.tasks.ai.analyze_email_with_ai")
def analyze_email_with_ai(self, email_id: str, user_id: str) -> Dict[str, Any]:
    """
    Analyze email content using AWS Bedrock AI
    
    Args:
        email_id: Processed email ID
        user_id: User ID
        
    Returns:
        Dict with analysis results
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_analyze_email_async(email_id, user_id))
        return result
    finally:
        loop.close()

@celery_app.task(bind=True, base=AIAnalysisTask, name="app.worker.tasks.ai.analyze_email_thread")
def analyze_email_thread_for_tasks(
    self,
    thread_id: str,
    email_ids: List[str],
    user_id: str,
    primary_subject: str
) -> Dict[str, Any]:
    """
    Analyze email thread for task extraction
    スレッド単位でメールを分析し、タスクを抽出または更新
    
    Args:
        thread_id: Thread identifier
        email_ids: List of email IDs in the thread
        user_id: User ID
        primary_subject: Primary subject of the thread
        
    Returns:
        Dict with analysis results
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _analyze_email_thread_async(thread_id, email_ids, user_id, primary_subject)
        )
        return result
    except Exception as e:
        self.retry(countdown=60, max_retries=3, exc=e)


async def _analyze_email_async(email_id: str, user_id: str) -> Dict[str, Any]:
    """Async implementation of email analysis"""
    async with get_db() as db:
        # Get email
        email = await crud_email.get_processed_email(db, email_id=email_id)
        if not email:
            raise ValueError(f"Email {email_id} not found")
        
        # Prepare prompt
        prompt = f"""
        Analyze the following email and determine if it contains actionable tasks or important information that should be tracked as a task.
        
        Email Subject: {email.subject}
        From: {email.sender}
        Body: {email.body}
        
        Please respond in JSON format with the following structure:
        {{
            "is_task": boolean,
            "tasks": [
                {{
                    "title": "string",
                    "description": "string",
                    "priority": "low|medium|high",
                    "due_date": "ISO date string or null",
                    "tags": ["string"]
                }}
            ],
            "summary": "string",
            "sentiment": "positive|neutral|negative",
            "key_points": ["string"]
        }}
        """
        
        # Call Bedrock
        bedrock = BedrockClient()
        response = await bedrock.invoke_model(prompt)
        
        try:
            analysis = json.loads(response)
        except json.JSONDecodeError:
            # Fallback parsing
            analysis = {
                "is_task": False,
                "tasks": [],
                "summary": response[:200],
                "sentiment": "neutral",
                "key_points": []
            }
        
        # Update email
        await crud_email.update_email_analysis(
            db,
            email_id=email_id,
            is_task=analysis["is_task"],
            ai_summary=analysis["summary"],
            ai_analysis=json.dumps(analysis)
        )
        
        # Create tasks if identified
        created_tasks = []
        if analysis["is_task"] and analysis["tasks"]:
            for task_data in analysis["tasks"]:
                task = await crud_task.create_task(
                    db,
                    task=TaskCreate(
                        title=task_data["title"],
                        description=task_data["description"],
                        priority=task_data.get("priority", "medium"),
                        due_date=task_data.get("due_date"),
                        tags=task_data.get("tags", []),
                        user_id=user_id,
                        source_email_id=email_id
                    )
                )
                created_tasks.append(str(task.id))
        
        return {
            "email_id": email_id,
            "is_task": analysis["is_task"],
            "tasks_created": len(created_tasks),
            "task_ids": created_tasks,
            "summary": analysis["summary"],
            "timestamp": datetime.utcnow().isoformat()
        }

async def _analyze_email_thread_async(
    thread_id: str,
    email_ids: List[str],
    user_id: str,
    primary_subject: str
) -> Dict[str, Any]:
    """
    Async implementation of thread analysis
    スレッド内の全メールを分析して、タスクを作成または更新
    """
    async with get_db() as db:
        # Get all emails in the thread
        emails = []
        for email_id in email_ids:
            email = await crud_email.get_processed_email(db, email_id=email_id)
            if email:
                emails.append(email)
        
        if not emails:
            raise ValueError(f"No emails found for thread {thread_id}")
        
        # Check if task already exists for this thread
        existing_task = await crud_task.get_task_by_thread_id(db, thread_id=thread_id, user_id=user_id)
        
        # Prepare email content for analysis
        thread_content = []
        for email in sorted(emails, key=lambda x: x.email_date):
            thread_content.append({
                "date": email.email_date.isoformat(),
                "from": email.sender,
                "subject": email.subject,
                "body": email.body_preview or "",
                "is_reply": bool(email.in_reply_to)
            })
        
        # Initialize AI service
        ai_service = BedrockService() if settings.USE_BEDROCK else OpenAIService()
        
        # Prepare prompt based on whether task exists
        if existing_task:
            # Update existing task
            prompt = f"""
            既存のタスクに関連する新しいメールが届きました。
            タスクの進捗状況を更新する必要があるか判断してください。
            
            既存タスク:
            - タイトル: {existing_task.title}
            - 説明: {existing_task.description}
            - ステータス: {existing_task.status}
            - 優先度: {existing_task.priority}
            
            スレッドのメール:
            {json.dumps(thread_content, ensure_ascii=False, indent=2)}
            
            以下の形式でJSONを返してください:
            {{
                "action": "update" または "no_change",
                "updates": {{
                    "status": "新しいステータス (todo/progress/done)",
                    "progress_notes": "進捗に関するメモ",
                    "priority": "新しい優先度 (low/medium/high)"
                }},
                "reason": "更新理由または変更なしの理由"
            }}
            """
        else:
            # Create new task if needed
            prompt = f"""
            以下のメールスレッドを分析して、タスクを作成する必要があるか判断してください。
            
            スレッドのメール:
            {json.dumps(thread_content, ensure_ascii=False, indent=2)}
            
            以下の形式でJSONを返してください:
            {{
                "action": "create" または "skip",
                "task": {{
                    "title": "タスクのタイトル",
                    "description": "タスクの説明",
                    "priority": "low/medium/high",
                    "status": "todo",
                    "due_date": "期限 (YYYY-MM-DD形式、なければnull)"
                }},
                "reason": "タスク作成理由またはスキップ理由"
            }}
            """
        
        # Call AI service
        analysis_result = await ai_service.analyze_content(prompt)
        
        # Process AI response
        try:
            result = json.loads(analysis_result)
        except json.JSONDecodeError:
            result = {"action": "skip", "reason": "AI response parsing failed"}
        
        # Execute action based on AI decision
        if result.get("action") == "create" and not existing_task:
            # Create new task
            task_data = result.get("task", {})
            new_task = await crud_task.create(
                db,
                obj_in={
                    "title": task_data.get("title", primary_subject),
                    "description": task_data.get("description", ""),
                    "status": task_data.get("status", "todo"),
                    "priority": task_data.get("priority", "medium"),
                    "due_date": task_data.get("due_date"),
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "source_email_id": emails[0].id,
                    "created_by": "ai",
                    "email_summary": f"スレッド内のメール {len(emails)} 件"
                }
            )
            
            # Mark emails as task-related
            for email in emails:
                await crud_email.update(db, db_obj=email, obj_in={"is_task": True})
            
            return {
                "action": "created",
                "task_id": str(new_task.id),
                "thread_id": thread_id,
                "email_count": len(emails)
            }
            
        elif result.get("action") == "update" and existing_task:
            # Update existing task
            updates = result.get("updates", {})
            if updates:
                await crud_task.update(
                    db,
                    db_obj=existing_task,
                    obj_in={
                        **updates,
                        "updated_by": "ai",
                        "updated_at": datetime.utcnow()
                    }
                )
            
            return {
                "action": "updated",
                "task_id": str(existing_task.id),
                "thread_id": thread_id,
                "updates": updates
            }
        
        return {
            "action": "skipped",
            "thread_id": thread_id,
            "reason": result.get("reason", "No action needed")
        }


@celery_app.task(bind=True, base=AIAnalysisTask, name="app.worker.tasks.ai.generate_task_suggestions")
def generate_task_suggestions(self, task_id: str, context: str) -> Dict[str, Any]:
    """
    Generate AI suggestions for a task
    
    Args:
        task_id: Task ID
        context: Additional context for suggestions
        
    Returns:
        Dict with suggestions
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_generate_suggestions_async(task_id, context))
        return result
    finally:
        loop.close()


async def _generate_suggestions_async(task_id: str, context: str) -> Dict[str, Any]:
    """Async implementation of task suggestions"""
    async with get_db() as db:
        # Get task
        task = await crud_task.get_task(db, task_id=task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Prepare prompt
        prompt = f"""
        Provide actionable suggestions for the following task:
        
        Task: {task.title}
        Description: {task.description}
        Priority: {task.priority}
        Current Status: {task.status}
        Additional Context: {context}
        
        Please provide:
        1. Step-by-step action plan
        2. Potential blockers and solutions
        3. Resource recommendations
        4. Time estimation
        5. Similar task references (if any)
        
        Format the response as structured JSON.
        """
        
        # Call Bedrock
        bedrock = BedrockClient()
        response = await bedrock.invoke_model(prompt, max_tokens=3000)
        
        try:
            suggestions = json.loads(response)
        except json.JSONDecodeError:
            suggestions = {
                "action_plan": [response[:500]],
                "blockers": [],
                "resources": [],
                "time_estimate": "Unknown",
                "references": []
            }
        
        # Save AI support record
        ai_support = await crud_task.create_ai_support(
            db,
            task_id=task_id,
            support_type="task_suggestions",
            ai_response=json.dumps(suggestions),
            metadata={"context": context}
        )
        
        return {
            "task_id": task_id,
            "ai_support_id": str(ai_support.id),
            "suggestions": suggestions,
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=AIAnalysisTask, name="app.worker.tasks.ai.summarize_thread")
def summarize_email_thread(self, email_ids: List[str]) -> Dict[str, Any]:
    """
    Summarize an email thread
    
    Args:
        email_ids: List of email IDs in the thread
        
    Returns:
        Dict with thread summary
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_summarize_thread_async(email_ids))
        return result
    finally:
        loop.close()


async def _summarize_thread_async(email_ids: List[str]) -> Dict[str, Any]:
    """Async implementation of thread summarization"""
    async with get_db() as db:
        # Get all emails in thread
        emails = []
        for email_id in email_ids:
            email = await crud_email.get_processed_email(db, email_id=email_id)
            if email:
                emails.append(email)
        
        if not emails:
            raise ValueError("No emails found in thread")
        
        # Sort by date
        emails.sort(key=lambda x: x.received_at)
        
        # Prepare thread content
        thread_content = "\n\n".join([
            f"From: {email.sender}\nDate: {email.received_at}\nSubject: {email.subject}\n{email.body}"
            for email in emails
        ])
        
        # Prepare prompt
        prompt = f"""
        Summarize the following email thread:
        
        {thread_content}
        
        Provide:
        1. Executive summary (2-3 sentences)
        2. Key decisions made
        3. Action items identified
        4. Participants and their roles
        5. Next steps
        
        Format as JSON.
        """
        
        # Call Bedrock
        bedrock = BedrockClient()
        response = await bedrock.invoke_model(prompt, max_tokens=2000)
        
        try:
            summary = json.loads(response)
        except json.JSONDecodeError:
            summary = {
                "executive_summary": response[:300],
                "decisions": [],
                "action_items": [],
                "participants": [],
                "next_steps": []
            }
        
        return {
            "thread_size": len(emails),
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }