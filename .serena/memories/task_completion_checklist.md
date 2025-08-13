# タスク完了時のチェックリスト

## コード品質チェック

### バックエンド (Python)
1. **フォーマット実行**
   ```bash
   cd packages/backend
   black .
   isort .
   ```

2. **リント実行**
   ```bash
   flake8
   mypy app
   ```

3. **テスト実行**
   ```bash
   pytest
   pytest --cov=app tests/  # カバレッジ確認
   ```

### フロントエンド (TypeScript/React)
1. **リント・フォーマット**
   ```bash
   cd packages/frontend
   npm run lint
   npm run format
   ```

2. **型チェック**
   ```bash
   npm run type-check
   ```

3. **テスト実行**
   ```bash
   npm run test
   ```

## 統合チェック

1. **全体のリント・フォーマット**
   ```bash
   # プロジェクトルートで
   npm run lint
   npm run format
   ```

2. **ビルド確認**
   ```bash
   npm run build
   ```

3. **Docker環境での動作確認**
   ```bash
   docker-compose up -d
   # ヘルスチェック確認
   curl http://localhost:8000/health
   ```

## コミット前の最終確認

1. **変更内容の確認**
   ```bash
   git status
   git diff
   ```

2. **不要なファイルが含まれていないか確認**
   - .env ファイル
   - __pycache__
   - node_modules
   - 個人的な設定ファイル

3. **コミットメッセージの規約**
   - feat: 新機能
   - fix: バグ修正
   - docs: ドキュメント変更
   - style: フォーマット変更
   - refactor: リファクタリング
   - test: テスト追加・修正
   - chore: ビルドプロセスや補助ツールの変更

## プルリクエスト作成時

1. **ブランチが最新か確認**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **CI/CDパイプラインの確認**
   - GitHub Actions が全てグリーン
   - テストカバレッジが低下していない

3. **ドキュメントの更新**
   - 新機能の場合は README やドキュメントを更新
   - API変更の場合は OpenAPI 仕様を更新