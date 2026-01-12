import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Use vi.hoisted to ensure mocks are available during hoisting
const { mockGetJobs, mockCreateJob, mockGetJob } = vi.hoisted(() => ({
  mockGetJobs: vi.fn(),
  mockCreateJob: vi.fn(),
  mockGetJob: vi.fn(),
}));

// Mock the API module
vi.mock('@/api/jobs', () => ({
  getJobs: mockGetJobs,
  getJob: mockGetJob,
  createJob: mockCreateJob,
  regenerateJob: vi.fn(),
}));

// Import after the mock
import { useJobs, useJob, useCreateJob } from '../../hooks/useJobs';

// Create a test query client
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      gcTime: 0, // Immediately garbage collect
    },
  },
});

describe('useJobs Hook', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it('fetch jobs', async () => {
    const mockJobs = [
      { id: '1', name: 'Test Job 1', status: 'completed', createdAt: new Date().toISOString() },
      { id: '2', name: 'Test Job 2', status: 'processing', createdAt: new Date().toISOString() },
    ];
    
    mockGetJobs.mockResolvedValue(mockJobs);
    
    const { result } = renderHook(() => useJobs(), { wrapper });
    
    // Initially, data should be undefined and isPending should be true
    expect(result.current.isPending).toBe(true);
    
    // Wait for the jobs to be fetched
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });
    
    expect(result.current.data).toEqual(mockJobs);
  });

  it('create job', async () => {
    const newJobData = { productId: 'product-123', adjustments: { voice: 'test-voice' } };
    const createdJob = { id: '3', ...newJobData, status: 'pending', createdAt: new Date().toISOString() };
    
    mockCreateJob.mockResolvedValue(createdJob);
    
    const { result } = renderHook(() => useCreateJob(), { wrapper });
    
    let mutationResult;
    await act(async () => {
      mutationResult = await result.current.mutateAsync(newJobData);
    });
    
    expect(mockCreateJob).toHaveBeenCalledWith(newJobData.productId, newJobData.adjustments);
    expect(mutationResult).toEqual(createdJob);
  });
});