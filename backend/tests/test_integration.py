"""
tests/test_integration.py

Integration tests for complete user journeys.

Tests:
- Full user journey from registration to analytics
- Subscription limit enforcement
- Multiple interviews tracking
"""

import pytest
from httpx import AsyncClient


# ==================== FULL USER JOURNEY TEST ====================

@pytest.mark.asyncio
async def test_full_user_journey(
    test_client: AsyncClient,
    test_category,
    mock_openai_service
):
    """
    Test complete user journey:
    1. Register
    2. Start interview
    3. Complete interview
    4. View feedback
    5. Check analytics
    """
    # 1. Register
    register_response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "journey@example.com",
            "password": "Journey123!",
            "full_name": "Journey User",
            "current_job_title": "Developer",
            "target_job_role": "Senior Developer"
        }
    )
    
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Start interview
    start_response = await test_client.post(
        "/api/v1/interviews/start",
        headers=headers,
        json={
            "category_id": str(test_category.id),
            "difficulty": "beginner"
        }
    )
    
    assert start_response.status_code == 201
    session_id = start_response.json()["id"]
    
    # 3. Send a few messages
    for i in range(3):
        message_response = await test_client.post(
            f"/api/v1/interviews/{session_id}/message",
            headers=headers,
            json={"message": f"Test response {i+1}"}
        )
        assert message_response.status_code == 200
    
    # 4. End interview
    end_response = await test_client.post(
        f"/api/v1/interviews/{session_id}/end",
        headers=headers
    )
    
    assert end_response.status_code == 200
    assert end_response.json()["feedback_generated"] is True
    
    # 5. View feedback
    feedback_response = await test_client.get(
        f"/api/v1/feedback/{session_id}",
        headers=headers
    )
    
    assert feedback_response.status_code == 200
    feedback_data = feedback_response.json()
    assert "overall_score" in feedback_data
    assert "strengths" in feedback_data
    
    # 6. Check analytics
    analytics_response = await test_client.get(
        "/api/v1/analytics/statistics",
        headers=headers
    )
    
    assert analytics_response.status_code == 200
    analytics_data = analytics_response.json()
    assert analytics_data["total_interviews"] == 1
    
    # 7. Check progress trends
    trends_response = await test_client.get(
        "/api/v1/analytics/progress",
        headers=headers,
        params={"period": "7d"}
    )
    
    assert trends_response.status_code == 200
    trends_data = trends_response.json()
    assert len(trends_data["data_points"]) == 1


# ==================== SUBSCRIPTION LIMIT ENFORCEMENT TEST ====================

@pytest.mark.asyncio
async def test_subscription_limit_enforcement(
    test_client: AsyncClient,
    test_category,
    mock_openai_service
):
    """
    Test that subscription limits are enforced across multiple sessions.
    """
    # Register user (gets 5 free interviews)
    register_response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "limits@example.com",
            "password": "Limits123!",
            "full_name": "Limits User"
        }
    )
    
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Complete 5 interviews (free tier limit)
    for i in range(5):
        # Start interview
        start_response = await test_client.post(
            "/api/v1/interviews/start",
            headers=headers,
            json={
                "category_id": str(test_category.id),
                "difficulty": "beginner"
            }
        )
        
        assert start_response.status_code == 201
        session_id = start_response.json()["id"]
        
        # End interview
        await test_client.post(
            f"/api/v1/interviews/{session_id}/end",
            headers=headers
        )
    
    # Try to start 6th interview (should fail)
    sixth_response = await test_client.post(
        "/api/v1/interviews/start",
        headers=headers,
        json={
            "category_id": str(test_category.id),
            "difficulty": "beginner"
        }
    )
    
    assert sixth_response.status_code == 429  # Too Many Requests
    assert "limit" in sixth_response.json()["detail"].lower()


# ==================== MULTIPLE INTERVIEWS TRACKING TEST ====================

@pytest.mark.asyncio
async def test_multiple_interviews_tracking(
    test_client: AsyncClient,
    test_category,
    mock_openai_service
):
    """
    Test that progress is tracked correctly across multiple interviews.
    """
    # Register user
    register_response = await test_client.post(
        "/api/v1/auth/register",
        json={
            "email": "tracking@example.com",
            "password": "Tracking123!",
            "full_name": "Tracking User"
        }
    )
    
    assert register_response.status_code == 201, f"Registration failed: {register_response.text}"
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Complete 3 interviews
    session_ids = []
    for i in range(3):
        start_response = await test_client.post(
            "/api/v1/interviews/start",
            headers=headers,
            json={
                "category_id": str(test_category.id),
                "difficulty": "intermediate"
            }
        )
        
        session_id = start_response.json()["id"]
        session_ids.append(session_id)
        
        # Send a message
        await test_client.post(
            f"/api/v1/interviews/{session_id}/message",
            headers=headers,
            json={"message": "Test response"}
        )
        
        # End interview
        await test_client.post(
            f"/api/v1/interviews/{session_id}/end",
            headers=headers
        )
    
    # Check that all 3 are tracked
    stats_response = await test_client.get(
        "/api/v1/analytics/statistics",
        headers=headers
    )
    
    assert stats_response.status_code == 200
    stats_data = stats_response.json()
    assert stats_data["total_interviews"] == 3
    
    # Check feedback summary
    summary_response = await test_client.get(
        "/api/v1/feedback/summary",
        headers=headers
    )
    
    assert summary_response.status_code == 200
    summary_data = summary_response.json()
    assert summary_data["total_interviews"] == 3
    
    # Compare all 3 sessions
    compare_response = await test_client.post(
        "/api/v1/feedback/compare",
        headers=headers,
        json={"session_ids": session_ids}
    )
    
    assert compare_response.status_code == 200
    compare_data = compare_response.json()
    assert compare_data["sessions_compared"] == 3
