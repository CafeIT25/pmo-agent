from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4


class UserBase(SQLModel):
    """ユーザーの基本情報"""
    email: str = Field(unique=True, index=True)
    name: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False


class User(UserBase, table=True):
    """ユーザーテーブルモデル"""
    __tablename__ = "users"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    
    # リレーション
    email_accounts: List["EmailAccount"] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="user")
    exclude_domains: List["ExcludeDomain"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    """ユーザー作成用スキーマ"""
    password: str


class UserUpdate(SQLModel):
    """ユーザー更新用スキーマ"""
    name: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """データベース内のユーザー情報"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class UserOut(UserBase):
    """ユーザー情報の出力用スキーマ"""
    id: UUID