"""
Standardized response handler for consistent API responses
"""
from typing import Any, Dict, Optional, Union
from datetime import datetime
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standard API response model"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime
    request_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Standard error response model"""
    success: bool = False
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ResponseHandler:
    """Utility class for creating standardized responses"""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        request_id: Optional[str] = None
    ) -> APIResponse:
        """Create success response"""
        return APIResponse(
            success=True,
            message=message,
            data=data,
            timestamp=datetime.utcnow(),
            request_id=request_id
        )
    
    @staticmethod
    def error(
        error: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> ErrorResponse:
        """Create error response"""
        return ErrorResponse(
            error=error,
            message=message,
            details=details,
            timestamp=datetime.utcnow(),
            request_id=request_id
        )
    
    @staticmethod
    def paginated(
        items: list,
        total: int,
        page: int,
        per_page: int,
        message: str = "Success",
        request_id: Optional[str] = None
    ) -> APIResponse:
        """Create paginated response"""
        return APIResponse(
            success=True,
            message=message,
            data={
                "items": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": (total + per_page - 1) // per_page
                }
            },
            timestamp=datetime.utcnow(),
            request_id=request_id
        )

create_response = ResponseHandler.success
