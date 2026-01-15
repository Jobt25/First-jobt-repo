# ==================== app/models/interview_session.py ====================
"""Interview session model"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel, InterviewStatus


class InterviewSession(BaseModel):
    """
    Interview session tracking.

    Stores full conversation history and metadata.

    Relationships:
        - user: Many-to-one with User
        - job_category: Many-to-one with JobCategory
        - feedback: One-to-one with InterviewFeedback
    """

    __tablename__ = "interview_sessions"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Session metadata
    status = Column(
        SQLEnum(InterviewStatus),
        default=InterviewStatus.IN_PROGRESS,
        nullable=False,
        index=True
    )
    difficulty = Column(String(50), nullable=False)  # beginner/intermediate/advanced

    # Conversation data (JSONB for flexibility, JSON for SQLite tests)
    conversation_history = Column(JSON().with_variant(JSONB, "postgresql"), default=list, nullable=False)
    # Format: [{"role": "interviewer", "content": "...", "timestamp": "..."}, ...]

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # AI usage tracking (cost control)
    total_tokens_used = Column(Integer, default=0, nullable=False)
    openai_model_used = Column(String(100), nullable=True)

    # Relationships
    user = relationship("User", back_populates="interview_sessions")
    job_category = relationship("JobCategory", back_populates="interview_sessions")
    feedback = relationship(
        "InterviewFeedback",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<InterviewSession(user_id={self.user_id}, status={self.status})>"

