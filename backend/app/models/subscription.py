"""
app/models/subscription.py

User subscription tracking for Jobt AI Career Coach.

Plans:
- Free: 5 interviews/month, basic feedback (trial: 30 days)
- Starter: 20 interviews/month, detailed feedback ($9.99/month)
- Pro: Unlimited interviews, advanced analytics ($24.99/month)
- Enterprise: Custom features, team management (contact sales)
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .base import BaseModel


class SubscriptionPlan(str, enum.Enum):
    """Subscription plan types"""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status"""
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"  # Payment failed


class BillingCycle(str, enum.Enum):
    """Billing cycle options"""
    MONTHLY = "monthly"
    ANNUAL = "annual"


class Subscription(BaseModel):
    """
    User subscription tracking.

    Manages:
    - Plan type and status
    - Interview usage limits
    - Billing and payments
    - Trial periods

    Relationships:
        - user: One-to-one with User
    """

    __tablename__ = "subscriptions"

    # Foreign Key (one-to-one with User)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Plan Details
    plan = Column(
        String(50),  # Using String for easier querying
        default=SubscriptionPlan.FREE.value,
        nullable=False,
        index=True
    )

    status = Column(
        String(50),
        default=SubscriptionStatus.TRIAL.value,
        nullable=False,
        index=True
    )

    # Billing Configuration
    billing_cycle = Column(
        String(50),
        default=BillingCycle.MONTHLY.value,
        nullable=False
    )

    amount_paid = Column(Integer, default=0)  # In cents ($9.99 = 999)In kobo (₦25,000 = 2,500,000 kobo)
    currency = Column(String(3), default="NGN")

    # Dates
    starts_at = Column(DateTime(timezone=True), default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)

    # Renewal
    auto_renew = Column(Boolean, default=True)
    will_cancel_at_period_end = Column(Boolean, default=False)

    # Payment Tracking
    last_payment_date = Column(DateTime(timezone=True), nullable=True)
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    payment_method = Column(String(50), nullable=True)  # "Bank Transfer", "Credit Card", "Direct Deposit/POS"
    payment_method_id = Column(String(255), nullable=True)  # Paystack payment method ID

    # Transaction References
    paystack_customer_id = Column(String(255), nullable=True, index=True)
    paystack_subscription_id = Column(String(255), nullable=True, index=True)
    last_payment_reference = Column(String(255), nullable=True)

    # Usage Limits & Tracking
    max_interviews_per_month = Column(Integer, nullable=True)  # NULL = unlimited
    interviews_used_this_month = Column(Integer, default=0, nullable=False)
    last_usage_reset_date = Column(DateTime(timezone=True), default=func.now())

    # Feature Flags (for different plans)
    features = Column(JSONB, default=dict)
    # Example: {
    #     "advanced_feedback": True,
    #     "video_practice": False,
    #     "priority_support": True,
    #     "custom_branding": False
    # }

    # Cancellation Tracking
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(String(500), nullable=True)

    # Relationship
    user = relationship("User", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(plan={self.plan}, status={self.status}, user_id={self.user_id})>"

    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial period"""
        return self.status == SubscriptionStatus.TRIAL.value

    @property
    def is_active(self) -> bool:
        """Check if subscription is active (trial or paid)"""
        return self.status in [
            SubscriptionStatus.TRIAL.value,
            SubscriptionStatus.ACTIVE.value
        ]

    @property
    def has_unlimited_interviews(self) -> bool:
        """Check if user has unlimited interviews"""
        return self.max_interviews_per_month is None

    @property
    def interviews_remaining(self) -> int | None:
        """Calculate remaining interviews for the month"""
        if self.has_unlimited_interviews:
            return None  # Unlimited
        return max(0, self.max_interviews_per_month - self.interviews_used_this_month)

    @property
    def can_start_interview(self) -> bool:
        """Check if user can start a new interview"""
        if not self.is_active:
            return False
        if self.has_unlimited_interviews:
            return True
        return self.interviews_remaining > 0

    def increment_usage(self) -> None:
        """Increment interview usage count"""
        self.interviews_used_this_month += 1

    def reset_monthly_usage(self) -> None:
        """Reset monthly usage counter (called by scheduled task)"""
        from datetime import datetime
        self.interviews_used_this_month = 0
        self.last_usage_reset_date = datetime.utcnow()

    def get_plan_limits(self) -> dict:
        """Get plan limits as dictionary"""
        plan_configs = {
            SubscriptionPlan.FREE.value: {
                "max_interviews": 5,
                "advanced_feedback": False,
                "progress_tracking": True,
                "video_practice": False,
                "priority_support": False,
                "price_monthly": 0,
                "price_annual": 0
            },
            SubscriptionPlan.STARTER.value: {
                "max_interviews": 20,
                "advanced_feedback": True,
                "progress_tracking": True,
                "video_practice": False,
                "priority_support": False,
                "price_monthly": 9.99,
                "price_annual": 95.88  # 20% discount
            },
            SubscriptionPlan.PRO.value: {
                "max_interviews": None,  # Unlimited
                "advanced_feedback": True,
                "progress_tracking": True,
                "video_practice": True,
                "priority_support": True,
                "price_monthly": 24.99,
                "price_annual": 239.88  # 20% discount
            },
            SubscriptionPlan.ENTERPRISE.value: {
                "max_interviews": None,  # Unlimited
                "advanced_feedback": True,
                "progress_tracking": True,
                "video_practice": True,
                "priority_support": True,
                "custom_features": True,
                "team_management": True,
                "price_monthly": "custom",
                "price_annual": "custom"
            }
        }
        return plan_configs.get(self.plan, plan_configs[SubscriptionPlan.FREE.value])


# ==================== PLAN CONFIGURATIONS ====================

PLAN_FEATURES = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "price_annual": 0,
        "max_interviews": 5,
        "features": [
            "5 practice interviews per month",
            "Basic AI feedback",
            "Progress tracking",
            "Interview history"
        ],
        "trial_days": 30
    },
    "starter": {
        "name": "Starter",
        "price_monthly": 9.99,
        "price_annual": 95.88,  # 20% discount
        "max_interviews": 20,
        "features": [
            "20 practice interviews per month",
            "Advanced AI feedback",
            "Detailed analytics",
            "Progress tracking",
            "Strength/weakness analysis",
            "Custom practice scenarios"
        ],
        "popular": True
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 24.99,
        "price_annual": 239.88,  # 20% discount
        "max_interviews": None,  # Unlimited
        "features": [
            "Unlimited practice interviews",
            "Advanced AI feedback",
            "Video practice (coming soon)",
            "Priority support",
            "Salary negotiation practice",
            "Meeting simulation",
            "LinkedIn integration",
            "Export interview transcripts"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": "custom",
        "price_annual": "custom",
        "max_interviews": None,  # Unlimited
        "features": [
            "Everything in Pro",
            "Team management dashboard",
            "HR analytics",
            "Custom AI training",
            "White-label option",
            "Dedicated account manager",
            "Custom integrations",
            "Priority feature requests"
        ],
        "contact_sales": True
    }
}


def get_plan_config(plan_name: str) -> dict:
    """Get plan configuration by name"""
    return PLAN_FEATURES.get(plan_name, PLAN_FEATURES["free"])