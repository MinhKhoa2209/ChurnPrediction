import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User } from '../auth';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,
      setAuth: (user, token) => set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
      }),
      clearAuth: () => set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      }),
      setLoading: (loading) => set({ isLoading: loading }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      version: 1,
      onRehydrateStorage: () => (state, error) => {
        if (error) {
          console.error('Failed to rehydrate auth state:', error);
        }
      },
    }
  )
);
