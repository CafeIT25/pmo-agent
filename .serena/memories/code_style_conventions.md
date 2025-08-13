# コードスタイルとコンベンション

## Python (バックエンド)
- **フォーマット**: Black (line-length: 88)
- **インポート順序**: isort
- **型ヒント**: 全ての関数とクラスで必須
- **命名規則**: 
  - 関数/変数: snake_case
  - クラス: PascalCase
  - 定数: UPPER_SNAKE_CASE
- **Docstring**: Google スタイル

## TypeScript/JavaScript (フロントエンド)
- **フォーマット**: Prettier
  - semi: true
  - singleQuote: true
  - printWidth: 100
  - tabWidth: 2
- **リンター**: ESLint
- **命名規則**:
  - 関数/変数: camelCase
  - コンポーネント: PascalCase
  - 定数: UPPER_SNAKE_CASE
- **型定義**: 全ての関数とコンポーネントで必須

## 共通規則
- **エンコーディング**: UTF-8
- **改行コード**: LF
- **末尾スペース**: 削除
- **ファイル末尾改行**: あり

## アーキテクチャ原則
- **Clean Architecture**: ビジネスロジックとインフラの分離
- **SOLID原則**: 特に単一責任とインターフェース分離
- **DRY原則**: 重複コードの排除
- **KISS原則**: シンプルな実装を優先

## ディレクトリ構造
- フロントエンド: Atomic Design に基づくコンポーネント構造
- バックエンド: レイヤードアーキテクチャ (api/core/models/schemas/services)