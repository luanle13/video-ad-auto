import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/Button';

const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full text-center">
        <div className="text-9xl font-bold text-primary-600 mb-4">404</div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Page Not Found</h1>
        <p className="text-gray-600 mb-8">
          Sorry, we couldn't find the page you're looking for.
        </p>
        <Link to="/dashboard">
          <Button variant="primary" size="md">
            Go to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default NotFoundPage;