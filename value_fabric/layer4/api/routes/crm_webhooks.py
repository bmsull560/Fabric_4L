"""
CRM Webhook handlers for real-time updates from Salesforce and HubSpot.

Handles push notifications when accounts are created/updated in CRM,
triggering immediate sync to keep Account records fresh.
"""

import hashlib
import hmac
import json
import logging
import os
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    status,
)
from pydantic import BaseModel, Field, TypeAdapter
from value_fabric.shared.audit import AuditAction, AuditOutcome, emit_audit_event
from value_fabric.shared.models.typed_dict import TypedDictModel
from sqlalchemy.ext.asyncio import AsyncSession

# SECURITY: CRM webhook endpoints are server-to-server calls from
# Salesforce/HubSpot. Authentication is via HMAC signature verification,
# not JWT. get_db (no tenant context) is intentional here.
from ...database import get_db_from_context
from ...models.account import CRMProvider
from ...models.integration import Integration
from ...services.crm_sync_service import CRMSyncService
from ...services.integration_service import IntegrationService


class _handle_webhook_errorResult(TypedDictModel):
    audit_event_id: Any
    error_type: Any
    provider: Any
    status: str

class webhook_healthResult(TypedDictModel):
    status: str
    webhooks: list[Any]

class salesforce_webhookResult(TypedDictModel):
    event_type: Any
    provider: str
    record_id: Any
    status: str

class hubspot_webhookResult(TypedDictModel):
    companies_to_sync: Any
    events_processed: Any
    provider: str
    status: str

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/crm", tags=["CRM Webhooks"])

# Header constants for webhook signature verification
SALESFORCE_SIGNATURE_HEADER = "X-Salesforce-Signature"
HUBSPOT_SIGNATURE_HEADER = "X-HubSpot-Signature"
HUBSPOT_SIGNATURE_V3_HEADER = "X-HubSpot-Signature-v3"

# App state attribute names for webhook secrets
SALESFORCE_WEBHOOK_SECRET_ATTR = "salesforce_webhook_secret"
HUBSPOT_WEBHOOK_SECRET_ATTR = "hubspot_webhook_secret"

# Production safety: require explicit tenant_id in webhook URLs to prevent
# cross-tenant sync leakage. Set CRM_WEBHOOKS_REQUIRE_TENANT_ID=false only
# for single-tenant deployments.
_CRM_WEBHOOKS_REQUIRE_TENANT_ID = os.getenv(
    "CRM_WEBHOOKS_REQUIRE_TENANT_ID",
    "true" if os.getenv("ENVIRONMENT", "development").lower() == "production" else "false",
).lower() in ("true", "1", "yes")


# CONTRACT §2.5: Pydantic schemas for webhook payload validation
class SalesforceSObject(BaseModel):
    """Salesforce sObject in outbound message."""
    Id: str | None = None
    Name: str | None = None


class SalesforceNotification(BaseModel):
    """Salesforce outbound message notification wrapper."""
    sObject: SalesforceSObject = Field(default_factory=SalesforceSObject)  # noqa: N815


class SalesforceChangeEventHeader(BaseModel):
    """Salesforce ChangeEventHeader for platform events."""
    recordIds: list[str] = Field(default_factory=list)  # noqa: N815
    changeType: str = ""  # noqa: N815
    entityName: str = ""  # noqa: N815


class SalesforcePayloadData(BaseModel):
    """Salesforce platform event data wrapper."""
    payload: dict[str, Any] = Field(default_factory=dict)


class SalesforceWebhookPayload(BaseModel):
    """Unified schema for Salesforce webhook payloads.

    Supports both:
    - Platform events: {"data": {"payload": {"ChangeEventHeader": {...}}}}
    - Outbound messages: {"Notification": {"sObject": {"Id": "..."}}}
    """
    Notification: SalesforceNotification | None = None
    data: SalesforcePayloadData | None = None
    # Allow extra fields for flexibility
    model_config = {"extra": "allow"}


class HubSpotWebhookEvent(BaseModel):
    """Single HubSpot webhook subscription event.

    HubSpot sends arrays of these events for object changes.
    """
    eventId: int | None = None  # noqa: N815
    subscriptionId: int | None = None  # noqa: N815
    portalId: int | None = None  # noqa: N815
    occurredAt: int | None = None  # noqa: N815
    subscriptionType: str = ""  # noqa: N815
    objectId: int | None = None  # noqa: N815
    propertyName: str | None = None  # noqa: N815
    propertyValue: str | None = None  # noqa: N815
    # Allow extra fields for future compatibility
    model_config = {"extra": "allow"}


