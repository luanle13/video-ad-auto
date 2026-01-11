import React from 'react';
import { Link } from 'react-router-dom';
import { Job } from '@/types';
import JobStatusBadge from './JobStatusBadge';

interface JobCardProps {
  job: Job;
}

export const JobCard: React.FC<JobCardProps> = ({ job }) => {
  // Find the product title from step_outputs or use a default
  const productTitle = job.step_outputs?.product?.title || 'Untitled Product';
  const createdAt = new Date(job.created_at).toLocaleDateString();

  return (
    <Link 
      to={`/videos/${job.job_id}`}
      className="block hover:bg-gray-50 transition-colors duration-200 rounded-lg p-4 border border-gray-200"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {productTitle}
          </p>
          <p className="text-sm text-gray-500 truncate">
            Job ID: {job.job_id.substring(0, 8)}...
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm text-gray-900">{createdAt}</p>
            <JobStatusBadge status={job.status} />
          </div>
        </div>
      </div>
    </Link>
  );
};