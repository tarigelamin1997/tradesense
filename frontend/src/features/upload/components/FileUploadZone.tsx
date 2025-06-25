
import React, { useCallback, useState } from 'react';
import { CloudArrowUpIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { Card } from '../../../components/ui';

interface FileUploadZoneProps {
  onFileSelect: (file: File) => void;
  isUploading?: boolean;
  uploadProgress?: number;
  uploadStatus?: 'idle' | 'uploading' | 'success' | 'error';
  error?: string;
}

export const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onFileSelect,
  isUploading = false,
  uploadProgress = 0,
  uploadStatus = 'idle',
  error
}) => {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  }, [onFileSelect]);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const getStatusIcon = () => {
    switch (uploadStatus) {
      case 'success':
        return <CheckCircleIcon className="h-16 w-16 text-green-500 mx-auto mb-4" />;
      case 'error':
        return <XCircleIcon className="h-16 w-16 text-red-500 mx-auto mb-4" />;
      case 'uploading':
        return (
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
        );
      default:
        return <CloudArrowUpIcon className="mx-auto h-16 w-16 text-gray-400 mb-4" />;
    }
  };

  const getBorderColor = () => {
    if (dragActive) return 'border-blue-500 bg-blue-50';
    if (uploadStatus === 'success') return 'border-green-500 bg-green-50';
    if (uploadStatus === 'error') return 'border-red-500 bg-red-50';
    return 'border-gray-300 hover:border-gray-400';
  };

  return (
    <Card padding="lg">
      <div
        className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200 ${getBorderColor()}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {uploadStatus === 'idle' && (
          <>
            {getStatusIcon()}
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Drop your files here, or click to browse
            </h3>
            <p className="text-gray-600 mb-6">
              Supports CSV, Excel (.xlsx, .xls) files up to 10MB
            </p>
            <label className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer transition-colors">
              Choose File
              <input
                type="file"
                className="hidden"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileInput}
              />
            </label>
          </>
        )}

        {uploadStatus === 'uploading' && (
          <div className="space-y-4">
            {getStatusIcon()}
            <h3 className="text-lg font-semibold text-gray-900">
              Uploading file...
            </h3>
            <div className="max-w-md mx-auto">
              <div className="bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-600 mt-2">{uploadProgress}% complete</p>
            </div>
          </div>
        )}

        {(uploadStatus === 'success' || uploadStatus === 'error') && (
          <div className="space-y-4">
            {getStatusIcon()}
            <h3 className="text-lg font-semibold text-gray-900">
              {uploadStatus === 'success' ? 'Upload completed successfully!' : 'Upload failed'}
            </h3>
            {error && uploadStatus === 'error' && (
              <p className="text-red-600 text-sm">{error}</p>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};
