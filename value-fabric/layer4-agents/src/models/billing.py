"""SQLAlchemy models for Stripe billing integration.

Billing layer includes: subscription management, customer sync, webhook idempotency,
and usage-based metering with tenant isolation.

SECURITY: All tables have Row-Level Security (RLS) policies for multi-tenant isolation.
IDEMPOTENCY: Duplicate event detection via unique constraints on (tenant_id, event_id).
"""

from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
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


class UsageEventStatus(str, PyEnum):
    """Status of a usage event."""

    PENDING = "pending"  # Received but not yet aggregated
    PROCESSED = "processed"  # Included in billing calculation
    FAILED = "failed"  # Validation or processing error
    IGNORED = "ignored"  # Duplicate or out-of-period event


class BillingCustomer(Base):
    """Customer record synced with Stripe.

    Maps app user_id to Stripe customer for subscription management.
    """

    __tablename__ = "billing_customers"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # App user_id
    tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
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
        Index("ix_billing_customers_tenant", "tenant_id"),
        # Composite unique constraint for tenant-scoped customer lookup
        # Different tenants can have customers with the same logical ID
        UniqueConstraint("tenant_id", "id", name="uq_billing_customers_tenant_id"),
    )

    def __repr__(self) -> str:
        return f"<BillingCustomer(id={self.id}, stripe_id={self.stripe_customer_id})>"


class BillingSubscription(Base):
    """Subscription record synced with Stripe.

    Tracks plan, status, and billing period for entitlement checks.
    """

    __tablename__ = "billing_subscriptions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
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
        Index("ix_billing_subscriptions_tenant", "tenant_id"),
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
    tenant_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("ix_billing_webhook_events_type", "type"),
        Index("ix_billing_webhook_events_processed", "processed_at"),
        Index("ix_billing_webhook_events_tenant", "tenant_id"),
    )

    def __repr__(self) -> str:
        return f"<BillingWebhookEvent(id={self.id}, type={self.type})>"


class BillingUsageEvent(Base):
    """Usage event for metering and billing.

    High-throughput event ingestion for usage-based billing.
    Events are aggregated into billable quantities at period end.

    SECURITY: Events are tenant-scoped via RLS policies.
    IDEMPOTENCY: Duplicate event_id within tenant is rejected.
    """

    __tablename__ = "billing_usage_events"

    # Primary key - UUID generated by application or database
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Tenant isolation
    tenant_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Customer attribution
    customer_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Event identification (idempotency key)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Event type and metric
    event_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Quantities
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamping
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    # Processing status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=UsageEventStatus.PENDING, index=True
    )

    # Metadata for debugging and enrichment
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Idempotency: event_id + tenant_id must be unique
        UniqueConstraint("tenant_id", "event_id", name="uq_billing_usage_events_tenant_event"),
        # Query optimization indexes
        Index("ix_billing_usage_events_customer_timestamp", "customer_id", "timestamp"),
        Index("ix_billing_usage_events_status_created", "status", "created_at"),
        Index("ix_billing_usage_events_event_name", "event_name"),
    )

    def __repr__(self) -> str:
        return f"<BillingUsageEvent(id={self.id}, customer={self.customer_id}, metric={self.metric_name}, qty={self.quantity})>"
