import { create } from 'zustand';
import { persist, StateStorage } from 'zustand/middleware';
import { User } from '@/types';
import { login as loginApi, getMe, logout as logoutApi, saveTokens, clearTokens, getAccessToken } from '@/api/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

const storage: StateStorage = {
  getItem: (name) => {
    const str = localStorage.getItem(name);
    return str ? JSON.parse(str) : null;
  },
  setItem: (name, value) => {
    localStorage.setItem(name, JSON.stringify(value));
  },
  removeItem: (name) => {
    localStorage.removeItem(name);
  },
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      
      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          // Call API login
          const tokens = await loginApi(email, password);
          
          // Save tokens
          saveTokens(tokens);
          
          // Fetch user
          const user = await getMe();
          
          // Set isAuthenticated
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          set({ user: null, isAuthenticated: false, isLoading: false });
          throw error;
        }
      },
      
      logout: () => {
        // Clear tokens from storage
        logoutApi();
        
        // Reset state
        set({ user: null, isAuthenticated: false, isLoading: false });
      },
      
      checkAuth: async () => {
        set({ isLoading: true });
        
        try {
          const token = getAccessToken();
          
          if (!token) {
            set({ user: null, isAuthenticated: false, isLoading: false });
            return;
          }
          
          // Validate token by fetching user
          const user = await getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error) {
          // If token validation fails, clear tokens and reset state
          clearTokens();
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      storage,
    }
  )
);