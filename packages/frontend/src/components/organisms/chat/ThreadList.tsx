import React, { useEffect } from 'react';
import { Button } from '@/components/atoms/button';
import { ScrollArea } from '@/components/atoms/scroll-area';
import { Badge } from '@/components/atoms/badge';
import { 
  Plus, 
  MessageSquare, 
  Trash2, 
  Calendar,
  MoreVertical 
} from 'lucide-react';
// DropdownMenu の代替として、簡単なコンテキストメニューを使用
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { useChatStore, ChatThread } from '@/store/chatStore';
import { cn } from '@/lib/utils';

interface ThreadListProps {
  className?: string;
  onCreateThread?: () => void;
}

export const ThreadList: React.FC<ThreadListProps> = ({ 
  className,
  onCreateThread 
}) => {
  const {
    threads,
    activeThreadId,
    isLoading,
    error,
    fetchThreads,
    selectThread,
    deleteThread,
    clearError
  } = useChatStore();

  useEffect(() => {
    fetchThreads();
  }, [fetchThreads]);

  const handleThreadSelect = (threadId: string) => {
    if (threadId !== activeThreadId) {
      selectThread(threadId);
    }
  };

  const handleDeleteThread = async (threadId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    if (window.confirm('このスレッドを削除しますか？')) {
      await deleteThread(threadId);
    }
  };

  const handleCreateThread = () => {
    onCreateThread?.();
  };

  return (
    <div className={cn("flex flex-col h-full bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700", className)}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            AI チャット
          </h2>
          <Button
            onClick={handleCreateThread}
            size="sm"
            className="flex items-center gap-1"
          >
            <Plus className="h-4 w-4" />
            新規
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-4 mt-2">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearError}
              className="mt-1 h-auto p-0 text-red-600 dark:text-red-400"
            >
              閉じる
            </Button>
          </div>
        </div>
      )}

      {/* Thread List */}
      <ScrollArea className="flex-1">
        <div className="p-2">
          {isLoading && threads.length === 0 ? (
            <div className="p-4 text-center text-gray-500 dark:text-gray-400">
              読み込み中...
            </div>
          ) : threads.length === 0 ? (
            <div className="p-4 text-center text-gray-500 dark:text-gray-400">
              <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">チャットがありません</p>
              <p className="text-xs mt-1">「新規」ボタンで開始</p>
            </div>
          ) : (
            <div className="space-y-1">
              {threads.map((thread) => (
                <ThreadListItem
                  key={thread.id}
                  thread={thread}
                  isActive={thread.id === activeThreadId}
                  onClick={() => handleThreadSelect(thread.id)}
                  onDelete={(event) => handleDeleteThread(thread.id, event)}
                />
              ))}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
};

interface ThreadListItemProps {
  thread: ChatThread;
  isActive: boolean;
  onClick: () => void;
  onDelete: (event: React.MouseEvent) => void;
}

const ThreadListItem: React.FC<ThreadListItemProps> = ({
  thread,
  isActive,
  onClick,
  onDelete
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return format(date, 'HH:mm', { locale: ja });
    } else if (diffInHours < 24 * 7) {
      return format(date, 'M/d', { locale: ja });
    } else {
      return format(date, 'M/d', { locale: ja });
    }
  };

  return (
    <div
      className={cn(
        "group relative p-3 rounded-lg cursor-pointer transition-all duration-200",
        "hover:bg-gray-100 dark:hover:bg-gray-800",
        isActive && "bg-primary/10 dark:bg-primary/20 border border-primary/20"
      )}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className={cn(
            "font-medium text-sm truncate",
            isActive ? "text-primary" : "text-gray-900 dark:text-gray-100"
          )}>
            {thread.title}
          </h3>
          
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatDate(thread.updated_at)}
            </span>
            
            {thread.task_id && (
              <Badge variant="secondary" className="text-xs py-0 px-1">
                タスク
              </Badge>
            )}
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          className={cn(
            "h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity text-red-600 dark:text-red-400",
            isActive && "opacity-100"
          )}
          onClick={onDelete}
          title="削除"
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
};