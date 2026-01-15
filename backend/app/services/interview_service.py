"""
app/services/interview_service.py

Business logic for interview session management.

Handles:
- Starting new interview sessions
- Managing conversation flow
- Processing user responses
- Ending interviews and triggering feedback
- Session history and statistics
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func, and_, desc
from fastapi import HTTPException, status
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging

from ..models.interview_session import InterviewSession, InterviewStatus
from ..models.interview_feedback import InterviewFeedback
from ..models.user import User
from ..models.job_category import JobCategory
from ..services.openai_service import OpenAIService
from ..schemas.interview_schema import (
    InterviewSessionStart,
    InterviewMessageRequest,
    InterviewSessionResponse
)

logger = logging.getLogger(__name__)


class InterviewService:
    """Service class for interview operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.openai_service = OpenAIService()

    # ==================== START INTERVIEW ====================

    async def start_session(
            self,
            user: User,
            session_data: InterviewSessionStart
    ) -> InterviewSession:
        """
        Start a new interview session.

        Process:
        1. Check subscription limits
        2. Validate category exists
        3. Create session record
        4. Generate first question from AI
        5. Increment usage counter

        Args:
            user: Authenticated user
            session_data: Session configuration

        Returns:
            Created interview session

        Raises:
            HTTPException: If limit exceeded or category not found
        """
        logger.info(
            f"Starting interview for user {user.email} "
            f"(category: {session_data.category_id}, difficulty: {session_data.difficulty})"
        )

        # 1. Check subscription limits
        if not user.subscription:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active subscription found. Please subscribe to start interviews."
            )

        if not user.subscription.can_start_interview:
            remaining = user.subscription.interviews_remaining
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Monthly interview limit reached. Interviews remaining: {remaining or 0}. Upgrade your plan for more interviews."
            )

        # 2. Validate category exists
        category = await self._get_category(session_data.category_id)
        if not category or not category.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job category not found or inactive"
            )

        # 3. Create session
        session = InterviewSession(
            user_id=user.id,
            category_id=category.id,
            status=InterviewStatus.IN_PROGRESS.value,
            difficulty=session_data.difficulty.value,
            conversation_history=[],
            started_at=datetime.utcnow(),
            total_tokens_used=0,
            openai_model_used=self.openai_service.model
        )

        self.db.add(session)
        await self.db.flush()  # Get session ID

        # 4. Generate first question
        try:
            user_profile = {
                "full_name": user.full_name,
                "current_job_title": user.current_job_title,
                "target_job_role": user.target_job_role,
                "years_of_experience": user.years_of_experience
            }

            first_question = await self.openai_service.generate_first_question(
                job_category=category.name,
                difficulty=session_data.difficulty.value,
                user_profile=user_profile
            )

            # Add to conversation history
            session.conversation_history.append({
                "role": "interviewer",
                "content": first_question["question"],
                "timestamp": datetime.utcnow().isoformat()
            })

            session.total_tokens_used = first_question["tokens_used"]

        except Exception as e:
            logger.error(f"Error generating first question: {e}")
            # Fallback question
            session.conversation_history.append({
                "role": "interviewer",
                "content": f"Hello! Thank you for taking the time to interview for the {category.name} position. Let's start with: Tell me about yourself and your background.",
                "timestamp": datetime.utcnow().isoformat()
            })

        # 5. Increment usage counter
        user.subscription.increment_usage()

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            f"✓ Interview session started: {session.id} "
            f"(user: {user.email}, tokens: {session.total_tokens_used})"
        )

        return session

    # ==================== PROCESS MESSAGE ====================

    async def process_message(
            self,
            session_id: UUID,
            user_id: UUID,
            message_content: str
    ) -> Dict[str, Any]:
        """
        Process user's response and generate AI's next question.

        Args:
            session_id: Interview session UUID
            user_id: User UUID (for ownership verification)
            message_content: User's response text

        Returns:
            Dict with AI's response and metadata

        Raises:
            HTTPException: If session not found, completed, or unauthorized
        """
        # Get session and verify ownership
        session = await self._get_session_with_ownership(session_id, user_id)

        # Check session is still active
        if session.status != InterviewStatus.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Interview session is {session.status}. Cannot send messages to completed interviews."
            )

        # Check session timeout (30 minutes)
        if await self._is_session_expired(session):
            await self._mark_session_abandoned(session)
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Interview session expired due to inactivity (30 minutes). Please start a new interview."
            )

        # Add user's response to history
        # Create a new list to ensure SQLAlchemy detects the change (avoid in-place mutation)
        new_history = list(session.conversation_history)
        new_history.append({
            "role": "user",
            "content": message_content,
            "timestamp": datetime.utcnow().isoformat()
        })
        session.conversation_history = new_history

        # Get category for context
        category = await self._get_category(session.category_id)

        # Count questions asked so far (count existing interviewer messages)
        questions_asked = len([
            msg for msg in session.conversation_history
            if msg["role"] == "interviewer"
        ])

        # Check if we have reached the limit
        max_questions = self._get_max_questions(session.difficulty)
        
        # If the user is responding to the final question (or we exceeded limit), end the session
        if questions_asked >= max_questions:
            logger.info(f"Max questions ({max_questions}) reached. Ending session {session.id}.")
            
            # End the session
            completion_result = await self.end_session(
                session_id=session.id,
                user_id=user_id,
                reason="Interview completed",
                generate_feedback=True
            )
            
            # Return a special completion response
            return {
                "message": "Thank you for your answers. The interview is now complete. We are generating your feedback.",
                "is_final": True,
                "tokens_used": 0,
                "session_status": InterviewStatus.COMPLETED.value,
                "progress": {
                    "questions_asked": questions_asked,
                    "total_questions": max_questions,
                    "percentage": 100
                },
                "time_remaining_minutes": 0,
                "completion_data": completion_result,
                "time_warning": None
            }

        # Generate AI's follow-up question
        try:
            follow_up = await self.openai_service.generate_follow_up_question(
                conversation_history=session.conversation_history,
                job_category=category.name,
                difficulty=session.difficulty,
                questions_asked=questions_asked
            )

            # Add AI's question to history
            # Create a new list to ensure SQLAlchemy detects the change
            new_history = list(session.conversation_history)
            new_history.append({
                "role": "interviewer",
                "content": follow_up["question"],
                "timestamp": datetime.utcnow().isoformat()
            })
            session.conversation_history = new_history

            # Update token usage
            session.total_tokens_used += follow_up["tokens_used"]

            # Check if this was the final question
            is_final = follow_up.get("is_final", False)

            await self.db.commit()

            logger.info(
                f"Processed message for session {session_id} "
                f"(tokens: {follow_up['tokens_used']}, is_final: {is_final})"
            )

            # Calculate progress and time remaining
            max_questions = self._get_max_questions(session.difficulty)
            time_remaining = self._get_time_remaining(session)
            
            # Build enhanced response
            response = {
                "message": follow_up["question"],
                "is_final": is_final,
                "tokens_used": follow_up["tokens_used"],
                "session_status": session.status,
                "progress": {
                    "questions_asked": questions_asked + 1,  # +1 because we just added AI's question
                    "total_questions": max_questions,
                    "percentage": int(((questions_asked + 1) / max_questions) * 100)
                },
                "time_remaining_minutes": time_remaining
            }
            
            # Add timeout warning if less than 5 minutes remaining
            if time_remaining is not None and time_remaining < 5:
                response["time_warning"] = f"Only {time_remaining} minutes remaining in this session"
            
            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate response. Please try again."
            )

    # ==================== END INTERVIEW ====================

    async def end_session(
            self,
            session_id: UUID,
            user_id: UUID,
            reason: Optional[str] = None,
            generate_feedback: bool = True
    ) -> Dict[str, Any]:
        """
        End interview session and optionally trigger feedback generation.

        Args:
            session_id: Interview session UUID
            user_id: User UUID
            reason: Optional reason for ending
            generate_feedback: Whether to generate feedback immediately (default: True)

        Returns:
            Dict with completion message and feedback status
        """
        # Get session and verify ownership
        session = await self._get_session_with_ownership(session_id, user_id)

        if session.status != InterviewStatus.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Interview already {session.status}"
            )

        # Mark as completed
        session.status = InterviewStatus.COMPLETED.value
        session.completed_at = datetime.utcnow()

        # Calculate duration
        # Ensure we have timezone-aware datetime for calculation if started_at is aware
        if session.started_at:
            now = datetime.utcnow()
            # If started_at has tzinfo, make now aware (assuming UTC)
            if session.started_at.tzinfo:
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            
            duration = (now - session.started_at).total_seconds()
            session.duration_seconds = int(duration)

        # ✅ FIX #1: Commit and refresh to prevent detached session access
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            f"Interview session ended: {session_id} "
            f"(duration: {session.duration_seconds}s, reason: {reason or 'completed'})"
        )

        # Generate feedback if requested (can be skipped for background processing)
        feedback_generated = False
        if generate_feedback:
            try:
                await self._generate_feedback(session)
                feedback_generated = True
            except Exception as e:
                # ✅ FIX #2: Don't re-raise - let interview end successfully even if feedback fails
                logger.error(f"Error generating feedback: {e}", exc_info=True)
                feedback_generated = False

        return {
            "message": "Interview completed successfully",
            "session_id": str(session_id),
            "duration_seconds": session.duration_seconds,
            "feedback_generated": feedback_generated
        }

    # ==================== GET SESSION ====================

    async def get_session(
            self,
            session_id: UUID,
            user_id: UUID
    ) -> InterviewSession:
        """
        Get interview session details.

        Args:
            session_id: Interview session UUID
            user_id: User UUID (for ownership verification)

        Returns:
            Interview session
        """
        return await self._get_session_with_ownership(session_id, user_id)

    # ==================== LIST SESSIONS ====================

    async def list_user_interviews(
            self,
            user_id: UUID,
            status: Optional[str] = None,
            limit: int = 20,
            offset: int = 0
    ) -> Dict[str, Any]:
        """
        List user's interview history.

        Args:
            user_id: User UUID
            status: Filter by status (optional)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            Dict with interviews and pagination info
        """
        # Build query
        query = select(InterviewSession).options(
            selectinload(InterviewSession.job_category),
            selectinload(InterviewSession.feedback)
        ).where(
            InterviewSession.user_id == user_id
        )

        # Apply status filter
        if status:
            query = query.where(InterviewSession.status == status)

        # Get total count
        count_query = select(func.count(InterviewSession.id)).where(
            InterviewSession.user_id == user_id
        )
        if status:
            count_query = count_query.where(InterviewSession.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and sorting
        query = query.order_by(desc(InterviewSession.started_at))
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        interviews = result.scalars().all()

        return {
            "items": interviews,
            "total": total,
            "page": (offset // limit) + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit
        }

    # ==================== FEEDBACK GENERATION ====================

    async def _generate_feedback(self, session: InterviewSession) -> InterviewFeedback:
        """
        Generate AI-powered feedback for completed interview.

        Args:
            session: Completed interview session

        Returns:
            Generated feedback record
        """
        logger.info(f"Generating feedback for session {session.id}")

        # Get category for context
        category = await self._get_category(session.category_id)

        try:
            # Calculate real metrics from conversation
            user_responses = [
                msg["content"] for msg in session.conversation_history
                if msg.get("role") == "user"
            ]
            
            # Count filler words across all responses
            from ..services.openai_service import count_filler_words
            total_filler_words = sum(count_filler_words(response) for response in user_responses)
            
            # Calculate average response length (in words)
            avg_response_length = None
            if user_responses:
                total_words = sum(len(response.split()) for response in user_responses)
                avg_response_length = total_words // len(user_responses)

            # Generate feedback using OpenAI
            feedback_data = await self.openai_service.generate_feedback(
                conversation_history=session.conversation_history,
                job_category=category.name,
                difficulty=session.difficulty
            )

            # Create feedback record with calculated metrics
            feedback = InterviewFeedback(
                session_id=session.id,
                overall_score=feedback_data.get("overall_score", 0.0),
                relevance_score=feedback_data.get("relevance_score", 0.0),
                confidence_score=feedback_data.get("confidence_score", 0.0),
                positivity_score=feedback_data.get("positivity_score", 0.0),
                strengths=feedback_data.get("strengths", []),
                weaknesses=feedback_data.get("weaknesses", []),
                summary=feedback_data.get("summary", ""),
                actionable_tips=feedback_data.get("actionable_tips", []),
                filler_words_count=total_filler_words,  # Use calculated count
                avg_response_length=avg_response_length
            )


            self.db.add(feedback)

            # Update session token usage
            session.total_tokens_used += feedback_data.get("tokens_used", 0)

            await self.db.commit()
            await self.db.refresh(feedback)

            logger.info(f"✓ Feedback generated for session {session.id}")

            return feedback

        except Exception as e:
            logger.error(f"Error generating feedback: {e}", exc_info=True)
            raise

    # ==================== PRIVATE HELPER METHODS ====================

    async def _get_category(self, category_id: UUID) -> JobCategory:
        """Get category by ID"""
        result = await self.db.execute(
            select(JobCategory).where(JobCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def _get_session_with_ownership(
            self,
            session_id: UUID,
            user_id: UUID
    ) -> InterviewSession:
        """
        Get session and verify user owns it.

        Raises:
            HTTPException: If not found or unauthorized
        """
        result = await self.db.execute(
            select(InterviewSession)
            .options(
                selectinload(InterviewSession.job_category),
                selectinload(InterviewSession.feedback)
            )
            .where(
                InterviewSession.id == session_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview session not found"
            )

        if str(session.user_id) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this interview session"
            )

        return session

    async def _is_session_expired(self, session: InterviewSession) -> bool:
        """Check if session has expired (30 minutes timeout)"""
        if not session.conversation_history:
            return False

        last_message = session.conversation_history[-1]
        last_timestamp = datetime.fromisoformat(last_message["timestamp"])
        timeout = timedelta(minutes=30)

        return datetime.utcnow() - last_timestamp > timeout

    async def _mark_session_abandoned(self, session: InterviewSession) -> None:
        """Mark session as abandoned due to timeout"""
        session.status = InterviewStatus.ABANDONED.value
        session.completed_at = datetime.utcnow()
        await self.db.commit()
        logger.info(f"Session {session.id} marked as abandoned (timeout)")
    
    def _get_time_remaining(self, session: InterviewSession) -> int | None:
        """
        Calculate time remaining in session (in minutes).
        
        Returns:
            Minutes remaining, or None if cannot calculate
        """
        if not session.conversation_history:
            return 30  # Full session time
        
        try:
            # Calculate from start time, not last message
            if not session.started_at:
                return 30
                
            # Ensure we have a timezone-aware or naive comparison consistent with started_at
            now = datetime.utcnow()
            
            # If started_at has tzinfo, make now aware (assuming UTC)
            if session.started_at.tzinfo:
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
                
            elapsed = now - session.started_at
            timeout = timedelta(minutes=30)
            remaining = timeout - elapsed
            
            # Return minutes, minimum 0
            return max(0, int(remaining.total_seconds() / 60))
        except Exception as e:
            logger.warning(f"Error calculating time remaining: {e}")
            return None
    
    def _get_max_questions(self, difficulty: str) -> int:
        """
        Get maximum number of questions based on difficulty.
        
        Args:
            difficulty: Interview difficulty level
            
        Returns:
            Maximum questions for this difficulty
        """
        question_limits = {
            "beginner": 5,
            "intermediate": 7,
            "advanced": 10
        }
        return question_limits.get(difficulty, 7)