"""
app/routers/api/v1/feedback_route.py

Feedback viewing and analysis endpoints.

All endpoints require authentication.

Endpoints:
- GET /feedback/{session_id} - Get detailed feedback
- GET /feedback/summary - Get user's feedback summary
- GET /feedback/history - List feedback history
- POST /feedback/compare - Compare multiple sessions
"""

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.oauth2 import get_current_user
from app.models.user import User
from app.services.feedback_service import FeedbackService
from app.schemas.feedback_schema import (
    FeedbackResponse,
    FeedbackSummaryResponse,
    FeedbackComparisonRequest,
    FeedbackComparisonResponse
)
from app.schemas.common_schema import PaginatedResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["Feedback"])





# ==================== GET FEEDBACK SUMMARY ====================

@router.get("/summary", response_model=FeedbackSummaryResponse)
async def get_feedback_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated feedback summary for current user.

    **Authentication required.**

    Returns:
    - Average scores across all interviews
    - Total interviews completed
    - Most common strengths and weaknesses
    - Improvement rate (% change from first to recent interviews)

    This endpoint helps users understand their overall progress
    and identify patterns in their interview performance.

    Example Response:
    ```json
    {
        "total_interviews": 10,
        "average_scores": {
            "overall": 82.5,
            "relevance": 85.0,
            "confidence": 78.0,
            "positivity": 88.0
        },
        "common_strengths": [
            {"item": "Clear communication", "count": 8},
            {"item": "Good examples", "count": 6}
        ],
        "common_weaknesses": [
            {"item": "Too many filler words", "count": 5}
        ],
        "improvement_rate": 15.5,
        "latest_score": 88.0
    }
    ```
    """
    service = FeedbackService(db)
    summary = await service.get_user_feedback_summary(current_user.id)

    logger.info(f"User {current_user.email} retrieved feedback summary")

    return summary


# ==================== LIST FEEDBACK HISTORY ====================

@router.get("/history", response_model=PaginatedResponse)
async def list_feedback_history(
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's feedback history with pagination.

    **Authentication required.**

    Returns a paginated list of all feedback for the current user,
    ordered by most recent first.

    Query Parameters:
    - limit: Number of results per page (1-100, default: 20)
    - offset: Pagination offset (default: 0)

    Use this to:
    - Review past interview feedback
    - Track improvement over time
    - Identify recurring patterns

    Example Response:
    ```json
    {
        "items": [
            {
                "session_id": "uuid-1",
                "overall_score": 88.0,
                "created_at": "2026-01-14T10:00:00Z"
            },
            {
                "session_id": "uuid-2",
                "overall_score": 82.0,
                "created_at": "2026-01-13T15:30:00Z"
            }
        ],
        "total": 10,
        "page": 1,
        "size": 20,
        "pages": 1
    }
    ```
    """
    service = FeedbackService(db)
    result = await service.list_user_feedback(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )

    logger.info(
        f"User {current_user.email} listed feedback history "
        f"(page {result['page']}, total: {result['total']})"
    )

    return result


# ==================== GET FEEDBACK BY SESSION ====================

@router.get("/{session_id}", response_model=FeedbackResponse)
async def get_feedback(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed feedback for a specific interview session.

    **Authentication required.**

    Returns comprehensive feedback including:
    - Overall, relevance, confidence, and positivity scores
    - Identified strengths and weaknesses
    - Actionable improvement tips
    - Filler word count and response metrics

    Path Parameters:
    - session_id: UUID of the interview session

    Example Response:
    ```json
    {
        "session_id": "uuid-here",
        "overall_score": 85.5,
        "relevance_score": 88.0,
        "confidence_score": 82.0,
        "positivity_score": 90.0,
        "strengths": ["Clear communication", "Good examples"],
        "weaknesses": ["Too many filler words"],
        "summary": "Strong performance overall...",
        "actionable_tips": ["Practice STAR method"],
        "filler_words_count": 12
    }
    ```
    """
    service = FeedbackService(db)
    feedback = await service.get_feedback_by_session(session_id, current_user.id)

    logger.info(f"User {current_user.email} retrieved feedback for session {session_id}")

    return feedback


# ==================== COMPARE FEEDBACK ====================

@router.post("/compare", response_model=FeedbackComparisonResponse)
async def compare_feedback(
    request: FeedbackComparisonRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare feedback across multiple interview sessions.

    **Authentication required.**

    Provide 2 or more session IDs to compare performance across
    different interviews. Useful for tracking improvement or
    comparing performance in different job categories.

    Request Body:
    ```json
    {
        "session_ids": ["uuid-1", "uuid-2", "uuid-3"]
    }
    ```

    Returns:
    - Score comparison for each session
    - Average improvement rate
    - Trend analysis

    Example Response:
    ```json
    {
        "sessions_compared": 3,
        "score_comparison": [
            {
                "session_id": "uuid-1",
                "overall_score": 88.0,
                "relevance_score": 90.0
            },
            {
                "session_id": "uuid-2",
                "overall_score": 82.0,
                "relevance_score": 85.0
            }
        ],
        "average_improvement": 7.3
    }
    ```
    """
    service = FeedbackService(db)
    comparison = await service.compare_feedback(
        user_id=current_user.id,
        session_ids=request.session_ids
    )

    logger.info(
        f"User {current_user.email} compared {len(request.session_ids)} sessions"
    )

    return comparison
