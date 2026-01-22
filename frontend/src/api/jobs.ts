import { apiClient } from './client';
import { Job, JobAdjustments } from '@/types';

// Types
export interface CreateJobRequest {
  product_id: string;
  adjustments?: JobAdjustments;
}

export interface RegenerateJobRequest {
  adjustments: JobAdjustments;
}

// Response types
interface JobListResponse {
  jobs: Job[];
  count: number;
}

// Job API functions
export const getJobs = async (status?: string): Promise<Job[]> => {
  const params = status ? { status } : {};
  const response = await apiClient.get<JobListResponse>('/jobs', { params });
  return response.data.jobs;
};

export const getJob = async (jobId: string): Promise<Job> => {
  const response = await apiClient.get<Job>(`/jobs/${jobId}`);
  return response.data;
};

export const createJob = async (
  productId: string, 
  adjustments?: JobAdjustments
): Promise<Job> => {
  const requestData: CreateJobRequest = {
    product_id: productId,
  };
  
  if (adjustments) {
    requestData.adjustments = adjustments;
  }
  
  const response = await apiClient.post<Job>('/jobs', requestData);
  return response.data;
};

export const regenerateJob = async (
  jobId: string, 
  adjustments: JobAdjustments
): Promise<Job> => {
  const requestData: RegenerateJobRequest = {
    adjustments,
  };
  
  const response = await apiClient.post<Job>(`/jobs/${jobId}/regenerate`, requestData);
  return response.data;
};

export const getVideoDownloadUrl = async (jobId: string): Promise<{ download_url: string }> => {
  const response = await apiClient.get<{ download_url: string }>(`/jobs/${jobId}/video-download-url`);
  return response.data;
};