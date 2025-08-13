from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.user import User

Base = declarative_base()


class OpenAIUsage(Base):
    """
    ユーザー別のOpenAI API使用量記録
    """
    __tablename__ = "openai_usage"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # API呼び出し情報
    model = Column(String(50), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0) 
    total_tokens = Column(Integer, nullable=False, default=0)
    
    # コスト情報
    cost_usd = Column(Float, nullable=False, default=0.0)
    cost_jpy = Column(Float, nullable=False, default=0.0)
    
    # 用途情報
    purpose = Column(String(100), nullable=True)  # email_analysis, task_investigation など
    endpoint = Column(String(100), nullable=True)  # 呼び出されたAPIエンドポイント
    
    # GPT-5固有パラメータ
    verbosity = Column(String(20), nullable=True)
    reasoning_effort = Column(String(20), nullable=True)
    
    # 追加情報
    request_data = Column(Text, nullable=True)  # リクエスト内容のサマリー
    response_data = Column(Text, nullable=True)  # レスポンス内容のサマリー
    
    # タイムスタンプ
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # リレーション
    user = relationship("User", back_populates="openai_usage")
    
    def to_dict(self):
        """辞書形式で返却"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "cost_jpy": round(self.cost_jpy, 2),
            "purpose": self.purpose,
            "endpoint": self.endpoint,
            "verbosity": self.verbosity,
            "reasoning_effort": self.reasoning_effort,
            "created_at": self.created_at.isoformat()
        }
        
    @classmethod
    def calculate_monthly_total(cls, user_id: str, year: int, month: int):
        """指定月のユーザー使用量合計を計算"""
        from sqlalchemy import func, extract
        from app.core.database import get_db
        
        session = next(get_db())
        try:
            result = session.query(
                func.sum(cls.input_tokens).label('total_input_tokens'),
                func.sum(cls.output_tokens).label('total_output_tokens'),
                func.sum(cls.total_tokens).label('total_tokens'),
                func.sum(cls.cost_usd).label('total_cost_usd'),
                func.sum(cls.cost_jpy).label('total_cost_jpy'),
                func.count(cls.id).label('request_count')
            ).filter(
                cls.user_id == user_id,
                extract('year', cls.created_at) == year,
                extract('month', cls.created_at) == month
            ).first()
            
            return {
                "total_input_tokens": result.total_input_tokens or 0,
                "total_output_tokens": result.total_output_tokens or 0,
                "total_tokens": result.total_tokens or 0,
                "total_cost_usd": round(result.total_cost_usd or 0.0, 6),
                "total_cost_jpy": round(result.total_cost_jpy or 0.0, 2),
                "request_count": result.request_count or 0
            }
        finally:
            session.close()


# User モデルにリレーションを追加する必要があります
# app/models/user.py に以下を追加：
# openai_usage = relationship("OpenAIUsage", back_populates="user")