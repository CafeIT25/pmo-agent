#!/usr/bin/env python3
"""
テストユーザー作成スクリプト
開発環境でのテスト用ユーザーを作成します
"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime

from app.core.database import async_engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.email import EmailAccount
from app.services.oauth_service import OAuthService


async def create_test_users():
    """テスト用ユーザーを作成"""
    oauth_service = OAuthService()
    
    # テストユーザーデータ
    test_users = [
        {
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "テスト ユーザー",
            "is_active": True,
            "is_superuser": False
        },
        {
            "email": "admin@example.com", 
            "password": "adminpass123",
            "full_name": "管理者 ユーザー",
            "is_active": True,
            "is_superuser": True
        },
        {
            "email": "demo@example.com",
            "password": "demopass123", 
            "full_name": "デモ ユーザー",
            "is_active": True,
            "is_superuser": False
        }
    ]
    
    async with AsyncSession(async_engine) as session:
        for user_data in test_users:
            # Check if user already exists
            statement = select(User).where(User.email == user_data["email"])
            result = await session.execute(statement)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"ユーザー {user_data['email']} は既に存在します")
                continue
            
            # Create new user
            user = User(
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                is_active=user_data["is_active"],
                is_superuser=user_data["is_superuser"],
                email_verified=True,  # テスト用なので既に確認済みとする
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            print(f"ユーザー作成完了: {user.email}")
            
            # Create mock email account for test user
            if user.email == "test@example.com":
                # Create mock Gmail account
                email_account = EmailAccount(
                    user_id=user.id,
                    email=user.email,
                    provider="google",
                    refresh_token=oauth_service.encrypt_token("mock_refresh_token_google"),
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                session.add(email_account)
                await session.commit()
                print(f"  - Gmail連携設定を追加しました")
                
            elif user.email == "demo@example.com":
                # Create mock Outlook account  
                email_account = EmailAccount(
                    user_id=user.id,
                    email=user.email,
                    provider="microsoft",
                    refresh_token=oauth_service.encrypt_token("mock_refresh_token_microsoft"),
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                session.add(email_account)
                await session.commit()
                print(f"  - Outlook連携設定を追加しました")
    
    print("\n=== テストユーザー情報 ===")
    print("1. 一般ユーザー")
    print("   Email: test@example.com")
    print("   Password: testpass123")
    print("   備考: Gmail連携済み (モック)")
    print("")
    print("2. 管理者ユーザー") 
    print("   Email: admin@example.com")
    print("   Password: adminpass123")
    print("   備考: 管理者権限あり")
    print("")
    print("3. デモユーザー")
    print("   Email: demo@example.com")
    print("   Password: demopass123")
    print("   備考: Outlook連携済み (モック)")
    print("========================")


if __name__ == "__main__":
    asyncio.run(create_test_users())