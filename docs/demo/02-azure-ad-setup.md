# Microsoft Azure AD 設定手順（Outlook連携用）

## 1. Azure アカウントの準備

### 1.1 Microsoft アカウントの作成（既存の場合はスキップ）

1. [Microsoft アカウント作成ページ](https://account.microsoft.com/account) にアクセス
2. 「Microsoft アカウントを作成」をクリック
3. 以下のいずれかを選択：
   - 新しいメールアドレスを取得
   - 既存のメールアドレスを使用
4. パスワードを設定
5. 本人確認（メールまたはSMS）

### 1.2 Azure Portal へのアクセス

1. [Azure Portal](https://portal.azure.com/) にアクセス
2. Microsoft アカウントでサインイン
3. 初回アクセス時は無料アカウントの作成画面が表示される
   - 「無料で開始」をクリック
   - クレジットカード情報入力（課金はされません）

## 2. Azure AD アプリケーションの登録

### 2.1 Azure Active Directory へ移動

1. Azure Portal のホーム画面
2. 左上のメニューボタン（☰）をクリック
3. 「Azure Active Directory」を選択

   または検索バーに「Azure Active Directory」と入力

### 2.2 アプリの登録

1. 左サイドメニューから「アプリの登録」を選択
   ```
   Azure Active Directory
   ├── 概要
   ├── ユーザー
   ├── グループ
   ├── アプリの登録  ← これを選択
   └── ...
   ```

2. 「+ 新規登録」ボタンをクリック

### 2.3 アプリケーション情報の入力

#### 名前
```
PMO Agent
```

#### サポートされているアカウントの種類

個人利用の場合：
```
✓ 任意の組織ディレクトリ内のアカウント (任意の Azure AD ディレクトリ - マルチテナント) と個人の Microsoft アカウント (Skype、Xbox など)
```

組織利用の場合：
```
✓ この組織ディレクトリのみに含まれるアカウント (単一テナント)
```

#### リダイレクト URI

1. プラットフォーム: 「Web」を選択
2. URI: 
   ```
   http://localhost:8000/api/v1/auth/callback/microsoft
   ```

3. 「登録」ボタンをクリック

## 3. アプリケーション設定の取得

### 3.1 アプリケーション（クライアント）ID の取得

登録完了後、概要ページに表示される：

```
アプリケーション (クライアント) ID
12345678-1234-1234-1234-123456789abc
```

この値をコピーして保存

### 3.2 ディレクトリ（テナント）ID の取得

同じく概要ページに表示される：

```
ディレクトリ (テナント) ID
87654321-4321-4321-4321-cba987654321
```

この値をコピーして保存（マルチテナントの場合は `common` を使用）

## 4. クライアントシークレットの作成

### 4.1 証明書とシークレット画面へ移動

1. 左サイドメニューから「証明書とシークレット」を選択
2. 「クライアント シークレット」タブを確認（デフォルト）

### 4.2 新しいクライアントシークレットの作成

1. 「+ 新しいクライアント シークレット」をクリック

2. 説明を入力：
   ```
   PMO Agent Client Secret
   ```

3. 有効期限を選択：
   - 推奨: 24か月
   - テスト用: 6か月でも可

4. 「追加」をクリック

### 4.3 シークレット値のコピー

⚠️ **重要**: シークレットの値は一度しか表示されません！

1. 「値」列に表示される文字列をコピー
   ```
   ~8Q8~.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

2. 安全な場所に保存

## 5. API のアクセス許可設定

### 5.1 API のアクセス許可画面へ移動

左サイドメニューから「API のアクセス許可」を選択

### 5.2 アクセス許可の追加

1. 「+ アクセス許可の追加」をクリック

2. 「Microsoft API」タブ → 「Microsoft Graph」を選択

3. 「委任されたアクセス許可」を選択

### 5.3 必要な権限の選択

以下の権限を検索して追加：

#### メール関連（必須）
- ✅ `Mail.Read` - ユーザーのメールを読み取る
- ✅ `Mail.ReadWrite` - ユーザーのメールの読み取りと書き込み

#### ユーザー情報（必須）
- ✅ `User.Read` - サインインとユーザープロファイルの読み取り

#### オフラインアクセス（必須）
- ✅ `offline_access` - ユーザーデータへの継続的なアクセス

#### オプション
- ✅ `Mail.Send` - ユーザーとしてメールを送信
- ✅ `Calendars.Read` - カレンダーの読み取り（将来の拡張用）

4. 「アクセス許可の追加」をクリック

### 5.4 権限の確認

追加された権限が一覧に表示されることを確認：

```
API/アクセス許可の名前    種類    説明                           状態
User.Read                委任    サインインとプロファイルの読み取り   ✓ 付与済み
Mail.Read                委任    ユーザーのメールを読み取る          ✓ 付与済み
Mail.ReadWrite           委任    メールの読み取りと書き込み          ✓ 付与済み
offline_access           委任    データへの継続的なアクセス          ✓ 付与済み
```

### 5.5 管理者の同意（組織アカウントの場合）

組織のテナントの場合、管理者の同意が必要な場合があります：

1. 「[組織名] に管理者の同意を与えます」ボタンをクリック
2. 確認ダイアログで「はい」を選択

## 6. 認証エンドポイントの確認

### 6.1 エンドポイント画面へ移動

概要ページで「エンドポイント」をクリック

### 6.2 使用するエンドポイント

以下のURLを確認（自動的に構成されます）：

#### OAuth 2.0 承認エンドポイント (v2)
```
https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/authorize
```

#### OAuth 2.0 トークン エンドポイント (v2)
```
https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token
```

## 7. プロジェクトへの設定

### 7.1 取得した値の整理

| 項目 | 値 | 環境変数名 |
|------|-----|-----------|
| アプリケーション ID | 12345678-1234-... | MICROSOFT_CLIENT_ID |
| クライアントシークレット | ~8Q8~.xxxxx... | MICROSOFT_CLIENT_SECRET |
| テナント ID | common または実際のID | MICROSOFT_TENANT_ID |

### 7.2 .env ファイルの編集

**📁 ファイルの場所**: `pmo-agent/packages/backend/.env`

```bash
cd pmo-agent/packages/backend
nano .env  # またはお好みのエディタ
```

**📝 編集するファイル**: `pmo-agent/packages/backend/.env`

以下の設定を追加（各値は Azure Portal から取得した値に置き換えてください）：

```env
# Microsoft/Outlook 設定
OUTLOOK_ENABLED=true
MICROSOFT_CLIENT_ID=12345678-1234-1234-1234-123456789abc  # ← 手順3.1で取得したアプリケーションID
MICROSOFT_CLIENT_SECRET=~8Q8~.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # ← 手順4.3で取得したシークレット値
MICROSOFT_TENANT_ID=common  # ← マルチテナントの場合は "common"
# MICROSOFT_TENANT_ID=87654321-4321-4321-4321-cba987654321  # ← シングルテナントの場合は手順3.2のテナントID
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback/microsoft
MICROSOFT_SCOPES=User.Read Mail.Read Mail.ReadWrite offline_access

# Graph API設定
GRAPH_API_BASE_URL=https://graph.microsoft.com/v1.0
GRAPH_API_TIMEOUT=30
# メール処理設定（現在は個別処理だが、将来のバッチ処理用）
# OUTLOOK_BATCH_SIZE=20
```

⚠️ **重要**: 
- 各IDとシークレットは、Azure Portal で取得した実際の値に置き換えてください
- シークレット値は一度しか表示されないため、必ず保存してください

## 8. 動作確認

### 8.1 認証URLの生成テスト

Python スクリプトで確認：

```python
# test_azure_auth.py
import os
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

# 設定値の確認
client_id = os.getenv("MICROSOFT_CLIENT_ID")
redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI")
tenant_id = os.getenv("MICROSOFT_TENANT_ID")
scopes = os.getenv("MICROSOFT_SCOPES")

if not all([client_id, redirect_uri, tenant_id]):
    print("❌ 環境変数が設定されていません")
    exit(1)

# 認証URLの生成
params = {
    "client_id": client_id,
    "response_type": "code",
    "redirect_uri": redirect_uri,
    "scope": scopes,
    "response_mode": "query"
}

auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"
full_url = f"{auth_url}?{urlencode(params)}"

print("✅ 認証URL生成成功!")
print(f"URL: {full_url[:100]}...")
```

### 8.2 実行

```bash
python test_azure_auth.py
```

## 9. トラブルシューティング

### エラー: AADSTS50011 (リダイレクトURIが一致しない)

**エラーメッセージ**:
```
The reply URL specified in the request does not match the reply URLs configured for the application
```

**解決策**:
1. Azure Portal でアプリの登録を開く
2. 「認証」→「Web」セクション
3. リダイレクトURIが正確に一致することを確認
4. 末尾のスラッシュ（/）の有無も確認

### エラー: AADSTS700016 (アプリケーションが見つからない)

**原因**: クライアントIDまたはテナントIDが間違っている

**解決策**:
1. Azure Portal で正しい値を再確認
2. コピー時の余分な空白を削除
3. テナントIDは `common` または実際のGUIDを使用

### エラー: AADSTS7000215 (無効なクライアントシークレット)

**原因**: シークレットの有効期限切れまたは値が間違っている

**解決策**:
1. 新しいクライアントシークレットを作成
2. 古いシークレットを削除
3. .env ファイルを更新

### 権限エラー

**症状**: メールの読み取りができない

**解決策**:
1. API のアクセス許可を再確認
2. 必要に応じて管理者の同意を取得
3. トークンをリフレッシュ

## 10. セキュリティのベストプラクティス

### 10.1 クライアントシークレットの管理

- ソースコードにハードコーディングしない
- 定期的にローテーション（6ヶ月ごと）
- 本番環境では Azure Key Vault を使用

### 10.2 権限の最小化

- 必要最小限の権限のみ要求
- `Mail.ReadWrite.All` などの広範な権限は避ける
- 定期的に使用状況を監査

### 10.3 リダイレクトURIの制限

- 本番環境では HTTPS を必須に
- ワイルドカードは使用しない
- 不要なURIは削除

## 11. 本番環境への移行

### 11.1 リダイレクトURIの追加

本番URLを追加：
```
https://your-domain.com/api/v1/auth/callback/microsoft
```

### 11.2 環境ごとの設定

```env
# 開発環境
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback/microsoft

# 本番環境
MICROSOFT_REDIRECT_URI=https://api.pmo-agent.com/api/v1/auth/callback/microsoft
```

## 12. 次のステップ

Azure AD の設定が完了したら、以下のドキュメントに進んでください：

1. [環境構築手順](./03-environment-setup.md) - アプリケーションセットアップ
2. [動作確認手順](./04-testing-guide.md) - Outlook連携のテスト
3. [トラブルシューティング](./05-troubleshooting.md) - 問題解決ガイド

## 13. 参考リンク

- [Microsoft Graph Documentation](https://docs.microsoft.com/graph/)
- [Azure AD アプリ登録](https://docs.microsoft.com/azure/active-directory/develop/)
- [OAuth 2.0 フロー](https://docs.microsoft.com/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [Graph Explorer](https://developer.microsoft.com/graph/graph-explorer) - API テストツール