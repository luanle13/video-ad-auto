import React from 'react';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { Spinner } from '@/components/Spinner'; // Assuming we have a spinner component

const ProtectedRoute: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const user = useRequireAuth();

  // Show loading while checking authentication
  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner />
      </div>
    );
  }

  // Render children if authenticated
  return <>{children}</>;
};

export default ProtectedRoute;