# ============================================================================
# Webhook Authentication Helpers
# ============================================================================


def _verify_webhook_token(integration: Integration, provided_token: str | None) -> bool:
    """Verify webhook token using constant-time comparison.

    SECURITY:
        - Uses hmac.compare_digest to prevent timing attacks.
        - Never logs the provided or stored token.
        - Returns False if no token is configured (fail-closed).
    """
    if not provided_token:
        return False

    # Extract webhook_token from decrypted credentials
    # Note: this is called after integration lookup but before sync.
    # The caller is responsible for having the integration object ready.
    _stored_token = None
    if integration and integration.credentials_encrypted:
        # We can't decrypt here (async context needed), so the caller
        # must pass the decrypted token. This signature is kept for
        # interface compatibility; the actual check is in _authenticate_webhook.
        pass
    return False


async def _authenticate_webhook(
    integration: Integration,
    provided_token: str | None,
    provided_signature: str | None,
    body: bytes,
    app_state_webhook_secret: str | None,
) -> None:
    """Authenticate a CRM webhook using token + optional HMAC signature.

    Raises:
        HTTPException: 401 if authentication fails.
    """
    from ...services.encryption_service import EncryptionService

    # Decrypt credentials to obtain the per-tenant webhook token
    try:
        decrypted = await EncryptionService.decrypt(
            integration.credentials_encrypted, integration.encryption_key_id
        )
        creds = json.loads(decrypted)
        stored_webhook_token = creds.get("webhook_token")
    except Exception:
        stored_webhook_token = None

    # Primary auth: per-tenant webhook token (constant-time comparison)
    token_valid = False
    if stored_webhook_token and provided_token:
        token_valid = hmac.compare_digest(stored_webhook_token, provided_token)

    if not token_valid:
        # Fallback: global HMAC secret (if no per-tenant token is configured)
        if app_state_webhook_secret and provided_signature:
            expected = hmac.new(app_state_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
            if hmac.compare_digest(expected, provided_signature):
                logger.warning(
                    "Webhook authenticated via global HMAC secret for tenant=%s. "
                    "Configure a per-tenant webhook_token for stronger security.",
                    integration.tenant_id,
                )
                return
        logger.warning(
            "Webhook authentication failed for tenant=%s provider=%s",
            integration.tenant_id,
            integration.provider,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook credentials",
        )

    # Secondary auth: HMAC signature verification (defense-in-depth)
    if app_state_webhook_secret and provided_signature:
        expected = hmac.new(app_state_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, provided_signature):
            logger.warning(
                "Webhook HMAC signature mismatch for tenant=%s provider=%s",
                integration.tenant_id,
                integration.provider,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )


# ============================================================================
# Salesforce Webhooks
# ============================================================================


@router.post("/salesforce", status_code=status.HTTP_202_ACCEPTED)
async def salesforce_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    tenant_id: str | None = Query(None, description="Tenant identifier for multi-tenant webhook routing"),
    webhook_token: str | None = Query(None, description="Per-tenant webhook token for authentication"),
    x_webhook_token: str | None = Header(None, alias="X-Webhook-Token"),
    x_salesforce_signature: str | None = Header(None, alias=SALESFORCE_SIGNATURE_HEADER),
    db: AsyncSession = Depends(get_db_from_context),
) -> dict[str, Any]:
    """Handle Salesforce outbound message or platform event webhook.

    Salesforce sends notifications when Accounts, Opportunities, or Contacts
    are created/updated. We trigger incremental sync for affected records.

    **Production Multi-Tenancy:**
    The `tenant_id` query parameter is required in production. Configure your
    Salesforce outbound message URL with `?tenant_id=<your-tenant-id>&webhook_token=<token>`.
    The handler verifies both tenant existence and webhook token authenticity
    before syncing to prevent cross-tenant data leakage.

    Headers:
        X-Webhook-Token: Per-tenant opaque token (preferred)
        X-Salesforce-Signature: HMAC signature (defense-in-depth)

    Request Body:
        Salesforce platform event or outbound message payload
    """
    # ------------------------------------------------------------------
    # Tenant isolation: fail closed in production if tenant_id is missing
    # ------------------------------------------------------------------
    if _CRM_WEBHOOKS_REQUIRE_TENANT_ID and not tenant_id:
        logger.warning(
            "Salesforce webhook rejected: tenant_id query parameter is required in production. "
            "Configure your Salesforce outbound message URL with ?tenant_id=<tenant-id>"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id query parameter is required",
        )

    # If tenant_id provided, verify the tenant has an active Salesforce integration
    effective_tenant_id = tenant_id or "default"
    integration = None
    if tenant_id:
        integration_service = IntegrationService(db)
        integration = await integration_service.get_integration(
            tenant_id, CRMProvider.SALESFORCE
        )
        if not integration:
            logger.warning(
                "Salesforce webhook rejected: no Salesforce integration for tenant=%s",
                tenant_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No Salesforce integration configured for tenant {tenant_id}",
            )
        if not integration.enabled:
            logger.warning(
                "Salesforce webhook rejected: Salesforce integration disabled for tenant=%s",
                tenant_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Salesforce integration is disabled for this tenant",
            )

    # Read body once and cache for both signature verification and JSON parsing
    body = await request.body()

    # Authenticate webhook using per-tenant token + optional HMAC
    provided_token = x_webhook_token or webhook_token
    app_state_secret = getattr(request.app.state, SALESFORCE_WEBHOOK_SECRET_ATTR, None)
    if integration:
        await _authenticate_webhook(
            integration,
            provided_token=provided_token,
            provided_signature=x_salesforce_signature,
            body=body,
            app_state_webhook_secret=app_state_secret,
        )
    elif app_state_secret and x_salesforce_signature:
        # Legacy path: no tenant lookup, only global HMAC (not recommended)
        expected = hmac.new(app_state_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, x_salesforce_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
            )

    # CONTRACT §2.5: Parse and validate webhook payload with Pydantic schema
    try:
        payload_str = body.decode()
        data = SalesforceWebhookPayload.model_validate_json(payload_str).model_dump()
    except Exception as e:
        logger.warning("Salesforce webhook received invalid payload", extra={"error": str(e), "body_preview": body[:200].decode(errors='replace')})
        data = {"raw_body": body.decode(errors='replace'), "parse_error": str(e)}

    # Extract record info from Salesforce payload
    # Platform events: {"data": {"payload": {"RecordId": "...", "ChangeEventHeader": {...}}}}
    # Outbound messages: {"Notification": {"sObject": {"Id": "...", ...}}}

    record_id = _extract_salesforce_record_id(data)
    event_type = _extract_salesforce_event_type(data)

    logger.info(
        "Salesforce webhook: %s for record %s tenant=%s",
        event_type,
        record_id,
        effective_tenant_id,
    )

    # Trigger sync for the affected record
    sync_service = CRMSyncService(db)

    try:
        if record_id:
            # Sync specific account
            await sync_service.sync_provider(
                CRMProvider.SALESFORCE,
                tenant_id=effective_tenant_id,
                incremental=True,
                account_ids=[record_id],
            )
            logger.info(
                "Triggered sync for Salesforce account %s tenant=%s",
                record_id,
                effective_tenant_id,
            )
        else:
            # No specific record - trigger general incremental sync
            await sync_service.sync_provider(
                CRMProvider.SALESFORCE,
                tenant_id=effective_tenant_id,
                incremental=True,
            )
            logger.info(
                "Triggered general Salesforce incremental sync tenant=%s",
                effective_tenant_id,
            )

        return salesforce_webhookResult.model_validate({
            "status": "accepted",
            "provider": "salesforce",
            "event_type": event_type,
            "record_id": record_id,
            "tenant_id": effective_tenant_id,
        })


    except Exception as e:
        return _handle_webhook_error(
            logger, e, "salesforce", record_id=record_id, event_type=event_type,
            request_id=getattr(request.state, "request_id", None),
        )


