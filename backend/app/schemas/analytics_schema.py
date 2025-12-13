# ==================== app/schemas/analytics.py ====================
"""Analytics schemas"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ProgressDataPoint(BaseModel):
    """Single data point in progress chart"""
    date: datetime
    score: float
    category: Optional[str] = None


class UserProgressTrend(BaseModel):
    """User's progress over time"""
    dates: List[datetime]
    scores: List[float]
    avg_score: float
    trend: str  # "improving", "stable", "declining"
    improvement_percentage: Optional[float] = None


class UserStatistics(BaseModel):
    """Comprehensive user statistics"""
    total_interviews: int
    completed_interviews: int
    avg_score: float
    highest_score: float
    lowest_score: float
    most_practiced_category: Optional[str] = None
    total_time_practiced: int  # seconds
    current_streak: int  # days