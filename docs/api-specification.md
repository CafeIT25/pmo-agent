# PMO Agent API 仕様書

## 最新版仕様（2024年1月更新）

## 概要

PMO Agent は、メール分析とタスク管理を自動化するAIエージェントシステムです。

### 主要機能

1. **スマートメール同期**
   - 同一スレッドのメールを1つのタスクとして管理
   - Re:, Fwd: を除去した件名での重複判定
   - In-Reply-To ヘッダーによるスレッド識別

2. **AI駆動のタスク管理**
   - メール内容からタスクステータスを自動判定（todo/progress/done）
   - 既存タスクの進捗自動更新
   - タスクに関する詳細調査・分析機能

3. **コスト最適化**
   - バッチ処理による API コール削減
   - 1回のAPIコールで最大10スレッドを同時処理
   - 月額1万円以下での運用を実現

## データモデル

### Task（タスク）

```typescript
interface Task {
  id: UUID;
  title: string;
  description?: string;
  status: 'todo' | 'progress' | 'done';  // 変更: 3段階ステータス
  priority: 'high' | 'medium' | 'low';
  
  // メール関連
  source_email_id?: UUID;
  source_email_link?: string;  // 元メールへの直接リンク
  email_summary?: string;       // メール要約
  
  // 追跡情報
  created_by: 'ai' | 'user';    // 作成者の識別
  updated_by: 'ai' | 'user';    // 更新者の識別
  
  // 日時
  due_date?: DateTime;
  created_at: DateTime;
  updated_at: DateTime;
  completed_at?: DateTime;
  
  // リレーション
  user_id: UUID;
  user: User;
  history: TaskHistory[];
  ai_supports: AISupport[];
}
```

### ステータスの判定ルール

- **TODO**: 新規依頼、質問、未着手のタスク
- **PROGRESS**: 「着手」「開始」「進行中」などの表現を含む
- **DONE**: 「完了」「終了」「できました」などの表現を含む

## API エンドポイント

### タスク管理

#### タスク一覧取得
```http
GET /api/v1/tasks
```

**クエリパラメータ**:
- `status`: `todo` | `progress` | `done`
- `priority`: `high` | `medium` | `low`
- `created_by`: `ai` | `user`
- `search`: 検索キーワード

**レスポンス**:
```json
{
  "tasks": [
    {
      "id": "uuid",
      "title": "プロジェクト計画書の作成",
      "status": "progress",
      "priority": "high",
      "created_by": "user",
      "updated_by": "ai",
      "email_summary": "関連メール3件...",
      "source_email_link": "https://mail.google.com/..."
    }
  ],
  "total": 10,
  "page": 1
}
```

#### タスク作成（手動）
```http
POST /api/v1/tasks
```

**リクエストボディ**:
```json
{
  "title": "新規タスク",
  "description": "詳細説明",
  "status": "todo",
  "priority": "medium",
  "due_date": "2024-02-01T00:00:00Z"
}
```

#### タスクステータス更新
```http
PATCH /api/v1/tasks/{id}/status
```

**リクエストボディ**:
```json
{
  "status": "progress",
  "updated_by": "user"
}
```

### メール同期

#### メール同期実行
```http
POST /api/v1/email/sync
```

**リクエストボディ**:
```json
{
  "account_id": "email_account_uuid",
  "since_date": "2024-01-01T00:00:00Z"  // オプション
}
```

**処理フロー**:
1. 最後の同期日時以降のメールを取得
2. スレッドごとにグループ化
3. 1回のAI APIコールで一括分析
4. 新規タスク作成 or 既存タスク更新

### AI機能

#### タスク調査
```http
POST /api/v1/tasks/{id}/investigate
```

**レスポンス**:
```json
{
  "investigation": {
    "analysis": "技術的実装方法...",
    "recommendations": ["推奨事項1", "推奨事項2"],
    "estimated_hours": 8,
    "risks": ["リスク1", "リスク2"],
    "next_steps": ["次のステップ1", "次のステップ2"]
  }
}
```

## OpenAI API 統合

### 使用モデル

- **メール分析**: GPT-3.5-turbo（コスト効率重視）
- **タスク調査**: GPT-3.5-turbo または GPT-4（必要に応じて）

### コスト管理

```python
class OpenAICostTracker:
    # 料金設定（2024年1月）
    PRICING = {
        "gpt-3.5-turbo": {
            "input": 0.0005,   # per 1K tokens
            "output": 0.0015   # per 1K tokens
        }
    }
```

**月間予算目安**:
- 予算: 1万円（約$70）
- 処理可能リクエスト: 約50,000回
- ユーザー2-3名で十分な容量

### プロンプト設計

#### メール分析プロンプト

```python
system_prompt = """
メール内容を分析して、以下を判定してください：
1. 新規タスクとして作成すべきか
2. 既存タスクの進捗更新が必要か
3. タスクのステータス（todo/progress/done）

判定基準：
- 「着手」「開始」→ status: "progress"
- 「完了」「終了」→ status: "done"
- それ以外 → status: "todo"
"""
```

## フロントエンド実装

### タスクカード表示