def _extract_salesforce_record_id(data: dict) -> str | None:
    """Extract record ID from Salesforce webhook payload."""
    # Platform Event format
    if "data" in data and "payload" in data["data"]:
        payload = data["data"]["payload"]
        # Change Data Capture format
        if "ChangeEventHeader" in payload:
            record_ids = payload["ChangeEventHeader"].get("recordIds", [])
            return record_ids[0] if record_ids else None
        # Custom platform event with RecordId
        return payload.get("RecordId") or payload.get("recordId")

    # Outbound Message format
    if "Notification" in data:
        notification = data["Notification"]
        if "sObject" in notification:
            return notification["sObject"].get("Id")

    # Generic sObject format
    return data.get("Id") or data.get("recordId") or data.get("RecordId")


def _extract_salesforce_event_type(data: dict) -> str:
    """Extract event type from Salesforce webhook payload."""
    if "data" in data and "payload" in data["data"]:
        payload = data["data"]["payload"]
        if "ChangeEventHeader" in payload:
            return payload["ChangeEventHeader"].get("entityName", "unknown")

    if "Notification" in data:
        notification = data["Notification"]
        if "sObject" in notification:
            obj_type = notification["sObject"].get("type", "unknown")
            return f"{obj_type}_update"

    return "unknown"


