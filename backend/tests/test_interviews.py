"""
tests/test_interviews.py

Interview system tests.

Tests:
- Starting interviews
- Sending messages
- Ending interviews
- Subscription limits
- Session timeout
- Question limits
"""

import pytest
from httpx import AsyncClient
from app.models.user import User
from app.models.job_category import JobCategory


# ==================== START INTERVIEW TESTS ====================

@pytest.mark.asyncio
async def test_start_interview_success(
    test_client: AsyncClient,
    auth_headers: dict,
    test_category: JobCategory,
    mock_openai_service
):
    """Test starting an interview successfully"""
    response = await test_client.post(
        "/api/v1/interviews/start",
        headers=auth_headers,
        json={
            "category_id": str(test_category.id),
            "difficulty": "intermediate"
        }
    )
    
    print(f"\nResponse status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["difficulty"] == "intermediate"
    assert "id" in data  # Session ID
    assert "conversation_history" in data  # Should have first question
    assert len(data["conversation_history"]) >= 1  # At least one message (first question)
    assert data["conversation_history"][0]["role"] == "interviewer"  # First message from AI



@pytest.mark.asyncio
async def test_start_interview_limit_exceeded(
    test_client: AsyncClient,
    auth_headers: dict,
    test_category: JobCategory,
    test_user: User,
    test_db,
    mock_openai_service
):
    """Test starting interview when monthly limit exceeded"""
    # Update subscription to max out interviews
    test_user.subscription.interviews_used_this_month = 5  # Free tier limit
    test_db.add(test_user.subscription)
    await test_db.commit()
    
    response = await test_client.post(
        "/api/v1/interviews/start",
        headers=auth_headers,
        json={
            "category_id": str(test_category.id),
            "difficulty": "beginner"
        }
    )
    
    assert response.status_code == 429  # Too Many Requests
    assert "limit" in response.json()["detail"].lower()


# ==================== SEND MESSAGE TESTS ====================

@pytest.mark.asyncio
async def test_send_message(
    test_client: AsyncClient,
    auth_headers: dict,
    test_category: JobCategory,
    mock_openai_service
):
    """Test sending a message during interview"""
    # Start interview first
    start_response = await test_client.post(
        "/api/v1/interviews/start",
        headers=auth_headers,
        json={
            "category_id": str(test_category.id),
            "difficulty": "intermediate"
        }
    )
    
    session_id = start_response.json()["id"]
    
    # Send message
    response = await test_client.post(
        f"/api/v1/interviews/{session_id}/message",
        headers=auth_headers,
        json={
            "content": "I have 3 years of experience in software development."
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "progress" in data
    assert "time_remaining_minutes" in data
    assert data["progress"]["questions_asked"] == 2


# ==================== END INTERVIEW TESTS ====================

@pytest.mark.asyncio
async def test_end_interview(
    test_client: AsyncClient,
    auth_headers: dict,
    test_category: JobCategory,
    mock_openai_service
):
    """Test ending an interview"""
    # Start interview
    start_response = await test_client.post(
        "/api/v1/interviews/start",
        headers=auth_headers,
        json={
            "category_id": str(test_category.id),
            "difficulty": "beginner"
        }
    )
    
    session_id = start_response.json()["id"]
    
    # End interview
    response = await test_client.post(
        f"/api/v1/interviews/{session_id}/end",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "successfully" in data["message"].lower()
    # Feedback is generated in background, so check for appropriate message
    assert "shortly" in data["message"].lower() or "feedback" in data["detail"].lower()


# ==================== LIST INTERVIEWS TESTS ====================

@pytest.mark.asyncio
async def test_list_interviews(
    test_client: AsyncClient,
    auth_headers: dict,
    test_interview_session
):
    """Test listing interview history"""
    response = await test_client.get(
        "/api/v1/interviews",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


# ==================== PROGRESS TRACKING TESTS ====================

@pytest.mark.asyncio
async def test_progress_tracking(
    test_client: AsyncClient,
    auth_headers: dict,
    test_category: JobCategory,
    mock_openai_service
):
    """Test that progress tracking works correctly"""
    # Start interview
    start_response = await test_client.post(
        "/api/v1/interviews/start",
        headers=auth_headers,
        json={
            "category_id": str(test_category.id),
            "difficulty": "intermediate"  # 7 questions
        }
    )
    
    session_id = start_response.json()["id"]
    
    # Send first message
    response = await test_client.post(
        f"/api/v1/interviews/{session_id}/message",
        headers=auth_headers,
        json={"content": "Test response"}
    )
    
    data = response.json()
    assert data["progress"]["questions_asked"] == 2
    assert data["progress"]["total_questions"] == 7
    assert data["progress"]["percentage"] > 0
