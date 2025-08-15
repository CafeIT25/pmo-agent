import { create } from 'zustand';
import axios from '@/api/client';
import { mockChatThreads, getChatThreadsByTaskId, getChatThreadById } from '@/data/mockChatData';
import { useDemoStore } from '@/store/demoStore';

export interface ChatMessage {
  id: string;
  thread_id: string;
  role: 'user' | 'assistant';
  content: string;
  token_count?: number;
  model_id?: string;
  cost?: number;
  created_at: string;
}

export interface ChatThread {
  id: string;
  user_id: string;
  task_id?: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: ChatMessage[];
}

interface ChatState {
  // State
  threads: ChatThread[];
  activeThreadId: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  isTyping: boolean;
  error: string | null;

  // Actions
  fetchThreads: () => Promise<void>;
  selectThread: (threadId: string | null) => Promise<void>;
  createThread: (title: string, taskId?: string, initialMessage?: string) => Promise<ChatThread>;
  sendMessage: (content: string) => Promise<void>;
  deleteThread: (threadId: string) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

const MAX_TOKENS = 4000; // OpenAI API制限を考慮した安全なトークン数

// トークン数を概算する関数（gpt-tokenizerの代替）
const estimateTokenCount = (text: string): number => {
  // 簡単な概算: 英語では約4文字=1トークン、日本語では約1.5文字=1トークン
  const englishChars = text.match(/[a-zA-Z0-9\s]/g)?.length || 0;
  const japaneseChars = text.length - englishChars;
  return Math.ceil(englishChars / 4 + japaneseChars / 1.5);
};

// トークン制限内でメッセージを選択する関数
const selectMessagesWithinTokenLimit = (messages: ChatMessage[], maxTokens: number = MAX_TOKENS): ChatMessage[] => {
  let totalTokens = 0;
  const selectedMessages: ChatMessage[] = [];
  
  // 最新メッセージから遡って選択
  for (let i = messages.length - 1; i >= 0; i--) {
    const message = messages[i];
    const messageTokens = message.token_count || estimateTokenCount(message.content);
    
    if (totalTokens + messageTokens > maxTokens) {
      break;
    }
    
    selectedMessages.unshift(message);
    totalTokens += messageTokens;
  }
  
  return selectedMessages;
};

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  threads: [],
  activeThreadId: null,
  messages: [],
  isLoading: false,
  isTyping: false,
  error: null,

  // Actions
  fetchThreads: async () => {
    set({ isLoading: true, error: null });
    try {
      // デモモードの場合はモックデータを使用
      const isDemoMode = useDemoStore.getState().isDemoMode;
      
      if (isDemoMode) {
        // モックデータを使用
        await new Promise(resolve => setTimeout(resolve, 500)); // 読み込み感を演出
        set({ threads: mockChatThreads, isLoading: false });
      } else {
        const response = await axios.get('/api/v1/chat/threads');
        set({ threads: response.data, isLoading: false });
      }
    } catch (error: any) {
      // デモモードではエラーが発生した場合もモックデータを使用
      const isDemoMode = useDemoStore.getState().isDemoMode;
      if (isDemoMode) {
        set({ threads: mockChatThreads, isLoading: false });
      } else {
        set({ 
          error: error.response?.data?.detail || 'スレッド一覧の取得に失敗しました',
          isLoading: false 
        });
      }
    }
  },

  selectThread: async (threadId: string | null) => {
    if (!threadId) {
      set({ activeThreadId: null, messages: [], isLoading: false });
      return;
    }
    
    set({ isLoading: true, error: null });
    try {
      const isDemoMode = useDemoStore.getState().isDemoMode;
      
      if (isDemoMode) {
        // モックデータを使用
        const thread = getChatThreadById(threadId);
        if (thread) {
          await new Promise(resolve => setTimeout(resolve, 300)); // 読み込み感を演出
          set({ 
            activeThreadId: threadId,
            messages: thread.messages || [],
            isLoading: false 
          });
        } else {
          set({ 
            error: 'スレッドが見つかりません',
            isLoading: false 
          });
        }
      } else {
        const response = await axios.get(`/api/v1/chat/threads/${threadId}`);
        const threadData: ChatThread & { messages: ChatMessage[] } = response.data;
        
        set({ 
          activeThreadId: threadId,
          messages: threadData.messages || [],
          isLoading: false 
        });
      }
    } catch (error: any) {
      const isDemoMode = useDemoStore.getState().isDemoMode;
      if (isDemoMode) {
        // デモモードではモックデータから検索
        const thread = getChatThreadById(threadId);
        if (thread) {
          set({ 
            activeThreadId: threadId,
            messages: thread.messages || [],
            isLoading: false 
          });
        } else {
          set({ 
            error: 'スレッドが見つかりません',
            isLoading: false 
          });
        }
      } else {
        set({ 
          error: error.response?.data?.detail || 'スレッドの取得に失敗しました',
          isLoading: false 
        });
      }
    }
  },

