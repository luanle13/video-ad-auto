import React from 'react';
import { Job, JobStatus } from '@/types';
import { CheckCircle, Clock, Loader, Play, Mic, Video } from 'lucide-react';

interface JobProgressProps {
  job: Job;
}

export const JobProgress: React.FC<JobProgressProps> = ({ job }) => {
  const steps = [
    { status: JobStatus.PENDING, label: 'Queued', icon: Clock },
    { status: JobStatus.ANALYZING, label: 'Analyzing Product', icon: Clock },
    { status: JobStatus.SCRIPTING, label: 'Generating Script', icon: Play },
    { status: JobStatus.GENERATING_TTS, label: 'Generating Audio', icon: Mic },
    { status: JobStatus.GENERATING_VIDEO, label: 'Generating Video', icon: Video },
    { status: JobStatus.COMPLETE, label: 'Complete', icon: CheckCircle },
  ];

  // Determine the current step based on job status
  const getCurrentStepIndex = () => {
    switch (job.status) {
      case JobStatus.PENDING:
        return 0;
      case JobStatus.ANALYZING:
        return 1;
      case JobStatus.SCRIPTING:
        return 2;
      case JobStatus.GENERATING_TTS:
        return 3;
      case JobStatus.GENERATING_VIDEO:
        return 4;
      case JobStatus.COMPLETE:
        return 5;
      case JobStatus.FAILED:
        // For failed jobs, show the step where it failed
        // This would require tracking the last successful step
        return steps.findIndex(s => s.status === job.status) !== -1 
          ? steps.findIndex(s => s.status === job.status) 
          : 5; // Default to complete if not found
      default:
        return 0;
    }
  };

  const currentStepIndex = getCurrentStepIndex();
  const isFailed = job.status === JobStatus.FAILED;

  return (
    <div className="space-y-4">
      {steps.map((step, index) => {
        const isCompleted = index < currentStepIndex;
        const isCurrent = index === currentStepIndex;
        const isPending = index > currentStepIndex;
        
        // Special handling for failed jobs
        if (isFailed && index > currentStepIndex) {
          return null; // Don't show steps after failure
        }

        // Icon based on step status
        let IconComponent = step.icon;
        let iconClass = 'w-5 h-5';
        
        if (isCompleted) {
          IconComponent = CheckCircle;
          iconClass += ' text-success-500';
        } else if (isCurrent) {
          if (job.status === JobStatus.PROCESSING || 
              job.status === JobStatus.ANALYZING || 
              job.status === JobStatus.SCRIPTING || 
              job.status === JobStatus.GENERATING_TTS || 
              job.status === JobStatus.GENERATING_VIDEO) {
            IconComponent = Loader;
            iconClass += ' text-primary-500 animate-spin';
          } else {
            iconClass += ' text-primary-500';
          }
        } else {
          iconClass += ' text-gray-400';
        }

        // Text color based on step status
        let textClass = 'text-sm';
        if (isCompleted) {
          textClass += ' text-success-700';
        } else if (isCurrent) {
          textClass += ' text-primary-700 font-medium';
        } else {
          textClass += ' text-gray-500';
        }

        return (
          <div key={step.status} className="flex items-start">
            <div className={`flex-shrink-0 pt-0.5 ${isCompleted ? 'text-success-500' : isCurrent ? 'text-primary-500' : 'text-gray-400'}`}>
              <IconComponent className={iconClass} />
            </div>
            <div className="ml-3">
              <p className={textClass}>{step.label}</p>
              {isCurrent && job.status === JobStatus.FAILED && (
                <p className="text-sm text-error-600 mt-1">
                  {job.error_message || 'An error occurred during this step'}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};