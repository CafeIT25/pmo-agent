import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/atoms/dialog';
import { Button } from '@/components/atoms/button';
import { Input } from '@/components/atoms/input';
import { Label } from '@/components/atoms/label';
import { Textarea } from '@/components/atoms/textarea';
import { MessageSquare, Loader2 } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';

interface CreateThreadModalProps {
  open: boolean;
  onClose: () => void;
  taskId?: string;
}

export const CreateThreadModal: React.FC<CreateThreadModalProps> = ({
  open,
  onClose,
  taskId
}) => {
  const [title, setTitle] = useState('');
  const [initialMessage, setInitialMessage] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  
  const { createThread } = useChatStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim()) return;

    setIsCreating(true);
    try {
      await createThread(
        title.trim(),
        taskId,
        initialMessage.trim() || undefined
      );
      
      // リセットして閉じる
      setTitle('');
      setInitialMessage('');
      onClose();
    } catch (error) {
      console.error('Failed to create thread:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleClose = () => {
    if (!isCreating) {
      setTitle('');
      setInitialMessage('');
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            新しいチャットスレッド
          </DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">スレッドタイトル *</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例: プロジェクトの進捗について"
              disabled={isCreating}
              maxLength={100}
              required
            />
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {title.length}/100文字
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="initial-message">最初のメッセージ（任意）</Label>
            <Textarea
              id="initial-message"
              value={initialMessage}
              onChange={(e) => setInitialMessage(e.target.value)}
              placeholder="例: 現在のプロジェクトの進捗状況について相談したいです。"
              disabled={isCreating}
              maxLength={1000}
              rows={3}
              className="resize-none"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {initialMessage.length}/1000文字
            </p>
          </div>

          {taskId && (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                このチャットはタスクに関連付けられます。
              </p>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isCreating}
            >
              キャンセル
            </Button>
            <Button
              type="submit"
              disabled={!title.trim() || isCreating}
            >
              {isCreating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  作成中...
                </>
              ) : (
                'スレッド作成'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};