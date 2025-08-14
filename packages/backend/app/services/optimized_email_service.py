"""
高パフォーマンス メール処理サービス

Gmail N+1問題を解決し、Railway無料プランで最高のパフォーマンスを実現する
最適化されたメール同期サービス
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Set
from urllib.parse import urlencode

import httpx
import redis.asyncio as redis
from fastapi import HTTPException

from app.core.config import settings
from app.services.oauth_service import OAuthService
from app.services.cache_service import CacheService
from app.models.email import ProcessedEmail
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """サーキットブレーカー実装"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """実行可能かチェック"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if datetime.now().timestamp() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """成功記録"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """失敗記録"""
        self.failure_count += 1
        self.last_failure_time = datetime.now().timestamp()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class GmailBatchService:
    """Gmail API バッチリクエストサービス"""
    
    def __init__(self):
        self.batch_size = getattr(settings, 'GMAIL_BATCH_SIZE', 20)
        self.max_concurrent_batches = getattr(settings, 'GMAIL_MAX_CONCURRENT_BATCHES', 3)
        self.fields = getattr(
            settings, 
            'GMAIL_FIELDS', 
            'id,threadId,labelIds,snippet,payload/headers,internalDate'
        )
    
    async def fetch_messages_batch(
        self, 
        message_ids: List[str], 
        access_token: str
    ) -> List[Dict]:
        """バッチリクエストでメッセージ詳細を効率取得"""
        
        if not message_ids:
            return []
        
        # バッチサイズでグループ化
        batches = [
            message_ids[i:i + self.batch_size] 
            for i in range(0, len(message_ids), self.batch_size)
        ]
        
        # 並行バッチ処理（制限付き）
        semaphore = asyncio.Semaphore(self.max_concurrent_batches)
        
        async def process_batch(batch):
            async with semaphore:
                return await self._execute_batch(batch, access_token)
        
        tasks = [process_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果統合とエラーハンドリング
        messages = []
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"Batch {i} failed: {result}")
                # 個別リクエストでフォールバック
                fallback_messages = await self._fallback_individual_requests(
                    batches[i], access_token
                )
                messages.extend(fallback_messages)
            else:
                messages.extend(result)
        
        return messages
    
    async def _execute_batch(
        self, 
        message_ids: List[str], 
        access_token: str
    ) -> List[Dict]:
        """単一バッチリクエストの実行"""
        
        boundary = f"batch_{uuid.uuid4().hex}"
        batch_body = self._build_batch_body(message_ids, boundary)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": f"multipart/mixed; boundary={boundary}",
            "Accept": "application/json"
        }
        
        timeout = httpx.Timeout(30.0, read=45.0)  # バッチ用に延長
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    "https://www.googleapis.com/batch/gmail/v1",
                    content=batch_body,
                    headers=headers
                )
                response.raise_for_status()
                
                return self._parse_batch_response(response.content, boundary)
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # レート制限の場合
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    raise
                logger.error(f"HTTP error in batch request: {e}")
                raise
    
    def _build_batch_body(self, message_ids: List[str], boundary: str) -> str:
        """バッチリクエストボディ構築"""
        parts = []
        
        for i, msg_id in enumerate(message_ids):
            part = f"""--{boundary}
Content-Type: application/http
Content-ID: <item{i}>

GET /gmail/v1/users/me/messages/{msg_id}?fields={self.fields}&format=metadata
Host: www.googleapis.com

