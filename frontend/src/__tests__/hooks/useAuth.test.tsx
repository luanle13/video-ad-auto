import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useAuth } from '../../hooks/useAuth';

// Define the mock functions first
const mockStoreLogin = vi.fn();
const mockLogout = vi.fn();
const mockCheckAuth = vi.fn();

// Mock the auth store with a dynamic return value
const mockUseAuthStore = vi.fn();

vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => mockUseAuthStore(),
}));

// Mock the auth API
vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  saveTokens: vi.fn(),
}));

describe('useAuth Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Set default mock return value
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      login: mockStoreLogin,
      logout: mockLogout,
      checkAuth: mockCheckAuth,
    });
  });

  it('initial state', () => {
    const { result } = renderHook(() => useAuth());
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.isLoading).toBe(true);
  });

  it('login success', async () => {
    const userData = { id: '1', email: 'test@example.com' };
    
    mockStoreLogin.mockResolvedValue(userData);
    
    // Update the mock to return authenticated state after login
    mockUseAuthStore.mockReturnValueOnce({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: mockStoreLogin,
      logout: mockLogout,
      checkAuth: mockCheckAuth,
    }).mockReturnValueOnce({
      user: userData,
      isAuthenticated: true,
      isLoading: false,
      login: mockStoreLogin,
      logout: mockLogout,
      checkAuth: mockCheckAuth,
    });
    
    const { result } = renderHook(() => useAuth());
    
    const loginResult = await result.current.login('test@example.com', 'password');
    
    expect(mockStoreLogin).toHaveBeenCalledWith('test@example.com', 'password');
    expect(loginResult).toEqual(userData);
  });

  it('login failure', async () => {
    mockStoreLogin.mockRejectedValue(new Error('Invalid credentials'));
    
    const { result } = renderHook(() => useAuth());
    
    await expect(result.current.login('invalid@example.com', 'wrongpassword'))
      .rejects.toThrow('Invalid credentials');
      
    expect(mockStoreLogin).toHaveBeenCalledWith('invalid@example.com', 'wrongpassword');
  });

  it('logout', async () => {
    const userData = { id: '1', email: 'test@example.com' };
    
    mockUseAuthStore.mockReturnValue({
      user: userData,
      isAuthenticated: true,
      isLoading: false,
      login: mockStoreLogin,
      logout: mockLogout,
      checkAuth: mockCheckAuth,
    });
    
    const { result } = renderHook(() => useAuth());
    
    await result.current.logout();
    
    expect(mockLogout).toHaveBeenCalled();
  });

  it('check auth with valid token', () => {
    const userData = { id: '1', email: 'test@example.com' };
    
    mockUseAuthStore.mockReturnValue({
      user: userData,
      isAuthenticated: true,
      isLoading: false,
      login: mockStoreLogin,
      logout: mockLogout,
      checkAuth: mockCheckAuth,
    });
    
    const { result } = renderHook(() => useAuth());
    
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toEqual({ id: '1', email: 'test@example.com' });
  });

  it('check auth with no token', () => {
    mockUseAuthStore.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: mockStoreLogin,
      logout: mockLogout,
      checkAuth: mockCheckAuth,
    });
    
    const { result } = renderHook(() => useAuth());
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });
});