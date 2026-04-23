"""Billing API routes for Stripe integration.

Provides endpoints for subscription management, customer portal,
entitlement checks, and usage-based billing. Includes high-throughput
usage event ingestion with idempotency and tenant isolation.
"""

from datetime import datetime
import logging
import os
import re
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# Customer ID validation pattern (alphanumeric, underscore, hyphen; 1-64 chars after prefix)
CUSTOMER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def validate_customer_id(customer_id: str) -> str:
    """Validate customer_id format to prevent injection attacks.
    
    Args:
        customer_id: The customer ID to validate
        
    Returns:
        The validated customer ID
        
    Raises:
        HTTPException: If customer_id contains invalid characters
    """
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customer_id is required"
        )
    if not CUSTOMER_ID_PATTERN.match(customer_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customer_id contains invalid characters"
        )
    return customer_id

from ...database import get_db, get_db_from_context
from ...services.billing_service import BillingService
from ...services.stripe_client import StripeError
from ...services.usage_service import UsageService, UsageValidationError

# Import shared identity for tenant context
try:
    from shared.identity.context import RequestContext
    from shared.identity.dependencies import get_request_context
    SHARED_IDENTITY_AVAILABLE = True
except ImportError:
    SHARED_IDENTITY_AVAILABLE = False
    RequestContext = None  # type: ignore
    get_request_context = None  # type: ignore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])

STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")


# ============================================================================
# Request/Response Models
# ============================================================================

class CheckoutRequest(BaseModel):
    """Request to create a checkout session."""

    plan_id: str = Field(..., description="Plan to subscribe to (pro, enterprise)")
    success_url: str = Field(..., description="Redirect URL after successful checkout")
    cancel_url: str = Field(..., description="Redirect URL if checkout canceled")


class PortalRequest(BaseModel):
    """Request to create a customer portal session."""

    return_url: str = Field(..., description="URL to return to after portal session")


class CustomerSyncRequest(BaseModel):
    """Request to sync customer with Stripe."""

    email: str = Field(..., description="Customer email address")
    name: str | None = Field(None, description="Customer name")


class SubscriptionResponse(BaseModel):
    """Subscription status response."""

    id: str | None
    plan_id: str
    status: str
    current_period_start: str | None
    current_period_end: str | None
    cancel_at_period_end: bool


# ============================================================================
# Subscription Endpoints
# ============================================================================

@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    customer_id: str = Query(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$"),
    db: AsyncSession = Depends(get_db_from_context if SHARED_IDENTITY_AVAILABLE else get_db),
) -> dict[str, Any]:
    """Get current subscription status for a customer.

    Args:
        customer_id: Internal customer/user ID

    Returns:
        Subscription details including plan and status
    """
    service = BillingService(db)
    subscription = await service.get_subscription(customer_id)

    if not subscription:
        # Return free tier default
        return {
            "id": None,
            "plan_id": "free",
            "status": "active",
            "current_period_start": None,
            "current_period_end": None,
            "cancel_at_period_end": False,
        }

    return {
        "id": subscription.id,
        "plan_id": subscription.plan_id,
        "status": subscription.status,
        "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        "cancel_at_period_end": subscription.cancel_at_period_end,
    }


