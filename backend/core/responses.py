"""
Standardized Response Models

Provides consistent response structures for all API endpoints.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model with common fields"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracking")

class SuccessResponse(BaseResponse):
    """Standard success response"""
    success: bool = True
    data: Optional[Any] = Field(None, description="Response data")

class ErrorResponse(BaseResponse):
    """Standard error response"""
    success: bool = False
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class PaginatedResponse(BaseResponse):
    """Paginated response for list endpoints"""
    success: bool = True
    data: List[Any] = Field(..., description="List of items")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Data retrieved successfully",
                "timestamp": "2025-01-01T12:00:00Z",
                "data": [],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total": 100,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }
    }

class HealthResponse(BaseResponse):
    """Health check response"""
    success: bool = True
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")

class AnalyticsResponse(BaseResponse):
    """Analytics response with metrics"""
    success: bool = True
    data: Dict[str, Any] = Field(..., description="Analytics data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class TradeResponse(BaseResponse):
    """Trade-specific response"""
    success: bool = True
    data: Dict[str, Any] = Field(..., description="Trade data")
    analysis: Optional[Dict[str, Any]] = Field(None, description="Trade analysis")
    recommendations: Optional[List[str]] = Field(None, description="Trading recommendations")

def create_success_response(
    data: Any = None, 
    message: str = "Operation completed successfully",
    request_id: Optional[str] = None
) -> SuccessResponse:
    """Create a standardized success response"""
    return SuccessResponse(
        message=message,
        data=data,
        request_id=request_id
    )

def create_error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Create a standardized error response"""
    return ErrorResponse(
        message=message,
        error_code=error_code,
        details=details,
        request_id=request_id
    )

def create_paginated_response(
    data: List[Any],
    page: int,
    per_page: int,
    total: int,
    message: str = "Data retrieved successfully",
    request_id: Optional[str] = None
) -> PaginatedResponse:
    """Create a standardized paginated response"""
    total_pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        message=message,
        data=data,
        request_id=request_id,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    )

def error_response(message: str, error: str = None, status_code: int = 400, data: dict = None):
    """
    Standardized error response for API endpoints.
    """
    return {
        "success": False,
        "message": message,
        "error": error,
        "data": data or {},
        "status_code": status_code
    }

def success_response(data: dict = None, message: str = "Success", status_code: int = 200):
    """
    Standardized success response for API endpoints.
    """
    return {
        "success": True,
        "message": message,
        "data": data or {},
        "status_code": status_code
    } 