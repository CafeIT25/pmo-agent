from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class ChatRole(str, Enum):
    """チャットメッセージの送信者"""
    USER = "user"
    ASSISTANT = "assistant"


class ChatThread(SQLModel, table=True):
    """チャットスレッドテーブルモデル"""
    __tablename__ = "chat_threads"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    task_id: Optional[UUID] = Field(default=None, foreign_key="tasks.id", index=True)
    title: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # リレーション
    messages: List["ChatMessage"] = Relationship(back_populates="thread")
    user: "User" = Relationship()
    task: Optional["Task"] = Relationship()


class ChatMessage(SQLModel, table=True):
    """チャットメッセージテーブルモデル"""
    __tablename__ = "chat_messages"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    thread_id: UUID = Field(foreign_key="chat_threads.id", index=True)
    role: ChatRole
    content: str
    token_count: Optional[int] = Field(default=None)  # トークン数計算用
    model_id: Optional[str] = Field(default=None)  # 使用したAIモデル
    cost: Optional[float] = Field(default=None)  # APIコスト
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # リレーション
    thread: ChatThread = Relationship(back_populates="messages")