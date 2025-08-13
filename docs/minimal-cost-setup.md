# PMO Agent 最小コスト動作検証ガイド

このガイドでは、OpenAI APIを使用して最小コストで PMO Agent を動作検証する手順を説明します。

## 必要なサービスとコスト見積もり

### 必須サービス
- **OpenAI API**: 約$5～10/月（軽い検証用途）
  - GPT-3.5-turbo使用
  - 入力: $0.0005/1K トークン
  - 出力: $0.0015/1K トークン

### オプションサービス（無料代替あり）
- **PostgreSQL**: Supabase Free Tier（500MB）または SQLite（無料）
- **Redis**: 不要（メモリキャッシュで代替）
- **メール**: Gmail API（無料枠あり）

## クイックスタート

### 1. プロジェクトのセットアップ

```bash
# リポジトリのクローン
git clone <repository-url>
cd pmo-agent

# 依存関係のインストール
npm install -g pnpm
pnpm install
```

### 2. バックエンドの設定

#### 2.1 Python環境のセットアップ

```bash
cd packages/backend

# Python仮想環境の作成と有効化
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

#### 2.2 環境変数の設定（.env）

```bash
cp .env.example .env
```

`.env` ファイルを以下のように編集：

```env
# === 基本設定 ===
PROJECT_NAME="PMO Agent"
VERSION="1.0.0"
API_PREFIX="/api/v1"
DEBUG=true

# === データベース（SQLite使用で無料） ===
DATABASE_URL=sqlite:///./pmo_agent.db
# PostgreSQL使用時（Supabase無料枠）
# DATABASE_URL=postgresql://user:password@host:5432/database

# === セキュリティ ===
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24時間

# === OpenAI設定（必須） ===
USE_OPENAI=true
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo  # コスト削減のため3.5使用
OPENAI_MAX_TOKENS=1000  # レスポンストークン制限
OPENAI_TEMPERATURE=0.3  # 安定性重視

# === AI設定 ===
USE_BEDROCK=false  # AWS Bedrockは使用しない
USE_MOCK_AI=false  # 本番AIを使用

# === メール設定（オプション） ===
# Gmailを使用する場合
GMAIL_ENABLED=true
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret

# Outlookは使用しない
OUTLOOK_ENABLED=false

# === キャッシュ設定 ===
USE_MEMORY_CACHE=true  # Redisの代わりにメモリキャッシュ使用
CACHE_TTL=3600  # 1時間

# === CORS設定 ===
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# === Celery設定（オプション） ===
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
# Celeryなしでも動作可能（同期処理になる）
USE_CELERY=false

# === ログ設定 ===
LOG_LEVEL=INFO
LOG_FILE=pmo_agent.log
```

#### 2.3 データベースの初期化

```bash
# マイグレーションの実行
alembic upgrade head

# 初期データの投入（オプション）
python scripts/seed_data.py
```

#### 2.4 バックエンドサーバーの起動

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. フロントエンドの設定

#### 3.1 環境変数の設定（.env.local）

```bash
cd packages/frontend
cp .env.example .env.local
```

`.env.local` ファイルを編集：

```env
# API設定
VITE_API_URL=http://localhost:8000
VITE_WEBSOCKET_URL=ws://localhost:8000

# 機能フラグ
VITE_MOCK_MODE=false  # 実際のAPIを使用
VITE_ENABLE_AI_FEATURES=true
VITE_ENABLE_EMAIL_SYNC=true
```

#### 3.2 フロントエンドサーバーの起動

```bash
pnpm dev
```

ブラウザで `http://localhost:5173` にアクセス

## 動作確認手順

### 1. ユーザー登録とログイン

1. トップページで「新規登録」をクリック
2. メールアドレスとパスワードを入力
3. ログイン

### 2. タスク作成とAI分析のテスト

```javascript
// テスト用タスクの例
{
  title: "プロジェクト提案書の作成",
  description: "Q2の新規プロジェクトについて提案書を作成する。予算と期限を含める。",
  priority: "high",
  due_date: "2024-02-01"
}
```

### 3. メール同期のテスト（Gmail使用時）

#### 3.1 Google Cloud Console での設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
3. Gmail API を有効化
4. OAuth 2.0 クライアントIDを作成
   - アプリケーションの種類: ウェブアプリケーション
   - 承認済みリダイレクトURI: `http://localhost:8000/api/v1/auth/callback/google`

