import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

interface TestWrapperProps {
  children: React.ReactNode;
  initialEntries?: string[];
}

export const TestWrapper: React.FC<TestWrapperProps> = ({ 
  children, 
  initialEntries = ['/'] 
}) => {
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <Toaster />
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
};