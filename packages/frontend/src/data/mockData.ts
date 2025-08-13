/**
 * デモ用モックデータ定義
 */

// 使用量ダッシュボード用モックデータ
export const mockUsageStats = {
  year: 2025,
  month: 8,
  user_id: "demo-user-001",
  summary: {
    total_input_tokens: 125000,
    total_output_tokens: 45000,
    total_tokens: 170000,
    total_cost_usd: 0.042500,
    total_cost_jpy: 6.38,
    request_count: 42,
    average_cost_per_request: 0.001012
  },
  model_breakdown: [
    {
      model: "gpt-5-mini",
      input_tokens: 98000,
      output_tokens: 35000,
      cost_usd: 0.032450,
      cost_jpy: 4.87,
      requests: 32
    },
    {
      model: "gpt-5",
      input_tokens: 15000,
      output_tokens: 8000,
      cost_usd: 0.008750,
      cost_jpy: 1.31,
      requests: 6
    },
    {
      model: "gpt-5-nano",
      input_tokens: 12000,
      output_tokens: 2000,
      cost_usd: 0.001300,
      cost_jpy: 0.20,
      requests: 4
    }
  ],
  purpose_breakdown: [
    {
      purpose: "メール分析・タスク生成",
      input_tokens: 75000,
      output_tokens: 28000,
      cost_usd: 0.024750,
      cost_jpy: 3.71,
      requests: 24
    },
    {
      purpose: "タスク調査・提案",
      input_tokens: 35000,
      output_tokens: 12000,
      cost_usd: 0.012500,
      cost_jpy: 1.88,
      requests: 12
    },
    {
      purpose: "AIチャット・質問回答",
      input_tokens: 15000,
      output_tokens: 5000,
      cost_usd: 0.005250,
      cost_jpy: 0.79,
      requests: 6
    }
  ],
  daily_usage: [
    { date: "2025-08-01", cost_usd: 0.002100, cost_jpy: 0.32, tokens: 8500, requests: 2 },
    { date: "2025-08-02", cost_usd: 0.003200, cost_jpy: 0.48, tokens: 12000, requests: 3 },
    { date: "2025-08-03", cost_usd: 0.001800, cost_jpy: 0.27, tokens: 7200, requests: 2 },
    { date: "2025-08-04", cost_usd: 0.004500, cost_jpy: 0.68, tokens: 15000, requests: 4 },
    { date: "2025-08-05", cost_usd: 0.003800, cost_jpy: 0.57, tokens: 13500, requests: 3 },
    { date: "2025-08-06", cost_usd: 0.002700, cost_jpy: 0.41, tokens: 9800, requests: 2 },
    { date: "2025-08-07", cost_usd: 0.005200, cost_jpy: 0.78, tokens: 16200, requests: 4 },
    { date: "2025-08-08", cost_usd: 0.003100, cost_jpy: 0.47, tokens: 11000, requests: 3 },
    { date: "2025-08-09", cost_usd: 0.004300, cost_jpy: 0.65, tokens: 14500, requests: 4 },
    { date: "2025-08-10", cost_usd: 0.002900, cost_jpy: 0.44, tokens: 10800, requests: 2 },
    { date: "2025-08-11", cost_usd: 0.003600, cost_jpy: 0.54, tokens: 12800, requests: 3 },
    { date: "2025-08-12", cost_usd: 0.004100, cost_jpy: 0.62, tokens: 13900, requests: 4 },
    { date: "2025-08-13", cost_usd: 0.001800, cost_jpy: 0.27, tokens: 6000, requests: 1 }
  ]
};

// 最近の使用履歴用モックデータ
export const mockRecentUsage = [
  {
    id: "usage-001",
    model: "gpt-5-mini",
    input_tokens: 2800,
    output_tokens: 1200,
    total_tokens: 4000,
    cost_usd: 0.003100,
    cost_jpy: 0.47,
    purpose: "メール分析・タスク生成",
    verbosity: "low",
    reasoning_effort: "low",
    created_at: "2025-08-13T09:30:00Z"
  },
  {
    id: "usage-002",
    model: "gpt-5-mini",
    input_tokens: 1800,
    output_tokens: 800,
    total_tokens: 2600,
    cost_usd: 0.002050,
    cost_jpy: 0.31,
    purpose: "タスク調査・提案",
    verbosity: "low",
    reasoning_effort: "low",
    created_at: "2025-08-13T08:45:00Z"
  },
  {
    id: "usage-003",
    model: "gpt-5",
    input_tokens: 3500,
    output_tokens: 1800,
    total_tokens: 5300,
    cost_usd: 0.022375,
    cost_jpy: 3.36,
    purpose: "AIチャット・質問回答",
    verbosity: "medium",
    reasoning_effort: "high",
    created_at: "2025-08-12T16:20:00Z"
  },
  {
    id: "usage-004",
    model: "gpt-5-nano",
    input_tokens: 1200,
    output_tokens: 400,
    total_tokens: 1600,
    cost_usd: 0.000220,
    cost_jpy: 0.03,
    purpose: "メール分析・タスク生成",
    verbosity: "low",
    reasoning_effort: "minimal",
    created_at: "2025-08-12T14:10:00Z"
  },
  {
    id: "usage-005",
    model: "gpt-5-mini",
    input_tokens: 2200,
    output_tokens: 950,
    total_tokens: 3150,
    cost_usd: 0.002450,
    cost_jpy: 0.37,
    purpose: "タスク調査・提案",
    verbosity: "low",
    reasoning_effort: "low",
    created_at: "2025-08-12T11:30:00Z"
  },
  {
    id: "usage-006",
    model: "gpt-5-mini",
    input_tokens: 3200,
    output_tokens: 1400,
    total_tokens: 4600,
    cost_usd: 0.003600,
    cost_jpy: 0.54,
    purpose: "メール分析・タスク生成",
    verbosity: "low",
    reasoning_effort: "low",
    created_at: "2025-08-11T15:45:00Z"
  }
];

