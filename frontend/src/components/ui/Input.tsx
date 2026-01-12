import React from 'react';
import clsx from 'clsx';
import { twMerge } from 'tailwind-merge';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  register?: any; // This would typically be FieldRegister from react-hook-form
}

const Input: React.FC<InputProps> = ({ 
  label, 
  error, 
  className = '', 
  type = 'text', 
  placeholder, 
  register,
  ...inputProps 
}) => {
  const inputClasses = twMerge(clsx(
    'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200',
    {
      'border-gray-300': !error,
      'border-error-500 focus:ring-error-500 focus:border-error-500': error,
    },
    className
  ));

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputProps.id} className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <input
        type={type}
        placeholder={placeholder}
        className={inputClasses}
        {...(register ? register : {})}
        {...inputProps}
      />
      {error && <p className="mt-1 text-sm text-error-600">{error}</p>}
    </div>
  );
};

export { Input };