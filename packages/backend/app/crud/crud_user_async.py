from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """メールアドレスでユーザーを取得"""
        statement = select(User).where(User.email == email)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """ユーザーを作成"""
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_active=obj_in.is_active,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Optional[User]:
        """ユーザー認証"""
        user = await self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def get(self, db: AsyncSession, *, id: str) -> Optional[User]:
        """IDでユーザーを取得"""
        statement = select(User).where(User.id == id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()


crud_user = CRUDUser(User)