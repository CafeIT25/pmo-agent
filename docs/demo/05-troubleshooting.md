# トラブルシューティングガイド

## 1. 環境構築時の問題

### 1.1 Python バージョンエラー

**症状**:
```
ERROR: This script requires Python 3.11 or higher!
```

**原因**: Python バージョンが古い

**解決方法**:

Windows:
```powershell
# Python 3.11 のインストール
winget install Python.Python.3.11

# または公式サイトからダウンロード
# https://www.python.org/downloads/
```

Mac:
```bash
# Homebrew を使用
brew install python@3.11

# pyenv を使用
pyenv install 3.11.7
pyenv local 3.11.7
```

Linux:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv

# CentOS/RHEL
sudo yum install python311
```

### 1.2 pnpm インストールエラー

**症状**:
```
'pnpm' is not recognized as an internal or external command
```

**解決方法**:

```bash
# npm を使用してインストール
npm install -g pnpm

# 権限エラーの場合
sudo npm install -g pnpm  # Mac/Linux
npm install -g pnpm --force  # Windows

# 別の方法（直接インストール）
curl -fsSL https://get.pnpm.io/install.sh | sh -
```

### 1.3 仮想環境の有効化失敗

**症状**:
```
venv\Scripts\activate : File cannot be loaded because running scripts is disabled
```

**原因**: PowerShell の実行ポリシー制限（Windows）

**解決方法**:

```powershell
# 管理者権限で PowerShell を開く
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 確認
Get-ExecutionPolicy

# 仮想環境の再有効化
.\venv\Scripts\Activate.ps1
```

## 2. データベース関連

### 2.1 SQLite ロックエラー

**症状**:
```
sqlite3.OperationalError: database is locked
```

**原因**: 複数のプロセスが同時にデータベースにアクセス

**解決方法**:

```python
# app/core/database.py を編集
connect_args = {
    "check_same_thread": False,
    "timeout": 30  # タイムアウトを延長
}
```

または：

```bash
# データベースファイルの再作成
rm pmo_agent.db
alembic upgrade head
```

### 2.2 マイグレーションエラー

**症状**:
```
alembic.util.exc.CommandError: Can't locate revision identified by 'head'
```

**解決方法**:

```bash
# マイグレーションファイルの確認
ls alembic/versions/

# マイグレーション履歴のリセット
alembic downgrade base
alembic upgrade head

