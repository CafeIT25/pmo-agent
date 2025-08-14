# PMO Agent デモ環境構築ガイド

このディレクトリには、PMO Agent のデモ環境を構築するための詳細な手順書が含まれています。

## 📚 ドキュメント一覧

### 1. [OpenAI API 設定手順](./01-openai-api-setup.md)
OpenAI アカウントの作成からAPIキーの取得、料金設定まで、画像付きで詳しく説明しています。

**所要時間**: 約15分  
**必要なもの**: 
- メールアドレス
- 電話番号（SMS認証用）
- クレジットカード（課金設定用）

### 2. [Azure AD 設定手順](./02-azure-ad-setup.md)
Microsoft 365 / Outlook 連携のための Azure Active Directory アプリケーション登録手順です。

**所要時間**: 約20分  
**必要なもの**:
- Microsoft アカウント
- Azure Portal へのアクセス（無料）

### 3. [環境構築手順](./03-environment-setup.md)
アプリケーションの環境構築、依存関係のインストール、設定ファイルの作成手順です。

**所要時間**: 約30分  
**必要なもの**:
- Node.js 18以上
- Python 3.11以上
- Git

### 4. [動作確認手順](./04-testing-guide.md)
構築した環境での機能テスト、API連携確認、メール同期テストの手順です。

**所要時間**: 約30分  
**テスト項目**:
- 基本機能（ユーザー登録、タスク管理）
- OpenAI API連携
- Outlook メール同期
- スレッド処理

### 📈 [パフォーマンス最適化ガイド](./performance-optimization-guide.md)
Gmail N+1問題を解決し、Railway無料プランで最高のパフォーマンスを実現する最適化手法です。

**効果**: Gmail同期時間87%改善（120秒→15秒）  
**最適化技術**:
- Gmail バッチリクエスト
- インテリジェントキャッシュ
- 並行処理最適化
- エラー耐性強化

### 5. [トラブルシューティング](./05-troubleshooting.md)
よくある問題とその解決方法、エラーメッセージ別の対処法をまとめています。

**カバー範囲**:
- 環境構築エラー
- API認証エラー
- データベースエラー
- パフォーマンス問題

## 🚀 デプロイフロー（推奨）

### ローカル開発環境（開発・テスト用）

最小限の手順で動作確認まで行う場合：

```bash
# 1. リポジトリのクローン
git clone <repository-url> pmo-agent
cd pmo-agent

# 2. 依存関係のインストール
npm install -g pnpm
pnpm install

# 3. バックエンドセットアップ
cd packages/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .envを編集してAPIキーを設定

# 4. データベース初期化
alembic upgrade head

# 5. バックエンド起動
uvicorn app.main:app --reload

# 6. フロントエンド起動（別ターミナル）
cd packages/frontend
cp .env.example .env.local
pnpm dev

# 7. ブラウザでアクセス
open http://localhost:5173
```

### 本番環境デプロイ（無料プラン）

完全な本番環境での検証を行う場合：

```mermaid
graph LR
    A[1. 前提条件] --> B[2. フロントエンド<br/>Vercel]
    B --> C[3. バックエンド<br/>Railway]
    C --> D[4. 統合設定]
    D --> E[5. 動作検証]
```

**推奨フロー**:
1. **[前提条件](./01-openai-api-setup.md) + [Azure AD設定](./02-azure-ad-setup.md)** (45分)
2. **[フロントエンド Vercel デプロイ](./06-frontend-deployment-vercel.md)** (30分)
3. **[バックエンド Railway デプロイ](./07-backend-deployment-railway.md)** (45分)
4. **[統合デプロイ設定](./09-production-deployment-guide.md)** (15分)
5. **[本番環境動作検証](./10-production-testing.md)** (90分)

**総所要時間**: 約3.5時間（初回）、1.5時間（慣れた場合）

## 💰 コスト見積もり

### 開発・検証環境

