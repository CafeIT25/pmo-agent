import { useState } from 'react';
import { Plus, X, Calendar, AlertCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/atoms/dialog';
import { Button } from '@/components/atoms/button';
import { Input } from '@/components/atoms/input';
import { Textarea } from '@/components/atoms/textarea';
import { Label } from '@/components/atoms/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/atoms/select';

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateTask: (task: any) => void;
}

export default function CreateTaskModal({ isOpen, onClose, onCreateTask }: CreateTaskModalProps) {
  const [taskData, setTaskData] = useState({
    title: '',
    description: '',
    priority: 'medium',
    status: 'todo',
    due_date: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!taskData.title.trim()) {
      alert('タスクタイトルを入力してください');
      return;
    }

    onCreateTask({
      ...taskData,
      created_by: 'user',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    // リセット
    setTaskData({
      title: '',
      description: '',
      priority: 'medium',
      status: 'todo',
      due_date: '',
    });
    
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle className="text-foreground">新規タスクの作成</DialogTitle>
            <DialogDescription className="text-foreground/80">
              手動でタスクを作成します。メール同期とは別に独自のタスクを管理できます。
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title" className="text-foreground">
                タスクタイトル <span className="text-red-500">*</span>
              </Label>
              <Input
                id="title"
                value={taskData.title}
                onChange={(e) => setTaskData({ ...taskData, title: e.target.value })}
                placeholder="例: レポート作成"
                className="text-foreground"
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description" className="text-foreground">説明</Label>
              <Textarea
                id="description"
                value={taskData.description}
                onChange={(e) => setTaskData({ ...taskData, description: e.target.value })}
                placeholder="タスクの詳細な説明を入力..."
                className="min-h-[100px] text-foreground"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="status" className="text-foreground">ステータス</Label>
                <Select
                  value={taskData.status}
                  onValueChange={(value) => setTaskData({ ...taskData, status: value })}
                >
                  <SelectTrigger id="status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todo">
                      <div className="flex items-center text-foreground">
                        <AlertCircle className="mr-2 h-4 w-4 text-foreground" />
                        TODO
                      </div>
                    </SelectItem>
                    <SelectItem value="progress">
                      <div className="flex items-center text-foreground">
                        <div className="mr-2 h-4 w-4 rounded-full border-2 border-foreground" />
                        進行中
                      </div>
                    </SelectItem>
                    <SelectItem value="done">
                      <div className="flex items-center text-foreground">
                        <div className="mr-2 h-4 w-4 rounded-full bg-foreground" />
                        完了
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="priority" className="text-foreground">優先度</Label>
                <Select
                  value={taskData.priority}
                  onValueChange={(value) => setTaskData({ ...taskData, priority: value })}
                >
                  <SelectTrigger id="priority">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="high">
                      <span className="text-red-500 font-semibold">高</span>
                    </SelectItem>
                    <SelectItem value="medium">
                      <span className="text-yellow-500 font-semibold">中</span>
                    </SelectItem>
                    <SelectItem value="low">
                      <span className="text-foreground">低</span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="due_date" className="text-foreground">期限</Label>
              <div className="relative">
                <Input
                  id="due_date"
                  type="date"
                  value={taskData.due_date}
                  onChange={(e) => setTaskData({ ...taskData, due_date: e.target.value })}
                  className="text-foreground [&::-webkit-calendar-picker-indicator]:cursor-pointer [&::-webkit-calendar-picker-indicator]:opacity-100"
                  placeholder="期限を選択..."
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose} className="text-foreground border-foreground/20 hover:bg-foreground/10 hover:text-foreground">
              キャンセル
            </Button>
            <Button type="submit" variant="gradient">
              <Plus className="mr-2 h-4 w-4" />
              タスクを作成
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}