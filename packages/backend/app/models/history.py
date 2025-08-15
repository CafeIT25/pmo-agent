from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, Dict
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class TaskAction(str, Enum):
    """タスクアクション"""
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    PRIORITY_CHANGED = "priority_changed"
    COMPLETED = "completed"


class TaskHistory(SQLModel, table=True):
    """タスク履歴テーブルモデル"""
    __tablename__ = "task_histories"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="tasks.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    action: TaskAction
    changes: Optional[Dict] = Field(default=None, sa_column_kwargs={"type": "json"})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # リレーション
    task: "Task" = Relationship(back_populates="history")


class AISupportType(str, Enum):
    """AIサポートタイプ"""
    RESEARCH = "research"
    SOLUTION = "solution"


class AISupport(SQLModel, table=True):
    """AIサポートテーブルモデル"""
    __tablename__ = "ai_supports"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="tasks.id", index=True)
    thread_id: Optional[str] = Field(default=None, index=True)  # メールスレッドID
    request_type: AISupportType
    prompt: str
    response: str
    model_id: str
    cost: Optional[float] = None
    metadata: Optional[Dict] = Field(default=None, sa_column_kwargs={"type": "json"})  # 追加メタデータ
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # リレーション
    task: "Task" = Relationship(back_populates="ai_supports")