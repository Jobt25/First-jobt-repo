# ==================== app/schemas/question_template.py ====================
"""Question template schemas"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import enum


class DifficultyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuestionTemplateBase(BaseModel):
    """Base question template schema"""
    question_text: str = Field(..., min_length=10)
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    expected_keywords: Optional[List[str]] = None
    ideal_response_length: Optional[int] = Field(None, ge=10, le=1000)


class QuestionTemplateCreate(QuestionTemplateBase):
    """Schema for creating question template"""
    category_id: UUID


class QuestionTemplateUpdate(BaseModel):
    """Schema for updating question template"""
    question_text: Optional[str] = Field(None, min_length=10)
    difficulty: Optional[DifficultyLevel] = None
    expected_keywords: Optional[List[str]] = None
    ideal_response_length: Optional[int] = Field(None, ge=10, le=1000)
    is_active: Optional[bool] = None


class QuestionTemplateResponse(QuestionTemplateBase):
    """Schema for question template response"""
    id: UUID
    category_id: UUID
    usage_count: int
    avg_user_score: Optional[float] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)