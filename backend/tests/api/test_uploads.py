"""
File upload API endpoint tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import io
import tempfile
import os
from backend.core.security import SecurityManager
from backend.models.user import User
from fastapi import HTTPException


class TestUploadsAPI:
    """Test file upload endpoints"""

    def test_upload_csv_success(self, client, auth_headers, mock_file_upload, test_db, test_user):
        """Test successful CSV file upload"""
        from backend.models.user import User
        user = test_db.query(User).filter(User.id == "test_user_123").first()
        print(f"[DEBUG][test_upload_csv_success] User in DB at test start: {user}")
        with patch('backend.api.v1.uploads.service.UploadService.process_file_upload') as mock_process:
            mock_process.return_value = {
                "success": True,
                "filename": "test.csv",
                "rows": 2,
                "columns": ["symbol", "entry_price", "exit_price"],
                "data_preview": [
                    {"symbol": "AAPL", "entry_price": 150.0, "exit_price": 155.0},
                    {"symbol": "GOOGL", "entry_price": 2800.0, "exit_price": 2850.0}
                ],
                "message": "File uploaded and processed successfully",
                "upload_id": "upload-123"
            }
            
            files = {"file": ("test.csv", mock_file_upload, "text/csv")}
            response = client.post("/api/v1/uploads/", files=files, headers=auth_headers)
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["filename"] == "test.csv"
            assert data["upload_id"] == "upload-123"
            assert data["rows"] == 2

    def test_upload_excel_success(self, client, auth_headers):
        """Test successful Excel file upload"""
        # Create mock Excel file content
        excel_content = b"mock_excel_content"
        
        with patch('backend.api.v1.uploads.service.UploadService.process_file_upload') as mock_process:
            mock_process.return_value = {
                "success": True,
                "filename": "test.xlsx",
                "rows": 5,
                "columns": ["symbol", "entry_price", "exit_price", "pnl"],
                "data_preview": [
                    {"symbol": "AAPL", "entry_price": 150.0, "exit_price": 155.0, "pnl": 50.0},
                    {"symbol": "GOOGL", "entry_price": 2800.0, "exit_price": 2850.0, "pnl": 500.0}
                ],
                "message": "File uploaded and processed successfully",
                "upload_id": "upload-456"
            }
            
            response = client.post(
                "/api/v1/uploads/",
                files={"file": ("test.xlsx", io.BytesIO(excel_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["filename"] == "test.xlsx"
            assert data["upload_id"] == "upload-456"
            assert data["rows"] == 5

    def test_upload_unauthorized(self, client, mock_file_upload):
        """Test file upload without authentication"""
        files = {"file": ("test.csv", mock_file_upload, "text/csv")}
        response = client.post("/api/v1/uploads/", files=files)
        assert response.status_code == 401

    def test_upload_unsupported_file_type(self, client, auth_headers):
        """Test upload of unsupported file type"""
        txt_content = b"This is a text file"
        
        response = client.post(
            "/api/v1/uploads/",
            files={"file": ("test.txt", io.BytesIO(txt_content), "text/plain")},
            headers=auth_headers
        )
        
        assert response.status_code == 400

    def test_upload_file_too_large(self, client, auth_headers):
        """Test upload of file that's too large"""
        # Create a large mock file
        large_content = b"x" * (20 * 1024 * 1024)  # 20MB

        # Mock the service to return a file too large error
        with patch('backend.api.v1.uploads.service.UploadService.process_file_upload') as mock_process:
            mock_process.side_effect = HTTPException(status_code=413, detail="File too large")
            response = client.post(
                "/api/v1/uploads/",
                files={"file": ("large.csv", io.BytesIO(large_content), "text/csv")},
                headers=auth_headers
            )
            
            assert response.status_code == 413  # Request Entity Too Large

    def test_upload_empty_file(self, client, auth_headers):
        """Test upload of empty file"""
        response = client.post(
            "/api/v1/uploads/",
            files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
            headers=auth_headers
        )
        
        assert response.status_code == 400

    def test_upload_malformed_csv(self, client, auth_headers):
        """Test upload of malformed CSV file"""
        malformed_csv = b"symbol,entry_time,quantity\nAAPL,invalid_date,not_a_number"
        
        with patch('backend.api.v1.uploads.service.UploadService.process_file_upload') as mock_process:
            mock_process.return_value = {
                "success": False,
                "filename": "malformed.csv",
                "rows": 0,
                "columns": ["symbol", "entry_time", "quantity"],
                "data_preview": [],
                "message": "File format error: Unable to parse CSV",
                "upload_id": "upload-malformed"
            }
            
            response = client.post(
                "/api/v1/uploads/",
                files={"file": ("malformed.csv", io.BytesIO(malformed_csv), "text/csv")},
                headers=auth_headers
            )
            
            assert response.status_code == 400

    def test_get_upload_status(self, client, auth_headers):
        """Test getting upload status by ID"""
        upload_id = "upload-123"
        
        with patch('backend.api.v1.uploads.service.UploadService.get_upload_status') as mock_get_status:
            mock_get_status.return_value = {
                "id": upload_id,
                "filename": "test.csv",
                "status": "completed",
                "records_processed": 100,
                "records_imported": 95,
                "created_at": "2024-01-15T10:00:00Z",
                "completed_at": "2024-01-15T10:05:00Z"
            }
            
            response = client.get(f"/api/v1/uploads/{upload_id}/status", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "completed"
            assert data["data"]["records_processed"] == 100

    def test_get_upload_status_not_found(self, client, auth_headers):
        """Test getting status for non-existent upload"""
        upload_id = "nonexistent-upload"
        
        with patch('backend.api.v1.uploads.service.UploadService.get_upload_status') as mock_get_status:
            mock_get_status.return_value = None
            
            response = client.get(f"/api/v1/uploads/{upload_id}/status", headers=auth_headers)
            
            assert response.status_code == 404

    def test_list_uploads(self, client, auth_headers):
        """Test listing user uploads"""
        with patch('backend.api.v1.uploads.service.UploadService.get_user_uploads') as mock_list:
            mock_list.return_value = [
                {
                    "id": "upload-1",
                    "filename": "trades_jan.csv",
                    "status": "completed",
                    "records_imported": 50,
                    "created_at": "2024-01-15T10:00:00Z"
                },
                {
                    "id": "upload-2",
                    "filename": "trades_feb.csv",
                    "status": "processing",
                    "records_imported": 0,
                    "created_at": "2024-02-01T09:00:00Z"
                }
            ]
            
            response = client.get("/api/v1/uploads/", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 2
            assert data["data"][0]["filename"] == "trades_jan.csv"

    def test_delete_upload(self, client, auth_headers):
        """Test deleting an upload"""
        upload_id = "upload-123"
        
        with patch('backend.api.v1.uploads.service.UploadService.delete_upload') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete(f"/api/v1/uploads/{upload_id}", headers=auth_headers)
            
            assert response.status_code == 204

    def test_delete_upload_not_found(self, client, auth_headers):
        """Test deleting non-existent upload"""
        upload_id = "nonexistent-upload"
        
        with patch('backend.api.v1.uploads.service.UploadService.delete_upload') as mock_delete:
            mock_delete.return_value = False
            
            response = client.delete(f"/api/v1/uploads/{upload_id}", headers=auth_headers)
            
            assert response.status_code == 404


class TestUploadValidation:
    """Test file upload validation"""

    def test_validate_csv_headers(self, client, auth_headers):
        """Test CSV header validation"""
        csv_with_wrong_headers = b"wrong_col1,wrong_col2\nvalue1,value2"
        
        with patch('backend.api.v1.uploads.service.UploadService.process_file_upload') as mock_process:
            mock_process.return_value = {
                "success": False,
                "error": "Missing required columns: symbol, entry_time, quantity",
                "required_columns": ["symbol", "entry_time", "quantity", "entry_price"]
            }
            
            response = client.post(
                "/api/v1/uploads/",
                files={"file": ("wrong_headers.csv", io.BytesIO(csv_with_wrong_headers), "text/csv")},
                headers=auth_headers
            )
            
            assert response.status_code == 400

    def test_validate_data_types(self, client, auth_headers):
        """Test data type validation during upload"""
        csv_with_wrong_types = b"symbol,entry_time,quantity,entry_price\nAAPL,not_a_date,not_a_number,not_a_price"
        
        with patch('backend.api.v1.uploads.service.UploadService.process_file_upload') as mock_process:
            mock_process.return_value = {
                "success": True,
                "filename": "wrong_types.csv",
                "rows": 1,
                "columns": ["symbol", "entry_time", "quantity", "entry_price"],
                "data_preview": [
                    {"symbol": "AAPL", "entry_time": "not_a_date", "quantity": "not_a_number", "entry_price": "not_a_price"}
                ],
                "message": "File uploaded with validation errors",
                "upload_id": "upload-wrong-types",
                "errors": [
                    "Row 1: Invalid date format for entry_time",
                    "Row 1: Invalid numeric value for quantity",
                    "Row 1: Invalid numeric value for entry_price"
                ]
            }
            
            response = client.post(
                "/api/v1/uploads/",
                files={"file": ("wrong_types.csv", io.BytesIO(csv_with_wrong_types), "text/csv")},
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["filename"] == "wrong_types.csv"
            assert data["upload_id"] == "upload-wrong-types"


@pytest.mark.integration
class TestUploadIntegration:
    """Integration tests for upload workflow"""

    def test_complete_upload_workflow(self, client, auth_headers, mock_file_upload):
        """Test complete upload workflow: upload -> check status -> list -> delete"""
        upload_id = "workflow-upload-123"
        
        with patch('backend.api.v1.uploads.service.UploadService.process_file_upload') as mock_process, \
             patch('backend.api.v1.uploads.service.UploadService.get_upload_status') as mock_get_status, \
             patch('backend.api.v1.uploads.service.UploadService.get_user_uploads') as mock_list, \
             patch('backend.api.v1.uploads.service.UploadService.delete_upload') as mock_delete:
            
            # 1. Upload file
            mock_process.return_value = {
                "success": True,
                "filename": "test.csv",
                "rows": 2,
                "columns": ["symbol", "entry_price", "exit_price"],
                "data_preview": [
                    {"symbol": "AAPL", "entry_price": 150.0, "exit_price": 155.0},
                    {"symbol": "GOOGL", "entry_price": 2800.0, "exit_price": 2850.0}
                ],
                "message": "File uploaded and processed successfully",
                "upload_id": upload_id
            }
            
            files = {"file": ("test.csv", mock_file_upload, "text/csv")}
            upload_response = client.post("/api/v1/uploads/", files=files, headers=auth_headers)
            assert upload_response.status_code == 201
            
            # 2. Check status
            mock_get_status.return_value = {
                "id": upload_id,
                "status": "completed",
                "records_imported": 2
            }
            
            status_response = client.get(f"/api/v1/uploads/{upload_id}/status", headers=auth_headers)
            assert status_response.status_code == 200
            
            # 3. List uploads
            mock_list.return_value = [{"id": upload_id, "filename": "test.csv"}]
            
            list_response = client.get("/api/v1/uploads/", headers=auth_headers)
            assert list_response.status_code == 200
            
            # 4. Delete upload
            mock_delete.return_value = True
            
            delete_response = client.delete(f"/api/v1/uploads/{upload_id}", headers=auth_headers)
            assert delete_response.status_code == 204


@pytest.fixture
def auth_headers():
    token = SecurityManager.create_access_token(data={"user_id": "test_user_123", "email": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_file_upload():
    return io.BytesIO(b"mock file content")
