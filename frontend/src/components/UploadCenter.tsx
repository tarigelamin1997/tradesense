import React, { useState, useRef, useCallback } from 'react';
import { uploadsService, FileUploadResponse, ValidationResult, ImportResult } from '../services/uploads';
import { 
  Upload, 
  FileSpreadsheet, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Loader,
  FileText,
  Download,
  Trash2
} from 'lucide-react';

interface UploadStatus {
  stage: 'idle' | 'uploading' | 'validating' | 'mapping' | 'importing' | 'complete' | 'error';
  progress: number;
  message: string;
}

interface ColumnMapping {
  [key: string]: string;
}

const REQUIRED_COLUMNS = ['symbol', 'direction', 'quantity', 'entry_price', 'entry_time'];
const OPTIONAL_COLUMNS = ['exit_price', 'exit_time', 'strategy_tag', 'notes', 'tags'];

function UploadCenter() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ 
    stage: 'idle', 
    progress: 0, 
    message: '' 
  });
  const [uploadResponse, setUploadResponse] = useState<FileUploadResponse | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [columnMapping, setColumnMapping] = useState<ColumnMapping>({});
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus({ stage: 'idle', progress: 0, message: '' });
      setUploadResponse(null);
      setValidationResult(null);
      setImportResult(null);
    }
  };

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && (file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.json'))) {
      setSelectedFile(file);
      setUploadStatus({ stage: 'idle', progress: 0, message: '' });
      setUploadResponse(null);
      setValidationResult(null);
      setImportResult(null);
    }
  }, []);

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploadStatus({ stage: 'uploading', progress: 0, message: 'Uploading file...' });
      
      const response = await uploadsService.uploadFile(selectedFile, (progress) => {
        setUploadStatus(prev => ({ ...prev, progress }));
      });
      
      setUploadResponse(response);
      setUploadStatus({ stage: 'validating', progress: 100, message: 'Validating file...' });
      
      // Auto-validate after upload
      const validation = await uploadsService.validateUpload(response.upload_id);
      setValidationResult(validation);
      
      if (validation.is_valid) {
        setUploadStatus({ stage: 'mapping', progress: 100, message: 'File validated successfully!' });
        if (validation.suggested_mapping) {
          setColumnMapping(validation.suggested_mapping);
        }
      } else {
        setUploadStatus({ 
          stage: 'error', 
          progress: 100, 
          message: 'Validation failed. Please check the errors below.' 
        });
      }
    } catch (error: any) {
      setUploadStatus({ 
        stage: 'error', 
        progress: 0, 
        message: error.message || 'Upload failed' 
      });
    }
  };

  const handleImport = async () => {
    if (!uploadResponse) return;

    try {
      setUploadStatus({ stage: 'importing', progress: 0, message: 'Importing trades...' });
      
      const result = await uploadsService.importTrades(uploadResponse.upload_id, columnMapping);
      setImportResult(result);
      
      if (result.success) {
        setUploadStatus({ 
          stage: 'complete', 
          progress: 100, 
          message: `Successfully imported ${result.imported_count} trades!` 
        });
      } else {
        setUploadStatus({ 
          stage: 'error', 
          progress: 100, 
          message: result.message || 'Import failed' 
        });
      }
    } catch (error: any) {
      setUploadStatus({ 
        stage: 'error', 
        progress: 0, 
        message: error.message || 'Import failed' 
      });
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setUploadStatus({ stage: 'idle', progress: 0, message: '' });
    setUploadResponse(null);
    setValidationResult(null);
    setImportResult(null);
    setColumnMapping({});
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
        <Upload className="w-6 h-6 mr-2" />
        Upload Center
      </h1>

      {/* File Upload Area */}
      {uploadStatus.stage === 'idle' && (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.json"
            onChange={handleFileSelect}
            className="hidden"
            id="file-input"
          />
          
          <FileSpreadsheet className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          
          {selectedFile ? (
            <div className="mb-4">
              <p className="text-lg font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</p>
            </div>
          ) : (
            <div className="mb-4">
              <p className="text-lg text-gray-700">Drop your file here or</p>
              <label
                htmlFor="file-input"
                className="text-blue-600 hover:text-blue-700 cursor-pointer font-medium"
              >
                browse files
              </label>
            </div>
          )}
          
          <p className="text-sm text-gray-500 mb-6">
            Supported formats: CSV, Excel (.xlsx), JSON
          </p>
          
          {selectedFile && (
            <div className="flex justify-center space-x-4">
              <button
                onClick={handleUpload}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Upload File
              </button>
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      )}

      {/* Upload Progress */}
      {uploadStatus.stage !== 'idle' && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              {uploadStatus.stage === 'uploading' || uploadStatus.stage === 'validating' || uploadStatus.stage === 'importing' ? (
                <Loader className="w-5 h-5 text-blue-600 animate-spin mr-2" />
              ) : uploadStatus.stage === 'complete' ? (
                <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              ) : uploadStatus.stage === 'error' ? (
                <XCircle className="w-5 h-5 text-red-600 mr-2" />
              ) : (
                <AlertCircle className="w-5 h-5 text-yellow-600 mr-2" />
              )}
              <span className="font-medium">{uploadStatus.message}</span>
            </div>
            {uploadStatus.stage === 'complete' || uploadStatus.stage === 'error' ? (
              <button
                onClick={handleReset}
                className="text-gray-500 hover:text-gray-700"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            ) : null}
          </div>
          
          {uploadStatus.stage === 'uploading' && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadStatus.progress}%` }}
              />
            </div>
          )}
        </div>
      )}

      {/* File Preview */}
      {uploadResponse && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">File Preview</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Filename:</span>
              <p className="font-medium">{uploadResponse.filename}</p>
            </div>
            <div>
              <span className="text-gray-500">Size:</span>
              <p className="font-medium">{formatFileSize(uploadResponse.file_size)}</p>
            </div>
            <div>
              <span className="text-gray-500">Rows:</span>
              <p className="font-medium">{uploadResponse.rows_detected || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-500">Columns:</span>
              <p className="font-medium">{uploadResponse.columns_detected?.length || 'N/A'}</p>
            </div>
          </div>
          
          {uploadResponse.columns_detected && (
            <div className="mt-4">
              <p className="text-sm text-gray-500 mb-2">Detected columns:</p>
              <div className="flex flex-wrap gap-2">
                {uploadResponse.columns_detected.map((col) => (
                  <span key={col} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                    {col}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Validation Results */}
      {validationResult && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            {validationResult.is_valid ? (
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600 mr-2" />
            )}
            Validation {validationResult.is_valid ? 'Passed' : 'Failed'}
          </h3>
          
          {validationResult.errors.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-medium text-red-600 mb-2">Errors:</p>
              <ul className="list-disc list-inside space-y-1">
                {validationResult.errors.map((error, idx) => (
                  <li key={idx} className="text-sm text-red-600">{error}</li>
                ))}
              </ul>
            </div>
          )}
          
          {validationResult.warnings.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-medium text-yellow-600 mb-2">Warnings:</p>
              <ul className="list-disc list-inside space-y-1">
                {validationResult.warnings.map((warning, idx) => (
                  <li key={idx} className="text-sm text-yellow-600">{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Column Mapping */}
      {uploadStatus.stage === 'mapping' && uploadResponse?.columns_detected && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Column Mapping</h3>
          <p className="text-sm text-gray-600 mb-4">
            Map your file columns to the required trade fields:
          </p>
          
          <div className="space-y-3">
            {[...REQUIRED_COLUMNS, ...OPTIONAL_COLUMNS].map((field) => (
              <div key={field} className="flex items-center space-x-4">
                <label className="w-32 text-sm font-medium text-gray-700">
                  {field.replace(/_/g, ' ').charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ')}
                  {REQUIRED_COLUMNS.includes(field) && <span className="text-red-500">*</span>}
                </label>
                <select
                  value={columnMapping[field] || ''}
                  onChange={(e) => setColumnMapping({ ...columnMapping, [field]: e.target.value })}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">-- Select Column --</option>
                  {uploadResponse.columns_detected.map((col) => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          
          <div className="mt-6 flex space-x-4">
            <button
              onClick={handleImport}
              disabled={!REQUIRED_COLUMNS.every(field => columnMapping[field])}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              Import Trades
            </button>
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Import Results */}
      {importResult && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            {importResult.success ? (
              <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
            ) : (
              <XCircle className="w-5 h-5 text-red-600 mr-2" />
            )}
            Import {importResult.success ? 'Complete' : 'Failed'}
          </h3>
          
          <div className="grid grid-cols-2 gap-4 text-sm mb-4">
            <div>
              <span className="text-gray-500">Imported:</span>
              <p className="font-medium text-green-600">{importResult.imported_count} trades</p>
            </div>
            <div>
              <span className="text-gray-500">Failed:</span>
              <p className="font-medium text-red-600">{importResult.failed_count} trades</p>
            </div>
          </div>
          
          {importResult.errors && importResult.errors.length > 0 && (
            <div>
              <p className="text-sm font-medium text-red-600 mb-2">Errors:</p>
              <ul className="list-disc list-inside space-y-1">
                {importResult.errors.slice(0, 5).map((error, idx) => (
                  <li key={idx} className="text-sm text-red-600">{error}</li>
                ))}
              </ul>
              {importResult.errors.length > 5 && (
                <p className="text-sm text-gray-500 mt-2">
                  And {importResult.errors.length - 5} more errors...
                </p>
              )}
            </div>
          )}
          
          <div className="mt-6">
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Upload Another File
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default UploadCenter;