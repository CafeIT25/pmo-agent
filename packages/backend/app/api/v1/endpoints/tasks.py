from fastapi import APIRouter, Query, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID, uuid4

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.task import Task as TaskModel
from app.crud import crud_task
from app.schemas.task import TaskCreate as TaskCreateSchema, TaskUpdate as TaskUpdateSchema

router = APIRouter()


class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    source_email_id: Optional[str] = None
    source_email_link: Optional[str] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskList(BaseModel):
    tasks: List[Task]
    total: int
    page: int
    limit: int


class AISupport(BaseModel):
    id: str
    task_id: str
    request_type: str
    prompt: str
    response: str
    model_id: str
    created_at: datetime


@router.get("", response_model=TaskList)
async def get_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """タスク一覧取得（認証済みユーザーのタスクのみ）"""
    # ユーザーのタスクのみ取得
    tasks = crud_task.get_multi_by_user(
        db=db,
        user_id=current_user.id,
        skip=(page - 1) * limit,
        limit=limit,
        status=status,
        priority=priority,
        search=search
    )
    
    total = crud_task.count_by_user(
        db=db,
        user_id=current_user.id,
        status=status,
        priority=priority,
        search=search
    )
    
    return TaskList(
        tasks=[Task(
            id=str(task.id),
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            source_email_id=str(task.source_email_id) if task.source_email_id else None,
            source_email_link=task.source_email_link,
            due_date=task.due_date,
            created_at=task.created_at,
            updated_at=task.updated_at
        ) for task in tasks],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=Task)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """タスク作成（認証済みユーザーのみ）"""
    task_in = TaskCreateSchema(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority or "medium",
        due_date=task_data.due_date,
        user_id=current_user.id,
        created_by="user"
    )
    
    task = crud_task.create(db=db, obj_in=task_in)
    
    return Task(
        id=str(task.id),
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        source_email_link=task.source_email_link,
        due_date=task.due_date,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/{task_id}", response_model=dict)
async def get_task_detail(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """タスク詳細取得（所有者のみアクセス可能）"""
    # タスクを取得
    task = crud_task.get(db=db, id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 所有者チェック
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this task"
        )
    
    return {
        "task": Task(
            id=str(task.id),
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            source_email_id=str(task.source_email_id) if task.source_email_id else None,
            source_email_link=task.source_email_link,
            due_date=task.due_date,
            created_at=task.created_at,
            updated_at=task.updated_at,
        ),
        "history": task.history if hasattr(task, 'history') else [],
        "ai_supports": task.ai_supports if hasattr(task, 'ai_supports') else [],
    }


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """タスク更新（所有者のみ）"""
    # タスクを取得
    task = crud_task.get(db=db, id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 所有者チェック
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task"
        )
    
    # 更新
    task_in = TaskUpdateSchema(
        title=task_update.title,
        description=task_update.description,
        status=task_update.status,
        priority=task_update.priority,
        due_date=task_update.due_date,
        updated_by="user"
    )
    
    task = crud_task.update(db=db, db_obj=task, obj_in=task_in)
    
    return Task(
        id=str(task.id),
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        source_email_link=task.source_email_link,
        due_date=task.due_date,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """タスク削除（所有者のみ）"""
    # タスクを取得
    task = crud_task.get(db=db, id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 所有者チェック
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task"
        )
    
    # 削除
    crud_task.remove(db=db, id=task_id)
    
    return {"message": f"Task {task_id} deleted successfully"}


@router.post("/{task_id}/ai-support", response_model=AISupport)
async def request_ai_support(
    task_id: str,
    support_type: str = "research",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AIサポート実行（タスク所有者のみ）"""
    # タスクを取得
    task = crud_task.get(db=db, id=task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 所有者チェック
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to request AI support for this task"
        )
    
    # TODO: 実際のAIサポート実装
    return AISupport(
        id=str(uuid4()),
        task_id=task_id,
        request_type=support_type,
        prompt="Task analysis request",
        response="AI analysis result placeholder",
        model_id="claude-3",
        created_at=datetime.utcnow(),
    )