import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { TokenResponse, ErrorResponse } from '@/types';

// Create axios instance
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors and refresh tokens
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Attempt to refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post<TokenResponse>(
            `${import.meta.env.VITE_API_URL || '/api'}/auth/refresh`,
            { refresh_token: refreshToken }
          );

          if (response.data.access_token) {
            localStorage.setItem('access_token', response.data.access_token);
            
            // Retry the original request with the new token
            originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
            return apiClient(originalRequest);
          }
        }
      } catch (refreshError) {
        // If refresh fails, logout the user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Optionally redirect to login page
        // window.location.href = '/login';
      }
    }

    // Transform error to consistent format
    const errorResponse: ErrorResponse = {
      error: error.response?.data?.error || error.message || 'An error occurred',
      code: error.response?.status?.toString() || 'UNKNOWN',
      details: error.response?.data || undefined,
    };

    return Promise.reject(errorResponse);
  }
);