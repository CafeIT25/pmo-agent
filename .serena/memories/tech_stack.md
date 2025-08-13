# PMO Agent 技術スタック

## フロントエンド
- **フレームワーク**: React + TypeScript + Vite
- **状態管理**: Zustand
- **スタイリング**: Tailwind CSS
- **UIコンポーネント**: shadcn/ui
- **API通信**: Axios
- **ルーティング**: React Router
- **フォーム管理**: React Hook Form
- **アイコン**: Lucide React

## バックエンド
- **言語/フレームワーク**: Python / FastAPI
- **データベース**: PostgreSQL
- **ORM**: SQLModel
- **認証**: JWT (JSON Web Tokens)
- **非同期タスク**: Celery / Redis
- **メール連携**: Google API Python Client, Microsoft Graph SDK

## AI / LLM
- **LLM基盤**: AWS Bedrock
- **SDK**: Boto3

## インフラストラクチャ (無料プラン)
- **フロントエンド**: Vercel (Hobby Plan)
- **バックエンドAPI**: Render (Free Plan)
- **データベース**: Render (Free Plan) - PostgreSQL
- **キャッシュ/キュー**: Render (Free Plan) - Redis
- **CI/CD**: GitHub Actions

## 開発ツール
- **モノレポ管理**: Turbo
- **パッケージマネージャー**: npm/yarn
- **コード品質**: ESLint, Prettier, Black, isort
- **テスト**: pytest (Backend), Jest/Vitest (Frontend)
- **Git hooks**: Husky + lint-staged