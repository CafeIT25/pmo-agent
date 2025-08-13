# OpenAI API 設定手順

## 1. OpenAI アカウントの作成

### 1.1 アカウント登録

1. [OpenAI Platform](https://platform.openai.com/signup) にアクセス
2. 以下のいずれかの方法でサインアップ：
   - メールアドレスとパスワード
   - Googleアカウント
   - Microsoftアカウント

### 1.2 メール認証

1. 登録メールアドレスに確認メールが届く
2. 「Verify email address」ボタンをクリック
3. ブラウザで確認完了画面が表示される

### 1.3 電話番号認証

1. 電話番号を入力（日本の場合: +81）
2. SMSで6桁の認証コードを受信
3. 認証コードを入力して確認

## 2. APIキーの作成

### 2.1 API Keys ページへアクセス

1. [OpenAI Platform](https://platform.openai.com/) にログイン
2. 左サイドバーまたは右上のメニューから「API keys」を選択
   
   ![API Keys メニュー位置]
   ```
   Dashboard
   ├── Usage
   ├── API keys  ← これを選択
   ├── Organization
   └── Billing
   ```

### 2.2 新しいAPIキーの作成

1. 「Create new secret key」ボタンをクリック

2. キーの名前を設定（オプション）
   ```
   Name: PMO Agent Development
   ```

3. 権限設定（デフォルトで OK）
   - All
   - または Restricted（必要な権限のみ選択）

4. 「Create secret key」をクリック

### 2.3 APIキーの保存

⚠️ **重要**: APIキーは一度しか表示されません！

1. 表示されたAPIキーをコピー
   ```
   sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

2. 安全な場所に保存：
   - パスワードマネージャー
   - 環境変数
   - `.env` ファイル（Git管理外）

3. 「Done」をクリック

## 3. 支払い情報の設定

### 3.1 Billing ページへアクセス

1. 左サイドバーから「Billing」を選択
2. 「Payment methods」タブを開く

### 3.2 クレジットカード情報の入力

1. 「Add payment method」をクリック
2. カード情報を入力：
   - カード番号
   - 有効期限
   - CVV
   - 請求先住所

3. 「Add payment method」で保存

### 3.3 使用制限の設定（推奨）

1. 「Usage limits」タブを開く
2. 月間制限を設定：
   ```
   Monthly budget: $10.00
   ```
3. アラート設定：
   ```
   Email me when usage exceeds: $5.00
   ```

## 4. プロジェクトへの設定

### 4.1 .env ファイルの編集

**📁 ファイルの場所**: `pmo-agent/packages/backend/.env`

```bash
cd pmo-agent/packages/backend
cp .env.example .env
```

### 4.2 APIキーの設定

**📝 編集するファイル**: `pmo-agent/packages/backend/.env`

`.env` ファイルを編集して以下の値を設定：

```env
# OpenAI設定
USE_OPENAI=true
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # ← ここに取得したAPIキーを貼り付け
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.3
```

⚠️ **重要**: 
- `OPENAI_API_KEY=` の後に、手順2.3で取得したAPIキー（`sk-proj-` で始まる文字列）を貼り付けてください
- キーの前後に余分なスペースや引用符を入れないでください

### 4.3 設定値の説明

| 設定項目 | 推奨値 | 説明 |
|---------|--------|------|
| USE_OPENAI | true | OpenAI APIを有効化 |
| OPENAI_API_KEY | sk-proj-xxx... | 取得したAPIキー |
| OPENAI_MODEL | gpt-3.5-turbo | 使用するモデル（コスト重視） |
| OPENAI_MAX_TOKENS | 1000 | 最大出力トークン数 |
| OPENAI_TEMPERATURE | 0.3 | 創造性レベル（0-1） |

## 5. APIキーの動作確認

### 5.1 Pythonスクリプトで確認

```python
# test_openai.py
import os
from openai import OpenAI

# .envから読み込む場合
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Hello, this is a test."}
        ],
        max_tokens=10
    )
    print("✅ API接続成功!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ エラー: {e}")
```

### 5.2 実行

```bash
python test_openai.py
```

期待される出力：
```
✅ API接続成功!
Response: Hello! This test is working correctly.
```

## 6. コスト管理

### 6.1 使用量の確認

1. [Usage ページ](https://platform.openai.com/usage) にアクセス
2. 日別・モデル別の使用量を確認

### 6.2 コスト計算例

GPT-3.5-turbo の料金（2024年1月時点）：
- 入力: $0.0005 / 1K トークン
- 出力: $0.0015 / 1K トークン

月間使用量の目安：
```
1日の処理:
- メール分析: 20件 × 500トークン = 10,000トークン
- タスク生成: 10件 × 300トークン = 3,000トークン
合計: 13,000トークン/日

月間コスト:
- 入力: 13,000 × 30 × $0.0005 = $0.195
- 出力: 13,000 × 30 × $0.0015 = $0.585
合計: 約$0.78/月
```

### 6.3 コスト削減のヒント

1. **モデル選択**
   - GPT-3.5-turbo: 最もコスト効率が良い
   - GPT-4: 高精度だが高コスト（10倍以上）

2. **トークン制限**
   ```env
   OPENAI_MAX_TOKENS=500  # 必要最小限に
   ```

3. **キャッシュ活用**
   ```python
   # 同じ質問は再度APIを呼ばない
   @cache.memoize(timeout=3600)
   def analyze_email(content):
       return openai_api_call(content)
   ```

## 7. トラブルシューティング

### エラー: Invalid API key

**原因**: APIキーが正しくない

**解決策**:
1. APIキーの先頭・末尾の空白を確認
2. `sk-` で始まることを確認
3. 新しいキーを生成

### エラー: Rate limit exceeded

**原因**: API呼び出し制限超過

**解決策**:
```python
# リトライロジックを実装
import time

def call_with_retry(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except RateLimitError:
            time.sleep(2 ** i)  # 指数バックオフ
    raise Exception("Max retries exceeded")
```

### エラー: Insufficient quota

**原因**: クレジットが不足

**解決策**:
1. Billing ページで残高確認
2. 支払い方法を追加
3. 使用制限を確認

## 8. セキュリティのベストプラクティス

### 8.1 APIキーの保護

❌ **やってはいけないこと**:
```python
# ハードコーディング
api_key = "sk-proj-xxxxx"  # 危険！
```

✅ **推奨方法**:
```python
# 環境変数から読み込み
import os
api_key = os.getenv("OPENAI_API_KEY")
```

### 8.2 .gitignore の設定

```gitignore
# 環境変数ファイル
.env
.env.local
.env.*.local

# APIキーを含む可能性のあるファイル
config/secrets.json
*.key
```

### 8.3 APIキーのローテーション

定期的にAPIキーを更新：
1. 新しいキーを生成
2. アプリケーションの設定を更新
3. 古いキーを削除

## 9. 次のステップ

APIキーの設定が完了したら、以下のドキュメントに進んでください：

1. [Microsoft Azure AD 設定](./02-azure-ad-setup.md) - Outlook連携用
2. [環境構築手順](./03-environment-setup.md) - アプリケーション設定
3. [動作確認手順](./04-testing-guide.md) - 機能テスト

## 10. 参考リンク

- [OpenAI Documentation](https://platform.openai.com/docs)
- [API Reference](https://platform.openai.com/docs/api-reference)
- [Pricing](https://openai.com/pricing)
- [Usage Policies](https://openai.com/policies/usage-policies)