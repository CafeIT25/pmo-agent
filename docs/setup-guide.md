# PMO Agent セットアップガイド

## 無料動作検証手順

PMO Agent を無料で動作検証するための手順です。開発サーバーでの動作確認を中心に説明します。

## 前提条件

- Node.js 18以上
- Python 3.11以上
- pnpm（パッケージマネージャー）
- Git

## 1. 環境構築

### 1.1 リポジトリのクローン

```bash
git clone <repository-url>
cd pmo-agent
```

### 1.2 依存関係のインストール

```bash
# pnpmのインストール（未インストールの場合）
npm install -g pnpm

# プロジェクトの依存関係インストール
pnpm install
```

### 1.3 環境変数の設定

#### フロントエンド（`.env.local`）

```bash
cd packages/frontend
cp .env.example .env.local
```

`.env.local` を編集：

```env
# API設定
VITE_API_URL=http://localhost:8000
VITE_WEBSOCKET_URL=ws://localhost:8000

# 開発環境設定
VITE_MOCK_MODE=true  # モックデータを使用する場合
```

#### バックエンド（`.env`）

```bash
cd packages/backend
cp .env.example .env
```

`.env` を編集：

```env
# データベース（SQLite使用で無料）
DATABASE_URL=sqlite:///./pmo_agent.db

# Redis（オプション - メモリキャッシュで代替可能）
REDIS_HOST=localhost
REDIS_PORT=6379
USE_MEMORY_CACHE=true  # Redisなしでメモリキャッシュ使用

# OpenAI API（無料枠なし - 要クレジット）
OPENAI_API_KEY=sk-your-api-key-here
# または無料検証用のモックモード
USE_MOCK_AI=true

# JWT設定
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS設定
CORS_ORIGINS=["http://localhost:5173"]

# メール設定（オプション）
GMAIL_ENABLED=false
OUTLOOK_ENABLED=false
```

## 2. 開発サーバーの起動

### 2.1 バックエンドサーバー

```bash
cd packages/backend

# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# データベースの初期化
alembic upgrade head

# 開発サーバーの起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2.2 フロントエンドサーバー

新しいターミナルで：

```bash
cd packages/frontend

# 開発サーバーの起動
pnpm dev
```

ブラウザで `http://localhost:5173` にアクセス

## 3. 無料検証用の設定

### 3.1 モックモードでの動作

AI機能をモックで動作させる場合：

1. バックエンドの `.env` で `USE_MOCK_AI=true` を設定
2. フロントエンドの `.env.local` で `VITE_MOCK_MODE=true` を設定

これにより、以下の機能がモックデータで動作します：
- メール同期（サンプルメールデータ）
- AI タスク判定（事前定義されたルール）
- AI 調査機能（テンプレート回答）

### 3.2 デモデータの利用

フロントエンドには3つのデモタスクが含まれています：

1. **プロジェクト計画書の作成**（進行中）
2. **API認証機能のバグ修正**（TODO）
3. **月次レポートのレビュー**（完了）

これらは `packages/frontend/src/data/mockTasks.ts` で定義されています。

## 4. 基本機能の確認

### 4.1 ユーザー登録・ログイン

1. トップページで「新規登録」をクリック
2. メールアドレスとパスワードを入力
3. モックモードではメール確認をスキップ

### 4.2 タスク管理

1. ダッシュボードで「新規タスク」ボタンをクリック
2. タスク情報を入力して作成
3. タスクカードをクリックして詳細表示
4. ステータスをドロップダウンで変更（TODO → 進行中 → 完了）

### 4.3 メール同期（モック）

1. 「メール同期」ボタンをクリック
2. モックデータから自動的にタスクが生成
3. 同一スレッドのメールは1つのタスクとして管理

### 4.4 AI調査機能（モック）

1. タスク詳細画面で「AI調査」タブを選択
2. 「AIに調査を依頼」ボタンをクリック
3. モックの調査結果が表示

## 5. OpenAI API を使用する場合

### 5.1 APIキーの取得

1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. アカウント作成・ログイン
3. API Keys セクションで新しいキーを生成
4. `.env` の `OPENAI_API_KEY` に設定

### 5.2 料金の目安

- GPT-3.5-turbo 使用時
- 入力: $0.0005/1K トークン
- 出力: $0.0015/1K トークン
- 月間予算1万円で約50,000リクエスト処理可能

### 5.3 コスト管理

バックエンドには `OpenAICostTracker` が実装されており、使用量を追跡できます。

## 6. 本番環境へのデプロイ（Vercel）

### 6.1 Vercel へのデプロイ

```bash
# Vercel CLI のインストール
npm i -g vercel

# フロントエンドのデプロイ
cd packages/frontend
vercel

# 環境変数の設定
# Vercel ダッシュボードで以下を設定：
# - VITE_API_URL: バックエンドのURL
# - その他必要な環境変数
```

### 6.2 バックエンドのデプロイ（Render.com）

1. [Render.com](https://render.com/) でアカウント作成
2. 新しい Web Service を作成
3. GitHub リポジトリを接続
4. ビルドコマンド: `pip install -r requirements.txt`
5. スタートコマンド: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. 環境変数を設定

## 7. トラブルシューティング

### 問題: CORS エラー

**解決策**: バックエンドの `.env` で `CORS_ORIGINS` にフロントエンドのURLを追加

### 問題: データベース接続エラー

**解決策**: SQLite を使用するか、PostgreSQL の接続文字列を確認

### 問題: AI機能が動作しない

**解決策**: 
1. `USE_MOCK_AI=true` でモックモードを有効化
2. または有効な OpenAI API キーを設定

### 問題: メール同期が動作しない

**解決策**: モックモードを使用するか、Google/Microsoft の OAuth 設定を完了

## 8. 開発のヒント

### 拡張性を考慮した設計

- **サービス層の抽象化**: AI サービスは Interface で定義され、簡単に切り替え可能
- **プラグイン可能なアーキテクチャ**: 新しいメールプロバイダーや AI プロバイダーを追加可能
- **設定の外部化**: 環境変数で動作を制御

### パフォーマンス最適化

- **バッチ処理**: 複数のメールを1回のAPIコールで処理
- **キャッシュ**: Redis またはメモリキャッシュでレスポンスを高速化
- **非同期処理**: Celery を使用したバックグラウンドタスク

## 9. 次のステップ

1. **認証機能の強化**: OAuth2.0、2要素認証
2. **通知機能**: メール、Slack 連携
3. **レポート機能**: タスク分析、生産性レポート
4. **チーム機能**: 複数ユーザーでのタスク共有

## サポート

問題が発生した場合は、以下を確認してください：

1. このドキュメントのトラブルシューティングセクション
2. `docs/` フォルダ内の他のドキュメント
3. GitHub Issues でのバグ報告

---

最終更新: 2024年1月