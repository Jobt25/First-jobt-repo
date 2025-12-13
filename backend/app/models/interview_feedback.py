# ==================== app/models/interview_feedback.py ====================
"""Interview feedback model"""

from sqlalchemy import Column, Text, Float, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .base import BaseModel


class InterviewFeedback(BaseModel):
    """
    AI-generated feedback for completed interviews.

    Stores scores, insights, and recommendations.
    """

    __tablename__ = "interview_feedback"

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Overall scores (0-100)
    overall_score = Column(Float, nullable=False)
    relevance_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    positivity_score = Column(Float, nullable=False)

    # Detailed analysis
    strengths = Column(JSONB, nullable=True)  # ["Clear communication", "Good examples"]
    weaknesses = Column(JSONB, nullable=True)  # ["Too many fillers", "Vague answers"]

    # AI-generated insights
    summary = Column(Text, nullable=True)
    actionable_tips = Column(JSONB, nullable=True)  # ["Practice STAR method"]

    # Metrics breakdown
    filler_words_count = Column(Integer, default=0, nullable=False)
    avg_response_length = Column(Integer, nullable=True)  # words
    response_time_avg = Column(Float, nullable=True)  # seconds

    # Relationship
    session = relationship("InterviewSession", back_populates="feedback")

    def __repr__(self):
        return f"<InterviewFeedback(session_id={self.session_id}, score={self.overall_score})>"
