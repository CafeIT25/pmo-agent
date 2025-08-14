# PMO Agent システム設計書

## 1. アーキテクチャ概要

PMO Agent は Clean Architecture と Domain-Driven Design の原則に基づいて設計されています。フロントエンドとバックエンドを明確に分離し、それぞれが独立してスケール可能な構成を採用しています。

### 1.1 システム構成図

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        PWA[PWA<br/>将来対応]
    end
    
    subgraph "Frontend (Vercel)"
        React[React App]
        Router[React Router]
        Store[Zustand Store]
        UI[shadcn/ui Components]
    end
    
    subgraph "Backend (Railway)"
        API[FastAPI<br/>REST API]
        Auth[Auth Service]
        Task[Task Service]
        Mail[Mail Service]
        AI[AI Service]
        OAuth[OAuth Service]
        Worker[Celery Worker]
        Cost[Cost Service]
    end
    
    subgraph "Data Layer (Railway)"
        PG[(PostgreSQL)]
        Redis[(Redis)]
    end
    
    subgraph "External Services"
        Google[Gmail API]
        MS[Microsoft Graph API]
        OpenAI[OpenAI API]
        Bedrock[AWS Bedrock]
        SMTP[SMTP Server]
    end
    
    Browser --> React
    React --> API
    API --> Auth
    API --> Task
    API --> Mail
    API --> AI
    
    Auth --> PG
    Task --> PG
    Mail --> Worker
    Worker --> Redis
    Worker --> Google
    Worker --> MS
    OAuth --> Google
    OAuth --> MS
    AI --> OpenAI
    AI --> Bedrock
    Cost --> OpenAI
    Auth --> SMTP
    
    Store -.-> React
    Router -.-> React
    UI -.-> React
```

### 1.2 レイヤーアーキテクチャ

```mermaid
graph LR
    subgraph "Presentation Layer"
        Pages[Pages]
        Components[Components]
        Hooks[Custom Hooks]
    end
    
    subgraph "Application Layer"
        Services[Services]
        UseCases[Use Cases]
        DTOs[DTOs]
    end
    
    subgraph "Domain Layer"
        Entities[Entities]
        ValueObjects[Value Objects]
        DomainServices[Domain Services]
        Repositories[Repository Interfaces]
    end
    
    subgraph "Infrastructure Layer"
        DB[Database]
        APIs[External APIs]
        Cache[Cache]
        Queue[Message Queue]
    end
    
    Pages --> Components
    Components --> Hooks
    Hooks --> Services
    Services --> UseCases
    UseCases --> DomainServices
    DomainServices --> Entities
    UseCases --> Repositories
    Repositories --> DB
    Services --> APIs
