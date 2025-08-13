import axios from 'axios';
import { mockClient, isMockMode } from './mockClient';
import { useAuthStore } from '@/store/authStore';

const realApiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
});

// モックモードの場合はmockClientを使用
const apiClient = isMockMode ? mockClient as any : realApiClient;

// モックモードでない場合のみインターセプターを設定
if (!isMockMode) {
  // リクエストインターセプター
  apiClient.interceptors.request.use(
    (config) => {
      // Zustandストアから直接トークンを取得
      const { accessToken } = useAuthStore.getState();
      if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
      // CSRF対策のためのヘッダー追加
      config.headers['X-Requested-With'] = 'XMLHttpRequest';
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // レスポンスインターセプター
  apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const { refreshToken, setTokens, clearAuth } = useAuthStore.getState();

          if (refreshToken) {
            const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/auth/refresh`, {
              refresh_token: refreshToken,
            });

            const { access_token, refresh_token: new_refresh_token } = response.data;

            // 新しいトークンを保存
            setTokens(access_token, new_refresh_token || refreshToken);

            // リトライ
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return apiClient(originalRequest);
          }
        } catch (refreshError) {
          // リフレッシュ失敗時はログアウト
          const { clearAuth } = useAuthStore.getState();
          clearAuth();
          window.location.href = '/login';
        }
      }

      return Promise.reject(error);
    }
  );
}

// モックモードの通知をコンソールに表示
if (isMockMode) {
  console.log('🎭 Mock Mode is enabled. Using mock data instead of real API.');
}

export default apiClient;