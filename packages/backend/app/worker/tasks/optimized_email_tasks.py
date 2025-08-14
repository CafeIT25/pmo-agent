"""
最適化されたメール処理Celeryタスク

高パフォーマンスでエラー耐性のあるメール同期とAI分析タスク
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from celery import Task

from app.worker.celery_app import celery_app
from app.services.optimized_email_service import (
    OptimizedEmailSyncService,
    PerformanceMonitor
)
from app.services.ai_service import AIService
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)


class OptimizedEmailSyncTask(Task):
    """最適化されたメール同期タスク基底クラス"""
    
    def __init__(self):
        self.email_service = None
        self.performance_monitor = None
    
    def __call__(self, *args, **kwargs):
        """タスク実行時にサービスインスタンスを初期化"""
        if not self.email_service:
            self.email_service = OptimizedEmailSyncService()
            self.performance_monitor = PerformanceMonitor()
        
        return super().__call__(*args, **kwargs)


@celery_app.task(
    bind=True,
    base=OptimizedEmailSyncTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    name='optimized_email_sync'
)
def optimized_email_sync(
    self, 
    account_id: str, 
    user_id: str, 
    provider: str = "gmail"
) -> Dict[str, Any]:
    """
    最適化されたメール同期タスク
    
    Args:
        account_id: メールアカウントID
        user_id: ユーザーID
        provider: プロバイダー（gmail/outlook）
    
    Returns:
        同期結果の辞書
    """
    
    start_time = datetime.utcnow()
    
    try:
        # 進捗状態の更新
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': 100,
                'status': f'Starting {provider} sync...',
                'provider': provider
            }
        )
        
        # 非同期関数を同期実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if provider.lower() == "gmail":
                result = loop.run_until_complete(
                    self.email_service.sync_gmail_optimized(account_id, user_id)
                )
            else:
                # Outlook同期は将来実装
                raise NotImplementedError(f"Provider {provider} not yet implemented")
            
            # 進捗状態の更新
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': 80,
                    'total': 100,
                    'status': 'Processing messages...',
                    'message_count': result.get('count', 0)
                }
            )
            
            # パフォーマンス監視
            loop.run_until_complete(
                self.performance_monitor.track_sync_performance(
                    provider=provider,
                    user_id=user_id,
                    message_count=result.get('count', 0),
                    duration=result.get('duration', 0),
                    api_calls=result.get('api_calls', 0),
                    cached_count=result.get('cached_count', 0)
                )
            )
            
            # 最終状態更新
            self.update_state(
                state='SUCCESS',
                meta={
                    'current': 100,
                    'total': 100,
                    'status': 'Sync completed successfully',
                    'result': result
                }
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Optimized {provider} sync completed for user {user_id}: "
                f"{result.get('count', 0)} messages in {duration:.2f}s"
            )
            
            return {
                **result,
                'task_duration': duration,
                'provider': provider,
                'optimization': 'enabled'
            }
            
        finally:
            loop.close()
    
    except Exception as e:
        # エラー状態の更新
        self.update_state(
            state='FAILURE',
            meta={
                'current': 0,
                'total': 100,
                'status': f'Sync failed: {str(e)}',
                'error': str(e),
                'provider': provider
            }
        )
        
        logger.error(
            f"Optimized {provider} sync failed for user {user_id}: {e}",
            exc_info=True
        )
        
        raise


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    name='optimized_ai_thread_analysis'
)
def optimized_ai_thread_analysis(
    self,
    thread_messages: List[Dict],
    user_id: str,
    account_id: str
) -> Dict[str, Any]:
    """
    最適化されたAIスレッド分析タスク
    
    Args:
        thread_messages: スレッド内のメッセージリスト
        user_id: ユーザーID
        account_id: アカウントID
    
    Returns:
        分析結果の辞書
    """
    
    start_time = datetime.utcnow()
    
    try:
        # 進捗状態の更新
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 0,
                'total': 100,
                'status': f'Analyzing {len(thread_messages)} messages...',
                'message_count': len(thread_messages)
            }
        )
        
        # AIサービス初期化
        ai_service = AIService()
        task_service = TaskService()
        
        # 非同期関数を同期実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 進捗更新
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': 20,
                    'total': 100,
                    'status': 'Sending to AI for analysis...'
                }
            )
            
            # スレッド全体をまとめてAI分析
            thread_analysis = loop.run_until_complete(
                ai_service.analyze_email_thread_optimized(
                    emails=thread_messages,
                    context={
                        'user_id': user_id,
                        'account_id': account_id,
                        'optimization_enabled': True
                    }
                )
            )
            
            # 進捗更新
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': 60,
                    'total': 100,
                    'status': 'Processing AI analysis results...'
                }
            )
            
            # AI判定結果に基づいてタスク作成
            task_created = False
            task_id = None
            
            if thread_analysis.get('should_create_task', False):
                task_result = loop.run_until_complete(
                    task_service.create_from_email_thread_optimized(
                        user_id=user_id,
                        thread_emails=thread_messages,
                        ai_analysis=thread_analysis,
                        account_id=account_id
                    )
                )
                task_created = True
                task_id = task_result.get('task_id')
            
            # 進捗更新
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': 90,
                    'total': 100,
                    'status': 'Finalizing analysis...'
                }
            )
            
            # 処理済みマークを各メールに設定
            for email in thread_messages:
                loop.run_until_complete(
                    _mark_email_as_analyzed(email['id'], user_id)
                )
            
            # 最終状態更新
            self.update_state(
                state='SUCCESS',
                meta={
                    'current': 100,
                    'total': 100,
                    'status': 'Analysis completed successfully',
                    'task_created': task_created,
                    'task_id': task_id
                }
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'analyzed_messages': len(thread_messages),
                'task_created': task_created,
                'task_id': task_id,
                'analysis_duration': duration,
                'ai_confidence': thread_analysis.get('confidence', 0.0),
                'ai_reasoning': thread_analysis.get('reasoning', ''),
                'optimization': 'enabled'
            }
            
            logger.info(
                f"Optimized AI analysis completed for user {user_id}: "
                f"{len(thread_messages)} messages, task_created={task_created}, "
                f"duration={duration:.2f}s"
            )
            
            return result
            
        finally:
            loop.close()
    
    except Exception as e:
        # エラー状態の更新
        self.update_state(
            state='FAILURE',
            meta={
                'current': 0,
                'total': 100,
                'status': f'Analysis failed: {str(e)}',
                'error': str(e),
                'message_count': len(thread_messages)
            }
        )
        
        logger.error(
            f"Optimized AI analysis failed for user {user_id}: {e}",
            exc_info=True
        )
        
        raise


@celery_app.task(name='batch_email_sync')
def batch_email_sync(user_accounts: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    複数アカウントの一括同期タスク
    
    Args:
        user_accounts: [{"user_id": "...", "account_id": "...", "provider": "..."}]
    
    Returns:
        一括同期結果
    """
    
    start_time = datetime.utcnow()
    total_accounts = len(user_accounts)
    
    logger.info(f"Starting batch sync for {total_accounts} accounts")
    
    # 結果収集
    results = []
    successful_syncs = 0
    failed_syncs = 0
    
    for i, account_info in enumerate(user_accounts):
        try:
            user_id = account_info['user_id']
            account_id = account_info['account_id']
            provider = account_info.get('provider', 'gmail')
            
            # 個別同期タスクを実行
            sync_result = optimized_email_sync.apply(
                args=[account_id, user_id, provider],
                timeout=300  # 5分タイムアウト
            )
            
            if sync_result.successful():
                successful_syncs += 1
                results.append({
                    'user_id': user_id,
                    'account_id': account_id,
                    'status': 'success',
                    'result': sync_result.result
                })
            else:
                failed_syncs += 1
                results.append({
                    'user_id': user_id,
                    'account_id': account_id,
                    'status': 'failed',
                    'error': str(sync_result.result)
                })
                
        except Exception as e:
            failed_syncs += 1
            results.append({
                'user_id': account_info.get('user_id', 'unknown'),
                'account_id': account_info.get('account_id', 'unknown'),
                'status': 'error',
                'error': str(e)
            })
            
            logger.error(f"Batch sync error for account {account_info}: {e}")
    
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    batch_result = {
        'total_accounts': total_accounts,
        'successful_syncs': successful_syncs,
        'failed_syncs': failed_syncs,
        'batch_duration': duration,
        'average_sync_time': duration / total_accounts if total_accounts > 0 else 0,
        'results': results,
        'optimization': 'enabled'
    }
    
    logger.info(
        f"Batch sync completed: {successful_syncs}/{total_accounts} successful, "
        f"duration={duration:.2f}s"
    )
    
    return batch_result


