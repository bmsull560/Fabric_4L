"""SQLAlchemy models for Stripe billing integration.

Minimal billing layer: subscription status, customer sync, webhook idempotency.
Usage metering deferred until product semantics stabilize.
"""

from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class SubscriptionStatus(str, PyEnum):
    """Stripe subscription statuses we care about."""

    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    PAUSED = "paused"


class PlanId(str, PyEnum):
    """Internal plan identifiers."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingCustomer(Base):
    """Customer record synced with Stripe.

    Maps app user_id to Stripe customer for subscription management.
    """

    __tablename__ = "billing_customers"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # App user_id
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    subscriptions: Mapped[list["BillingSubscription"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_billing_customers_stripe_id", "stripe_customer_id"),
    )

    def __repr__(self) -> str:
        return f"<BillingCustomer(id={self.id}, stripe_id={self.stripe_customer_id})>"


class BillingSubscription(Base):
    """Subscription record synced with Stripe.

    Tracks plan, status, and billing period for entitlement checks.
    """

    __tablename__ = "billing_subscriptions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("billing_customers.id", ondelete="CASCADE"), nullable=False
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    plan_id: Mapped[str] = mapped_column(String(50), nullable=False, default=PlanId.FREE)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SubscriptionStatus.INCOMPLETE
    )
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # Relationships
    customer: Mapped["BillingCustomer"] = relationship(back_populates="subscriptions")

    __table_args__ = (
        Index("ix_billing_subscriptions_customer", "customer_id"),
        Index("ix_billing_subscriptions_status", "status"),
        Index("ix_billing_subscriptions_plan", "plan_id"),
    )

    def __repr__(self) -> str:
        return f"<BillingSubscription(id={self.id}, plan={self.plan_id}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if subscription is in an active state."""
        return self.status in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        )

    @property
    def is_canceled(self) -> bool:
        """Check if subscription is canceled or will cancel."""
        return self.status == SubscriptionStatus.CANCELED or self.cancel_at_period_end


class BillingWebhookEvent(Base):
    """Webhook event log for idempotency.

    Prevents duplicate processing of Stripe webhook events.
    """

    __tablename__ = "billing_webhook_events"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # Stripe event ID
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("ix_billing_webhook_events_type", "type"),
        Index("ix_billing_webhook_events_processed", "processed_at"),
    )

    def __repr__(self) -> str:
        return f"<BillingWebhookEvent(id={self.id}, type={self.type})>"
