// API Module Index
export { apiClient } from './client';

// Auth exports
export {
  login,
  register,
  refreshToken,
  getMe,
  logout,
  saveTokens,
  getAccessToken,
  getRefreshToken,
  clearTokens,
} from './auth';

// Products exports
export {
  getProducts,
  getProduct,
  createProduct,
  deleteProduct,
  getUploadUrl,
  uploadImage,
  type CreateProductRequest,
} from './products';

// Jobs exports
export {
  getJobs,
  getJob,
  createJob,
  regenerateJob,
  getVideoDownloadUrl,
  type CreateJobRequest,
  type RegenerateJobRequest,
} from './jobs';

// Credentials exports
export {
  getCredentialsStatus,
  updateCredentials,
  deleteCredential,
  type CredentialsStatus,
} from './credentials';