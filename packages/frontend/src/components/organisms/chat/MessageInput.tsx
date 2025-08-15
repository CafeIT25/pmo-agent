import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/atoms/button';
import { Textarea } from '@/components/atoms/textarea';
import { Send, Paperclip } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { cn } from '@/lib/utils';

interface MessageInputProps {
  className?: string;
  placeholder?: string;
  disabled?: boolean;
}

export const MessageInput: React.FC<MessageInputProps> = ({ 
  className,
  placeholder = "メッセージを入力...",
  disabled = false
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { activeThreadId, sendMessage, isTyping } = useChatStore();

  const isDisabled = disabled || !activeThreadId || isTyping;

  // テキストエリアの高さを自動調整
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isDisabled) return;
    
    const messageContent = input.trim();
    setInput('');
    
    // テキストエリアの高さをリセット
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
    
    await sendMessage(messageContent);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className={cn("border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900", className)}>
      <form onSubmit={handleSubmit} className="p-4">
        <div className="flex gap-2 items-end">
          {/* ファイル添付ボタン（将来の拡張用） */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="shrink-0 h-10 w-10"
            disabled={isDisabled}
            title="ファイル添付（準備中）"
          >
            <Paperclip className="h-4 w-4" />
          </Button>

          {/* メッセージ入力エリア */}
          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isDisabled ? (
                activeThreadId ? "AIが入力中です..." : "スレッドを選択してください"
              ) : placeholder}
              disabled={isDisabled}
              className={cn(
                "min-h-[44px] max-h-[200px] resize-none pr-12",
                "focus:ring-2 focus:ring-primary focus:border-primary"
              )}
              rows={1}
            />
            
            {/* 文字数カウンター */}
            {input.length > 0 && (
              <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                {input.length}
              </div>
            )}
          </div>

          {/* 送信ボタン */}
          <Button
            type="submit"
            size="icon"
            className="shrink-0 h-10 w-10"
            disabled={!input.trim() || isDisabled}
            title="送信 (Enter)"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>

        {/* ヘルプテキスト */}
        <div className="flex justify-between items-center mt-2 text-xs text-gray-500 dark:text-gray-400">
          <span>
            {isTyping ? (
              "AIが回答を生成中です..."
            ) : (
              "Enterで送信、Shift+Enterで改行"
            )}
          </span>
          
          {activeThreadId && (
            <span className="text-primary/70">
              スレッド: {activeThreadId.slice(0, 8)}...
            </span>
          )}
        </div>
      </form>
    </div>
  );
};