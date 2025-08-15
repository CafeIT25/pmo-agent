from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.chat import ChatRole


class ChatMessageBase(BaseModel):
    role: ChatRole
    content: str


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    id: UUID
    thread_id: UUID
    token_count: Optional[int] = None
    model_id: Optional[str] = None
    cost: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatThreadBase(BaseModel):
    title: str
    task_id: Optional[UUID] = None


class ChatThreadCreate(ChatThreadBase):
    pass


class ChatThreadResponse(ChatThreadBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatThreadWithMessages(ChatThreadResponse):
    messages: List[ChatMessageResponse] = []


class ChatSendMessageRequest(BaseModel):
    content: str


class ChatSendMessageResponse(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class ChatCreateThreadRequest(BaseModel):
    title: str
    task_id: Optional[UUID] = None
    initial_message: Optional[str] = None