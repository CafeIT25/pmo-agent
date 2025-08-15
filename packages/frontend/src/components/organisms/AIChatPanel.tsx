import { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  Copy, 
  Check,
  Sparkles,
  MessageSquare
} from 'lucide-react';
import { Button } from '@/components/atoms/button';
import { Textarea } from '@/components/atoms/textarea';
import { ScrollArea } from '@/components/atoms/scroll-area';
import { Avatar, AvatarFallback } from '@/components/atoms/avatar';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { useChatStore } from '@/store/chatStore';

interface AIChatPanelProps {
  taskId: string;
  taskTitle: string;
  className?: string;
}

const AIChatPanel: React.FC<AIChatPanelProps> = ({ 
  taskId,
  taskTitle,
  className
}) => {
  const [input, setInput] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const { 
    threads, 
    activeThreadId, 
    messages, 
    isTyping,
    fetchThreads, 
    selectThread, 
    createThread,
    sendMessage
  } = useChatStore();

  // Effect to initiate loading and clear state when taskId changes
  useEffect(() => {
    if (taskId) {
      setIsLoading(true);
      selectThread(null); // Clear previous thread's messages to prevent flicker
      fetchThreads();
    } else {
      setIsLoading(false);
    }
  }, [taskId, fetchThreads, selectThread]);

  // Effect to find and select the correct thread once `threads` are loaded/updated
  useEffect(() => {
    if (!taskId) return;

    // Only process if threads have been fetched.
    // The store updates `threads` asynchronously after `fetchThreads()` is called.
    if (threads.length > 0) {
      // Find all threads for this task
      const taskThreads = threads.filter(thread => thread.task_id === taskId);
      
      if (taskThreads.length > 0) {
        // If there's no active thread or the active thread is not for this task, select the latest one
        if (!activeThreadId || !taskThreads.some(thread => thread.id === activeThreadId)) {
          // Get the most recent thread (latest updated_at)
          const latestThread = taskThreads.sort((a, b) => 
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
          )[0];
          selectThread(latestThread.id);
        }
      }
    }
    // Loading is complete after we've attempted to find the thread
    setIsLoading(false);
  }, [threads, taskId, activeThreadId, selectThread]);

  // Auto-scroll
  const scrollToBottom = () => {
    setTimeout(() => {
      if (scrollAreaRef.current) {
        const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
        if (scrollContainer) {
          scrollContainer.scrollTop = scrollContainer.scrollHeight;
        }
      }
    }, 100); // DOM更新を待つために少し遅延
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = useCallback(async () => {
    if (!input.trim()) return;

    const currentInput = input;
    setInput('');

    // If no thread is active, create one with the first message
    if (!activeThreadId) {
      try {
        await createThread(
          `${taskTitle} - AI調査`,
          taskId,
          currentInput
        );
      } catch (error) {
        console.error('Failed to create thread:', error);
      }
    } else {
      // Otherwise, send a message to the existing thread
      try {
        await sendMessage(currentInput);
      } catch (error) {
        console.error('Failed to send message:', error);
      }
    }
  }, [input, activeThreadId, taskId, taskTitle, createThread, sendMessage]);

  const handleCopy = useCallback((content: string, messageId: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(messageId);
    setTimeout(() => setCopiedId(null), 2000);
  }, []);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  return (
    <div className={cn("flex flex-col bg-white dark:bg-gray-900 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700", className)} style={{ height: '600px' }}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Sparkles className="h-6 w-6 text-primary" />
            <span className="absolute -bottom-1 -right-1 h-2 w-2 bg-green-500 rounded-full animate-pulse" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">AI アシスタント</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              調査モード - {taskTitle}
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea ref={scrollAreaRef} className="flex-1 overflow-hidden">
        <div className="p-4 space-y-6 pb-6">
          {isLoading ? (
            <div className="flex justify-center items-center h-full py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : messages.length === 0 && !isTyping ? (
            <div className="text-center text-gray-500 dark:text-gray-400 py-8">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">AIとの会話を開始</p>
              <p className="text-sm">最初のメッセージを送信して、このタスクに関する調査を始めましょう。</p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex gap-3 animate-fade-in",
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {message.role === 'assistant' && (
                    <Avatar className="h-8 w-8 shrink-0">
                      <AvatarFallback className="bg-gradient-to-br from-primary to-secondary">
                        <Bot className="h-4 w-4 text-white" />
                      </AvatarFallback>
                    </Avatar>
                  )}
                  
                  <div className={cn(
                    "group relative max-w-[70%] rounded-2xl px-4 py-3 transition-all duration-300",
                    message.role === 'user' 
                      ? "bg-primary text-white" 
                      : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  )}>
                    <div className="whitespace-pre-wrap break-words text-sm">
                      {message.content}
                    </div>
                    
                    <div className={cn(
                      "mt-1 flex items-center gap-2 text-xs",
                      message.role === 'user' ? "text-white/70" : "text-muted-foreground"
                    )}>
                      <time>
                        {format(new Date(message.created_at), 'HH:mm', { locale: ja })}
                      </time>
                    </div>

                    {/* Copy Button (Assistant messages only) */}
                    {message.role === 'assistant' && (
                      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 bg-white/80 dark:bg-gray-800/80 hover:bg-white dark:hover:bg-gray-700"
                          onClick={() => handleCopy(message.content, message.id)}
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

                  {message.role === 'user' && (
                    <Avatar className="h-8 w-8 shrink-0">
                      <AvatarFallback className="bg-gray-200 dark:bg-gray-700">
                        <User className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}
                </div>
              ))}

              {isTyping && (
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
                        AI が考えています...
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4 flex-shrink-0">
        <div className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <Textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="AIに質問する..."
              disabled={isTyping || isLoading}
              className="min-h-[44px] max-h-[120px] resize-none pr-12 focus:ring-2 focus:ring-primary focus:border-primary"
              rows={1}
            />
            
            {input.length > 0 && (
              <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                {input.length}
              </div>
            )}
          </div>

          <Button
            onClick={handleSend}
            disabled={!input.trim() || isTyping || isLoading}
            size="icon"
            className="shrink-0 h-11 w-11"
            aria-label="メッセージを送信"
          >
            {isTyping ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>

        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
          Enterで送信、Shift+Enterで改行
        </div>
      </div>
    </div>
  );
};

export default AIChatPanel;