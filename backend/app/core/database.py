"""
app/core/database.py - Database Configuration and Connection
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from ..config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    poolclass=NullPool,  # disable pooling in debug
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base
Base = declarative_base()


# ============================================
# DEPENDENCY INJECTION
# ============================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions

    Usage in FastAPI routes:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db here
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================
# DATABASE INITIALIZATION
# ============================================

async def init_db():
    """
    Initialize database - create all tables

    Call this from main.py on startup:
        @app.on_event("startup")
        async def startup_event():
            await init_db()
    """
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from app import models  # noqa: F401

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db():
    """
    Close database connections

    Call this from main.py on shutdown:
        @app.on_event("shutdown")
        async def shutdown_event():
            await close_db()
    """
    await engine.dispose()
    logger.info("Database connections closed")


# ============================================
# DATABASE UTILITIES
# ============================================

async def check_db_connection() -> bool:
    """
    Check if database connection is healthy

    Returns:
        True if connection is successful
    """
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def reset_monthly_interview_counts():
    """
    Reset all users' monthly interview counts
    Should be called via scheduled task (e.g., cron job on 1st of each month)
    """
    from app.models import User
    from sqlalchemy import update
    from datetime import datetime

    async with AsyncSessionLocal() as session:
        try:
            stmt = update(User).values(
                interview_count_current_month=0,
                last_interview_reset_date=datetime.utcnow()
            )
            await session.execute(stmt)
            await session.commit()
            logger.info("Monthly interview counts reset successfully")
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to reset monthly counts: {e}")
            raise