def _handle_webhook_error(
    logger: logging.Logger,
    error: Exception,
    provider: str,
    *,
    record_id: str | None = None,
    event_type: str = "unknown",
    event_count: int = 0,
    companies_to_sync: int = 0,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Handle webhook processing error with audit logging.

    Returns a 202 Accepted response to prevent CRM retry storms,
    while emitting an audit event for observability.
    """
    extra = {"provider": provider, "error_type": type(error).__name__}
    if request_id:
        extra["request_id"] = request_id
    if record_id:
        extra["record_id"] = record_id
    if event_count:
        extra["event_count"] = event_count

    logger.error(f"Failed to process {provider} webhook: {type(error).__name__}: {str(error)}", extra=extra)

    # Build resource_id based on provider and available context
    resource_id = record_id or f"{provider}_{event_count}_events"

    # Build details dict with only relevant fields
    # Note: error_type only (not str(error)) to prevent leaking sensitive data
    details: dict[str, Any] = {
        "provider": provider,
        "error_type": type(error).__name__,
    }
    if event_type != "unknown":
        details["event_type"] = event_type
    if record_id:
        details["record_id"] = record_id
    if event_count:
        details["event_count"] = event_count
    if companies_to_sync:
        details["companies_to_sync"] = companies_to_sync

    event = emit_audit_event(
        AuditAction.WEBHOOK_PROCESSING_FAILED,
        resource_type="CRM_Webhook",
        resource_id=resource_id,
        outcome=AuditOutcome.FAILURE,
        details=details,
    )

    return _handle_webhook_errorResult.model_validate({
        "status": "error",
        "provider": provider,
        "error_type": type(error).__name__,
        "audit_event_id": str(event.id),
    })


# ============================================================================
# HubSpot Webhooks
# ============================================================================


@router.post("/hubspot", status_code=status.HTTP_202_ACCEPTED)
async def hubspot_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    tenant_id: str | None = Query(None, description="Tenant identifier for multi-tenant webhook routing"),
    webhook_token: str | None = Query(None, description="Per-tenant webhook token for authentication"),
    x_webhook_token: str | None = Header(None, alias="X-Webhook-Token"),
    x_hubspot_signature: str | None = Header(None, alias=HUBSPOT_SIGNATURE_HEADER),
    x_hubspot_signature_v3: str | None = Header(None, alias=HUBSPOT_SIGNATURE_V3_HEADER),
    db: AsyncSession = Depends(get_db_from_context),
) -> dict[str, Any]:
    """Handle HubSpot webhook for contact/company/deal changes.

    HubSpot sends notifications when objects are created, updated, or deleted.
    We trigger incremental sync for affected company (account) records.

    **Production Multi-Tenancy:**
    The `tenant_id` query parameter is required in production. Configure your
    HubSpot webhook URL with `?tenant_id=<your-tenant-id>&webhook_token=<token>`.
    The handler verifies both tenant existence and webhook token authenticity
    before syncing to prevent cross-tenant data leakage.

    Headers:
        X-Webhook-Token: Per-tenant opaque token (preferred)
        X-HubSpot-Signature: Legacy signature (optional)
        X-HubSpot-Signature-v3: v3 signature for verification (optional)

    Request Body:
        Array of subscription notification events:
        [
            {
                "eventId": 123,
                "subscriptionId": 456,
                "portalId": 789,
                "occurredAt": 1234567890,
                "subscriptionType": "company.propertyChange",
                "objectId": 987654321,
                "propertyName": "name",
                "propertyValue": "New Company Name"
            }
        ]
    """
    # ------------------------------------------------------------------
    # Tenant isolation: fail closed in production if tenant_id is missing
    # ------------------------------------------------------------------
    if _CRM_WEBHOOKS_REQUIRE_TENANT_ID and not tenant_id:
        logger.warning(
            "HubSpot webhook rejected: tenant_id query parameter is required in production. "
            "Configure your HubSpot webhook URL with ?tenant_id=<tenant-id>"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id query parameter is required",
        )

    # If tenant_id provided, verify the tenant has an active HubSpot integration
    effective_tenant_id = tenant_id or "default"
    integration = None
    if tenant_id:
        integration_service = IntegrationService(db)
        integration = await integration_service.get_integration(
            tenant_id, CRMProvider.HUBSPOT
        )
        if not integration:
            logger.warning(
                "HubSpot webhook rejected: no HubSpot integration for tenant=%s",
                tenant_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No HubSpot integration configured for tenant {tenant_id}",
            )
        if not integration.enabled:
            logger.warning(
                "HubSpot webhook rejected: HubSpot integration disabled for tenant=%s",
                tenant_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HubSpot integration is disabled for this tenant",
            )

    # Read body once and cache for both signature verification and JSON parsing
    body = await request.body()

    # Authenticate webhook using per-tenant token + optional HMAC
    provided_token = x_webhook_token or webhook_token
    app_state_secret = getattr(request.app.state, HUBSPOT_WEBHOOK_SECRET_ATTR, None)
    provided_signature = x_hubspot_signature_v3 or x_hubspot_signature
    if integration:
        await _authenticate_webhook(
            integration,
            provided_token=provided_token,
            provided_signature=provided_signature,
            body=body,
            app_state_webhook_secret=app_state_secret,
        )
    elif app_state_secret and provided_signature:
        # Legacy path: no tenant lookup, only global HMAC (not recommended)
        expected = hmac.new(app_state_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, provided_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
            )

    # CONTRACT §2.5: Parse and validate HubSpot events with Pydantic schema
    try:
        payload_str = body.decode()
        # HubSpot sends arrays of events
        events_adapter = TypeAdapter(list[HubSpotWebhookEvent])
        events_data = events_adapter.validate_json(payload_str)
        events = [e.model_dump() for e in events_data]
    except Exception as e:
        logger.warning(f"HubSpot webhook received invalid payload: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload") from e

    # Collect unique company IDs to sync
    company_ids = set()
    event_count = 0

    for event in events:
        # Skip non-dict events (malformed payload protection)
        if not isinstance(event, dict):
            logger.warning(f"Skipping non-dict event in HubSpot webhook: {type(event)}")
            continue

        event_count += 1
        subscription_type = event.get("subscriptionType", "")
        object_id = event.get("objectId")

        # Validate subscription_type is string before .lower()
        if not isinstance(subscription_type, str):
            logger.warning(f"Skipping event with non-string subscriptionType: {type(subscription_type)}")
            continue

        # Handle company events directly
        if "company" in subscription_type.lower() and object_id:
            company_ids.add(str(object_id))

        # Handle deal events - we need to find associated company
        elif "deal" in subscription_type.lower() and object_id:
            # Deal events require looking up the associated company
            # We'll trigger a general sync to pick up deal changes
            pass

    logger.info(
        "HubSpot webhook: %s events, %s unique companies tenant=%s",
        event_count,
        len(company_ids),
        effective_tenant_id,
    )

    # Trigger sync
    sync_service = CRMSyncService(db)

    try:
        if company_ids:
            # Sync specific companies
            await sync_service.sync_provider(
                CRMProvider.HUBSPOT,
                tenant_id=effective_tenant_id,
                incremental=True,
                account_ids=list(company_ids),
            )
            logger.info(
                "Triggered sync for %s HubSpot companies tenant=%s",
                len(company_ids),
                effective_tenant_id,
            )
        else:
            # No specific companies - trigger general incremental sync
            await sync_service.sync_provider(
                CRMProvider.HUBSPOT,
                tenant_id=effective_tenant_id,
                incremental=True,
            )
            logger.info(
                "Triggered general HubSpot incremental sync tenant=%s",
                effective_tenant_id,
            )

        return hubspot_webhookResult.model_validate({
            "status": "accepted",
            "provider": "hubspot",
            "events_processed": event_count,
            "companies_to_sync": len(company_ids),
            "tenant_id": effective_tenant_id,
        })


    except Exception as e:
        return _handle_webhook_error(
            logger,
            e,
            "hubspot",
            event_count=event_count,
            companies_to_sync=len(company_ids),
            request_id=getattr(request.state, "request_id", None),
        )


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def webhook_health() -> dict[str, Any]:
    """Health check endpoint for webhook monitoring."""
    return webhook_healthResult.model_validate({
        "status": "healthy",
        "webhooks": ["salesforce", "hubspot"],
    })


