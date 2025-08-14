import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Mail, 
  ExternalLink, 
  Bot, 
  User, 
  Clock,
  Calendar,
  AlertCircle,
  CheckCircle,
  Sparkles
} from 'lucide-react';
import { Button } from '@/components/atoms/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/atoms/card';
import { Badge } from '@/components/atoms/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/atoms/tabs';
import { Textarea } from '@/components/atoms/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/atoms/select';
import { getTaskDetail } from '@/data/mockTasks';
import AIChatPanel from '@/components/organisms/AIChatPanel';

export default function TaskDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  // モックデータから取得
  const taskDetail = getTaskDetail(id || '');
  
  if (!taskDetail) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">タスクが見つかりません</h2>
          <Button onClick={() => navigate('/tasks')}>タスク一覧へ戻る</Button>
        </div>
      </div>
    );
  }

  const task = taskDetail;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircle className="h-5 w-5 text-success" />;
      case 'progress':
        return <Clock className="h-5 w-5 text-primary" />;
      default:
        return <AlertCircle className="h-5 w-5 text-foreground/60" />;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'done':
        return '完了';
      case 'progress':
        return '進行中';
      default:
        return 'TODO';
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
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="icon"
            className="text-foreground hover:text-primary"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-foreground">{task.title}</h1>
            <div className="mt-1 flex items-center space-x-4 text-sm text-foreground/60">
              <span className="flex items-center">
                {task.created_by === 'ai' ? (
                  <Bot className="mr-1 h-3 w-3" />
                ) : (
                  <User className="mr-1 h-3 w-3" />
                )}
                {task.created_by === 'ai' ? 'AI作成' : 'ユーザー作成'}
              </span>
              <span>•</span>
              <span>{new Date(task.created_at).toLocaleDateString('ja-JP')}</span>
            </div>
          </div>
        </div>
        
        {task.source_email_link && (
          <Button variant="outline" className="text-foreground border-border hover:bg-accent hover:text-accent-foreground" asChild>
            <a href={task.source_email_link} target="_blank" rel="noopener noreferrer">
              <Mail className="mr-2 h-4 w-4" />
              元メールを開く
              <ExternalLink className="ml-2 h-3 w-3" />
            </a>
          </Button>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* メインコンテンツ */}
        <div className="lg:col-span-2 space-y-6">
          <Tabs defaultValue="overview" className="w-full">
            <TabsList>
              <TabsTrigger value="overview">概要</TabsTrigger>
              {task.created_by === 'ai' && (
                <TabsTrigger value="email">メール履歴</TabsTrigger>
              )}
              <TabsTrigger value="investigation">AI調査</TabsTrigger>
            </TabsList>
            
            <TabsContent value="overview" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{task.created_by === 'ai' ? 'タスク詳細' : 'タスク概要'}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium mb-2 text-foreground">
                      {task.created_by === 'ai' ? '説明' : '概要'}
                    </h3>
                    <p className="text-sm text-foreground/70">{task.description}</p>
                  </div>
                  
                  <div>
                    <h3 className="text-sm font-medium mb-2 text-foreground">ステータス</h3>
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(task.status)}
                      <span className="text-sm font-medium text-foreground">{getStatusLabel(task.status)}</span>
                      {task.updated_by === 'ai' && (
                        <span className="flex items-center text-xs text-foreground/60 ml-2">
                          <Bot className="mr-1 h-3 w-3" />
                          AIによる更新
                        </span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            {task.created_by === 'ai' && (
              <TabsContent value="email" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>メール履歴</CardTitle>
                  <CardDescription>タスクに関連するメールのやり取り</CardDescription>
                </CardHeader>
                <CardContent>
                  {taskDetail.email_thread && taskDetail.email_thread.length > 0 ? (
                    <div className="space-y-4">
                      {/* メール要約 */}
                      <div className="p-4 bg-muted/50 rounded-lg mb-6">
                        <h4 className="font-medium mb-2 text-foreground">メール要約</h4>
                        <p className="text-sm text-secondary whitespace-pre-wrap">
                          {task.email_summary}
                        </p>
                      </div>
                      
                      {/* メールスレッド */}
                      <div className="space-y-3">
                        <h4 className="font-medium text-foreground">メール履歴詳細</h4>
                        {taskDetail.email_thread.map((email, index) => (
                          <div key={email.id} className="border rounded-lg p-4">
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex-1">
                                <div className="flex items-center space-x-2 mb-1">
                                  {email.type === 'received' && (
                                    <Badge variant="info" className="text-xs">受信</Badge>
                                  )}
                                  {email.type === 'sent' && (
                                    <Badge variant="success" className="text-xs">送信</Badge>
                                  )}
                                  {email.type === 'reply' && (
                                    <Badge variant="warning" className="text-xs">返信</Badge>
                                  )}
                                  <span className="text-xs text-secondary">
                                    {new Date(email.date).toLocaleString('ja-JP')}
                                  </span>
                                </div>
                                <div className="text-sm text-foreground">
                                  <span className="font-medium">From:</span> {email.from}
                                </div>
                                <div className="text-sm text-foreground">
                                  <span className="font-medium">To:</span> {email.to}
                                </div>
                                <div className="text-sm font-medium mt-1 text-foreground">
                                  {email.subject}
                                </div>
                              </div>
                            </div>
                            <div className="mt-3 pt-3 border-t">
                              <pre className="whitespace-pre-wrap text-sm text-secondary">
                                {email.body}
                              </pre>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-secondary">
                      <Mail className="mx-auto h-12 w-12 mb-2 opacity-50" />
                      <p>メール履歴がありません</p>
                    </div>
                  )}
                </CardContent>
              </Card>
              </TabsContent>
            )}
            
            <TabsContent value="investigation" className="space-y-4">
              <Card className="p-0 overflow-hidden">
                <AIChatPanel
                  taskTitle={task.title}
                  emailThread={taskDetail.email_thread || []}
                />
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* サイドバー */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>タスク情報</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground">ステータス</label>
                <Select defaultValue={task.status}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todo">
                      <div className="flex items-center">
                        <AlertCircle className="mr-2 h-4 w-4" />
                        TODO
                      </div>
                    </SelectItem>
                    <SelectItem value="progress">
                      <div className="flex items-center">
                        <Clock className="mr-2 h-4 w-4" />
                        進行中
                      </div>
                    </SelectItem>
                    <SelectItem value="done">
                      <div className="flex items-center">
                        <CheckCircle className="mr-2 h-4 w-4" />
                        完了
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="text-sm font-medium text-foreground">優先度</label>
                <div className="mt-1">
                  <Badge variant={getPriorityColor(task.priority)}>
                    {task.priority === 'high' ? '高' : task.priority === 'medium' ? '中' : '低'}
                  </Badge>
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-foreground">期限</label>
                <div className="mt-1 flex items-center text-sm text-foreground">
                  <Calendar className="mr-2 h-4 w-4" />
                  {task.due_date ? new Date(task.due_date).toLocaleDateString('ja-JP') : '未設定'}
                </div>
              </div>
              
              <div>
                <label className="text-sm font-medium text-foreground">最終更新</label>
                <div className="mt-1 text-sm text-foreground/60">
                  {new Date(task.updated_at).toLocaleString('ja-JP')}
                  {task.updated_by === 'ai' && (
                    <div className="flex items-center mt-1">
                      <Bot className="mr-1 h-3 w-3" />
                      AIによる更新
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>メモ</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea 
                placeholder="タスクに関するメモを入力..."
                className="min-h-[120px]"
              />
              <Button className="mt-2 w-full" variant="outline">
                保存
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}