"""
CRM Webhook handlers for real-time updates from Salesforce and HubSpot.

Handles push notifications when accounts are created/updated in CRM,
triggering immediate sync to keep Account records fresh.
"""

import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from shared.audit import AuditAction, AuditOutcome, emit_audit_event
from sqlalchemy.ext.asyncio import AsyncSession

# SECURITY: CRM webhook endpoints are server-to-server calls from
# Salesforce/HubSpot. Authentication is via HMAC signature verification,
# not JWT. get_db (no tenant context) is intentional here.
from ...database import get_db
from ...models.account import CRMProvider
from ...services.crm_sync_service import CRMSyncService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/crm", tags=["CRM Webhooks"])

# Header constants for webhook signature verification
SALESFORCE_SIGNATURE_HEADER = "X-Salesforce-Signature"
HUBSPOT_SIGNATURE_HEADER = "X-HubSpot-Signature"
HUBSPOT_SIGNATURE_V3_HEADER = "X-HubSpot-Signature-v3"

# App state attribute names for webhook secrets
SALESFORCE_WEBHOOK_SECRET_ATTR = "salesforce_webhook_secret"
HUBSPOT_WEBHOOK_SECRET_ATTR = "hubspot_webhook_secret"


# ============================================================================
# Salesforce Webhooks
# ============================================================================


@router.post("/salesforce", status_code=status.HTTP_202_ACCEPTED)
async def salesforce_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_salesforce_signature: str | None = Header(None, alias=SALESFORCE_SIGNATURE_HEADER),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle Salesforce outbound message or platform event webhook.

    Salesforce sends notifications when Accounts, Opportunities, or Contacts
    are created/updated. We trigger incremental sync for affected records.

    Headers:
        X-Salesforce-Signature: HMAC signature for verification (optional)

    Request Body:
        Salesforce platform event or outbound message payload
    """
    # Read body once and cache for both signature verification and JSON parsing
    body = await request.body()

    # Verify signature if configured
    webhook_secret = getattr(request.app.state, SALESFORCE_WEBHOOK_SECRET_ATTR, None)
    if webhook_secret:
        sig_valid = False
        if x_salesforce_signature:
            expected = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
            sig_valid = hmac.compare_digest(expected, x_salesforce_signature)
        if not sig_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
            )

    # Parse JSON from cached body bytes (don't call request.json() - body already consumed)
    try:
        data = json.loads(body.decode())
    except json.JSONDecodeError:
        logger.warning("Salesforce webhook received non-JSON payload", extra={"body_preview": body[:200].decode(errors='replace')})
        data = {"raw_body": body.decode(errors='replace')}

    # Extract record info from Salesforce payload
    # Platform events: {"data": {"payload": {"RecordId": "...", "ChangeEventHeader": {...}}}}
    # Outbound messages: {"Notification": {"sObject": {"Id": "...", ...}}}

    record_id = _extract_salesforce_record_id(data)
    event_type = _extract_salesforce_event_type(data)

    logger.info(f"Salesforce webhook: {event_type} for record {record_id}")

    # Trigger sync for the affected record
    sync_service = CRMSyncService(db)

    try:
        if record_id:
            # Sync specific account
            await sync_service.sync_provider(
                CRMProvider.SALESFORCE, incremental=True, account_ids=[record_id]
            )
            logger.info(f"Triggered sync for Salesforce account {record_id}")
        else:
            # No specific record - trigger general incremental sync
            await sync_service.sync_provider(CRMProvider.SALESFORCE, incremental=True)
            logger.info("Triggered general Salesforce incremental sync")

        return {
            "status": "accepted",
            "provider": "salesforce",
            "event_type": event_type,
            "record_id": record_id,
        }

    except Exception as e:
        return _handle_webhook_error(
            logger, e, "salesforce", record_id=record_id, event_type=event_type
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

    return {
        "status": "error",
        "provider": provider,
        "error_type": type(error).__name__,
        "audit_event_id": str(event.id),
    }


# ============================================================================
# HubSpot Webhooks
# ============================================================================


@router.post("/hubspot", status_code=status.HTTP_202_ACCEPTED)
async def hubspot_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hubspot_signature: str | None = Header(None, alias=HUBSPOT_SIGNATURE_HEADER),
    x_hubspot_signature_v3: str | None = Header(None, alias=HUBSPOT_SIGNATURE_V3_HEADER),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Handle HubSpot webhook for contact/company/deal changes.

    HubSpot sends notifications when objects are created, updated, or deleted.
    We trigger incremental sync for affected company (account) records.

    Headers:
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
    # Read body once and cache for both signature verification and JSON parsing
    body = await request.body()

    # Verify signature if configured (v3 or legacy)
    webhook_secret = getattr(request.app.state, HUBSPOT_WEBHOOK_SECRET_ATTR, None)
    if webhook_secret:
        sig_to_verify = x_hubspot_signature_v3 or x_hubspot_signature
        sig_valid = False
        if sig_to_verify:
            expected = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
            sig_valid = hmac.compare_digest(expected, sig_to_verify)
        if not sig_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
            )

    # Parse JSON from cached body bytes
    try:
        events = json.loads(body.decode())
        if events is None:
            events = []
        elif not isinstance(events, list):
            events = [events]
    except json.JSONDecodeError as e:
        logger.warning(f"HubSpot webhook received invalid payload: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

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

    logger.info(f"HubSpot webhook: {event_count} events, {len(company_ids)} unique companies")

    # Trigger sync
    sync_service = CRMSyncService(db)

    try:
        if company_ids:
            # Sync specific companies
            await sync_service.sync_provider(
                CRMProvider.HUBSPOT, incremental=True, account_ids=list(company_ids)
            )
            logger.info(f"Triggered sync for {len(company_ids)} HubSpot companies")
        else:
            # No specific companies - trigger general incremental sync
            await sync_service.sync_provider(CRMProvider.HUBSPOT, incremental=True)
            logger.info("Triggered general HubSpot incremental sync")

        return {
            "status": "accepted",
            "provider": "hubspot",
            "events_processed": event_count,
            "companies_to_sync": len(company_ids),
        }

    except Exception as e:
        return _handle_webhook_error(
            logger,
            e,
            "hubspot",
            event_count=event_count,
            companies_to_sync=len(company_ids),
        )


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def webhook_health() -> dict[str, Any]:
    """Health check endpoint for webhook monitoring."""
    return {
        "status": "healthy",
        "webhooks": ["salesforce", "hubspot"],
    }
