"""
app/core/security.py - Security Utilities

This module handles pure security operations:
- Password hashing and verification
- JWT token creation and verification
- Token payload encryption/decryption

NO authentication dependencies here - this is pure utility functions.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import logging

from ..config import settings

logger = logging.getLogger(__name__)

# ==================== PASSWORD HASHING ====================

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a plain password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.

    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (optional but recommended)

    Args:
        password: Plain text password

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    # Optional: Check for special characters
    # special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    # if not any(c in special_chars for c in password):
    #     return False, "Password must contain at least one special character"

    return True, ""


# ==================== JWT TOKEN OPERATIONS ====================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary containing claims (sub, email, role, etc.)
        expires_delta: Token expiration time (default: from settings)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    logger.debug(f"Access token created for: {data.get('sub', 'unknown')}")
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.

    Refresh tokens have longer expiration and are used to get new access tokens.

    Args:
        data: Dictionary containing claims (sub, email)
        expires_delta: Token expiration time (default: 30 days)

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()

    # Refresh tokens last 30 days by default
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Token payload dict or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token without verification (use cautiously).

    Args:
        token: JWT token string

    Returns:
        Token payload dict or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        return payload
    except Exception as e:
        logger.error(f"Token decode error: {e}")
        return None


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    Verify token is of expected type (access or refresh).

    Args:
        payload: Decoded token payload
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        True if token type matches
    """
    return payload.get("type") == expected_type


# ==================== SECURE RANDOM TOKENS ====================

def generate_password_reset_token() -> str:
    """
    Generate a secure random token for password reset.

    Returns:
        URL-safe random token (32 bytes)
    """
    return secrets.token_urlsafe(32)


def generate_verification_token() -> str:
    """
    Generate a secure random token for email verification.

    Returns:
        URL-safe random token (32 bytes)
    """
    return secrets.token_urlsafe(32)


def generate_api_key() -> str:
    """
    Generate a secure API key for external integrations.

    Returns:
        URL-safe random API key (48 bytes)
    """
    return f"jobt_{secrets.token_urlsafe(48)}"


# ==================== TOKEN VALIDATION ====================

def validate_token_expiry(payload: Dict[str, Any]) -> bool:
    """
    Check if token has expired.

    Args:
        payload: Decoded token payload

    Returns:
        True if token is still valid
    """
    exp = payload.get("exp")
    if not exp:
        return False

    expiry_time = datetime.fromtimestamp(exp)
    return datetime.utcnow() < expiry_time


def get_token_expiry_time(payload: Dict[str, Any]) -> Optional[datetime]:
    """
    Get token expiration datetime.

    Args:
        payload: Decoded token payload

    Returns:
        Datetime of expiration or None
    """
    exp = payload.get("exp")
    if not exp:
        return None

    return datetime.fromtimestamp(exp)


def get_time_until_expiry(payload: Dict[str, Any]) -> Optional[timedelta]:
    """
    Get time remaining until token expires.

    Args:
        payload: Decoded token payload

    Returns:
        Timedelta until expiry or None
    """
    expiry = get_token_expiry_time(payload)
    if not expiry:
        return None

    remaining = expiry - datetime.utcnow()
    return remaining if remaining.total_seconds() > 0 else timedelta(0)


# ==================== UTILITY FUNCTIONS ====================

def create_token_payload(
    user_id: str,
    email: str,
    role: str,
    **extra_claims
) -> Dict[str, Any]:
    """
    Create a standard token payload.

    Args:
        user_id: User UUID
        email: User email
        role: User role
        **extra_claims: Additional claims to include

    Returns:
        Dictionary with standard claims
    """
    payload = {
        "sub": email,  # Subject (standard JWT claim)
        "user_id": str(user_id),
        "email": email,
        "role": role,
    }

    # Add any extra claims
    if extra_claims:
        payload.update(extra_claims)

    return payload


def mask_email(email: str) -> str:
    """
    Mask email address for logging/display.

    Example: john.doe@example.com -> j***e@example.com

    Args:
        email: Email address

    Returns:
        Masked email
    """
    if "@" not in email:
        return email

    local, domain = email.split("@")
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    return f"{masked_local}@{domain}"


def is_strong_password(password: str) -> bool:
    """
    Quick check if password is strong.

    Args:
        password: Plain text password

    Returns:
        True if password meets minimum requirements
    """
    is_valid, _ = validate_password_strength(password)
    return is_valid


# ==================== CONSTANTS ====================

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# Default expiration times
DEFAULT_ACCESS_TOKEN_EXPIRE = timedelta(hours=1)
DEFAULT_REFRESH_TOKEN_EXPIRE = timedelta(days=30)
DEFAULT_PASSWORD_RESET_EXPIRE = timedelta(hours=24)
DEFAULT_EMAIL_VERIFICATION_EXPIRE = timedelta(days=7)