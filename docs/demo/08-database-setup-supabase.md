# データベース Supabase セットアップ手順（オプション）

> **注意**: Railway は PostgreSQL を内蔵しているため、この手順は追加のデータベース機能（リアルタイム同期、ファイルストレージ等）が必要な場合のみ実施してください。

## 1. Supabase vs Railway PostgreSQL 比較

| 機能 | Railway PostgreSQL | Supabase |
|------|-------------------|----------|
| **基本DB** | ✅ 無料で500時間 | ✅ 無料で無制限 |
| **容量** | 1GB | 500MB |
| **リアルタイム** | ❌ | ✅ |
| **認証** | 手動実装 | ✅ 内蔵 |
| **ファイルストレージ** | ❌ | ✅ 1GB |
| **API自動生成** | ❌ | ✅ |

## 2. 推奨パターン

### パターン A: Railway PostgreSQL のみ（推奨）
- シンプルな構成
- 無料枠で十分
- FastAPI で認証実装

### パターン B: Supabase併用
- ファイルアップロード機能が必要
- リアルタイム通知が必要
- 複雑な認証が必要

## 3. Supabase アカウント作成

### 3.1 アカウント登録

1. [Supabase](https://supabase.com/) にアクセス
2. 「Start your project」をクリック
3. GitHub アカウントで登録：
   ```
   Continue with GitHub
   ```

### 3.2 新しいプロジェクト作成

1. 「New Project」をクリック
2. 以下を入力：
   ```
   Name: pmo-agent-db
   Database Password: [強力なパスワード]
   Region: Northeast Asia (Tokyo)
   Pricing Plan: Free
   ```
3. 「Create new project」をクリック

## 4. Supabase プロジェクト設定

### 4.1 データベース情報の取得

Supabase ダッシュボード → Settings → Database：

```
Host: db.xxx.supabase.co
Port: 5432
Database name: postgres
Username: postgres
Password: [設定したパスワード]
```

### 4.2 API キーの取得

Settings → API：

```
Project URL: https://xxx.supabase.co
anon public: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4.3 接続URLの生成

```
postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
```

## 5. Supabase での認証設定

### 5.1 認証プロバイダーの設定

Authentication → Settings → Auth Providers：

1. **Email** を有効化（デフォルト）
2. **Microsoft** を有効化：
   ```
   Client ID: [Azure ADのクライアントID]
   Client Secret: [Azure ADのシークレット]
   ```
3. **Redirect URLs** を設定：
   ```
   https://pmo-agent-frontend.vercel.app/auth/callback
   https://xxx.supabase.co/auth/v1/callback
   ```

### 5.2 RLS（Row Level Security）の設定

SQL Editor で実行：

```sql
-- ユーザーテーブルのRLS有効化
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- タスクテーブルの作成とRLS
CREATE TABLE IF NOT EXISTS public.tasks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'todo',
    priority TEXT DEFAULT 'medium',
    due_date TIMESTAMP WITH TIME ZONE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;

-- タスクアクセスポリシー
CREATE POLICY "Users can view own tasks" ON public.tasks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own tasks" ON public.tasks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own tasks" ON public.tasks
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own tasks" ON public.tasks
    FOR DELETE USING (auth.uid() = user_id);
```

## 6. FastAPI との統合

### 6.1 Supabase Python クライアントのインストール

```bash
cd packages/backend
pip install supabase
```

### 6.2 Supabase 設定の追加

**📁 ファイルの場所**: `packages/backend/app/core/supabase.py`

```python
import os
from supabase import create_client, Client
from app.core.config import settings

supabase_url = settings.SUPABASE_URL
supabase_key = settings.SUPABASE_ANON_KEY

supabase: Client = create_client(supabase_url, supabase_key)

async def get_supabase_client() -> Client:
    """Supabase クライアントの取得"""
    return supabase
```

### 6.3 環境変数の追加

Railway の環境変数に追加：

```env
# Supabase 設定
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# データベース設定（Supabaseを使用する場合）
DATABASE_URL=postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
```

## 7. ファイルストレージの設定

### 7.1 ストレージバケットの作成

Supabase ダッシュボード → Storage：

1. 「New Bucket」をクリック
2. 設定：
   ```
   Name: task-attachments
   Public bucket: false
   File size limit: 5MB
   Allowed file types: image/*, application/pdf, text/*
   ```

### 7.2 ストレージポリシーの設定

```sql
-- ファイルアクセスポリシー
CREATE POLICY "Users can upload own files" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'task-attachments' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can view own files" ON storage.objects
    FOR SELECT USING (bucket_id = 'task-attachments' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete own files" ON storage.objects
    FOR DELETE USING (bucket_id = 'task-attachments' AND auth.uid()::text = (storage.foldername(name))[1]);
```

### 7.3 ファイルアップロード API の追加

**📁 ファイルの場所**: `packages/backend/app/api/v1/endpoints/files.py`

```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.core.supabase import get_supabase_client
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """ファイルアップロード"""
    
    # ファイルサイズチェック（5MB）
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    
    # ファイル名の生成
    file_path = f"{current_user.id}/{file.filename}"
    
    try:
        # Supabase Storage にアップロード
        response = supabase.storage.from_("task-attachments").upload(
            path=file_path,
            file=await file.read(),
            file_options={"content-type": file.content_type}
        )
        
        if response.get("error"):
            raise HTTPException(status_code=400, detail=response["error"]["message"])
        
        # 公開URLの取得
        public_url = supabase.storage.from_("task-attachments").get_public_url(file_path)
        
        return {
            "filename": file.filename,
            "file_path": file_path,
            "public_url": public_url,
            "size": file.size,
            "content_type": file.content_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
```

## 8. リアルタイム機能の設定

### 8.1 リアルタイム購読の有効化

Supabase ダッシュボード → Database → Replication：

1. 「public.tasks」テーブルを選択
2. 「Enable replication」をクリック

### 8.2 フロントエンドでのリアルタイム実装

**📁 ファイルの場所**: `packages/frontend/src/hooks/useRealtimeTasks.ts`

```typescript
import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'
import { Task } from '../types/task'

const supabase = createClient(
  process.env.VITE_SUPABASE_URL!,
  process.env.VITE_SUPABASE_ANON_KEY!
)

export function useRealtimeTasks() {
  const [tasks, setTasks] = useState<Task[]>([])

  useEffect(() => {
    // 初期データの取得
    const fetchTasks = async () => {
      const { data } = await supabase
        .from('tasks')
        .select('*')
        .order('created_at', { ascending: false })
      
      if (data) setTasks(data)
    }

    // リアルタイム購読
    const subscription = supabase
      .channel('tasks-channel')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'tasks'
        },
        (payload) => {
          const { eventType, new: newRecord, old: oldRecord } = payload

          setTasks(prev => {
            switch (eventType) {
              case 'INSERT':
                return [newRecord as Task, ...prev]
              case 'UPDATE':
                return prev.map(task => 
                  task.id === newRecord.id ? newRecord as Task : task
                )
              case 'DELETE':
                return prev.filter(task => task.id !== oldRecord.id)
              default:
                return prev
            }
          })
        }
      )
      .subscribe()

    fetchTasks()

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  return tasks
}
```

## 9. バックアップとリストア

### 9.1 自動バックアップの設定

Supabase では自動的にバックアップが作成されます：
- **Point-in-time Recovery**: 7日間（無料プラン）
- **Daily Backups**: 7日間保持

### 9.2 手動バックアップ

```bash
# pg_dump を使用したバックアップ
pg_dump "postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres" > backup.sql

# 特定テーブルのみ
pg_dump -t public.tasks "postgresql://..." > tasks_backup.sql
```

### 9.3 リストア

```bash
# 全データベースの復元
psql "postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres" < backup.sql

# 特定テーブルの復元
psql "postgresql://..." < tasks_backup.sql
```

## 10. 監視とパフォーマンス

### 10.1 Supabase ダッシュボードでの監視

Reports タブで確認できる項目：
- Database size
- API requests
- Realtime connections
- Storage usage

### 10.2 クエリパフォーマンスの最適化

```sql
-- インデックスの作成
CREATE INDEX idx_tasks_user_id ON public.tasks(user_id);
CREATE INDEX idx_tasks_status ON public.tasks(status);
CREATE INDEX idx_tasks_due_date ON public.tasks(due_date);

-- 複合インデックス
CREATE INDEX idx_tasks_user_status ON public.tasks(user_id, status);
```

## 11. セキュリティ設定

### 11.1 API キーの保護

```env
# 本番環境では service_role キーを使用
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 11.2 CORS の設定

Supabase Settings → API → CORS Origins：
```
https://pmo-agent-frontend.vercel.app
http://localhost:5173
```

### 11.3 RLS の詳細設定

```sql
-- より詳細なアクセス制御
CREATE POLICY "Admins can view all tasks" ON public.tasks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM auth.users 
            WHERE auth.users.id = auth.uid() 
            AND auth.users.raw_app_meta_data->>'role' = 'admin'
        )
    );
```

## 12. コスト管理

### 12.1 Supabase 無料枠

- **Database**: 500MB
- **Storage**: 1GB
- **Bandwidth**: 2GB
- **API requests**: 50,000/月
- **Realtime**: 200 concurrent connections

### 12.2 使用量の監視

Supabase ダッシュボード → Usage で確認：
- Database size: 500MB まで
- API requests: 50,000/月 まで
- Storage: 1GB まで

## 13. Migration from Railway PostgreSQL

既に Railway PostgreSQL を使用している場合：

### 13.1 データのエクスポート

```bash
# Railway からデータエクスポート
railway shell
pg_dump $DATABASE_URL > railway_backup.sql
```

### 13.2 Supabase へのインポート

```bash
# Supabase にインポート
psql "postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres" < railway_backup.sql
```

### 13.3 接続先の切り替え

Railway の環境変数を更新：
```env
DATABASE_URL=postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
```

## 14. トラブルシューティング

### 14.1 接続エラー

```bash
# 接続テスト
psql "postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres" -c "SELECT version();"
```

### 14.2 RLS エラー

```sql
-- RLS 無効化（デバッグ用）
ALTER TABLE public.tasks DISABLE ROW LEVEL SECURITY;

-- ポリシーの確認
SELECT * FROM pg_policies WHERE tablename = 'tasks';
```

### 14.3 API レート制限

Supabase Settings → API → Rate limiting：
- 適切なレート制限を設定
- 必要に応じて有料プランに移行

## 15. 次のステップ

Supabase の設定が完了したら：

1. **[統合テスト](./09-production-testing.md)** - 全体システムの動作確認
2. **[Outlook連携テスト](./10-outlook-integration-test.md)** - Microsoft 連携の検証
3. **[監視設定](./11-monitoring-setup.md)** - 本番運用の監視体制

---

**所要時間**: 約30分（Supabase使用の場合）
**推奨**: Railway PostgreSQL で十分な場合はスキップ
**次の手順**: [統合テスト](./09-production-testing.md)