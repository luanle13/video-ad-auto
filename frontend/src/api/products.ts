import { apiClient } from './client';
import { Product } from '@/types';

// Types
export interface CreateProductRequest {
  title: string;
  description: string;
  price: string;  // Price as string e.g., "99.99"
  image_keys: string[];
}

// Product API functions
export const getProducts = async (): Promise<Product[]> => {
  const response = await apiClient.get<Product[]>('/products');
  return response.data;
};

export const getProduct = async (productId: string): Promise<Product> => {
  const response = await apiClient.get<Product>(`/products/${productId}`);
  return response.data;
};

export const createProduct = async (data: CreateProductRequest): Promise<Product> => {
  const response = await apiClient.post<Product>('/products', data);
  return response.data;
};

export const deleteProduct = async (productId: string): Promise<void> => {
  await apiClient.delete(`/products/${productId}`);
};

export const getUploadUrl = async (
  filename: string, 
  contentType: string
): Promise<{ key: string; url: string; fields: Record<string, string> }> => {
  const response = await apiClient.post<{ key: string; url: string; fields: Record<string, string> }>(
    '/products/upload-url',
    {
      filename,
      content_type: contentType,
    }
  );
  return response.data;
};

export const uploadImage = async (
  url: string,
  fields: Record<string, string>,
  file: File
): Promise<void> => {
  const formData = new FormData();
  
  // Add all fields to form data
  Object.keys(fields).forEach(key => {
    formData.append(key, fields[key]);
  });
  
  // Add the file
  formData.append('file', file);
  
  // Upload to S3 using the presigned URL
  await fetch(url, {
    method: 'POST',
    body: formData,
  });
};