```

## 2. データモデル設計

### 2.1 ER 図

```mermaid
erDiagram
    User ||--o{ EmailAccount : has
    User ||--o{ Task : owns
    User ||--o{ ExcludeDomain : configures
    EmailAccount ||--o{ EmailSyncJob : triggers
    EmailSyncJob ||--o{ ProcessedEmail : processes
    Task ||--o| ProcessedEmail : "created from"
    Task ||--o{ TaskHistory : has
    Task ||--o{ AISupport : receives
    
    User {
        uuid id PK
        string email UK
        string password_hash
        boolean is_active
        boolean is_verified
        datetime created_at
        datetime updated_at
        datetime last_login_at
    }
    
    EmailAccount {
        uuid id PK
        uuid user_id FK
        string provider "google|microsoft"
        string email
        text encrypted_tokens
        datetime token_expires_at
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    Task {
        uuid id PK
        uuid user_id FK
        string title
        text description
        string status "pending|in_progress|completed"
        string priority "high|medium|low"
        uuid source_email_id FK
        string source_email_link
        datetime due_date
        datetime created_at
        datetime updated_at
        datetime completed_at
    }
    
    ProcessedEmail {
        uuid id PK
        uuid sync_job_id FK
        string email_id UK
        string sender
        string subject
        text body_preview
        boolean is_task
        json ai_analysis
        datetime email_date
        datetime processed_at
    }
    
    EmailSyncJob {
        uuid id PK
        uuid email_account_id FK
        string status "pending|processing|completed|failed"
        integer total_emails
        integer processed_emails
        json error_details
        datetime started_at
        datetime completed_at
    }
    
    ExcludeDomain {
        uuid id PK
        uuid user_id FK
        string domain
        datetime created_at
    }
    
    TaskHistory {
        uuid id PK
        uuid task_id FK
        uuid user_id FK
        string action "created|updated|status_changed"
        json changes
        datetime created_at
    }
    
    AISupport {
        uuid id PK
        uuid task_id FK
        string request_type "research|solution"
        text prompt
        text response
        string model_id
        decimal cost
        datetime created_at
    }
```

### 2.2 インデックス戦略

```sql
-- ユーザー関連
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_last_login ON users(last_login_at);

-- タスク関連
CREATE INDEX idx_task_user_status ON tasks(user_id, status);
CREATE INDEX idx_task_user_priority ON tasks(user_id, priority);
CREATE INDEX idx_task_created_at ON tasks(created_at);
CREATE INDEX idx_task_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;

-- メール関連
CREATE INDEX idx_processed_email_email_id ON processed_emails(email_id);
CREATE INDEX idx_email_sync_job_account ON email_sync_jobs(email_account_id);
CREATE INDEX idx_email_sync_job_status ON email_sync_jobs(status);

-- 履歴関連
CREATE INDEX idx_task_history_task ON task_histories(task_id);
CREATE INDEX idx_task_history_created ON task_histories(created_at);
```

## 3. API 設計

### 3.1 エンドポイント一覧

#### 認証関連

```yaml
POST /api/v1/auth/register
  description: 新規ユーザー登録
  body:
    email: string
    password: string
  response:
    message: string

POST /api/v1/auth/verify
  description: メールアドレス確認
  body:
    token: string
  response:
    access_token: string
    refresh_token: string

POST /api/v1/auth/login
  description: ログイン
  body:
    email: string
    password: string
  response:
    access_token: string
    refresh_token: string

POST /api/v1/auth/refresh
  description: トークンリフレッシュ
  body:
    refresh_token: string
  response:
    access_token: string

POST /api/v1/auth/logout
  description: ログアウト
  headers:
    Authorization: Bearer {token}
```

#### ユーザー設定関連

```yaml
GET /api/v1/users/me
  description: 現在のユーザー情報取得
  headers:
    Authorization: Bearer {token}
  response:
    user: User

PUT /api/v1/users/me
  description: ユーザー情報更新
  headers:
    Authorization: Bearer {token}
  body:
    name?: string
    timezone?: string

GET /api/v1/users/me/email-accounts
  description: メールアカウント一覧取得
  headers:
    Authorization: Bearer {token}
  response:
    accounts: EmailAccount[]

POST /api/v1/users/me/email-accounts
  description: メールアカウント連携
  headers:
    Authorization: Bearer {token}
  body:
    provider: "google" | "microsoft"
    auth_code: string

DELETE /api/v1/users/me/email-accounts/{id}
  description: メールアカウント連携解除
  headers:
    Authorization: Bearer {token}

GET /api/v1/users/me/exclude-domains
  description: 除外ドメイン一覧取得
  headers:
    Authorization: Bearer {token}
  response:
    domains: ExcludeDomain[]

POST /api/v1/users/me/exclude-domains
  description: 除外ドメイン追加
  headers:
    Authorization: Bearer {token}
  body:
    domain: string

DELETE /api/v1/users/me/exclude-domains/{id}
  description: 除外ドメイン削除
  headers:
    Authorization: Bearer {token}
```

#### タスク関連

```yaml
GET /api/v1/tasks
  description: タスク一覧取得
  headers:
    Authorization: Bearer {token}
  query:
    status?: "pending" | "in_progress" | "completed"
    priority?: "high" | "medium" | "low"
    search?: string
    page?: number
    limit?: number
    sort?: string
  response:
    tasks: Task[]
    total: number
    page: number
    limit: number

POST /api/v1/tasks
  description: タスク作成
  headers:
    Authorization: Bearer {token}
  body:
    title: string
    description?: string
    priority?: "high" | "medium" | "low"
    due_date?: datetime

GET /api/v1/tasks/{id}
  description: タスク詳細取得
  headers:
    Authorization: Bearer {token}
  response:
    task: Task
    history: TaskHistory[]
    ai_supports: AISupport[]

PUT /api/v1/tasks/{id}
  description: タスク更新
  headers:
    Authorization: Bearer {token}
  body:
    title?: string
    description?: string
    status?: "pending" | "in_progress" | "completed"
    priority?: "high" | "medium" | "low"
    due_date?: datetime

DELETE /api/v1/tasks/{id}
  description: タスク削除
  headers:
    Authorization: Bearer {token}

POST /api/v1/tasks/{id}/ai-support
  description: AIサポート実行
  headers:
    Authorization: Bearer {token}
  body:
    type: "research" | "solution"
  response:
    support: AISupport
```

#### メール同期関連

```yaml
POST /api/v1/email/sync
  description: メール同期開始
  headers:
    Authorization: Bearer {token}
  body:
    account_id: string
  response:
    job_id: string

GET /api/v1/email/sync/{job_id}
  description: 同期ジョブ状態取得
  headers:
    Authorization: Bearer {token}
  response:
    job: EmailSyncJob

GET /api/v1/email/sync/history
  description: 同期履歴取得
  headers:
    Authorization: Bearer {token}
  query:
    page?: number
    limit?: number
  response:
    jobs: EmailSyncJob[]
    total: number
```

### 3.2 認証・認可フロー

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant DB
    participant Email
    
    Client->>API: POST /auth/register
    API->>Auth: Create user
    Auth->>DB: Save user (unverified)
    Auth->>Email: Send verification email
    API-->>Client: 201 Created
    
    Client->>API: POST /auth/verify?token=xxx
    API->>Auth: Verify token
    Auth->>DB: Update user (verified)
    Auth->>Auth: Generate JWT
    API-->>Client: 200 OK (tokens)
    
    Client->>API: GET /tasks (with token)
    API->>Auth: Validate JWT
    Auth-->>API: User info
    API->>DB: Fetch tasks
    API-->>Client: 200 OK (tasks)
```

## 4. コンポーネント設計

### 4.1 フロントエンドコンポーネント構造

```typescript
// Domain Entities
interface User {
  id: string;
  email: string;
  name?: string;
  emailAccounts: EmailAccount[];
  createdAt: Date;
}

interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  sourceEmailId?: string;
  sourceEmailLink?: string;
  dueDate?: Date;
  createdAt: Date;
  updatedAt: Date;
}

interface EmailAccount {
  id: string;
  provider: 'google' | 'microsoft';
  email: string;
  isActive: boolean;
}

// Value Objects
type TaskStatus = 'pending' | 'in_progress' | 'completed';
type TaskPriority = 'high' | 'medium' | 'low';

// Store Interface (Zustand)
interface AuthStore {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

interface TaskStore {
  tasks: Task[];
  isLoading: boolean;
  filter: TaskFilter;
  fetchTasks: () => Promise<void>;
  createTask: (task: CreateTaskDto) => Promise<void>;
  updateTask: (id: string, updates: UpdateTaskDto) => Promise<void>;
  deleteTask: (id: string) => Promise<void>;
  setFilter: (filter: TaskFilter) => void;
}

// Component Props
interface TaskCardProps {
  task: Task;
  onStatusChange: (status: TaskStatus) => void;
  onEdit: () => void;
  onDelete: () => void;
}

interface TaskListProps {
  tasks: Task[];
  view: 'card' | 'list';
  onTaskSelect: (task: Task) => void;
}

interface EmailSyncButtonProps {
  accountId: string;
  onSyncComplete: () => void;
}
```

### 4.2 バックエンドサービス設計

```python
# Domain Layer
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class Task:
    def __init__(
        self,
        id: UUID,
        user_id: UUID,
        title: str,
        description: Optional[str] = None,
        status: str = 'pending',
        priority: str = 'medium'
    ):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_status(self, new_status: str) -> None:
        if new_status not in ['pending', 'in_progress', 'completed']:
            raise ValueError(f"Invalid status: {new_status}")
        self.status = new_status
        self.updated_at = datetime.utcnow()

# Repository Interface
class TaskRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: UUID) -> Optional[Task]:
        pass

    @abstractmethod
    async def find_by_user(
        self, 
        user_id: UUID, 
        filters: dict
    ) -> List[Task]:
        pass

    @abstractmethod
    async def save(self, task: Task) -> Task:
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        pass

# Application Service
class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        email_service: EmailService,
        ai_service: AIService
    ):
        self.task_repository = task_repository
        self.email_service = email_service
        self.ai_service = ai_service

    async def create_task_from_email(
        self,
        user_id: UUID,
        email_data: dict
    ) -> Task:
        # AI判定
        ai_result = await self.ai_service.analyze_email(email_data)
        
        if not ai_result.is_task:
            return None
        
        # タスク作成
        task = Task(
            id=UUID(),
            user_id=user_id,
            title=ai_result.task_title,
            description=ai_result.task_description,
            priority=ai_result.priority
        )
        
        # 保存
        return await self.task_repository.save(task)

# Infrastructure Layer
class PostgresTaskRepository(TaskRepository):
    def __init__(self, db_session):
        self.db = db_session

    async def find_by_id(self, id: UUID) -> Optional[Task]:
        # SQLModel implementation
        pass

    async def find_by_user(
        self, 
        user_id: UUID, 
        filters: dict
    ) -> List[Task]:
        # SQLModel implementation with filters
        pass
```

## 5. セキュリティ設計

### 5.1 認証・認可

```mermaid
graph TB
    subgraph "認証フロー"
        Login[ログイン] --> JWT[JWT生成]
        JWT --> Access[Access Token<br/>1時間]
        JWT --> Refresh[Refresh Token<br/>30日]
        Refresh --> Renew[トークン更新]
    end
    
    subgraph "認可フロー"
        Request[APIリクエスト] --> Validate[JWT検証]
        Validate --> UserID[ユーザーID抽出]
        UserID --> Permission[権限確認]
        Permission --> Allow[許可/拒否]
    end
    
    subgraph "セキュリティ層"
        HTTPS[HTTPS強制]
        CORS[CORS設定]
        RateLimit[レート制限]
        CSP[Content Security Policy]
    end
```

### 5.2 データ保護

```python
# 暗号化設定
from cryptography.fernet import Fernet
import os

class EncryptionService:
    def __init__(self):
        self.key = os.environ.get('ENCRYPTION_KEY').encode()
        self.cipher = Fernet(self.key)
    
    def encrypt_tokens(self, tokens: dict) -> str:
        """OAuth トークンを暗号化"""
        json_tokens = json.dumps(tokens)
        encrypted = self.cipher.encrypt(json_tokens.encode())
        return encrypted.decode()
    
    def decrypt_tokens(self, encrypted: str) -> dict:
        """暗号化されたトークンを復号"""
        decrypted = self.cipher.decrypt(encrypted.encode())
        return json.loads(decrypted.decode())

# パスワードハッシュ化
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)
```

## 6. 非同期処理設計

### 6.1 Celery タスクフロー

```mermaid
graph LR
    API[FastAPI] --> Queue[Redis Queue]
    Queue --> Worker1[Celery Worker 1]
    Queue --> Worker2[Celery Worker 2]
    
    Worker1 --> MailSync[メール同期]
    Worker1 --> AIThread[AI スレッド分析]
    
    MailSync --> Gmail[Gmail API]
    MailSync --> Graph[Microsoft Graph API]
    AIThread --> OpenAI[OpenAI API]
    AIThread --> Bedrock[AWS Bedrock]
    
    Worker1 --> Result[Redis Result]
    Worker2 --> Result
    
    Result --> API
```

### 6.2 タスク定義

```python
from celery import Celery
from typing import List, Dict

celery_app = Celery('pmo_agent')

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def sync_emails(self, account_id: str, user_id: str) -> Dict:
    """メール同期タスク"""
    # 進捗更新
    self.update_state(
        state='PROGRESS',
        meta={'current': 0, 'total': 100}
    )
    
    # メールサービス
    email_service = EmailService()
    
    # Gmail: 最大50件のメッセージIDを取得後、個別に詳細取得
    # Outlook: デルタクエリでバッチ取得
    emails = email_service.sync_emails_async(account_id, user_id)
    
    # 各メールを個別にデータベースに保存
    for email in emails:
        email_service.save_email_to_db(email, user_id)
    
    # スレッドごとにグループ化してAI分析
    thread_groups = email_service.group_by_thread(emails)
    
    for thread_id, thread_emails in thread_groups.items():
        # スレッド単位でAI分析タスクをキューに追加
        analyze_email_thread_for_tasks.delay(thread_emails, user_id)
    
    return {'total': len(emails), 'threads': len(thread_groups), 'status': 'completed'}

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 60})
def analyze_email_thread_for_tasks(self, thread_emails: List[Dict], user_id: str) -> None:
    """スレッド単位でメールをAI分析してタスク生成"""
    ai_service = AIService()
    task_service = TaskService()
    email_service = EmailService()
    
    # スレッド全体をまとめてAI分析
    thread_analysis = ai_service.analyze_email_thread(
        emails=thread_emails,
        context={'user_id': user_id}
    )
    
    # AI判定結果に基づいてタスク作成
    if thread_analysis.get('should_create_task', False):
        task_service.create_from_email_thread(
            user_id=user_id,
            thread_emails=thread_emails,
            ai_analysis=thread_analysis
        )
        
    # 処理済みマークを各メールに設定
    for email in thread_emails:
        email_service.mark_as_processed(email['id'])
```

## 7. パフォーマンス最適化

### 7.1 キャッシュ戦略

```python
from functools import lru_cache
import redis
import json

class CacheService:
    def __init__(self):
        self.redis = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
    
    def cache_key(self, prefix: str, **kwargs) -> str:
        """キャッシュキー生成"""
        parts = [prefix]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}:{v}")
        return ":".join(parts)
    
    async def get_user_tasks(
        self, 
        user_id: str, 
        filters: dict
    ) -> List[Task]:
        # キャッシュ確認
        cache_key = self.cache_key(
            "tasks", 
            user_id=user_id, 
            **filters
        )
        cached = self.redis.get(cache_key)
        
        if cached:
            return json.loads(cached)
        
        # DB取得
        tasks = await self.task_repository.find_by_user(
            user_id, 
            filters
        )
        
        # キャッシュ保存（5分）
        self.redis.setex(
            cache_key,
            300,
            json.dumps([t.dict() for t in tasks])
        )
        
        return tasks
```

### 7.2 データベース最適化

```sql
-- パーティショニング（将来対応）
CREATE TABLE tasks_2024_01 PARTITION OF tasks
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- マテリアライズドビュー
CREATE MATERIALIZED VIEW user_task_summary AS
SELECT 
    user_id,
    status,
    COUNT(*) as task_count,
    MAX(updated_at) as last_updated
FROM tasks
GROUP BY user_id, status;

-- 定期リフレッシュ
REFRESH MATERIALIZED VIEW CONCURRENTLY user_task_summary;
```

## 8. エラーハンドリング

### 8.1 エラー分類と対処

```python
from enum import Enum
from typing import Optional

class ErrorCode(Enum):
    # 認証エラー
    INVALID_CREDENTIALS = "AUTH001"
    TOKEN_EXPIRED = "AUTH002"
    UNAUTHORIZED = "AUTH003"
    
    # ビジネスエラー
    TASK_NOT_FOUND = "TASK001"
    INVALID_STATUS = "TASK002"
    
    # 外部サービスエラー
    EMAIL_SYNC_FAILED = "EXT001"
    AI_SERVICE_ERROR = "EXT002"
    
    # システムエラー
    DATABASE_ERROR = "SYS001"
    INTERNAL_ERROR = "SYS002"

class AppException(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[dict] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

# エラーハンドラー
from fastapi import Request
from fastapi.responses import JSONResponse

async def app_exception_handler(
    request: Request, 
    exc: AppException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.code.value,
        content={
            "error": {
                "code": exc.code.name,
                "message": exc.message,
                "details": exc.details
            }
        }
    )
```

## 9. デプロイメント設計

### 9.1 環境構成

```yaml
# docker-compose.yml (開発環境)
version: '3.8'

services:
  backend:
    build: ./packages/backend
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/pmo_agent
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"
  
  frontend:
    build: ./packages/frontend
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    ports:
      - "3000:3000"
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=pmo_agent
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  celery:
    build: ./packages/backend
    command: celery -A app.worker worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/pmo_agent
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

### 9.2 CI/CD パイプライン

```yaml
# .github/workflows/deploy.yml
name: Deploy PMO Agent

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install backend dependencies
        run: |
          cd packages/backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run backend tests
        run: |
          cd packages/backend
          pytest
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install frontend dependencies
        run: |
          cd packages/frontend
          npm ci
      
      - name: Run frontend tests
        run: |
          cd packages/frontend
          npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Vercel
        run: |
          cd packages/frontend
          npx vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
      
      - name: Deploy to Render
        run: |
          curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
```

## 10. モニタリング設計

### 10.1 ヘルスチェック

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    """基本ヘルスチェック"""
    return {"status": "healthy"}

@health_router.get("/health/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db)
):
    """詳細ヘルスチェック"""
    checks = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "celery": "unknown"
    }
    
    # Database check
    try:
        await db.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"
    
    # Redis check
    try:
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        checks["redis"] = "healthy"
    except Exception:
        checks["redis"] = "unhealthy"
    
    # Overall status
    overall = "healthy" if all(
        v == "healthy" for v in checks.values()
    ) else "degraded"
    
    return {
        "status": overall,
        "checks": checks,
        "timestamp": datetime.utcnow()
    }
```

### 10.2 ログ設計

```python
import logging
from pythonjsonlogger import jsonlogger

# ログ設定
def setup_logging():
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    logHandler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
    
    return logger

# 構造化ログ
logger = setup_logging()

class LoggerMiddleware:
    async def __call__(self, request, call_next):
        start_time = time.time()
        
        # リクエストログ
        logger.info(
            "request_started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host
            }
        )
        
        response = await call_next(request)
        
        # レスポンスログ
        duration = time.time() - start_time
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration": duration
            }
        )
        
        return response
```

## 11. 将来の拡張性考慮

### 11.1 マイクロサービス化準備

```mermaid
graph TB
    subgraph "現在のモノリシック構成"
        CurrentAPI[FastAPI<br/>すべての機能]
    end
    
    subgraph "将来のマイクロサービス構成"
        Gateway[API Gateway]
        AuthSvc[認証サービス]
        TaskSvc[タスクサービス]
        MailSvc[メールサービス]
        AISvc[AIサービス]
        
        Gateway --> AuthSvc
        Gateway --> TaskSvc
        Gateway --> MailSvc
        Gateway --> AISvc
    end
    
    CurrentAPI -.移行.-> Gateway
```

### 11.2 スケーラビリティ対応

- **水平スケーリング**: ステートレス設計により複数インスタンス対応
- **データベース**: Read レプリカ、シャーディング対応準備
- **キャッシュ**: Redis クラスター対応
- **メッセージキュー**: RabbitMQ/Kafka への移行パス

この設計により、初期は無料プランで運用しながら、ユーザー増加に応じて段階的にスケールアップすることが可能です。