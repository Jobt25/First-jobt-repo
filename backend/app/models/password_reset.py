# ==================== app/models/password_reset.py ====================
"""Password reset token model"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class PasswordReset(BaseModel):
    """
    Password reset token tracking.

    Tokens expire after 24 hours and can only be used once.
    """

    __tablename__ = "password_resets"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    # Relationship
    user = relationship("User", back_populates="password_resets")

    def __repr__(self):
        return f"<PasswordReset(user_id={self.user_id}, used={self.used})>"
