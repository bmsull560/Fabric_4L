"""
CRM Webhook handlers for real-time updates from Salesforce and HubSpot.

Handles push notifications when accounts are created/updated in CRM,
triggering immediate sync to keep Account records fresh.
"""

import hashlib
import hmac
import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.account import CRMProvider
from ...services.crm_sync_service import CRMSyncService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/crm", tags=["CRM Webhooks"])


# ============================================================================
# Salesforce Webhooks
# ============================================================================


@router.post("/salesforce", status_code=status.HTTP_200_OK)
async def salesforce_webhook(
    request: Request,
    x_salesforce_signature: str | None = Header(None),
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
    body = await request.body()

    # Verify signature if configured
    webhook_secret = getattr(request.app.state, "salesforce_webhook_secret", None)
    if webhook_secret and x_salesforce_signature:
        expected = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, x_salesforce_signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
            )

    try:
        data = await request.json()
    except Exception:
        logger.warning("Salesforce webhook received non-JSON payload")
        data = {"raw_body": body.decode()}

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
        logger.error(f"Failed to process Salesforce webhook: {e}")
        # Return 200 to prevent Salesforce from retrying (we logged the error)
        return {
            "status": "error",
            "provider": "salesforce",
            "error": str(e),
        }


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


# ============================================================================
# HubSpot Webhooks
# ============================================================================


@router.post("/hubspot", status_code=status.HTTP_200_OK)
async def hubspot_webhook(
    request: Request,
    x_hubspot_signature: str | None = Header(None),
    x_hubspot_signature_v3: str | None = Header(None),
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
    body = await request.body()

    # Verify signature if configured
    webhook_secret = getattr(request.app.state, "hubspot_webhook_secret", None)
    if webhook_secret:
        if x_hubspot_signature_v3:
            # V3 signature verification
            expected = hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, x_hubspot_signature_v3):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature"
                )

    try:
        events = await request.json()
        if not isinstance(events, list):
            events = [events]
    except Exception as e:
        logger.warning(f"HubSpot webhook received invalid payload: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    # Collect unique company IDs to sync
    company_ids = set()
    event_count = 0

    for event in events:
        event_count += 1
        subscription_type = event.get("subscriptionType", "")
        object_id = event.get("objectId")

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
        logger.error(f"Failed to process HubSpot webhook: {e}")
        # Return 200 to prevent HubSpot from retrying
        return {
            "status": "error",
            "provider": "hubspot",
            "error": str(e),
        }


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