```typescript
interface TaskCardProps {
  task: Task;
  onStatusChange: (status: 'todo' | 'progress' | 'done') => void;
}

// ステータス表示
const StatusBadge = ({ status, updatedBy }) => (
  <div className="flex items-center">
    <Select value={status} onValueChange={onStatusChange}>
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="todo">TODO</SelectItem>
        <SelectItem value="progress">進行中</SelectItem>
        <SelectItem value="done">完了</SelectItem>
      </SelectContent>
    </Select>
    {updatedBy === 'ai' && <Bot className="ml-2" />}
  </div>
);
```

### タスク詳細画面

3つのタブで情報を整理：

1. **概要タブ**: タスクの基本情報とステータス
2. **メール内容タブ**: 関連メールの要約表示
3. **AI調査タブ**: タスクに関する詳細分析

## データベース設計

### マイグレーション（SQLAlchemy）

```python
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum('todo', 'progress', 'done'), default='todo')
    priority = Column(Enum('high', 'medium', 'low'), default='medium')
    
    # メール関連
    source_email_id = Column(UUID, ForeignKey('processed_emails.id'))
    source_email_link = Column(String(500))
    email_summary = Column(Text)
    
    # 追跡情報
    created_by = Column(String(50), default='user')
    updated_by = Column(String(50), default='user')
    
    # インデックス
    __table_args__ = (
        Index('idx_task_user_status', 'user_id', 'status'),
        Index('idx_task_created_at', 'created_at'),
    )
```

## セキュリティ

### 認証・認可

- **JWT トークンベース認証**
  - アクセストークン: 1時間（メモリ保持のみ）
  - リフレッシュトークン: 30日（セッション管理）
  - トークンは localStorage に保存しない（XSS対策）

### タスクアクセス制御

- **所有者ベースのアクセス制御**
  - 各タスクは作成したユーザーのみアクセス可能
  - タスク ID に UUID を使用（推測不可能）
  - APIレベルでユーザー検証を実施

### データ保護

- **暗号化**
  - OAuth トークンの暗号化（AES-256）
  - パスワードのハッシュ化（bcrypt）
  - HTTPS 強制通信

### セキュリティヘッダー

- **HTTPセキュリティヘッダー**
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Strict-Transport-Security: max-age=31536000
  - Content-Security-Policy: default-src 'self'
  - Referrer-Policy: strict-origin-when-cross-origin

### CORS設定

- **厳格なCORS設定**
  - 許可オリジン: 環境変数で明示的に指定
  - 許可メソッド: GET, POST, PUT, DELETE, OPTIONS のみ
  - 許可ヘッダー: Authorization, Content-Type, X-Requested-With
  - 認証情報: credentials を含むリクエストのみ許可

### フロントエンドセキュリティ

- **XSS対策**
  - React による自動エスケープ
  - dangerouslySetInnerHTML の不使用
  - ユーザー入力の適切なサニタイズ

- **CSRF対策**
  - X-Requested-With ヘッダーの検証
  - SameSite Cookie 属性の使用

### 機密情報管理

- **環境変数**
  - 機密情報は環境変数で管理
  - .env ファイルは Git 管理外
  - 本番環境ではセキュアな設定管理サービスを使用

### 監査とロギング

- **セキュリティイベントの記録**
  - 認証失敗の記録
  - 不正アクセス試行の検出
  - APIレート制限の実装

## パフォーマンス最適化

### キャッシュ戦略

```python
class CacheService:
    async def get_user_tasks(self, user_id, filters):
        cache_key = f"tasks:{user_id}:{hash(filters)}"
        
        # キャッシュ確認
        if cached := await redis.get(cache_key):
            return json.loads(cached)
        
        # DB取得とキャッシュ
        tasks = await db.fetch_tasks(user_id, filters)
        await redis.setex(cache_key, 300, json.dumps(tasks))
        return tasks
```

### バッチ処理

- メール同期: 100件ごとにバッチ処理
- AI分析: 10スレッドを1回のAPIコールで処理

## エラーハンドリング

```python
class ErrorCode(Enum):
    # タスク関連
    TASK_NOT_FOUND = "TASK001"
    INVALID_STATUS = "TASK002"
    
    # AI関連
    AI_SERVICE_ERROR = "AI001"
    AI_QUOTA_EXCEEDED = "AI002"
    
    # メール関連
    EMAIL_SYNC_FAILED = "EMAIL001"
    INVALID_PROVIDER = "EMAIL002"
```

## 今後の拡張計画

### Phase 1（実装済み）
- ✅ メール同期とタスク自動生成
- ✅ ステータス自動判定（todo/progress/done）
- ✅ AI調査機能
- ✅ 手動タスク作成

### Phase 2（計画中）
- [ ] チーム機能（タスクの共有・割り当て）
- [ ] 通知機能（Slack/Teams連携）
- [ ] レポート生成（週次/月次）
- [ ] カレンダー連携

### Phase 3（将来）
- [ ] 予測分析（完了日予測、リスク予測）
- [ ] 自動タスク割り当て
- [ ] プロジェクトテンプレート
- [ ] AI による作業時間見積もり

---

最終更新: 2024年1月
バージョン: 2.0.0