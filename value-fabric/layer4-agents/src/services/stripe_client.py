"""Stripe SDK client configuration and initialization."""

import logging
import os
from typing import Any

import stripe

logger = logging.getLogger(__name__)

# Initialize Stripe with API key from environment
_stripe_api_key = os.environ.get("STRIPE_SECRET_KEY", "")
if _stripe_api_key:
    stripe.api_key = _stripe_api_key
    logger.info("Stripe SDK initialized")
else:
    logger.warning("STRIPE_SECRET_KEY not configured - billing features disabled")

# Price IDs from environment (set in Stripe Dashboard)
STRIPE_PRICE_PRO = os.environ.get("STRIPE_PRICE_PRO", "")
STRIPE_PRICE_ENTERPRISE = os.environ.get("STRIPE_PRICE_ENTERPRISE", "")

# Valid plan IDs
VALID_PLANS = {"pro", "enterprise"}


class StripeNotConfiguredError(Exception):
    """Raised when Stripe is not properly configured."""
    pass


def get_stripe() -> Any:
    """Get configured Stripe module.

    Raises:
        StripeNotConfiguredError: If STRIPE_SECRET_KEY is not set.
    """
    if not stripe.api_key:
        raise StripeNotConfiguredError(
            "Stripe is not configured. Set STRIPE_SECRET_KEY environment variable."
        )
    return stripe


def get_price_id(plan_id: str) -> str | None:
    """Get Stripe price ID for a plan.

    Args:
        plan_id: Plan identifier ('pro' or 'enterprise')

    Returns:
        Stripe price ID or None if plan not found or not configured
    """
    if plan_id not in VALID_PLANS:
        logger.warning(f"Invalid plan_id: {plan_id}. Valid plans: {VALID_PLANS}")
        return None

    price_map = {
        "pro": STRIPE_PRICE_PRO,
        "enterprise": STRIPE_PRICE_ENTERPRISE,
    }
    price_id = price_map.get(plan_id)

    if not price_id:
        logger.warning(f"Price ID not configured for plan: {plan_id}")

    return price_id
