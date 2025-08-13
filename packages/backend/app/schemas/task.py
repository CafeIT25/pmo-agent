from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    tags: Optional[List[str]] = []
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    user_id: str
    source_email_id: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None


class TaskInDB(TaskBase):
    id: UUID
    status: str
    user_id: UUID
    source_email_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Task(TaskInDB):
    pass