
import React, { useState, useCallback } from 'react';
import { uploadsService, FileUploadResponse } from '../../../services/uploads';
import { Button } from '../../../components/ui/Button';

interface FileUploadZoneProps {
  onUploadSuccess?: (result: FileUploadResponse) => void;
  onUploadError?: (error: string) => void;
}

const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onUploadSuccess,
  onUploadError
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState<FileUploadResponse | null>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!file) return;

    // Validate file type
    const validTypes = [
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];

    if (!validTypes.includes(file.type) && !file.name.match(/\.(csv|xlsx|xls)$/i)) {
      onUploadError?.('Please upload a CSV or Excel file');
      return;
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      onUploadError?.('File size must be less than 10MB');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const result = await uploadsService.uploadFile(file, (progress) => {
        setUploadProgress(progress);
      });

      setUploadResult(result);
      onUploadSuccess?.(result);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Upload failed';
      onUploadError?.(errorMessage);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [onUploadSuccess, onUploadError]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  }, [handleFile]);

  return (
    <div className="space-y-4">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${isUploading ? 'opacity-50' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {isUploading ? (
          <div className="space-y-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600">Uploading... {uploadProgress}%</p>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-4xl text-gray-400">📄</div>
            <div>
              <p className="text-lg font-medium text-gray-900">
                Drop your trade file here
              </p>
              <p className="text-gray-600">
                Supports CSV and Excel files (max 10MB)
              </p>
            </div>
            <div>
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload">
                <Button as="span" className="cursor-pointer">
                  Choose File
                </Button>
              </label>
            </div>
          </div>
        )}
      </div>

      {uploadResult && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-green-800">Upload Successful</h3>
          <div className="mt-2 text-sm text-green-700">
            <p>File: {uploadResult.filename}</p>
            <p>Size: {(uploadResult.file_size / 1024).toFixed(1)} KB</p>
            {uploadResult.rows_detected && (
              <p>Rows detected: {uploadResult.rows_detected}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploadZone;
