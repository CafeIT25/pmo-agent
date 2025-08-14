# バックエンド Railway デプロイ手順

## 1. Railway アカウントの準備

### 1.1 Railway アカウント作成

1. [Railway](https://railway.app/) にアクセス
2. 「Login」をクリック
3. GitHub アカウントで連携：
   ```
   Login with GitHub
   ```
4. 必要な権限を許可

### 1.2 Railway CLI のインストール

```bash
# Homebrew (Mac/Linux)
brew install railway/railway/railway

# npm (Windows/Mac/Linux)
npm install -g @railway/cli

# 直接インストール
curl -fsSL https://railway.app/install.sh | sh

# ログイン
railway login
# → ブラウザでRailwayアカウントと連携

# 確認
railway --version
```

### 1.3 無料枠の確認

Railway の無料枠：
- **$5 クレジット/月**
- **500時間実行時間/月**
- **1GB RAM**
- **1GB ディスク**
- **公開ドメイン提供**

## 2. プロジェクトの準備

### 2.1 バックエンドディレクトリの確認

```bash
cd pmo-agent/packages/backend

# 必要ファイルの確認
ls -la
```

期待されるファイル：
```
├── app/                 # FastAPI アプリケーション
├── alembic/            # データベースマイグレーション
├── requirements.txt    # Python 依存関係
├── .env.example       # 環境変数テンプレート
└── main.py または app/main.py
```

### 2.2 Railway 用設定ファイルの作成

**📁 ファイルの場所**: `pmo-agent/packages/backend/railway.toml`

```toml
[build]
builder = "NIXPACKS"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[env]
RAILWAY_STATIC_URL = true
```

### 2.3 Procfile の作成

**📁 ファイルの場所**: `pmo-agent/packages/backend/Procfile`

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 2.4 実行用スクリプトの作成

**📁 ファイルの場所**: `pmo-agent/packages/backend/start.sh`

```bash
#!/bin/bash

# データベースマイグレーション実行
alembic upgrade head

# FastAPI アプリケーション起動
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

実行権限を付与：
```bash
chmod +x start.sh
```

### 2.5 requirements.txt の最適化

**📁 ファイルの場所**: `pmo-agent/packages/backend/requirements.txt`

本番環境用の依存関係を追加：

```txt
# 既存の依存関係
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.23
alembic>=1.13.0
openai>=1.6.1
httpx>=0.25.2
python-dotenv>=1.0.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# 本番環境用追加パッケージ
psycopg2-binary>=2.9.7    # PostgreSQL ドライバ
gunicorn>=21.2.0          # WSGI サーバー（バックアップ）
sentry-sdk[fastapi]>=1.38.0  # エラー監視
```

## 3. Railway プロジェクトの作成

### 3.1 新しいプロジェクトを作成

```bash
cd pmo-agent/packages/backend

# Railway プロジェクトの初期化
railway login
railway init

# プロジェクト設定
? Enter project name: pmo-agent-backend
? Environment: production
```

### 3.2 GitHub リポジトリとの連携

1. コードをGitHubにプッシュ：

```bash
# プロジェクトルートで
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

2. Railway ダッシュボードで：
   - Projects → pmo-agent-backend
   - Settings → Service → Connect Repository
   - GitHub リポジトリを選択
   - Root Directory: `packages/backend`

### 3.3 ビルド設定

Railway ダッシュボードで：

1. **Build Command**:
   ```
   pip install -r requirements.txt
   ```

2. **Start Command**:
   ```
   ./start.sh
   ```

3. **Root Directory**:
   ```
   packages/backend
   ```

## 4. データベースの設定

### 4.1 PostgreSQL サービスの追加

Railway ダッシュボードで：

1. 「+ New」→「Database」→ «PostgreSQL»
2. サービス名: `pmo-agent-db`
3. 自動的にデータベースが作成される

### 4.2 データベース接続情報の取得

1. PostgreSQL サービスを選択
2. 「Variables」タブで以下を確認：
   ```
   PGHOST=xxxxx.railway.app
   PGPORT=5432
   PGDATABASE=railway
   PGUSER=postgres
   PGPASSWORD=xxxxxxxxxxxxx
   ```

3. 接続URLの生成：
   ```
   postgresql://postgres:password@host:5432/railway
   ```

## 5. 環境変数の設定

### 5.1 Railway での環境変数設定

Railway ダッシュボード → Service → Variables で以下を設定：

#### 基本設定
```env
# アプリケーション設定
PROJECT_NAME=PMO Agent
VERSION=1.0.0
API_PREFIX=/api/v1
DEBUG=false
ENVIRONMENT=production

# セキュリティ
SECRET_KEY=your-production-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

#### データベース設定
```env
# Railway PostgreSQL（自動設定）
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

#### OpenAI 設定
```env
USE_OPENAI=true
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.3
```

#### Microsoft/Outlook 設定
```env
OUTLOOK_ENABLED=true
MICROSOFT_CLIENT_ID=12345678-1234-1234-1234-123456789abc
MICROSOFT_CLIENT_SECRET=~8Q8~.xxxxxxxxxxxxxxxxxxxxx
MICROSOFT_TENANT_ID=common
MICROSOFT_REDIRECT_URI=https://${{RAILWAY_STATIC_URL}}/api/v1/auth/callback/microsoft
MICROSOFT_SCOPES=User.Read Mail.Read Mail.ReadWrite offline_access
```

#### CORS 設定
```env
CORS_ORIGINS=["https://pmo-agent-frontend.vercel.app","http://localhost:5173"]
```

### 5.2 SECRET_KEY の生成

```bash
# 本番用の安全なキーを生成
python -c "import secrets; print(secrets.token_hex(32))"

# 出力例: a1b2c3d4e5f6789...（64文字のランダム文字列）
```

この値を Railway の `SECRET_KEY` 環境変数に設定

## 6. デプロイの実行

### 6.1 Railway CLI でのデプロイ

```bash
cd pmo-agent/packages/backend

# 現在のプロジェクトを確認
railway status

# デプロイの実行
railway up

# デプロイログの確認
railway logs
```

### 6.2 GitHub 連携での自動デプロイ

1. GitHub への push で自動的にデプロイ開始
2. Railway ダッシュボードでビルドログを確認
3. デプロイ完了後、ドメインが自動生成される

期待されるURL：
```
https://pmo-agent-backend-production-xxxx.up.railway.app
```

## 7. データベースマイグレーションの実行

### 7.1 Railway Shell でのマイグレーション

```bash
# Railway のシェルに接続
railway shell

# マイグレーション実行
alembic upgrade head

# テーブル確認
python -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT tablename FROM pg_tables WHERE schemaname = \\'public\\';'))
    print(list(result))
"
```

### 7.2 初期データの投入

```bash
# テストユーザーの作成
cat > create_admin_user.py << 'EOF'
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.core.security import get_password_hash

async def create_admin_user():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(DATABASE_URL)
    SessionLocal = sessionmaker(engine, class_=AsyncSession)
    
    async with SessionLocal() as session:
        admin_user = User(
            email="admin@pmo-agent.com",
            hashed_password=get_password_hash("AdminPass123!"),
            full_name="Admin User",
            is_active=True,
            is_superuser=True
        )
        session.add(admin_user)
        await session.commit()
        print("✅ 管理者ユーザー作成完了")
        print("Email: admin@pmo-agent.com")
        print("Password: AdminPass123!")

if __name__ == "__main__":
    asyncio.run(create_admin_user())
EOF

python create_admin_user.py
```

## 8. API の動作確認

### 8.1 ヘルスチェック

```bash
# Railway アプリのURLを確認
railway status

# ヘルスチェック
curl https://your-app.up.railway.app/health
```

期待されるレスポンス：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:00:00",
  "version": "1.0.0",
  "environment": "production"
}
```

### 8.2 API ドキュメントの確認

ブラウザで以下にアクセス：
```
https://your-app.up.railway.app/docs
```

確認項目：
- [ ] Swagger UI が表示される
- [ ] 全エンドポイントが一覧表示される
- [ ] 認証エンドポイントが動作する

### 8.3 データベース接続の確認

```bash
curl -X POST https://your-app.up.railway.app/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }'
```

## 9. Azure AD リダイレクト URI の更新

### 9.1 Railway URL の確認

```bash
# デプロイされたURLを取得
railway status

