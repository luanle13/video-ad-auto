import React from 'react';
import { JobStatus } from '@/types';
import { Circle, Clock, Loader, CheckCircle, AlertCircle, Play, Mic, Video } from 'lucide-react';

interface JobStatusBadgeProps {
  status: JobStatus;
}

const JobStatusBadge: React.FC<JobStatusBadgeProps> = ({ status }) => {
  const getStatusInfo = () => {
    switch (status) {
      case JobStatus.PENDING:
        return {
          text: 'Pending',
          icon: <Clock size={14} />,
          className: 'bg-gray-100 text-gray-800',
        };
      case JobStatus.PROCESSING:
        return {
          text: 'Processing',
          icon: <Loader size={14} className="animate-spin" />,
          className: 'bg-blue-100 text-blue-800',
        };
      case JobStatus.ANALYZING:
        return {
          text: 'Analyzing',
          icon: <Circle size={14} className="animate-pulse" />,
          className: 'bg-indigo-100 text-indigo-800',
        };
      case JobStatus.SCRIPTING:
        return {
          text: 'Scripting',
          icon: <Play size={14} />,
          className: 'bg-purple-100 text-purple-800',
        };
      case JobStatus.GENERATING_TTS:
        return {
          text: 'Generating Audio',
          icon: <Mic size={14} />,
          className: 'bg-yellow-100 text-yellow-800',
        };
      case JobStatus.GENERATING_VIDEO:
        return {
          text: 'Generating Video',
          icon: <Video size={14} />,
          className: 'bg-orange-100 text-orange-800',
        };
      case JobStatus.COMPLETE:
        return {
          text: 'Complete',
          icon: <CheckCircle size={14} />,
          className: 'bg-green-100 text-green-800',
        };
      case JobStatus.FAILED:
        return {
          text: 'Failed',
          icon: <AlertCircle size={14} />,
          className: 'bg-red-100 text-red-800',
        };
      default:
        return {
          text: status,
          icon: <AlertCircle size={14} />,
          className: 'bg-gray-100 text-gray-800',
        };
    }
  };

  const { text, icon, className } = getStatusInfo();

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${className}`}>
      {icon}
      <span className="ml-1">{text}</span>
    </span>
  );
};

export default JobStatusBadge;