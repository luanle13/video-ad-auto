import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import ImageUpload from './ImageUpload';
import { toast } from 'react-hot-toast';

// Define the Zod schema for validation
const productSchema = z.object({
  title: z.string()
    .min(1, 'Title is required')
    .max(100, 'Title must be less than 100 characters'),
  description: z.string()
    .min(1, 'Description is required')
    .max(500, 'Description must be less than 500 characters'),
  price: z.number()
    .positive('Price must be greater than 0')
    .min(0.01, 'Price must be greater than 0'),
});

type ProductFormData = z.infer<typeof productSchema>;

interface ProductFormProps {
  onSubmit: (data: ProductFormData & { images: File[] }) => void;
  isLoading?: boolean;
}

const ProductForm: React.FC<ProductFormProps> = ({ onSubmit, isLoading = false }) => {
  const [images, setImages] = useState<File[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    setError,
  } = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      title: '',
      description: '',
      price: 0,
    }
  });

  const onFormSubmit = (formData: ProductFormData) => {
    if (images.length === 0) {
      setError('root', {
        message: 'At least one image is required'
      });
      return;
    }

    // Combine form data with images and submit
    onSubmit({
      ...formData,
      images
    });
  };

  const handleImageChange = (files: File[]) => {
    setImages(files);
    if (files.length === 0 && errors.root?.message === 'At least one image is required') {
      setError('root', {
        message: ''
      });
    }
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
      <div className="space-y-4">
        <Input
          label="Title"
          type="text"
          placeholder="Enter product title"
          error={errors.title?.message}
          {...register('title', { 
            onChange: (e) => setValue('title', e.target.value, { shouldValidate: true })
          })}
        />

        <Input
          label="Description"
          as="textarea"
          rows={4}
          placeholder="Enter product description"
          error={errors.description?.message}
          {...register('description', { 
            onChange: (e) => setValue('description', e.target.value, { shouldValidate: true })
          })}
        />

        <Input
          label="Price ($)"
          type="number"
          step="0.01"
          placeholder="0.00"
          error={errors.price?.message}
          {...register('price', { 
            valueAsNumber: true,
            onChange: (e) => setValue('price', parseFloat(e.target.value) || 0, { shouldValidate: true })
          })}
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Images
          </label>
          <ImageUpload 
            onFilesChange={handleImageChange}
            maxFiles={5}
            maxSize={5 * 1024 * 1024} // 5MB
            acceptedTypes={['image/jpeg', 'image/png', 'image/webp']}
          />
          {errors.root?.message && (
            <p className="mt-1 text-sm text-error-600">{errors.root.message}</p>
          )}
        </div>
      </div>

      <div>
        <Button 
          type="submit" 
          variant="primary" 
          size="md"
          isLoading={isLoading}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? 'Creating Product...' : 'Create Product'}
        </Button>
      </div>
    </form>
  );
};

export default ProductForm;