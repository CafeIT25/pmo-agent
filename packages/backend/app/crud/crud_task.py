from typing import Optional, List, Dict, Any
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import and_, func, desc, asc
from datetime import datetime
from uuid import UUID

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.history import TaskHistory, AISupport
from app.models.user import User
from app.models.email import ProcessedEmail
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
        limit: int = 50,  # Railway無料プラン対応で制限
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Task]:
        """
        Get tasks for a user with optimal performance
        N+1問題を解決し、Railway制限を考慮した実装
        """
        statement = select(Task).where(Task.user_id == user_id)
        
        if status:
            statement = statement.where(Task.status == status)
        if priority:
            statement = statement.where(Task.priority == priority)
        
        # N+1問題解決: 関連データを事前読み込み
        statement = statement.options(
            # ユーザー情報を事前読み込み（必要な場合のみ）
            joinedload(Task.user).load_only(User.name, User.email),
            
            # ソースメール情報を条件付きで読み込み
            joinedload(Task.source_email).load_only(
                ProcessedEmail.sender,
                ProcessedEmail.subject,
                ProcessedEmail.email_date
            )
        )
        
        # パフォーマンス最適化: インデックスを活用したソート
        statement = statement.order_by(
            desc(Task.updated_at),  # 更新日降順
            asc(Task.priority == TaskPriority.HIGH),  # 高優先度を上位に
        )
        
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

    async def get_dashboard_summary_optimized(
        self, 
        db: AsyncSession, 
        user_id: str
    ) -> dict:
        """
        ダッシュボード用のサマリー情報を1回のクエリで取得
        Railway無料プラン向けメモリ効率最適化
        """
        
        # 集約クエリで一度にサマリーを取得（N+1問題回避）
        summary_query = select(
            func.count().label('total_tasks'),
            func.count().filter(Task.status == TaskStatus.TODO).label('todo_count'),
            func.count().filter(Task.status == TaskStatus.PROGRESS).label('progress_count'),
            func.count().filter(Task.status == TaskStatus.DONE).label('done_count'),
            func.count().filter(
                and_(
                    Task.due_date.isnot(None),
                    Task.due_date < func.now(),
                    Task.status != TaskStatus.DONE
                )
            ).label('overdue_count')
        ).where(Task.user_id == user_id)
        
        result = await db.execute(summary_query)
        row = result.first()
        
        return {
            'total_tasks': row.total_tasks or 0,
            'todo_count': row.todo_count or 0,
            'progress_count': row.progress_count or 0, 
            'done_count': row.done_count or 0,
            'overdue_count': row.overdue_count or 0,
            'completion_rate': round((row.done_count / row.total_tasks * 100), 1) if row.total_tasks > 0 else 0
        }

    async def get_tasks_with_emails_optimized(
        self, 
        db: AsyncSession, 
        user_id: str,
        has_email: bool = True,
        limit: int = 20
    ) -> List[Task]:
        """
        メール起源のタスクを効率的に取得
        AI分析機能向け最適化
        """
        
        statement = select(Task).where(Task.user_id == user_id)
        
        if has_email:
            # メール起源のタスクのみ
            statement = statement.where(Task.source_email_id.isnot(None))
            
            # メール情報も事前読み込み
            statement = statement.options(
                joinedload(Task.source_email).load_only(
                    ProcessedEmail.sender,
                    ProcessedEmail.subject,
                    ProcessedEmail.body_preview,
                    ProcessedEmail.email_date,
                    ProcessedEmail.ai_analysis
                )
            )
        else:
            # ユーザー作成タスクのみ
            statement = statement.where(Task.source_email_id.is_(None))
        
        # 最新順でソート（インデックス活用）
        statement = statement.order_by(desc(Task.created_at)).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def batch_update_task_status(
        self, 
        db: AsyncSession, 
        task_ids: List[str], 
        new_status: TaskStatus,
        user_id: str
    ) -> int:
        """
        複数タスクのステータスを一括更新
        Railway制限下でのパフォーマンス最適化
        """
        
        from sqlalchemy import update
        
        # 一括更新クエリ（個別更新よりも高速）
        update_query = (
            update(Task)
            .where(
                and_(
                    Task.id.in_(task_ids),
                    Task.user_id == user_id  # セキュリティ: 自分のタスクのみ
                )
            )
            .values(
                status=new_status,
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow() if new_status == TaskStatus.DONE else None
            )
        )
        
        result = await db.execute(update_query)
        await db.commit()
        
        return result.rowcount


crud_task = CRUDTask(Task)