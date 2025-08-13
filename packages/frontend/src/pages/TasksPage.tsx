import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Grid, List, Search, Filter, Calendar, Tag, Mail, Bot, User, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/atoms/button';
import { Input } from '@/components/atoms/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/atoms/card';
import { Badge } from '@/components/atoms/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/atoms/select';
import CreateTaskModal from '@/components/organisms/CreateTaskModal';
import { mockTasks, type Task } from '@/data/mockTasks';
import { useDemoData } from '@/hooks/useDemoData';

export default function TasksPage() {
  const navigate = useNavigate();
  const [view, setView] = useState<'card' | 'list'>('card');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const { isDemoMode } = useDemoData();

  // デモモード時のみモックタスクを表示
  const displayTasks = isDemoMode ? mockTasks : tasks;

  return (
    <div className="space-y-4">
      {/* ヘッダー */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">タスク管理</h1>
            <p className="mt-0.5 text-sm text-foreground/60">
              プロジェクトのタスクを管理・追跡
              {isDemoMode && (
                <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-800">
                  デモモード
                </span>
              )}
            </p>
          </div>
          
          <Button 
            variant="gradient" 
            size="default" 
            className="shadow-lg rounded-xl hover:scale-105 transition-transform duration-200"
            onClick={() => setIsCreateModalOpen(true)}
          >
            <Plus className="mr-2 h-4 w-4" />
            新規タスク
          </Button>
        </div>

        {/* フィルターバー */}
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-1 items-center space-x-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/60" />
              <Input
                placeholder="タスクを検索..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Button variant="outline" size="icon" className="text-foreground border-border hover:bg-accent hover:text-accent-foreground">
              <Filter className="h-4 w-4" />
            </Button>
          </div>

          <div className="flex items-center space-x-2">
            <div className="flex items-center rounded-lg border-2 border-border bg-card p-1">
              <Button
                variant={view === 'card' ? 'default' : 'ghost'}
                size="icon-sm"
                className={view !== 'card' ? 'text-foreground hover:text-primary' : ''}
                onClick={() => setView('card')}
              >
                <Grid className="h-4 w-4" />
              </Button>
              <Button
                variant={view === 'list' ? 'default' : 'ghost'}
                size="icon-sm"
                className={view !== 'list' ? 'text-foreground hover:text-primary' : ''}
                onClick={() => setView('list')}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* ステータスサマリー */}
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-gradient-to-br from-background to-muted/20 border-border/50 hover:shadow-xl transition-all duration-300 rounded-xl">
          <CardHeader className="pb-2 pt-4">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-foreground/60">未着手</CardDescription>
            <CardTitle className="text-3xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              {displayTasks.filter(task => task.status === 'todo').length}
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xs text-foreground/50">今日の新規: 0</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-background to-warning/10 border-border/50 hover:shadow-xl transition-all duration-300 rounded-xl">
          <CardHeader className="pb-2 pt-4">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-foreground/60">進行中</CardDescription>
            <CardTitle className="text-3xl font-bold text-warning">
              {displayTasks.filter(task => task.status === 'progress').length}
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xs text-foreground/50">期限近い: 0</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-background to-info/10 border-border/50 hover:shadow-xl transition-all duration-300 rounded-xl">
          <CardHeader className="pb-2 pt-4">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-foreground/60">レビュー中</CardDescription>
            <CardTitle className="text-3xl font-bold text-info">0</CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xs text-foreground/50">待機中: -</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-background to-success/10 border-border/50 hover:shadow-xl transition-all duration-300 rounded-xl">
          <CardHeader className="pb-2 pt-4">
            <CardDescription className="text-xs font-semibold uppercase tracking-wider text-foreground/60">完了</CardDescription>
            <CardTitle className="text-3xl font-bold text-success">
              {displayTasks.filter(task => task.status === 'done').length}
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xs text-foreground/50">今週: {displayTasks.filter(task => task.status === 'done').length}</p>
          </CardContent>
        </Card>
      </div>

      {/* タスクリスト */}
      {displayTasks.length === 0 ? (
        <Card>
          <CardContent className="flex min-h-[300px] items-center justify-center p-8">
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-muted">
                <Calendar className="h-12 w-12 text-foreground/60" />
              </div>
              <h3 className="mb-2 text-lg font-semibold">タスクがありません</h3>
              <p className="mb-6 text-sm text-foreground/60">
                メール同期を実行するか、新規タスクを作成してください。
              </p>
              <div className="flex justify-center space-x-4">
                <Button variant="outline">
                  <Mail className="mr-2 h-4 w-4" />
                  メール同期
                </Button>
                <Button 
                  variant="gradient"
                  onClick={() => setIsCreateModalOpen(true)}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  新規タスク
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {displayTasks
            .filter(task => 
              task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
              task.description.toLowerCase().includes(searchQuery.toLowerCase())
            )
            .map((task) => (
              <TaskCard 
                key={task.id} 
                task={task} 
                view={view}
                onClick={() => navigate(`/tasks/${task.id}`)}
                onStatusChange={(taskId, newStatus) => {
                  if (isDemoMode) {
                    // デモモードでは変更を無視
                    return;
                  }
                  setTasks(tasks.map(t => 
                    t.id === taskId 
                      ? { ...t, status: newStatus as 'todo' | 'progress' | 'done', updated_by: 'user', updated_at: new Date().toISOString() }
                      : t
                  ));
                }}
              />
            ))}
        </div>
      )}

      {/* タスク作成モーダル */}
      <CreateTaskModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreateTask={(newTask) => {
          const task: Task = {
            ...newTask,
            id: crypto.randomUUID(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
          setTasks([task, ...tasks]);
          setIsCreateModalOpen(false);
        }}
      />
    </div>
  );
}

// タスクカードコンポーネント
function TaskCard({ 
  task, 
  view, 
  onClick,
  onStatusChange
}: { 
  task: Task; 
  view: 'card' | 'list';
  onClick: () => void;
  onStatusChange: (taskId: string, status: string) => void;
}) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircle className="h-3.5 w-3.5 text-success" />;
      case 'progress':
        return <Clock className="h-3.5 w-3.5 text-primary" />;
      default:
        return <AlertCircle className="h-3.5 w-3.5 text-foreground/50" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'warning';
      default:
        return 'secondary';
    }
  };

  return (
    <Card className="transition-all duration-200 hover:shadow-lg rounded-xl border border-border/50 hover:border-primary/30 bg-gradient-to-r from-card to-card/90 hover:from-primary/5 hover:to-accent/5">
      <CardContent className="flex items-center justify-between py-3 px-4">
        {/* 左側: タスク名とアイコン */}
        <div className="flex items-center space-x-3 flex-1">
          <div className="flex-shrink-0">
            {getStatusIcon(task.status)}
          </div>
          <h3 
            className="text-sm font-medium text-foreground cursor-pointer hover:text-primary flex-1 truncate transition-all duration-200 hover:translate-x-1"
            onClick={onClick}
          >
            {task.title}
          </h3>
          {task.created_by === 'ai' && (
            <Bot className="h-3.5 w-3.5 text-accent opacity-70" title="AIが作成" />
          )}
        </div>

        {/* 右側: コントロール */}
        <div className="flex items-center space-x-2">
          {/* 優先度バッジ */}
          <Badge variant={getPriorityColor(task.priority)} className="text-xs px-2 py-0.5 rounded-full font-semibold">
            {task.priority === 'high' ? '高' : task.priority === 'medium' ? '中' : '低'}
          </Badge>

          {/* ステータス変更ドロップダウン */}
          <Select 
            value={task.status} 
            onValueChange={(value) => {
              onStatusChange(task.id, value);
              event?.stopPropagation();
            }}
          >
            <SelectTrigger className="w-[110px] h-8 text-xs rounded-lg border-border/50 bg-background/50" onClick={(e) => e.stopPropagation()}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todo">
                <div className="flex items-center text-xs">
                  <AlertCircle className="mr-1.5 h-3 w-3" />
                  TODO
                </div>
              </SelectItem>
              <SelectItem value="progress">
                <div className="flex items-center text-xs">
                  <Clock className="mr-1.5 h-3 w-3" />
                  進行中
                </div>
              </SelectItem>
              <SelectItem value="done">
                <div className="flex items-center text-xs">
                  <CheckCircle className="mr-1.5 h-3 w-3" />
                  完了
                </div>
              </SelectItem>
            </SelectContent>
          </Select>

          {/* メールリンク */}
          {task.source_email_link && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={(e) => {
                e.stopPropagation();
                window.open(task.source_email_link, '_blank');
              }}
              title="元メールを開く"
            >
              <Mail className="h-3 w-3" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}