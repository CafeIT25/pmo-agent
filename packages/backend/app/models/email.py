from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class EmailProvider(str, Enum):
    """メールプロバイダー"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"


class EmailAccountBase(SQLModel):
    """メールアカウントの基本情報"""
    provider: EmailProvider
    email: str
    is_active: bool = True


class EmailAccount(EmailAccountBase, table=True):
    """メールアカウントテーブルモデル"""
    __tablename__ = "email_accounts"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    encrypted_tokens: str  # 暗号化されたOAuthトークン
    token_expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # リレーション
    user: "User" = Relationship(back_populates="email_accounts")
    sync_jobs: List["EmailSyncJob"] = Relationship(back_populates="email_account")


class ProcessedEmail(SQLModel, table=True):
    """処理済みメールテーブルモデル"""
    __tablename__ = "processed_emails"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    sync_job_id: UUID = Field(foreign_key="email_sync_jobs.id", index=True)
    email_id: str = Field(unique=True, index=True)  # プロバイダー側のメールID
    sender: str
    subject: str
    body_preview: Optional[str] = None
    is_task: bool = False
    ai_analysis: Optional[Dict] = Field(default=None, sa_column_kwargs={"type": "json"})
    email_date: datetime
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # スレッド情報
    thread_id: Optional[str] = Field(default=None, index=True)  # スレッドID
    message_id: Optional[str] = Field(default=None, index=True)  # Message-ID ヘッダー
    in_reply_to: Optional[str] = Field(default=None)  # In-Reply-To ヘッダー
    references: Optional[str] = Field(default=None)  # References ヘッダー
    
    # リレーション
    sync_job: "EmailSyncJob" = Relationship(back_populates="processed_emails")
    tasks: List["Task"] = Relationship(back_populates="source_email")


class EmailSyncJobStatus(str, Enum):
    """同期ジョブのステータス"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EmailSyncJob(SQLModel, table=True):
    """メール同期ジョブテーブルモデル"""
    __tablename__ = "email_sync_jobs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email_account_id: UUID = Field(foreign_key="email_accounts.id", index=True)
    status: EmailSyncJobStatus = EmailSyncJobStatus.PENDING
    total_emails: int = 0
    processed_emails: int = 0
    error_details: Optional[Dict] = Field(default=None, sa_column_kwargs={"type": "json"})
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # リレーション
    email_account: "EmailAccount" = Relationship(back_populates="sync_jobs")
    processed_emails: List["ProcessedEmail"] = Relationship(back_populates="sync_job")


class ExcludeDomain(SQLModel, table=True):
    """除外ドメインテーブルモデル"""
    __tablename__ = "exclude_domains"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    domain: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # リレーション
    user: "User" = Relationship(back_populates="exclude_domains")