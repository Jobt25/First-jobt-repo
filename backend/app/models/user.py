"""
app/models/user.py

User model - authentication and profile data with subscription support
"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import BaseModel


class UserRole(str, enum.Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """
    User model for authentication and profile management.

    Relationships:
        - interview_sessions: One-to-many with InterviewSession
        - password_resets: One-to-many with PasswordReset
        - subscription: One-to-one with Subscription
    """

    __tablename__ = "users"

    # Authentication
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.USER.value, nullable=False)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Profile information
    full_name = Column(String(255), nullable=True)
    current_job_title = Column(String(255), nullable=True)
    target_job_role = Column(String(255), nullable=True)
    years_of_experience = Column(Integer, nullable=True)

    # Usage tracking (kept for backward compatibility, but subscription table is primary)
    interview_count_current_month = Column(Integer, default=0, nullable=False)
    last_interview_reset_date = Column(DateTime(timezone=True), default=func.now())

    # Activity tracking
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    interview_sessions = relationship(
        "InterviewSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    password_resets = relationship(
        "PasswordReset",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    subscription = relationship(
        "Subscription",
        back_populates="user",
        uselist=False,  # One-to-one
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<User(email={self.email}, role={self.role})>"

    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN.value

    @property
    def has_active_subscription(self) -> bool:
        """Check if user has active subscription"""
        return self.subscription and self.subscription.is_active

    @property
    def can_start_interview(self) -> bool:
        """Check if user can start a new interview"""
        if not self.subscription:
            return False
        return self.subscription.can_start_interview

    @property
    def subscription_plan(self) -> str:
        """Get user's subscription plan"""
        if not self.subscription:
            return "none"
        return self.subscription.plan