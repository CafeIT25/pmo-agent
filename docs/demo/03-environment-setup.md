# 環境構築手順

## 前提条件の確認

### 必要なソフトウェア

| ソフトウェア | 最小バージョン | 確認コマンド | インストール方法 |
|------------|--------------|------------|---------------|
| Node.js | 18.0.0 | `node --version` | [nodejs.org](https://nodejs.org/) |
| Python | 3.11.0 | `python --version` | [python.org](https://www.python.org/) |
| Git | 2.0.0 | `git --version` | [git-scm.com](https://git-scm.com/) |
| pnpm | 8.0.0 | `pnpm --version` | `npm install -g pnpm` |

### 動作確認

```bash
# すべてのバージョンを確認
node --version && python --version && git --version && pnpm --version
```

期待される出力例：
```
v18.17.0
Python 3.11.4
git version 2.41.0
8.6.12
```

## 1. プロジェクトのセットアップ

### 1.1 リポジトリのクローン

```bash
# 作業ディレクトリに移動
cd ~/projects  # または任意のディレクトリ

# リポジトリをクローン
git clone <repository-url> pmo-agent
cd pmo-agent

# ディレクトリ構造の確認
ls -la
```

期待されるディレクトリ構造：
```
pmo-agent/
├── packages/
│   ├── frontend/     # Next.js/React フロントエンド
│   └── backend/      # FastAPI バックエンド
├── docs/            # ドキュメント
├── pnpm-workspace.yaml
├── package.json
└── README.md
```

### 1.2 依存関係のインストール

```bash
# プロジェクトルートで実行
pnpm install

# インストール確認
pnpm list --depth=0
```

## 2. バックエンドの設定

### 2.1 Python仮想環境の作成

```bash
cd packages/backend

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Mac/Linux
source venv/bin/activate

# 確認（プロンプトに (venv) が表示される）
which python
```

### 2.2 Python依存関係のインストール

```bash
# pip のアップグレード
pip install --upgrade pip

# 依存関係のインストール
pip install -r requirements.txt

# インストール確認
pip list | grep -E "fastapi|openai|httpx"
```

期待される主要パッケージ：
```
fastapi          0.104.1
openai           1.6.1
httpx            0.25.2
sqlalchemy       2.0.23
alembic          1.13.0
```

### 2.3 環境変数の設定

**📁 ファイルの場所**: `pmo-agent/packages/backend/.env`

```bash
# .env.example をコピー
cp .env.example .env

# エディタで開く
nano .env  # または code .env, vim .env など
```

**📝 編集するファイル**: `pmo-agent/packages/backend/.env`

**必須設定項目**（各セクションで取得した値を設定）：

```env
# ========== 基本設定 ==========
PROJECT_NAME="PMO Agent"
VERSION="1.0.0"
API_PREFIX="/api/v1"
DEBUG=true
ENVIRONMENT=development

# ========== セキュリティ ==========
SECRET_KEY=your-secret-key-here-$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ========== データベース（SQLite） ==========
DATABASE_URL=sqlite:///./pmo_agent.db

# ========== OpenAI（必須） ==========
USE_OPENAI=true
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # ← 01-openai-api-setup.md の手順2.3で取得したAPIキー
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.3

# ========== Microsoft/Outlook（オプション） ==========
OUTLOOK_ENABLED=true
MICROSOFT_CLIENT_ID=12345678-1234-1234-1234-123456789abc  # ← 02-azure-ad-setup.md の手順3.1で取得
MICROSOFT_CLIENT_SECRET=~8Q8~.xxxxxxxxxxxxxxxxxxxxx       # ← 02-azure-ad-setup.md の手順4.3で取得
MICROSOFT_TENANT_ID=common                                # ← 02-azure-ad-setup.md の手順3.2で取得（マルチテナントは"common"）
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback/microsoft
MICROSOFT_SCOPES=User.Read Mail.Read Mail.ReadWrite offline_access

# ========== その他 ==========
USE_MOCK_AI=false
USE_BEDROCK=false
USE_MEMORY_CACHE=true
USE_CELERY=false
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### 2.4 SECRET_KEY の生成

```bash
# Linux/Mac
echo "SECRET_KEY=$(openssl rand -hex 32)"

# Windows (PowerShell)
-join ((1..32) | ForEach {'{0:X}' -f (Get-Random -Max 256)})

# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

生成された値を `.env` の `SECRET_KEY` に設定。

### 2.5 データベースの初期化

```bash
# マイグレーションファイルの確認
ls alembic/versions/

# データベースのマイグレーション実行
alembic upgrade head

# テーブルの確認
python -c "
import sqlite3
conn = sqlite3.connect('pmo_agent.db')
cursor = conn.cursor()
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table';\")
print(cursor.fetchall())
"
```

期待されるテーブル：
```
[('alembic_version',), ('users',), ('tasks',), ('processed_emails',), ...]
```

### 2.6 初期データの投入（オプション）

```bash
# テストユーザーの作成スクリプト
cat > create_test_user.py << 'EOF'
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_engine, AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def create_test_user():
    async with AsyncSessionLocal() as session:
        # テストユーザー作成
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        session.add(user)
        await session.commit()
        print("✅ テストユーザー作成完了")
        print("Email: test@example.com")
        print("Password: password123")

if __name__ == "__main__":
    asyncio.run(create_test_user())
EOF

python create_test_user.py
```

## 3. フロントエンドの設定

### 3.1 ディレクトリ移動

```bash
# プロジェクトルートから
cd packages/frontend
```

### 3.2 環境変数の設定

**📁 ファイルの場所**: `pmo-agent/packages/frontend/.env.local`

```bash
# .env.example をコピー（.env.example がない場合は新規作成）
cp .env.example .env.local 2>/dev/null || touch .env.local

# エディタで開く
nano .env.local
```

**📝 編集するファイル**: `pmo-agent/packages/frontend/.env.local`

設定内容：

```env
# API接続設定
VITE_API_URL=http://localhost:8000
VITE_WEBSOCKET_URL=ws://localhost:8000

# 機能フラグ
VITE_MOCK_MODE=false
VITE_ENABLE_AI_FEATURES=true
VITE_ENABLE_EMAIL_SYNC=true
```

### 3.3 依存関係の確認

```bash
# package.json の確認
cat package.json | grep -A 5 "dependencies"

# node_modules の確認
ls -la node_modules | head -10
```

## 4. アプリケーションの起動

### 4.1 バックエンドの起動

```bash
# backend ディレクトリで実行
cd packages/backend

# 仮想環境が有効化されていることを確認
which python  # (venv) が表示される

# 開発サーバーの起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

期待される出力：
```
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 4.2 API の動作確認

新しいターミナルで：

```bash
# ヘルスチェック
curl http://localhost:8000/health

# API ドキュメント（ブラウザで開く）
open http://localhost:8000/docs  # Mac
start http://localhost:8000/docs  # Windows
xdg-open http://localhost:8000/docs  # Linux
```

### 4.3 フロントエンドの起動

新しいターミナルで：

```bash
cd packages/frontend

# 開発サーバーの起動
pnpm dev
```

期待される出力：
```
  VITE v4.5.0  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.1.100:5173/
  ➜  press h to show help
```

### 4.4 アプリケーションへのアクセス

ブラウザで `http://localhost:5173` を開く

## 5. 起動確認チェックリスト

### バックエンド

- [ ] `http://localhost:8000/health` が `{"status":"healthy"}` を返す
- [ ] `http://localhost:8000/docs` で Swagger UI が表示される
- [ ] ログにエラーが表示されていない

### フロントエンド

- [ ] `http://localhost:5173` でログイン画面が表示される
- [ ] コンソールにエラーが表示されていない
- [ ] 「新規登録」ボタンがクリックできる

### 統合確認

- [ ] フロントエンドからバックエンドAPIに接続できる
- [ ] CORS エラーが発生していない

## 6. よくある問題と解決方法

### ポート競合エラー

**エラー**: `[Errno 48] Address already in use`

**解決策**:
```bash
# 使用中のポートを確認
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# プロセスを終了
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows
```

### モジュールインポートエラー

**エラー**: `ModuleNotFoundError: No module named 'xxx'`

**解決策**:
```bash
# 仮想環境の確認
which python

# 再インストール
pip install -r requirements.txt --force-reinstall
```

### データベース接続エラー

**エラー**: `sqlalchemy.exc.OperationalError`

**解決策**:
```bash
# データベースファイルの確認
ls -la *.db

# 権限の修正
chmod 664 pmo_agent.db

# 再作成
rm pmo_agent.db
alembic upgrade head
```

### CORS エラー

**エラー**: `Access to fetch at 'http://localhost:8000' from origin 'http://localhost:5173' has been blocked by CORS policy`

**解決策**:

`.env` で CORS_ORIGINS を確認：
```env
CORS_ORIGINS=["http://localhost:5173"]
```

## 7. 開発ツール（オプション）

### 7.1 VSCode 拡張機能

推奨拡張機能：
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense

### 7.2 データベース管理ツール

SQLite ブラウザ：
```bash
# インストール
# Mac
brew install --cask db-browser-for-sqlite

# Windows (Chocolatey)
choco install sqlitebrowser

# Linux
sudo apt-get install sqlitebrowser
```

### 7.3 API テストツール

Postman または Thunder Client（VSCode拡張）のインストール

## 8. 次のステップ

環境構築が完了したら、以下のドキュメントに進んでください：

1. [動作確認手順](./04-testing-guide.md) - 機能テストの実施
2. [トラブルシューティング](./05-troubleshooting.md) - 問題が発生した場合
3. [デプロイガイド](./06-deployment-guide.md) - 本番環境への展開

## 9. スクリプト化（全自動セットアップ）

```bash
#!/bin/bash
# setup.sh - 自動セットアップスクリプト

echo "🚀 PMO Agent セットアップを開始します..."

# 依存関係のインストール
echo "📦 依存関係をインストール中..."
pnpm install

# バックエンドセットアップ
echo "🔧 バックエンドを設定中..."
cd packages/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
echo "⚠️  .env ファイルを編集してAPIキーを設定してください"

# データベース初期化
echo "💾 データベースを初期化中..."
alembic upgrade head

# フロントエンドセットアップ
echo "🎨 フロントエンドを設定中..."
cd ../frontend
cp .env.example .env.local

echo "✅ セットアップ完了！"
echo "📝 .env ファイルを編集してから、以下のコマンドで起動してください："
echo "  Backend: cd packages/backend && uvicorn app.main:app --reload"
echo "  Frontend: cd packages/frontend && pnpm dev"
```

使用方法：
```bash
chmod +x setup.sh
./setup.sh
```