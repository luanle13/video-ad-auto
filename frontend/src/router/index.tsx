import { createBrowserRouter, Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/login',
    lazy: () => import('@/pages/LoginPage'),
  },
  {
    path: '/register',
    lazy: () => import('@/pages/RegisterPage'),
  },
  {
    path: '/dashboard',
    element: <ProtectedRoute />,
    lazy: () => import('@/pages/DashboardPage'),
  },
  {
    path: '/products/new',
    element: <ProtectedRoute />,
    lazy: () => import('@/pages/CreateProductPage'),
  },
  {
    path: '/videos/new',
    element: <ProtectedRoute />,
    lazy: () => import('@/pages/CreateVideoPage'),
  },
  {
    path: '/videos/:jobId',
    element: <ProtectedRoute />,
    lazy: () => import('@/pages/VideoPreviewPage'),
  },
  {
    path: '/settings',
    element: <ProtectedRoute />,
    lazy: () => import('@/pages/SettingsPage'),
  },
  {
    path: '*',
    lazy: () => import('@/pages/NotFoundPage'),
  },
]);