"""
            parts.append(part)
        
        parts.append(f"--{boundary}--")
        return "\n".join(parts)
    
    def _parse_batch_response(self, response_content: bytes, boundary: str) -> List[Dict]:
        """バッチレスポンスの解析"""
        content = response_content.decode('utf-8')
        parts = content.split(f"--{boundary}")
        
        messages = []
        for part in parts:
            if "HTTP/1.1 200" in part and "{" in part:
                # JSONレスポンス部分を抽出
                json_start = part.find('{')
                if json_start != -1:
                    json_part = part[json_start:].strip()
                    try:
                        message = json.loads(json_part)
                        messages.append(message)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse batch response part: {e}")
        
        return messages
    
    async def _fallback_individual_requests(
        self, 
        message_ids: List[str], 
        access_token: str
    ) -> List[Dict]:
        """個別リクエストでのフォールバック"""
        
        logger.info(f"Falling back to individual requests for {len(message_ids)} messages")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        messages = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for msg_id in message_ids:
                try:
                    response = await client.get(
                        f"https://www.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
                        headers=headers,
                        params={"fields": self.fields, "format": "metadata"}
                    )
                    response.raise_for_status()
                    messages.append(response.json())
                    
                    # レート制限対策
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to fetch message {msg_id}: {e}")
        
        return messages


class IntelligentCacheService:
    """インテリジェントキャッシュサービス"""
    
    def __init__(self):
        self.redis = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        self.cache_ttl = {
            "message_content": getattr(settings, 'CACHE_MESSAGE_TTL', 3600),
            "sync_tokens": getattr(settings, 'CACHE_SYNC_TOKEN_TTL', 86400),
            "user_preferences": 1800
        }
    
    async def get_cached_messages(
        self, 
        message_ids: List[str]
    ) -> Dict[str, Dict]:
        """複数メッセージの一括キャッシュ取得"""
        
        if not message_ids:
            return {}
        
        cache_keys = [f"email:msg:{msg_id}" for msg_id in message_ids]
        
        # Pipeline使用で高速一括取得
        pipe = self.redis.pipeline()
        for key in cache_keys:
            pipe.get(key)
        
        cached_values = await pipe.execute()
        
        # デシリアライズと結果マッピング
        result = {}
        for msg_id, cached_json in zip(message_ids, cached_values):
            if cached_json:
                try:
                    result[msg_id] = json.loads(cached_json)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid cache data for message {msg_id}")
        
        return result
    
    async def cache_messages_batch(
        self, 
        messages: List[Dict]
    ) -> None:
        """メッセージの一括キャッシュ保存"""
        
        if not messages:
            return
        
        pipe = self.redis.pipeline()
        
        for message in messages:
            cache_key = f"email:msg:{message['id']}"
            
            # メッセージデータの軽量化
            cache_data = {
                "id": message["id"],
                "threadId": message.get("threadId"),
                "snippet": message.get("snippet"),
                "internalDate": message.get("internalDate"),
                "headers": self._extract_important_headers(message),
                "cached_at": datetime.utcnow().isoformat()
            }
            
            pipe.setex(
                cache_key,
                self.cache_ttl["message_content"],
                json.dumps(cache_data, default=str)
            )
        
        await pipe.execute()
        logger.info(f"Cached {len(messages)} messages")
    
    def _extract_important_headers(self, message: Dict) -> Dict:
        """重要なヘッダーのみ抽出"""
        headers = {}
        
        payload = message.get("payload", {})
        header_list = payload.get("headers", [])
        
        important_headers = {
            "From", "To", "Subject", "Date", "Message-ID", "In-Reply-To"
        }
        
        for header in header_list:
            name = header.get("name", "")
            if name in important_headers:
                headers[name] = header.get("value", "")
        
        return headers
    
    async def filter_uncached_messages(
        self, 
        message_ids: List[str]
    ) -> List[str]:
        """キャッシュされていないメッセージIDを抽出"""
        
        cached_messages = await self.get_cached_messages(message_ids)
        cached_ids = set(cached_messages.keys())
        
        uncached_ids = [
            msg_id for msg_id in message_ids 
            if msg_id not in cached_ids
        ]
        
        logger.info(
            f"Cache hit: {len(cached_ids)}/{len(message_ids)} messages. "
            f"Need to fetch: {len(uncached_ids)}"
        )
        
        return uncached_ids
    
    async def get_sync_token(self, account_id: str) -> Optional[str]:
        """同期トークンの取得"""
        return await self.redis.get(f"email:sync_token:{account_id}")
    
    async def set_sync_token(self, account_id: str, token: str) -> None:
        """同期トークンの保存"""
        await self.redis.setex(
            f"email:sync_token:{account_id}",
            self.cache_ttl["sync_tokens"],
            token
        )


class OptimizedEmailSyncService:
    """最適化されたメール同期サービス"""
    
    def __init__(self):
        self.gmail_batch = GmailBatchService()
        self.cache_service = IntelligentCacheService()
        self.oauth_service = OAuthService()
        self.circuit_breaker = CircuitBreaker()
        
        # パフォーマンス設定
        self.max_retries = 3
        self.backoff_factor = getattr(settings, 'RATE_LIMIT_BACKOFF_FACTOR', 2)
        self.max_sync_duration = getattr(settings, 'MAX_SYNC_DURATION', 300)
    
    async def sync_gmail_optimized(
        self, 
        account_id: str, 
        user_id: str
    ) -> Dict:
        """最適化されたGmail同期"""
        
        start_time = datetime.utcnow()
        
        try:
            # サーキットブレーカーチェック
            if not self.circuit_breaker.can_execute():
                raise HTTPException(
                    status_code=503, 
                    detail="Gmail sync temporarily unavailable"
                )
            
            # アクセストークン取得
            access_token = await self._get_fresh_access_token(account_id)
            
            # 1. 増分同期トークンチェック
            last_token = await self.cache_service.get_sync_token(account_id)
            
            if last_token:
                # 増分同期（変更分のみ）
                message_list = await self._fetch_gmail_incremental(
                    access_token, last_token
                )
            else:
                # 初回同期（直近100件）
                message_list = await self._fetch_gmail_initial(access_token)
            
            if not message_list.get("messages"):
                return {
                    "status": "no_new_messages", 
                    "count": 0,
                    "duration": (datetime.utcnow() - start_time).total_seconds()
                }
            
            messages = message_list["messages"]
            message_ids = [msg["id"] for msg in messages]
            
            logger.info(f"Found {len(message_ids)} new messages for user {user_id}")
            
            # 2. キャッシュチェック（重複排除）
            uncached_ids = await self.cache_service.filter_uncached_messages(message_ids)
            
            detailed_messages = []
            
            if uncached_ids:
                # 3. バッチリクエストで詳細取得
                logger.info(f"Fetching details for {len(uncached_ids)} uncached messages")
                
                new_detailed_messages = await self.gmail_batch.fetch_messages_batch(
                    uncached_ids, access_token
                )
                
                # 4. キャッシュ更新
                await self.cache_service.cache_messages_batch(new_detailed_messages)
                detailed_messages.extend(new_detailed_messages)
            
            # 5. キャッシュされたメッセージも取得
            if len(uncached_ids) < len(message_ids):
                cached_messages = await self.cache_service.get_cached_messages(
                    [mid for mid in message_ids if mid not in uncached_ids]
                )
                detailed_messages.extend(cached_messages.values())
            
            # 6. 次回同期用トークン保存
            if "historyId" in message_list:
                await self.cache_service.set_sync_token(
                    account_id, message_list["historyId"]
                )
            
            # 7. メッセージ処理
            result = await self._process_messages(detailed_messages, user_id, account_id)
            
            # 成功記録
            self.circuit_breaker.record_success()
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Gmail sync completed for user {user_id}: "
                f"{len(detailed_messages)} messages in {duration:.2f}s"
            )
            
            return {
                "status": "success",
                "count": len(detailed_messages),
                "duration": duration,
                "cached_count": len(message_ids) - len(uncached_ids),
                "api_calls": len(uncached_ids) // self.gmail_batch.batch_size + 1
            }
            
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Gmail sync failed for user {user_id}: {e}")
            raise
    
    async def _fetch_gmail_initial(self, access_token: str) -> Dict:
        """Gmail初回同期（直近メッセージ取得）"""
        
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "maxResults": 100,
            "q": "in:inbox OR in:sent",  # 受信・送信両方
            "fields": "messages/id,messages/threadId,nextPageToken,resultSizeEstimate"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://www.googleapis.com/gmail/v1/users/me/messages",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def _fetch_gmail_incremental(
        self, 
        access_token: str, 
        history_id: str
    ) -> Dict:
        """Gmail増分同期（履歴ベース）"""
        
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "startHistoryId": history_id,
            "historyTypes": ["messageAdded", "messageDeleted"],
            "fields": "history,historyId,nextPageToken"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://www.googleapis.com/gmail/v1/users/me/history",
                headers=headers,
                params=params
            )
            
            if response.status_code == 404:
                # 履歴が古すぎる場合は初回同期に切り替え
                logger.warning("History ID too old, falling back to initial sync")
                return await self._fetch_gmail_initial(access_token)
            
            response.raise_for_status()
            history_data = response.json()
            
            # 履歴から新しいメッセージを抽出
            messages = []
            for history_record in history_data.get("history", []):
                for added in history_record.get("messagesAdded", []):
                    messages.append(added["message"])
            
            return {
                "messages": messages,
                "historyId": history_data.get("historyId")
            }
    
    async def _get_fresh_access_token(self, account_id: str) -> str:
        """新しいアクセストークンの取得"""
        
        # OAuthサービスからトークン取得
        token_data = await self.oauth_service.get_valid_token(account_id)
        
        if not token_data:
            raise HTTPException(
                status_code=401,
                detail="Gmail account not connected or token expired"
            )
        
        return token_data["access_token"]
    
    async def _process_messages(
        self, 
        messages: List[Dict], 
        user_id: str, 
        account_id: str
    ) -> Dict:
        """メッセージの処理とデータベース保存"""
        
        if not messages:
            return {"processed": 0, "threads": 0}
        
        # スレッドごとにグループ化
        thread_groups = {}
        processed_count = 0
        
        async with AsyncSessionLocal() as db:
            for message in messages:
                thread_id = message.get("threadId") or message["id"]
                
                # 既に処理済みかチェック
                existing = await db.execute(
                    "SELECT id FROM processed_emails WHERE message_id = :msg_id",
                    {"msg_id": message["id"]}
                )
                
                if existing.first():
                    continue  # 重複スキップ
                
                # ProcessedEmailとして保存
                processed_email = ProcessedEmail(
                    message_id=message["id"],
                    thread_id=thread_id,
                    user_id=user_id,
                    account_id=account_id,
                    subject=self._extract_subject(message),
                    sender=self._extract_sender(message),
                    received_at=self._parse_internal_date(message.get("internalDate")),
                    snippet=message.get("snippet", ""),
                    raw_data=message
                )
                
                db.add(processed_email)
                processed_count += 1
                
                # スレッドグループに追加
                if thread_id not in thread_groups:
                    thread_groups[thread_id] = []
                thread_groups[thread_id].append(message)
            
            await db.commit()
        
        # スレッド単位でAI分析タスクをキューに追加
        from app.worker.tasks.email import analyze_email_thread_for_tasks
        
        for thread_id, thread_messages in thread_groups.items():
            analyze_email_thread_for_tasks.delay(
                thread_messages, user_id, account_id
            )
        
        return {
            "processed": processed_count,
            "threads": len(thread_groups)
        }
    
    def _extract_subject(self, message: Dict) -> str:
        """件名の抽出"""
        headers = message.get("payload", {}).get("headers", [])
        for header in headers:
            if header.get("name", "").lower() == "subject":
                return header.get("value", "")
        return ""
    
    def _extract_sender(self, message: Dict) -> str:
        """送信者の抽出"""
        headers = message.get("payload", {}).get("headers", [])
        for header in headers:
            if header.get("name", "").lower() == "from":
                return header.get("value", "")
        return ""
    
    def _parse_internal_date(self, internal_date: str) -> Optional[datetime]:
        """内部日付の解析"""
        if not internal_date:
            return None
        
        try:
            # Gmail内部日付はミリ秒単位のUnixタイムスタンプ
            timestamp = int(internal_date) / 1000
            return datetime.utcfromtimestamp(timestamp)
        except (ValueError, TypeError):
            return None


class PerformanceMonitor:
    """パフォーマンス監視サービス"""
    
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
    
    async def track_sync_performance(
        self,
        provider: str,
        user_id: str,
        message_count: int,
        duration: float,
        api_calls: int,
        cached_count: int = 0
    ):
        """同期パフォーマンスの追跡"""
        
        metrics = {
            "provider": provider,
            "user_id": user_id,
            "message_count": str(message_count),
            "duration": str(round(duration, 2)),
            "api_calls": str(api_calls),
            "cached_count": str(cached_count),
            "messages_per_second": str(round(message_count / duration if duration > 0 else 0, 2)),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Redis Streams でメトリクス記録
        await self.redis.xadd(
            f"email_sync_metrics:{provider}", 
            metrics, 
            maxlen=1000
        )
        
        # パフォーマンス異常検知
        if duration > 60:  # 60秒超過の場合
            await self._alert_performance_issue(provider, metrics)
        
        logger.info(
            f"Sync metrics - {provider}: {message_count} messages, "
            f"{duration:.2f}s, {api_calls} API calls, "
            f"{cached_count} cached"
        )
    
    async def _alert_performance_issue(self, provider: str, metrics: Dict):
        """パフォーマンス問題のアラート"""
        logger.warning(
            f"Performance issue detected for {provider}: "
            f"{metrics['duration']}s for {metrics['message_count']} messages"
        )
        
        # 将来的にSlack/Discord通知などを追加可能