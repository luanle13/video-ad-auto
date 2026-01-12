import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { JobStatus } from '@/types';
import DashboardPage from '@/pages/DashboardPage';

// Mock the useJobs hook
const mockUseJobs = vi.fn();
const mockNavigate = vi.fn();

vi.mock('@/hooks/useJobs', () => ({
  useJobs: () => mockUseJobs(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders job list correctly', async () => {
    mockUseJobs.mockReturnValue({
      data: [
        {
          job_id: 'job-1',
          user_id: 'user-1',
          product_id: 'product-1',
          status: JobStatus.COMPLETE,
          adjustments: {},
          step_outputs: {},
          video_url: 'https://example.com/video.mp4',
          created_at: '2023-01-01T00:00:00Z',
          updated_at: '2023-01-01T00:00:00Z',
        },
      ],
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter initialEntries={['/dashboard']}>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/recent jobs/i)).toBeInTheDocument();
    });
    
    expect(screen.getByText(/total videos/i)).toBeInTheDocument();
    expect(screen.getByText(/processing/i)).toBeInTheDocument();
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
  });

  it('shows empty state when no jobs exist', async () => {
    mockUseJobs.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter initialEntries={['/dashboard']}>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByText(/no jobs yet/i)).toBeInTheDocument();
      expect(screen.getByText(/get started by creating your first video/i)).toBeInTheDocument();
    });
  });

  it('create button navigates to new video page', async () => {
    mockUseJobs.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter initialEntries={['/dashboard']}>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    
    const createButtons = screen.getAllByRole('button', { name: /create video/i });
    fireEvent.click(createButtons[0]);
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/videos/new');
    });
  });

  it('displays loading state when jobs are loading', async () => {
    mockUseJobs.mockReturnValue({
      data: [],
      isLoading: true,
      isError: false,
    });

    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter initialEntries={['/dashboard']}>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>
    );
    
    // Check for loading indicator
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });
});