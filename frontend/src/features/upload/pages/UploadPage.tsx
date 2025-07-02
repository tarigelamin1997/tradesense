
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { useTradeStore } from '../../../store/trades';
import { FileUploadZone } from '../components/FileUploadZone';
import { Card, CardHeader, CardTitle, CardContent } from '../../../components/ui';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { uploadData, analyzeData, isLoading, error } = useTradeStore();
  
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [analysisStatus, setAnalysisStatus] = useState<'idle' | 'analyzing' | 'success' | 'error'>('idle');

  const handleFileUpload = async (file: File) => {
    // Validate file type
    const allowedTypes = ['.csv', '.xlsx', '.xls'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
      setUploadStatus('error');
      return;
    }

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

  return (
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
      <div className="mb-8">
        <FileUploadZone
          onFileSelect={handleFileUpload}
          isUploading={uploadStatus === 'uploading'}
          uploadProgress={uploadProgress}
          uploadStatus={uploadStatus}
          error={error}
        />

        {/* Analysis Status */}
        {analysisStatus !== 'idle' && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              {analysisStatus === 'analyzing' && (
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
              )}
              <span className="text-gray-900 font-medium">
                {analysisStatus === 'analyzing' ? 'Analyzing trade data...' : 'Analysis completed successfully!'}
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
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-amber-500 mr-2" />
            File Requirements
          </CardTitle>
        </CardHeader>
        <CardContent>
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
        </CardContent>
      </Card>
    </div>
  );
};
