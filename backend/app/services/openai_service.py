"""
app/services/openai_service.py

AI integration service supporting both OpenAI and Grok (console.grok.com).

FIXED: Removes timestamp field from messages before sending to API.

Grok offers generous free tier with multiple models:
- Free: 30 RPM, 6-30K TPM depending on model
- Developer: Higher limits for scaling

Compatible with OpenAI v1.x API (both use same interface).

Handles:
- Interview question generation
- Response analysis
- Conversation continuation
- Feedback generation
- Token usage tracking
- Rate limit handling
"""

from openai import AsyncOpenAI, OpenAIError, RateLimitError, APIError
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from ..config import settings
from ..prompts.interviewer_prompts import (
    get_interviewer_system_prompt,
    get_question_generation_prompt,
    get_feedback_generation_prompt
)

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Service for AI API interactions.

    Supports:
    - OpenAI (api.openai.com)
    - Grok (api.x.ai) - Recommended for MVP
    """

    def __init__(self):
        # Initialize async client
        # Works with both OpenAI and Grok (same API format)
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,  # Use for both OpenAI and Grok
            base_url=settings.OPENAI_BASE_URL  # Grok: https://api.x.ai/v1
        )
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = 0.7  # Balance creativity and consistency

        logger.info(
            f"AI Service initialized: model={self.model}, "
            f"base_url={settings.OPENAI_BASE_URL}"
        )

    async def generate_first_question(
        self,
        job_category: str,
        difficulty: str,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate the first interview question based on job category and user profile.

        Args:
            job_category: Job category name (e.g., "Software Engineer")
            difficulty: Interview difficulty level
            user_profile: User's profile information

        Returns:
            Dict with question text and tokens used
        """
        try:
            # Build system prompt
            system_prompt = get_interviewer_system_prompt(
                job_category=job_category,
                difficulty=difficulty
            )

            # Build user context
            user_context = self._build_user_context(user_profile)

            # First question prompt
            user_prompt = get_question_generation_prompt(
                is_first=True,
                user_context=user_context
            )

            # Call AI
            response = await self._call_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300
            )

            logger.info(
                f"Generated first question for {job_category} "
                f"(tokens: {response['tokens_used']}, model: {response['model']})"
            )

            return {
                "question": response["content"],
                "tokens_used": response["tokens_used"],
                "model": response["model"]
            }

        except Exception as e:
            logger.error(f"Error generating first question: {e}", exc_info=True)
            raise

    async def generate_follow_up_question(
        self,
        conversation_history: List[Dict[str, str]],
        job_category: str,
        difficulty: str,
        questions_asked: int
    ) -> Dict[str, Any]:
        """
        Generate a follow-up question based on conversation history.

        Args:
            conversation_history: List of previous messages
            job_category: Job category name
            difficulty: Interview difficulty level
            questions_asked: Number of questions already asked

        Returns:
            Dict with question text, is_final flag, and tokens used
        """
        try:
            # Build system prompt
            system_prompt = get_interviewer_system_prompt(
                job_category=job_category,
                difficulty=difficulty
            )

            # Determine if this should be final question
            max_questions = self._get_max_questions(difficulty)
            is_final = questions_asked >= max_questions - 1

            # Build follow-up prompt
            user_prompt = get_question_generation_prompt(
                is_first=False,
                is_final=is_final,
                questions_asked=questions_asked
            )

            # Call AI with conversation history
            response = await self._call_ai(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                messages=conversation_history,
                max_tokens=300
            )

            logger.info(
                f"Generated follow-up question #{questions_asked + 1} "
                f"(is_final: {is_final}, tokens: {response['tokens_used']})"
            )

            return {
                "question": response["content"],
                "is_final": is_final,
                "tokens_used": response["tokens_used"],
                "model": response["model"]
            }

        except Exception as e:
            logger.error(f"Error generating follow-up question: {e}", exc_info=True)
            raise

    async def generate_feedback(
        self,
        conversation_history: List[Dict[str, str]],
        job_category: str,
        difficulty: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive feedback for completed interview.

        Args:
            conversation_history: Complete conversation
            job_category: Job category name
            difficulty: Interview difficulty level

        Returns:
            Dict with scores, strengths, weaknesses, and tips
        """
        try:
            # Build feedback generation prompt
            feedback_prompt = get_feedback_generation_prompt(
                conversation_history=conversation_history,
                job_category=job_category,
                difficulty=difficulty
            )

            # Call AI
            response = await self._call_ai(
                system_prompt="You are an expert interview coach providing detailed, actionable feedback.",
                user_prompt=feedback_prompt,
                max_tokens=1000,
                temperature=0.5  # More consistent for feedback
            )

            # Parse feedback (expecting JSON format from AI)
            feedback = self._parse_feedback_response(response["content"])
            feedback["tokens_used"] = response["tokens_used"]

            logger.info(
                f"Generated feedback for {job_category} interview "
                f"(tokens: {response['tokens_used']})"
            )

            return feedback

        except Exception as e:
            logger.error(f"Error generating feedback: {e}", exc_info=True)
            raise

    # ==================== PRIVATE METHODS ====================

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _call_ai(
        self,
        system_prompt: str,
        user_prompt: str,
        messages: Optional[List[Dict[str, str]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Make API call with retry logic and rate limit handling.

        Works with both OpenAI and Grok APIs (same interface).

        CRITICAL FIX: Strips 'timestamp' field from messages before sending to API.

        Args:
            system_prompt: System instructions
            user_prompt: User/assistant prompt
            messages: Previous conversation history
            max_tokens: Max tokens to generate
            temperature: Sampling temperature

        Returns:
            Dict with response content and token usage
        """
        # Build messages array
        api_messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if provided
        # CRITICAL FIX: Strip timestamp field - API only accepts role and content
        if messages:
            cleaned_messages = [
                {
                    "role": "assistant" if msg["role"] == "interviewer" else msg["role"],
                    "content": msg["content"]
                }
                for msg in messages
                # Only include user and interviewer messages (skip system messages)
                if msg.get("role") in ["user", "interviewer", "assistant"]
            ]
            api_messages.extend(cleaned_messages)

        # Add current user prompt
        api_messages.append({"role": "user", "content": user_prompt})

        try:
            # Use async API (works for both OpenAI and Grok)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )

            # Extract response
            return {
                "content": response.choices[0].message.content.strip(),
                "tokens_used": response.usage.total_tokens,
                "model": response.model
            }

        except OpenAIError as e:
            # Let tenacity handle retries for RateLimitError and APIError
            # For other errors, log and re-raise to stop retrying
            logger.error(f"AI service error: {e}")
            raise 

        except Exception as e:
            logger.error(f"Unexpected error calling AI: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred. Please try again."
            )

    def _build_user_context(self, user_profile: Dict[str, Any]) -> str:
        """Build context string from user profile"""
        context_parts = []

        if user_profile.get("full_name"):
            context_parts.append(f"Candidate: {user_profile['full_name']}")

        if user_profile.get("current_job_title"):
            context_parts.append(f"Current Role: {user_profile['current_job_title']}")

        if user_profile.get("target_job_role"):
            context_parts.append(f"Target Role: {user_profile['target_job_role']}")

        if user_profile.get("years_of_experience"):
            years = user_profile['years_of_experience']
            context_parts.append(f"Experience: {years} years")

        return "\n".join(context_parts) if context_parts else "No additional context provided."

    def _get_max_questions(self, difficulty: str) -> int:
        """Get maximum number of questions based on difficulty"""
        question_limits = {
            "beginner": 5,
            "intermediate": 7,
            "advanced": 10
        }
        return question_limits.get(difficulty, 7)

    def _parse_feedback_response(self, content: str) -> Dict[str, Any]:
        """
        Parse feedback from AI response.

        Expects JSON format or structured text.
        """
        import json
        import re

        try:
            # Try to parse as JSON first
            if content.strip().startswith("{"):
                return json.loads(content)

            # Otherwise, extract structured data
            feedback = {
                "overall_score": 0.0,
                "relevance_score": 0.0,
                "confidence_score": 0.0,
                "positivity_score": 0.0,
                "strengths": [],
                "weaknesses": [],
                "summary": "",
                "actionable_tips": [],
                "filler_words_count": 0
            }

            # Extract scores (looking for patterns like "Score: 85/100")
            score_patterns = {
                "overall_score": r"overall.*?(\d+)",
                "relevance_score": r"relevance.*?(\d+)",
                "confidence_score": r"confidence.*?(\d+)",
                "positivity_score": r"positivity.*?(\d+)"
            }

            for key, pattern in score_patterns.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    feedback[key] = float(match.group(1))

            # Extract lists (strengths, weaknesses, tips)
            strengths_match = re.search(
                r"strengths?:?\s*\n((?:[-•*]\s*.+\n?)+)",
                content,
                re.IGNORECASE
            )
            if strengths_match:
                feedback["strengths"] = [
                    line.strip("- •*").strip()
                    for line in strengths_match.group(1).split("\n")
                    if line.strip()
                ]

            weaknesses_match = re.search(
                r"weaknesses?:?\s*\n((?:[-•*]\s*.+\n?)+)",
                content,
                re.IGNORECASE
            )
            if weaknesses_match:
                feedback["weaknesses"] = [
                    line.strip("- •*").strip()
                    for line in weaknesses_match.group(1).split("\n")
                    if line.strip()
                ]

            # Extract summary
            summary_match = re.search(
                r"summary:?\s*(.+?)(?:\n\n|\Z)",
                content,
                re.IGNORECASE | re.DOTALL
            )
            if summary_match:
                feedback["summary"] = summary_match.group(1).strip()

            return feedback

        except Exception as e:
            logger.error(f"Error parsing feedback: {e}")
            # Return default feedback if parsing fails
            return {
                "overall_score": 70.0,
                "relevance_score": 70.0,
                "confidence_score": 70.0,
                "positivity_score": 70.0,
                "strengths": ["Completed the interview"],
                "weaknesses": ["Feedback parsing error"],
                "summary": "Interview completed. Detailed feedback unavailable.",
                "actionable_tips": ["Continue practicing"],
                "filler_words_count": 0
            }


# Import for error handling in _call_ai
from fastapi import HTTPException


# ==================== UTILITY FUNCTIONS ====================

def estimate_tokens(text: str) -> int:
    """
    Rough estimation of tokens in text.

    Approximation: 1 token ~= 4 characters
    """
    return len(text) // 4


def count_filler_words(text: str) -> int:
    """
    Count filler words in response.

    Common filler words: um, uh, like, you know, basically, actually, etc.
    """
    filler_words = [
        "um", "uh", "like", "you know", "basically", "actually",
        "literally", "sort of", "kind of", "i mean", "well",
        "so", "right", "okay", "yeah"
    ]

    text_lower = text.lower()
    count = 0

    for filler in filler_words:
        # Count whole word occurrences
        import re
        pattern = r'\b' + re.escape(filler) + r'\b'
        count += len(re.findall(pattern, text_lower))

    return count


# ==================== MODEL RECOMMENDATIONS ====================

"""
Recommended Grok Models for Jobt AI MVP:

FREE TIER (Perfect for MVP):
1. **llama-3.3-70b-versatile** (RECOMMENDED)
   - 30 RPM, 1K RPD, 12K TPM
   - Best balance of quality and limits
   - Great for interview conversations
   
2. **meta-llama/llama-4-scout-17b-16e-instruct**
   - 30 RPM, 1K RPD, 30K TPM
   - Higher token limit for longer conversations
   
3. **qwen/qwen3-32b**
   - 60 RPM, 1K RPD, 6K TPM
   - Higher request rate

COST ANALYSIS (Estimated):
- Free tier: 0 cost, up to 1K interviews/day
- Developer tier: Higher limits for scaling

FUTURE SCALING:
- Start with Grok free tier for MVP
- Upgrade to Developer plan as user base grows
- Consider hybrid: Grok for interviews, separate model for feedback
- Monitor usage and optimize based on real data
"""