// タスク一覧用モックデータ
export const mockTasks = [
  {
    id: "task-001",
    title: "新機能のUI設計書作成",
    description: "ユーザーダッシュボードの新機能に関するUI設計書を作成する必要があります。",
    status: "progress",
    priority: "high",
    created_by: "ai",
    created_at: "2025-08-10T09:00:00Z",
    updated_at: "2025-08-12T14:30:00Z",
    email_summary: "関連メール 3 件\n\n1. 2025-08-10 - 田中部長\n   新機能のUI設計について\n2. 2025-08-11 - デザインチーム\n   デザインガイドライン共有\n3. 2025-08-12 - 開発チーム\n   技術的制約について"
  },
  {
    id: "task-002",
    title: "データベース最適化の検討",
    description: "現在のクエリパフォーマンスが低下しているため、インデックス追加や正規化の見直しが必要です。",
    status: "todo",
    priority: "medium",
    created_by: "ai",
    created_at: "2025-08-11T10:30:00Z",
    updated_at: "2025-08-11T10:30:00Z",
    email_summary: "関連メール 2 件\n\n1. 2025-08-11 - システム管理者\n   パフォーマンス問題の報告\n2. 2025-08-11 - DBA\n   最適化案の提案"
  },
  {
    id: "task-003",
    title: "セキュリティ監査対応",
    description: "第3者機関によるセキュリティ監査の指摘事項に対する対応を実施する。",
    status: "done",
    priority: "high",
    created_by: "ai",
    created_at: "2025-08-08T13:00:00Z",
    updated_at: "2025-08-13T08:00:00Z",
    email_summary: "関連メール 5 件\n\n1. 2025-08-08 - 監査法人\n   監査結果報告書\n2. 2025-08-09 - セキュリティチーム\n   対応方針の検討\n3. 2025-08-12 - 開発チーム\n   修正完了報告"
  }
];

// 設定画面用モックデータ
export const mockSettings = {
  user: {
    name: "山田 太郎",
    email: "yamada@example.com"
  },
  emailAccounts: [
    {
      id: "email-001",
      provider: "gmail",
      email: "yamada@gmail.com",
      isActive: true,
      lastSyncAt: "2025-08-13T08:30:00Z"
    },
    {
      id: "email-002", 
      provider: "outlook",
      email: "yamada@company.com",
      isActive: true,
      lastSyncAt: "2025-08-13T09:00:00Z"
    }
  ],
  excludeDomains: [
    "spam-domain.com",
    "newsletter-provider.com",
    "automated-system.local"
  ]
};

// 通知センター用モックデータ
export const mockNotifications = [
  {
    id: "notif-001",
    type: "task_created",
    title: "新しいタスクが作成されました",
    message: "「新機能のUI設計書作成」タスクがメール分析により作成されました",
    createdAt: "2025-08-13T09:30:00Z",
    isRead: false
  },
  {
    id: "notif-002", 
    type: "email_sync",
    title: "メール同期完了",
    message: "Gmail から 5件の新しいメールを同期しました",
    createdAt: "2025-08-13T09:00:00Z",
    isRead: false
  },
  {
    id: "notif-003",
    type: "cost_alert",
    title: "API使用料金アラート",
    message: "今月のOpenAI使用量が予算の80%に達しました",
    createdAt: "2025-08-12T18:00:00Z",
    isRead: true
  }
];

// AI調査結果用モックデータ
export const mockInvestigationResult = {
  taskTitle: "新機能のUI設計書作成",
  analysis: `## 実装・解決方法

このタスクは、ユーザーダッシュボードの新機能に関するUI設計書を作成するものです。以下のアプローチを推奨します：

### 1. 要件定義の整理
- メールに記載された機能要件の詳細確認
- ユーザーストーリーの作成
- 技術的制約の整理

### 2. UI/UXデザインプロセス
- ワイヤーフレームの作成
- モックアップデザイン
- プロトタイプ開発

## 必要なリソースやツール

- **デザインツール**: Figma または Adobe XD
- **プロトタイピングツール**: InVision または Principle
- **ドキュメント管理**: Confluence または Notion
- **チームメンバー**: UIデザイナー、UXデザイナー、フロントエンド開発者

## 推定作業時間

- 要件整理・分析: 4時間
- ワイヤーフレーム作成: 8時間  
- デザインモックアップ: 12時間
- プロトタイプ作成: 6時間
- レビュー・修正: 4時間

**合計: 約34時間（4-5営業日）**

## 潜在的なリスクや注意点

1. **要件の曖昧性**: メールベースの要件は詳細が不足している可能性
2. **技術的制約**: 既存システムとの互換性問題
3. **デザインシステム**: 既存のデザインガイドラインとの整合性
4. **レスポンシブ対応**: マルチデバイス対応の考慮

## 推奨される次のステップ

1. **即座実行**:
   - 田中部長との要件確認ミーティング設定
   - デザインチームからのガイドライン詳細取得
   
2. **1週間以内**:
   - ワイヤーフレーム初版作成
   - 技術チームとの制約事項確認
   
3. **2週間以内**:
   - デザインモックアップ完成
   - ステークホルダーレビュー実施

この順序で進めることで、効率的かつ品質の高いUI設計書を作成できます。`
};