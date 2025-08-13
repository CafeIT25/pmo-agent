# PMO Agent セットアップガイド

このガイドでは、PMO Agent の開発環境を一から構築する手順を説明します。

## 必要な環境

- Node.js 18.0 以上
- Python 3.9 以上
- Docker Desktop
- Git

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd pmo-agent
```

### 2. 環境変数の設定

バックエンドの環境変数を設定します：

```bash
cd packages/backend
cp .env.example .env
```

`.env` ファイルを編集し、必要な値を設定します。最低限必要な設定：

```env
# データベース接続
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pmo_agent

# Redis
REDIS_URL=redis://localhost:6379

# JWT秘密鍵（ランダムな文字列に変更）
SECRET_KEY=your-secret-key-here

# AWS Bedrock（AI機能を使用する場合）
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1

# OAuth設定（メール連携を使用する場合）
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
```

### 3. Docker サービスの起動

プロジェクトルートに戻って Docker サービスを起動します：

```bash
cd ../..  # プロジェクトルートに戻る
docker-compose up -d postgres redis
```

サービスが正常に起動したか確認：

```bash
docker-compose ps
```

### 4. バックエンドのセットアップ

#### 4.1 Python 仮想環境の作成

```bash
cd packages/backend
python3 -m venv venv
```

#### 4.2 仮想環境の有効化

Linux/Mac:
```bash
source venv/bin/activate
```

Windows:
```bash
venv\Scripts\activate
```

#### 4.3 依存関係のインストール

```bash
pip install -r requirements.txt
```

#### 4.4 データベースマイグレーション

```bash
# 初回のみ：マイグレーション初期化
alembic init alembic

# マイグレーションファイルの生成
alembic revision --autogenerate -m "Initial migration"

# マイグレーションの実行
alembic upgrade head
```

#### 4.5 テストユーザーの作成

```bash
python scripts/create_test_user.py
```

以下のテストユーザーが作成されます：

| Email | Password | 権限 | 備考 |
|-------|----------|------|------|
| test@example.com | testpass123 | 一般ユーザー | Gmail連携モック済み |
| admin@example.com | adminpass123 | 管理者 | 全機能アクセス可能 |
| demo@example.com | demopass123 | 一般ユーザー | Outlook連携モック済み |

### 5. フロントエンドのセットアップ

新しいターミナルを開き：

```bash
cd packages/frontend
npm install
```

### 6. アプリケーションの起動

#### 6.1 バックエンドサーバーの起動

```bash
cd packages/backend
# 仮想環境が有効化されていることを確認
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 6.2 Celery ワーカーの起動（別ターミナル）

```bash
cd packages/backend
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

celery -A app.worker.celery_app worker --loglevel=info --queues=default,email,ai
```

#### 6.3 Celery Beat の起動（定期タスク用、別ターミナル）

```bash
cd packages/backend
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

celery -A app.worker.celery_app beat --loglevel=info
```

#### 6.4 フロントエンドの起動（別ターミナル）

```bash
cd packages/frontend
npm run dev
```

### 7. アプリケーションへのアクセス

- フロントエンド: http://localhost:5173
- バックエンド API: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs

### 8. 動作確認

1. ブラウザで http://localhost:5173 にアクセス
2. テストユーザー（例：test@example.com / testpass123）でログイン
3. ダッシュボードが表示されることを確認

## フロントエンドのみの起動（モックモード）

Docker や バックエンドサービスなしで、フロントエンドのみを起動してUIを確認できます。

### 1. モックモードの有効化

`.env.development` ファイルが既に設定されています：

```env
VITE_API_URL=http://localhost:8000
VITE_MOCK_MODE=true
```

### 2. フロントエンドの起動

```bash
cd packages/frontend
npm install  # 初回のみ
npm run dev
```

### 3. ブラウザでアクセス

http://localhost:5173 にアクセスします。

### 4. モックモードでのログイン情報

以下のテストアカウントでログインできます：

| Email | Password | 備考 |
|-------|----------|------|
| test@example.com | testpass123 | Gmail連携モック済み |
| admin@example.com | adminpass123 | 管理者権限 |
| demo@example.com | demopass123 | Outlook連携モック済み |

### 5. モックモードの機能

- ✅ ログイン/ログアウト
- ✅ ユーザー登録
- ✅ タスクの作成・編集・削除
- ✅ メール同期（シミュレート）
- ✅ AI分析（シミュレート）
- ✅ 全てのUIコンポーネント

## トラブルシューティング

### Docker権限エラー

```
PermissionError: [Errno 13] Permission denied: '/var/run/docker.sock'
```

このエラーが発生した場合：

1. ユーザーを docker グループに追加：
   ```bash
   sudo usermod -aG docker $USER
   ```

2. ログアウトして再ログイン、または：
   ```bash
   newgrp docker
   ```

3. Docker サービスの再起動：
   ```bash
   sudo systemctl restart docker
   ```

4. それでも解決しない場合は、フロントエンドのみのモックモードで起動してください（上記参照）。

### データベース接続エラー

```bash
# PostgreSQL コンテナのログを確認
docker-compose logs postgres

# データベースに直接接続してテスト
docker-compose exec postgres psql -U postgres -d pmo_agent
```

### Redis 接続エラー

```bash
# Redis コンテナのログを確認
docker-compose logs redis

# Redis に接続してテスト
docker-compose exec redis redis-cli ping
```

### ポート競合

既に使用されているポートがある場合は、`docker-compose.yml` で別のポートに変更：

```yaml
services:
  postgres:
    ports:
      - "5433:5432"  # 5433 に変更
```

### Python パッケージインストールエラー

```bash
# pip をアップグレード
pip install --upgrade pip

# 個別にインストール
pip install fastapi uvicorn sqlmodel alembic
```

## 開発時の便利なコマンド

### データベースのリセット

```bash
# データベースを削除して再作成
docker-compose down -v
docker-compose up -d postgres redis
cd packages/backend
alembic upgrade head
python scripts/create_test_user.py
```

### ログの確認

```bash
# すべてのサービスのログ
docker-compose logs -f

# 特定のサービスのログ
docker-compose logs -f postgres
docker-compose logs -f redis
```

### テストの実行

```bash
cd packages/backend
pytest

# カバレッジ付き
pytest --cov=app --cov-report=html
```

## 本番環境へのデプロイ

本番環境へのデプロイについては、別途 `DEPLOYMENT.md` を参照してください。

## 補足情報

### OAuth 設定（オプション）

実際のメール連携機能を使用する場合は、Google/Microsoft の開発者コンソールで OAuth アプリケーションを作成し、クライアント ID とシークレットを取得する必要があります。

### AWS Bedrock 設定（オプション）

AI 機能を使用する場合は、AWS アカウントで Bedrock を有効化し、適切な IAM 権限を持つアクセスキーを作成する必要があります。

### 開発用の便利な設定

VSCode を使用している場合は、以下の拡張機能をインストールすることをお勧めします：

- Python
- Pylance
- Black Formatter
- ESLint
- Prettier
- Docker

## サポート

問題が発生した場合は、Issue を作成するか、開発チームに連絡してください。