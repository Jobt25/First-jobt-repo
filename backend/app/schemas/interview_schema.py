# ==================== app/schemas/interview.py ====================
"""Interview session schemas"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import enum
from ..models.base import DifficultyLevel


class InterviewStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InterviewSessionStart(BaseModel):
    """Schema for starting interview session"""
    category_id: UUID
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE


class ConversationMessage(BaseModel):
    """Single message in conversation"""
    role: str = Field(..., pattern="^(interviewer|user)$")
    content: str = Field(..., min_length=1, max_length=5000)
    timestamp: datetime


class InterviewSessionResponse(BaseModel):
    """Schema for interview session response"""
    id: UUID
    user_id: UUID
    category_id: Optional[UUID] = None
    status: InterviewStatus
    difficulty: str
    conversation_history: List[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    total_tokens_used: int
    openai_model_used: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InterviewMessageRequest(BaseModel):
    """User's response during interview"""
    content: str = Field(..., min_length=1, max_length=5000)


class InterviewMessageResponse(BaseModel):
    """AI's response to user"""
    message: str
    is_final: bool = False  # True if interview should end
    tokens_used: int
    session_status: InterviewStatus


class InterviewEndRequest(BaseModel):
    """Request to end interview"""
    reason: Optional[str] = Field(None, max_length=500)


class InterviewHistoryItem(BaseModel):
    """Condensed interview for history list"""
    id: UUID
    job_category_name: Optional[str] = None
    difficulty: str
    overall_score: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: InterviewStatus
    duration_seconds: Optional[int] = None