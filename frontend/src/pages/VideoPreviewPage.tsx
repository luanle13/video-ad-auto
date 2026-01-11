import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useJob } from '@/hooks/useJobs';
import { useRegenerateJob } from '@/hooks/useJobs';
import { useGetVideoDownloadUrl } from '@/hooks/useJobs'; // This hook doesn't exist yet, we'll need to create it
import { JobStatus } from '@/types';
import JobStatusBadge from '@/components/jobs/JobStatusBadge';
import { JobProgress } from '@/components/jobs/JobProgress';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { toast } from 'react-hot-toast';

// Note: We'll need to create the useGetVideoDownloadUrl hook separately
// For now, we'll create a placeholder implementation
const useGetVideoDownloadUrl = (jobId: string) => {
  // This would normally be a proper hook using react-query
  // For now, we'll just return a mock implementation
  return {
    data: jobId ? { download_url: `https://example.com/download/${jobId}` } : null,
    isLoading: false,
    isError: false,
  };
};

const VideoPreviewPage: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { data: job, isLoading, isError, refetch } = useJob(jobId!);
  const { mutateAsync: regenerateJob, isLoading: isRegenerating } = useRegenerateJob();
  const { data: downloadUrlData } = useGetVideoDownloadUrl(jobId!);
  
  const [regenerateAdjustments, setRegenerateAdjustments] = React.useState({
    background_style: '',
    tone: '',
    emphasis: '',
    duration_preference: 30,
    additional_instructions: '',
  });

  // Poll for job updates when in processing states
  useEffect(() => {
    if (job && 
        (job.status === JobStatus.PROCESSING || 
         job.status === JobStatus.ANALYZING || 
         job.status === JobStatus.SCRIPTING || 
         job.status === JobStatus.GENERATING_TTS || 
         job.status === JobStatus.GENERATING_VIDEO)) {
      const interval = setInterval(() => {
        refetch();
      }, 5000); // Refresh every 5 seconds

      return () => clearInterval(interval);
    }
  }, [job, refetch]);

  if (isLoading) {
    return (
      <div className="p-6 flex justify-center items-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (isError || !job) {
    return (
      <div className="p-6">
        <div className="text-center py-10">
          <h3 className="text-lg font-medium text-gray-900">Error loading job</h3>
          <p className="mt-1 text-sm text-gray-500">Please try again later.</p>
          <Button 
            variant="primary" 
            size="md" 
            onClick={() => navigate('/dashboard')}
            className="mt-4"
          >
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const handleRegenerate = async () => {
    if (!jobId) return;
    
    try {
      await regenerateJob({
        jobId,
        adjustments: regenerateAdjustments
      });
      toast.success('Video regeneration started!');
      refetch(); // Refresh job data
    } catch (error) {
      console.error('Error regenerating job:', error);
      toast.error('Failed to regenerate video. Please try again.');
    }
  };

  const handleDownload = () => {
    if (downloadUrlData?.download_url) {
      window.open(downloadUrlData.download_url, '_blank');
    } else {
      toast.error('Download URL not available yet.');
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header with job status */}
      <div className="mb-8">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {job.step_outputs?.product?.title || 'Video Preview'}
            </h1>
            <p className="text-gray-600">Job ID: {job.job_id}</p>
          </div>
          <div className="flex items-center space-x-4">
            <JobStatusBadge status={job.status} />
            {job.status === JobStatus.COMPLETE && (
              <Button 
                variant="primary" 
                size="md"
                onClick={handleDownload}
              >
                Download Video
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column - Video player and controls */}
        <div className="lg:col-span-2">
          <div className="bg-gray-900 rounded-xl overflow-hidden aspect-video flex items-center justify-center">
            {job.status === JobStatus.COMPLETE && job.video_url ? (
              <video 
                src={job.video_url} 
                controls 
                className="w-full h-full object-contain"
              />
            ) : job.status === JobStatus.FAILED ? (
              <div className="text-center p-8">
                <div className="text-red-500 mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900">Video Generation Failed</h3>
                <p className="mt-1 text-sm text-gray-500">
                  {job.error_message || 'An error occurred during video generation.'}
                </p>
              </div>
            ) : (
              <div className="text-center p-8">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500 mx-auto mb-4"></div>
                <h3 className="text-lg font-medium text-gray-900">Processing Video</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Your video is being generated. This may take a few minutes.
                </p>
              </div>
            )}
          </div>

          {/* Regenerate Form */}
          {(job.status === JobStatus.COMPLETE || job.status === JobStatus.FAILED) && (
            <div className="mt-6 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Regenerate Video</h2>
              <div className="space-y-4">
                <Input
                  label="Background Style"
                  type="text"
                  placeholder="e.g., modern, vintage, minimalist"
                  value={regenerateAdjustments.background_style}
                  onChange={(e) => setRegenerateAdjustments(prev => ({
                    ...prev,
                    background_style: e.target.value
                  }))}
                />
                <Input
                  label="Tone"
                  type="text"
                  placeholder="e.g., professional, casual, energetic"
                  value={regenerateAdjustments.tone}
                  onChange={(e) => setRegenerateAdjustments(prev => ({
                    ...prev,
                    tone: e.target.value
                  }))}
                />
                <Input
                  label="Emphasis"
                  type="text"
                  placeholder="What should be highlighted?"
                  value={regenerateAdjustments.emphasis}
                  onChange={(e) => setRegenerateAdjustments(prev => ({
                    ...prev,
                    emphasis: e.target.value
                  }))}
                />
                <Input
                  label="Additional Instructions"
                  as="textarea"
                  rows={3}
                  placeholder="Any specific requirements for the video..."
                  value={regenerateAdjustments.additional_instructions}
                  onChange={(e) => setRegenerateAdjustments(prev => ({
                    ...prev,
                    additional_instructions: e.target.value
                  }))}
                />
                <div className="flex justify-end">
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleRegenerate}
                    isLoading={isRegenerating}
                    disabled={isRegenerating}
                  >
                    {isRegenerating ? 'Regenerating...' : 'Regenerate Video'}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right column - Progress and details */}
        <div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Generation Progress</h2>
            <JobProgress job={job} />
          </div>

          {/* Job Details */}
          <div className="mt-6 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Job Details</h2>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-500">Created</p>
                <p className="text-gray-900">{new Date(job.created_at).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Updated</p>
                <p className="text-gray-900">{new Date(job.updated_at).toLocaleString()}</p>
              </div>
              {job.error_message && (
                <div>
                  <p className="text-sm text-gray-500">Error</p>
                  <p className="text-error-600">{job.error_message}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPreviewPage;