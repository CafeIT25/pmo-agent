from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

router = APIRouter()


class User(BaseModel):
    id: str
    email: str
    name: str | None = None


class EmailAccount(BaseModel):
    id: str
    provider: str
    email: str
    is_active: bool


class ExcludeDomain(BaseModel):
    id: str
    domain: str


@router.get("/me", response_model=User)
async def get_current_user():
    """現在のユーザー情報取得"""
    # TODO: 実装
    return User(
        id="dummy_id",
        email="user@example.com",
        name="Test User",
    )


@router.put("/me", response_model=User)
async def update_current_user(name: str | None = None, timezone: str | None = None):
    """ユーザー情報更新"""
    # TODO: 実装
    return User(
        id="dummy_id",
        email="user@example.com",
        name=name or "Test User",
    )


@router.get("/me/email-accounts", response_model=List[EmailAccount])
async def get_email_accounts():
    """メールアカウント一覧取得"""
    # TODO: 実装
    return []


@router.post("/me/email-accounts", response_model=EmailAccount)
async def connect_email_account(provider: str, auth_code: str):
    """メールアカウント連携"""
    # TODO: 実装
    return EmailAccount(
        id="dummy_account_id",
        provider=provider,
        email="connected@example.com",
        is_active=True,
    )


@router.delete("/me/email-accounts/{account_id}")
async def disconnect_email_account(account_id: str):
    """メールアカウント連携解除"""
    # TODO: 実装
    return {"message": "Email account disconnected"}


@router.get("/me/exclude-domains", response_model=List[ExcludeDomain])
async def get_exclude_domains():
    """除外ドメイン一覧取得"""
    # TODO: 実装
    return []


@router.post("/me/exclude-domains", response_model=ExcludeDomain)
async def add_exclude_domain(domain: str):
    """除外ドメイン追加"""
    # TODO: 実装
    return ExcludeDomain(
        id="dummy_domain_id",
        domain=domain,
    )


@router.delete("/me/exclude-domains/{domain_id}")
async def remove_exclude_domain(domain_id: str):
    """除外ドメイン削除"""
    # TODO: 実装
    return {"message": "Domain removed from exclusion list"}