# 出力例
# URL: https://pmo-agent-backend-production-xxxx.up.railway.app
```

### 9.2 Azure Portal での設定更新

1. [Azure Portal](https://portal.azure.com/) にアクセス
2. Azure Active Directory → アプリの登録 → PMO Agent
3. 「認証」→「Web」のリダイレクト URI に追加：
   ```
   https://pmo-agent-backend-production-xxxx.up.railway.app/api/v1/auth/callback/microsoft
   ```

### 9.3 フロントエンド環境変数の更新

Vercel ダッシュボードで環境変数を更新：

```env
VITE_API_URL=https://pmo-agent-backend-production-xxxx.up.railway.app
VITE_WEBSOCKET_URL=wss://pmo-agent-backend-production-xxxx.up.railway.app
```

更新後、Vercel で再デプロイ：
```bash
vercel --prod
```

## 10. 監視とログ

### 10.1 Railway ログの監視

```bash
# リアルタイムログ
railway logs --follow

# 過去のログ
railway logs --tail 100
```

### 10.2 エラー監視（Sentry）

```bash
# Sentry SDK の設定
pip install sentry-sdk[fastapi]
```

```python
# app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.ENVIRONMENT == "production":
    sentry_sdk.init(
        dsn="YOUR_SENTRY_DSN",
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment="production"
    )
