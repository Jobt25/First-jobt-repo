# ==================== app/models/system_metrics.py ====================
"""System metrics model"""

from sqlalchemy import Column, DateTime, Integer, Float

from .base import BaseModel


class SystemMetrics(BaseModel):
    """
    Daily system metrics for admin dashboard.

    Aggregated nightly via cron job.
    """

    __tablename__ = "system_metrics"

    date = Column(DateTime(timezone=True), unique=True, nullable=False, index=True)

    # Usage metrics
    active_users = Column(Integer, default=0, nullable=False)
    new_users = Column(Integer, default=0, nullable=False)
    total_sessions = Column(Integer, default=0, nullable=False)
    completed_sessions = Column(Integer, default=0, nullable=False)

    # Performance metrics
    avg_session_duration = Column(Float, nullable=True)  # seconds
    avg_overall_score = Column(Float, nullable=True)

    # Cost tracking
    total_openai_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)

    def __repr__(self):
        return f"<SystemMetrics(date={self.date}, active_users={self.active_users})>"