import React from 'react';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { Button } from '@/components/atoms/button';
import { Badge } from '@/components/atoms/badge';
import { 
  Bot, 
  Settings, 
  MoreVertical,
  ExternalLink 
} from 'lucide-react';
// DropdownMenu の代替として、簡単なボタンを使用
import { useChatStore } from '@/store/chatStore';
import { cn } from '@/lib/utils';

interface ChatWindowProps {
  className?: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ className }) => {
  const { 
    threads, 
    activeThreadId, 
    messages,
    isTyping 
  } = useChatStore();

  const activeThread = threads.find(t => t.id === activeThreadId);

  if (!activeThreadId || !activeThread) {
    return (
      <div className={cn("flex flex-col items-center justify-center h-full bg-white dark:bg-gray-900", className)}>
        <Bot className="h-16 w-16 text-gray-400 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
          AI チャットアシスタント
        </h2>
        <p className="text-gray-500 dark:text-gray-400 text-center max-w-md mb-6">
          左のサイドバーからチャットスレッドを選択するか、<br />
          新しいスレッドを作成して会話を開始してください。
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-lg">
          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">📊 プロジェクト分析</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              進捗状況の分析や課題の特定をサポート
            </p>
          </div>
          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">💡 タスク提案</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              効率的なタスク管理のアドバイス
            </p>
          </div>
          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">🔍 問題解決</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              プロジェクトの課題解決をサポート
            </p>
          </div>
          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
            <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-2">📝 レポート作成</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              進捗レポートの作成をアシスト
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full bg-white dark:bg-gray-900", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Bot className="h-6 w-6 text-primary" />
            <span className="absolute -bottom-1 -right-1 h-2 w-2 bg-green-500 rounded-full animate-pulse" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">
              {activeThread.title}
            </h3>
            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              <span>
                {messages.length} メッセージ
              </span>
              {activeThread.task_id && (
                <>
                  <span>•</span>
                  <Badge variant="secondary" className="text-xs py-0 px-1">
                    タスク連携
                  </Badge>
                </>
              )}
              {isTyping && (
                <>
                  <span>•</span>
                  <span className="text-primary animate-pulse">
                    AI入力中...
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <Button variant="ghost" size="icon" title="設定">
          <Settings className="h-4 w-4" />
        </Button>
      </div>

      {/* Messages */}
      <MessageList className="flex-1" />

      {/* Input */}
      <MessageInput />
    </div>
  );
};