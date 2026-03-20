import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  email: string;
  full_name: string;
  currency: string;
  avatar_url?: string;
  is_verified: boolean;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (token: string, user: User) => void;
  updateUser: (user: Partial<User>) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      setAuth: (token, user) => set({ token, user, isAuthenticated: true }),
      updateUser: (data) => set((state) => ({ user: state.user ? { ...state.user, ...data } : null })),
      logout: () => set({ token: null, user: null, isAuthenticated: false }),
    }),
    {
      name: 'smartspend-auth',
    }
  )
);
