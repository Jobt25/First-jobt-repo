"""
app/services/analytics_service.py

Business logic for interview analytics and progress tracking.

Handles:
- Progress trends over time
- Score breakdowns by category
- User statistics and metrics
- Improvement rate calculations
- Category performance comparison
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, case
from fastapi import HTTPException, status
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging

from ..models.interview_feedback import InterviewFeedback
from ..models.interview_session import InterviewSession, InterviewStatus
from ..models.job_category import JobCategory
from ..models.user import User

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service class for analytics operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== PROGRESS TRENDS ====================

    async def get_progress_trends(
            self,
            user_id: UUID,
            period: str = '30d'
    ) -> Dict[str, Any]:
        """
        Get progress trends over time.

        Args:
            user_id: User UUID
            period: Time period ('7d', '30d', '90d', 'all')

        Returns:
            Dict with time-series data of scores
        """
        # Calculate date range
        end_date = datetime.utcnow()
        if period == '7d':
            start_date = end_date - timedelta(days=7)
        elif period == '30d':
            start_date = end_date - timedelta(days=30)
        elif period == '90d':
            start_date = end_date - timedelta(days=90)
        else:  # 'all'
            start_date = datetime(2020, 1, 1)  # Far past date

        # Get all feedback within period
        query = (
            select(InterviewFeedback, InterviewSession)
            .join(InterviewSession, InterviewFeedback.session_id == InterviewSession.id)
            .where(
                and_(
                    InterviewSession.user_id == user_id,
                    InterviewSession.completed_at >= start_date,
                    InterviewSession.status == InterviewStatus.COMPLETED.value
                )
            )
            .order_by(InterviewSession.completed_at)
        )

        result = await self.db.execute(query)
        rows = result.all()

        if not rows:
            return {
                "period": period,
                "data_points": [],
                "trend": "no_data",
                "message": "No interview data available for this period"
            }

        # Build time-series data
        data_points = []
        for feedback, session in rows:
            data_points.append({
                "date": session.completed_at.isoformat(),
                "overall_score": feedback.overall_score,
                "relevance_score": feedback.relevance_score,
                "confidence_score": feedback.confidence_score,
                "positivity_score": feedback.positivity_score,
                "session_id": str(session.id)
            })

        # Calculate trend (improving, declining, stable)
        trend = self._calculate_trend(data_points)

        logger.info(f"Generated progress trends for user {user_id} ({period}): {len(data_points)} points")

        return {
            "period": period,
            "data_points": data_points,
            "total_interviews": len(data_points),
            "trend": trend,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }

    # ==================== SCORE BREAKDOWN ====================

    async def get_score_breakdown(
            self,
            user_id: UUID,
            category_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get score breakdown by category.

        Args:
            user_id: User UUID
            category_id: Optional category filter

        Returns:
            Dict with category-wise performance
        """
        # Build query
        query = (
            select(
                JobCategory.name,
                JobCategory.id,
                func.count(InterviewFeedback.id).label('interview_count'),
                func.avg(InterviewFeedback.overall_score).label('avg_overall'),
                func.avg(InterviewFeedback.relevance_score).label('avg_relevance'),
                func.avg(InterviewFeedback.confidence_score).label('avg_confidence'),
                func.avg(InterviewFeedback.positivity_score).label('avg_positivity'),
                func.max(InterviewFeedback.overall_score).label('best_score'),
                func.min(InterviewFeedback.overall_score).label('worst_score')
            )
            .join(InterviewSession, InterviewFeedback.session_id == InterviewSession.id)
            .join(JobCategory, InterviewSession.category_id == JobCategory.id)
            .where(InterviewSession.user_id == user_id)
        )

        # Apply category filter if provided
        if category_id:
            query = query.where(JobCategory.id == category_id)

        query = query.group_by(JobCategory.id, JobCategory.name)

        result = await self.db.execute(query)
        rows = result.all()

        if not rows:
            return {
                "categories": [],
                "message": "No interview data available"
            }

        # Build breakdown
        categories = []
        for row in rows:
            categories.append({
                "category_name": row.name,
                "category_id": str(row.id),
                "interview_count": row.interview_count,
                "average_scores": {
                    "overall": round(row.avg_overall, 1),
                    "relevance": round(row.avg_relevance, 1),
                    "confidence": round(row.avg_confidence, 1),
                    "positivity": round(row.avg_positivity, 1)
                },
                "best_score": round(row.best_score, 1),
                "worst_score": round(row.worst_score, 1)
            })

        # Sort by average overall score (descending)
        categories.sort(key=lambda x: x["average_scores"]["overall"], reverse=True)

        logger.info(f"Generated score breakdown for user {user_id}: {len(categories)} categories")

        return {
            "categories": categories,
            "total_categories": len(categories)
        }

    # ==================== USER STATISTICS ====================

    async def get_user_statistics(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get overall user statistics.

        Args:
            user_id: User UUID

        Returns:
            Dict with comprehensive user stats
        """
        # Get all completed sessions
        sessions_query = (
            select(InterviewSession)
            .where(
                and_(
                    InterviewSession.user_id == user_id,
                    InterviewSession.status == InterviewStatus.COMPLETED.value
                )
            )
        )

        sessions_result = await self.db.execute(sessions_query)
        sessions = sessions_result.scalars().all()

        if not sessions:
            return {
                "total_interviews": 0,
                "message": "No completed interviews yet"
            }

        # Get all feedback
        feedback_query = (
            select(InterviewFeedback)
            .join(InterviewSession, InterviewFeedback.session_id == InterviewSession.id)
            .where(InterviewSession.user_id == user_id)
        )

        feedback_result = await self.db.execute(feedback_query)
        all_feedback = feedback_result.scalars().all()

        # Calculate statistics
        total_interviews = len(sessions)
        total_time_spent = sum(s.duration_seconds or 0 for s in sessions)

        # Average scores
        if all_feedback:
            avg_overall = sum(f.overall_score for f in all_feedback) / len(all_feedback)
            avg_relevance = sum(f.relevance_score for f in all_feedback) / len(all_feedback)
            avg_confidence = sum(f.confidence_score for f in all_feedback) / len(all_feedback)
            avg_positivity = sum(f.positivity_score for f in all_feedback) / len(all_feedback)
        else:
            avg_overall = avg_relevance = avg_confidence = avg_positivity = 0.0

        # Most practiced category
        category_counts = {}
        for session in sessions:
            cat_id = str(session.category_id)
            category_counts[cat_id] = category_counts.get(cat_id, 0) + 1

        most_practiced_category_id = max(category_counts, key=category_counts.get) if category_counts else None
        most_practiced_category_name = None

        if most_practiced_category_id:
            cat_result = await self.db.execute(
                select(JobCategory.name).where(JobCategory.id == UUID(most_practiced_category_id))
            )
            most_practiced_category_name = cat_result.scalar_one_or_none()

        # Calculate streak (consecutive days with interviews)
        streak = self._calculate_streak(sessions)

        # Improvement rate
        improvement_rate = await self._calculate_improvement_rate(user_id)

        statistics = {
            "total_interviews": total_interviews,
            "total_time_spent_minutes": total_time_spent // 60,
            "average_scores": {
                "overall": round(avg_overall, 1),
                "relevance": round(avg_relevance, 1),
                "confidence": round(avg_confidence, 1),
                "positivity": round(avg_positivity, 1)
            },
            "most_practiced_category": {
                "name": most_practiced_category_name,
                "count": category_counts.get(most_practiced_category_id, 0) if most_practiced_category_id else 0
            },
            "current_streak_days": streak,
            "improvement_rate": improvement_rate
        }

        logger.info(f"Generated statistics for user {user_id}: {total_interviews} interviews")

        return statistics

    # ==================== CATEGORY COMPARISON ====================

    async def get_category_comparison(self, user_id: UUID) -> Dict[str, Any]:
        """
        Compare performance across different categories.

        Args:
            user_id: User UUID

        Returns:
            Dict with category comparison data
        """
        # Reuse score breakdown
        breakdown = await self.get_score_breakdown(user_id)

        if not breakdown["categories"]:
            return {
                "comparison": [],
                "message": "No data available for comparison"
            }

        # Identify best and worst categories
        categories = breakdown["categories"]
        best_category = categories[0] if categories else None
        worst_category = categories[-1] if categories else None

        return {
            "comparison": categories,
            "best_category": best_category,
            "worst_category": worst_category,
            "total_categories_practiced": len(categories)
        }

    # ==================== IMPROVEMENT RATE ====================

    async def calculate_improvement_rate(self, user_id: UUID) -> float:
        """
        Calculate overall improvement rate.

        Args:
            user_id: User UUID

        Returns:
            Percentage improvement
        """
        return await self._calculate_improvement_rate(user_id)

    # ==================== PRIVATE HELPER METHODS ====================

    def _calculate_trend(self, data_points: List[Dict]) -> str:
        """
        Calculate trend from data points.

        Returns:
            'improving', 'declining', or 'stable'
        """
        if len(data_points) < 2:
            return "insufficient_data"

        # Compare first half vs second half
        mid = len(data_points) // 2
        first_half_avg = sum(p["overall_score"] for p in data_points[:mid]) / mid
        second_half_avg = sum(p["overall_score"] for p in data_points[mid:]) / (len(data_points) - mid)

        diff = second_half_avg - first_half_avg

        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"

    def _calculate_streak(self, sessions: List[InterviewSession]) -> int:
        """
        Calculate consecutive days with interviews.

        Args:
            sessions: List of interview sessions

        Returns:
            Number of consecutive days
        """
        if not sessions:
            return 0

        # Sort by date (most recent first)
        sorted_sessions = sorted(sessions, key=lambda s: s.completed_at, reverse=True)

        # Get unique dates
        dates = set()
        for session in sorted_sessions:
            if session.completed_at:
                date = session.completed_at.date()
                dates.add(date)

        dates = sorted(dates, reverse=True)

        if not dates:
            return 0

        # Check if most recent is today or yesterday
        today = datetime.utcnow().date()
        if dates[0] not in [today, today - timedelta(days=1)]:
            return 0  # Streak broken

        # Count consecutive days
        streak = 1
        for i in range(len(dates) - 1):
            if (dates[i] - dates[i + 1]).days == 1:
                streak += 1
            else:
                break

        return streak

    async def _calculate_improvement_rate(self, user_id: UUID) -> float:
        """
        Calculate improvement rate comparing first vs recent interviews.

        Returns:
            Percentage improvement
        """
        # Get all feedback ordered by date
        query = (
            select(InterviewFeedback)
            .join(InterviewSession, InterviewFeedback.session_id == InterviewSession.id)
            .where(InterviewSession.user_id == user_id)
            .order_by(desc(InterviewSession.completed_at))
        )

        result = await self.db.execute(query)
        all_feedback = result.scalars().all()

        if len(all_feedback) < 2:
            return 0.0

        # Compare first 3 vs last 3 (or all if less than 6)
        sample_size = min(3, len(all_feedback) // 2)

        if sample_size == 0:
            return 0.0

        # Recent interviews (most recent)
        recent = all_feedback[:sample_size]
        recent_avg = sum(f.overall_score for f in recent) / len(recent)

        # First interviews (oldest)
        oldest = all_feedback[-sample_size:]
        oldest_avg = sum(f.overall_score for f in oldest) / len(oldest)

        # Calculate percentage change
        if oldest_avg == 0:
            return 0.0

        improvement = ((recent_avg - oldest_avg) / oldest_avg) * 100
        return round(improvement, 1)
