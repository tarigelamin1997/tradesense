
"""
Upload schemas for file upload and data processing
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class FileUploadResponse(BaseModel):
    """File upload response schema"""
    success: bool = Field(..., description="Upload success status")
    filename: str = Field(..., description="Uploaded filename")
    rows: int = Field(..., description="Number of rows processed")
    columns: List[str] = Field(..., description="Column names found")
    data_preview: List[Dict[str, Any]] = Field(..., description="First few rows of data")
    message: str = Field(..., description="Upload status message")
    upload_id: str = Field(..., description="Unique upload identifier")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "filename": "trades_2024.csv",
                "rows": 150,
                "columns": ["symbol", "pnl", "entry_time", "exit_time"],
                "data_preview": [
                    {"symbol": "ES", "pnl": 1250.0, "entry_time": "2024-01-15T10:30:00Z"},
                    {"symbol": "NQ", "pnl": -500.0, "entry_time": "2024-01-16T11:15:00Z"}
                ],
                "message": "File uploaded and processed successfully",
                "upload_id": "upload_12345"
            }
        }


class DataValidationResult(BaseModel):
    """Data validation result schema"""
    valid: bool = Field(..., description="Validation success status")
    errors: List[str] = Field(default=[], description="Validation errors")
    warnings: List[str] = Field(default=[], description="Validation warnings")
    processed_rows: int = Field(..., description="Number of rows that passed validation")
    total_rows: int = Field(..., description="Total number of rows")
    
    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "errors": [],
                "warnings": ["Missing exit_time for 5 trades"],
                "processed_rows": 145,
                "total_rows": 150
            }
        }


class ColumnMappingRequest(BaseModel):
    """Column mapping request for custom data formats"""
    upload_id: str = Field(..., description="Upload identifier")
    column_mapping: Dict[str, str] = Field(..., description="Mapping of file columns to standard fields")
    
    class Config:
        schema_extra = {
            "example": {
                "upload_id": "upload_12345",
                "column_mapping": {
                    "Symbol": "symbol",
                    "P&L": "pnl",
                    "Open Time": "entry_time",
                    "Close Time": "exit_time",
                    "Entry": "entry_price",
                    "Exit": "exit_price"
                }
            }
        }


class BulkTradeImportRequest(BaseModel):
    """Bulk trade import request"""
    upload_id: str = Field(..., description="Upload identifier")
    column_mapping: Optional[Dict[str, str]] = Field(None, description="Column mapping")
    validate_only: bool = Field(default=False, description="Only validate, don't import")
    
    class Config:
        schema_extra = {
            "example": {
                "upload_id": "upload_12345",
                "column_mapping": {
                    "Symbol": "symbol",
                    "P&L": "pnl",
                    "Open Time": "entry_time"
                },
                "validate_only": False
            }
        }


class BulkImportResponse(BaseModel):
    """Bulk import response schema"""
    success: bool = Field(..., description="Import success status")
    imported_trades: int = Field(..., description="Number of trades imported")
    failed_trades: int = Field(..., description="Number of trades that failed import")
    validation_result: DataValidationResult = Field(..., description="Validation results")
    message: str = Field(..., description="Import status message")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "imported_trades": 145,
                "failed_trades": 5,
                "validation_result": {
                    "valid": True,
                    "errors": [],
                    "warnings": ["Missing exit_time for 5 trades"],
                    "processed_rows": 145,
                    "total_rows": 150
                },
                "message": "Bulk import completed successfully"
            }
        }
