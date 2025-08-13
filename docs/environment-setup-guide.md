# PMO Agent 環境設定ガイド

このドキュメントでは、PMO Agent の環境変数設定に必要な値の取得方法を詳しく説明します。

## 目次

1. [データベース接続設定（PostgreSQL）](#1-データベース接続設定postgresql)
2. [Redis接続設定](#2-redis接続設定)
3. [JWT秘密鍵の生成](#3-jwt秘密鍵の生成)
4. [AWS Bedrock設定](#4-aws-bedrock設定)
5. [OAuth設定（Google/Microsoft）](#5-oauth設定)

---

## 1. データベース接続設定（PostgreSQL）

### 環境変数
```
DATABASE_URL=postgresql://[ユーザー名]:[パスワード]@[ホスト]:[ポート]/[データベース名]
```

### ローカル開発環境の設定手順

#### 方法1: Docker Composeを使用（推奨）

1. プロジェクトのdocker-compose.ymlファイルを確認
   ```bash
   cd pmo-agent
   cat docker-compose.yml
   ```

2. Docker Composeでデータベースを起動
   ```bash
   docker-compose up -d postgres
   ```

3. デフォルト値を使用
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pmo_agent
   ```

#### 方法2: ローカルPostgreSQLインストール

1. PostgreSQLをインストール
   - Windows: [公式サイト](https://www.postgresql.org/download/windows/)からダウンロード
   - Mac: `brew install postgresql`
   - Linux: `sudo apt-get install postgresql`

2. PostgreSQLサービスを起動
   ```bash
   # Mac/Linux
   brew services start postgresql
   # または
   sudo service postgresql start
   ```

3. データベースとユーザーを作成
   ```bash
   psql -U postgres
   CREATE DATABASE pmo_agent;
   CREATE USER pmo_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE pmo_agent TO pmo_user;
   \q
   ```

4. 環境変数を設定
   ```
   DATABASE_URL=postgresql://pmo_user:your_password@localhost:5432/pmo_agent
   ```

### 本番環境の設定

クラウドプロバイダーごとの設定：

#### AWS RDS
1. AWS ConsoleでRDS PostgreSQLインスタンスを作成
2. エンドポイント、ユーザー名、パスワードを取得
3. `DATABASE_URL=postgresql://[username]:[password]@[endpoint]:5432/[dbname]`

#### Google Cloud SQL
1. Cloud SQL PostgreSQLインスタンスを作成
2. 接続情報を取得
3. Cloud SQL Proxyを設定（必要に応じて）

#### Heroku
1. Heroku Postgresアドオンを追加
2. `heroku config:get DATABASE_URL`で接続文字列を取得

---

## 2. Redis接続設定

### 環境変数
```
REDIS_URL=redis://[ホスト]:[ポート]
```

### ローカル開発環境の設定手順

#### 方法1: Docker Composeを使用（推奨）

1. Docker ComposeでRedisを起動
   ```bash
   docker-compose up -d redis
   ```

2. デフォルト値を使用
   ```
   REDIS_URL=redis://localhost:6379
   ```

#### 方法2: ローカルRedisインストール

1. Redisをインストール
   - Windows: [Redis for Windows](https://github.com/microsoftarchive/redis/releases)
   - Mac: `brew install redis`
   - Linux: `sudo apt-get install redis-server`

2. Redisサービスを起動
   ```bash
   # Mac
   brew services start redis
   # Linux
   sudo service redis-server start
   ```

3. 接続確認
   ```bash
   redis-cli ping
   # "PONG"が返ればOK
   ```

### 本番環境の設定

#### AWS ElastiCache
1. ElastiCache Redisクラスターを作成
2. エンドポイントを取得
3. `REDIS_URL=redis://[endpoint]:6379`

#### Redis Cloud
1. [Redis Cloud](https://redis.com/cloud/)でインスタンスを作成
2. 接続情報を取得
3. `REDIS_URL=redis://:[password]@[endpoint]:[port]`

---

## 3. JWT秘密鍵の生成

### 環境変数
```
SECRET_KEY=your-secret-key-here
```

### 生成方法

#### 方法1: Node.jsを使用
```javascript
// generate-secret.js
const crypto = require('crypto');
const secret = crypto.randomBytes(64).toString('hex');
console.log('SECRET_KEY=' + secret);
```

実行：
```bash
node generate-secret.js
```

#### 方法2: OpenSSLを使用
```bash
openssl rand -hex 64
```

#### 方法3: Pythonを使用
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(64))"
```

### セキュリティ上の注意点
- 本番環境では必ず強力なランダム文字列を使用
- 秘密鍵は絶対にGitにコミットしない
- 定期的に鍵を更新することを推奨
- 最低でも32文字以上、推奨は64文字以上

---

## 4. AWS Bedrock設定

### 環境変数
```
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
```

### 設定手順

1. **AWSアカウントの作成**
   - [AWS](https://aws.amazon.com/)でアカウントを作成

2. **IAMユーザーの作成**
   ```
   1. AWS Consoleにログイン
   2. IAM → ユーザー → ユーザーを追加
   3. ユーザー名を入力（例：pmo-agent-bedrock）
   4. アクセスキー - プログラムによるアクセスを選択
   ```

3. **必要な権限の付与**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel",
           "bedrock:InvokeModelWithResponseStream",
           "bedrock:ListFoundationModels"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

4. **アクセスキーの取得**
   - IAMユーザー作成時に表示される
   - CSVファイルでダウンロード可能
   - **注意**: シークレットアクセスキーは一度しか表示されない

5. **Bedrockの有効化**
   ```
   1. AWS Console → Bedrock
   2. Model access → Edit
   3. 使用したいモデルを有効化（Claude, Titan等）
   4. リージョンを確認（us-east-1推奨）
   ```

### ローカル開発での代替手段
AI機能を使用しない場合は、これらの環境変数を空にしておくことも可能：
```
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
```

---

## 5. OAuth設定

### Google OAuth設定

#### 環境変数
```
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

#### 設定手順

1. **Google Cloud Consoleにアクセス**
   - [Google Cloud Console](https://console.cloud.google.com/)

2. **プロジェクトの作成または選択**
   ```
   1. プロジェクトセレクタをクリック
   2. 新しいプロジェクトを作成（または既存のものを選択）
   3. プロジェクト名：pmo-agent（例）
   ```

3. **OAuth同意画面の設定**
   ```
   1. APIとサービス → OAuth同意画面
   2. 外部を選択（または内部、組織による）
   3. アプリ名、サポートメール等を入力
   4. スコープの追加：
      - openid
      - email
      - profile
      - https://www.googleapis.com/auth/gmail.readonly（メール読み取り用）
   ```

4. **認証情報の作成**
   ```
   1. APIとサービス → 認証情報
   2. 認証情報を作成 → OAuthクライアントID
   3. アプリケーションの種類：ウェブアプリケーション
   4. 承認済みのリダイレクトURI：
      - http://localhost:3000/auth/google/callback（開発環境）
      - https://your-domain.com/auth/google/callback（本番環境）
   ```

5. **クライアントIDとシークレットの取得**
   - 作成後に表示される
   - JSONファイルでダウンロード可能

### Microsoft OAuth設定

#### 環境変数
```
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
```

#### 設定手順

1. **Azure Portalにアクセス**
   - [Azure Portal](https://portal.azure.com/)

2. **アプリの登録**
   ```
   1. Azure Active Directory → アプリの登録
   2. 新規登録をクリック
   3. 名前：PMO Agent（例）
   4. サポートされているアカウントの種類を選択
   5. リダイレクトURI：
      - Web: http://localhost:3000/auth/microsoft/callback（開発環境）
      - Web: https://your-domain.com/auth/microsoft/callback（本番環境）
   ```

3. **APIのアクセス許可**
   ```
   1. APIのアクセス許可 → アクセス許可の追加
   2. Microsoft Graph → 委任されたアクセス許可
   3. 以下を選択：
      - openid
      - profile
      - email
      - Mail.Read（メール読み取り用）
   ```

4. **クライアントシークレットの作成**
   ```
   1. 証明書とシークレット → 新しいクライアントシークレット
   2. 説明を入力（例：PMO Agent Secret）
   3. 有効期限を選択
   4. 値をコピー（一度しか表示されない）
   ```

5. **アプリケーション（クライアント）IDの取得**
   - 概要ページに表示される

### ローカル開発での代替手段
メール連携機能を使用しない場合は、これらの環境変数を空にしておくことも可能：
```
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
```

---

## 環境変数の設定方法

### 1. .envファイルの作成
```bash
cd pmo-agent
cp .env.example .env
```

### 2. .envファイルの編集
お好みのエディタで.envファイルを開き、上記で取得した値を設定

### 3. 環境変数の確認
```bash
# Node.jsでの確認
node -e "require('dotenv').config(); console.log(process.env.DATABASE_URL)"
```

### セキュリティのベストプラクティス

1. **.gitignoreの確認**
   ```bash
   # .envファイルがgitignoreされているか確認
   cat .gitignore | grep .env
   ```

2. **環境ごとの分離**
   - 開発：.env.development
   - テスト：.env.test
   - 本番：.env.production（サーバー上で直接設定）

3. **シークレット管理ツールの使用**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault

4. **定期的な鍵の更新**
   - JWT秘密鍵：3-6ヶ月ごと
   - OAuthクライアントシークレット：1年ごと
   - データベースパスワード：3ヶ月ごと

---

## トラブルシューティング

### データベース接続エラー
```
Error: connect ECONNREFUSED 127.0.0.1:5432
```
→ PostgreSQLが起動していない。docker-compose up -d postgresを実行

### Redis接続エラー
```
Error: Redis connection to localhost:6379 failed
```
→ Redisが起動していない。docker-compose up -d redisを実行

### AWS認証エラー
```
UnrecognizedClientException: The security token included in the request is invalid
```
→ AWS認証情報が正しくない。アクセスキーとシークレットキーを再確認

### OAuth認証エラー
```
Error: Invalid client_id or client_secret
```
→ OAuth設定が正しくない。リダイレクトURIも含めて再確認

---

## 次のステップ

1. すべての環境変数を設定したら、アプリケーションを起動
   ```bash
   cd pmo-agent
   pnpm install
   pnpm dev
   ```

2. 各サービスの接続を確認
   - データベース：マイグレーションの実行
   - Redis：キャッシュの動作確認
   - AWS Bedrock：AI機能のテスト
   - OAuth：ログイン機能のテスト

3. 問題が発生した場合は、ログを確認
   ```bash
   # バックエンドログ
   pnpm --filter backend logs
   
   # フロントエンドログ
   pnpm --filter frontend logs
   ```