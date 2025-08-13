from typing import Optional, List, Dict, Any
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime
import json

from app.models.email import EmailAccount, ProcessedEmail
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


crud_email = CRUDEmail(EmailAccount)