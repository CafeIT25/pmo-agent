import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface DemoState {
  isDemoMode: boolean;
  toggleDemoMode: () => void;
  setDemoMode: (enabled: boolean) => void;
}

export const useDemoStore = create<DemoState>()(
  persist(
    (set) => ({
      isDemoMode: false,
      toggleDemoMode: () => set((state) => ({ isDemoMode: !state.isDemoMode })),
      setDemoMode: (enabled: boolean) => set({ isDemoMode: enabled }),
    }),
    {
      name: 'pmo-demo-mode',
    }
  )
);