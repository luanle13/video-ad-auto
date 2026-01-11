import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  getJobs as getJobsApi, 
  getJob as getJobApi, 
  createJob as createJobApi, 
  regenerateJob as regenerateJobApi 
} from '@/api/jobs';
import { Job, JobStatus, JobAdjustments } from '@/types';

export const useJobs = (status?: string) => {
  return useQuery<Job[]>({
    queryKey: ['jobs', status],
    queryFn: () => getJobsApi(status),
  });
};

export const useJob = (id: string) => {
  return useQuery<Job>({
    queryKey: ['job', id],
    queryFn: () => getJobApi(id),
    enabled: !!id,
    refetchInterval: (data) => {
      // Refetch every 5 seconds if the job is in a processing state
      if (data && 
          (data.status === JobStatus.PROCESSING || 
           data.status === JobStatus.ANALYZING || 
           data.status === JobStatus.SCRIPTING || 
           data.status === JobStatus.GENERATING_TTS || 
           data.status === JobStatus.GENERATING_VIDEO)) {
        return 5000; // 5 seconds
      }
      return false; // Don't refetch if not in processing state
    },
  });
};

export const useCreateJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ productId, adjustments }: { productId: string; adjustments?: JobAdjustments }) => 
      createJobApi(productId, adjustments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};

export const useRegenerateJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ jobId, adjustments }: { jobId: string; adjustments: JobAdjustments }) => 
      regenerateJobApi(jobId, adjustments),
    onSuccess: (data) => {
      queryClient.setQueryData(['job', data.job_id], data);
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
};