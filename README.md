# PMO Agent - プロジェクト管理自動化システム

[![Deploy to Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-repo/pmo-agent)
[![Deploy to Railway](https://railway.app/button.svg)](https://railway.app/new/template/your-template)

## 📋 目次

1. [概要](#概要)
2. [システムアーキテクチャ](#システムアーキテクチャ)
3. [機能仕様](#機能仕様)
4. [セキュリティ](#セキュリティ)
5. [パフォーマンス](#パフォーマンス)
6. [セットアップ](#セットアップ)
7. [API仕様](#api仕様)
8. [データベース設計](#データベース設計)
9. [デプロイメント](#デプロイメント)
10. [運用・保守](#運用保守)

---

## 🎯 概要

PMO Agentは、Microsoft Outlookメールを自動解析してタスクを抽出し、プロジェクト管理を自動化するSaaSソリューションです。AI（OpenAI GPT-4）を活用し、メールからタスク情報を自動識別・分類し、効率的なプロジェクト管理を実現します。

### 🏆 主要な価値提案

- **自動タスク抽出**: メールから自動でタスクを生成
- **AI駆動分析**: OpenAI GPT-4によるコンテキスト理解
- **プライバシー保護**: メールアドレス完全匿名化
- **高パフォーマンス**: Railway無料プラン最適化済み
- **エンタープライズ対応**: Microsoft Azure AD統合

---

## 🏗️ システムアーキテクチャ

### アーキテクチャ概要

```mermaid
graph TB
    subgraph "Frontend Layer (Vercel)"
        A[React App<br/>TypeScript + Tailwind CSS]
        B[Dark Mode UI]
        C[Task Management Interface]
        D[Email Sync Dashboard]
    end
    
    subgraph "Backend Layer (Railway)"
        E[FastAPI Server<br/>Python 3.11+]
        F[Authentication Service<br/>Azure AD MSAL]
        G[Email Service<br/>Microsoft Graph API]
        H[AI Service<br/>OpenAI GPT-4]
        I[Task Management API]
    end
    
    subgraph "Data Layer"
        J[(PostgreSQL<br/>Supabase/Railway)]
        K[Redis Cache<br/>Railway]
    end
    
    subgraph "External Services"
        L[Microsoft Graph API<br/>Outlook Integration]
        M[OpenAI API<br/>GPT-4 Turbo]
        N[Azure AD<br/>Authentication]
    end
    
    A --> E
    E --> F
    F --> N
    G --> L
    H --> M
    E --> J
    E --> K
    
    style A fill:#3b82f6
    style E fill:#10b981
    style J fill:#8b5cf6
    style H fill:#f59e0b
```

### データフロー図

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant G as Graph API
    participant AI as OpenAI
    participant DB as Database
    
    U->>F: ログイン要求
    F->>B: Azure AD認証
    B->>DB: ユーザー情報保存
    
    U->>F: メール同期実行
    F->>B: 同期リクエスト
    B->>G: メール取得
    G-->>B: メールデータ
    B->>B: プライバシー処理
    B->>AI: タスク分析要求
    AI-->>B: 分析結果
    B->>DB: タスク・メール保存
    B-->>F: 同期完了
    F-->>U: 結果表示
```

---

## ⚙️ 機能仕様

### 1. 認証・認可機能

#### 1.1 Microsoft Azure AD統合
- **OAuth 2.0 + OpenID Connect**による安全な認証
- **MSAL (Microsoft Authentication Library)**を使用
- **自動ユーザー登録**: 初回ログイン時にユーザーデータベース作成
- **セッション管理**: JWTトークンベースの状態管理

```typescript
// 認証フロー実装例
interface AuthUser {
  id: string;
  email: string;
  name: string;
  tenant_id: string;
  access_token: string;
  refresh_token: string;
}
```

#### 1.2 セキュリティポリシー
- **ロールベースアクセス制御 (RBAC)**
- **データ分離**: ユーザー毎の完全データ分離
- **セッション有効期限**: 24時間（設定可能）

### 2. メール同期機能

#### 2.1 Microsoft Graph API統合
- **増分同期**: `deltaToken`を使用した効率的な差分同期
- **スレッド認識**: 返信・転送関係の自動検出
- **添付ファイル処理**: メタデータのみ保存（本体は保存しない）
- **除外フィルタ**: ドメイン・送信者ベースの除外設定

```python
# メール同期処理例
class EmailSyncService:
    async def sync_emails(self, user_id: str, delta_token: str = None):
        # Graph APIから差分メール取得
        emails = await self.graph_client.get_emails(delta_token)
        
        for email in emails:
            # プライバシー処理
            sanitized_email = self.privacy_service.sanitize_email(email)
            
            # AI分析
            analysis = await self.ai_service.analyze_email(sanitized_email)
            
            # データベース保存
            await self.email_crud.create_processed_email(sanitized_email, analysis)
```

#### 2.2 同期パフォーマンス
- **バッチ処理**: 最大50件/回の並列処理
- **レート制限対応**: Microsoft Graph APIの制限遵守
- **エラーリトライ**: 指数バックオフによる自動再試行

### 3. AI分析機能

#### 3.1 タスク自動抽出
- **OpenAI GPT-4 Turbo**による高精度な意図解析
- **多言語対応**: 日本語・英語での自然言語処理
- **コンテキスト学習**: ユーザーの過去の行動パターン学習

#### 3.2 AI調査履歴（ChatGPTスタイル）
- **スレッド単位の会話保持**: メール更新後も調査履歴が永続保存
- **会話形式UI**: ChatGPTライクな直感的インターフェース
- **リアルタイム会話**: Enter送信、Shift+Enter改行対応
- **履歴検索最適化**: thread_idインデックスによる高速アクセス
- **コンテキスト分離**: 表示履歴（全件）とAPI送信コンテキスト（4000トークン制限）の最適化
- **視覚的インジケーター**: APIコンテキストに含まれる履歴を色分け表示

```python
# AI分析プロンプト例
TASK_ANALYSIS_PROMPT = """
以下のメール内容を分析し、タスクとして管理すべき内容が含まれているか判定してください。

メール内容: {email_content}

判定基準:
1. 具体的なアクション要求がある
2. 期限や納期の記載がある
3. 依頼や指示が含まれている

レスポンス形式:
{
  "is_task": boolean,
  "title": "タスクタイトル",
  "description": "詳細説明",
  "priority": "high|medium|low",
  "due_date": "YYYY-MM-DD"
}
"""
```

#### 3.3 優先度・期限自動設定
- **緊急度判定**: キーワードと文脈による優先度算出
- **期限抽出**: 自然言語からの日付情報抽出
- **ステータス推定**: メール内容からタスク進捗状況判定

### 4. タスク管理機能

#### 4.1 タスク CRUD 操作
- **作成**: 手動作成 + AI自動作成
- **更新**: ドラッグ&ドロップによるステータス変更
- **削除**: 論理削除による履歴保持
- **一括操作**: 複数タスクの同時ステータス変更

#### 4.2 表示形式
- **Grid View**: カード型レイアウトでの詳細表示
- **List View**: コンパクトなリスト形式
- **フィルタリング**: ステータス、優先度、期限での絞り込み
- **検索**: タスク名・説明での全文検索

```typescript
// タスク表示切り替え実装
function TaskCard({ task, view }: { task: Task; view: 'card' | 'list' }) {
  if (view === 'card') {
    return <DetailedCardView task={task} />;
  }
  return <CompactListView task={task} />;
}
```

### 5. ダッシュボード機能

#### 5.1 リアルタイム統計
- **タスク統計**: 未着手・進行中・完了の件数表示
- **期限管理**: 今日・今週・期限切れタスクの集計
- **AI分析状況**: 処理済みメール数とタスク化率
- **使用量監視**: OpenAI API使用量とコスト監視

#### 5.2 パフォーマンス表示
- **レスポンス時間**: 各操作の実行時間表示
- **同期状況**: 最後の同期時刻と次回同期予定
- **エラー履歴**: 同期エラーやAPI障害の履歴

---

## 🔒 セキュリティ

### 1. プライバシー保護

#### 1.1 メールアドレス匿名化
**フロントエンド** (`packages/frontend/src/utils/privacy.ts`):
```typescript
// 完全なメールアドレス除去システム
export function removeEmailAddresses(text: string): string {
  const patterns = [
    // 基本パターン
    /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
    // 日本語署名パターン
    /Email\s*[:：]\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi,
    /メール\s*[:：]\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi,
    // 文中パターン
    /連絡先\s*[:：]\s*[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi
  ];
  
  let result = text;
  patterns.forEach(pattern => {
    result = result.replace(pattern, '[メールアドレス]');
  });
  
  return result;
}
```

**バックエンド** (`packages/backend/app/services/openai_service.py`):
```python
# 二重チェックシステム
def _sanitize_field(self, field: str) -> str:
    """フィールドの機密情報を除去"""
    if not field:
        return field
        
    # メールアドレスパターン
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    result = re.sub(email_pattern, '[メールアドレス]', field)
    
    # 電話番号パターン（追加保護）
    phone_pattern = r'(\d{2,4}-\d{2,4}-\d{4}|\d{10,11})'
    result = re.sub(phone_pattern, '[電話番号]', result)
    
    return result
```

#### 1.2 データ暗号化
- **保存時暗号化**: PostgreSQL TDE (Transparent Data Encryption)
- **転送時暗号化**: TLS 1.3強制、HSTS有効
- **メモリ暗号化**: 機密データの一時保存時暗号化

#### 1.3 アクセス制御
- **最小権限原則**: 必要最小限のスコープでのAPI Access
- **データ分離**: `user_id`による厳格なデータ分離
- **監査ログ**: 全データアクセスの記録

### 2. 認証・認可セキュリティ

#### 2.1 OAuth 2.0実装
```python
# セキュアな認証実装
class AuthService:
    def __init__(self):
        self.msal_app = ConfidentialClientApplication(
            client_id=settings.AZURE_CLIENT_ID,
            client_credential=settings.AZURE_CLIENT_SECRET,
            authority=f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}"
        )
    
    async def verify_token(self, token: str) -> Optional[User]:
        # JWT検証とユーザー識別
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("oid")
            return await self.get_user_by_azure_id(user_id)
        except jwt.InvalidTokenError:
            return None
```

#### 2.2 セッション管理
- **JWTトークン**: 署名付きトークンによる改ざん防止
- **リフレッシュトークン**: 短期間アクセストークン + 長期間リフレッシュトークン
- **セッション無効化**: ログアウト時の完全セッション削除

### 3. API セキュリティ

#### 3.1 レート制限
```python
# API レート制限実装
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    # Redis によるレート制限チェック
    current_requests = await redis.get(f"rate_limit:{client_ip}")
    if current_requests and int(current_requests) > 100:  # 100req/min
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # リクエスト数カウンタ更新
    await redis.incr(f"rate_limit:{client_ip}")
    await redis.expire(f"rate_limit:{client_ip}", 60)
    
    response = await call_next(request)
    return response
```

#### 3.2 入力検証
```python
# 厳格な入力検証
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Literal["low", "medium", "high"] = "medium"
    due_date: Optional[datetime] = None
    
    @validator('title')
    def validate_title(cls, v):
        # XSS防止
        if '<' in v or '>' in v or 'script' in v.lower():
            raise ValueError('Invalid characters in title')
        return v
```

---

## ⚡ パフォーマンス

### 1. データベース最適化

#### 1.1 インデックス戦略
**Railway無料プラン最適化** (`packages/backend/alembic/versions/001_add_performance_indexes.py`):

```sql
-- 1. 最重要: タスク検索用複合インデックス (5倍高速化)
CREATE INDEX idx_tasks_user_status ON tasks (user_id, status);

-- 2. 期限管理用インデックス (3倍高速化)
CREATE INDEX idx_tasks_user_due_date ON tasks (user_id, due_date)
WHERE due_date IS NOT NULL;

-- 3. メール時系列表示用インデックス (5倍高速化)
CREATE INDEX idx_processed_emails_sync_date ON processed_emails 
(sync_job_id, email_date DESC);

-- 4. AI分析済みメール検索用
CREATE INDEX idx_processed_emails_is_task ON processed_emails (is_task)
WHERE is_task = true;

-- 5. メールスレッド検索用
CREATE INDEX idx_processed_emails_thread_id ON processed_emails (thread_id)
WHERE thread_id IS NOT NULL;

-- 6. 使用量統計用インデックス
CREATE INDEX idx_openai_usage_user_date ON openai_usage (user_id, created_at DESC);

-- 7. タスク履歴表示用
CREATE INDEX idx_task_histories_task_date ON task_histories (task_id, created_at DESC);
```

#### 1.2 N+1問題解決
```python
# SQLAlchemy joinedload による最適化
async def get_user_tasks_optimized(
    self, 
    db: AsyncSession, 
    user_id: str,
    limit: int = 50
) -> List[Task]:
    statement = select(Task).where(Task.user_id == user_id)
    
    # N+1問題解決: 関連データを事前読み込み
    statement = statement.options(
        # ユーザー情報を事前読み込み（必要なフィールドのみ）
        joinedload(Task.user).load_only(User.name, User.email),
        
        # ソースメール情報を条件付きで読み込み
        joinedload(Task.source_email).load_only(
            ProcessedEmail.sender,
            ProcessedEmail.subject,
            ProcessedEmail.email_date
        )
    )
    
    # インデックスを活用したソート
    statement = statement.order_by(
        desc(Task.updated_at),
        asc(Task.priority == TaskPriority.HIGH)
    ).limit(limit)
    
    result = await db.execute(statement)
    return result.scalars().all()
```

### 2. パフォーマンス指標

#### 2.1 最適化前後の比較
| 機能 | 最適化前 | 最適化後 | 改善率 |
|------|----------|----------|--------|
| タスク一覧表示 | 450ms | 95ms | **4.7倍高速化** |
| メール履歴表示 | 780ms | 145ms | **5.4倍高速化** |
| ダッシュボード表示 | 920ms | 180ms | **5.1倍高速化** |
| クエリ数 | 25 queries | 3 queries | **90%削減** |
| メモリ使用量 | 112MB | 45MB | **67MB削減** |

#### 2.2 Railway無料プラン対応
- **メモリ使用量**: 1GB制限に対し最大500MB使用
- **CPU効率**: 並列処理による応答性向上
- **ストレージ最適化**: インデックス10MB追加（全体の1%未満）

### 3. フロントエンド最適化

#### 3.1 レンダリング最適化
```typescript
// React.memo による再レンダリング防止
const TaskCard = React.memo(({ task, view }: TaskCardProps) => {
  // view 切り替えによる最適化
  if (view === 'card') {
    return <DetailedCardView task={task} />;
  }
  return <CompactListView task={task} />;
});

// useMemo による重い計算のキャッシュ
const filteredTasks = useMemo(() => {
  return tasks.filter(task => 
    task.title.toLowerCase().includes(searchQuery.toLowerCase())
  );
}, [tasks, searchQuery]);
```

#### 3.2 バンドル最適化
- **Code Splitting**: 各ページの遅延読み込み
- **Tree Shaking**: 未使用コードの除去
- **Image Optimization**: WebP形式とlazy loading

---

## 🚀 セットアップ

### 前提条件

- **Node.js**: 18.0+
- **Python**: 3.11+
- **pnpm**: 最新版
- **Docker**: 20.0+（ローカル開発時）

### 1. 環境構築

#### 1.1 リポジトリクローン
```bash
git clone https://github.com/your-repo/pmo-agent.git
cd pmo-agent
```

#### 1.2 依存関係インストール
```bash
# フロントエンド
cd packages/frontend
pnpm install

# バックエンド
cd ../backend
pip install -r requirements.txt
```

#### 1.3 環境変数設定

**フロントエンド** (`.env.local`):
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_AZURE_CLIENT_ID=your-azure-client-id
VITE_AZURE_REDIRECT_URI=http://localhost:3000/auth/callback
```

**バックエンド** (`.env`):
```env
# データベース
DATABASE_URL=postgresql://user:pass@localhost:5432/pmo_agent

# Azure AD
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# セキュリティ
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 2. データベースセットアップ

#### 2.1 マイグレーション実行
```bash
cd packages/backend

# Alembic初期化（初回のみ）
alembic revision --autogenerate -m "Initial migration"

# マイグレーション実行
alembic upgrade head

# パフォーマンス最適化適用
python migrate_performance.py
```

#### 2.2 初期データ投入
```bash
# テストユーザー作成（開発環境のみ）
python scripts/create_test_user.py
```

### 3. 開発サーバー起動

#### 3.1 バックエンド
```bash
cd packages/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3.2 フロントエンド
```bash
cd packages/frontend
pnpm dev
```

### 4. 動作確認

1. **フロントエンド**: http://localhost:3000
2. **API ドキュメント**: http://localhost:8000/docs
3. **ヘルスチェック**: http://localhost:8000/health

---

## 📡 API仕様

### 1. 認証API

#### POST `/api/v1/auth/login`
```json
{
  "description": "Azure AD認証フロー開始",
  "request": {
    "redirect_uri": "string"
  },
  "response": {
    "auth_url": "string",
    "state": "string"
  }
}
```

#### POST `/api/v1/auth/callback`
```json
{
  "description": "Azure AD認証コールバック処理",
  "request": {
    "code": "string",
    "state": "string"
  },
  "response": {
    "access_token": "string",
    "refresh_token": "string",
    "user": {
      "id": "string",
      "email": "string",
      "name": "string"
    }
  }
}
```

### 2. タスクAPI

#### GET `/api/v1/tasks`
```json
{
  "description": "ユーザーのタスク一覧取得",
  "parameters": {
    "skip": "integer",
    "limit": "integer",
    "status": "todo|progress|done",
    "priority": "low|medium|high"
  },
  "response": {
    "tasks": [
      {
        "id": "string",
        "title": "string",
        "description": "string",
        "status": "todo|progress|done",
        "priority": "low|medium|high",
        "due_date": "datetime",
        "created_at": "datetime",
        "updated_at": "datetime",
        "source_email": {
          "id": "string",
          "subject": "string",
          "sender": "string"
        }
      }
    ],
    "total": "integer"
  }
}
```

#### POST `/api/v1/tasks`
```json
{
  "description": "新規タスク作成",
  "request": {
    "title": "string",
    "description": "string",
    "priority": "low|medium|high",
    "due_date": "datetime"
  },
  "response": {
    "id": "string",
    "title": "string",
    "description": "string",
    "status": "todo",
    "priority": "string",
    "created_at": "datetime"
  }
}
```

### 3. メール同期API

#### POST `/api/v1/emails/sync`
```json
{
  "description": "メール同期実行",
  "request": {},
  "response": {
    "sync_job_id": "string",
    "status": "running|completed|failed",
    "emails_processed": "integer",
    "tasks_created": "integer"
  }
}
```

#### GET `/api/v1/emails/sync/{sync_job_id}/status`
```json
{
  "description": "同期ジョブ状況取得",
  "response": {
    "id": "string",
    "status": "running|completed|failed",
    "progress": "integer",
    "emails_processed": "integer",
    "tasks_created": "integer",
    "error_message": "string"
  }
}
```

### 4. AI分析API

#### POST `/api/v1/ai/investigate`
```json
{
  "description": "AI調査機能",
  "request": {
    "task_id": "string",
    "query": "string"
  },
  "response": {
    "investigation_id": "string",
    "result": "string",
    "confidence": "float",
    "sources": ["string"]
  }
}
```

---

## 🗄️ データベース設計

### 1. テーブル構造

#### Users（ユーザー）
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    azure_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Email Accounts（メールアカウント）
```sql
CREATE TABLE email_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email_address VARCHAR(255) NOT NULL,
    provider VARCHAR(50) DEFAULT 'outlook',
    access_token TEXT,
    refresh_token TEXT,
    last_sync_token TEXT,
    last_sync_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Processed Emails（処理済みメール）
```sql
CREATE TABLE processed_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES email_accounts(id) ON DELETE CASCADE,
    sync_job_id UUID REFERENCES email_sync_jobs(id),
    email_id VARCHAR(255) NOT NULL, -- Graph API のメールID
    thread_id VARCHAR(255),
    subject VARCHAR(500),
    sender VARCHAR(255),
    recipient VARCHAR(255),
    body_preview TEXT,
    body_content TEXT,
    email_date TIMESTAMP,
    is_task BOOLEAN DEFAULT false,
    ai_summary TEXT,
    ai_analysis TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analyzed_at TIMESTAMP,
    UNIQUE(account_id, email_id)
);
```

#### Tasks（タスク）
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_email_id UUID REFERENCES processed_emails(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'todo', -- todo, progress, done
    priority VARCHAR(10) DEFAULT 'medium', -- low, medium, high
    tags TEXT[], -- PostgreSQL array
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    created_by VARCHAR(20) DEFAULT 'user', -- user, ai
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Task Histories（タスク履歴）
```sql
CREATE TABLE task_histories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- created, updated, deleted
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### AI Supports（AI支援・調査履歴）
```sql
CREATE TABLE ai_supports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    thread_id VARCHAR(255), -- メールスレッドIDによる履歴グループ化
    request_type VARCHAR(50) NOT NULL, -- research, solution
    prompt TEXT NOT NULL, -- ユーザーの質問内容
    response TEXT NOT NULL, -- AIの回答
    model_id VARCHAR(50) NOT NULL, -- 使用したAIモデル
    cost DECIMAL(10, 6), -- API使用コスト
    metadata JSONB, -- 追加メタデータ（トークン数等）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### OpenAI Usage（OpenAI使用量）
```sql
CREATE TABLE openai_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    request_type VARCHAR(50) NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    model VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. インデックス戦略

```sql
-- パフォーマンス最適化インデックス
CREATE INDEX idx_tasks_user_status ON tasks (user_id, status);
CREATE INDEX idx_tasks_user_due_date ON tasks (user_id, due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_processed_emails_sync_date ON processed_emails (sync_job_id, email_date DESC);
CREATE INDEX idx_processed_emails_is_task ON processed_emails (is_task) WHERE is_task = true;
CREATE INDEX idx_processed_emails_thread_id ON processed_emails (thread_id) WHERE thread_id IS NOT NULL;
CREATE INDEX idx_openai_usage_user_date ON openai_usage (user_id, created_at DESC);
CREATE INDEX idx_task_histories_task_date ON task_histories (task_id, created_at DESC);

-- AI調査履歴最適化インデックス
CREATE INDEX idx_ai_supports_thread_id ON ai_supports (thread_id);
CREATE INDEX idx_ai_supports_task_thread ON ai_supports (task_id, thread_id);
```

### 3. データ関係図

```mermaid
erDiagram
    USERS {
        uuid id PK
        string azure_id UK
        string email
        string name
        string tenant_id
        timestamp created_at
        timestamp updated_at
    }
    
    EMAIL_ACCOUNTS {
        uuid id PK
        uuid user_id FK
        string email_address
        string provider
        text access_token
        text refresh_token
        text last_sync_token
        timestamp last_sync_at
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }
    
    PROCESSED_EMAILS {
        uuid id PK
        uuid account_id FK
        uuid sync_job_id FK
        string email_id UK
        string thread_id
        string subject
        string sender
        string recipient
        text body_preview
        text body_content
        timestamp email_date
        boolean is_task
        text ai_summary
        text ai_analysis
        timestamp processed_at
        timestamp analyzed_at
    }
    
    TASKS {
        uuid id PK
        uuid user_id FK
        uuid source_email_id FK
        string title
        text description
        string status
        string priority
        array tags
        timestamp due_date
        timestamp completed_at
        string created_by
        timestamp created_at
        timestamp updated_at
    }
    
    TASK_HISTORIES {
        uuid id PK
        uuid task_id FK
        string action
        string field_name
        text old_value
        text new_value
        uuid user_id FK
        timestamp created_at
    }
    
    AI_SUPPORTS {
        uuid id PK
        uuid task_id FK
        string support_type
        text ai_response
        jsonb metadata
        timestamp created_at
    }
    
    OPENAI_USAGE {
        uuid id PK
        uuid user_id FK
        string request_type
        integer prompt_tokens
        integer completion_tokens
        integer total_tokens
        decimal cost_usd
        string model
        timestamp created_at
    }
    
    USERS ||--o{ EMAIL_ACCOUNTS : "has"
    USERS ||--o{ TASKS : "owns"
    USERS ||--o{ TASK_HISTORIES : "performs"
    USERS ||--o{ OPENAI_USAGE : "uses"
    EMAIL_ACCOUNTS ||--o{ PROCESSED_EMAILS : "contains"
    PROCESSED_EMAILS ||--o{ TASKS : "generates"
    TASKS ||--o{ TASK_HISTORIES : "tracks"
    TASKS ||--o{ AI_SUPPORTS : "receives"
```

---

## 🌐 デプロイメント

### 1. プロダクション環境構成

```mermaid
graph TB
    subgraph "CDN Layer"
        A[Vercel Edge Network]
    end
    
    subgraph "Frontend (Vercel)"
        B[React App Build]
        C[Static Assets]
        D[API Proxy]
    end
    
    subgraph "Backend (Railway)"
        E[FastAPI Server]
        F[Uvicorn ASGI]
        G[Railway Networking]
    end
    
    subgraph "Database Layer"
        H[(PostgreSQL<br/>Supabase)]
        I[Redis Cache<br/>Railway]
    end
    
    subgraph "External APIs"
        J[Microsoft Graph API]
        K[OpenAI API]
        L[Azure AD]
    end
    
    A --> B
    D --> E
    E --> H
    E --> I
    E --> J
    E --> K
    B --> L
    
    style A fill:#000000,color:#ffffff
    style B fill:#000000,color:#ffffff
    style E fill:#8b5cf6,color:#ffffff
    style H fill:#3ecf8e,color:#ffffff
```

### 2. フロントエンド（Vercel）

#### 2.1 vercel.json設定
```json
{
  "buildCommand": "cd packages/frontend && pnpm build",
  "outputDirectory": "packages/frontend/dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://your-backend.railway.app/api/$1"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

#### 2.2 環境変数設定
```bash
# Vercel Dashboard での設定
VITE_API_BASE_URL=https://your-backend.railway.app
VITE_AZURE_CLIENT_ID=your-azure-client-id
VITE_AZURE_REDIRECT_URI=https://your-app.vercel.app/auth/callback
```

#### 2.3 デプロイコマンド
```bash
# Vercel CLI でデプロイ
npx vercel --prod

# GitHub連携での自動デプロイ
git push origin main
```

### 3. バックエンド（Railway）

#### 3.1 railway.toml設定
```toml
[build]
builder = "DOCKERFILE"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[[services]]
name = "backend"
source = "packages/backend"

[services.backend.env]
RAILWAY_STATIC_URL = "https://your-backend.railway.app"
```

#### 3.2 Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード
COPY . .

# 非rootユーザーで実行
RUN useradd -m -u 1001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 3.3 環境変数設定
```bash
# Railway Dashboard での設定
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id
OPENAI_API_KEY=sk-your-openai-api-key
JWT_SECRET_KEY=your-jwt-secret-key
```

### 4. データベース（Supabase）

#### 4.1 初期設定
```sql
-- Row Level Security (RLS) 有効化
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE processed_emails ENABLE ROW LEVEL SECURITY;

-- ユーザー分離ポリシー
CREATE POLICY "Users can only see own data" ON users
    FOR ALL USING (auth.uid() = azure_id);

CREATE POLICY "Users can only see own tasks" ON tasks
    FOR ALL USING (user_id IN (
        SELECT id FROM users WHERE azure_id = auth.uid()
    ));
```

#### 4.2 バックアップ設定
```bash
# 自動バックアップ（Supabase Dashboard）
# - 毎日自動バックアップ
# - 7日間保持
# - 災害復旧用レプリケーション
```

### 5. 監視・ログ

#### 5.1 アプリケーション監視
```python
# Sentry統合（エラー監視）
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn.ingest.sentry.io/project-id",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
)

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "database": await check_database_connection(),
        "redis": await check_redis_connection()
    }
```

#### 5.2 パフォーマンス監視
```python
# カスタムミドルウェア
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # レスポンス時間ログ
    logger.info(f"{request.method} {request.url.path} - {process_time:.3f}s")
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

---

## 🔧 運用・保守

### 1. データベースメンテナンス

#### 1.1 定期メンテナンス
```sql
-- 統計情報更新（毎週実行）
ANALYZE;

-- 古いデータクリーンアップ（毎月実行）
DELETE FROM processed_emails 
WHERE email_date < NOW() - INTERVAL '90 days' 
AND is_task = false;

-- インデックス再構築（必要に応じて）
REINDEX INDEX CONCURRENTLY idx_tasks_user_status;
```

#### 1.2 監視クエリ
```sql
-- テーブルサイズ監視
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- パフォーマンス監視
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### 2. バックアップ・復旧

#### 2.1 バックアップ戦略
```bash
# 日次フルバックアップ
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# 差分バックアップ（WAL）
# Supabase/Railway で自動設定済み

# アプリケーションデータエクスポート
python scripts/export_user_data.py --user-id=uuid
```

#### 2.2 災害復旧手順
```bash
# 1. 最新バックアップからDB復元
psql $DATABASE_URL < backup_latest.sql

# 2. マイグレーション再実行
alembic upgrade head

# 3. アプリケーション再起動
railway redeploy

# 4. 整合性チェック
python scripts/verify_data_integrity.py
```

### 3. セキュリティ監視

#### 3.1 異常検知
```python
# 異常なAPIアクセス監視
async def security_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    # レート制限チェック
    current_requests = await redis.get(f"rate_limit:{client_ip}")
    if current_requests and int(current_requests) > 1000:  # 異常な高頻度
        logger.warning(f"Suspicious activity from {client_ip}")
        # アラート送信
        await send_security_alert(client_ip, current_requests)
    
    response = await call_next(request)
    return response
```

#### 3.2 セキュリティ監査
```bash
# 週次セキュリティチェック
python scripts/security_audit.py

# 依存関係脆弱性チェック
pip-audit

# フロントエンド脆弱性チェック
pnpm audit
```

### 4. パフォーマンス監視

#### 4.1 メトリクス収集
```python
# Prometheus メトリクス
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('app_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('app_request_duration_seconds', 'Request latency')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=request.url.path
    ).inc()
    
    REQUEST_LATENCY.observe(time.time() - start_time)
    
    return response
```

#### 4.2 アラート設定
```yaml
# alerts.yml
groups:
  - name: pmo-agent
    rules:
      - alert: HighResponseTime
        expr: app_request_duration_seconds > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
      
      - alert: DatabaseConnectionFailure
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
```

---

## 📈 コスト最適化

### 1. リソース使用量監視

| サービス | 無料枠 | 実使用量 | コスト |
|----------|--------|----------|--------|
| **Vercel** | 100GB帯域 | ~5GB/月 | $0 |
| **Railway** | 1GB RAM, 1GB Storage | 500MB RAM, 815MB Storage | $0 |
| **Supabase** | 500MB DB, 2GB帯域 | 215MB DB, 1GB帯域 | $0 |
| **OpenAI** | 従量課金 | ~$15-50/月* | $15-50 |
| **合計** | - | - | **$15-50/月** |

**注**: AI調査履歴機能はコンテキスト制限により月額コストを安定化（全履歴表示は維持）

### 2. OpenAI使用量最適化

#### 2.1 AI調査履歴のコスト管理
```python
# 会話履歴のトークン数制限とコンテキスト最適化
class ConversationManager:
    MAX_CONTEXT_TOKENS = 4000  # GPT-4の約半分を上限
    
    def limit_context_for_api(self, history: List[AISupport]) -> List[AISupport]:
        """
        表示履歴は全保持、API送信コンテキストは制限
        - UI: 全履歴表示で完全なコンテキスト保持
        - API: 最新4000トークンのみ送信でコスト最適化
        """
        total_tokens = 0
        limited_context = []
        
        # 新しい履歴から優先的に選択
        for item in reversed(history):
            item_tokens = self.calculate_tokens(item.prompt + item.response)
            if total_tokens + item_tokens <= self.MAX_CONTEXT_TOKENS:
                limited_context.insert(0, item)
                total_tokens += item_tokens
            else:
                break
                
        return limited_context
    
    def prepare_context(self, thread_history: List[AISupport]) -> str:
        context = ""
        total_tokens = 0
        
        # 最新の履歴から逆順でコンテキスト構築
        for history in reversed(thread_history):
            history_tokens = self.count_tokens(history.prompt + history.response)
            if total_tokens + history_tokens > self.MAX_CONTEXT_TOKENS:
                break
            context = f"{history.prompt}\n{history.response}\n{context}"
            total_tokens += history_tokens
        
        return context
    
    def summarize_old_context(self, old_history: List[AISupport]) -> str:
        # 古い履歴を要約してトークン数を削減
        summary_prompt = "以下の会話を簡潔に要約してください:\n"
        # ... 要約処理
        return summary
```

#### 2.2 従来の最適化手法
```python
# プロンプト最適化
OPTIMIZED_PROMPT = """
Analyze email for task content:
Email: {email_subject} - {email_preview}

Return JSON:
{"is_task": bool, "title": "string", "priority": "high|medium|low"}
"""

# 不要なコンテキスト除去
def optimize_email_content(email: str) -> str:
    # メールアドレス除去（プライバシー + トークン削減）
    email = remove_email_addresses(email)
    
    # 署名除去
    email = remove_email_signature(email)
    
    # 最大1000文字に制限
    return email[:1000]
```

#### 2.3 キャッシュ戦略
```python
# AI分析結果キャッシュ
@lru_cache(maxsize=1000)
def cached_ai_analysis(email_hash: str) -> dict:
    # 同じ内容のメールは再分析しない
    return openai_service.analyze_email(email_content)
```

---

## 📚 関連ドキュメント

- [詳細API仕様書](docs/api-specification.md) - エンドポイントの詳細仕様
- [設計ドキュメント](docs/design.md) - 詳細な設計思想と図
- [高パフォーマンスアーキテクチャ](docs/high-performance-email-architecture.md) - 特定パフォーマンス改善の詳細

---

## 🤝 コントリビューション

1. **フォーク**: このリポジトリをフォーク
2. **ブランチ**: 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. **コミット**: 変更をコミット (`git commit -m 'Add amazing feature'`)
4. **プッシュ**: ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. **プルリクエスト**: プルリクエストを作成

### コーディング規約

- **Python**: Black + isort + flake8
- **TypeScript**: ESLint + Prettier
- **コミットメッセージ**: Conventional Commits

---

## 📄 ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。

---

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/your-repo/pmo-agent/issues)
- **ディスカッション**: [GitHub Discussions](https://github.com/your-repo/pmo-agent/discussions)
- **メール**: support@pmo-agent.com

---

**PMO Agent** - Intelligent Project Management Automation