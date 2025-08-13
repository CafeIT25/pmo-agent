// モックデータとレスポンスを提供するサービス
export interface MockUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface MockTask {
  id: string;
  title: string;
  description: string;
  status: 'todo' | 'in_progress' | 'done';
  priority: 'low' | 'medium' | 'high';
  due_date: string;
  created_at: string;
  updated_at: string;
  user_id: string;
}

// モックユーザーデータ
const mockUsers: MockUser[] = [
  {
    id: '1',
    email: 'test@example.com',
    full_name: 'テスト ユーザー',
    is_active: true,
    is_superuser: false,
  },
  {
    id: '2',
    email: 'admin@example.com',
    full_name: '管理者 ユーザー',
    is_active: true,
    is_superuser: true,
  },
  {
    id: '3',
    email: 'demo@example.com',
    full_name: 'デモ ユーザー',
    is_active: true,
    is_superuser: false,
  },
];

// モックタスクデータ
const mockTasks: MockTask[] = [
  {
    id: '1',
    title: 'プロジェクト計画書の作成',
    description: 'Q4のプロジェクト計画書を作成する',
    status: 'todo',
    priority: 'high',
    due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: '1',
  },
  {
    id: '2',
    title: 'ステークホルダー会議の準備',
    description: '月次ステークホルダー会議の資料準備',
    status: 'in_progress',
    priority: 'medium',
    due_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: '1',
  },
  {
    id: '3',
    title: 'リスク評価レポート',
    description: 'プロジェクトのリスク評価を実施',
    status: 'done',
    priority: 'low',
    due_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date().toISOString(),
    user_id: '1',
  },
];

// メールアカウントのモックデータ
const mockEmailAccounts = [
  {
    id: '1',
    email: 'test@example.com',
    provider: 'google',
    is_active: true,
    last_sync: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
  },
  {
    id: '2',
    email: 'demo@example.com',
    provider: 'microsoft',
    is_active: true,
    last_sync: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
];

// 遅延を追加して実際のAPIレスポンスをシミュレート
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// モックレスポンス関数
export const mockService = {
  // 認証
  async login(email: string, password: string) {
    await delay(500);
    
    // モックパスワードチェック
    const validCredentials = [
      { email: 'test@example.com', password: 'testpass123' },
      { email: 'admin@example.com', password: 'adminpass123' },
      { email: 'demo@example.com', password: 'demopass123' },
    ];
    
    const isValid = validCredentials.some(
      cred => cred.email === email && cred.password === password
    );
    
    if (!isValid) {
      throw new Error('メールアドレスまたはパスワードが正しくありません');
    }
    
    const user = mockUsers.find(u => u.email === email);
    return {
      access_token: 'mock_access_token_' + Date.now(),
      refresh_token: 'mock_refresh_token_' + Date.now(),
      token_type: 'bearer',
      user,
    };
  },

  async register(email: string, password: string, full_name: string) {
    await delay(500);
    
    // 既存ユーザーチェック
    if (mockUsers.some(u => u.email === email)) {
      throw new Error('このメールアドレスは既に使用されています');
    }
    
    const newUser: MockUser = {
      id: String(mockUsers.length + 1),
      email,
      full_name,
      is_active: true,
      is_superuser: false,
    };
    
    mockUsers.push(newUser);
    
    return {
      access_token: 'mock_access_token_' + Date.now(),
      refresh_token: 'mock_refresh_token_' + Date.now(),
      token_type: 'bearer',
      user: newUser,
    };
  },

  // ユーザー情報
  async getCurrentUser() {
    await delay(300);
    return mockUsers[0]; // テストユーザーを返す
  },

  // タスク
  async getTasks() {
    await delay(400);
    return mockTasks;
  },

  async createTask(data: Partial<MockTask>) {
    await delay(500);
    const newTask: MockTask = {
      id: String(mockTasks.length + 1),
      title: data.title || '',
      description: data.description || '',
      status: data.status || 'todo',
      priority: data.priority || 'medium',
      due_date: data.due_date || new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      user_id: '1',
    };
    mockTasks.push(newTask);
    return newTask;
  },

  async updateTask(id: string, data: Partial<MockTask>) {
    await delay(400);
    const taskIndex = mockTasks.findIndex(t => t.id === id);
    if (taskIndex === -1) {
      throw new Error('タスクが見つかりません');
    }
    
    mockTasks[taskIndex] = {
      ...mockTasks[taskIndex],
      ...data,
      updated_at: new Date().toISOString(),
    };
    
    return mockTasks[taskIndex];
  },

  async deleteTask(id: string) {
    await delay(400);
    const taskIndex = mockTasks.findIndex(t => t.id === id);
    if (taskIndex === -1) {
      throw new Error('タスクが見つかりません');
    }
    
    mockTasks.splice(taskIndex, 1);
    return { success: true };
  },

  // メール同期
  async syncEmails(accountId: string) {
    await delay(2000); // 実際の同期処理をシミュレート
    
    // ランダムに成功/失敗を返す（デモ用）
    if (Math.random() > 0.8) {
      throw new Error('メール同期に失敗しました');
    }
    
    return {
      task_id: 'mock_task_' + Date.now(),
      status: 'completed',
      synced_count: Math.floor(Math.random() * 50) + 10,
      new_tasks: Math.floor(Math.random() * 5),
    };
  },

  async getEmailAccounts() {
    await delay(300);
    return mockEmailAccounts;
  },

  // AI分析
  async analyzeTask(taskId: string) {
    await delay(3000); // AI処理をシミュレート
    
    const task = mockTasks.find(t => t.id === taskId);
    if (!task) {
      throw new Error('タスクが見つかりません');
    }
    
    return {
      task_id: taskId,
      suggestions: [
        {
          type: 'subtask',
          content: `${task.title}のサブタスク1`,
          priority: 'medium',
        },
        {
          type: 'subtask',
          content: `${task.title}のサブタスク2`,
          priority: 'low',
        },
        {
          type: 'risk',
          content: 'スケジュール遅延のリスクがあります',
          mitigation: 'バッファ時間を追加することを推奨',
        },
      ],
      estimated_hours: Math.floor(Math.random() * 20) + 5,
      complexity: 'medium',
    };
  },

  // タスクステータス確認（Celeryタスク）
  async getTaskStatus(taskId: string) {
    await delay(200);
    
    // モックステータスを返す
    const statuses = ['pending', 'processing', 'completed', 'failed'];
    const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
    
    return {
      task_id: taskId,
      status: randomStatus,
      progress: randomStatus === 'processing' ? Math.floor(Math.random() * 80) + 20 : 100,
      result: randomStatus === 'completed' ? { success: true } : null,
      error: randomStatus === 'failed' ? 'タスクの実行に失敗しました' : null,
    };
  },
};