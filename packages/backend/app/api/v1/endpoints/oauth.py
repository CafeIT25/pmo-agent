from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from typing import Optional
from datetime import datetime, timedelta
import jwt

from app.core.config import settings
from app.core.database import get_db
from app.services.oauth_service import OAuthService
from app.crud.crud_email import crud_email
from app.crud.crud_user_async import crud_user
from app.schemas.user import UserCreate


router = APIRouter()


@router.get("/google/authorize")
async def google_authorize(
    redirect_uri: str = Query(..., description="OAuth redirect URI")
):
    """Google OAuth認証開始"""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile https://www.googleapis.com/auth/gmail.readonly",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code"),
    redirect_uri: str = Query(..., description="OAuth redirect URI")
):
    """Google OAuth コールバック処理"""
    oauth_service = OAuthService()
    
    try:
        # Exchange code for tokens
        token_data = await oauth_service.exchange_code(
            code=code,
            provider="google",
            redirect_uri=redirect_uri
        )
        
        async with get_db() as db:
            # Check if user exists
            user = await crud_user.get_by_email(db, email=token_data["email"])
            
            if not user:
                # Create new user
                user = await crud_user.create(
                    db,
                    obj_in=UserCreate(
                        email=token_data["email"],
                        full_name=token_data["name"],
                        is_active=True,
                        password="oauth_user"  # Placeholder for OAuth users
                    )
                )
            
            # Create or update email account
            email_account = await crud_email.create_email_account(
                db,
                account_data={
                    "user_id": str(user.id),
                    "email": token_data["email"],
                    "provider": "google",
                    "refresh_token": token_data["refresh_token"],
                    "is_active": True
                }
            )
            
            # Generate JWT token for the user
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(user.id)},
                expires_delta=access_token_expires
            )
            
            # Redirect to frontend with token
            frontend_url = "http://localhost:3000"  # TODO: Get from settings
            return RedirectResponse(
                url=f"{frontend_url}/auth/callback?token={access_token}&email={user.email}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/microsoft/authorize")
async def microsoft_authorize(
    redirect_uri: str = Query(..., description="OAuth redirect URI")
):
    """Microsoft OAuth認証開始"""
    params = {
        "client_id": settings.MICROSOFT_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile offline_access https://graph.microsoft.com/Mail.Read",
        "response_mode": "query"
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{query_string}"
    
    return RedirectResponse(url=auth_url)


@router.get("/microsoft/callback")
async def microsoft_callback(
    code: str = Query(..., description="Authorization code"),
    redirect_uri: str = Query(..., description="OAuth redirect URI")
):
    """Microsoft OAuth コールバック処理"""
    oauth_service = OAuthService()
    
    try:
        # Exchange code for tokens
        token_data = await oauth_service.exchange_code(
            code=code,
            provider="microsoft",
            redirect_uri=redirect_uri
        )
        
        async with get_db() as db:
            # Check if user exists
            user = await crud_user.get_by_email(db, email=token_data["email"])
            
            if not user:
                # Create new user
                user = await crud_user.create(
                    db,
                    obj_in=UserCreate(
                        email=token_data["email"],
                        full_name=token_data["name"],
                        is_active=True,
                        password="oauth_user"  # Placeholder for OAuth users
                    )
                )
            
            # Create or update email account
            email_account = await crud_email.create_email_account(
                db,
                account_data={
                    "user_id": str(user.id),
                    "email": token_data["email"],
                    "provider": "microsoft",
                    "refresh_token": token_data["refresh_token"],
                    "is_active": True
                }
            )
            
            # Generate JWT token for the user
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(user.id)},
                expires_delta=access_token_expires
            )
            
            # Redirect to frontend with token
            frontend_url = "http://localhost:3000"  # TODO: Get from settings
            return RedirectResponse(
                url=f"{frontend_url}/auth/callback?token={access_token}&email={user.email}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt