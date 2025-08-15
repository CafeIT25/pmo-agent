# Serena MCP 活用ガイド

## 概要

Serena MCP (Model Context Protocol) は、AI コーディングアシスタントに セマンティックコード検索と編集機能を提供するオープンソースツールキットです。

## セットアップ済み機能

### 1. 基本設定

プロジェクトには以下が設定済みです：

- **設定ファイル**: `.serena/serena_config.yml`
- **Cursor 統合**: `.cursor/mcp.json`
- **プロジェクトルート**: 自動認識
- **コンテキスト**: `ide-assistant` モード

### 2. 対応言語

- TypeScript/JavaScript (フロントエンド)
- Python (バックエンド)
- JSON/YAML (設定ファイル)
- Markdown (ドキュメント)

### 3. インデックス対象

- `packages/frontend/src/` - React/TypeScript コンポーネント
- `packages/backend/app/` - FastAPI/Python アプリケーション
- `docs/` - プロジェクトドキュメント

## 主な機能

### セマンティック検索

```bash
# コード内の特定の機能を検索
serena search "認証機能"
serena search "チャット機能"
serena search "タスク管理"
```

### コード編集

- 自動フォーマット機能
- 編集時のバックアップ作成
- LSP (Language Server Protocol) 統合

### シェル実行

- プロジェクトルートでの安全なコマンド実行
- タイムアウト設定 (5分)
- ログ記録

## 活用方法

### 1. Claude Code での利用

```bash
# Claude Code に Serena MCP を追加
claude mcp add-json "serena" '{
  "command": "uvx",
  "args": [
    "--from",
    "git+https://github.com/oraios/serena",
    "serena-mcp-server",
    "--context",
    "ide-assistant"
  ]
}'
```

### 2. コード解析とリファクタリング

- **大規模コードベースの理解**: セマンティック検索でコードの関連性を把握
- **依存関係の追跡**: 関数やクラスの使用箇所を自動検出
- **リファクタリング支援**: 安全な変更提案と影響範囲分析

### 3. バグ修正とデバッグ

- **エラーパターンの検索**: 類似のバグ修正例を検索
- **コードフローの追跡**: 実行パスの可視化
- **テストケースの提案**: 関連するテストパターンの検出

## パフォーマンス最適化

### インデックス管理

```yaml
# .serena/serena_config.yml での設定
performance:
  cache_enabled: true
  max_file_size: 1048576  # 1MB
  index_on_startup: true
```

### 除外パターン

不要なファイルを除外してパフォーマンスを向上：

```yaml
exclude_patterns:
  - "node_modules/**"
  - "dist/**"
  - "__pycache__/**"
```

## トラブルシューティング

### ログ確認

```bash
# Serena ログの確認
tail -f .serena/logs/serena.log
```

### 設定の検証

```bash
# 設定ファイルの構文チェック
serena validate-config
```

### キャッシュのクリア

```bash
# インデックスの再構築
serena reindex
```

## 推奨ワークフロー

1. **プロジェクト開始時**: `serena index` でコードベースをインデックス化
2. **機能開発時**: セマンティック検索で関連コードを調査
3. **コードレビュー時**: 自動解析で潜在的な問題を検出
4. **リファクタリング時**: 影響範囲を事前に分析

## セキュリティ考慮事項

- シェル実行は制限された環境で実行
- 機密情報のインデックス化を避ける
- ログファイルのアクセス権限を適切に設定

## 追加リソース

- [Serena GitHub Repository](https://github.com/oraios/serena)
- [MCP.pizza Documentation](https://www.mcp.pizza/)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)