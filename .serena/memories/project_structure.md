# PMO Agent プロジェクト構造

```
pmo-agent/
├── .github/
│   └── workflows/          # CI/CD (GitHub Actions)
│       └── deploy.yml
├── docs/                   # プロジェクトドキュメント
│   ├── requirements.md     # 要件定義書 (EARS記法)
│   ├── design.md          # システム設計書
│   └── tasks.md           # 実装タスクリスト
├── packages/
│   ├── frontend/          # React (Vite) プロジェクト
│   │   ├── public/        # 静的アセット
│   │   ├── src/
│   │   │   ├── api/       # APIクライアント
│   │   │   ├── assets/    # 画像など
│   │   │   ├── components/# Atomic Design
│   │   │   │   ├── atoms/
│   │   │   │   ├── molecules/
│   │   │   │   ├── organisms/
│   │   │   │   └── templates/
│   │   │   ├── hooks/     # カスタムフック
│   │   │   ├── pages/     # ページコンポーネント
│   │   │   ├── store/     # Zustand ストア
│   │   │   ├── types/     # 型定義
│   │   │   ├── utils/     # ユーティリティ
│   │   │   └── main.tsx   # エントリーポイント
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   └── backend/           # FastAPI プロジェクト
│       ├── app/
│       │   ├── api/       # APIルーター
│       │   │   └── v1/
│       │   │       ├── endpoints/
│       │   │       └── api.py
│       │   ├── core/      # 設定、セキュリティ
│       │   ├── crud/      # データベース操作
│       │   ├── models/    # SQLModel
│       │   ├── schemas/   # Pydantic スキーマ
│       │   ├── services/  # ビジネスロジック
│       │   ├── worker/    # Celery タスク
│       │   └── main.py    # FastAPI アプリ
│       ├── tests/         # テストコード
│       ├── alembic/       # DBマイグレーション
│       ├── requirements.txt
│       └── Dockerfile
│
├── docker-compose.yml     # 開発環境
├── package.json          # モノレポ管理
├── turbo.json           # Turbo設定
├── .prettierrc          # Prettier設定
└── .gitignore

## 主要ファイルの役割

- **turbo.json**: モノレポのビルド・タスク管理
- **docker-compose.yml**: PostgreSQL, Redis, Backend の開発環境
- **requirements.txt**: Python依存関係
- **package.json**: Node.js依存関係とスクリプト

## 環境変数ファイル
- **.env**: ローカル開発用（gitignore対象）
- **.env.example**: 環境変数のテンプレート