"""
app/core/oauth2.py - Authentication & Authorization

This module handles:
- User authentication (extracting user from JWT)
- Authorization (role-based access control)
- Dependency injection for protected routes
- Interview session ownership verification

Separation of concerns:
- security.py: Pure security functions (hashing, JWT creation)
- oauth2.py: FastAPI dependencies and auth logic
"""

from typing import Optional
from fastapi import Depends, status, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
import logging

from .database import get_db
from .security import verify_token, verify_token_type
from ..models.user import User
from ..config import settings

logger = logging.getLogger(__name__)

# ==================== SECURITY SCHEMES ====================

# HTTPBearer for API requests (Authorization: Bearer <token>)
security = HTTPBearer()

# OAuth2PasswordBearer for Swagger UI compatibility
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ==================== TOKEN EXTRACTION ====================

async def get_token_from_bearer(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract token from Authorization: Bearer header.

    Args:
        credentials: Bearer token credentials

    Returns:
        Token string
    """
    return credentials.credentials


# ==================== CORE AUTHENTICATION ====================

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.

    This is the base dependency for ALL protected routes.

    Flow:
    1. Extract token from Authorization header
    2. Verify token signature and expiration
    3. Extract user email from token
    4. Fetch user from database
    5. Verify user is active

    Args:
        credentials: Bearer token from Authorization header
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token invalid, expired, or user not found/inactive
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify token
        payload = verify_token(credentials.credentials)

        if not payload:
            logger.warning("Token verification failed: Invalid signature or expired")
            raise credentials_exception

        # Verify token type
        if not verify_token_type(payload, "access"):
            logger.warning("Token type mismatch: Expected 'access' token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract user identifier
        user_email: str = payload.get("sub")
        if user_email is None:
            logger.warning("Token missing 'sub' claim")
            raise credentials_exception

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise credentials_exception

    # Fetch user from database
    try:
        result = await db.execute(
            select(User).options(joinedload(User.subscription)).where(User.email == user_email)
        )
        user = result.scalar_one_or_none()

        if user is None:
            logger.warning(f"User not found in database: {user_email}")
            raise credentials_exception

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user_email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )

        logger.debug(f"✓ Authenticated: {user.email} (role: {user.role})")
        logger.debug(f"User subscription: {user.subscription}")
        if user.subscription:
             logger.debug(f"Subscription status: {user.subscription.status}")
        else:
             logger.warning(f"!!! User {user.email} HAS NO SUBSCRIPTION LOADED !!!")
             
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure user is active.

    This is redundant since get_current_user already checks,
    but kept for semantic clarity and backwards compatibility.

    Args:
        current_user: Authenticated user

    Returns:
        User object
    """
    return current_user


# ==================== ROLE-BASED AUTHORIZATION ====================

async def get_current_admin(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Require user to be an admin.

    Used for:
    - Managing job categories
    - Managing question templates
    - Viewing system metrics
    - User management

    Args:
        current_user: Authenticated user

    Returns:
        User object if admin

    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != "admin":
        logger.warning(
            f"⚠ Access denied: {current_user.email} attempted admin action "
            f"(role: {current_user.role})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    logger.debug(f"✓ Admin access granted: {current_user.email}")
    return current_user


# ==================== RESOURCE OWNERSHIP VERIFICATION ====================

async def verify_interview_ownership(
        session_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Verify user owns the specified interview session.

    CRITICAL for security: Prevents users from accessing other users' interviews.

    Args:
        session_id: Interview session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        User object if ownership verified

    Raises:
        HTTPException: If session not found or user doesn't own it
    """
    from ..models.interview_session import InterviewSession

    try:
        # Fetch session
        result = await db.execute(
            select(InterviewSession).where(
                InterviewSession.id == session_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            logger.warning(f"Interview session not found: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview session not found"
            )

        # Verify ownership
        if str(session.user_id) != str(current_user.id):
            logger.warning(
                f"⚠ Unauthorized access attempt: {current_user.email} "
                f"tried to access session {session_id} (owner: {session.user_id})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this interview session"
            )

        logger.debug(f"✓ Interview ownership verified: {session_id}")
        return current_user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying interview ownership: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error verifying session ownership"
        )


# ==================== RATE LIMITING CHECKS ====================

async def check_interview_limit(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Check if user has exceeded their monthly interview limit.

    Free tier: 5 interviews per month
    Premium tier: Unlimited (future feature)

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        User object if limit not exceeded

    Raises:
        HTTPException: If monthly limit exceeded
    """
    from datetime import datetime

    # Check if we need to reset the counter (new month)
    if current_user.last_interview_reset_date:
        last_reset = current_user.last_interview_reset_date
        current_month = datetime.utcnow().month
        last_reset_month = last_reset.month

        # Reset counter if new month
        if current_month != last_reset_month:
            current_user.interview_count_current_month = 0
            current_user.last_interview_reset_date = datetime.utcnow()
            await db.commit()
            logger.info(f"Reset interview count for user: {current_user.email}")

    # Check limit
    FREE_TIER_LIMIT = settings.FREE_TIER_MONTHLY_LIMIT

    if current_user.interview_count_current_month >= FREE_TIER_LIMIT:
        logger.warning(
            f"⚠ Interview limit exceeded: {current_user.email} "
            f"({current_user.interview_count_current_month}/{FREE_TIER_LIMIT})"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly interview limit reached ({FREE_TIER_LIMIT}/{FREE_TIER_LIMIT}). "
                   "Upgrade to Pro for unlimited interviews."
        )

    return current_user


async def increment_interview_count(
        current_user: User,
        db: AsyncSession
) -> None:
    """
    Increment user's interview count after starting a session.

    Call this AFTER successfully creating an interview session.

    Args:
        current_user: User object
        db: Database session
    """
    current_user.interview_count_current_month += 1
    await db.commit()
    await db.refresh(current_user)

    logger.info(
        f"Interview count incremented: {current_user.email} "
        f"({current_user.interview_count_current_month}/{settings.FREE_TIER_MONTHLY_LIMIT})"
    )


# ==================== ROLE CHECKER CLASS ====================

class RoleChecker:
    """
    Flexible role-based access control.

    Usage in routes:
        # Single role
        @router.get("/admin", dependencies=[Depends(RoleChecker(["admin"]))])

        # Multiple roles
        @router.get("/staff", dependencies=[Depends(RoleChecker(["admin", "teacher"]))])
    """

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            logger.warning(
                f"⚠ Role check failed: {current_user.email} "
                f"(has: {current_user.role}, needs: {self.allowed_roles})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {', '.join(self.allowed_roles)}"
            )

        return current_user


# ==================== PRE-CONFIGURED DEPENDENCIES ====================

# Common role checkers
require_admin = RoleChecker(["admin"])
require_user = RoleChecker(["user", "admin"])  # All authenticated users


# ==================== TOKEN REFRESH LOGIC ====================

async def verify_refresh_token(
        token: str,
        db: AsyncSession = Depends(get_db)
) -> User:
    """
    Verify refresh token and return user.

    Used for token refresh endpoint.

    Args:
        token: Refresh token string
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )

    try:
        # Verify token
        payload = verify_token(token)

        if not payload:
            raise credentials_exception

        # Verify it's a refresh token
        if not verify_token_type(payload, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected refresh token"
            )

        user_email: str = payload.get("sub")
        if not user_email:
            raise credentials_exception

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh token verification error: {e}")
        raise credentials_exception

    # Fetch user
    result = await db.execute(
        select(User).where(User.email == user_email)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    return user


# ==================== UTILITY FUNCTIONS ====================

def get_user_from_token(token: str) -> Optional[dict]:
    """
    Extract user info from token without database lookup.

    Useful for logging or non-critical operations.

    Args:
        token: JWT token string

    Returns:
        Dict with user info or None
    """
    payload = verify_token(token)
    if not payload:
        return None

    return {
        "email": payload.get("sub"),
        "user_id": payload.get("user_id"),
        "role": payload.get("role")
    }


async def get_user_by_id(
        user_id: str,
        db: AsyncSession
) -> Optional[User]:
    """
    Fetch user by ID.

    Args:
        user_id: User UUID
        db: Database session

    Returns:
        User object or None
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(
        email: str,
        db: AsyncSession
) -> Optional[User]:
    """
    Fetch user by email.

    Args:
        email: User email address
        db: Database session

    Returns:
        User object or None
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


# ==================== LOGGING HELPERS ====================

def log_authentication_attempt(email: str, success: bool):
    """Log authentication attempts for security monitoring."""
    if success:
        logger.info(f"✓ Login successful: {email}")
    else:
        logger.warning(f"✗ Login failed: {email}")


def log_authorization_attempt(user_email: str, resource: str, success: bool):
    """Log authorization attempts for audit trail."""
    if success:
        logger.debug(f"✓ Access granted: {user_email} → {resource}")
    else:
        logger.warning(f"✗ Access denied: {user_email} → {resource}")