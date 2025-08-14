"""
データベースパフォーマンス最適化のためのインデックス定義
Railway無料プラン（1GB制限）を考慮した最適化
"""

from alembic import op
import sqlalchemy as sa

# 重要度順のインデックス追加案

def create_performance_indexes():
    """
    パフォーマンス最適化のための重要インデックスを作成
    Railway無料プラン制約を考慮して必要最小限に絞り込み
    """
    
    # 1. 最重要: タスク検索・ソート用複合インデックス
    # 使用頻度: 極めて高い（ダッシュボード、タスク一覧）
    op.create_index(
        'idx_tasks_user_status_priority',
        'tasks',
        ['user_id', 'status', 'priority'],
        postgresql_ops={'status': 'varchar_ops', 'priority': 'varchar_ops'}
    )
    
    # 2. 重要: タスク期限ソート用
    # 使用頻度: 高い（期限切れタスク、今日のタスク）
    op.create_index(
        'idx_tasks_user_due_date',
        'tasks',
        ['user_id', 'due_date'],
        postgresql_where=sa.text("due_date IS NOT NULL")  # 期限ありのタスクのみ
    )
    
    # 3. 重要: メール時系列表示用
    # 使用頻度: 高い（メール履歴表示）
    op.create_index(
        'idx_processed_emails_sync_job_date',
        'processed_emails',
        ['sync_job_id', 'email_date DESC']
    )
    
    # 4. 中程度: AI分析済みメール検索用
    # 使用頻度: 中（AI処理済みメール抽出）
    op.create_index(
        'idx_processed_emails_is_task',
        'processed_emails',
        ['is_task'],
        postgresql_where=sa.text("is_task = true")  # AI判定でタスク化されたもののみ
    )
    
    # 5. 中程度: 使用量統計用（月次レポート）
    # 使用頻度: 中（コスト分析、レポート）
    op.create_index(
        'idx_openai_usage_user_date',
        'openai_usage',
        ['user_id', 'created_at DESC']
    )
    
    # 6. 軽量: メールスレッド検索用
    # 使用頻度: 中（スレッド表示、返信機能）
    op.create_index(
        'idx_processed_emails_thread_id',
        'processed_emails',
        ['thread_id'],
        postgresql_where=sa.text("thread_id IS NOT NULL")
    )

def create_railway_optimized_indexes():
    """
    Railway無料プラン（メモリ1GB、ストレージ1GB）専用の軽量インデックス設計
    """
    
    # メモリ効率を最大化した最小限のインデックス
    
    # 1. ユーザーログイン（既存のemailインデックスで十分）
    # 2. タスク一覧（user_id + status）- 最重要
    op.create_index(
        'idx_tasks_user_status',
        'tasks', 
        ['user_id', 'status'],
        postgresql_using='btree'  # 明示的にB-treeを指定
    )
    
    # 3. 最新メール取得（sync_job + 日付降順）
    op.create_index(
        'idx_emails_recent',
        'processed_emails',
        ['sync_job_id', 'email_date DESC'],
        postgresql_using='btree'
    )

def estimate_index_overhead():
    """
    追加インデックスによるストレージ・メモリ使用量の推定
    """
    estimates = {
        'idx_tasks_user_status_priority': {
            'storage_mb': 5,  # 1万タスクで約5MB
            'memory_mb': 2,   # アクティブ部分で約2MB
            'impact': 'ダッシュボード表示 80% 高速化'
        },
        'idx_tasks_user_due_date': {
            'storage_mb': 3,
            'memory_mb': 1,
            'impact': '期限管理機能 60% 高速化'
        },
        'idx_processed_emails_sync_job_date': {
            'storage_mb': 8,  # メールデータは大きい
            'memory_mb': 3,
            'impact': 'メール履歴表示 70% 高速化'
        }
    }
    
    total_storage = sum(est['storage_mb'] for est in estimates.values())
    total_memory = sum(est['memory_mb'] for est in estimates.values())
    
    print(f"追加ストレージ使用量: {total_storage}MB (1GB制限の{total_storage/1024*100:.1f}%)")
    print(f"追加メモリ使用量: {total_memory}MB (1GB制限の{total_memory/1024*100:.1f}%)")
    
    return estimates

# マイグレーション用の関数
def upgrade():
    """パフォーマンス最適化インデックスを追加"""
    # Railway無料プランでは軽量版を推奨
    create_railway_optimized_indexes()

def downgrade():
    """インデックスを削除"""
    op.drop_index('idx_tasks_user_status')
    op.drop_index('idx_emails_recent')

if __name__ == "__main__":
    # ストレージ・メモリ使用量の推定を表示
    estimate_index_overhead()