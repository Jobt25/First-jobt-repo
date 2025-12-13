# ==================== app/schemas/feedback.py ====================
"""Feedback schemas"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class InterviewFeedbackResponse(BaseModel):
    """Detailed feedback response"""
    id: UUID
    session_id: UUID
    overall_score: float = Field(..., ge=0, le=100)
    relevance_score: float = Field(..., ge=0, le=100)
    confidence_score: float = Field(..., ge=0, le=100)
    positivity_score: float = Field(..., ge=0, le=100)
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    summary: Optional[str] = None
    actionable_tips: Optional[List[str]] = None
    filler_words_count: int
    avg_response_length: Optional[int] = None
    response_time_avg: Optional[float] = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedbackSummary(BaseModel):
    """Condensed feedback for history"""
    session_id: UUID
    overall_score: float
    completed_at: datetime
    job_category_name: Optional[str] = None
    key_insight: Optional[str] = None


class ScoreBreakdown(BaseModel):
    """Score breakdown by dimension"""
    overall: float
    relevance: float
    confidence: float
    positivity: float