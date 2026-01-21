import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { X, Upload } from 'lucide-react';
import { toast } from 'react-hot-toast';

interface ImageUploadProps {
  onFilesChange: (files: File[]) => void;
  maxFiles?: number;
  maxSize?: number; // in bytes
  acceptedTypes?: string[];
}

const ImageUpload: React.FC<ImageUploadProps> = ({
  onFilesChange,
  maxFiles = 5,
  maxSize = 5 * 1024 * 1024, // 5MB
  acceptedTypes = ['image/jpeg', 'image/png', 'image/webp']
}) => {
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);

  const onDrop = useCallback((acceptedFiles: File[], fileRejections: any[]) => {
    // Handle rejected files
    fileRejections.forEach(({ file, errors }) => {
      errors.forEach((e: any) => {
        if (e.code === 'file-too-large') {
          toast.error(`File ${file.name} is too large. Maximum size is 5MB.`);
        } else if (e.code === 'file-invalid-type') {
          toast.error(`File ${file.name} has invalid type. Only JPEG, PNG, and WebP are allowed.`);
        } else {
          toast.error(`File ${file.name} has an error: ${e.message}`);
        }
      });
    });

    // Process accepted files
    const validFiles = acceptedFiles.filter(file => {
      if (file.size > maxSize) {
        toast.error(`${file.name} exceeds 5MB limit.`);
        return false;
      }
      if (!acceptedTypes.includes(file.type)) {
        toast.error(`${file.name} has unsupported type. Only JPEG, PNG, and WebP are allowed.`);
        return false;
      }
      return true;
    });

    // Check if adding new files would exceed maxFiles
    if (files.length + validFiles.length > maxFiles) {
      const remainingSlots = maxFiles - files.length;
      if (remainingSlots > 0) {
        validFiles.splice(remainingSlots);
        toast.error(`Maximum ${maxFiles} files allowed. Only ${remainingSlots} more file(s) added.`);
      } else {
        toast.error(`Maximum ${maxFiles} files already selected.`);
        return;
      }
    }

    // Add valid files
    const newFiles = [...files, ...validFiles];
    setFiles(newFiles);

    // Generate previews for new files
    const newPreviews = validFiles.map(file => URL.createObjectURL(file));
    setPreviews(prev => [...prev, ...newPreviews]);

    // Notify parent component
    onFilesChange(newFiles);
  }, [files, maxSize, acceptedTypes, onFilesChange]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp']
    },
    maxFiles: maxFiles,
    maxSize: maxSize,
    multiple: true
  });

  const removeFile = (index: number) => {
    const newFiles = files.filter((_, i) => i !== index);
    setFiles(newFiles);

    // Revoke the preview URL to free memory
    URL.revokeObjectURL(previews[index]);
    const newPreviews = previews.filter((_, i) => i !== index);
    setPreviews(newPreviews);

    onFilesChange(newFiles);
  };

  return (
    <div className="space-y-4">
      {/* Dropzone Area */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          isDragActive 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-primary-400'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center">
          <Upload className="w-10 h-10 text-gray-400 mb-2" />
          <p className="text-sm text-gray-600">
            {isDragActive 
              ? 'Drop the images here...' 
              : 'Drag & drop images here, or click to select'}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Support: JPEG, PNG, WebP. Max 5MB each. Up to {maxFiles} files.
          </p>
        </div>
      </div>

      {/* Preview Grid */}
      {previews.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {previews.map((preview, index) => (
            <div key={index} className="relative group">
              <img
                src={preview}
                alt={`Preview ${index + 1}`}
                className="w-full h-32 object-cover rounded-lg border border-gray-200"
              />
              <button
                type="button"
                onClick={() => removeFile(index)}
                className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                aria-label="Remove image"
              >
                <X size={14} />
              </button>
              <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1 text-center">
                {files[index].name}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* File Count */}
      {files.length > 0 && (
        <div className="text-sm text-gray-600">
          {files.length} of {maxFiles} images selected
        </div>
      )}
    </div>
  );
};

export default ImageUpload;