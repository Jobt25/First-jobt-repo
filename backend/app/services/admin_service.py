"""
app/services/admin_service.py

Service layer for admin dashboard and system management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from uuid import UUID
import logging

from app.models.user import User, UserRole
from app.models.interview_session import InterviewSession, InterviewStatus
from app.models.job_category import JobCategory

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== USER MANAGEMENT ====================

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List users with pagination and search.

        Args:
            skip: Pagination offset
            limit: Pagination limit
            search: Search by email or name

        Returns:
            Dict with users list and total count
        """
        query = select(User).order_by(desc(User.created_at))
        count_query = select(func.count(User.id))

        if search:
            search_filter = or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Get users
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()

        return {
            "items": users,
            "total": total,
            "page": (skip // limit) + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit if limit > 0 else 0
        }

    async def get_user_details(self, user_id: UUID) -> Optional[User]:
        """Get detailed user information"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_user_status(self, user_id: UUID, is_active: bool) -> Optional[User]:
        """Activate or deactivate a user"""
        user = await self.get_user_details(user_id)
        if not user:
            return None

        user.is_active = is_active
        await self.db.commit()
        await self.db.refresh(user)
        
        status_str = "activated" if is_active else "deactivated"
        logger.info(f"User {user.email} {status_str} by admin")
        
        return user

    # ==================== SYSTEM ANALYTICS ====================

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get aggregated system statistics for the dashboard.
        
        Calculates:
        - User growth (today/total)
        - Active usage (sessions today)
        - Session completion rates
        - Token usage approximations
        """
        today = datetime.utcnow().date()
        start_of_today = datetime.combine(today, datetime.min.time())
        month_start = today.replace(day=1)

        # 1. User Stats
        total_users_query = select(func.count(User.id))
        new_users_today_query = select(func.count(User.id)).where(User.created_at >= start_of_today)
        
        # 2. Session Stats
        total_sessions_query = select(func.count(InterviewSession.id))
        sessions_today_query = select(func.count(InterviewSession.id)).where(InterviewSession.started_at >= start_of_today)
        completed_sessions_today_query = select(func.count(InterviewSession.id)).where(
            InterviewSession.started_at >= start_of_today,
            InterviewSession.status == InterviewStatus.COMPLETED.value
        )
        
        # 3. Execution
        total_users = (await self.db.execute(total_users_query)).scalar() or 0
        new_users_today = (await self.db.execute(new_users_today_query)).scalar() or 0
        
        total_sessions = (await self.db.execute(total_sessions_query)).scalar() or 0
        sessions_today = (await self.db.execute(sessions_today_query)).scalar() or 0
        completed_today = (await self.db.execute(completed_sessions_today_query)).scalar() or 0
        
        return {
            "total_users": total_users,
            "new_users_today": new_users_today,
            "new_users_this_week": 0, # Placeholder for optimization
            "active_users_today": 0, # Placeholder
            "active_users_this_week": 0,
            "active_users_this_month": 0,
            "total_sessions_all_time": total_sessions,
            "total_sessions_today": sessions_today,
            "completed_sessions_today": completed_today,
            "avg_session_score": 0.0,
            "total_tokens_used_today": 0,
            "total_tokens_used_month": 0,
            "estimated_cost_today": 0.0,
            "estimated_cost_month": 0.0
        }
