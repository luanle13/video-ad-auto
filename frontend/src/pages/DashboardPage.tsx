import React from 'react';
import { Link } from 'react-router-dom';
import { useJobs } from '@/hooks/useJobs';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { JobCard } from '@/components/jobs/JobCard';
import { JobStatus } from '@/types';

const DashboardPage: React.FC = () => {
  const { data: jobs = [], isLoading, isError } = useJobs();
  const navigate = useNavigate();

  // Calculate stats
  const totalVideos = jobs.length;
  const processingJobs = jobs.filter(job => 
    job.status === JobStatus.PROCESSING || 
    job.status === JobStatus.ANALYZING || 
    job.status === JobStatus.SCRIPTING || 
    job.status === JobStatus.GENERATING_TTS || 
    job.status === JobStatus.GENERATING_VIDEO
  ).length;
  const completedJobs = jobs.filter(job => job.status === JobStatus.COMPLETE).length;

  if (isError) {
    return (
      <div className="p-6">
        <div className="text-center py-10">
          <h3 className="text-lg font-medium text-gray-900">Error loading dashboard</h3>
          <p className="mt-1 text-sm text-gray-500">Please try again later.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Manage your AI-generated videos</p>
        </div>
        <Button 
          variant="primary" 
          size="md"
          onClick={() => navigate('/videos/new')}
        >
          Create Video
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Total Videos</h3>
          <p className="mt-2 text-3xl font-bold text-primary-600">{totalVideos}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Processing</h3>
          <p className="mt-2 text-3xl font-bold text-warning-600">{processingJobs}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Completed</h3>
          <p className="mt-2 text-3xl font-bold text-success-600">{completedJobs}</p>
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Recent Jobs</h2>
        </div>
        <div className="p-6">
          {isLoading ? (
            <div className="flex justify-center py-10">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary-500"></div>
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-10">
              <h3 className="text-lg font-medium text-gray-900">No jobs yet</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by creating your first video.</p>
              <div className="mt-6">
                <Button 
                  variant="primary" 
                  size="md"
                  onClick={() => navigate('/videos/new')}
                >
                  Create Video
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {jobs.slice(0, 5).map((job) => (
                <JobCard key={job.job_id} job={job} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;