@router.post("/checkout")
async def create_checkout(
    request: CheckoutRequest,
    customer_id: str = Query(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$"),
    db: AsyncSession = Depends(get_db_from_context if SHARED_IDENTITY_AVAILABLE else get_db),
) -> dict[str, str]:
    """Create a Stripe checkout session for subscription.

    Args:
        customer_id: Internal customer/user ID
        request: Checkout session parameters

    Returns:
        Session ID and checkout URL
    """
    service = BillingService(db)

    try:
        result = await service.create_checkout_session(
            customer_id=customer_id,
            plan_id=request.plan_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )
        return result
    except ValueError as e:
        logger.warning(f"Checkout creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/portal")
async def create_portal(
    request: PortalRequest,
    customer_id: str = Query(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$"),
    db: AsyncSession = Depends(get_db_from_context if SHARED_IDENTITY_AVAILABLE else get_db),
) -> dict[str, str]:
    """Create a Stripe customer portal session.

    Args:
        customer_id: Internal customer/user ID
        request: Portal session parameters

    Returns:
        Portal URL for customer to manage billing
    """
    service = BillingService(db)

    try:
        result = await service.create_portal_session(
            customer_id=customer_id,
            return_url=request.return_url,
        )
        return result
    except ValueError as e:
        logger.warning(f"Portal creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


# ============================================================================
# Entitlement Endpoints
# ============================================================================

@router.get("/entitlements")
async def get_entitlements(
    customer_id: str = Query(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$"),
    db: AsyncSession = Depends(get_db_from_context if SHARED_IDENTITY_AVAILABLE else get_db),
) -> dict[str, Any]:
    """Get all feature entitlements for a customer.

    Args:
        customer_id: Internal customer/user ID

    Returns:
        Plan details and feature availability map
    """
    service = BillingService(db)
    return await service.get_entitlements(customer_id)


@router.get("/check-feature")
async def check_feature(
    customer_id: str = Query(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$"),
    feature_id: str = Query(..., min_length=1, max_length=64),
    db: AsyncSession = Depends(get_db_from_context if SHARED_IDENTITY_AVAILABLE else get_db),
) -> dict[str, Any]:
    """Check if a customer has access to a specific feature.

    Args:
        customer_id: Internal customer/user ID
        feature_id: Feature identifier to check

    Returns:
        Feature access status
    """
    service = BillingService(db)
    has_access = await service.check_entitlement(customer_id, feature_id)

    return {
        "feature_id": feature_id,
        "has_access": has_access,
    }


# ============================================================================
# Customer Management
# ============================================================================

@router.post("/sync-customer")
async def sync_customer(
    request: CustomerSyncRequest,
    customer_id: str = Query(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$"),
    db: AsyncSession = Depends(get_db_from_context if SHARED_IDENTITY_AVAILABLE else get_db),
    context: "RequestContext" = Depends(get_request_context) if SHARED_IDENTITY_AVAILABLE else None,  # type: ignore
) -> dict[str, Any]:
    """Sync customer with Stripe (create or update).

    Args:
        customer_id: Internal customer/user ID
        request: Customer details

    Returns:
        Customer record with Stripe ID if available
    """
    service = BillingService(db)
    
    # Extract tenant_id from context if available
    tenant_id = context.tenant_id if (SHARED_IDENTITY_AVAILABLE and context) else None
    
    customer = await service.get_or_create_customer(
        customer_id=customer_id,
        email=request.email,
        name=request.name,
        tenant_id=tenant_id,
    )

    await db.commit()

    return {
        "id": customer.id,
        "stripe_customer_id": customer.stripe_customer_id,
        "email": customer.email,
        "name": customer.name,
        "tenant_id": customer.tenant_id,
    }


# ============================================================================
# Webhook Endpoint
# ============================================================================

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle Stripe webhook events.

    Processes subscription lifecycle events from Stripe with idempotency.
    Must configure webhook secret in STRIPE_WEBHOOK_SECRET env var.

    Headers:
        Stripe-Signature: Webhook signature for verification

    Returns:
        Processing status
    """
    if not STRIPE_WEBHOOK_SECRET:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing not configured",
        )

    # Read raw body for signature verification
    body = await request.body()

    service = BillingService(db)

    try:
        await service.handle_webhook(body, stripe_signature, STRIPE_WEBHOOK_SECRET)
        await db.commit()
        return {"received": True}
    except ValueError as e:
        await db.rollback()
        logger.warning(f"Webhook validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        ) from e
    except StripeError as e:
        await db.rollback()
        logger.error(f"Stripe API error during webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe processing failed",
        ) from e
    except Exception as e:
        await db.rollback()
        logger.exception(f"Unexpected webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        ) from e


# ============================================================================
# Usage Metering Endpoints
# ============================================================================

@router.post("/events")
async def ingest_usage_event(
    request: UsageEventRequest,
    db: AsyncSession = Depends(get_db_from_context if SHARED_IDENTITY_AVAILABLE else get_db),
    context: "RequestContext" = Depends(get_request_context) if SHARED_IDENTITY_AVAILABLE else None,  # type: ignore
) -> dict[str, Any]:
    """Ingest a single usage event for billing.

    Args:
        request: Usage event details

    Returns:
        Ingested event with ID and status

    Raises:
        400: Validation error
        409: Duplicate event (idempotency conflict)
    """
    tenant_id = context.tenant_id if (SHARED_IDENTITY_AVAILABLE and context) else None
    
    service = UsageService(db, tenant_id=tenant_id)
    
    try:
        event = await service.ingest_event(
            event_id=request.event_id,
            customer_id=request.customer_id,
            event_name=request.event_name,
            metric_name=request.metric_name,
            quantity=request.quantity,
            unit=request.unit,
            timestamp=request.timestamp,
            metadata=request.metadata,
        )
        
        await db.commit()
        
        return {
            "id": event.id,
            "event_id": event.event_id,
            "status": event.status,
            "tenant_id": event.tenant_id,
            "customer_id": event.customer_id,
            "metric_name": event.metric_name,
            "quantity": event.quantity,
            "timestamp": event.timestamp.isoformat(),
            "created_at": event.created_at.isoformat(),
        }
        
    except UsageValidationError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": e.message, "field": e.field},
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"Usage event ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest usage event",
        )


@router.post("/events/batch")
async def ingest_usage_batch(
    request: UsageBatchRequest,
    db: AsyncSession = Depends(get_db_from_context if SHARED_IDENTITY_AVAILABLE else get_db),
    context: "RequestContext" = Depends(get_request_context) if SHARED_IDENTITY_AVAILABLE else None,  # type: ignore
) -> dict[str, Any]:
    """Ingest multiple usage events in a batch.

    Args:
        request: Batch of usage events (max 1000)

    Returns:
        Summary with counts of created, duplicate, and error events

    Raises:
        400: Batch validation error
    """
    tenant_id = context.tenant_id if (SHARED_IDENTITY_AVAILABLE and context) else None
    
    service = UsageService(db, tenant_id=tenant_id)
    
    try:
        # Convert Pydantic models to dicts for the service
        events_data = [event.model_dump() for event in request.events]
        result = await service.ingest_batch(events_data)
        
        await db.commit()
        
        return {
            "created": result["created"],
            "duplicates": result["duplicates"],
            "errors": result["errors"],
            "error_details": result.get("error_details"),
        }
        
    except UsageValidationError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": e.message, "field": e.field},
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"Batch ingestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process batch",
        )


@router.get("/usage/{customer_id}/summary")
async def get_usage_summary(
    customer_id: str,
    metric_name: str,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: AsyncSession = Depends(get_db_from_context if SHARED_IDENTITY_AVAILABLE else get_db),
    context: "RequestContext" = Depends(get_request_context) if SHARED_IDENTITY_AVAILABLE else None,  # type: ignore
) -> dict[str, Any]:
    """Get aggregated usage summary for a customer and metric.

    Args:
        customer_id: Customer to query
        metric_name: Metric to aggregate
        start_date: Start of period (ISO format)
        end_date: End of period (ISO format)

    Returns:
        Usage summary with total quantity and event count
    """
    tenant_id = context.tenant_id if (SHARED_IDENTITY_AVAILABLE and context) else None
    
    service = UsageService(db, tenant_id=tenant_id)
    
    try:
        summary = await service.get_usage_summary(
            customer_id=customer_id,
            metric_name=metric_name,
            start_date=start_date,
            end_date=end_date,
        )
        return summary
        
    except UsageValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": e.message},
        )
    except Exception as e:
        logger.exception(f"Usage summary failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage summary",
        )


@router.get("/usage/{customer_id}/events")
async def list_usage_events(
    customer_id: str,
    metric_name: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_from_context if SHARED_IDENTITY_AVAILABLE else get_db),
    context: "RequestContext" = Depends(get_request_context) if SHARED_IDENTITY_AVAILABLE else None,  # type: ignore
) -> list[dict[str, Any]]:
    """List individual usage events for a customer.

    Args:
        customer_id: Customer to query
        metric_name: Optional metric filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum results (1-1000)
        offset: Pagination offset

    Returns:
        List of usage events
    """
    tenant_id = context.tenant_id if (SHARED_IDENTITY_AVAILABLE and context) else None
    
    service = UsageService(db, tenant_id=tenant_id)
    
    try:
        events = await service.list_customer_usage(
            customer_id=customer_id,
            metric_name=metric_name,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        
        return [
            {
                "id": e.id,
                "event_id": e.event_id,
                "event_name": e.event_name,
                "metric_name": e.metric_name,
                "quantity": e.quantity,
                "unit": e.unit,
                "timestamp": e.timestamp.isoformat(),
                "status": e.status,
                "metadata": e.metadata,
            }
            for e in events
        ]
        
    except UsageValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": e.message},
        )
    except Exception as e:
        logger.exception(f"Usage events listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage events",
        )
