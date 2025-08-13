from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from app.models.user import User
from app.core.deps import get_current_user
from app.worker.tasks.ai import generate_task_suggestions, summarize_email_thread


router = APIRouter()


class TaskSuggestionRequest(BaseModel):
    task_id: str
    context: Optional[str] = ""


class TaskSuggestionResponse(BaseModel):
    job_id: str
    status: str = "queued"


class EmailThreadSummaryRequest(BaseModel):
    email_ids: list[str]


class EmailThreadSummaryResponse(BaseModel):
    job_id: str
    status: str = "queued"


class AIJobStatus(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


@router.post("/task-suggestions", response_model=TaskSuggestionResponse)
async def request_task_suggestions(
    request: TaskSuggestionRequest,
    current_user: User = Depends(get_current_user)
):
    """タスクに対するAI提案を生成"""
    try:
        result = generate_task_suggestions.delay(
            task_id=request.task_id,
            context=request.context
        )
        return TaskSuggestionResponse(job_id=result.id)
    except Exception as e:
        if "OPENAI_INSUFFICIENT_CREDITS" in str(e):
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "message": "OpenAI APIのクレジットが不足しています。管理者に連絡してください。"
                }
            )
        elif "OPENAI_RATE_LIMIT" in str(e):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit",
                    "message": "OpenAI APIのレート制限に達しました。しばらく待ってから再試行してください。"
                }
            )
        else:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/email-thread-summary", response_model=EmailThreadSummaryResponse)
async def request_email_thread_summary(
    request: EmailThreadSummaryRequest,
    current_user: User = Depends(get_current_user)
):
    """メールスレッドの要約を生成"""
    try:
        result = summarize_email_thread.delay(
            email_ids=request.email_ids
        )
        return EmailThreadSummaryResponse(job_id=result.id)
    except Exception as e:
        if "OPENAI_INSUFFICIENT_CREDITS" in str(e):
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "message": "OpenAI APIのクレジットが不足しています。管理者に連絡してください。"
                }
            )
        elif "OPENAI_RATE_LIMIT" in str(e):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit",
                    "message": "OpenAI APIのレート制限に達しました。しばらく待ってから再試行してください。"
                }
            )
        else:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}", response_model=AIJobStatus)
async def get_ai_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """AI処理ジョブの状態を取得"""
    from celery.result import AsyncResult
    from app.worker.celery_app import celery_app
    
    result = AsyncResult(job_id, app=celery_app)
    
    status_map = {
        "PENDING": "pending",
        "STARTED": "processing",
        "RETRY": "retrying",
        "SUCCESS": "completed",
        "FAILURE": "failed"
    }
    
    response = AIJobStatus(
        job_id=job_id,
        status=status_map.get(result.state, result.state.lower()),
        created_at=datetime.utcnow()
    )
    
    if result.state == "SUCCESS":
        response.result = result.result
        response.completed_at = datetime.utcnow()
    elif result.state == "FAILURE":
        response.error = str(result.info)
        response.completed_at = datetime.utcnow()
    
    return response