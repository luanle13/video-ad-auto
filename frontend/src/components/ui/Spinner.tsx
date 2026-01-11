import React from 'react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const spinnerClasses = twMerge(
    clsx(
      'animate-spin rounded-full border-2 border-current border-t-transparent',
      sizeClasses[size],
      className
    )
  );

  return (
    <div className="flex items-center justify-center">
      <div className={spinnerClasses} role="status">
        <span className="sr-only">Loading...</span>
      </div>
    </div>
  );
};

export default Spinner;