
import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDataStore } from '../stores/dataStore';
import {
  CloudArrowUpIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const UploadData = () => {
  const navigate = useNavigate();
  const { uploadData, analyzeData, isLoading, error } = useDataStore();
  
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [analysisStatus, setAnalysisStatus] = useState<'idle' | 'analyzing' | 'success' | 'error'>('idle');
  const [uploadedFileName, setUploadedFileName] = useState('');

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
      handleFileUpload(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    // Validate file type
    const allowedTypes = ['.csv', '.xlsx', '.xls'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
      setUploadStatus('error');
      return;
    }

    setUploadedFileName(file.name);
    setUploadStatus('uploading');
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const result = await uploadData(formData, (progress) => {
        setUploadProgress(progress);
      });

      setUploadStatus('success');
      
      // Automatically start analysis
      if (result.success && result.data) {
        setAnalysisStatus('analyzing');
        await analyzeData(result.data);
        setAnalysisStatus('success');
        
        // Navigate to dashboard after successful analysis
        setTimeout(() => {
          navigate('/dashboard');
        }, 2000);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadStatus('error');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="h-6 w-6 text-green-500" />;
      case 'error':
        return <XCircleIcon className="h-6 w-6 text-red-500" />;
      case 'uploading':
      case 'analyzing':
        return (
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
        );
      default:
        return null;
    }
  };

  const getStatusMessage = (status: string, type: 'upload' | 'analysis') => {
    const action = type === 'upload' ? 'Upload' : 'Analysis';
    
    switch (status) {
      case 'uploading':
        return `Uploading ${uploadedFileName}...`;
      case 'analyzing':
        return 'Analyzing trade data...';
      case 'success':
        return `${action} completed successfully!`;
      case 'error':
        return `${action} failed. Please try again.`;
      default:
        return '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Upload Your Trading Data
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Import your trade history to unlock powerful analytics and insights that will transform your trading performance.
          </p>
        </div>

        {/* Upload Area */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <div
            className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200 ${
              dragActive
                ? 'border-blue-500 bg-blue-50'
                : uploadStatus === 'success'
                ? 'border-green-500 bg-green-50'
                : uploadStatus === 'error'
                ? 'border-red-500 bg-red-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {uploadStatus === 'idle' && (
              <>
                <CloudArrowUpIcon className="mx-auto h-16 w-16 text-gray-400 mb-4" />
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
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto"></div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Uploading {uploadedFileName}
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
                {getStatusIcon(uploadStatus)}
                <h3 className="text-lg font-semibold text-gray-900">
                  {getStatusMessage(uploadStatus, 'upload')}
                </h3>
                {uploadStatus === 'error' && error && (
                  <p className="text-red-600 text-sm">{error}</p>
                )}
              </div>
            )}
          </div>

          {/* Analysis Status */}
          {analysisStatus !== 'idle' && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                {getStatusIcon(analysisStatus)}
                <span className="text-gray-900 font-medium">
                  {getStatusMessage(analysisStatus, 'analysis')}
                </span>
              </div>
              {analysisStatus === 'success' && (
                <p className="text-green-600 text-sm mt-2">
                  Redirecting to dashboard in a few seconds...
                </p>
              )}
            </div>
          )}
        </div>

        {/* File Requirements */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-amber-500 mr-2" />
            File Requirements
          </h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Required Columns</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Symbol (e.g., ES, NQ, AAPL)</li>
                <li>• Entry Time/Date</li>
                <li>• Exit Time/Date</li>
                <li>• Direction (Long/Short)</li>
                <li>• Quantity</li>
                <li>• Entry Price</li>
                <li>• Exit Price</li>
                <li>• P&L (Profit/Loss)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Supported Formats</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• CSV files (.csv)</li>
                <li>• Excel files (.xlsx, .xls)</li>
                <li>• Maximum file size: 10MB</li>
                <li>• UTF-8 encoding recommended</li>
              </ul>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">Pro Tip</h4>
            <p className="text-blue-800 text-sm">
              For best results, ensure your data is clean and properly formatted. 
              Our system will automatically detect and map common column names from popular trading platforms.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadData;
