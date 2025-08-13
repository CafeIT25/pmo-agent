"""
ユーザー別OpenAI使用量追跡サービス
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_

from app.core.database import get_db
from app.models.usage import OpenAIUsage
from app.models.user import User


class UserUsageTracker:
    """
    ユーザー別のOpenAI使用量追跡
    """
    
    # GPT-5 シリーズの料金（2025年8月時点）
    PRICING = {
        "gpt-5": {
            "input": 1.25,   # per 1M tokens
            "output": 10.00  # per 1M tokens
        },
        "gpt-5-mini": {
            "input": 0.25,   # per 1M tokens
            "output": 2.00   # per 1M tokens
        },
        "gpt-5-nano": {
            "input": 0.05,   # per 1M tokens
            "output": 0.40   # per 1M tokens
        },
        "gpt-5-chat-latest": {
            "input": 1.25,   # per 1M tokens
            "output": 10.00  # per 1M tokens
        },
        "gpt-4o": {
            "input": 2.5,    # per 1M tokens
            "output": 10.0   # per 1M tokens
        },
        "gpt-3.5-turbo": {
            "input": 0.5,    # per 1M tokens
            "output": 1.5    # per 1M tokens
        }
    }
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    def log_usage(
        self,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        purpose: str,
        endpoint: str = None,
        verbosity: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        request_summary: Optional[str] = None,
        response_summary: Optional[str] = None
    ) -> OpenAIUsage:
        """ユーザーの使用量をデータベースに記録"""
        
        # コスト計算
        cost_usd = self.calculate_cost(model, input_tokens, output_tokens)
        cost_jpy = round(cost_usd * 150, 2)  # 概算レート
        total_tokens = input_tokens + output_tokens
        
        # 使用量記録を作成
        usage_record = OpenAIUsage(
            user_id=user_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            cost_jpy=cost_jpy,
            purpose=purpose,
            endpoint=endpoint,
            verbosity=verbosity,
            reasoning_effort=reasoning_effort,
            request_data=request_summary,
            response_data=response_summary,
            created_at=datetime.utcnow()
        )
        
        self.db.add(usage_record)
        self.db.commit()
        self.db.refresh(usage_record)
        
        return usage_record
    
    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """コスト計算（GPT-5対応）"""
        # モデル名の正規化
        if model.startswith("gpt-5-mini"):
            pricing_model = "gpt-5-mini"
        elif model.startswith("gpt-5-nano"):
            pricing_model = "gpt-5-nano" 
        elif model.startswith("gpt-5-chat"):
            pricing_model = "gpt-5-chat-latest"
        elif model.startswith("gpt-5"):
            pricing_model = "gpt-5"
        else:
            pricing_model = model
        
        pricing = self.PRICING.get(pricing_model, self.PRICING["gpt-5-mini"])
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return round(input_cost + output_cost, 6)
    
    def get_user_monthly_usage(
        self,
        user_id: str,
        year: int = None,
        month: int = None
    ) -> Dict[str, Any]:
        """ユーザーの月次使用量を取得"""
        
        if not year or not month:
            now = datetime.utcnow()
            year = year or now.year
            month = month or now.month
        
        # 月次合計の取得
        monthly_total = self.db.query(
            func.sum(OpenAIUsage.input_tokens).label('total_input_tokens'),
            func.sum(OpenAIUsage.output_tokens).label('total_output_tokens'),
            func.sum(OpenAIUsage.total_tokens).label('total_tokens'),
            func.sum(OpenAIUsage.cost_usd).label('total_cost_usd'),
            func.sum(OpenAIUsage.cost_jpy).label('total_cost_jpy'),
            func.count(OpenAIUsage.id).label('request_count')
        ).filter(
            OpenAIUsage.user_id == user_id,
            extract('year', OpenAIUsage.created_at) == year,
            extract('month', OpenAIUsage.created_at) == month
        ).first()
        
        # モデル別の使用量
        model_stats = self.db.query(
            OpenAIUsage.model,
            func.sum(OpenAIUsage.input_tokens).label('input_tokens'),
            func.sum(OpenAIUsage.output_tokens).label('output_tokens'),
            func.sum(OpenAIUsage.cost_usd).label('cost_usd'),
            func.count(OpenAIUsage.id).label('requests')
        ).filter(
            OpenAIUsage.user_id == user_id,
            extract('year', OpenAIUsage.created_at) == year,
            extract('month', OpenAIUsage.created_at) == month
        ).group_by(OpenAIUsage.model).all()
        
        # 用途別の使用量
        purpose_stats = self.db.query(
            OpenAIUsage.purpose,
            func.sum(OpenAIUsage.input_tokens).label('input_tokens'),
            func.sum(OpenAIUsage.output_tokens).label('output_tokens'),
            func.sum(OpenAIUsage.cost_usd).label('cost_usd'),
            func.count(OpenAIUsage.id).label('requests')
        ).filter(
            OpenAIUsage.user_id == user_id,
            extract('year', OpenAIUsage.created_at) == year,
            extract('month', OpenAIUsage.created_at) == month
        ).group_by(OpenAIUsage.purpose).all()
        
        # 日別使用量（グラフ用）
        daily_stats = self.db.query(
            func.date(OpenAIUsage.created_at).label('date'),
            func.sum(OpenAIUsage.cost_usd).label('daily_cost'),
            func.sum(OpenAIUsage.total_tokens).label('daily_tokens'),
            func.count(OpenAIUsage.id).label('daily_requests')
        ).filter(
            OpenAIUsage.user_id == user_id,
            extract('year', OpenAIUsage.created_at) == year,
            extract('month', OpenAIUsage.created_at) == month
        ).group_by(func.date(OpenAIUsage.created_at)).order_by(func.date(OpenAIUsage.created_at)).all()
        
        return {
            "year": year,
            "month": month,
            "user_id": user_id,
            "summary": {
                "total_input_tokens": monthly_total.total_input_tokens or 0,
                "total_output_tokens": monthly_total.total_output_tokens or 0,
                "total_tokens": monthly_total.total_tokens or 0,
                "total_cost_usd": round(monthly_total.total_cost_usd or 0.0, 6),
                "total_cost_jpy": round(monthly_total.total_cost_jpy or 0.0, 2),
                "request_count": monthly_total.request_count or 0,
                "average_cost_per_request": round(
                    (monthly_total.total_cost_usd or 0.0) / max(monthly_total.request_count or 1, 1), 6
                )
            },
            "model_breakdown": [
                {
                    "model": stat.model,
                    "input_tokens": stat.input_tokens,
                    "output_tokens": stat.output_tokens,
                    "cost_usd": round(stat.cost_usd, 6),
                    "cost_jpy": round(stat.cost_usd * 150, 2),
                    "requests": stat.requests
                }
                for stat in model_stats
            ],
            "purpose_breakdown": [
                {
                    "purpose": stat.purpose or "unknown",
                    "input_tokens": stat.input_tokens,
                    "output_tokens": stat.output_tokens,
                    "cost_usd": round(stat.cost_usd, 6),
                    "cost_jpy": round(stat.cost_usd * 150, 2),
                    "requests": stat.requests
                }
                for stat in purpose_stats
            ],
            "daily_usage": [
                {
                    "date": stat.date.isoformat(),
                    "cost_usd": round(stat.daily_cost, 6),
                    "cost_jpy": round(stat.daily_cost * 150, 2),
                    "tokens": stat.daily_tokens,
                    "requests": stat.daily_requests
                }
                for stat in daily_stats
            ]
        }
    
    def get_user_recent_usage(
        self,
        user_id: str,
        days: int = 7,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """ユーザーの最近の使用履歴を取得"""
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        recent_usage = self.db.query(OpenAIUsage).filter(
            and_(
                OpenAIUsage.user_id == user_id,
                OpenAIUsage.created_at >= since_date
            )
        ).order_by(OpenAIUsage.created_at.desc()).limit(limit).all()
        
        return [usage.to_dict() for usage in recent_usage]
    
    def get_user_usage_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """ユーザーの使用量サマリーを取得"""
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        summary = self.db.query(
            func.sum(OpenAIUsage.input_tokens).label('total_input_tokens'),
            func.sum(OpenAIUsage.output_tokens).label('total_output_tokens'),
            func.sum(OpenAIUsage.total_tokens).label('total_tokens'),
            func.sum(OpenAIUsage.cost_usd).label('total_cost_usd'),
            func.sum(OpenAIUsage.cost_jpy).label('total_cost_jpy'),
            func.count(OpenAIUsage.id).label('request_count'),
            func.max(OpenAIUsage.created_at).label('last_used')
        ).filter(
            and_(
                OpenAIUsage.user_id == user_id,
                OpenAIUsage.created_at >= since_date
            )
        ).first()
        
        return {
            "period_days": days,
            "total_input_tokens": summary.total_input_tokens or 0,
            "total_output_tokens": summary.total_output_tokens or 0,
            "total_tokens": summary.total_tokens or 0,
            "total_cost_usd": round(summary.total_cost_usd or 0.0, 6),
            "total_cost_jpy": round(summary.total_cost_jpy or 0.0, 2),
            "request_count": summary.request_count or 0,
            "last_used": summary.last_used.isoformat() if summary.last_used else None,
            "average_cost_per_request": round(
                (summary.total_cost_usd or 0.0) / max(summary.request_count or 1, 1), 6
            )
        }


# グローバルインスタンス
user_usage_tracker = UserUsageTracker()