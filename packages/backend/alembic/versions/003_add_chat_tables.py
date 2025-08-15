"""Add chat_threads and chat_messages tables

Revision ID: 003_add_chat_tables
Revises: 002_ai_support_thread_id
Create Date: 2025-08-14 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003_add_chat_tables'
down_revision = '002_ai_support_thread_id'
depends_on = None

def upgrade():
    """
    ChatGPT風のスレッド型チャット機能のためのテーブル追加
    - chat_threads: チャットスレッド管理
    - chat_messages: チャットメッセージ履歴
    """
    
    # chat_threads テーブルを作成
    op.create_table('chat_threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # chat_messages テーブルを作成
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('USER', 'ASSISTANT', name='chatrole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=True),
        sa.Column('model_id', sa.String(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['thread_id'], ['chat_threads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # インデックスを作成
    op.create_index('idx_chat_threads_user_id', 'chat_threads', ['user_id'])
    op.create_index('idx_chat_threads_task_id', 'chat_threads', ['task_id'])
    op.create_index('idx_chat_messages_thread_id', 'chat_messages', ['thread_id'])
    op.create_index('idx_chat_messages_created_at', 'chat_messages', ['created_at'])

def downgrade():
    """変更を元に戻す"""
    op.drop_index('idx_chat_messages_created_at')
    op.drop_index('idx_chat_messages_thread_id')
    op.drop_index('idx_chat_threads_task_id')
    op.drop_index('idx_chat_threads_user_id')
    op.drop_table('chat_messages')
    op.drop_table('chat_threads')
    op.execute('DROP TYPE chatrole')