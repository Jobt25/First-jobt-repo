"""
app/routers/api/v1/auth.py

Authentication routes for Jobt AI Career Coach:
- User registration
- Login (regular + Swagger-compatible)
- Token refresh
- Profile management
- Password change
- Password reset (request + confirm)
- Logout
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_password_reset_token,
    validate_password_strength
)
from app.core.oauth2 import get_current_user, verify_refresh_token

from app.schemas.auth_schema import (
    UserLogin,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
    RefreshTokenRequest
)
from app.schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserResponse
)
from app.models.user import User
from app.models.password_reset import PasswordReset
from app.models.subscription import Subscription
from app.services.email_service import EmailService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


# ==================== HELPER FUNCTIONS ====================

async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    """Fetch user by email"""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def create_trial_subscription(user_id: str, db: AsyncSession) -> Subscription:
    """Create a free trial subscription for new user"""
    from datetime import datetime, timedelta

    subscription = Subscription(
        user_id=user_id,
        plan="free",
        status="trial",
        billing_cycle="monthly",
        trial_ends_at=datetime.utcnow() + timedelta(days=30),
        max_interviews_per_month=5,  # Free tier limit
        interviews_used_this_month=0
    )
    db.add(subscription)
    return subscription


# ==================== REGISTRATION ====================

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserCreate,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.

    Process:
    1. Validate email uniqueness
    2. Validate password strength
    3. Create user record
    4. Create free trial subscription (30 days, 5 interviews)
    5. Return access token + refresh token

    Free Trial Benefits:
    - 5 interviews per month
    - Basic feedback analysis
    - Progress tracking
    - 30-day trial period
    """
    logger.info(f"Registration attempt for email: {user_data.email}")

    # Check if email already exists
    existing_user = await get_user_by_email(user_data.email, db)

    if existing_user:
        logger.warning(f"Registration failed: Email {user_data.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please login or use password reset if you forgot your password."
        )

    # Validate password strength
    is_valid, error_message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    try:
        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            current_job_title=user_data.current_job_title,
            target_job_role=user_data.target_job_role,
            years_of_experience=user_data.years_of_experience,
            role="user",  # Default role
            is_active=True,
            is_verified=False  # Require email verification (future feature)
        )
        db.add(user)
        await db.flush()  # Get user.id without committing

        logger.info(f"User created: {user.email} (ID: {user.id})")

        # Create trial subscription
        subscription = await create_trial_subscription(str(user.id), db)

        # Commit all changes
        await db.commit()
        await db.refresh(user)

        logger.info(f"✓ Registration successful for {user.email} with 30-day trial")

        # Send welcome email (Background Task)
        email_service = EmailService()
        background_tasks.add_task(
            email_service.send_welcome_email,
            user.email,
            user.full_name or "User"
        )

        # Create tokens
        access_token = create_access_token(
            data={
                "sub": user.email,
                "user_id": str(user.id),
                "role": user.role
            }
        )

        refresh_token = create_refresh_token(
            data={
                "sub": user.email,
                "user_id": str(user.id)
            }
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,  # 1 hour
            refresh_token=refresh_token
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed. Please try again later."
        )


# ==================== LOGIN ====================

