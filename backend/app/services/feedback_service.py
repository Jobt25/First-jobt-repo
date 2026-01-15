"""
app/services/feedback_service.py

Business logic for interview feedback management.

Handles:
- Retrieving feedback for sessions
- Calculating feedback summaries
- Listing feedback history
- Comparing feedback across sessions
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from fastapi import HTTPException, status
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging

from ..models.interview_feedback import InterviewFeedback
from ..models.interview_session import InterviewSession
from ..models.user import User

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service class for feedback operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== GET FEEDBACK ====================

    async def get_feedback_by_session(
            self,
            session_id: UUID,
            user_id: UUID
    ) -> InterviewFeedback:
        """
        Get detailed feedback for a specific interview session.

        Args:
            session_id: Interview session UUID
            user_id: User UUID (for ownership verification)

        Returns:
            Interview feedback

        Raises:
            HTTPException: If session not found, unauthorized, or no feedback
        """
        # Verify session ownership
        session = await self._get_session_with_ownership(session_id, user_id)

        # Get feedback
        result = await self.db.execute(
            select(InterviewFeedback).where(
                InterviewFeedback.session_id == session_id
            )
        )
        feedback = result.scalar_one_or_none()

        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not yet generated for this interview. Please complete the interview first."
            )

        logger.info(f"Retrieved feedback for session {session_id}")
        return feedback

    # ==================== FEEDBACK SUMMARY ====================

    async def get_user_feedback_summary(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get aggregated feedback summary for a user.

        Calculates:
        - Average scores across all interviews
        - Total interviews completed
        - Most common strengths and weaknesses
        - Improvement trend

        Args:
            user_id: User UUID

        Returns:
            Dict with summary statistics
        """
        # Get all feedback for user's completed sessions
        query = (
            select(InterviewFeedback)
            .join(InterviewSession, InterviewFeedback.session_id == InterviewSession.id)
            .where(InterviewSession.user_id == user_id)
            .order_by(desc(InterviewSession.completed_at))
        )

        result = await self.db.execute(query)
        all_feedback = result.scalars().all()

        if not all_feedback:
            return {
                "total_interviews": 0,
                "average_scores": None,
                "message": "No feedback available yet. Complete an interview to see your progress!"
            }

        # Calculate averages
        total = len(all_feedback)
        avg_overall = sum(f.overall_score for f in all_feedback) / total
        avg_relevance = sum(f.relevance_score for f in all_feedback) / total
        avg_confidence = sum(f.confidence_score for f in all_feedback) / total
        avg_positivity = sum(f.positivity_score for f in all_feedback) / total

        # Extract common strengths and weaknesses
        all_strengths = []
        all_weaknesses = []
        for f in all_feedback:
            if f.strengths:
                all_strengths.extend(f.strengths)
            if f.weaknesses:
                all_weaknesses.extend(f.weaknesses)

        # Get most common (simple frequency count)
        common_strengths = self._get_most_common(all_strengths, limit=5)
        common_weaknesses = self._get_most_common(all_weaknesses, limit=5)

        # Calculate improvement trend (compare first 3 vs last 3)
        improvement_rate = self._calculate_improvement_rate(all_feedback)

        summary = {
            "total_interviews": total,
            "average_scores": {
                "overall": round(avg_overall, 1),
                "relevance": round(avg_relevance, 1),
                "confidence": round(avg_confidence, 1),
                "positivity": round(avg_positivity, 1)
            },
            "common_strengths": common_strengths,
            "common_weaknesses": common_weaknesses,
            "improvement_rate": improvement_rate,
            "latest_score": round(all_feedback[0].overall_score, 1) if all_feedback else None
        }

        logger.info(f"Generated feedback summary for user {user_id} ({total} interviews)")
        return summary

    # ==================== FEEDBACK HISTORY ====================

    async def list_user_feedback(
            self,
            user_id: UUID,
            limit: int = 20,
            offset: int = 0
    ) -> Dict[str, Any]:
        """
        List user's feedback history with pagination.

        Args:
            user_id: User UUID
            limit: Maximum results
            offset: Pagination offset

        Returns:
            Dict with feedback list and pagination info
        """
        # Build query
        query = (
            select(InterviewFeedback)
            .join(InterviewSession, InterviewFeedback.session_id == InterviewSession.id)
            .where(InterviewSession.user_id == user_id)
            .order_by(desc(InterviewSession.completed_at))
        )

        # Get total count
        count_query = (
            select(func.count(InterviewFeedback.id))
            .join(InterviewSession, InterviewFeedback.session_id == InterviewSession.id)
            .where(InterviewSession.user_id == user_id)
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        feedback_list = result.scalars().all()

        return {
            "items": feedback_list,
            "total": total,
            "page": (offset // limit) + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if total > 0 else 0
        }

    # ==================== COMPARE FEEDBACK ====================

    async def compare_feedback(
            self,
            user_id: UUID,
            session_ids: List[UUID]
    ) -> Dict[str, Any]:
        """
        Compare feedback across multiple sessions.

        Args:
            user_id: User UUID
            session_ids: List of session UUIDs to compare

        Returns:
            Dict with comparison data
        """
        if len(session_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 sessions required for comparison"
            )

        # Get feedback for all sessions
        feedback_list = []
        for session_id in session_ids:
            try:
                feedback = await self.get_feedback_by_session(session_id, user_id)
                feedback_list.append(feedback)
            except HTTPException:
                # Skip sessions without feedback
                continue

        if len(feedback_list) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough feedback available for comparison"
            )

        # Calculate comparison metrics
        comparison = {
            "sessions_compared": len(feedback_list),
            "score_comparison": [
                {
                    "session_id": str(f.session_id),
                    "overall_score": f.overall_score,
                    "relevance_score": f.relevance_score,
                    "confidence_score": f.confidence_score,
                    "positivity_score": f.positivity_score
                }
                for f in feedback_list
            ],
            "average_improvement": self._calculate_improvement_between_sessions(feedback_list)
        }

        return comparison

    # ==================== PRIVATE HELPER METHODS ====================

    async def _get_session_with_ownership(
            self,
            session_id: UUID,
            user_id: UUID
    ) -> InterviewSession:
        """
        Get session and verify user owns it.

        Raises:
            HTTPException: If not found or unauthorized
        """
        result = await self.db.execute(
            select(InterviewSession).where(
                InterviewSession.id == session_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview session not found"
            )

        if str(session.user_id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this interview session"
            )

        return session

    def _get_most_common(self, items: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Get most common items from list"""
        from collections import Counter

        if not items:
            return []

        counter = Counter(items)
        most_common = counter.most_common(limit)

        return [
            {"item": item, "count": count}
            for item, count in most_common
        ]

    def _calculate_improvement_rate(self, feedback_list: List[InterviewFeedback]) -> float:
        """
        Calculate improvement rate comparing first vs last interviews.

        Returns:
            Percentage improvement (positive = improving, negative = declining)
        """
        if len(feedback_list) < 2:
            return 0.0

        # Compare first 3 vs last 3 (or all if less than 6)
        sample_size = min(3, len(feedback_list) // 2)

        if sample_size == 0:
            return 0.0

        # Last interviews (most recent)
        recent = feedback_list[:sample_size]
        recent_avg = sum(f.overall_score for f in recent) / len(recent)

        # First interviews (oldest)
        oldest = feedback_list[-sample_size:]
        oldest_avg = sum(f.overall_score for f in oldest) / len(oldest)

        # Calculate percentage change
        if oldest_avg == 0:
            return 0.0

        improvement = ((recent_avg - oldest_avg) / oldest_avg) * 100
        return round(improvement, 1)

    def _calculate_improvement_between_sessions(
            self,
            feedback_list: List[InterviewFeedback]
    ) -> float:
        """Calculate average improvement between consecutive sessions"""
        if len(feedback_list) < 2:
            return 0.0

        # Sort by session date (assuming feedback_list is already sorted)
        improvements = []
        for i in range(len(feedback_list) - 1):
            current = feedback_list[i].overall_score
            previous = feedback_list[i + 1].overall_score

            if previous > 0:
                improvement = ((current - previous) / previous) * 100
                improvements.append(improvement)

        if not improvements:
            return 0.0

        return round(sum(improvements) / len(improvements), 1)
