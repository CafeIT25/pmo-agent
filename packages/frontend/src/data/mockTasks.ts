/**
 * デモ用のモックタスクデータ
 */

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'todo' | 'progress' | 'done';
  priority: 'high' | 'medium' | 'low';
  created_by: 'ai' | 'user';
  updated_by: 'ai' | 'user';
  email_summary?: string;
  source_email_link?: string;
  due_date?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export const mockTasks: Task[] = [
  {
    id: 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
    title: 'プロジェクト計画書の作成',
    description: 'Q1の新規プロジェクトに関する計画書を作成し、ステークホルダーへ共有する必要があります。',
    status: 'progress',
    priority: 'high',
    created_by: 'user',
    updated_by: 'user',
    due_date: '2024-02-15',
    created_at: '2024-01-10T09:00:00Z',
    updated_at: '2024-01-18T14:30:00Z',
    email_summary: `
プロジェクト計画書について以下の要件が確認されました：

1. エグゼクティブサマリー
2. スコープ定義
3. タイムライン（ガントチャート含む）
4. リソース配分
5. リスク管理計画

関連メール履歴：
- 2024/01/10: 初回要件受領（山田部長より）
- 2024/01/12: スコープ確認会議の議事録
- 2024/01/15: リソース配分の承認連絡
    `,
    source_email_link: 'https://mail.google.com/mail/u/0/#inbox/18d3a4b5c6d7e8f9'
  },
  {
    id: '6ba7b810-9dad-11d1-80b4-00c04fd430c8',
    title: 'API認証機能のバグ修正',
    description: '本番環境でトークンのリフレッシュが正常に動作しない問題が報告されています。緊急度高。',
    status: 'todo',
    priority: 'high',
    created_by: 'ai',
    updated_by: 'ai',
    due_date: '2024-01-25',
    created_at: '2024-01-18T08:00:00Z',
    updated_at: '2024-01-18T16:45:00Z',
    email_summary: `
バグレポート概要：
- 発生環境: 本番環境
- 影響範囲: 全ユーザーの約15%
- 症状: リフレッシュトークンが期限切れ後に更新されない
- 再現手順: 
  1. 30分以上アイドル状態を維持
  2. 操作を再開すると401エラー

調査結果：
- Redis のトークン保存期限設定に問題の可能性
- 非同期処理のタイミング問題も疑われる

関連メール：
- 2024/01/18 08:00: サポートチームからのバグ報告
- 2024/01/18 14:00: 開発チームでの初期調査結果
- 2024/01/18 16:00: 優先度高での対応要請（CTO承認）
    `,
    source_email_link: 'https://mail.google.com/mail/u/0/#inbox/18d3b5c7d8e9fa01'
  },
  {
    id: '6ba7b811-9dad-11d1-80b4-00c04fd430c8',
    title: '月次レポートのレビュー',
    description: '12月度の月次レポートをレビューし、経営会議用の資料として最終化する。',
    status: 'done',
    priority: 'medium',
    created_by: 'ai',
    updated_by: 'user',
    due_date: '2024-01-20',
    created_at: '2024-01-08T10:00:00Z',
    updated_at: '2024-01-19T17:00:00Z',
    completed_at: '2024-01-19T17:00:00Z',
    email_summary: `
月次レポートのレビュー依頼：

含まれる項目：
- 売上実績と予算対比
- 主要KPIの達成状況
- プロジェクト進捗サマリー
- 次月の重点施策

変更履歴：
- v1.0: 初稿作成（財務部）
- v1.1: KPI部分の修正
- v1.2: グラフデザインの更新
- v2.0: 最終版（承認済み）

関連メール：
- 2024/01/08: レビュー依頼受領
- 2024/01/15: 修正要望のフィードバック
- 2024/01/19: 最終承認通知
    `,
    source_email_link: 'https://mail.google.com/mail/u/0/#inbox/18d2c6d8e9fb0112'
  }
];

// タスク詳細用の追加データ
export interface TaskDetail extends Task {
  history?: TaskHistory[];
  comments?: TaskComment[];
  attachments?: TaskAttachment[];
  email_thread?: EmailThread[];
}

export interface EmailThread {
  id: string;
  from: string;
  to: string;
  subject: string;
  body: string;
  date: string;
  type: 'received' | 'sent' | 'reply';
}

export interface TaskHistory {
  id: string;
  action: string;
  timestamp: string;
  user: string;
  details?: string;
}

export interface TaskComment {
  id: string;
  author: string;
  content: string;
  timestamp: string;
}

export interface TaskAttachment {
  id: string;
  name: string;
  size: number;
  type: string;
  url: string;
}

