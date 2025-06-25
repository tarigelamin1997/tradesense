
"""
Uploads router - handles file upload and data processing endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Dict, Any, Optional
import logging

from backend.api.v1.uploads.schemas import (
    FileUploadResponse,
    DataValidationResult,
    ColumnMappingRequest,
    BulkImportResponse
)
from backend.api.v1.uploads.service import UploadsService
from backend.core.security import get_current_active_user
from backend.core.response import ResponseHandler, APIResponse
from backend.core.exceptions import TradeSenseException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["File Uploads"])
uploads_service = UploadsService()


@router.post("/", response_model=FileUploadResponse, summary="Upload File")
async def upload_file(
    file: UploadFile = File(..., description="CSV or Excel file containing trade data"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> FileUploadResponse:
    """
    Upload a trade data file (CSV or Excel)
    
    Accepts CSV and Excel files with trade data. Returns upload metadata and data preview.
    
    **Supported formats:**
    - CSV (.csv)
    - Excel (.xlsx, .xls)
    
    **Maximum file size:** 10MB
    """
    try:
        return await uploads_service.process_file_upload(current_user["user_id"], file)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Upload endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{upload_id}/validate", response_model=DataValidationResult, summary="Validate Upload Data")
async def validate_upload(
    upload_id: str,
    column_mapping: Optional[Dict[str, str]] = None,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> DataValidationResult:
    """
    Validate uploaded data structure and content
    
    - **upload_id**: Upload identifier from file upload
    - **column_mapping**: Optional mapping of file columns to standard fields
    
    Returns validation results with errors and warnings
    """
    try:
        return await uploads_service.validate_data(upload_id, column_mapping)
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Validation endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{upload_id}/import", response_model=BulkImportResponse, summary="Import Trade Data")
async def import_trades(
    upload_id: str,
    column_mapping: Optional[Dict[str, str]] = None,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> BulkImportResponse:
    """
    Import validated trade data into the system
    
    - **upload_id**: Upload identifier from file upload
    - **column_mapping**: Optional mapping of file columns to standard fields
    
    Processes and imports all valid trade records
    """
    try:
        return await uploads_service.import_trades(
            current_user["user_id"], 
            upload_id, 
            column_mapping
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Import endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{upload_id}/status", response_model=APIResponse, summary="Get Upload Status")
async def get_upload_status(
    upload_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> APIResponse:
    """
    Get status and metadata for an upload
    
    Returns upload information including processing status and file details
    """
    try:
        result = await uploads_service.get_upload_status(current_user["user_id"], upload_id)
        return ResponseHandler.success(
            data=result,
            message="Upload status retrieved successfully"
        )
    except TradeSenseException:
        raise
    except Exception as e:
        logger.error(f"Upload status endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=APIResponse, summary="Get User Uploads")
async def get_user_uploads(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> APIResponse:
    """
    Get list of user's uploads
    
    Returns all uploads for the current user with their status
    """
    try:
        # In production, this would query the database
        # For now, return mock data
        uploads = [
            {
                "upload_id": "demo_upload_001",
                "filename": "sample_trades.csv",
                "uploaded_at": "2024-01-15T10:30:00Z",
                "processed": True,
                "rows": 150
            }
        ]
        
        return ResponseHandler.success(
            data={"uploads": uploads},
            message="User uploads retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Get uploads endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
