# ==================== app/models/job_category.py ====================
"""Job category model"""

from sqlalchemy import Column, String, Text, Boolean, Integer
from sqlalchemy.orm import relationship

from .base import BaseModel


class JobCategory(BaseModel):
    """
    Job categories for interview practice.

    Examples: Software Engineer, Product Manager, Sales Rep

    Relationships:
        - question_templates: One-to-many with QuestionTemplate
        - interview_sessions: One-to-many with InterviewSession
    """

    __tablename__ = "job_categories"

    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    industry = Column(String(255), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    typical_questions_count = Column(Integer, default=0, nullable=False)

    # Relationships
    question_templates = relationship(
        "QuestionTemplate",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    interview_sessions = relationship(
        "InterviewSession",
        back_populates="job_category",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<JobCategory(name={self.name}, industry={self.industry})>"
