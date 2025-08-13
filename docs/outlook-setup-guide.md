# Outlook (Microsoft 365) 連携設定ガイド

## 前提条件

- Microsoft 365 アカウント（個人または組織）
- Azure Active Directory へのアクセス権限

## 1. Azure AD アプリケーションの登録

### 1.1 Azure Portal へアクセス

1. [Azure Portal](https://portal.azure.com/) にログイン
2. 「Azure Active Directory」を選択
3. 左メニューから「アプリの登録」を選択
4. 「新規登録」をクリック

### 1.2 アプリケーション情報の入力

```
名前: PMO Agent
サポートされているアカウントの種類: 
  - 個人用: 「任意の組織ディレクトリ内のアカウントと個人用 Microsoft アカウント」
  - 組織用: 「この組織ディレクトリのみ」
リダイレクトURI:
  - プラットフォーム: Web
  - URI: http://localhost:8000/api/v1/auth/callback/microsoft
```

### 1.3 アプリケーションの設定

登録完了後：

1. **アプリケーション（クライアント）ID** をコピー
2. 「証明書とシークレット」→「新しいクライアント シークレット」
3. シークレットの値をコピー（一度しか表示されないので注意）

### 1.4 API のアクセス許可

「APIのアクセス許可」→「アクセス許可の追加」→「Microsoft Graph」

必要な権限（委任されたアクセス許可）：
- `Mail.Read` - メールの読み取り
- `Mail.ReadWrite` - メールの読み書き（タスク更新用）
- `Mail.Send` - メールの送信（オプション）
- `User.Read` - ユーザープロファイルの読み取り
- `offline_access` - 更新トークンの取得

## 2. PMO Agent の設定

### 2.1 バックエンドの環境変数

`packages/backend/.env` を編集：

```env
# === Microsoft/Outlook 設定 ===
OUTLOOK_ENABLED=true
MICROSOFT_CLIENT_ID=your-application-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=common  # または組織のテナントID
MICROSOFT_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback/microsoft

# OAuth スコープ
MICROSOFT_SCOPES=User.Read Mail.Read Mail.ReadWrite offline_access

# Graph API設定
GRAPH_API_BASE_URL=https://graph.microsoft.com/v1.0
GRAPH_API_TIMEOUT=30
```

### 2.2 OAuth認証フローの実装確認

`packages/backend/app/services/oauth_service.py` を確認：

```python
class OAuthService:
    """OAuth authentication service for email providers"""
    
    async def get_microsoft_auth_url(self, state: str) -> str:
        """Generate Microsoft OAuth URL"""
        params = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
            "scope": settings.MICROSOFT_SCOPES,
            "state": state,
            "response_mode": "query"
        }
        
        auth_url = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
        return f"{auth_url}?{urlencode(params)}"
    
    async def exchange_microsoft_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token",
                data={
                    "client_id": settings.MICROSOFT_CLIENT_ID,
                    "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )
            response.raise_for_status()
            return response.json()
```

## 3. メール同期の動作確認

### 3.1 アプリケーションの起動

```bash
# バックエンド
cd packages/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# フロントエンド
cd packages/frontend
pnpm dev
```

### 3.2 Outlook連携の手順

1. ブラウザで `http://localhost:5173` にアクセス
2. ログイン後、「設定」画面を開く
3. 「メール連携」セクションの「Microsoft 365」で「連携する」をクリック
4. Microsoftアカウントでログイン
5. 要求された権限を承認
6. 自動的にPMO Agentに戻る

### 3.3 メール同期のテスト

1. ダッシュボードで「メール同期」ボタンをクリック
2. 同期状況の確認（進行状況が表示される）
3. 同期完了後、タスク一覧を確認

## 4. Outlook特有の機能

### 4.1 ConversationId によるスレッド管理

Outlookでは `conversationId` を使用してスレッドを識別：

```python
def _parse_outlook_message(self, msg_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Outlook message format"""
    
    # Outlookの conversationId を優先的に使用
    conversation_id = msg_data.get("conversationId", "")
    
    # スレッドIDとして使用
    thread_id = conversation_id if conversation_id else self._generate_thread_id(subject)
    
    return {
        "id": msg_data["id"],
        "thread_id": thread_id,
        "conversation_id": conversation_id,
        # ...
    }
```

### 4.2 Delta Query による効率的な同期

初回同期後は Delta Query で差分のみ取得：

```python
async def sync_outlook(self, access_token: str, last_sync_token: Optional[str] = None):
    """Sync emails from Outlook using delta query"""
    
    if last_sync_token:
        # 前回の deltaLink を使用
        url = last_sync_token
    else:
        # 初回は全件取得 + delta query
        url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages/delta"
        url += "?$select=id,subject,from,toRecipients,body,receivedDateTime,conversationId"
```

### 4.3 重要なメールのフィルタリング

```python
# 重要度の高いメールのみ同期
url += "&$filter=importance eq 'high' or isRead eq false"

# 特定の期間のメールのみ
from_date = (datetime.now() - timedelta(days=7)).isoformat()
url += f"&$filter=receivedDateTime ge {from_date}"
```

## 5. トラブルシューティング

### 問題: 認証エラー (AADSTS50011)

**原因**: リダイレクトURIが一致しない

**解決策**: 
- Azure ADアプリの設定で正確なリダイレクトURIを確認
- HTTPSが必要な場合は ngrok を使用

```bash
# ngrokでローカルをHTTPS化
ngrok http 8000
# 表示されたURLをリダイレクトURIとして登録
```

### 問題: 権限不足エラー

**原因**: 必要なスコープが付与されていない

**解決策**:
1. Azure AD で必要な権限を追加
2. ユーザーに再度承認を求める（既存トークンを削除）

```python
# トークンのリフレッシュを強制
await oauth_service.refresh_token(
    refresh_token=account.refresh_token,
    provider="microsoft",
    force_refresh=True
)
```

### 問題: レート制限エラー (429)

**原因**: Microsoft Graph API のレート制限

**解決策**:
```python
# リトライロジックの実装
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def call_graph_api(url: str, headers: Dict):
    # API呼び出し
```

## 6. 検証シナリオ

### シナリオ1: 基本的なメール同期

1. テストメールを Outlook に送信
   ```
   件名: [タスク] プロジェクト提案書の作成
   本文: 2月15日までに提案書を作成してください。
   ```

2. メール同期を実行

3. 期待される結果：
   - タスクが自動作成される
   - 期限が2月15日に設定される
   - 優先度が「中」に設定される

### シナリオ2: スレッドの処理

1. 最初のメール：
   ```
   件名: プロジェクトミーティングについて
   本文: 来週のミーティング日程を調整したいです。
   ```

2. 返信メール：
   ```
   件名: Re: プロジェクトミーティングについて
   本文: 火曜日の14時はいかがでしょうか？
   ```

3. 期待される結果：
   - 1つのタスクとして管理される
   - メール履歴に両方のメールが表示される
   - タスクの更新日時が最新メールの日時になる

### シナリオ3: 重要度による優先度設定

1. Outlookで重要度「高」のメールを送信
2. メール同期を実行
3. 期待される結果：
   - タスクの優先度が「高」に設定される

## 7. パフォーマンス最適化

### バッチサイズの調整

```python
# 一度に取得するメール数を制限
OUTLOOK_BATCH_SIZE = 20  # デフォルト: 50
```

### 選択的なフィールド取得

```python
# 必要なフィールドのみ取得してトラフィック削減
select_fields = "id,subject,from,conversationId,receivedDateTime,importance"
url += f"&$select={select_fields}"
```

### キャッシュの活用

```python
# 同じconversationIdのメールはキャッシュから取得
@cache.memoize(timeout=3600)
async def get_conversation_emails(conversation_id: str):
    # Graph APIでconversation内の全メールを取得
```

## 8. セキュリティのベストプラクティス

1. **最小権限の原則**
   - 必要最小限のスコープのみ要求
   - Mail.ReadWrite より Mail.Read を優先

2. **トークンの安全な保管**
   - リフレッシュトークンは暗号化して保存
   - アクセストークンはメモリのみ

3. **監査ログ**
   - すべてのAPI呼び出しをログに記録
   - 異常なアクセスパターンを検知

## 9. コスト管理

Microsoft Graph API は基本的に無料ですが、以下の制限があります：

- **スロットリング制限**: 
  - ユーザーごと: 10,000リクエスト/10分
  - アプリごと: 全テナントで 150,000リクエスト/10分

- **推奨事項**:
  - Delta Query を使用して差分のみ取得
  - 必要なフィールドのみ選択
  - バッチリクエストの活用

## 10. 次のステップ

1. **カレンダー連携**: タスクの期限をOutlookカレンダーと同期
2. **Teams連携**: チームでのタスク共有
3. **自動返信**: AIがメールに自動返信する機能