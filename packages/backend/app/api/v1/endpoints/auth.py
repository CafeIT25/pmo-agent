from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.deps import get_db
from app.core.security import create_access_token, create_refresh_token
from app.crud.crud_user_async import crud_user
from app.schemas.user import UserCreate, Token

router = APIRouter()

# OAuth2スキーム
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


class TokenData(BaseModel):
    email: str | None = None


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str | None = None


@router.post("/register")
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """新規ユーザー登録"""
    
    # 既存ユーザーチェック
    user = await crud_user.get_by_email(db, email=user_data.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # ユーザー作成
    user_in = UserCreate(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
    )
    user = await crud_user.create(db, obj_in=user_in)
    
    # TODO: 確認メール送信
    
    return {"message": "User created successfully. Please check your email to verify your account."}


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """ログイン"""
    
    # ユーザー認証
    user = await crud_user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # トークン生成
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))
    
    # 最終ログイン時刻を更新
    user.last_login = datetime.utcnow()
    db.add(user)
    await db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=dict)
async def refresh_token_endpoint(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """トークンリフレッシュ"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = await crud_user.get(db, id=user_id)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # 新しいアクセストークンを生成
    access_token = create_access_token(subject=str(user.id))
    
    return {"access_token": access_token}


@router.post("/logout")
async def logout():
    """ログアウト"""
    # TODO: 実装
    return {"message": "Logout successful"}