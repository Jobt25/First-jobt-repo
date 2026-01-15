"""
app/routers/api/v1/interviews_route.py

Interview session management endpoints.

All endpoints require authentication.

Endpoints:
- POST /interviews/start - Start new interview
- POST /interviews/{id}/message - Send user response
- POST /interviews/{id}/end - End interview
- GET /interviews/{id} - Get session details
- GET /interviews - List user's interview history
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID
import logging

from app.core.database import get_db, AsyncSessionLocal
from app.core.oauth2 import get_current_user
from app.models.user import User
from app.models.interview_session import InterviewSession
from app.services.interview_service import InterviewService
from app.schemas.interview_schema import (
    InterviewSessionStart,
    InterviewSessionResponse,
    InterviewMessageRequest,
    InterviewMessageResponse,
    InterviewEndRequest,
    InterviewHistoryItem
)
from app.schemas.common_schema import MessageResponse, PaginatedResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interviews", tags=["Interviews"])


# ==================== BACKGROUND TASKS ====================

async def generate_feedback_background(session_id: UUID):
    """
    Generate feedback in background task.
    
    This runs after the end interview response is sent to the user.
    Creates its own database session to avoid conflicts.
    """
    logger.info(f"Starting background feedback generation for session {session_id}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Get the session
            result = await db.execute(
                select(InterviewSession).where(InterviewSession.id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if not session:
                logger.error(f"Session {session_id} not found for feedback generation")
                return
            
            # Generate feedback
            service = InterviewService(db)
            await service._generate_feedback(session)
            
            logger.info(f"✓ Background feedback generated successfully for session {session_id}")
            
        except Exception as e:
            logger.error(
                f"Background feedback generation failed for session {session_id}: {e}",
                exc_info=True
            )
            # Don't re-raise - background task failure shouldn't affect user


# ==================== START INTERVIEW ====================

@router.post("/start", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_interview(
    session_data: InterviewSessionStart,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new interview session.

    **Authentication required.**

    Process:
    1. Checks subscription limits (5 interviews/month for free tier)
    2. Validates job category exists
    3. Creates interview session
    4. Generates first AI question
    5. Increments usage counter

    Request Body:
    ```json
    {
        "category_id": "uuid-here",
        "difficulty": "intermediate"
    }
    ```

    Difficulty Options:
    - **beginner**: 5 questions, basic concepts
    - **intermediate**: 7 questions, practical scenarios
    - **advanced**: 10 questions, complex problem-solving

    Returns:
    - Complete session details
    - First interview question from AI
    - Token usage tracking

    Raises:
    - 403: No active subscription
    - 404: Category not found
    - 429: Monthly interview limit exceeded

    Example Response:
    ```json
    {
        "id": "uuid",
        "user_id": "uuid",
        "category_id": "uuid",
        "status": "in_progress",
        "difficulty": "intermediate",
        "conversation_history": [
            {
                "role": "interviewer",
                "content": "Hello! Let's start with: Tell me about yourself...",
                "timestamp": "2025-12-13T10:00:00Z"
            }
        ],
        "started_at": "2025-12-13T10:00:00Z",
        "total_tokens_used": 45
    }
    ```

    Tips:
    - Choose difficulty based on your experience level
    - Make sure you're in a quiet environment
    - Have 15-30 minutes available
    - Be ready to respond thoughtfully
    """
    logger.info(
        f"User {current_user.email} starting interview "
        f"(category: {session_data.category_id}, difficulty: {session_data.difficulty})"
    )

    service = InterviewService(db)
    session = await service.start_session(current_user, session_data)

    return InterviewSessionResponse.model_validate(session)


# ==================== SEND MESSAGE ====================

