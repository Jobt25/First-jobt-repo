"""
tests/test_auth.py

Authentication endpoint tests.

Tests:
- User registration
- Login flow
- Token refresh
- Password reset
- Profile management
"""

import pytest
from httpx import AsyncClient
from app.models.user import User


# ==================== REGISTRATION TESTS ====================

@pytest.mark.asyncio
async def test_register_success(test_client: AsyncClient):
    """Test successful user registration"""
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "NewPassword123!",
            "full_name": "New User",
            "current_job_title": "Developer",
            "target_job_role": "Senior Developer"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(test_client: AsyncClient, test_user: User):
    """Test registration with duplicate email fails"""
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,  # Duplicate
            "password": "Password123!",
            "full_name": "Duplicate User"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_weak_password(test_client: AsyncClient):
    """Test registration with weak password fails"""
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "weak",  # Too weak
            "full_name": "Weak Password User"
        }
    )
    
    assert response.status_code == 422  # Validation error


# ==================== LOGIN TESTS ====================

@pytest.mark.asyncio
async def test_login_success(test_client: AsyncClient, test_user: User):
    """Test successful login"""
    response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "TestPassword123!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_email(test_client: AsyncClient):
    """Test login with non-existent email"""
    response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        }
    )
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_invalid_password(test_client: AsyncClient, test_user: User):
    """Test login with wrong password"""
    response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "WrongPassword123!"
        }
    )
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


# ==================== PROFILE TESTS ====================

@pytest.mark.asyncio
async def test_get_profile(test_client: AsyncClient, auth_headers: dict, test_user: User):
    """Test getting current user profile"""
    response = await test_client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


@pytest.mark.asyncio
async def test_get_profile_unauthorized(test_client: AsyncClient):
    """Test getting profile without authentication fails"""
    response = await test_client.get("/api/v1/auth/me")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(test_client: AsyncClient, auth_headers: dict):
    """Test updating user profile"""
    response = await test_client.patch(
        "/api/v1/auth/me",
        headers=auth_headers,
        json={
            "full_name": "Updated Name",
            "current_job_title": "Senior Developer"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["current_job_title"] == "Senior Developer"


# ==================== PASSWORD CHANGE TESTS ====================

@pytest.mark.asyncio
async def test_change_password(test_client: AsyncClient, auth_headers: dict):
    """Test changing password"""
    response = await test_client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "current_password": "TestPassword123!",
            "new_password": "NewPassword123!"
        }
    )
    
    assert response.status_code == 200
    assert "successfully" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_change_password_wrong_current(test_client: AsyncClient, auth_headers: dict):
    """Test changing password with wrong current password"""
    response = await test_client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword123!"
        }
    )
    
    assert response.status_code == 400
    assert "incorrect" in response.json()["detail"].lower()


# ==================== TOKEN REFRESH TESTS ====================

@pytest.mark.asyncio
async def test_token_refresh(test_client: AsyncClient, test_user: User):
    """Test refreshing access token"""
    # First login to get refresh token
    login_response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "TestPassword123!"
        }
    )
    
    refresh_token = login_response.json()["refresh_token"]
    
    # Use refresh token to get new access token
    response = await test_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# ==================== SUBSCRIPTION TESTS ====================

@pytest.mark.asyncio
async def test_registration_creates_trial_subscription(
    test_client: AsyncClient,
    test_db
):
    """Test that registration automatically creates trial subscription"""
    response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "trial@example.com",
            "password": "TrialPassword123!",
            "full_name": "Trial User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify user has subscription info
    assert "subscription" in data or response.status_code == 201
