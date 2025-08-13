import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from '@/api/client';

interface User {
  id: string;
  email: string;
  name?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  accessToken: string | null;
  refreshToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      accessToken: null,
      refreshToken: null,

      login: async (email: string, password: string) => {
        try {
          const response = await axios.post('/api/v1/auth/login', {
            username: email,
            password,
          });

          const { access_token, refresh_token } = response.data;

          set({
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
          });

          // ユーザー情報を取得
          const userResponse = await axios.get('/api/v1/users/me', {
            headers: {
              Authorization: `Bearer ${access_token}`,
            },
          });

          set({ user: userResponse.data });
        } catch (error) {
          throw error;
        }
      },

      logout: () => {
        set({
          user: null,
          isAuthenticated: false,
          accessToken: null,
          refreshToken: null,
        });
      },

      setTokens: (accessToken: string, refreshToken: string) => {
        set({
          accessToken,
          refreshToken,
          isAuthenticated: true,
        });
      },

      clearAuth: () => {
        set({
          user: null,
          isAuthenticated: false,
          accessToken: null,
          refreshToken: null,
        });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        // トークンは保存しない（セキュリティ強化）
        // セッション中のみメモリに保持
        isAuthenticated: state.isAuthenticated,
        user: state.user ? { id: state.user.id, email: state.user.email, name: state.user.name } : null,
      }),
    }
  )
);