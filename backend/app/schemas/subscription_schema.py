"""
app/schemas/subscription.py

Pydantic schemas for subscription management
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class SubscriptionBase(BaseModel):
    """Base subscription schema"""
    plan: str
    status: str
    billing_cycle: str


class SubscriptionResponse(SubscriptionBase):
    """Subscription response with full details"""
    id: UUID
    user_id: UUID

    # Plan details
    amount_paid: int
    currency: str

    # Dates
    starts_at: datetime
    expires_at: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None

    # Renewal
    auto_renew: bool
    will_cancel_at_period_end: bool

    # Payment info
    last_payment_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    payment_method: Optional[str] = None

    # Usage
    max_interviews_per_month: Optional[int] = None
    interviews_used_this_month: int
    interviews_remaining: Optional[int] = None

    # Features
    features: Dict[str, Any] = {}

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionSummary(BaseModel):
    """Condensed subscription info for user profile"""
    plan: str
    status: str
    interviews_used: int
    interviews_limit: Optional[int] = None
    trial_ends_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_trial: bool
    can_start_interview: bool


class SubscriptionUpgradeRequest(BaseModel):
    """Request to upgrade subscription"""
    plan: str = Field(..., pattern="^(starter|pro|enterprise)$")
    billing_cycle: str = Field(..., pattern="^(monthly|annual)$")
    payment_method_id: Optional[str] = None  # Stripe payment method ID


class SubscriptionCancelRequest(BaseModel):
    """Request to cancel subscription"""
    reason: Optional[str] = Field(None, max_length=500)
    cancel_immediately: bool = False  # If False, cancel at period end


class PaymentMethodUpdate(BaseModel):
    """Update payment method"""
    payment_method_id: str
    make_default: bool = True


class PlanComparisonResponse(BaseModel):
    """Plan comparison for pricing page"""
    plan: str
    name: str
    price_monthly: float | str
    price_annual: float | str
    max_interviews: Optional[int] = None
    features: list[str]
    popular: bool = False
    contact_sales: bool = False


class UsageStatistics(BaseModel):
    """User's usage statistics"""
    current_period_start: datetime
    current_period_end: datetime
    interviews_used: int
    interviews_limit: Optional[int] = None
    percentage_used: Optional[float] = None
    days_until_reset: int


class BillingHistoryItem(BaseModel):
    """Single billing transaction"""
    date: datetime
    amount: float
    currency: str
    status: str  # "succeeded", "failed", "pending"
    invoice_url: Optional[str] = None
    payment_method: Optional[str] = None
    plan: str


class SubscriptionWebhookEvent(BaseModel):
    """Webhook event from payment provider (Stripe)"""
    event_type: str
    subscription_id: str
    customer_id: str
    data: Dict[str, Any]


class TrialExtensionRequest(BaseModel):
    """Request trial extension (admin only)"""
    user_id: UUID
    additional_days: int = Field(..., ge=1, le=90)
    reason: Optional[str] = None