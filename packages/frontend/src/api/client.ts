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
const apiClient = isMockMode ? mockClient : realApiClient;

// モックモードでない場合のみインターセプターを設定
if (!isMockMode) {
  // リクエストインターセプター
  realApiClient.interceptors.request.use(
    (config) => {
      // Zustandストアから直接トークンを取得
      const { accessToken } = useAuthStore.getState();
      if (accessToken && config.headers) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
      // CSRF対策のためのヘッダー追加
      if (config.headers) {
        config.headers['X-Requested-With'] = 'XMLHttpRequest';
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // レスポンスインターセプター
  realApiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && originalRequest && !(originalRequest as { _retry?: boolean })._retry) {
        (originalRequest as { _retry?: boolean })._retry = true;

        try {
          const { refreshToken, setTokens } = useAuthStore.getState();

          if (refreshToken) {
            const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/v1/auth/refresh`, {
              refresh_token: refreshToken,
            });

            const { access_token, refresh_token } = response.data;
            setTokens(access_token, refresh_token);

            // 元のリクエストを再実行
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
            }
            return realApiClient(originalRequest);
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

export { apiClient };
export default apiClient;