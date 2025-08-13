import asyncio
from typing import Dict, List, Any
from celery import Task
from datetime import datetime
import json

from app.worker.celery_app import celery_app
from app.services.email_service import EmailService
from app.services.oauth_service import OAuthService
from app.core.database import get_db
from app.models.email import ProcessedEmail, EmailAccount
from app.models.task import Task as TaskModel
from app.crud.crud_email import crud_email
from app.crud.crud_task import crud_task
from app.worker.tasks.ai import analyze_email_thread_for_tasks


class EmailSyncTask(Task):
    """Base class for email sync tasks with retry logic"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True


@celery_app.task(bind=True, base=EmailSyncTask, name="app.worker.tasks.email.sync_emails")
def sync_emails(self, user_id: str, account_id: str) -> Dict[str, Any]:
    """
    Sync emails from Gmail/Outlook for a specific account
    
    Args:
        user_id: User ID
        account_id: Email account ID
        
    Returns:
        Dict with sync results
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_sync_emails_async(user_id, account_id, self.request.id))
        return result
    finally:
        loop.close()


async def _sync_emails_async(user_id: str, account_id: str, task_id: str) -> Dict[str, Any]:
    """Async implementation of email sync - 個別メール処理方式"""
    async with get_db() as db:
        # Get email account
        account = await crud_email.get_email_account(db, account_id=account_id, user_id=user_id)
        if not account:
            raise ValueError(f"Email account {account_id} not found")
        
        # Initialize services
        oauth_service = OAuthService()
        email_service = EmailService()
        
        # Get access token
        token_data = await oauth_service.refresh_token(account.refresh_token, account.provider)
        
        # Sync emails
        if account.provider == "google":
            emails = await email_service.sync_gmail(
                access_token=token_data["access_token"],
                last_sync_token=account.last_sync_token
            )
        elif account.provider == "microsoft":
            emails = await email_service.sync_outlook(
                access_token=token_data["access_token"],
                last_sync_token=account.last_sync_token
            )
        else:
            raise ValueError(f"Unsupported provider: {account.provider}")
        
        # Process emails individually and group by thread
        processed_count = 0
        threads = {}  # thread_id -> list of emails
        
        for email_data in emails["messages"]:
            # Check if email already processed
            existing = await crud_email.get_email_by_message_id(
                db, message_id=email_data["id"], account_id=account_id
            )
            
            if not existing:
                # Create processed email record with thread info
                processed_email = await crud_email.create_processed_email(
                    db,
                    email_data={
                        "account_id": account_id,
                        "email_id": email_data["id"],  # プロバイダー側のID
                        "message_id": email_data.get("message_id", ""),  # Message-IDヘッダー
                        "thread_id": email_data.get("thread_id", ""),
                        "in_reply_to": email_data.get("in_reply_to", ""),
                        "references": email_data.get("references", ""),
                        "subject": email_data.get("subject", ""),
                        "sender": email_data.get("from", ""),
                        "recipients": json.dumps(email_data.get("to", [])),
                        "body": email_data.get("body", ""),
                        "body_preview": email_data.get("snippet", "")[:500] if email_data.get("snippet") else None,
                        "received_at": email_data.get("date"),
                        "is_task": False,
                        "raw_data": json.dumps(email_data)
                    }
                )
                
                # スレッドごとにメールをグループ化
                thread_id = email_data.get("thread_id", "")
                if thread_id not in threads:
                    threads[thread_id] = []
                threads[thread_id].append({
                    "email_id": str(processed_email.id),
                    "subject": email_data.get("subject", ""),
                    "from": email_data.get("from", ""),
                    "date": email_data.get("date", ""),
                    "body": email_data.get("body", ""),
                    "is_reply": bool(email_data.get("in_reply_to"))
                })
                
                processed_count += 1
        
        # スレッド単位でAI分析タスクをキューに追加
        # 同じスレッドのメールは一緒に処理される
        for thread_id, thread_emails in threads.items():
            # スレッド内のメールIDリスト
            email_ids = [email["email_id"] for email in thread_emails]
            
            # スレッドの最初のメール（返信でないもの）または最新のメールを代表とする
            primary_email = next((e for e in thread_emails if not e["is_reply"]), thread_emails[-1])
            
            # AI分析タスクをキュー（スレッド単位）
            analyze_email_thread_for_tasks.delay(
                thread_id=thread_id,
                email_ids=email_ids,
                user_id=user_id,
                primary_subject=primary_email["subject"]
            )
        
        # Update sync token
        await crud_email.update_sync_token(
            db,
            account_id=account_id,
            sync_token=emails.get("nextSyncToken", emails.get("deltaLink"))
        )
        
        return {
            "task_id": task_id,
            "status": "completed",
            "processed_emails": processed_count,
            "processed_threads": len(threads),
            "sync_token_updated": True,
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=EmailSyncTask, name="app.worker.tasks.email.analyze_email_for_tasks")
def analyze_email_for_tasks(self, email_id: str, user_id: str) -> Dict[str, Any]:
    """
    Analyze email content and create tasks if applicable
    
    Args:
        email_id: Processed email ID
        user_id: User ID
        
    Returns:
        Dict with analysis results
    """
    from app.worker.tasks.ai import analyze_email_with_ai
    
    # Delegate to AI task
    result = analyze_email_with_ai.apply_async(
        args=[email_id, user_id],
        queue="ai"
    )
    
    return {
        "email_id": email_id,
        "ai_task_id": result.id,
        "status": "queued_for_ai_analysis"
    }


@celery_app.task(bind=True, name="app.worker.tasks.email.send_email")
def send_email(self, to: List[str], subject: str, body: str, user_id: str) -> Dict[str, Any]:
    """
    Send email via SMTP
    
    Args:
        to: List of recipient emails
        subject: Email subject
        body: Email body
        user_id: User ID for tracking
        
    Returns:
        Dict with send results
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        email_service = EmailService()
        result = loop.run_until_complete(
            email_service.send_email(to=to, subject=subject, body=body)
        )
        
        return {
            "task_id": self.request.id,
            "status": "sent",
            "recipients": to,
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        loop.close()