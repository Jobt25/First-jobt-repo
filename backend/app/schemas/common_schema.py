# ==================== app/schemas/common.py ====================
"""Common/utility schemas"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(
            cls,
            items: List[T],
            total: int,
            page: int,
            size: int
    ):
        """Helper to create paginated response"""
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size  # Ceiling division
        )


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime
    database: str = "connected"
    version: str
    uptime_seconds: Optional[int] = None


class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)