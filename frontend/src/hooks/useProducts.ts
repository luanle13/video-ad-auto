import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getProducts as getProductsApi,
  getProduct as getProductApi,
  createProduct as createProductApi,
  deleteProduct as deleteProductApi,
  getUploadUrl,
  uploadImage,
} from '@/api/products';
import { Product } from '@/types';

export const useProducts = () => {
  return useQuery<Product[]>({
    queryKey: ['products'],
    queryFn: getProductsApi,
  });
};

export const useProduct = (id: string) => {
  return useQuery<Product>({
    queryKey: ['product', id],
    queryFn: () => getProductApi(id),
    enabled: !!id,
  });
};

// Input type for product creation from the form
interface CreateProductInput {
  title: string;
  description: string;
  price: number;
  images: File[];
}

export const useCreateProduct = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateProductInput): Promise<Product> => {
      // Step 1: Upload all images to S3
      const imageKeys: string[] = [];

      for (const file of data.images) {
        // Get presigned URL for this image
        const uploadData = await getUploadUrl(file.name, file.type);

        // Upload the file to S3
        await uploadImage(uploadData.url, uploadData.fields, file);

        // Store the S3 key
        imageKeys.push(uploadData.key);
      }

      // Step 2: Create the product with S3 keys
      return createProductApi({
        title: data.title,
        description: data.description,
        price: data.price.toString(), // Convert number to string
        image_keys: imageKeys,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
};

export const useDeleteProduct = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => deleteProductApi(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
};