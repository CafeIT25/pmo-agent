import { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  RefreshCw, 
  Copy, 
  Check,
  Sparkles,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  MoreVertical,
  Search,
  Mail,
  ToggleLeft,
  ToggleRight
} from 'lucide-react';
import { Button } from '@/components/atoms/button';
import { Textarea } from '@/components/atoms/textarea';
import { ScrollArea } from '@/components/atoms/scroll-area';
import { Avatar, AvatarFallback } from '@/components/atoms/avatar';
import { Badge } from '@/components/atoms/badge';
import { cn } from '@/lib/utils';
import { sanitizeEmailThread } from '@/utils/privacy';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  mode?: 'investigate' | 'reply';
  status?: 'sending' | 'sent' | 'error';
  feedback?: 'positive' | 'negative';
}

interface AIChatPanelProps {
  taskTitle: string;
  emailThread: any[];
  onReplyGenerated?: (reply: string) => void;
}

export default function AIChatPanel({ 
  taskTitle, 
  emailThread,
  onReplyGenerated 
}: AIChatPanelProps) {
  const [mode, setMode] = useState<'investigate' | 'reply'>('investigate');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `こんにちは！「${taskTitle}」について、どのようなお手伝いができますか？

以下のような調査や作成が可能です：
• メール内容の詳細分析
• 技術的な調査と提案
• 返信文案の作成
• プロジェクトの進捗確認

お気軽にご質問ください。`,
      timestamp: new Date(),
    }
  ]);
  
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
      mode: mode,
      status: 'sending'
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // 個人情報を除去したメールスレッドを準備
    const sanitizedThread = sanitizeEmailThread(emailThread);

    // AIレスポンスのシミュレーション
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: generateAIResponse(input, sanitizedThread, mode),
        timestamp: new Date(),
        mode: mode,
        status: 'sent'
      };

      setMessages(prev => [...prev.slice(0, -1), 
        { ...userMessage, status: 'sent' },
        assistantMessage
      ]);
      setIsTyping(false);
    }, 2000);
  };

  const generateAIResponse = (query: string, sanitizedThread: any[], currentMode: 'investigate' | 'reply') => {
    const lowerQuery = query.toLowerCase();
    
    if (currentMode === 'reply') {
      const reply = `
承知いたしました。以下の返信文案を作成しました：

---

お世話になっております。

ご連絡いただいた件について、確認いたしました。

${taskTitle}の進捗状況は以下の通りです：
• 現在の完成度：約80%
• 完了予定日：今週末
• 残作業：最終レビューと微調整

ご不明な点がございましたら、お気軽にお問い合わせください。

よろしくお願いいたします。

---

この返信文案は編集可能です。必要に応じて修正してください。`;
      
      if (onReplyGenerated) {
        onReplyGenerated(reply);
      }
      return reply;
    }
    
    if (currentMode === 'investigate') {
      return `
## 調査結果

メールスレッドを分析した結果、以下のポイントが確認されました：

### 📊 状況分析
• プロジェクトの進行状況は順調
• 主要なマイルストーンは予定通り達成
• リソース配分に若干の調整が必要

### 💡 推奨アクション
1. **短期的対応**
   - 週次レビューの実施
   - ステークホルダーへの進捗報告
   
2. **中期的対応**
   - リスク評価の更新
   - バッファ時間の確保

### 🔍 技術的考察
現在の実装アプローチは適切ですが、以下の最適化を検討してください：
• パフォーマンスチューニング
• エラーハンドリングの強化
• ドキュメントの更新

他にご質問はありますか？`;
    }
    
    return `
ご質問ありがとうございます。

「${query}」について、以下の情報をご提供します：

このタスクは重要度が高く、優先的に対応することをお勧めします。
メールスレッドの内容から、関係者間での認識合わせが重要であることが読み取れます。

具体的な対応方法について、さらに詳しくお聞きになりたい点はありますか？`;
  };

  const handleCopy = (content: string, messageId: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(messageId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleFeedback = (messageId: string, feedback: 'positive' | 'negative') => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, feedback } : msg
    ));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-white dark:bg-gray-900 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Sparkles className="h-6 w-6 text-primary" />
            <span className="absolute -bottom-1 -right-1 h-2 w-2 bg-green-500 rounded-full animate-pulse" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">AI アシスタント</h3>
            <p className="text-xs text-secondary ">
              {mode === 'investigate' ? '調査モード' : '返信作成モード'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={mode === 'investigate' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setMode('investigate')}
            className="gap-1"
          >
            <Search className="h-4 w-4" />
            調査
          </Button>
          <Button
            variant={mode === 'reply' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setMode('reply')}
            className="gap-1"
          >
            <Mail className="h-4 w-4" />
            返信作成
          </Button>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-4">
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
                "group relative max-w-[70%] rounded-2xl px-4 py-3",
                message.role === 'user' 
                  ? "bg-primary text-white" 
                  : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
              )}>
                <div className="whitespace-pre-wrap break-words text-sm">
                  {message.content}
                </div>
                
                <div className={cn(
                  "mt-1 flex items-center gap-2 text-xs",
                  message.role === 'user' ? "text-white/70" : "text-secondary "
                )}>
                  <time>
                    {format(message.timestamp, 'HH:mm', { locale: ja })}
                  </time>
                  {message.status === 'sending' && (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  )}
                  {message.status === 'sent' && (
                    <Check className="h-3 w-3" />
                  )}
                </div>

                {/* Action Buttons */}
                {message.role === 'assistant' && (
                  <div className="absolute -bottom-8 left-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={() => handleCopy(message.content, message.id)}
                    >
                      {copiedId === message.id ? (
                        <Check className="h-3 w-3 text-success" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className={cn(
                        "h-7 w-7",
                        message.feedback === 'positive' && "text-success"
                      )}
                      onClick={() => handleFeedback(message.id, 'positive')}
                    >
                      <ThumbsUp className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className={cn(
                        "h-7 w-7",
                        message.feedback === 'negative' && "text-destructive"
                      )}
                      onClick={() => handleFeedback(message.id, 'negative')}
                    >
                      <ThumbsDown className="h-3 w-3" />
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
                <div className="flex gap-1">
                  <span className="h-2 w-2 bg-gray-400 rounded-full animate-pulse" />
                  <span className="h-2 w-2 bg-gray-400 rounded-full animate-pulse delay-75" />
                  <span className="h-2 w-2 bg-gray-400 rounded-full animate-pulse delay-150" />
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={mode === 'investigate' ? "調査したい内容を入力..." : "返信内容について入力..."}
              className="min-h-[80px] resize-none pr-12 rounded-xl"
            />
            <div className="absolute bottom-2 right-2 flex gap-1">
              <Badge variant="secondary" className="text-xs">
                {input.length}/2000
              </Badge>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isTyping}
              className="h-[80px]"
              variant="gradient"
            >
              {isTyping ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>
        <div className="mt-2 flex items-center justify-between">
          <div className="flex gap-2">
            <Badge 
              variant={mode === 'investigate' ? 'default' : 'outline'}
              className="gap-1"
            >
              {mode === 'investigate' ? (
                <>
                  <Search className="h-3 w-3" />
                  調査モード
                </>
              ) : (
                <>
                  <Mail className="h-3 w-3" />
                  返信作成モード
                </>
              )}
            </Badge>
          </div>
          <p className="text-xs text-secondary ">
            Shift+Enter で改行
          </p>
        </div>
      </div>
    </div>
  );
}