  createThread: async (title: string, taskId?: string, initialMessage?: string) => {
    const isDemoMode = useDemoStore.getState().isDemoMode;
    
    set({ isLoading: true, error: null });
    
    if (isDemoMode) {
      // Demo mode: create a mock thread
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API delay
      
      const newThread: ChatThread = {
        id: `demo_thread_${Date.now()}`,
        user_id: 'demo_user',
        task_id: taskId || '',
        title,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages: []
      };
      
      set(state => ({
        threads: [newThread, ...state.threads],
        activeThreadId: newThread.id,
        messages: newThread.messages || [],
        isLoading: false
      }));
      
      // If there's an initial message, send it
      if (initialMessage) {
        await get().sendMessage(initialMessage);
      }
      
      return newThread;
    } else {
      // Real API logic
      try {
        const response = await axios.post('/api/v1/chat/threads', {
          title,
          task_id: taskId,
          initial_message: initialMessage
        });
        
        const newThread: ChatThread = response.data;
        
        set(state => ({ 
          threads: [newThread, ...state.threads],
          activeThreadId: newThread.id,
          messages: newThread.messages || [],
          isLoading: false 
        }));
        
        // 初期メッセージがある場合、メッセージ履歴を再取得
        if (initialMessage) {
          await get().selectThread(newThread.id);
        }
        
        return newThread;
      } catch (error: any) {
        set({ 
          error: error.response?.data?.detail || 'スレッドの作成に失敗しました',
          isLoading: false 
        });
        throw error;
      }
    }
  },

  sendMessage: async (content: string) => {
    const { activeThreadId } = get();
    const isDemoMode = useDemoStore.getState().isDemoMode;

    if (!activeThreadId) {
      set({ error: 'アクティブなスレッドがありません' });
      return;
    }

    const userMessage: ChatMessage = {
      id: `temp_user_${Date.now()}`,
      thread_id: activeThreadId,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    };

    set(state => ({
      messages: [...state.messages, userMessage],
      isTyping: true,
      error: null,
    }));

    if (isDemoMode) {
      // --- Demo Mode Logic ---
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate thinking

      const assistantMessage: ChatMessage = {
        id: `temp_assistant_${Date.now()}`,
        thread_id: activeThreadId,
        role: 'assistant',
        content: `これはデモ用の返信です。

**タスク提案:**
ユーザーが送信した「${content}」というメッセージに基づき、以下の対応が考えられます。

1.  **タスクの細分化:** より具体的なサブタスクに分割し、担当者を割り当てます。
2.  **関連資料の収集:** 関連するドキュメントや過去の類似タスクを検索します。
3.  **専門家への相談:** 必要に応じて、専門知識を持つチームメンバーに意見を求めます。`,
        created_at: new Date().toISOString(),
        model_id: 'demo-gpt-4',
        token_count: 150,
        cost: 0,
      };

      set(state => ({
        messages: [...state.messages, assistantMessage],
        isTyping: false,
      }));

      // Update thread timestamp
      set(state => ({
        threads: state.threads.map(thread =>
          thread.id === activeThreadId
            ? { ...thread, updated_at: new Date().toISOString() }
            : thread
        ),
      }));
    } else {
      // --- Real API Logic ---
      try {
        const response = await axios.post(`/api/v1/chat/threads/${activeThreadId}/messages`, {
          content,
        });

        const { user_message, assistant_message } = response.data;

        set(state => ({
          messages: [
            ...state.messages.filter(m => m.id !== userMessage.id), // Remove optimistic message
            user_message,
            assistant_message,
          ],
          isTyping: false,
        }));

        // Update thread timestamp
        set(state => ({
          threads: state.threads.map(thread =>
            thread.id === activeThreadId
              ? { ...thread, updated_at: new Date().toISOString() }
              : thread
          ),
        }));
      } catch (error: any) {
        set(state => ({
          messages: state.messages.filter(m => m.id !== userMessage.id), // Remove optimistic message on error
          error: error.response?.data?.detail || 'メッセージの送信に失敗しました',
          isTyping: false,
        }));
      }
    }
  },

  deleteThread: async (threadId: string) => {
    set({ isLoading: true, error: null });
    try {
      await axios.delete(`/api/v1/chat/threads/${threadId}`);
      
      set(state => ({
        threads: state.threads.filter(thread => thread.id !== threadId),
        activeThreadId: state.activeThreadId === threadId ? null : state.activeThreadId,
        messages: state.activeThreadId === threadId ? [] : state.messages,
        isLoading: false
      }));
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'スレッドの削除に失敗しました',
        isLoading: false 
      });
    }
  },

  clearError: () => set({ error: null }),

  reset: () => set({
    threads: [],
    activeThreadId: null,
    messages: [],
    isLoading: false,
    isTyping: false,
    error: null
  })
}));