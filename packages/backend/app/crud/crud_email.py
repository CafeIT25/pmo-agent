from typing import Optional, List, Dict, Any
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import and_, func, desc, asc
from datetime import datetime, timedelta
import json

from app.models.email import EmailAccount, ProcessedEmail, EmailSyncJob
from app.models.user import User
from app.crud.base import CRUDBase


class CRUDEmail(CRUDBase[EmailAccount]):
    async def get_email_account(
        self,
        db: AsyncSession,
        account_id: str,
        user_id: str
    ) -> Optional[EmailAccount]:
        """Get email account by ID and user"""
        statement = select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == user_id
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_user_email_accounts(
        self,
        db: AsyncSession,
        user_id: str
    ) -> List[EmailAccount]:
        """Get all email accounts for a user"""
        statement = select(EmailAccount).where(EmailAccount.user_id == user_id)
        result = await db.execute(statement)
        return result.scalars().all()
    
    async def create_email_account(
        self,
        db: AsyncSession,
        account_data: Dict[str, Any]
    ) -> EmailAccount:
        """Create new email account"""
        account = EmailAccount(**account_data)
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return account
    
    async def update_sync_token(
        self,
        db: AsyncSession,
        account_id: str,
        sync_token: str
    ) -> None:
        """Update last sync token"""
        statement = select(EmailAccount).where(EmailAccount.id == account_id)
        result = await db.execute(statement)
        account = result.scalar_one_or_none()
        
        if account:
            account.last_sync_token = sync_token
            account.last_sync_at = datetime.utcnow()
            await db.commit()
    
    async def get_processed_email(
        self,
        db: AsyncSession,
        email_id: str
    ) -> Optional[ProcessedEmail]:
        """Get processed email by ID"""
        statement = select(ProcessedEmail).where(ProcessedEmail.id == email_id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_email_by_message_id(
        self,
        db: AsyncSession,
        message_id: str,
        account_id: str
    ) -> Optional[ProcessedEmail]:
        """
        Get email by provider message ID
        注意: message_id パラメータは実際にはプロバイダー側のメールID（email_id フィールド）を参照
        """
        statement = select(ProcessedEmail).where(
            ProcessedEmail.email_id == message_id,  # プロバイダー側のIDで検索
            ProcessedEmail.account_id == account_id
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    
    async def create_processed_email(
        self,
        db: AsyncSession,
        email_data: Dict[str, Any]
    ) -> ProcessedEmail:
        """Create processed email record"""
        email = ProcessedEmail(**email_data)
        db.add(email)
        await db.commit()
        await db.refresh(email)
        return email
    
    async def update_email_analysis(
        self,
        db: AsyncSession,
        email_id: str,
        is_task: bool,
        ai_summary: str,
        ai_analysis: str
    ) -> None:
        """Update email with AI analysis results"""
        statement = select(ProcessedEmail).where(ProcessedEmail.id == email_id)
        result = await db.execute(statement)
        email = result.scalar_one_or_none()
        
        if email:
            email.is_task = is_task
            email.ai_summary = ai_summary
            email.ai_analysis = ai_analysis
            email.analyzed_at = datetime.utcnow()
            await db.commit()
    
    async def get_unprocessed_emails(
        self,
        db: AsyncSession,
        account_id: str,
        limit: int = 50
    ) -> List[ProcessedEmail]:
        """Get emails that haven't been analyzed"""
        statement = select(ProcessedEmail).where(
            ProcessedEmail.account_id == account_id,
            ProcessedEmail.analyzed_at.is_(None)
        ).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_user_emails_optimized(
        self,
        db: AsyncSession,
        sync_job_id: str,
        limit: int = 50,
        offset: int = 0,
        include_thread: bool = False
    ) -> List[ProcessedEmail]:
        """
        ユーザーのメール一覧を最適化して取得
        Railway無料プラン対応・N+1問題解決
        """
        
        statement = select(ProcessedEmail).where(
            ProcessedEmail.sync_job_id == sync_job_id
        )
        
        if include_thread:
            # スレッド情報も含める場合
            statement = statement.options(
                joinedload(ProcessedEmail.sync_job).load_only(
                    EmailSyncJob.email_account_id,
                    EmailSyncJob.status
                )
            )
        
        # インデックスを活用したソート（日付降順）
        statement = statement.order_by(desc(ProcessedEmail.email_date))
        
        # ページネーション
        statement = statement.offset(offset).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_email_threads_optimized(
        self,
        db: AsyncSession,
        sync_job_id: str,
        thread_id: str,
        limit: int = 20
    ) -> List[ProcessedEmail]:
        """
        メールスレッドを効率的に取得
        AI分析・返信機能向け最適化
        """
        
        statement = select(ProcessedEmail).where(
            and_(
                ProcessedEmail.sync_job_id == sync_job_id,
                ProcessedEmail.thread_id == thread_id
            )
        ).order_by(
            asc(ProcessedEmail.email_date)  # スレッドは時系列順
        ).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_ai_analyzed_emails(
        self,
        db: AsyncSession,
        sync_job_id: str,
        is_task: Optional[bool] = None,
        limit: int = 30
    ) -> List[ProcessedEmail]:
        """
        AI分析済みメールを効率的に取得
        タスク管理機能向け最適化
        """
        
        statement = select(ProcessedEmail).where(
            and_(
                ProcessedEmail.sync_job_id == sync_job_id,
                ProcessedEmail.ai_analysis.isnot(None)
            )
        )
        
        if is_task is not None:
            statement = statement.where(ProcessedEmail.is_task == is_task)
        
        # AI分析日時でソート（インデックス未設定のため最小限に）
        statement = statement.order_by(desc(ProcessedEmail.processed_at))
        statement = statement.limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_recent_emails_summary(
        self,
        db: AsyncSession,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        最近のメール統計サマリーを効率的に取得
        ダッシュボード向け最適化
        """
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # サブクエリでユーザーの同期ジョブIDを取得
        sync_job_subquery = select(EmailSyncJob.id).join(
            EmailAccount, EmailSyncJob.email_account_id == EmailAccount.id
        ).where(EmailAccount.user_id == user_id).subquery()
        
        # 集約クエリで一度に統計を取得
        summary_query = select(
            func.count().label('total_emails'),
            func.count().filter(ProcessedEmail.is_task == True).label('task_emails'),
            func.count().filter(ProcessedEmail.ai_analysis.isnot(None)).label('analyzed_emails'),
            func.count().filter(
                ProcessedEmail.email_date >= cutoff_date
            ).label('recent_emails')
        ).where(
            ProcessedEmail.sync_job_id.in_(sync_job_subquery)
        )
        
        result = await db.execute(summary_query)
        row = result.first()
        
        return {
            'total_emails': row.total_emails or 0,
            'task_emails': row.task_emails or 0,
            'analyzed_emails': row.analyzed_emails or 0,
            'recent_emails': row.recent_emails or 0,
            'task_conversion_rate': round((row.task_emails / row.total_emails * 100), 1) if row.total_emails > 0 else 0
        }

    async def cleanup_old_emails(
        self,
        db: AsyncSession,
        days_to_keep: int = 90
    ) -> int:
        """
        古いメールデータを削除してストレージを節約
        Railway無料プラン（1GB制限）対応
        """
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # 古いメールを削除（タスク化されていないもののみ）
        from sqlalchemy import delete
        
        delete_query = delete(ProcessedEmail).where(
            and_(
                ProcessedEmail.email_date < cutoff_date,
                ProcessedEmail.is_task == False  # タスク化されたメールは保持
            )
        )
        
        result = await db.execute(delete_query)
        await db.commit()
        
        return result.rowcount


crud_email = CRUDEmail(EmailAccount)