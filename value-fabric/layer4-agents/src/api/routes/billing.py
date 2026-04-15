"""Billing API routes for Stripe integration.

Provides endpoints for subscription management, customer portal,
and entitlement checks. Minimal scope: checkout, portal, webhooks.
"""

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

from ...database import get_db
from ...services.billing_service import BillingService
from ...services.stripe_client import StripeError

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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Sync customer with Stripe (create or update).

    Args:
        customer_id: Internal customer/user ID
        request: Customer details

    Returns:
        Customer record with Stripe ID if available
    """
    service = BillingService(db)
    customer = await service.get_or_create_customer(
        customer_id=customer_id,
        email=request.email,
        name=request.name,
    )

    await db.commit()

    return {
        "id": customer.id,
        "stripe_customer_id": customer.stripe_customer_id,
        "email": customer.email,
        "name": customer.name,
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
