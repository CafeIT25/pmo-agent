/**
 * デモモード対応のデータ取得フック
 */
import { useDemoStore } from '@/store/demoStore';
import { 
  mockUsageStats, 
  mockRecentUsage, 
  mockTasks, 
  mockSettings, 
  mockNotifications,
  mockInvestigationResult 
} from '@/data/mockData';
import apiClient from '@/api/client';

export const useDemoData = () => {
  const isDemoMode = useDemoStore((state) => state.isDemoMode);

  // 使用量ダッシュボード用データ取得
  const fetchUsageData = async (params?: any) => {
    if (isDemoMode) {
      // モックデータを Promise として返す
      return {
        monthly: mockUsageStats,
        recent: mockRecentUsage
      };
    }
    
    // 本番APIからデータ取得
    const [monthlyResponse, recentResponse] = await Promise.all([
      apiClient.get('/api/v1/cost/monthly', { params }),
      apiClient.get('/api/v1/cost/recent', { 
        params: { days: 7, limit: 20 } 
      })
    ]);

    return {
      monthly: monthlyResponse.data,
      recent: recentResponse.data
    };
  };

  // タスク一覧データ取得
  const fetchTasksData = async () => {
    if (isDemoMode) {
      return mockTasks;
    }
    
    const response = await apiClient.get('/api/v1/tasks');
    return response.data;
  };

  // 設定データ取得
  const fetchSettingsData = async () => {
    if (isDemoMode) {
      return mockSettings;
    }
    
    const response = await apiClient.get('/api/v1/settings');
    return response.data;
  };

  // 通知データ取得
  const fetchNotificationsData = async () => {
    if (isDemoMode) {
      return mockNotifications;
    }
    
    const response = await apiClient.get('/api/v1/notifications');
    return response.data;
  };

  // AI調査結果取得
  const fetchInvestigationData = async (taskId: string) => {
    if (isDemoMode) {
      return mockInvestigationResult;
    }
    
    const response = await apiClient.post(`/api/v1/tasks/${taskId}/investigate`);
    return response.data;
  };

  // メール同期
  const syncEmails = async () => {
    if (isDemoMode) {
      // モックでは2秒待機して成功を返す
      await new Promise(resolve => setTimeout(resolve, 2000));
      return { 
        success: true, 
        message: 'デモモード: メール同期が完了しました（5件の新しいメールを処理）' 
      };
    }
    
    const response = await apiClient.post('/api/v1/emails/sync');
    return response.data;
  };

  // タスク作成
  const createTask = async (taskData: any) => {
    if (isDemoMode) {
      const newTask = {
        id: `task-demo-${Date.now()}`,
        ...taskData,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        created_by: 'user'
      };
      return newTask;
    }
    
    const response = await apiClient.post('/api/v1/tasks', taskData);
    return response.data;
  };

  // タスク更新
  const updateTask = async (taskId: string, updates: any) => {
    if (isDemoMode) {
      return {
        id: taskId,
        ...updates,
        updated_at: new Date().toISOString()
      };
    }
    
    const response = await apiClient.put(`/api/v1/tasks/${taskId}`, updates);
    return response.data;
  };

  return {
    isDemoMode,
    fetchUsageData,
    fetchTasksData,
    fetchSettingsData, 
    fetchNotificationsData,
    fetchInvestigationData,
    syncEmails,
    createTask,
    updateTask
  };
};