# 完全リセット
rm -rf alembic/versions/*
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 2.3 テーブル作成エラー

**症状**:
```
sqlalchemy.exc.OperationalError: no such table: users
```

**解決方法**:

```bash
# Python シェルで直接作成
python
>>> from app.core.database import engine
>>> from app.models import Base
>>> Base.metadata.create_all(bind=engine)
>>> exit()
```

## 3. OpenAI API エラー

### 3.1 認証エラー

**症状**:
```
openai.AuthenticationError: Invalid API key provided
```

**原因**: APIキーが正しくない

**解決方法**:

1. APIキーの確認：
```bash
# .env ファイルを確認
grep OPENAI_API_KEY .env

# 先頭・末尾の空白を削除
OPENAI_API_KEY=sk-proj-xxxxx  # 空白なし
```

2. 新しいAPIキーの生成：
- [OpenAI Platform](https://platform.openai.com/api-keys) にアクセス
- 新しいキーを生成
- .env を更新

### 3.2 レート制限エラー

**症状**:
```
openai.RateLimitError: Rate limit exceeded
```

**解決方法**:

1. リトライロジックの実装：
```python
# app/services/openai_service.py
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_openai_api(prompt):
    # API呼び出し
```

2. レート制限の調整：
```env
# .env
OPENAI_RATE_LIMIT_PER_MINUTE=20
OPENAI_MAX_RETRIES=3
OPENAI_RETRY_DELAY=5
```

### 3.3 クォータ超過

**症状**:
```
openai.error.InvalidRequestError: You exceeded your current quota
```

**解決方法**:

1. 使用量の確認：
- [Usage ページ](https://platform.openai.com/usage) で確認

2. 支払い方法の追加：
- [Billing ページ](https://platform.openai.com/settings/organization/billing)
- クレジットカードを追加

3. 使用量の最適化：
```env
# トークン数を削減
OPENAI_MAX_TOKENS=500
OPENAI_MODEL=gpt-3.5-turbo  # より安価なモデル
```

## 4. Outlook/Microsoft 連携エラー

### 4.1 リダイレクトURIエラー

**症状**:
```
AADSTS50011: The reply URL specified in the request does not match the reply URLs configured for the application
```

**解決方法**:

1. Azure Portal で確認：
   - アプリの登録 → 認証 → リダイレクトURI
   - 正確に一致することを確認（末尾のスラッシュも）

2. 複数のURIを登録：
```
http://localhost:8000/api/v1/auth/callback/microsoft
http://127.0.0.1:8000/api/v1/auth/callback/microsoft
https://localhost:8000/api/v1/auth/callback/microsoft  # HTTPS版
```

### 4.2 権限不足エラー

**症状**:
```
403 Forbidden: The user or administrator has not consented to use the application
```

**解決方法**:

1. 管理者の同意を取得：
   - Azure Portal → API のアクセス許可
   - 「[組織名] に管理者の同意を与えます」をクリック

2. ユーザーレベルで再認証：
```python
# 既存のトークンをクリア
await db.execute("DELETE FROM oauth_tokens WHERE user_id = ?", [user_id])

# 再認証URLを生成
auth_url = oauth_service.get_microsoft_auth_url(state="new_consent")
```

### 4.3 トークン期限切れ

**症状**:
```
401 Unauthorized: Access token has expired
```

**解決方法**:

```python
# app/services/oauth_service.py
async def refresh_microsoft_token(refresh_token: str):
    """トークンの自動更新"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
        )
        return response.json()
```

## 5. フロントエンドエラー

### 5.1 CORS エラー

**症状**:
```
Access to fetch at 'http://localhost:8000' from origin 'http://localhost:5173' has been blocked by CORS policy
```

**解決方法**:

1. バックエンドの .env を確認：
```env
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

2. FastAPI の CORS 設定：
```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5.2 WebSocket 接続エラー

**症状**:
```
WebSocket connection to 'ws://localhost:8000' failed
```

**解決方法**:

```javascript
// frontend/src/config.ts
const WS_URL = process.env.NODE_ENV === 'production' 
  ? 'wss://your-domain.com'
  : 'ws://localhost:8000';
```

### 5.3 ビルドエラー

**症状**:
```
Module not found: Can't resolve '@/components/...'
```

**解決方法**:

```bash
# node_modules の再インストール
rm -rf node_modules pnpm-lock.yaml
pnpm install

# キャッシュのクリア
pnpm store prune
```

## 6. パフォーマンス問題

### 6.1 API レスポンスが遅い

**原因と対策**:

1. **N+1 クエリ問題**:
```python
# 悪い例
tasks = await get_tasks()
for task in tasks:
    task.emails = await get_emails(task.id)  # N回のクエリ

# 良い例
tasks = await get_tasks_with_emails()  # JOINを使用
```

2. **キャッシュの活用**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_cached_analysis(email_id: str):
    return await analyze_email(email_id)
```

### 6.2 メモリ使用量が多い

**対策**:

1. **ページネーション**:
```python
# 一度に全件取得しない
async def get_tasks(page: int = 1, limit: int = 20):
    offset = (page - 1) * limit
    return await db.query(Task).offset(offset).limit(limit).all()
```

2. **不要なデータの削除**:
```python
# 大きなフィールドを除外
tasks = await db.query(Task).options(
    defer('large_content_field')
).all()
```

## 7. セキュリティ警告

### 7.1 SECRET_KEY 警告

**症状**:
```
WARNING: Using default SECRET_KEY. This is insecure!
```

**解決方法**:

```bash
# 安全なキーの生成
python -c "import secrets; print(secrets.token_hex(32))"

# .env に設定
SECRET_KEY=生成された値
```

### 7.2 HTTPS 警告

**症状**:
```
WARNING: Running in production without HTTPS
```

**解決方法**（開発環境）:

```bash
# mkcert を使用してローカルSSL証明書を作成
mkcert -install
mkcert localhost 127.0.0.1

# Uvicorn でHTTPS起動
uvicorn app.main:app --ssl-keyfile=localhost-key.pem --ssl-certfile=localhost.pem
```

## 8. ログとデバッグ

### 8.1 詳細ログの有効化

```env
# .env
LOG_LEVEL=DEBUG
DEBUG=true
```

```python
# app/core/logging.py
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

### 8.2 リクエスト/レスポンスのログ

```python
# app/middleware/logging.py
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # リクエストログ
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # レスポンスログ
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} ({process_time:.3f}s)")
    
    return response
```

## 9. 緊急時の対処

### 9.1 サービス完全停止

```bash
# すべてのプロセスを停止
pkill -f uvicorn
pkill -f "pnpm dev"

# ポートの解放
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9

# クリーンスタート
cd packages/backend
rm -rf __pycache__ .pytest_cache
python -m venv venv --clear
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 別ターミナル
cd packages/frontend
rm -rf node_modules .next
pnpm install
pnpm dev
```

### 9.2 データベースリセット

```bash
# 完全リセット
rm pmo_agent.db
rm -rf alembic/versions/*
alembic revision --autogenerate -m "Initial"
alembic upgrade head

# テストデータの投入
python scripts/seed_data.py
```

## 10. サポート連絡先

問題が解決しない場合：

1. **ログの収集**:
```bash
# ログファイルをまとめる
tar -czf logs.tar.gz *.log
```

2. **環境情報の記録**:
```bash
# システム情報
uname -a > system_info.txt
python --version >> system_info.txt
node --version >> system_info.txt
pip list >> system_info.txt
```

3. **Issue の作成**:
- GitHub Issues にログと環境情報を添付
- 再現手順を詳細に記載
- エラーメッセージの全文を含める