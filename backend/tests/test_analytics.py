"""
tests/test_analytics.py

Analytics system tests.

Tests:
- Progress trends
- Score breakdown
- User statistics
- Category comparison
"""

import pytest
from httpx import AsyncClient
from app.models.interview_session import InterviewSession


# ==================== PROGRESS TRENDS TESTS ====================

@pytest.mark.asyncio
async def test_get_progress_trends(
    test_client: AsyncClient,
    auth_headers: dict,
    test_interview_session: InterviewSession
):
    """Test getting progress trends"""
    response = await test_client.get(
        "/api/v1/analytics/progress",
        headers=auth_headers,
        params={"period": "30d"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data_points" in data
    assert "trend" in data
    assert "total_interviews" in data
    assert data["period"] == "30d"


@pytest.mark.asyncio
async def test_progress_trends_different_periods(
    test_client: AsyncClient,
    auth_headers: dict,
    test_interview_session: InterviewSession
):
    """Test progress trends with different periods"""
    for period in ["7d", "30d", "90d", "all"]:
        response = await test_client.get(
            "/api/v1/analytics/progress",
            headers=auth_headers,
            params={"period": period}
        )
        
        assert response.status_code == 200
        assert response.json()["period"] == period


# ==================== SCORE BREAKDOWN TESTS ====================

@pytest.mark.asyncio
async def test_get_score_breakdown(
    test_client: AsyncClient,
    auth_headers: dict,
    test_interview_session: InterviewSession
):
    """Test getting score breakdown by category"""
    response = await test_client.get(
        "/api/v1/analytics/breakdown",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "total_categories" in data
    assert len(data["categories"]) >= 1


# ==================== USER STATISTICS TESTS ====================

@pytest.mark.asyncio
async def test_get_user_statistics(
    test_client: AsyncClient,
    auth_headers: dict,
    test_interview_session: InterviewSession
):
    """Test getting user statistics"""
    response = await test_client.get(
        "/api/v1/analytics/statistics",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_interviews" in data
    assert "total_time_spent_minutes" in data
    assert "average_scores" in data
    assert "most_practiced_category" in data
    assert "current_streak_days" in data
    assert "improvement_rate" in data
    assert data["total_interviews"] >= 1


# ==================== CATEGORY COMPARISON TESTS ====================

@pytest.mark.asyncio
async def test_get_category_comparison(
    test_client: AsyncClient,
    auth_headers: dict,
    test_interview_session: InterviewSession
):
    """Test getting category comparison"""
    response = await test_client.get(
        "/api/v1/analytics/comparison",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "comparison" in data
    assert "total_categories_practiced" in data
    assert data["total_categories_practiced"] >= 1


# ==================== EMPTY DATA TESTS ====================

@pytest.mark.asyncio
async def test_analytics_with_no_data(
    test_client: AsyncClient,
    test_db
):
    """Test analytics endpoints with user who has no interviews"""
    # Register new user
    register_response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "nodata@example.com",
            "password": "NoData123!",
            "full_name": "No Data User"
        }
    )
    
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test progress trends
    response = await test_client.get(
        "/api/v1/analytics/progress",
        headers=headers,
        params={"period": "30d"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_interviews"] == 0
    assert "message" in data
