"""Add thread_id and metadata to ai_supports table

Revision ID: 002_ai_support_thread_id
Revises: 001_performance_indexes
Create Date: 2025-08-14 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_ai_support_thread_id'
down_revision = '001_performance_indexes'
depends_on = None

def upgrade():
    """
    AI調査履歴をスレッド単位で管理するための拡張
    - thread_id: メールスレッドIDによる履歴グループ化
    - metadata: 追加のメタデータ保存
    """
    
    # ai_supports テーブルに thread_id カラムを追加
    op.add_column('ai_supports', sa.Column('thread_id', sa.String(), nullable=True))
    
    # ai_supports テーブルに metadata カラムを追加
    op.add_column('ai_supports', sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # thread_id インデックスを作成（履歴検索の高速化）
    op.create_index('idx_ai_supports_thread_id', 'ai_supports', ['thread_id'])
    
    # task_id + thread_id 複合インデックス（特定タスク内のスレッド履歴検索）
    op.create_index('idx_ai_supports_task_thread', 'ai_supports', ['task_id', 'thread_id'])

def downgrade():
    """変更を元に戻す"""
    op.drop_index('idx_ai_supports_task_thread')
    op.drop_index('idx_ai_supports_thread_id')
    op.drop_column('ai_supports', 'metadata')
    op.drop_column('ai_supports', 'thread_id')