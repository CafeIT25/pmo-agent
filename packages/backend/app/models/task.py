from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class TaskStatus(str, Enum):
    """タスクのステータス"""
    TODO = "todo"
    PROGRESS = "progress"
    DONE = "done"


class TaskPriority(str, Enum):
    """タスクの優先度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskBase(SQLModel):
    """タスクの基本情報"""
    title: str = Field(index=True)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class Task(TaskBase, table=True):
    """タスクテーブルモデル"""
    __tablename__ = "tasks"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    source_email_id: Optional[UUID] = Field(default=None, foreign_key="processed_emails.id")
    source_email_link: Optional[str] = None
    email_summary: Optional[str] = None  # メール要約
    updated_by: Optional[str] = Field(default="user")  # "ai" or "user"
    created_by: Optional[str] = Field(default="user")  # "ai" or "user"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # リレーション
    user: "User" = Relationship(back_populates="tasks")
    source_email: Optional["ProcessedEmail"] = Relationship(back_populates="tasks")
    history: List["TaskHistory"] = Relationship(back_populates="task")
    ai_supports: List["AISupport"] = Relationship(back_populates="task")


class TaskCreate(TaskBase):
    """タスク作成用スキーマ"""
    pass


class TaskUpdate(SQLModel):
    """タスク更新用スキーマ"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None


class TaskOut(TaskBase):
    """タスク情報の出力用スキーマ"""
    id: UUID
    user_id: UUID
    source_email_id: Optional[UUID] = None
    source_email_link: Optional[str] = None
    email_summary: Optional[str] = None
    updated_by: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None