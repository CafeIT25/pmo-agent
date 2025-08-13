import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
from cryptography.fernet import Fernet

from app.core.config import settings


class OAuthService:
    """OAuth service for managing tokens"""
    
    def __init__(self):
        self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt sensitive token"""
        return self.fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token"""
        return self.fernet.decrypt(encrypted_token.encode()).decode()
    
    async def refresh_token(self, refresh_token: str, provider: str) -> Dict[str, Any]:
        """
        Refresh OAuth access token
        
        Args:
            refresh_token: Encrypted refresh token
            provider: OAuth provider (google/microsoft)
            
        Returns:
            Dict with new access token and expiry
        """
        # Decrypt refresh token
        decrypted_token = self.decrypt_token(refresh_token)
        
        if provider == "google":
            return await self._refresh_google_token(decrypted_token)
        elif provider == "microsoft":
            return await self._refresh_microsoft_token(decrypted_token)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def _refresh_google_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Google OAuth token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "access_token": data["access_token"],
                "expires_in": data["expires_in"],
                "expires_at": (datetime.utcnow() + timedelta(seconds=data["expires_in"])).isoformat()
            }
    
    async def _refresh_microsoft_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Microsoft OAuth token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "client_id": settings.MICROSOFT_CLIENT_ID,
                    "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "scope": "https://graph.microsoft.com/.default"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "access_token": data["access_token"],
                "expires_in": data["expires_in"],
                "expires_at": (datetime.utcnow() + timedelta(seconds=data["expires_in"])).isoformat()
            }
    
    async def exchange_code(
        self,
        code: str,
        provider: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens
        
        Args:
            code: Authorization code
            provider: OAuth provider
            redirect_uri: Redirect URI used in authorization
            
        Returns:
            Dict with access and refresh tokens
        """
        if provider == "google":
            return await self._exchange_google_code(code, redirect_uri)
        elif provider == "microsoft":
            return await self._exchange_microsoft_code(code, redirect_uri)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def _exchange_google_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange Google authorization code"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Get user info
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {data['access_token']}"}
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            return {
                "access_token": data["access_token"],
                "refresh_token": self.encrypt_token(data["refresh_token"]),
                "expires_in": data["expires_in"],
                "email": user_data["email"],
                "name": user_data.get("name", ""),
                "provider": "google"
            }
    
    async def _exchange_microsoft_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange Microsoft authorization code"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "client_id": settings.MICROSOFT_CLIENT_ID,
                    "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                    "scope": "openid email profile https://graph.microsoft.com/Mail.Read"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Get user info
            user_response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {data['access_token']}"}
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            return {
                "access_token": data["access_token"],
                "refresh_token": self.encrypt_token(data["refresh_token"]),
                "expires_in": data["expires_in"],
                "email": user_data["mail"] or user_data["userPrincipalName"],
                "name": user_data.get("displayName", ""),
                "provider": "microsoft"
            }