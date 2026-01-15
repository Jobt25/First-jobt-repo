# app/models/base.py
import enum

"""
app/models/base.py - Base SQLAlchemy Models

Contains reusable base classes with common fields:
- TimestampMixin: created_at, updated_at
- UUIDMixin: UUID primary key
- BaseModel: Combines both + common methods

All models should inherit from BaseModel for consistency.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.types import TypeDecorator, CHAR
import uuid

from ..core.database import Base


# ==================== CUSTOM TYPES ====================

class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type for PostgreSQL,
    and CHAR(36) for SQLite/others, handling conversion transparently.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return str(value)
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            try:
                return uuid.UUID(value)
            except ValueError:
                return value
        return value


# ==================== MIXINS ====================

@declarative_mixin
class TimestampMixin:
    """
    Mixin that adds timestamp fields to models.

    Fields:
        created_at: Record creation timestamp (auto-set)
        updated_at: Record last update timestamp (auto-updated)
    """

    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            default=datetime.utcnow,
            nullable=False,
            index=True
        )

    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=True
        )


@declarative_mixin
class UUIDMixin:
    """
    Mixin that adds UUID primary key to models.

    Fields:
        id: UUID v4 primary key (auto-generated)
    """

    @declared_attr
    def id(cls):
        return Column(
            GUID(),
            primary_key=True,
            default=uuid.uuid4,
            unique=True,
            nullable=False,
            index=True
        )


# ==================== BASE MODEL ====================

class BaseModel(Base, UUIDMixin, TimestampMixin):
    """
    Base model class that all models should inherit from.

    Provides:
    - UUID primary key (id)
    - Timestamps (created_at, updated_at)
    - Common utility methods

    Usage:
        class User(BaseModel):
            __tablename__ = "users"
            email = Column(String, unique=True)
    """

    __abstract__ = True  # This won't create a table

    def to_dict(self) -> dict:
        """
        Convert model instance to dictionary.

        Returns:
            Dict with all column values
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def update_from_dict(self, data: dict) -> None:
        """
        Update model fields from dictionary.

        Args:
            data: Dictionary with field names and values
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation of model."""
        return f"<{self.__class__.__name__}(id={self.id})>"

    @classmethod
    def get_tablename(cls) -> str:
        """Get table name for this model."""
        return cls.__tablename__


# ==================== UTILITY FUNCTIONS ====================

def generate_uuid() -> uuid.UUID:
    """Generate a new UUID v4."""
    return uuid.uuid4()


def is_valid_uuid(value: str) -> bool:
    """
    Check if string is a valid UUID.

    Args:
        value: String to check

    Returns:
        True if valid UUID
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


class UserRole(str, enum.Enum):
    """

    """
    USER = "user"
    ADMIN = "admin"


class InterviewStatus(str, enum.Enum):
    """

    """
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class DifficultyLevel(str, enum.Enum):
    """

    """
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

