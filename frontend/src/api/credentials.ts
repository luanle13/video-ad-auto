import { apiClient } from './client';

// Types
export interface CredentialsStatus {
  tiktok_configured: boolean;
  shopee_configured: boolean;
  facebook_configured: boolean;
}

// Credentials API functions
export const getCredentialsStatus = async (): Promise<CredentialsStatus> => {
  const response = await apiClient.get<CredentialsStatus>('/credentials/status');
  return response.data;
};

export const updateCredentials = async (data: any): Promise<CredentialsStatus> => {
  const response = await apiClient.post<CredentialsStatus>('/credentials', data);
  return response.data;
};

export const deleteCredential = async (platform: string): Promise<void> => {
  await apiClient.delete(`/credentials/${platform}`);
};