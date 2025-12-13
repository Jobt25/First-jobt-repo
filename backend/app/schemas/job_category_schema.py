# ==================== app/schemas/job_category.py ====================
"""Job category schemas"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class JobCategoryBase(BaseModel):
    """Base job category schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=255)


class JobCategoryCreate(JobCategoryBase):
    """Schema for creating job category"""
    pass


class JobCategoryUpdate(BaseModel):
    """Schema for updating job category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    industry: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class JobCategoryResponse(JobCategoryBase):
    """Schema for job category response"""
    id: UUID
    is_active: bool
    typical_questions_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobCategoryDetail(JobCategoryResponse):
    """Detailed job category with statistics"""
    total_interviews: int = 0
    avg_completion_rate: Optional[float] = None
    avg_score: Optional[float] = None