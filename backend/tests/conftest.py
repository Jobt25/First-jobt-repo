import sys
from pathlib import Path
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, StaticPool
from httpx import AsyncClient
from uuid import uuid4

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.core.database import get_db, Base
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionPlan, SubscriptionStatus
from app.models.job_category import JobCategory
from app.models.interview_session import InterviewSession, InterviewStatus
from app.models.interview_feedback import InterviewFeedback
from app.core.security import get_password_hash
from app.core.security import get_password_hash
from datetime import datetime, timedelta


# Test database URL (use in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ==================== DATABASE FIXTURES ====================

@pytest.fixture(scope="session", autouse=True)
def setup_sqlite_compatibility():
    """
    Patch SQLite dialect to support PostgreSQL types (JSONB, UUID) during tests.
    """
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
    from sqlalchemy.dialects.postgresql import JSONB, UUID

    def visit_JSONB(self, type_, **kw):
        return "JSON"

    def visit_UUID(self, type_, **kw):
        return "VARCHAR(36)"

    setattr(SQLiteTypeCompiler, "visit_JSONB", visit_JSONB)
    setattr(SQLiteTypeCompiler, "visit_UUID", visit_UUID)


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh test database for each test.
    
    Uses in-memory SQLite for speed.
    """
    # Create async engine with StaticPool to share connection
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


# ==================== CLIENT FIXTURE ====================

@pytest.fixture
async def test_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test client with database dependency override.
    """
    from httpx import ASGITransport
    
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


# ==================== USER FIXTURES ====================

@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """
    Create a test user with trial subscription.
    """
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("TestPassword123!"),
        full_name="Test User",
        current_job_title="Software Developer",
        target_job_role="Senior Software Engineer",
        years_of_experience=3,
        is_active=True,
        role="user"
    )
    
    test_db.add(user)
    await test_db.flush()
    
    # Create trial subscription
    subscription = Subscription(
        id=uuid4(),
        user_id=user.id,
        plan=SubscriptionPlan.FREE.value,
        status=SubscriptionStatus.TRIAL.value,
        max_interviews_per_month=5,
        interviews_used_this_month=0,
        trial_ends_at=datetime.utcnow() + timedelta(days=30)
    )
    
    test_db.add(subscription)
    await test_db.commit()
    await test_db.refresh(user)
    
    return user


@pytest.fixture
async def test_admin_user(test_db: AsyncSession) -> User:
    """
    Create a test admin user.
    """
    user = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPassword123!"),
        full_name="Admin User",
        is_active=True,
        role="admin"
    )
    
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    return user


# ==================== CATEGORY FIXTURE ====================

@pytest.fixture
async def test_category(test_db: AsyncSession) -> JobCategory:
    """
    Create a test job category.
    """
    category = JobCategory(
        id=uuid4(),
        name="Software Engineer",
        description="Software development and engineering roles",
        industry="Technology",
        is_active=True
    )
    
    test_db.add(category)
    await test_db.commit()
    await test_db.refresh(category)
    
    return category


# ==================== INTERVIEW SESSION FIXTURE ====================

@pytest.fixture
async def test_interview_session(
    test_db: AsyncSession,
    test_user: User,
    test_category: JobCategory
) -> InterviewSession:
    """
    Create a completed test interview session with feedback.
    """
    session = InterviewSession(
        id=uuid4(),
        user_id=test_user.id,
        category_id=test_category.id,
        status=InterviewStatus.COMPLETED.value,
        difficulty="intermediate",
        conversation_history=[
            {
                "role": "interviewer",
                "content": "Tell me about yourself",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "role": "user",
                "content": "I am a software developer with 3 years of experience",
                "timestamp": datetime.utcnow().isoformat()
            }
        ],
        started_at=datetime.utcnow() - timedelta(minutes=30),
        completed_at=datetime.utcnow(),
        duration_seconds=1800,
        total_tokens_used=500
    )
    
    test_db.add(session)
    await test_db.flush()
    
    # Create feedback
    feedback = InterviewFeedback(
        id=uuid4(),
        session_id=session.id,
        overall_score=85.0,
        relevance_score=88.0,
        confidence_score=82.0,
        positivity_score=90.0,
        strengths=["Clear communication", "Good examples"],
        weaknesses=["Could provide more detail"],
        summary="Strong performance overall",
        actionable_tips=["Practice STAR method"],
        filler_words_count=5,
        avg_response_length=150
    )
    
    test_db.add(feedback)
    await test_db.commit()
    await test_db.refresh(session)
    
    return session


# ==================== AUTH TOKEN FIXTURE ====================

@pytest.fixture
async def auth_token(test_client: AsyncClient, test_user: User) -> str:
    """
    Get authentication token for test user.
    """
    response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "TestPassword123!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def auth_headers(auth_token: str) -> dict:
    """
    Get authentication headers for requests.
    """
    return {"Authorization": f"Bearer {auth_token}"}


# ==================== MOCK OPENAI SERVICE ====================

@pytest.fixture
def mock_openai_service(monkeypatch):
    """
    Mock OpenAI service to avoid API calls during tests.
    """
    from app.services import openai_service
    
    async def mock_generate_first_question(*args, **kwargs):
        return {
            "question": "Tell me about yourself and your background.",
            "tokens_used": 50,
            "model": "test-model"
        }
    
    async def mock_generate_follow_up_question(*args, **kwargs):
        questions_asked = kwargs.get("questions_asked", 0)
        is_final = questions_asked >= 6  # 7 questions for intermediate
        
        return {
            "question": "What are your greatest strengths?" if not is_final else "Do you have any questions for me?",
            "is_final": is_final,
            "tokens_used": 50,
            "model": "test-model"
        }
    
    async def mock_generate_feedback(*args, **kwargs):
        return {
            "overall_score": 85.0,
            "relevance_score": 88.0,
            "confidence_score": 82.0,
            "positivity_score": 90.0,
            "strengths": ["Clear communication", "Good examples"],
            "weaknesses": ["Could provide more detail"],
            "summary": "Strong performance overall",
            "actionable_tips": ["Practice STAR method", "Provide more specific examples"],
            "filler_words_count": 5,
            "tokens_used": 200
        }
    
    monkeypatch.setattr(
        openai_service.OpenAIService,
        "generate_first_question",
        mock_generate_first_question
    )
    monkeypatch.setattr(
        openai_service.OpenAIService,
        "generate_follow_up_question",
        mock_generate_follow_up_question
    )
    monkeypatch.setattr(
        openai_service.OpenAIService,
        "generate_feedback",
        mock_generate_feedback
    )
    
    return openai_service.OpenAIService
