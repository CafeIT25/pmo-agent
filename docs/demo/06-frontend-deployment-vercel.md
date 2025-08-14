# フロントエンド Vercel デプロイ手順

## 1. Vercel アカウントの準備

### 1.1 Vercel アカウント作成

1. [Vercel](https://vercel.com/) にアクセス
2. 「Sign Up」をクリック
3. GitHub アカウントで連携（推奨）
   ```
   Continue with GitHub
   ```
4. 必要な権限を許可

### 1.2 Vercel CLI のインストール

```bash
# グローバルインストール
npm install -g vercel

# ログイン
vercel login
# → ブラウザでVercelアカウントと連携

# 確認
vercel --version
```

## 2. プロジェクトの準備

### 2.1 フロントエンドディレクトリの確認

```bash
cd pmo-agent/packages/frontend

# package.json の確認
cat package.json | grep -A 5 '"scripts"'
```

期待される scripts:
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

### 2.2 ビルド設定の最適化

**📁 ファイルの場所**: `pmo-agent/packages/frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // 本番では無効化
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@headlessui/react', '@heroicons/react']
        }
      }
    }
  },
  server: {
    port: 5173,
    host: true
  }
})
```

### 2.3 環境変数の設定（本番用）

**📁 ファイルの場所**: `pmo-agent/packages/frontend/.env.production`

```env
# 本番環境用設定（後でRailwayのURLに更新）
VITE_API_URL=https://your-backend-app.railway.app
VITE_WEBSOCKET_URL=wss://your-backend-app.railway.app

# 機能フラグ
VITE_MOCK_MODE=false
VITE_ENABLE_AI_FEATURES=true
VITE_ENABLE_EMAIL_SYNC=true

# 本番環境識別
VITE_ENVIRONMENT=production
```

## 3. Vercel プロジェクトの作成

### 3.1 GitHub リポジトリとの連携

1. GitHub にプロジェクトをプッシュ（まだの場合）：

```bash
# プロジェクトルートで
git add .
git commit -m "Add production environment configuration"
git push origin main
```

2. Vercel ダッシュボードで「New Project」をクリック
3. GitHub リポジトリを選択
4. 「Import」をクリック

### 3.2 プロジェクト設定

#### Framework Preset
```
Vite
```

#### Root Directory
```
packages/frontend
```

#### Build Command
```
npm run build
```

#### Output Directory
```
dist
```

#### Install Command
```
pnpm install
```

### 3.3 環境変数の設定

Vercel ダッシュボードで：

1. Project Settings → Environment Variables
2. 以下の変数を追加：

| Name | Value | Environment |
|------|-------|-------------|
| `VITE_API_URL` | `https://your-backend-app.railway.app` | Production |
| `VITE_WEBSOCKET_URL` | `wss://your-backend-app.railway.app` | Production |
| `VITE_MOCK_MODE` | `false` | Production |
| `VITE_ENABLE_AI_FEATURES` | `true` | Production |
| `VITE_ENABLE_EMAIL_SYNC` | `true` | Production |
| `VITE_ENVIRONMENT` | `production` | Production |

⚠️ **重要**: バックエンドのデプロイ後にAPIのURLを更新する必要があります

## 4. デプロイの実行

### 4.1 初回デプロイ

```bash
cd packages/frontend

# Vercel プロジェクトの初期化
vercel

# プロジェクト設定
? Set up and deploy "~/pmo-agent/packages/frontend"? [Y/n] y
? Which scope do you want to deploy to? [あなたのアカウント]
? Link to existing project? [Y/n] n
? What's your project's name? pmo-agent-frontend
? In which directory is your code located? ./

# 設定確認
? Want to modify these settings? [y/N] y
```

設定内容：
```
✅ Project Name: pmo-agent-frontend
✅ Framework: Vite
✅ Root Directory: ./
✅ Build Command: npm run build
✅ Output Directory: dist
```

### 4.2 本番デプロイ

```bash
# 本番環境へデプロイ
vercel --prod
```

期待される出力：
```
🔍  Inspect: https://vercel.com/your-username/pmo-agent-frontend/xxx
✅  Production: https://pmo-agent-frontend.vercel.app
```

## 5. カスタムドメインの設定（オプション）

### 5.1 独自ドメインの追加

1. Vercel ダッシュボード → Project → Settings → Domains
2. カスタムドメインを入力：
   ```
   pmo-agent.your-domain.com
   ```
3. DNS レコードを設定：
   ```
   Type: CNAME
   Name: pmo-agent
   Value: cname.vercel-dns.com
   ```

### 5.2 HTTPS の自動設定

Vercel は自動的に Let's Encrypt SSL証明書を設定します。
- 数分後に `https://pmo-agent.your-domain.com` でアクセス可能

## 6. デプロイ後の設定更新

### 6.1 Azure AD リダイレクト URI の追加

1. [Azure Portal](https://portal.azure.com/) にアクセス
2. Azure Active Directory → アプリの登録 → PMO Agent
3. 「認証」→「プラットフォーム構成」→「Web」
4. リダイレクト URI を追加：

**追加するURI**:
```
https://your-backend-app.railway.app/api/v1/auth/callback/microsoft
```

⚠️ **重要**: バックエンドのURLを使用します

### 6.2 CORS 設定の更新

バックエンドの `.env` で CORS_ORIGINS を更新（後の手順で実施）：
```env
CORS_ORIGINS=["https://pmo-agent-frontend.vercel.app","http://localhost:5173"]
```

## 7. ビルドエラーの対処

### 7.1 TypeScript エラー

```bash
# 型チェックの実行
cd packages/frontend
npx tsc --noEmit

# エラーがある場合は修正
```

### 7.2 依存関係エラー

```bash
# 依存関係の再インストール
rm -rf node_modules pnpm-lock.yaml
pnpm install

# ローカルビルドテスト
pnpm build
```

### 7.3 環境変数エラー

```javascript
// src/config/env.ts
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  wsUrl: import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:8000',
  mockMode: import.meta.env.VITE_MOCK_MODE === 'true',
  // 必須環境変数のチェック
  get isValid() {
    return Boolean(this.apiUrl && this.wsUrl)
  }
}

// 起動時チェック
if (!config.isValid) {
  console.error('Missing required environment variables')
}
```

## 8. パフォーマンス最適化

### 8.1 画像最適化

```bash
# 画像最適化パッケージのインストール
pnpm add -D @squoosh/lib

# vite.config.ts に追加
import { squooshPlugin } from 'vite-plugin-squoosh'

export default defineConfig({
  plugins: [
    react(),
    squooshPlugin({
      // WebP変換設定
      webp: {},
      // AVIF変換設定  
      avif: {}
    })
  ]
})
```

### 8.2 バンドルサイズ分析

```bash
# 分析ツールのインストール
pnpm add -D rollup-plugin-visualizer

# ビルド時に分析レポート生成
pnpm build
```

## 9. 監視とログ

### 9.1 Vercel Analytics の有効化

1. Vercel ダッシュボード → Project → Analytics
2. 「Enable Analytics」をクリック
3. Web Vitals、Page Views、Unique Visitors が記録される

### 9.2 エラー監視（Sentry連携）

```bash
# Sentry SDK のインストール
pnpm add @sentry/react @sentry/vite-plugin
```

```typescript
// src/main.tsx
import * as Sentry from "@sentry/react"

if (import.meta.env.PROD) {
  Sentry.init({
    dsn: "YOUR_SENTRY_DSN",
    environment: "production"
  })
}
```

## 10. 自動デプロイの設定

### 10.1 Git Hooks

Vercel は自動的に以下を実行：
- `main` ブランチへの push → 本番デプロイ
- PR作成 → プレビューデプロイ

### 10.2 デプロイ通知

1. Project Settings → Git
2. 「Deploy Hooks」でWebhookを設定
3. Slack/Discord通知の設定

## 11. 動作確認

### 11.1 基本機能チェック

デプロイ完了後、以下を確認：

```bash
# ヘルスチェック
curl https://pmo-agent-frontend.vercel.app

# ページの読み込み確認
curl -I https://pmo-agent-frontend.vercel.app
```

確認項目：
- [ ] ページが正常に表示される
- [ ] ログイン画面が表示される
- [ ] APIへの接続エラーが表示される（バックエンド未デプロイのため）
- [ ] コンソールエラーが環境変数関連のみ

### 11.2 パフォーマンス確認

1. [PageSpeed Insights](https://pagespeed.web.dev/) でテスト
2. [Lighthouse](https://lighthouse-dot-webdotdevsite.appspot.com/) でスコア確認

目標値：
- Performance: 90+
- Accessibility: 95+
- Best Practices: 90+
- SEO: 80+

## 12. トラブルシューティング

### ビルド失敗

```bash
# ローカルでビルドテスト
cd packages/frontend
pnpm build

# エラー詳細の確認
vercel logs
```

### 環境変数が効かない

```bash
# Vercel プロジェクトの環境変数確認
vercel env ls

# 再デプロイ
vercel --prod --force
```

### ドメインアクセスエラー

```bash
# DNS設定確認
nslookup pmo-agent-frontend.vercel.app
dig pmo-agent-frontend.vercel.app
```

## 13. 次のステップ

フロントエンドのデプロイが完了したら：

1. **[バックエンドデプロイ](./07-backend-deployment-railway.md)** - Railway でのAPI デプロイ
2. **[データベース設定](./08-database-setup-supabase.md)** - Supabase での DB 構築
3. **[統合テスト](./09-production-testing.md)** - 全体の動作確認

## 14. コスト管理

### Vercel 無料枠
- **帯域幅**: 100GB/月
- **ビルド時間**: 6,000分/月  
- **プロジェクト数**: 無制限
- **チームメンバー**: 無制限

### 監視方法
1. Vercel ダッシュボード → Usage
2. 帯域幅使用量を定期的に確認
3. 90% 到達時にアラート設定

---

**所要時間**: 約30分
**前提条件**: GitHub アカウント、ドメイン（オプション）
**次の手順**: [バックエンドデプロイ](./07-backend-deployment-railway.md)