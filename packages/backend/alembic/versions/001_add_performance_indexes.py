"""Add performance indexes for Railway optimization

Revision ID: 001_performance_indexes
Revises: 
Create Date: 2025-08-14 04:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001_performance_indexes'
down_revision = None
depends_on = None

def upgrade():
    """
    Railway無料プラン最適化のための最重要インデックスを追加
    ストレージ使用量: ~10MB（1GB制限の1%未満）
    """
    
    # 1. 最重要: タスク検索用複合インデックス
    # 使用頻度: 極めて高い（ダッシュボード、タスク一覧）
    # 期待効果: タスク一覧表示 5倍高速化
    op.create_index(
        'idx_tasks_user_status',
        'tasks',
        ['user_id', 'status'],
        postgresql_using='btree'
    )
    
    # 2. 重要: タスク期限管理用インデックス
    # 使用頻度: 高い（期限切れタスク、今日のタスク）
    # 期待効果: 期限管理機能 3倍高速化
    op.create_index(
        'idx_tasks_user_due_date',
        'tasks',
        ['user_id', 'due_date'],
        postgresql_where=sa.text("due_date IS NOT NULL"),
        postgresql_using='btree'
    )
    
    # 3. 重要: メール時系列表示用インデックス
    # 使用頻度: 高い（メール履歴表示）
    # 期待効果: メール履歴表示 5倍高速化
    op.create_index(
        'idx_processed_emails_sync_date',
        'processed_emails',
        ['sync_job_id', sa.text('email_date DESC')],
        postgresql_using='btree'
    )
    
    # 4. 中程度: AI分析済みメール検索用
    # 使用頻度: 中（AI処理済みメール抽出）
    # 期待効果: AI機能 3倍高速化
    op.create_index(
        'idx_processed_emails_is_task',
        'processed_emails',
        ['is_task'],
        postgresql_where=sa.text("is_task = true"),
        postgresql_using='btree'
    )
    
    # 5. 軽量: メールスレッド検索用
    # 使用頻度: 中（スレッド表示、返信機能）
    # 期待効果: スレッド機能 2倍高速化
    op.create_index(
        'idx_processed_emails_thread_id',
        'processed_emails',
        ['thread_id'],
        postgresql_where=sa.text("thread_id IS NOT NULL"),
        postgresql_using='btree'
    )
    
    # 6. 使用量統計用（月次レポート）
    # 使用頻度: 中（コスト分析、レポート）
    # 期待効果: 使用量レポート 10倍高速化
    op.create_index(
        'idx_openai_usage_user_date',
        'openai_usage',
        ['user_id', sa.text('created_at DESC')],
        postgresql_using='btree'
    )
    
    # 7. タスク履歴表示用
    # 使用頻度: 中（タスク詳細画面）
    # 期待効果: タスク履歴表示 5倍高速化
    op.create_index(
        'idx_task_histories_task_date',
        'task_histories',
        ['task_id', sa.text('created_at DESC')],
        postgresql_using='btree'
    )

def downgrade():
    """インデックスを削除"""
    op.drop_index('idx_task_histories_task_date')
    op.drop_index('idx_openai_usage_user_date')
    op.drop_index('idx_processed_emails_thread_id')
    op.drop_index('idx_processed_emails_is_task')
    op.drop_index('idx_processed_emails_sync_date')
    op.drop_index('idx_tasks_user_due_date')
    op.drop_index('idx_tasks_user_status')