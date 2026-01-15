# ==================== app/schemas/analytics.py ====================
"""Analytics schemas"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ProgressDataPoint(BaseModel):
    """Single data point in progress chart"""
    date: str = Field(..., description="ISO format datetime")
    overall_score: float
    relevance_score: float
    confidence_score: float
    positivity_score: float
    session_id: str


class DateRange(BaseModel):
    """Date range for analytics"""
    start: str
    end: str


class ProgressTrendsResponse(BaseModel):
    """Progress trends over time"""
    period: str = Field(..., description="Time period: 7d, 30d, 90d, or all")
    data_points: List[ProgressDataPoint]
    total_interviews: int
    trend: str = Field(..., description="improving, declining, stable, or no_data")
    date_range: DateRange
    message: Optional[str] = None


class ScoreAverages(BaseModel):
    """Average scores across dimensions"""
    overall: float
    relevance: float
    confidence: float
    positivity: float


class CategoryPerformance(BaseModel):
    """Performance in a specific category"""
    category_name: str
    category_id: str
    interview_count: int
    average_scores: ScoreAverages
    best_score: float
    worst_score: float


class ScoreBreakdownResponse(BaseModel):
    """Score breakdown by category"""
    categories: List[CategoryPerformance]
    total_categories: int
    message: Optional[str] = None


class MostPracticedCategory(BaseModel):
    """Most practiced category info"""
    name: Optional[str] = None
    count: int = 0


class UserStatisticsResponse(BaseModel):
    """Comprehensive user statistics"""
    total_interviews: int
    total_time_spent_minutes: int
    average_scores: ScoreAverages
    most_practiced_category: MostPracticedCategory
    current_streak_days: int = Field(..., description="Consecutive days with interviews")
    improvement_rate: float = Field(..., description="Percentage improvement from first to recent")
    message: Optional[str] = None


class CategoryComparisonResponse(BaseModel):
    """Category comparison data"""
    comparison: List[CategoryPerformance]
    best_category: Optional[CategoryPerformance] = None
    worst_category: Optional[CategoryPerformance] = None
    total_categories_practiced: int
    message: Optional[str] = None


# Legacy schemas (kept for compatibility)
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