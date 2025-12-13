# ==================== app/schemas/admin.py ====================
"""Admin schemas"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class AdminDashboardStats(BaseModel):
    """Admin dashboard statistics"""
    total_users: int
    active_users_today: int
    active_users_this_week: int
    active_users_this_month: int
    total_sessions_today: int
    total_sessions_all_time: int
    completed_sessions_today: int
    avg_session_score: Optional[float] = None
    total_tokens_used_today: int
    total_tokens_used_month: int
    estimated_cost_today: float
    estimated_cost_month: float
    new_users_today: int
    new_users_this_week: int


class SystemMetricsResponse(BaseModel):
    """System metrics for a specific date"""
    id: UUID
    date: datetime
    active_users: int
    new_users: int
    total_sessions: int
    completed_sessions: int
    avg_session_duration: Optional[float] = None
    avg_overall_score: Optional[float] = None
    total_openai_tokens: int
    estimated_cost_usd: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserManagementResponse(BaseModel):
    """User info for admin management"""
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    total_interviews: int
    last_login: Optional[datetime] = None
    created_at: datetime


class UpdateUserRoleRequest(BaseModel):
    """Request to update user role"""
    role: str = Field(..., pattern="^(user|admin)$")


class UpdateUserStatusRequest(BaseModel):
    """Request to update user status"""
    is_active: bool