@router.post("/{session_id}/message", response_model=InterviewMessageResponse)
async def send_message(
    session_id: UUID,
    message: InterviewMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send your response and get AI's next question.

    **Authentication required.**

    This is the core interview interaction endpoint.

    Path Parameters:
    - session_id: UUID of the active interview session

    Request Body:
    ```json
    {
        "content": "Your response to the previous question..."
    }
    ```

    Process:
    1. Validates session ownership
    2. Checks session is still active
    3. Adds your response to conversation
    4. AI analyzes your answer
    5. AI generates follow-up question
    6. Tracks token usage

    Returns:
    - AI's next question
    - Whether this is the final question
    - Token usage for this interaction
    - Current session status

    Raises:
    - 400: Session already completed
    - 403: Not your session
    - 404: Session not found
    - 408: Session expired (30 min timeout)

    Example Response:
    ```json
    {
        "message": "That's interesting. Can you tell me more about how you handled the technical challenges?",
        "is_final": false,
        "tokens_used": 38,
        "session_status": "in_progress"
    }
    ```

    Tips:
    - Take your time to think before responding
    - Use the STAR method for behavioral questions
    - Be specific with examples
    - It's okay to ask for clarification
    - Aim for 1-2 minute responses (150-250 words)
    """
    logger.info(f"User {current_user.email} sending message to session {session_id}")

    service = InterviewService(db)
    response = await service.process_message(
        session_id=session_id,
        user_id=current_user.id,
        message_content=message.content
    )

    return InterviewMessageResponse(
        message=response["message"],
        is_final=response["is_final"],
        tokens_used=response["tokens_used"],
        session_status=response["session_status"],
        progress=response["progress"],
        time_remaining_minutes=response.get("time_remaining_minutes"),
        time_warning=response.get("time_warning")
    )


# ==================== END INTERVIEW ====================

@router.post("/{session_id}/end", response_model=MessageResponse)
async def end_interview(
    session_id: UUID,
    background_tasks: BackgroundTasks,
    end_data: Optional[InterviewEndRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    End interview session and generate feedback.

    **Authentication required.**

    Call this endpoint when:
    - You've completed all questions
    - You need to end early
    - The AI indicated this was the final question

    Path Parameters:
    - session_id: UUID of the interview session

    Request Body (optional):
    ```json
    {
        "reason": "Completed all questions"
    }
    ```

    Process:
    1. Marks session as completed
    2. Calculates interview duration
    3. Triggers AI feedback generation
    4. Generates comprehensive performance analysis

    Returns:
    - Confirmation message
    - Session ID
    - Interview duration
    - Feedback generation status

    Raises:
    - 400: Session already ended
    - 403: Not your session
    - 404: Session not found

    Example Response:
    ```json
    {
        "message": "Interview completed successfully",
        "detail": "Session ID: uuid, Duration: 1245 seconds, Feedback generated"
    }
    ```

    After ending:
    - View feedback at: GET /api/v1/feedback/{session_id}
    - See your progress: GET /api/v1/analytics/progress
    - Start new interview: POST /api/v1/interviews/start

    Note: Feedback generation takes 10-30 seconds. Check the feedback
    endpoint shortly after ending the interview.
    """
    logger.info(f"User {current_user.email} ending interview session {session_id}")

    reason = end_data.reason if end_data else None

    service = InterviewService(db)
    # End session without generating feedback immediately
    result = await service.end_session(
        session_id=session_id,
        user_id=current_user.id,
        reason=reason,
        generate_feedback=False  # ✅ Don't block - generate in background
    )

    # Schedule feedback generation in background
    background_tasks.add_task(
        generate_feedback_background,
        session_id=session_id
    )

    # Calculate duration in minutes for the response
    duration_minutes = round(result['duration_seconds'] / 60)

    return MessageResponse(
        message="Interview ended successfully. Feedback is being generated in the background.",
        detail={
            "session_id": str(result['session_id']),
            "status": "completed",
            "feedback_generated": False,  # Client should poll status endpoint
            "duration_minutes": duration_minutes
        }
    )


# ==================== CHECK FEEDBACK STATUS ====================

@router.get("/{session_id}/feedback/status", status_code=status.HTTP_200_OK)
async def check_feedback_status(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if feedback has been generated for a session.
    
    Poll this endpoint after ending an interview to know when 
    the detailed feedback is ready.
    """
    # Verify ownership
    # We can use fetch session service method which handles ownership check
    service = InterviewService(db)
    session = await service.get_session(session_id, current_user.id)
    
    # Check for feedback
    # Eager load feedback to ensure we have the relationship
    # Note: Service.get_session should ideally load this or we query specifically
    
    # Simple check: Does session have feedback relation populated?
    # Since we need to be sure, let's query the feedback table directly or check relation
    
    is_ready = False
    if session.feedback:
        is_ready = True
    else:
        # If not eager loaded, try to load it specifically?
        # Ideally get_session loads it. Let's assume get_session logic.
        # If using the base get_session, it might lazy load.
        # But we made get_session use selectinload for feedback!
        pass
        
    return {
        "session_id": str(session.id),
        "status": session.status,
        "feedback_ready": is_ready
    }


# ==================== GET SESSION ====================

@router.get("/{session_id}", response_model=InterviewSessionResponse)
async def get_interview_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about an interview session.

    **Authentication required.**

    Use this to:
    - Review conversation history
    - Check session status
    - View token usage
    - See interview duration

    Path Parameters:
    - session_id: UUID of the interview session

    Returns:
    - Complete session details including:
      - Full conversation history
      - Session metadata (status, duration, tokens)
      - Timestamps (started, completed)
      - Job category and difficulty

    Raises:
    - 403: Not your session
    - 404: Session not found

    Example Use Cases:
    - Resume an in-progress interview
    - Review past interviews
    - Debug issues during interview
    - Check token usage
    """
    service = InterviewService(db)
    session = await service.get_session(session_id, current_user.id)

    return InterviewSessionResponse.model_validate(session)


# ==================== LIST INTERVIEWS ====================

@router.get("", response_model=PaginatedResponse)
async def list_interviews(
    status: Optional[str] = Query(None, description="Filter by status (in_progress, completed, abandoned)"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List your interview history with pagination.

    **Authentication required.**

    Query Parameters:
    - status: Filter by status (optional)
      - "in_progress": Active interviews
      - "completed": Finished interviews with feedback
      - "abandoned": Timed out interviews
    - limit: Results per page (default: 20, max: 100)
    - offset: Skip N results (for pagination)

    Returns:
    - Paginated list of interview sessions
    - Total count
    - Page information

    Example Response:
    ```json
    {
        "items": [
            {
                "id": "uuid",
                "job_category_name": "Software Engineer",
                "difficulty": "intermediate",
                "overall_score": 82.5,
                "started_at": "2025-12-10T14:00:00Z",
                "completed_at": "2025-12-10T14:35:00Z",
                "status": "completed",
                "duration_seconds": 2100
            }
        ],
        "total": 15,
        "page": 1,
        "size": 20,
        "pages": 1
    }
    ```

    Tips:
    - Use status filter to find incomplete interviews
    - Sort by started_at (most recent first)
    - Track your progress over time
    - See which categories you've practiced

    Common Patterns:
    ```
    # Get all completed interviews
    GET /api/v1/interviews?status=completed

    # Get active interview (resume)
    GET /api/v1/interviews?status=in_progress

    # Get next page
    GET /api/v1/interviews?offset=20&limit=20
    ```
    """
    service = InterviewService(db)
    result = await service.list_user_interviews(
        user_id=current_user.id,
        status=status,
        limit=limit,
        offset=offset
    )

    # Convert to history items (simplified response)
    items = []
    for session in result["items"]:
        # Get category name
        category_name = None
        if session.job_category:
            category_name = session.job_category.name

        # Get feedback score if available
        overall_score = None
        if session.feedback:
            overall_score = session.feedback.overall_score

        items.append(InterviewHistoryItem(
            id=session.id,
            job_category_name=category_name,
            difficulty=session.difficulty,
            overall_score=overall_score,
            started_at=session.started_at,
            completed_at=session.completed_at,
            status=session.status,
            duration_seconds=session.duration_seconds
        ))

    return PaginatedResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        size=result["size"],
        pages=result["pages"]
    )