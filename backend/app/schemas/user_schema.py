# ==================== app/schemas/user.py ====================
"""User-related schemas"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import enum


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    current_job_title: Optional[str] = Field(None, max_length=255)
    target_job_role: Optional[str] = Field(None, max_length=255)
    years_of_experience: Optional[int] = Field(None, ge=0, le=50)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = Field(None, max_length=255)
    current_job_title: Optional[str] = Field(None, max_length=255)
    target_job_role: Optional[str] = Field(None, max_length=255)
    years_of_experience: Optional[int] = Field(None, ge=0, le=50)


class UserResponse(UserBase):
    """Schema for user response (excludes password)"""
    id: UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    interview_count_current_month: int
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserProfile(UserResponse):
    """Extended user profile with statistics"""
    total_interviews: int = 0
    avg_score: Optional[float] = None
    last_interview_date: Optional[datetime] = None
    interviews_this_month: int = 0
    improvement_rate: Optional[float] = None  # percentage