export const getTaskDetail = (taskId: string): TaskDetail | undefined => {
  const task = mockTasks.find(t => t.id === taskId);
  if (!task) return undefined;

  // タスクごとのメールスレッドを設定
  let emailThread: EmailThread[] = [];
  
  if (taskId === 'f47ac10b-58cc-4372-a567-0e02b2c3d479') {
    emailThread = [
      {
        id: 'email-1',
        from: 'yamada@example.com',
        to: 'pm@company.com',
        subject: 'プロジェクト計画書の作成について',
        body: `お疲れ様です。

Q1の新規プロジェクトについて、計画書の作成をお願いします。
以下の項目を含めてください：

1. エグゼクティブサマリー
2. スコープ定義
3. タイムライン（ガントチャート含む）
4. リソース配分
5. リスク管理計画

期限は2月15日でお願いします。`,
        date: '2024-01-10T09:00:00Z',
        type: 'received'
      },
      {
        id: 'email-2',
        from: 'pm@company.com',
        to: 'yamada@example.com',
        subject: 'Re: プロジェクト計画書の作成について',
        body: `承知しました。

計画書の作成に着手します。
スコープ定義について、詳細を確認させていただきたい点があります。
明日の会議で相談させてください。`,
        date: '2024-01-10T14:00:00Z',
        type: 'sent'
      },
      {
        id: 'email-3',
        from: 'yamada@example.com',
        to: 'pm@company.com',
        subject: 'Re: プロジェクト計画書の作成について',
        body: `了解しました。

明日15:00から会議室Aで打ち合わせしましょう。
リソース配分についても、財務部の承認が取れましたので共有します。`,
        date: '2024-01-11T10:00:00Z',
        type: 'reply'
      },
      {
        id: 'email-4',
        from: 'pm@company.com',
        to: 'yamada@example.com',
        subject: 'Re: プロジェクト計画書の作成について',
        body: `本日の打ち合わせありがとうございました。

スコープ定義の部分を更新し、ガントチャートも作成しました。
現在60%程度完成しています。予定通り期限までに完成予定です。`,
        date: '2024-01-15T16:00:00Z',
        type: 'sent'
      }
    ];
  } else if (taskId === '6ba7b810-9dad-11d1-80b4-00c04fd430c8') {
    emailThread = [
      {
        id: 'email-1',
        from: 'support@company.com',
        to: 'dev-team@company.com',
        subject: '【緊急】本番環境でAPI認証エラー',
        body: `開発チーム各位

本番環境で以下の問題が発生しています：

症状：
- リフレッシュトークンが期限切れ後に更新されない
- 影響範囲：全ユーザーの約15%
- エラーコード：401 Unauthorized

再現手順：
1. 30分以上アイドル状態を維持
2. 操作を再開すると401エラー

至急対応をお願いします。`,
        date: '2024-01-18T08:00:00Z',
        type: 'received'
      },
      {
        id: 'email-2',
        from: 'dev-team@company.com',
        to: 'support@company.com',
        subject: 'Re: 【緊急】本番環境でAPI認証エラー',
        body: `調査を開始しました。

初期調査の結果：
- Redis のトークン保存期限設定に問題の可能性
- 非同期処理のタイミング問題も疑われる

現在、詳細なログを確認中です。`,
        date: '2024-01-18T14:00:00Z',
        type: 'sent'
      }
    ];
  } else if (taskId === '6ba7b811-9dad-11d1-80b4-00c04fd430c8') {
    emailThread = [
      {
        id: 'email-1',
        from: 'finance@company.com',
        to: 'pm@company.com',
        subject: '12月度月次レポートのレビュー依頼',
        body: `月次レポートのレビューをお願いします。

含まれる項目：
- 売上実績と予算対比
- 主要KPIの達成状況
- プロジェクト進捗サマリー
- 次月の重点施策

1/20までにフィードバックをお願いします。`,
        date: '2024-01-08T10:00:00Z',
        type: 'received'
      },
      {
        id: 'email-2',
        from: 'pm@company.com',
        to: 'finance@company.com',
        subject: 'Re: 12月度月次レポートのレビュー依頼',
        body: `レポートを確認しました。

修正依頼：
- KPIセクションのグラフを更新してください
- プロジェクトBの進捗を追加してください

その他は問題ありません。`,
        date: '2024-01-15T14:00:00Z',
        type: 'sent'
      },
      {
        id: 'email-3',
        from: 'finance@company.com',
        to: 'pm@company.com',
        subject: 'Re: 12月度月次レポートのレビュー依頼',
        body: `修正が完了しました。

v2.0を添付します。
最終確認をお願いします。`,
        date: '2024-01-19T10:00:00Z',
        type: 'reply'
      },
      {
        id: 'email-4',
        from: 'pm@company.com',
        to: 'finance@company.com',
        subject: 'Re: 12月度月次レポートのレビュー依頼',
        body: `確認完了しました。

v2.0で承認します。
経営会議での発表準備を進めてください。

お疲れ様でした。`,
        date: '2024-01-19T17:00:00Z',
        type: 'sent'
      }
    ];
  }

  const taskDetail: TaskDetail = {
    ...task,
    email_thread: emailThread,
    history: [
      {
        id: '1',
        action: 'created',
        timestamp: task.created_at,
        user: task.created_by === 'ai' ? 'AI Agent' : 'ユーザー',
        details: 'タスクが作成されました'
      },
      {
        id: '2',
        action: 'status_changed',
        timestamp: task.updated_at,
        user: task.updated_by === 'ai' ? 'AI Agent' : 'ユーザー',
        details: `ステータスが「${task.status}」に変更されました`
      }
    ],
    comments: [
      {
        id: '1',
        author: '田中太郎',
        content: 'このタスクについて、追加の要件確認が必要です。',
        timestamp: '2024-01-17T10:00:00Z'
      }
    ],
    attachments: []
  };

  return taskDetail;
};