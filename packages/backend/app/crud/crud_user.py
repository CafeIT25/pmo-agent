from typing import Optional
from sqlmodel import Session, select
from app.crud.base import CRUDBase
from app.models.user import User, UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """ユーザーCRUD操作"""
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """メールアドレスでユーザーを取得"""
        statement = select(User).where(User.email == email)
        return db.exec(statement).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """ユーザーを作成"""
        db_obj = User(
            email=obj_in.email,
            password_hash=get_password_hash(obj_in.password),
            name=obj_in.name,
            is_active=obj_in.is_active,
            is_verified=obj_in.is_verified,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[User]:
        """ユーザー認証"""
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """ユーザーがアクティブか確認"""
        return user.is_active

    def is_verified(self, user: User) -> bool:
        """ユーザーが検証済みか確認"""
        return user.is_verified


crud_user = CRUDUser(User)