from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select, desc
from app.models.chat import ChatThread, ChatMessage, ChatRole
from app.crud.base import CRUDBase


class CRUDChatThread(CRUDBase[ChatThread, dict, dict]):
    def get_by_user(self, db: Session, *, user_id: UUID) -> List[ChatThread]:
        """ユーザーのチャットスレッド一覧を取得"""
        statement = select(ChatThread).where(
            ChatThread.user_id == user_id
        ).order_by(desc(ChatThread.updated_at))
        return db.exec(statement).all()
    
    def get_by_task(self, db: Session, *, task_id: UUID) -> List[ChatThread]:
        """特定タスクのチャットスレッド一覧を取得"""
        statement = select(ChatThread).where(
            ChatThread.task_id == task_id
        ).order_by(desc(ChatThread.updated_at))
        return db.exec(statement).all()
    
    def create_thread(
        self, 
        db: Session, 
        *, 
        user_id: UUID, 
        title: str,
        task_id: Optional[UUID] = None
    ) -> ChatThread:
        """新しいチャットスレッドを作成"""
        thread = ChatThread(
            user_id=user_id,
            task_id=task_id,
            title=title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)
        return thread
    
    def update_timestamp(self, db: Session, *, thread_id: UUID) -> Optional[ChatThread]:
        """スレッドの更新日時を現在時刻に更新"""
        thread = self.get(db, id=thread_id)
        if thread:
            thread.updated_at = datetime.utcnow()
            db.add(thread)
            db.commit()
            db.refresh(thread)
        return thread


class CRUDChatMessage(CRUDBase[ChatMessage, dict, dict]):
    def get_by_thread(
        self, 
        db: Session, 
        *, 
        thread_id: UUID,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """スレッドのメッセージ履歴を取得"""
        statement = select(ChatMessage).where(
            ChatMessage.thread_id == thread_id
        ).order_by(ChatMessage.created_at)
        
        if limit:
            # 最新のメッセージから指定数を取得
            statement = statement.limit(limit)
        
        return db.exec(statement).all()
    
    def create_message(
        self,
        db: Session,
        *,
        thread_id: UUID,
        role: ChatRole,
        content: str,
        token_count: Optional[int] = None,
        model_id: Optional[str] = None,
        cost: Optional[float] = None
    ) -> ChatMessage:
        """新しいメッセージを作成"""
        message = ChatMessage(
            thread_id=thread_id,
            role=role,
            content=content,
            token_count=token_count,
            model_id=model_id,
            cost=cost,
            created_at=datetime.utcnow()
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    def get_recent_messages_with_token_limit(
        self,
        db: Session,
        *,
        thread_id: UUID,
        max_tokens: int = 4096
    ) -> List[ChatMessage]:
        """トークン制限内での最新メッセージを取得"""
        # 全メッセージを新しい順で取得
        statement = select(ChatMessage).where(
            ChatMessage.thread_id == thread_id
        ).order_by(desc(ChatMessage.created_at))
        
        all_messages = db.exec(statement).all()
        
        # トークン制限内のメッセージを選択
        selected_messages = []
        total_tokens = 0
        
        for message in all_messages:
            message_tokens = message.token_count or len(message.content.split())  # 概算
            if total_tokens + message_tokens > max_tokens:
                break
            selected_messages.append(message)
            total_tokens += message_tokens
        
        # 時系列順に戻す
        return list(reversed(selected_messages))


# インスタンス作成
chat_thread = CRUDChatThread(ChatThread)
chat_message = CRUDChatMessage(ChatMessage)