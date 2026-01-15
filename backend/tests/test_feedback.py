"""
tests/test_feedback.py

Feedback system tests.

Tests:
- Getting feedback
- Feedback summary
- Feedback history
- Feedback comparison
"""

import pytest
from httpx import AsyncClient
from app.models.interview_session import InterviewSession


# ==================== GET FEEDBACK TESTS ====================

@pytest.mark.asyncio
async def test_get_feedback(
    test_client: AsyncClient,
    auth_headers: dict,
    test_interview_session: InterviewSession
):
    """Test getting feedback for a session"""
    response = await test_client.get(
        f"/api/v1/feedback/{test_interview_session.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["overall_score"] == 85.0
    assert data["relevance_score"] == 88.0
    assert "strengths" in data
    assert "weaknesses" in data
    assert "actionable_tips" in data


@pytest.mark.asyncio
async def test_get_feedback_not_found(
    test_client: AsyncClient,
    auth_headers: dict
):
    """Test getting feedback for non-existent session"""
    import uuid
    fake_id = str(uuid.uuid4())
    
    response = await test_client.get(
        f"/api/v1/feedback/{fake_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404


# ==================== FEEDBACK SUMMARY TESTS ====================

@pytest.mark.asyncio
async def test_get_feedback_summary(
    test_client: AsyncClient,
    auth_headers: dict,
    test_interview_session: InterviewSession
):
    """Test getting feedback summary"""
    response = await test_client.get(
        "/api/v1/feedback/summary",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_interviews"] >= 1
    assert "average_scores" in data
    assert "improvement_rate" in data


# ==================== FEEDBACK HISTORY TESTS ====================

@pytest.mark.asyncio
async def test_list_feedback_history(
    test_client: AsyncClient,
    auth_headers: dict,
    test_interview_session: InterviewSession
):
    """Test listing feedback history"""
    response = await test_client.get(
        "/api/v1/feedback/history",
        headers=auth_headers,
        params={"limit": 20, "offset": 0}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


# ==================== FEEDBACK COMPARISON TESTS ====================

@pytest.mark.asyncio
async def test_compare_feedback(
    test_client: AsyncClient,
    auth_headers: dict,
    test_interview_session: InterviewSession,
    test_db,
    test_user,
    test_category
):
    """Test comparing feedback across sessions"""
    # Create second session
    from app.models.interview_session import InterviewSession, InterviewStatus
    from app.models.interview_feedback import InterviewFeedback
    from datetime import datetime, timedelta
    from uuid import uuid4
    
    session2 = InterviewSession(
        id=uuid4(),
        user_id=test_user.id,
        category_id=test_category.id,
        status=InterviewStatus.COMPLETED.value,
        difficulty="intermediate",
        conversation_history=[],
        started_at=datetime.utcnow() - timedelta(days=1),
        completed_at=datetime.utcnow() - timedelta(days=1),
        duration_seconds=1800
    )
    
    test_db.add(session2)
    await test_db.flush()
    
    feedback2 = InterviewFeedback(
        id=uuid4(),
        session_id=session2.id,
        overall_score=90.0,
        relevance_score=92.0,
        confidence_score=88.0,
        positivity_score=95.0,
        strengths=["Excellent communication"],
        weaknesses=["None"],
        summary="Outstanding performance",
        actionable_tips=["Keep it up"],
        filler_words_count=2
    )
    
    test_db.add(feedback2)
    await test_db.commit()
    
    # Compare
    response = await test_client.post(
        "/api/v1/feedback/compare",
        headers=auth_headers,
        json={
            "session_ids": [
                str(test_interview_session.id),
                str(session2.id)
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["sessions_compared"] == 2
    assert "score_comparison" in data
    assert "average_improvement" in data
