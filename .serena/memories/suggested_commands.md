# PMO Agent 開発コマンド

## プロジェクト全体
```bash
# 依存関係のインストール
pnpm install

# 開発サーバー起動（フロントエンド・バックエンド同時）
pnpm dev

# ビルド
pnpm build

# テスト実行
pnpm test

# リント実行
pnpm lint

# コードフォーマット
pnpm format
```

## バックエンド開発
```bash
# バックエンドディレクトリへ移動
cd packages/backend

# Python仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt

# 開発サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# データベースマイグレーション
alembic upgrade head
alembic revision --autogenerate -m "Description"

# テスト実行
pytest
pytest --cov=app tests/

# コードフォーマット・チェック
black .
isort .
flake8
mypy app
```

## フロントエンド開発
```bash
# フロントエンドディレクトリへ移動
cd packages/frontend

# 開発サーバー起動
pnpm dev

# ビルド
pnpm build

# テスト
pnpm test

# リント
pnpm lint
```

## Docker操作
```bash
# 全サービス起動
docker-compose up -d

# ログ確認
docker-compose logs -f

# サービス停止
docker-compose down

# データベースを含めて削除
docker-compose down -v
```

## Git操作
```bash
# ブランチ作成
git checkout -b feature/機能名

# コミット前のチェック
pnpm lint
pnpm test

# コミット
git add .
git commit -m "feat: 機能の説明"

# プッシュ
git push origin feature/機能名
```

## 環境変数設定
```bash
# .env ファイルのコピー
cp .env.example .env

# 編集
nano .env  # または好みのエディタ
```