#### 3.2 アプリケーションでの連携

1. 設定画面で「メール連携」を選択
2. 「Googleアカウントと連携」をクリック
3. Googleアカウントでログインして承認

### 4. AI機能のテスト

#### 4.1 メールからのタスク抽出

サンプルメール：
```
件名: プロジェクト会議の調整について
本文:
来週の火曜日（2/6）の14:00からプロジェクトキックオフ会議を開催したいと思います。
以下の準備をお願いします：
- 提案書の最終版を準備
- 予算計画を作成
- チームメンバーのスケジュール確認
```

期待される結果：
- 3つのタスクが自動生成される
- 各タスクに適切な優先度が設定される

#### 4.2 スレッド判定のテスト

1. 同じ件名で「Re:」を付けた返信メールを作成
2. メール同期を実行
3. 既存タスクが更新されることを確認

## コスト管理のベストプラクティス

### 1. トークン使用量の制限

```python
# backend/app/services/openai_service.py で設定
MAX_TOKENS = 1000  # レスポンスの最大トークン数
MAX_PROMPT_LENGTH = 2000  # プロンプトの最大文字数
```

### 2. キャッシュの活用

```python
# 同じメールスレッドの再分析を防ぐ
@cache.memoize(timeout=3600)
def analyze_thread(thread_id: str):
    # AI分析処理
```

### 3. バッチ処理の最適化

```python
# スレッド単位で処理（個別メールごとではない）
threads = group_emails_by_thread(emails)
for thread in threads:
    analyze_thread_once(thread)  # 1スレッド1回のAPI呼び出し
```

### 4. 使用量のモニタリング

```python
# OpenAI使用量の追跡
tracker = OpenAICostTracker()
response = await openai_client.chat.completions.create(...)
tracker.log_usage(response.usage)

# 日次レポート
daily_cost = tracker.get_daily_cost()
print(f"本日のOpenAI使用料: ${daily_cost:.2f}")
```

## トラブルシューティング

### OpenAI APIエラー

```python
# エラー: Rate limit exceeded
# 解決策: .envで以下を設定
OPENAI_RATE_LIMIT_RETRY=true
OPENAI_MAX_RETRIES=3
OPENAI_RETRY_DELAY=60
```

### メモリ不足エラー

```python
# 解決策: キャッシュサイズを制限
CACHE_MAX_SIZE=100  # 最大100アイテム
CACHE_TTL=1800  # 30分で自動削除
```

### データベース接続エラー

```bash
# SQLiteのパーミッション問題
chmod 664 pmo_agent.db
chmod 775 .
```

## 推奨される検証シナリオ

### フェーズ1: 基本機能（コスト: ~$1）
1. タスクの手動作成・編集・削除
2. ステータス管理
3. 優先度設定

### フェーズ2: AI機能（コスト: ~$3）
1. 単一メールからのタスク抽出
2. タスク内容のAI分析
3. 優先度の自動判定

### フェーズ3: スレッド処理（コスト: ~$5）
1. メールスレッドの同期
2. スレッド単位でのタスク管理
3. 既存タスクの自動更新

## セキュリティ上の注意

1. **APIキーの管理**
   - `.env` ファイルを Git にコミットしない
   - 本番環境では環境変数を使用

2. **CORS設定**
   - 本番環境では許可するオリジンを制限

3. **レート制限**
   - OpenAI APIのレート制限に注意
   - 必要に応じて独自のレート制限を実装

## 本番環境への移行

最小コストでの本番運用：

- **フロントエンド**: Vercel Free Tier
- **バックエンド**: Render.com Free Tier (制限あり)
- **データベース**: Supabase Free Tier (500MB)
- **Redis**: Upstash Free Tier (10,000コマンド/日)

月額コスト見積もり：
- 開発・検証: $5-10
- 小規模本番（10ユーザー）: $20-30
- 中規模本番（100ユーザー）: $100-200

## サポート

問題が発生した場合：
1. ログファイルを確認: `packages/backend/pmo_agent.log`
2. OpenAI使用量を確認: `http://localhost:8000/api/v1/admin/openai-usage`
3. デバッグモードで実行: `DEBUG=true uvicorn app.main:app --reload`