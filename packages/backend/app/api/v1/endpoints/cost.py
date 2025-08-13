from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List
from datetime import datetime

from app.models.user import User
from app.core.deps import get_current_user
from app.services.user_usage_tracker import UserUsageTracker
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/monthly")
async def get_monthly_usage(
    year: int = Query(None, description="年 (例: 2025)"),
    month: int = Query(None, description="月 (例: 8)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """ログインユーザーの月次OpenAI使用量を取得"""
    tracker = UserUsageTracker(db)
    return tracker.get_user_monthly_usage(
        user_id=str(current_user.id),
        year=year,
        month=month
    )


@router.get("/recent")
async def get_recent_usage(
    days: int = Query(7, description="過去何日分のデータを取得するか"),
    limit: int = Query(50, description="取得する最大レコード数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """ログインユーザーの最近の使用履歴を取得"""
    tracker = UserUsageTracker(db)
    return tracker.get_user_recent_usage(
        user_id=str(current_user.id),
        days=days,
        limit=limit
    )


@router.get("/summary")
async def get_usage_summary(
    days: int = Query(30, description="過去何日分のサマリーを取得するか"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """ログインユーザーの使用量サマリーを取得"""
    tracker = UserUsageTracker(db)
    return tracker.get_user_usage_summary(
        user_id=str(current_user.id),
        days=days
    )


@router.post("/estimate")
async def estimate_cost(
    model: str,
    input_tokens: int,
    max_output_tokens: int = 4000,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """コスト見積もりを取得"""
    tracker = UserUsageTracker(db)
    return tracker.calculate_cost_estimate(model, input_tokens, max_output_tokens)


@router.get("/models")
async def get_available_models(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """利用可能なモデルと料金情報を取得"""
    return {
        "models": UserUsageTracker.PRICING,
        "recommended": "gpt-5-mini",
        "description": {
            "gpt-5-mini": "コスト効率が良く、高品質な小型モデル",
            "gpt-5": "最高性能のフルモデル（高コスト）",
            "gpt-5-nano": "超高速・最低コストモデル",
            "gpt-5-chat-latest": "ChatGPT相当の非推論モデル"
        }
    }