@celery_app.task(name='cleanup_old_cache')
def cleanup_old_cache() -> Dict[str, Any]:
    """
    古いキャッシュデータのクリーンアップタスク
    
    Returns:
        クリーンアップ結果
    """
    
    start_time = datetime.utcnow()
    
    try:
        from app.services.optimized_email_service import IntelligentCacheService
        
        cache_service = IntelligentCacheService()
        
        # 非同期関数を同期実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 期限切れキャッシュの削除
            deleted_keys = loop.run_until_complete(
                _cleanup_expired_cache(cache_service)
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            result = {
                'deleted_keys': deleted_keys,
                'cleanup_duration': duration,
                'status': 'completed'
            }
            
            logger.info(
                f"Cache cleanup completed: {deleted_keys} keys deleted, "
                f"duration={duration:.2f}s"
            )
            
            return result
            
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}", exc_info=True)
        raise


# ヘルパー関数

async def _mark_email_as_analyzed(message_id: str, user_id: str) -> None:
    """メールを分析済みとしてマーク"""
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        await db.execute(
            "UPDATE processed_emails SET analyzed_at = :analyzed_at "
            "WHERE message_id = :message_id AND user_id = :user_id",
            {
                "analyzed_at": datetime.utcnow(),
                "message_id": message_id,
                "user_id": user_id
            }
        )
        await db.commit()


async def _cleanup_expired_cache(cache_service) -> int:
    """期限切れキャッシュの削除"""
    
    # パターンマッチングで対象キーを取得
    patterns = [
        "email:msg:*",
        "email:sync_token:*"
    ]
    
    deleted_count = 0
    
    for pattern in patterns:
        keys = await cache_service.redis.keys(pattern)
        
        # 期限切れキーの削除
        for key in keys:
            ttl = await cache_service.redis.ttl(key)
            if ttl == -1:  # TTLが設定されていない場合
                await cache_service.redis.delete(key)
                deleted_count += 1
    
    return deleted_count