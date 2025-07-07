
import { apiClient } from './api';

export interface FileUploadResponse {
  upload_id: string;
  filename: string;
  file_size: number;
  rows_detected?: number;
  columns_detected?: string[];
  preview_data?: any[];
  message: string;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  suggested_mapping?: Record<string, string>;
}

export interface ImportResult {
  success: boolean;
  imported_count: number;
  failed_count: number;
  errors?: string[];
  message: string;
}

class UploadsService {
  async uploadFile(
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.uploadFile<FileUploadResponse>(
      '/api/v1/uploads/',
      formData,
      onProgress
    );
    return response.data;
  }

  async validateUpload(
    uploadId: string,
    columnMapping?: Record<string, string>
  ): Promise<ValidationResult> {
    const response = await apiClient.post<ValidationResult>(
      `/api/v1/uploads/${uploadId}/validate`,
      { column_mapping: columnMapping }
    );
    return response.data;
  }

  async importTrades(
    uploadId: string,
    columnMapping?: Record<string, string>
  ): Promise<ImportResult> {
    const response = await apiClient.post<ImportResult>(
      `/api/v1/uploads/${uploadId}/import`,
      { column_mapping: columnMapping }
    );
    return response.data;
  }

  async getUploadStatus(uploadId: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/uploads/${uploadId}/status`);
    return response.data;
  }

  async getUserUploads(): Promise<any[]> {
    const response = await apiClient.get('/api/v1/uploads/');
    return response.data.data.uploads;
  }
}

export const uploadsService = new UploadsService();