| サービス | 月額コスト | 備考 |
|---------|-----------|------|
| OpenAI API | $5-10 | GPT-3.5-turbo使用、軽い検証 |
| データベース | $0 | SQLite使用 |
| ホスティング | $0 | ローカル環境 |
| **合計** | **$5-10** | |

### 小規模本番環境（10ユーザー）

| サービス | 月額コスト | 備考 |
|---------|-----------|------|
| OpenAI API | $20-30 | 日次利用 |
| データベース | $0-5 | Supabase Free/Starter |
| ホスティング | $0-10 | Vercel/Render |
| **合計** | **$20-45** | |

## 🔒 セキュリティ注意事項

1. **APIキーの管理**
   - `.env` ファイルは絶対にGitにコミットしない
   - 本番環境では環境変数を使用
   - 定期的にキーをローテーション

2. **アクセス制限**
   - CORS設定を適切に行う
   - 本番環境ではHTTPSを必須に
   - レート制限を実装

3. **データ保護**
   - センシティブなデータは暗号化
   - バックアップを定期的に取得
   - アクセスログを記録

## 📊 必要なAPI設定値一覧と記載場所

### 🗂️ 設定ファイルの場所

| ファイル | パス | 用途 |
|---------|------|------|
| **バックエンド環境変数** | `pmo-agent/packages/backend/.env` | APIキー、データベース設定など |
| **フロントエンド環境変数** | `pmo-agent/packages/frontend/.env.local` | API接続先、機能フラグなど |

### OpenAI 設定

| 設定項目 | 環境変数名 | 取得方法 | 記載ファイル |
|---------|-----------|---------|-------------|
| APIキー | OPENAI_API_KEY | [01-openai-api-setup.md](./01-openai-api-setup.md) 手順2.3 | `backend/.env` |
| モデル | OPENAI_MODEL | gpt-3.5-turbo（推奨） | `backend/.env` |
| 最大トークン | OPENAI_MAX_TOKENS | 1000（推奨） | `backend/.env` |

### Microsoft/Outlook 設定

| 設定項目 | 環境変数名 | 取得方法 | 記載ファイル |
|---------|-----------|---------|-------------|
| クライアントID | MICROSOFT_CLIENT_ID | [02-azure-ad-setup.md](./02-azure-ad-setup.md) 手順3.1 | `backend/.env` |
| クライアントシークレット | MICROSOFT_CLIENT_SECRET | [02-azure-ad-setup.md](./02-azure-ad-setup.md) 手順4.3 | `backend/.env` |
| テナントID | MICROSOFT_TENANT_ID | common または実際のID（手順3.2） | `backend/.env` |

## 🛠️ 推奨開発ツール

- **エディタ**: Visual Studio Code
  - 拡張機能: Python, Pylance, ESLint, Prettier
- **API テスト**: Postman または Thunder Client
- **データベース管理**: DB Browser for SQLite
- **ログ監視**: tail, grep, jq

## 📝 チェックリスト

環境構築完了の確認：

- [ ] Python 3.11以上がインストールされている
- [ ] Node.js 18以上がインストールされている
- [ ] OpenAI APIキーを取得した
- [ ] Azure ADアプリを登録した（Outlook連携する場合）
- [ ] .env ファイルを設定した
- [ ] データベースを初期化した
- [ ] バックエンドが起動する
- [ ] フロントエンドが起動する
- [ ] ログイン画面が表示される
- [ ] タスクを作成できる
- [ ] AI機能が動作する

## 🆘 サポート

問題が発生した場合：

1. [トラブルシューティング](./05-troubleshooting.md) を確認
2. ログファイルを確認（`packages/backend/pmo_agent.log`）
3. GitHub Issues で質問

## 📈 次のステップ

デモ環境の構築が完了したら：

1. **機能拡張**: カスタムタスクフィールド、通知機能など
2. **本番デプロイ**: クラウド環境への展開
3. **チーム利用**: 複数ユーザーでの運用
4. **自動化強化**: より高度なAI機能の実装

---

最終更新: 2024年1月
バージョン: 1.0.0