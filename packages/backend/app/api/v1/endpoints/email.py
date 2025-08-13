from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.models.user import User
from app.core.deps import get_current_user

router = APIRouter()


class EmailSyncJob(BaseModel):
    id: str
    email_account_id: str
    status: str
    total_emails: int
    processed_emails: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class EmailSyncRequest(BaseModel):
    account_id: str


class EmailSyncResponse(BaseModel):
    job_id: str


class EmailSyncHistory(BaseModel):
    jobs: List[EmailSyncJob]
    total: int


@router.post("/sync", response_model=EmailSyncResponse)
async def start_email_sync(
    sync_request: EmailSyncRequest,
    current_user: User = Depends(get_current_user)
):
    """メール同期開始"""
    from app.worker.tasks.email import sync_emails
    
    try:
        # Queue Celery task
        result = sync_emails.delay(
            user_id=str(current_user.id),
            account_id=sync_request.account_id
        )
        
        return EmailSyncResponse(job_id=result.id)
    except Exception as e:
        if "OPENAI_INSUFFICIENT_CREDITS" in str(e):
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "message": "OpenAI APIのクレジットが不足しています。メール分析にはAI機能が必要です。管理者に連絡してください。"
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


@router.get("/sync/{job_id}", response_model=EmailSyncJob)
async def get_sync_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """同期ジョブ状態取得"""
    from celery.result import AsyncResult
    from app.worker.celery_app import celery_app
    
    result = AsyncResult(job_id, app=celery_app)
    
    if result.state == "PENDING":
        status = "pending"
        info = {"processed_emails": 0, "total_emails": 0}
    elif result.state == "PROGRESS":
        status = "processing"
        info = result.info or {}
    elif result.state == "SUCCESS":
        status = "completed"
        info = result.result or {}
    else:  # FAILURE
        status = "failed"
        info = {"error": str(result.info)}
    
    return EmailSyncJob(
        id=job_id,
        email_account_id=info.get("account_id", ""),
        status=status,
        total_emails=info.get("total_emails", 0),
        processed_emails=info.get("processed_emails", 0),
        started_at=datetime.utcnow(),
        error_message=info.get("error")
    )


@router.get("/sync/history", response_model=EmailSyncHistory)
async def get_sync_history(
    page: int = 1,
    limit: int = 20,
):
    """同期履歴取得"""
    # TODO: 実装
    return EmailSyncHistory(
        jobs=[],
        total=0,
    )