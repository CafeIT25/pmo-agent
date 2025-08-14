import { mockService } from '../services/mockService';

// モックモードかどうかを判定 (デフォルトで有効)
export const isMockMode = import.meta.env.VITE_MOCK_MODE !== 'false' && 
                         (import.meta.env.VITE_MOCK_MODE === 'true' || 
                          import.meta.env.VITE_API_URL === undefined || 
                          import.meta.env.VITE_API_URL === '' ||
                          import.meta.env.NODE_ENV === 'development' ||
                          true); // デフォルトで有効

// APIクライアントのモックラッパー
export const mockClient = {
  interceptors: {
    request: {
      use: () => {},
    },
    response: {
      use: () => {},
    },
  },

  // GETリクエスト
  async get(url: string) {
    if (url.includes('/auth/me')) {
      return { data: await mockService.getCurrentUser() };
    }
    if (url.includes('/tasks')) {
      return { data: await mockService.getTasks() };
    }
    if (url.includes('/email/accounts')) {
      return { data: await mockService.getEmailAccounts() };
    }
    if (url.includes('/worker/task/')) {
      const taskId = url.split('/').pop() || '';
      return { data: await mockService.getTaskStatus(taskId) };
    }
    
    throw new Error(`Mock not implemented for GET ${url}`);
  },

  // POSTリクエスト
  async post(url: string, data?: any) {
    if (url.includes('/auth/login')) {
      return { data: await mockService.login(data.username, data.password) };
    }
    if (url.includes('/auth/register')) {
      return { data: await mockService.register(data.email, data.password, data.full_name) };
    }
    if (url.includes('/tasks')) {
      return { data: await mockService.createTask(data) };
    }
    if (url.includes('/email/sync')) {
      return { data: await mockService.syncEmails(data.account_id) };
    }
    if (url.includes('/ai/analyze')) {
      return { data: await mockService.analyzeTask(data.task_id) };
    }
    
    throw new Error(`Mock not implemented for POST ${url}`);
  },

  // PUTリクエスト
  async put(url: string, data?: any) {
    if (url.includes('/tasks/')) {
      const taskId = url.split('/').filter(Boolean).pop() || '';
      return { data: await mockService.updateTask(taskId, data) };
    }
    
    throw new Error(`Mock not implemented for PUT ${url}`);
  },

  // DELETEリクエスト
  async delete(url: string) {
    if (url.includes('/tasks/')) {
      const taskId = url.split('/').filter(Boolean).pop() || '';
      return { data: await mockService.deleteTask(taskId) };
    }
    
    throw new Error(`Mock not implemented for DELETE ${url}`);
  },

  // エラーハンドリング用ヘルパー
  isAxiosError(error: any): boolean {
    return error && error.response !== undefined;
  },
};