@router.post("/login", response_model=Token)
async def login(
        login_data: UserLogin,
        db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return access + refresh tokens.

    Returns:
    - access_token: Short-lived JWT (1 hour)
    - refresh_token: Long-lived JWT (30 days)
    - expires_in: Token expiration time in seconds
    """
    logger.info(f"Login attempt for email: {login_data.email}")

    # Find user
    user = await get_user_by_email(login_data.email, db)

    # Verify credentials
    if not user or not verify_password(login_data.password, user.hashed_password):
        logger.warning(f"Login failed: Invalid credentials for {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login failed: User {login_data.email} is deactivated")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support at support@jobt.ai"
        )

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    await db.commit()

    logger.info(f"✓ Login successful for {user.email}")

    # Create tokens
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "role": user.role
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": user.email,
            "user_id": str(user.id)
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,  # 1 hour
        refresh_token=refresh_token
    )


@router.post("/login/swagger", response_model=Token)
async def login_swagger(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    """
    Swagger UI compatible login endpoint.

    OAuth2 spec uses "username" field → We treat it as email.
    Enables the "Authorize" button in Swagger UI (/docs).
    """
    email = form_data.username
    password = form_data.password

    logger.info(f"[Swagger] Login attempt for: {email}")

    # Find user
    user = await get_user_by_email(email, db)

    # Verify credentials
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"[Swagger] Login failed for {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()

    logger.info(f"✓ [Swagger] Login successful for {email}")

    # Create tokens
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "role": user.role
        }
    )

    refresh_token = create_refresh_token(
        data={
            "sub": user.email,
            "user_id": str(user.id)
        }
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        refresh_token=refresh_token
    )


# ==================== TOKEN REFRESH ====================

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
        request: RefreshTokenRequest,
        db: AsyncSession = Depends(get_db)
):
    """
    Get a new access token using refresh token.

    Refresh tokens are long-lived (30 days) and can be used
    to obtain new access tokens without re-authentication.
    """
    logger.info("Token refresh attempt")

    # Verify refresh token
    user = await verify_refresh_token(request.refresh_token, db)

    # Create new access token
    access_token = create_access_token(
        data={
            "sub": user.email,
            "user_id": str(user.id),
            "role": user.role
        }
    )

    logger.info(f"✓ Token refreshed for {user.email}")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        refresh_token=request.refresh_token  # Return same refresh token
    )


# ==================== GET CURRENT USER ====================

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
        current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.

    Requires: Valid JWT token in Authorization header
    """
    return UserResponse.model_validate(current_user)


# ==================== UPDATE PROFILE ====================

@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
        profile_data: UserUpdate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile.

    Allowed fields:
    - full_name
    - current_job_title
    - target_job_role
    - years_of_experience
    """
    logger.info(f"Profile update for {current_user.email}")

    # Update only provided fields
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    current_user.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(current_user)

    logger.info(f"✓ Profile updated for {current_user.email}")

    return UserResponse.model_validate(current_user)


# ==================== CHANGE PASSWORD ====================

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
        current_password: str,
        new_password: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Change password for authenticated user.

    Requires:
    - current_password: For verification
    - new_password: Must meet strength requirements
    """
    logger.info(f"Password change attempt for {current_user.email}")

    # Verify current password
    if not verify_password(current_password, current_user.hashed_password):
        logger.warning(f"Password change failed: Wrong current password for {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Validate new password strength
    is_valid, error_message = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Update password
    current_user.hashed_password = get_password_hash(new_password)
    current_user.updated_at = datetime.utcnow()

    await db.commit()

    logger.info(f"✓ Password changed for {current_user.email}")

    return {
        "message": "Password changed successfully",
        "detail": "Please login again with your new password"
    }


# ==================== PASSWORD RESET (REQUEST) ====================

@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(
        reset_data: PasswordResetRequest,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    """
    Request password reset email.

    Process:
    1. Validate email exists
    2. Generate reset token (valid for 24 hours)
    3. Save token to database
    4. Send reset email (background task)

    Note: Always returns success to prevent email enumeration
    """
    logger.info(f"Password reset requested for: {reset_data.email}")

    # Find user (don't reveal if email exists for security)
    user = await get_user_by_email(reset_data.email, db)

    if user:
        # Generate secure reset token
        reset_token = generate_password_reset_token()

        # Save to database
        password_reset = PasswordReset(
            user_id=user.id,
            token=reset_token,
            expires_at=datetime.utcnow() + timedelta(hours=24),
            used=False
        )
        db.add(password_reset)
        await db.commit()

        # Send email in background
        email_service = EmailService()
        background_tasks.add_task(
            email_service.send_password_reset_email,
            user.email,
            reset_token
        )

        logger.info(f"Reset token generated for {user.email}")
        logger.warning(
            f"[MVP MODE] Reset token for {user.email}: {reset_token}\n"
            f"Reset link: http://localhost:3000/reset-password?token={reset_token}\n"
            f"Email sent via EmailService (check logs if mock mode)."
        )
    else:
        logger.info(f"Password reset requested for non-existent email: {reset_data.email}")

    # Always return success (prevents email enumeration)
    return {
        "message": "If the email exists, a password reset link has been sent.",
        "detail": "Please check your email and follow the instructions.",
        "note": "[MVP] Check server logs for reset token"
    }


# ==================== PASSWORD RESET (CONFIRM) ====================

@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
        reset_data: PasswordResetConfirm,
        db: AsyncSession = Depends(get_db)
):
    """
    Confirm password reset with token.

    Process:
    1. Verify reset token exists and is not expired
    2. Verify token hasn't been used
    3. Update user password
    4. Mark token as used
    """
    logger.info("Password reset confirmation attempt")

    # Find token
    result = await db.execute(
        select(PasswordReset).where(
            PasswordReset.token == reset_data.token,
            PasswordReset.used == False
        )
    )
    password_reset = result.scalar_one_or_none()

    # Verify token exists and is valid
    if not password_reset:
        logger.warning("Password reset failed: Invalid token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used reset token"
        )

    # Check if expired
    if datetime.utcnow() > password_reset.expires_at:
        logger.warning("Password reset failed: Expired token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired. Please request a new one."
        )

    # Validate new password
    is_valid, error_message = validate_password_strength(reset_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Get user
    result = await db.execute(
        select(User).where(User.id == password_reset.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.updated_at = datetime.utcnow()

    # Mark token as used
    password_reset.used = True

    await db.commit()

    logger.info(f"✓ Password reset successful for {user.email}")

    return {
        "message": "Password reset successful",
        "detail": "You can now login with your new password",
        "email": user.email
    }


# ==================== LOGOUT ====================

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
        current_user: User = Depends(get_current_user)
):
    """
    Logout current user.

    Note: JWT tokens are stateless, so actual logout requires:
    - Client discarding the token
    - (Optional) Token blacklist in Redis for immediate invalidation

    For MVP, client-side token deletion is sufficient.

    Future Enhancement:
    - Implement Redis-based token blacklist
    - Add "Logout from all devices" feature
    """
    logger.info(f"User logged out: {current_user.email}")

    # TODO: Add token to Redis blacklist
    # await redis_client.setex(
    #     f"blacklist:{token}",
    #     timedelta(hours=1),
    #     "logged_out"
    # )

    return {
        "message": "Logged out successfully",
        "detail": "Token will expire naturally after 1 hour. Please delete the token on your client."
    }


# ==================== VERIFY EMAIL (Future Feature) ====================

@router.post("/verify-email/{token}", status_code=status.HTTP_200_OK)
async def verify_email(
        token: str,
        db: AsyncSession = Depends(get_db)
):
    """
    Verify user email with token.

    This is a placeholder for future email verification feature.
    """
    # TODO: Implement email verification
    return {
        "message": "Email verification endpoint - To be implemented",
        "status": "coming_soon"
    }