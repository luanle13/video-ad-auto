import { useAuthStore } from '@/stores/authStore';
import { register as registerApi, saveTokens } from '@/api/auth';

export const useAuth = () => {
  const { user, isAuthenticated, isLoading, login: storeLogin, logout, checkAuth } = useAuthStore();

  const login = async (email: string, password: string) => {
    return storeLogin(email, password);
  };

  const register = async (email: string, password: string) => {
    const tokens = await registerApi(email, password);
    // Save tokens after registration
    saveTokens(tokens);
    // Update the auth state by checking auth
    await checkAuth();
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    register,
  };
};