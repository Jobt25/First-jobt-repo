# ==================== app/schemas/feedback.py ====================
"""Feedback schemas"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Alias for consistency with route naming
FeedbackResponse = InterviewFeedbackResponse


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


class CommonItem(BaseModel):
    """Common item with frequency count"""
    item: str
    count: int


class FeedbackSummaryResponse(BaseModel):
    """Aggregated feedback summary for user"""
    total_interviews: int
    average_scores: Optional[ScoreBreakdown] = None
    common_strengths: List[CommonItem] = []
    common_weaknesses: List[CommonItem] = []
    improvement_rate: float = Field(..., description="Percentage improvement from first to recent interviews")
    latest_score: Optional[float] = None
    message: Optional[str] = None


class FeedbackComparisonRequest(BaseModel):
    """Request to compare multiple sessions"""
    session_ids: List[UUID] = Field(..., min_length=2, description="At least 2 session IDs required")


class SessionScoreComparison(BaseModel):
    """Score comparison for a single session"""
    session_id: str
    overall_score: float
    relevance_score: float
    confidence_score: float
    positivity_score: float


class FeedbackComparisonResponse(BaseModel):
    """Comparison of feedback across sessions"""
    sessions_compared: int
    score_comparison: List[SessionScoreComparison]
    average_improvement: float = Field(..., description="Average improvement rate between sessions")
