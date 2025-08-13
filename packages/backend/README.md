# PMO Agent Backend

## 開発環境セットアップ

### 1. 環境変数設定

```bash
cp .env.example .env
# .env ファイルを編集して必要な値を設定
```

### 2. Docker起動

```bash
# プロジェクトルートから
docker-compose up -d postgres redis
```

### 3. データベースマイグレーション

```bash
cd packages/backend
alembic upgrade head
```

### 4. テストユーザー作成

開発環境用のテストユーザーを作成します：

```bash
python scripts/create_test_user.py
```

作成されるテストユーザー：

| Email | Password | 備考 |
|-------|----------|------|
| test@example.com | testpass123 | 一般ユーザー（Gmail連携モック済み） |
| admin@example.com | adminpass123 | 管理者ユーザー |
| demo@example.com | demopass123 | デモユーザー（Outlook連携モック済み） |

### 5. サーバー起動

```bash
# 開発サーバー
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celeryワーカー（別ターミナル）
celery -A app.worker.celery_app worker --loglevel=info

# Celery Beat（定期タスク用、別ターミナル）
celery -A app.worker.celery_app beat --loglevel=info
```

## API ドキュメント

サーバー起動後、以下のURLでAPIドキュメントを確認できます：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## テスト実行

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=app --cov-report=html

# 特定のテストのみ
pytest tests/test_email_endpoints.py
```

## 主要エンドポイント

### 認証
- `POST /api/v1/auth/login` - ログイン
- `POST /api/v1/auth/register` - 新規登録
- `POST /api/v1/auth/refresh` - トークンリフレッシュ

### メール連携
- `POST /api/v1/email/sync` - メール同期開始
- `GET /api/v1/email/sync/{job_id}` - 同期状態確認

### AI機能
- `POST /api/v1/ai/task-suggestions` - タスク提案生成
- `GET /api/v1/ai/job/{job_id}` - AI処理状態確認

### OAuth
- `GET /api/v1/oauth/google/authorize` - Google認証開始
- `GET /api/v1/oauth/microsoft/authorize` - Microsoft認証開始