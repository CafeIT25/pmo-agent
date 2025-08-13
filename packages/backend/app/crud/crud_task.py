from typing import Optional, List, Dict, Any
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime
from uuid import UUID

from app.models.task import Task
from app.models.history import TaskHistory, AISupport
from app.schemas.task import TaskCreate, TaskUpdate
from app.crud.base import CRUDBase


class CRUDTask(CRUDBase[Task]):
    async def get_task(
        self,
        db: AsyncSession,
        task_id: str
    ) -> Optional[Task]:
        """Get task by ID"""
        statement = select(Task).where(Task.id == task_id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_user_tasks(
        self,
        db: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Task]:
        """Get tasks for a user with optional filters"""
        statement = select(Task).where(Task.user_id == user_id)
        
        if status:
            statement = statement.where(Task.status == status)
        if priority:
            statement = statement.where(Task.priority == priority)
        
        statement = statement.offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()
    
    async def create_task(
        self,
        db: AsyncSession,
        task: TaskCreate
    ) -> Task:
        """Create new task"""
        db_task = Task(
            title=task.title,
            description=task.description,
            status="pending",
            priority=task.priority or "medium",
            tags=task.tags or [],
            user_id=task.user_id,
            source_email_id=task.source_email_id,
            due_date=task.due_date
        )
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        
        # Create initial history entry
        history = TaskHistory(
            task_id=db_task.id,
            action="created",
            field_name="task",
            old_value=None,
            new_value=db_task.title,
            user_id=task.user_id
        )
        db.add(history)
        await db.commit()
        
        return db_task
    
    async def update_task(
        self,
        db: AsyncSession,
        task_id: str,
        task_update: TaskUpdate,
        user_id: str
    ) -> Optional[Task]:
        """Update task"""
        statement = select(Task).where(Task.id == task_id)
        result = await db.execute(statement)
        task = result.scalar_one_or_none()
        
        if not task:
            return None
        
        # Track changes for history
        changes = []
        
        if task_update.title and task_update.title != task.title:
            changes.append(("title", task.title, task_update.title))
            task.title = task_update.title
        
        if task_update.description and task_update.description != task.description:
            changes.append(("description", task.description, task_update.description))
            task.description = task_update.description
        
        if task_update.status and task_update.status != task.status:
            changes.append(("status", task.status, task_update.status))
            task.status = task_update.status
        
        if task_update.priority and task_update.priority != task.priority:
            changes.append(("priority", task.priority, task_update.priority))
            task.priority = task_update.priority
        
        if task_update.tags is not None:
            changes.append(("tags", str(task.tags), str(task_update.tags)))
            task.tags = task_update.tags
        
        if task_update.due_date != task.due_date:
            changes.append(("due_date", str(task.due_date), str(task_update.due_date)))
            task.due_date = task_update.due_date
        
        task.updated_at = datetime.utcnow()
        
        # Create history entries
        for field_name, old_value, new_value in changes:
            history = TaskHistory(
                task_id=task.id,
                action="updated",
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                user_id=user_id
            )
            db.add(history)
        
        await db.commit()
        await db.refresh(task)
        return task
    
    async def delete_task(
        self,
        db: AsyncSession,
        task_id: str,
        user_id: str
    ) -> bool:
        """Delete task"""
        statement = select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id
        )
        result = await db.execute(statement)
        task = result.scalar_one_or_none()
        
        if task:
            # Create deletion history
            history = TaskHistory(
                task_id=task.id,
                action="deleted",
                field_name="task",
                old_value=task.title,
                new_value=None,
                user_id=user_id
            )
            db.add(history)
            
            await db.delete(task)
            await db.commit()
            return True
        
        return False
    
    async def get_task_history(
        self,
        db: AsyncSession,
        task_id: str
    ) -> List[TaskHistory]:
        """Get task history"""
        statement = select(TaskHistory).where(
            TaskHistory.task_id == task_id
        ).order_by(TaskHistory.created_at.desc())
        result = await db.execute(statement)
        return result.scalars().all()
    
    async def create_ai_support(
        self,
        db: AsyncSession,
        task_id: str,
        support_type: str,
        ai_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AISupport:
        """Create AI support record"""
        support = AISupport(
            task_id=task_id,
            support_type=support_type,
            ai_response=ai_response,
            metadata=metadata or {}
        )
        db.add(support)
        await db.commit()
        await db.refresh(support)
        return support
    
    async def get_ai_supports(
        self,
        db: AsyncSession,
        task_id: str
    ) -> List[AISupport]:
        """Get AI support history for task"""
        statement = select(AISupport).where(
            AISupport.task_id == task_id
        ).order_by(AISupport.created_at.desc())
        result = await db.execute(statement)
        return result.scalars().all()


crud_task = CRUDTask(Task)