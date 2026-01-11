import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { toast } from 'react-hot-toast';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

type Platform = 'tiktok' | 'shopee' | 'facebook';

interface CredentialFormProps {
  platform: Platform;
  isConfigured: boolean;
  onSave: (credentials: Record<string, string>) => void;
  onDelete: () => void;
  isLoading?: boolean;
}

const platformNames: Record<Platform, string> = {
  tiktok: 'TikTok',
  shopee: 'Shopee',
  facebook: 'Facebook'
};

const CredentialForm: React.FC<CredentialFormProps> = ({
  platform,
  isConfigured,
  onSave,
  onDelete,
  isLoading = false
}) => {
  const [accessToken, setAccessToken] = useState('');
  const [additionalField, setAdditionalField] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!accessToken.trim()) {
      toast.error('Access token is required');
      return;
    }

    // Prepare credentials object based on platform
    const credentials: Record<string, string> = {
      access_token: accessToken
    };

    // Add platform-specific fields
    if (platform === 'tiktok') {
      credentials.tiktok_specific_field = additionalField;
    } else if (platform === 'shopee') {
      credentials.shopee_specific_field = additionalField;
    } else if (platform === 'facebook') {
      credentials.facebook_specific_field = additionalField;
    }

    onSave(credentials);
  };

  const handleDelete = () => {
    onDelete();
  };

  const platformName = platformNames[platform];

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">{platformName} Credentials</h3>
        <div className="flex items-center">
          {isConfigured ? (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-success-100 text-success-800">
              <CheckCircle className="mr-1 h-4 w-4" />
              Configured
            </span>
          ) : (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              <XCircle className="mr-1 h-4 w-4" />
              Not Configured
            </span>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Access Token"
          type="password"
          placeholder={`Enter your ${platformName} access token`}
          value={accessToken}
          onChange={(e) => setAccessToken(e.target.value)}
          required
        />

        {/* Platform-specific additional fields */}
        {platform === 'tiktok' && (
          <Input
            label="TikTok User ID (Optional)"
            type="text"
            placeholder="Enter your TikTok User ID"
            value={additionalField}
            onChange={(e) => setAdditionalField(e.target.value)}
          />
        )}

        {platform === 'shopee' && (
          <Input
            label="Shop ID (Optional)"
            type="text"
            placeholder="Enter your Shopee Shop ID"
            value={additionalField}
            onChange={(e) => setAdditionalField(e.target.value)}
          />
        )}

        {platform === 'facebook' && (
          <Input
            label="Page ID (Optional)"
            type="text"
            placeholder="Enter your Facebook Page ID"
            value={additionalField}
            onChange={(e) => setAdditionalField(e.target.value)}
          />
        )}

        <div className="flex space-x-3 pt-2">
          <Button
            type="submit"
            variant="primary"
            size="md"
            isLoading={isLoading}
            disabled={isLoading}
          >
            {isConfigured ? 'Update' : 'Save'} Credentials
          </Button>
          
          {isConfigured && (
            <Button
              type="button"
              variant="danger"
              size="md"
              onClick={handleDelete}
              disabled={isLoading}
            >
              Delete
            </Button>
          )}
        </div>
      </form>
    </div>
  );
};

export default CredentialForm;