from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# データベースエンジンの作成（同期）
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# 非同期エンジンの作成
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    future=True,
)


def create_db_and_tables():
    """データベースとテーブルを作成する"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """データベースセッションを取得する"""
    with Session(engine) as session:
        yield session

# 非同期セッション用の設定
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_async_session():
    """非同期データベースセッションを取得する"""
    async with AsyncSessionLocal() as session:
        yield session
