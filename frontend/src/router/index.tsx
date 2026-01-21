import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import Spinner from '@/components/ui/Spinner';

// Lazy loaded pages
const LoginPage = lazy(() => import('@/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage'));
const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const CreateVideoPage = lazy(() => import('@/pages/CreateVideoPage'));
const VideoPreviewPage = lazy(() => import('@/pages/VideoPreviewPage'));
const SettingsPage = lazy(() => import('@/pages/SettingsPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFound'));

const SuspenseWrapper = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><Spinner /></div>}>
    {children}
  </Suspense>
);

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/login',
    element: <SuspenseWrapper><LoginPage /></SuspenseWrapper>,
  },
  {
    path: '/register',
    element: <SuspenseWrapper><RegisterPage /></SuspenseWrapper>,
  },
  {
    path: '/dashboard',
    element: <ProtectedRoute><SuspenseWrapper><DashboardPage /></SuspenseWrapper></ProtectedRoute>,
  },
  {
    path: '/videos/new',
    element: <ProtectedRoute><SuspenseWrapper><CreateVideoPage /></SuspenseWrapper></ProtectedRoute>,
  },
  {
    path: '/videos/:jobId',
    element: <ProtectedRoute><SuspenseWrapper><VideoPreviewPage /></SuspenseWrapper></ProtectedRoute>,
  },
  {
    path: '/settings',
    element: <ProtectedRoute><SuspenseWrapper><SettingsPage /></SuspenseWrapper></ProtectedRoute>,
  },
  {
    path: '*',
    element: <SuspenseWrapper><NotFoundPage /></SuspenseWrapper>,
  },
]);