from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, tasks, email, ai, oauth, cost, chat

api_router = APIRouter()

# 各エンドポイントのルーターを登録
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(email.router, prefix="/email", tags=["email"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["oauth"])
api_router.include_router(cost.router, prefix="/cost", tags=["cost"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])