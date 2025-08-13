import { useState } from 'react';
import { Bot, Search, Mail, Edit3, Send, Copy, Loader2, X } from 'lucide-react';
import { Button } from '@/components/atoms/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/atoms/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/atoms/tabs';
import { Textarea } from '@/components/atoms/textarea';
import { Label } from '@/components/atoms/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/atoms/select';
import { useToast } from '@/components/atoms/use-toast';
import { sanitizeEmailThread, generateMailtoLink, generateOutlookWebLink, generateGmailLink } from '@/utils/privacy';

interface AIInvestigationModalProps {
  isOpen: boolean;
  onClose: () => void;
  taskTitle: string;
  emailThread: any[];
  originalEmails: any[]; // 元のメール情報（アドレス含む）
}

export default function AIInvestigationModal({
  isOpen,
  onClose,
  taskTitle,
  emailThread,
  originalEmails,
}: AIInvestigationModalProps) {
  const { toast } = useToast();
  const [mode, setMode] = useState<'investigate' | 'reply'>('investigate');
  const [isLoading, setIsLoading] = useState(false);
  const [investigationResult, setInvestigationResult] = useState('');
  const [replyDraft, setReplyDraft] = useState('');
  const [emailClient, setEmailClient] = useState<'gmail' | 'outlook' | 'default'>('default');

  const handleInvestigate = async () => {
    setIsLoading(true);
    
    try {
      // 個人情報を除去
      const sanitizedThread = sanitizeEmailThread(emailThread);
      
      // AI調査リクエスト（モック）
      setTimeout(() => {
        if (mode === 'investigate') {
          setInvestigationResult(`
## 調査結果

### 状況分析
このメールスレッドは、プロジェクト計画書の作成に関する一連のやり取りです。

### 主要なポイント
1. **初回依頼**: Q1の新規プロジェクト計画書作成
2. **必要要素**: エグゼクティブサマリー、スコープ定義、タイムライン、リソース配分、リスク管理計画
3. **進捗状況**: 現在60%完成、スコープ定義とガントチャート作成済み

### 推奨アクション
- 残り40%の作業を期限までに完了させる
- リスク管理計画の詳細化が必要
- エグゼクティブサマリーの最終確認

### 技術的な実装提案
プロジェクト計画書作成にあたって、以下のツールの活用を推奨：
- Microsoft Project または Jira でのタスク管理
- Confluence でのドキュメント共有
- Slack での進捗報告の自動化
          `);
        } else {
          setReplyDraft(`
お世話になっております。

プロジェクト計画書の件につきまして、進捗をご報告いたします。

現在の完成度は約80%となっており、以下の項目が完了しております：
- エグゼクティブサマリー（ドラフト版）
- スコープ定義（確定版）
- ガントチャート（第2版）
- リソース配分計画（承認済み）

残りの作業：
- リスク管理計画の詳細化
- エグゼクティブサマリーの最終調整
- 全体レビューと微調整

予定通り、今週末までには完成予定です。
ご確認のほど、よろしくお願いいたします。
          `);
        }
        setIsLoading(false);
      }, 2000);
    } catch (error) {
      toast({
        title: 'エラー',
        description: 'AI調査中にエラーが発生しました',
        variant: 'destructive',
      });
      setIsLoading(false);
    }
  };

  const handleSendReply = () => {
    if (!originalEmails.length) return;
    
    const lastEmail = originalEmails[originalEmails.length - 1];
    const to = lastEmail.from;
    const cc = lastEmail.cc?.join(', ') || '';
    const subject = `Re: ${lastEmail.subject}`;
    const body = replyDraft;
    
    let link = '';
    switch (emailClient) {
      case 'gmail':
        link = generateGmailLink(to, cc, subject, body);
        break;
      case 'outlook':
        link = generateOutlookWebLink(to, cc, subject, body);
        break;
      default:
        link = generateMailtoLink(to, cc, subject, body);
        break;
    }
    
    window.open(link, '_blank');
  };

  const handleCopyReply = () => {
    navigator.clipboard.writeText(replyDraft);
    toast({
      title: 'コピー完了',
      description: '返信内容をクリップボードにコピーしました',
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            AI調査・返信作成
          </DialogTitle>
          <DialogDescription>
            {taskTitle}に関する調査と返信作成を行います
          </DialogDescription>
        </DialogHeader>

        <Tabs value={mode} onValueChange={(v) => setMode(v as 'investigate' | 'reply')} className="flex-1">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="investigate" className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              調査モード
            </TabsTrigger>
            <TabsTrigger value="reply" className="flex items-center gap-2">
              <Mail className="h-4 w-4" />
              返信作成モード
            </TabsTrigger>
          </TabsList>

          <TabsContent value="investigate" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>調査内容</Label>
              <div className="p-4 bg-muted rounded-lg max-h-60 overflow-y-auto">
                <p className="text-sm text-foreground/60">
                  メールスレッドの内容を分析し、技術的な調査や推奨事項を提供します。
                  個人情報は自動的に除去されます。
                </p>
              </div>
            </div>

            {!investigationResult ? (
              <Button 
                onClick={handleInvestigate} 
                disabled={isLoading}
                className="w-full"
                variant="gradient"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    調査中...
                  </>
                ) : (
                  <>
                    <Bot className="mr-2 h-4 w-4" />
                    AIに調査を依頼
                  </>
                )}
              </Button>
            ) : (
              <div className="space-y-4">
                <div className="prose prose-sm max-w-none p-4 bg-background border rounded-lg max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap font-sans">{investigationResult}</pre>
                </div>
                <Button 
                  onClick={() => setInvestigationResult('')}
                  variant="outline"
                  className="w-full"
                >
                  再調査
                </Button>
              </div>
            )}
          </TabsContent>

          <TabsContent value="reply" className="space-y-4 mt-4">
            {!replyDraft ? (
              <>
                <div className="space-y-2">
                  <Label>返信作成の説明</Label>
                  <div className="p-4 bg-muted rounded-lg">
                    <p className="text-sm text-foreground/60">
                      メールの内容を分析し、適切な返信文案を作成します。
                      作成後、編集してからメールクライアントで送信できます。
                    </p>
                  </div>
                </div>

                <Button 
                  onClick={handleInvestigate} 
                  disabled={isLoading}
                  className="w-full"
                  variant="gradient"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      返信作成中...
                    </>
                  ) : (
                    <>
                      <Edit3 className="mr-2 h-4 w-4" />
                      AIに返信作成を依頼
                    </>
                  )}
                </Button>
              </>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>返信内容（編集可能）</Label>
                  <Textarea
                    value={replyDraft}
                    onChange={(e) => setReplyDraft(e.target.value)}
                    className="min-h-[200px] font-sans"
                    placeholder="返信内容を入力..."
                  />
                </div>

                <div className="space-y-2">
                  <Label>メールクライアント</Label>
                  <Select value={emailClient} onValueChange={(v: any) => setEmailClient(v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="default">デフォルト（メールアプリ）</SelectItem>
                      <SelectItem value="gmail">Gmail</SelectItem>
                      <SelectItem value="outlook">Outlook</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex gap-2">
                  <Button 
                    onClick={handleSendReply}
                    className="flex-1"
                    variant="gradient"
                  >
                    <Send className="mr-2 h-4 w-4" />
                    メールクライアントで開く
                  </Button>
                  <Button 
                    onClick={handleCopyReply}
                    variant="outline"
                  >
                    <Copy className="mr-2 h-4 w-4" />
                    コピー
                  </Button>
                </div>

                <Button 
                  onClick={() => setReplyDraft('')}
                  variant="ghost"
                  className="w-full"
                >
                  再作成
                </Button>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}