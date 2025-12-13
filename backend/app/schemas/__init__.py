# ==================== app/schemas/__init__.py ====================
"""
Export all schemas for easy importing.

Usage:
    from app.schemas import UserRegister, InterviewSessionResponse
"""

from .user_schema import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
)

from .auth_schema import (
    UserLogin,
    Token,
    TokenData,
    PasswordResetRequest,
    PasswordResetConfirm,
    RefreshTokenRequest,
)

from .job_category_schema import (
    JobCategoryBase,
    JobCategoryCreate,
    JobCategoryUpdate,
    JobCategoryResponse,
    JobCategoryDetail,
)

from .question_template_schema import (
    QuestionTemplateBase,
    QuestionTemplateCreate,
    QuestionTemplateUpdate,
    QuestionTemplateResponse,
    DifficultyLevel,
)

from .interview_schema import (
    InterviewSessionStart,
    InterviewSessionResponse,
    InterviewMessageRequest,
    InterviewMessageResponse,
    InterviewEndRequest,
    InterviewHistoryItem,
    ConversationMessage,
    InterviewStatus,
)

from .feedback_schema import (
    InterviewFeedbackResponse,
    FeedbackSummary,
    ScoreBreakdown,
)

from .analytics_schema import (
    UserProgressTrend,
    UserStatistics,
    ProgressDataPoint,
)

from .admin_schema import (
    AdminDashboardStats,
    SystemMetricsResponse,
    UserManagementResponse,
    UpdateUserRoleRequest,
    UpdateUserStatusRequest,
)

from .common_schema import (
    MessageResponse,
    PaginatedResponse,
    HealthCheckResponse,
)

__all__ = [
    # User
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserProfile",
    # Auth
    "UserLogin", "Token", "TokenData", "PasswordResetRequest",
    "PasswordResetConfirm", "RefreshTokenRequest",
    # Job Category
    "JobCategoryBase", "JobCategoryCreate", "JobCategoryUpdate",
    "JobCategoryResponse", "JobCategoryDetail",
    # Question Template
    "QuestionTemplateBase", "QuestionTemplateCreate", "QuestionTemplateUpdate",
    "QuestionTemplateResponse", "DifficultyLevel",
    # Interview
    "InterviewSessionStart", "InterviewSessionResponse", "InterviewMessageRequest",
    "InterviewMessageResponse", "InterviewEndRequest", "InterviewHistoryItem",
    "ConversationMessage", "InterviewStatus",
    # Feedback
    "InterviewFeedbackResponse", "FeedbackSummary", "ScoreBreakdown",
    # Analytics
    "UserProgressTrend", "UserStatistics", "ProgressDataPoint",
    # Admin
    "AdminDashboardStats", "SystemMetricsResponse", "UserManagementResponse",
    "UpdateUserRoleRequest", "UpdateUserStatusRequest",
    # Common
    "MessageResponse", "PaginatedResponse", "HealthCheckResponse",
]