```

### 10.3 ヘルスチェック監視

```python
# app/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # データベース接続チェック
        await db.execute("SELECT 1")
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

## 11. パフォーマンス最適化

### 11.1 接続プールの設定

```python
# app/core/database.py
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 11.2 キャッシュの設定

```bash
# Redis を Railway に追加
railway add redis
```

```python
# app/core/cache.py
import redis.asyncio as redis

redis_client = redis.from_url(
    os.getenv("REDIS_URL"),
    encoding="utf-8",
    decode_responses=True
)
```

## 12. セキュリティ設定

### 12.1 HTTPS の強制

```python
# app/main.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

### 12.2 レート制限

```bash
pip install slowapi
```

```python
# app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# エンドポイントでの使用
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    # ログイン処理
```

## 13. トラブルシューティング

### 13.1 デプロイエラー

```bash
# ビルドログの確認
railway logs --deployment

# 環境変数の確認
railway variables

# シェルでのデバッグ
railway shell
```

### 13.2 データベース接続エラー

```bash
# データベースURLの確認
railway variables | grep DATABASE_URL

# 接続テスト
railway shell
python -c "
import os
import asyncpg
import asyncio

async def test_db():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    result = await conn.fetchval('SELECT version()')
    print(f'PostgreSQL version: {result}')
    await conn.close()

asyncio.run(test_db())
"
```

### 13.3 メモリ不足エラー

```python
# app/core/config.py
# メモリ使用量の最適化
import gc
import os

# ガベージコレクション設定
gc.set_threshold(700, 10, 10)

# Uvicorn ワーカー数の制限
workers = min(2, int(os.getenv("WEB_CONCURRENCY", 1)))
```

## 14. コスト管理

### 14.1 Railway 使用量の監視

Railway ダッシュボードで確認：
- **CPU 使用時間**: 500時間/月まで無料
- **メモリ使用量**: 1GB まで
- **ネットワーク**: 無制限

### 14.2 最適化のポイント

1. **スリープ設定**:
   ```python
   # 非アクティブ時のスリープ
   if settings.ENVIRONMENT == "production":
       uvicorn.run(app, host="0.0.0.0", port=port, 
                  timeout_keep_alive=30,
                  timeout_graceful_shutdown=30)
   ```

2. **リソース使用量の削減**:
   ```bash
   # 不要なパッケージの削除
   pip uninstall pytest pytest-asyncio httpx-mock
   pip freeze > requirements.txt
   ```

## 15. 次のステップ

バックエンドのデプロイが完了したら：

1. **[データベース設定](./08-database-setup-supabase.md)** - Supabase での追加設定（オプション）
2. **[統合テスト](./09-production-testing.md)** - フロントエンド・バックエンド連携確認
3. **[Outlook連携テスト](./10-outlook-integration-test.md)** - Microsoft 連携の動作確認

---

**所要時間**: 約45分
**前提条件**: GitHub アカウント、OpenAI API キー、Azure AD 設定完了
**次の手順**: [統合テスト](./09-production-testing.md)