"""
キャッシュサービス
Redis を使用した効率的なキャッシュ管理
"""
import redis
import json
from typing import Optional, Any
from app.core.config import settings


class CacheService:
    """Redisキャッシュサービス"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True
        )
        
    async def get(self, key: str) -> Optional[str]:
        """キャッシュから値を取得"""
        try:
            return self.redis_client.get(key)
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        expire: int = 3600
    ) -> bool:
        """キャッシュに値を設定"""
        try:
            return self.redis_client.setex(key, expire, value)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """キャッシュから削除"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """キーの存在確認"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False