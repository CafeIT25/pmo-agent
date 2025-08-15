import React, { useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/atoms/scroll-area';
import { Avatar, AvatarFallback } from '@/components/atoms/avatar';
import { Button } from '@/components/atoms/button';
import { 
  Bot, 
  User, 
  Copy, 
  Check,
  Loader2
} from 'lucide-react';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { useChatStore, ChatMessage } from '@/store/chatStore';
import { cn } from '@/lib/utils';

interface MessageListProps {
  className?: string;
}

export const MessageList: React.FC<MessageListProps> = ({ className }) => {
  const { messages, isTyping } = useChatStore();
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  // 新しいメッセージが追加されたら自動スクロール
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [messages, isTyping]);

  const handleCopy = async (content: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedId(messageId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      <ScrollArea ref={scrollAreaRef} className="flex-1">
        <div className="p-4 space-y-6">
          {messages.length === 0 && !isTyping ? (
            <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-center">
              <Bot className="h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                AI アシスタントとの会話を開始しましょう
              </h3>
              <p className="text-gray-500 dark:text-gray-400 max-w-md">
                プロジェクト管理、タスク分析、進捗管理について何でもお聞きください。
              </p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <MessageItem
                  key={message.id}
                  message={message}
                  onCopy={handleCopy}
                  copiedId={copiedId}
                />
              ))}
              
              {isTyping && <TypingIndicator />}
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

interface MessageItemProps {
  message: ChatMessage;
  onCopy: (content: string, messageId: string) => void;
  copiedId: string | null;
}

const MessageItem: React.FC<MessageItemProps> = ({ message, onCopy, copiedId }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={cn(
      "flex gap-3 animate-fade-in",
      isUser ? 'justify-end' : 'justify-start'
    )}>
      {!isUser && (
        <Avatar className="h-8 w-8 shrink-0">
          <AvatarFallback className="bg-gradient-to-br from-primary to-secondary">
            <Bot className="h-4 w-4 text-white" />
          </AvatarFallback>
        </Avatar>
      )}
      
      <div className={cn(
        "group relative max-w-[70%] rounded-2xl px-4 py-3 transition-all duration-300",
        isUser 
          ? "bg-primary text-white" 
          : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
      )}>
        <div className="whitespace-pre-wrap break-words text-sm">
          {message.content}
        </div>
        
        <div className={cn(
          "mt-1 flex items-center gap-2 text-xs",
          isUser ? "text-white/70" : "text-muted-foreground"
        )}>
          <time>
            {format(new Date(message.created_at), 'HH:mm', { locale: ja })}
          </time>
          
          {message.model_id && (
            <span className="text-xs opacity-70">
              {message.model_id}
            </span>
          )}
        </div>

        {/* Copy Button (Assistant messages only) */}
        {!isUser && (
          <div className="absolute -bottom-8 left-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onCopy(message.content, message.id)}
              aria-label="メッセージをコピー"
            >
              {copiedId === message.id ? (
                <Check className="h-3 w-3 text-success" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>
          </div>
        )}
      </div>

      {isUser && (
        <Avatar className="h-8 w-8 shrink-0">
          <AvatarFallback className="bg-gray-200 dark:bg-gray-700">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
};

const TypingIndicator: React.FC = () => {
  return (
    <div className="flex gap-3 animate-fade-in">
      <Avatar className="h-8 w-8">
        <AvatarFallback className="bg-gradient-to-br from-primary to-secondary">
          <Bot className="h-4 w-4 text-white" />
        </AvatarFallback>
      </Avatar>
      
      <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            入力中...
          </span>
        </div>
      </div>
    </div>
  );
};