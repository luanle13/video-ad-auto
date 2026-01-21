import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProducts, useCreateProduct } from '@/hooks/useProducts';
import { useCreateJob } from '@/hooks/useJobs';
import ProductForm from '@/components/products/ProductForm';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { toast } from 'react-hot-toast';
import { JobAdjustments } from '@/types';

const CreateVideoPage: React.FC = () => {
  const [mode, setMode] = useState<'select' | 'create'>('select');
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [adjustments, setAdjustments] = useState<JobAdjustments>({
    background_style: '',
    tone: '',
    emphasis: '',
    duration_preference: 30,
    additional_instructions: '',
  });
  
  const { data: products = [], isLoading: productsLoading } = useProducts();
  const { mutateAsync: createProduct, isPending: creatingProduct } = useCreateProduct();
  const { mutateAsync: createJob, isPending: creatingJob } = useCreateJob();
  const navigate = useNavigate();

  const handleAdjustmentChange = (field: keyof JobAdjustments, value: any) => {
    setAdjustments(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCreateVideo = async () => {
    try {
      let productId = selectedProductId;

      // If in create mode, create the product first
      if (mode === 'create') {
        // Note: ProductForm would handle the product creation
        // For this implementation, we'll assume the product was created
        // and the ID is available in a callback
        toast.error('Product creation mode requires form integration');
        return;
      }

      // Validate that a product is selected
      if (!productId) {
        toast.error('Please select a product');
        return;
      }

      // Create the job with adjustments
      const job = await createJob({
        productId,
        adjustments
      });

      toast.success('Video creation started successfully!');
      navigate(`/videos/${job.job_id}`);
    } catch (error) {
      console.error('Error creating video:', error);
      toast.error('Failed to create video. Please try again.');
    }
  };

  const handleProductSubmit = async (data: any) => {
    try {
      // Create the product
      const product = await createProduct(data);
      
      // Set the created product ID for job creation
      setSelectedProductId(product.product_id);
      
      // Switch to select mode to use the created product
      setMode('select');
      
      toast.success('Product created successfully!');
    } catch (error) {
      console.error('Error creating product:', error);
      toast.error('Failed to create product. Please try again.');
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Create Video</h1>
      
      {/* Mode Selection */}
      <div className="mb-8">
        <div className="flex space-x-4 border-b border-gray-200">
          <button
            type="button"
            className={`pb-3 px-1 border-b-2 font-medium text-sm ${
              mode === 'select'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setMode('select')}
          >
            Select Existing Product
          </button>
          <button
            type="button"
            className={`pb-3 px-1 border-b-2 font-medium text-sm ${
              mode === 'create'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setMode('create')}
          >
            Create New Product
          </button>
        </div>
      </div>

      {/* Product Selection/Creation */}
      <div className="mb-8">
        {mode === 'select' ? (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Product
            </label>
            {productsLoading ? (
              <div className="animate-pulse bg-gray-200 rounded h-10"></div>
            ) : (
              <select
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Select a product</option>
                {products.map(product => (
                  <option key={product.product_id} value={product.product_id}>
                    {product.title}
                  </option>
                ))}
              </select>
            )}
          </div>
        ) : (
          <div>
            <h2 className="text-lg font-medium text-gray-900 mb-4">Create New Product</h2>
            <ProductForm 
              onSubmit={handleProductSubmit} 
              isLoading={creatingProduct}
            />
          </div>
        )}
      </div>

      {/* Adjustments Section */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 mb-8">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Video Adjustments</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <Input
              label="Background Style"
              type="text"
              placeholder="e.g., modern, vintage, minimalist"
              value={adjustments.background_style}
              onChange={(e) => handleAdjustmentChange('background_style', e.target.value)}
            />
          </div>
          
          <div>
            <Input
              label="Tone"
              type="text"
              placeholder="e.g., professional, casual, energetic"
              value={adjustments.tone}
              onChange={(e) => handleAdjustmentChange('tone', e.target.value)}
            />
          </div>
          
          <div>
            <Input
              label="Emphasis"
              type="text"
              placeholder="What should be highlighted?"
              value={adjustments.emphasis}
              onChange={(e) => handleAdjustmentChange('emphasis', e.target.value)}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Duration Preference (seconds)
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="15"
                max="60"
                value={adjustments.duration_preference}
                onChange={(e) => handleAdjustmentChange('duration_preference', parseInt(e.target.value))}
                className="w-full"
              />
              <span className="text-sm font-medium text-gray-900 w-12">
                {adjustments.duration_preference}s
              </span>
            </div>
          </div>
        </div>
        
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Additional Instructions
          </label>
          <textarea
            rows={4}
            placeholder="Any specific requirements for the video..."
            value={adjustments.additional_instructions}
            onChange={(e) => handleAdjustmentChange('additional_instructions', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      {/* Submit Button */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          size="md"
          onClick={handleCreateVideo}
          disabled={creatingJob || (mode === 'select' && !selectedProductId)}
          isLoading={creatingJob}
        >
          {creatingJob ? 'Creating Video...' : 'Create Video'}
        </Button>
      </div>
    </div>
  );
};

export default CreateVideoPage;