# ==================== app/models/question_template.py ====================
"""Question template model"""

from sqlalchemy import Column, String, Text, Boolean, Integer, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class DifficultyLevel(str, enum.Enum):
    """Question difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class QuestionTemplate(BaseModel):
    """
    Question templates for interviews.

    Admin-managed questions used by AI during interviews.
    """

    __tablename__ = "question_templates"

    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    question_text = Column(Text, nullable=False)
    difficulty = Column(
        SQLEnum(DifficultyLevel),
        default=DifficultyLevel.INTERMEDIATE,
        nullable=False,
        index=True
    )

    # Expected answer characteristics (for feedback scoring)
    expected_keywords = Column(JSONB, nullable=True)  # ["leadership", "teamwork"]
    ideal_response_length = Column(Integer, nullable=True)  # words

    # Usage analytics
    usage_count = Column(Integer, default=0, nullable=False)
    avg_user_score = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship
    category = relationship("JobCategory", back_populates="question_templates")

    def __repr__(self):
        return f"<QuestionTemplate(category_id={self.category_id}, difficulty={self.difficulty})>"
