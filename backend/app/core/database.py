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
# Create async engine
# Handle invalid query params for asyncpg
db_url = settings.DATABASE_URL
connect_args = {}

# List of params not supported by asyncpg
unsupported_params = ["sslmode", "channel_binding", "gssencmode"]

if "?" in db_url:
    base_url, query = db_url.split("?", 1)
    params = query.split("&")
    valid_params = []
    
    found_unsupported = False
    for p in params:
        key = p.split("=")[0]
        if key in unsupported_params:
            found_unsupported = True
        else:
            valid_params.append(p)
            
    # Reconstruct URL without unsupported params
    db_url = base_url + ("?" + "&".join(valid_params) if valid_params else "")
    
    # If we stripped params (likely prod DB), enforce SSL
    if found_unsupported or "neon.tech" in db_url or "supabase.co" in db_url:
        connect_args["ssl"] = "require"

engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    future=True,
    poolclass=NullPool,  # disable pooling in debug
    connect_args=connect_args
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