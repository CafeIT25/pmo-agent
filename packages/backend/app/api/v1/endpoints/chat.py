from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID
from sqlmodel import Session

from app.models.user import User
from app.models.chat import ChatRole
from app.core.deps import get_current_user, get_db
from app.crud.crud_chat import chat_thread, chat_message
from app.schemas.chat import (
    ChatThreadResponse,
    ChatThreadWithMessages,
    ChatCreateThreadRequest,
    ChatSendMessageRequest,
    ChatSendMessageResponse,
    ChatMessageResponse
)
from app.services.openai_service import get_openai_service


router = APIRouter()


@router.get("/threads", response_model=List[ChatThreadResponse])
async def get_chat_threads(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザーのチャットスレッド一覧を取得"""
    threads = chat_thread.get_by_user(db, user_id=current_user.id)
    return threads


@router.post("/threads", response_model=ChatThreadResponse)
async def create_chat_thread(
    request: ChatCreateThreadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """新しいチャットスレッドを作成"""
    thread = chat_thread.create_thread(
        db,
        user_id=current_user.id,
        title=request.title,
        task_id=request.task_id
    )
    
    # 初期メッセージがあれば追加
    if request.initial_message:
        await _send_message_to_thread(
            db=db,
            thread_id=thread.id,
            content=request.initial_message,
            current_user=current_user
        )
    
    return thread


@router.get("/threads/{thread_id}", response_model=ChatThreadWithMessages)
async def get_chat_thread(
    thread_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """特定のチャットスレッドとメッセージ履歴を取得"""
    thread = chat_thread.get(db, id=thread_id)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    messages = chat_message.get_by_thread(db, thread_id=thread_id)
    
    return ChatThreadWithMessages(
        **thread.dict(),
        messages=messages
    )


@router.post("/threads/{thread_id}/messages", response_model=ChatSendMessageResponse)
async def send_message(
    thread_id: UUID,
    request: ChatSendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """チャットスレッドにメッセージを送信してAIの応答を取得"""
    # スレッドの存在確認
    thread = chat_thread.get(db, id=thread_id)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    return await _send_message_to_thread(
        db=db,
        thread_id=thread_id,
        content=request.content,
        current_user=current_user
    )


@router.delete("/threads/{thread_id}")
async def delete_chat_thread(
    thread_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """チャットスレッドを削除"""
    thread = chat_thread.get(db, id=thread_id)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # メッセージも含めて削除
    chat_thread.remove(db, id=thread_id)
    return {"message": "Thread deleted successfully"}


async def _send_message_to_thread(
    db: Session,
    thread_id: UUID,
    content: str,
    current_user: User
) -> ChatSendMessageResponse:
    """スレッドにメッセージを送信し、AIの応答を生成する内部関数"""
    
    # ユーザーメッセージを保存
    user_message = chat_message.create_message(
        db,
        thread_id=thread_id,
        role=ChatRole.USER,
        content=content
    )
    
    # トークン制限内で過去の会話履歴を取得
    conversation_history = chat_message.get_recent_messages_with_token_limit(
        db,
        thread_id=thread_id,
        max_tokens=4000  # GPT-4のコンテキスト制限を考慮
    )
    
    # OpenAI APIで応答を生成
    try:
        openai_service = get_openai_service()
        
        # 会話履歴をOpenAI形式に変換
        messages = []
        for msg in conversation_history[:-1]:  # 最新のユーザーメッセージは除く
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        # 最新のユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": content
        })
        
        # システムプロンプトを追加
        system_prompt = """あなたはPMO（プロジェクトマネジメントオフィス）のAIアシスタントです。
プロジェクト管理、タスク分析、進捗管理に関する質問に答えてください。
具体的で実用的なアドバイスを提供し、必要に応じて次のアクションを提案してください。"""
        
        messages.insert(0, {
            "role": "system", 
            "content": system_prompt
        })
        
        response = await openai_service.generate_chat_completion(
            messages=messages,
            model="gpt-4",
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        # AI応答を保存
        assistant_message = chat_message.create_message(
            db,
            thread_id=thread_id,
            role=ChatRole.ASSISTANT,
            content=ai_response,
            model_id="gpt-4",
            token_count=response.usage.total_tokens if response.usage else None,
            cost=_calculate_cost(response.usage.total_tokens if response.usage else 0)
        )
        
        # スレッドの更新日時を更新
        chat_thread.update_timestamp(db, thread_id=thread_id)
        
        return ChatSendMessageResponse(
            user_message=user_message,
            assistant_message=assistant_message
        )
        
    except Exception as e:
        # エラーの場合、エラーメッセージをAI応答として保存
        error_message = f"申し訳ございません。AIサービスでエラーが発生しました: {str(e)}"
        
        assistant_message = chat_message.create_message(
            db,
            thread_id=thread_id,
            role=ChatRole.ASSISTANT,
            content=error_message
        )
        
        return ChatSendMessageResponse(
            user_message=user_message,
            assistant_message=assistant_message
        )


def _calculate_cost(total_tokens: int) -> float:
    """トークン数からコストを計算（GPT-4の価格設定）"""
    # GPT-4の価格: $0.03/1K tokens (input) + $0.06/1K tokens (output)
    # 簡略化のため平均価格 $0.045/1K tokens を使用
    return (total_tokens / 1000) * 0.045