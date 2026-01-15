"""
app/routers/api/v1/analytics_route.py

Analytics and progress tracking endpoints.

All endpoints require authentication.

Endpoints:
- GET /analytics/progress - Progress trends over time
- GET /analytics/breakdown - Score breakdown by category
- GET /analytics/statistics - Overall user statistics
- GET /analytics/comparison - Category performance comparison
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.oauth2 import get_current_user
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics_schema import (
    ProgressTrendsResponse,
    ScoreBreakdownResponse,
    UserStatisticsResponse,
    CategoryComparisonResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ==================== PROGRESS TRENDS ====================

@router.get("/progress", response_model=ProgressTrendsResponse)
async def get_progress_trends(
    period: str = Query("30d", regex="^(7d|30d|90d|all)$", description="Time period: 7d, 30d, 90d, or all"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get progress trends over time.

    **Authentication required.**

    Shows how your interview scores have changed over time,
    helping you visualize your improvement journey.

    Query Parameters:
    - period: Time period to analyze
      - `7d`: Last 7 days
      - `30d`: Last 30 days (default)
      - `90d`: Last 90 days
      - `all`: All time

    Returns:
    - Time-series data of all your scores
    - Overall trend (improving, declining, stable)
    - Total interviews in period

    Example Response:
    ```json
    {
        "period": "30d",
        "data_points": [
            {
                "date": "2026-01-14T10:00:00Z",
                "overall_score": 88.0,
                "relevance_score": 90.0,
                "confidence_score": 85.0,
                "positivity_score": 92.0,
                "session_id": "uuid-here"
            }
        ],
        "total_interviews": 5,
        "trend": "improving",
        "date_range": {
            "start": "2025-12-15T00:00:00Z",
            "end": "2026-01-14T11:29:00Z"
        }
    }
    ```

    Use this to:
    - Track your improvement over time
    - Identify patterns in your performance
    - Motivate yourself with visible progress
    """
    service = AnalyticsService(db)
    trends = await service.get_progress_trends(
        user_id=current_user.id,
        period=period
    )

    logger.info(
        f"User {current_user.email} retrieved progress trends "
        f"({period}, {trends['total_interviews']} interviews)"
    )

    return trends


# ==================== SCORE BREAKDOWN ====================

@router.get("/breakdown", response_model=ScoreBreakdownResponse)
async def get_score_breakdown(
    category_id: Optional[UUID] = Query(None, description="Filter by specific category"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get score breakdown by job category.

    **Authentication required.**

    See how you perform in different job categories,
    helping you identify your strengths and areas for improvement.

    Query Parameters:
    - category_id: Optional UUID to filter by specific category

    Returns:
    - Performance metrics for each category you've practiced
    - Average scores, best/worst scores
    - Interview count per category
    - Categories sorted by average score (best first)

    Example Response:
    ```json
    {
        "categories": [
            {
                "category_name": "Software Engineer",
                "category_id": "uuid-here",
                "interview_count": 5,
                "average_scores": {
                    "overall": 88.5,
                    "relevance": 90.0,
                    "confidence": 85.0,
                    "positivity": 92.0
                },
                "best_score": 95.0,
                "worst_score": 78.0
            }
        ],
        "total_categories": 3
    }
    ```

    Use this to:
    - Identify which roles you're best suited for
    - Focus practice on weaker categories
    - Track category-specific improvement
    """
    service = AnalyticsService(db)
    breakdown = await service.get_score_breakdown(
        user_id=current_user.id,
        category_id=category_id
    )

    logger.info(
        f"User {current_user.email} retrieved score breakdown "
        f"({breakdown['total_categories']} categories)"
    )

    return breakdown


# ==================== USER STATISTICS ====================

@router.get("/statistics", response_model=UserStatisticsResponse)
async def get_user_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive user statistics.

    **Authentication required.**

    Your complete interview practice overview including
    totals, averages, streaks, and improvement metrics.

    Returns:
    - Total interviews completed
    - Total time spent practicing
    - Average scores across all dimensions
    - Most practiced category
    - Current streak (consecutive days)
    - Overall improvement rate

    Example Response:
    ```json
    {
        "total_interviews": 15,
        "total_time_spent_minutes": 450,
        "average_scores": {
            "overall": 85.5,
            "relevance": 88.0,
            "confidence": 82.0,
            "positivity": 90.0
        },
        "most_practiced_category": {
            "name": "Software Engineer",
            "count": 8
        },
        "current_streak_days": 5,
        "improvement_rate": 12.5
    }
    ```

    Use this to:
    - Get a quick overview of your progress
    - Track your practice consistency (streak)
    - See your overall improvement rate
    - Understand time investment
    """
    service = AnalyticsService(db)
    statistics = await service.get_user_statistics(current_user.id)

    logger.info(
        f"User {current_user.email} retrieved statistics "
        f"({statistics.get('total_interviews', 0)} interviews)"
    )

    return statistics


# ==================== CATEGORY COMPARISON ====================

@router.get("/comparison", response_model=CategoryComparisonResponse)
async def get_category_comparison(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare performance across different job categories.

    **Authentication required.**

    Side-by-side comparison of your performance in different
    job categories, highlighting your best and worst areas.

    Returns:
    - All categories with performance metrics
    - Best performing category
    - Worst performing category
    - Total categories practiced

    Example Response:
    ```json
    {
        "comparison": [
            {
                "category_name": "Software Engineer",
                "average_scores": {"overall": 88.5},
                "interview_count": 5
            },
            {
                "category_name": "Product Manager",
                "average_scores": {"overall": 75.0},
                "interview_count": 3
            }
        ],
        "best_category": {
            "category_name": "Software Engineer",
            "average_scores": {"overall": 88.5}
        },
        "worst_category": {
            "category_name": "Product Manager",
            "average_scores": {"overall": 75.0}
        },
        "total_categories_practiced": 2
    }
    ```

    Use this to:
    - Identify your strongest interview categories
    - Find areas that need more practice
    - Make informed career decisions
    - Focus your preparation efforts
    """
    service = AnalyticsService(db)
    comparison = await service.get_category_comparison(current_user.id)

    logger.info(
        f"User {current_user.email} retrieved category comparison "
        f"({comparison['total_categories_practiced']} categories)"
    )

    return comparison
