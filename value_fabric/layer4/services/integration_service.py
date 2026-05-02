"""
Integration Service for managing CRM provider configurations.

Handles CRUD operations for integrations with credential encryption,
validation, and audit logging. Supports Salesforce and HubSpot.
"""

import asyncio
import json
import logging
import os
import re
import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from value_fabric.shared.models.typed_dict import TypedDictModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..metrics import get_metrics
from ..models.account import CRMProvider
from ..models.integration import Integration, IntegrationStatus
from .encryption_service import DEFAULT_KEY_ID, EncryptionService


class IntegrationService_trigger_syncResult(TypedDictModel):
    provider: Any
    queued_at: Any
    status: str
    sync_id: Any

class IntegrationService_test_connectionResult(TypedDictModel):
    error_code: str
    message: str
    success: bool

class IntegrationService__test_salesforce_connectionResult(TypedDictModel):
    details: dict[str, Any] | None = None
    error_code: str | None = None
    message: str
    success: bool

class IntegrationService__test_hubspot_connectionResult(TypedDictModel):
    details: dict[str, Any] | None = None
    error_code: str | None = None
    message: str
    success: bool

class IntegrationService__test_crm_connectionResult(TypedDictModel):
    error_code: str
    message: str
    success: bool

# CRM API endpoint constants
SALESFORCE_API_VERSION = "v58.0"
HUBSPOT_API_VERSION = "v3"

logger = logging.getLogger(__name__)
_SYNC_JOBS: dict[str, asyncio.Task[None]] = {}

# URL validation pattern for instance URLs
_INSTANCE_URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
    r'localhost|'  # localhost
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class IntegrationValidationError(ValueError):
    """Raised when integration configuration is invalid."""

    pass


class IntegrationNotFoundError(ValueError):
    """Raised when requested integration does not exist."""

    pass


class IntegrationService:
    """Service for managing CRM integration configurations.

    Handles:
    - CRUD operations with encrypted credential storage
    - Configuration validation
    - Connection testing
    - Audit logging
    """

    # Validation constants
    MIN_SYNC_INTERVAL = 5  # minutes
    MAX_SYNC_INTERVAL = 1440  # minutes (24 hours)
    MIN_BATCH_SIZE = 10
    MAX_BATCH_SIZE = 500

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_integrations(
        self, tenant_id: str, provider: CRMProvider | None = None
    ) -> list[Integration]:
        """List all integrations for a tenant.

        Args:
            tenant_id: Tenant identifier
            provider: Optional filter by provider type

        Returns:
            List of integration configurations (credentials excluded)
        """
        query = select(Integration).where(Integration.tenant_id == tenant_id)

        if provider:
            query = query.where(Integration.provider == provider)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_integration(
        self, tenant_id: str, provider: CRMProvider
    ) -> Integration | None:
        """Get integration by tenant and provider.

        Args:
            tenant_id: Tenant identifier
            provider: CRM provider type

        Returns:
            Integration or None if not found
        """
        result = await self.db.execute(
            select(Integration).where(
                Integration.tenant_id == tenant_id,
                Integration.provider == provider,
            )
        )
        return result.scalar_one_or_none()

    async def create_or_update_integration(
        self,
        tenant_id: str,
        provider: CRMProvider,
        enabled: bool,
        credentials: dict[str, str],
        instance_url: str | None = None,
        sync_interval_minutes: int = 60,
        sync_batch_size: int = 100,
        user_id: str | None = None,
        salesforce_org_id: str | None = None,
    ) -> tuple[Integration, bool]:
        """Create or update an integration configuration.

        SECURITY: refresh_token is NOT accepted here. It is obtained
        exclusively via the OAuth callback flow and stored separately.

        Args:
            tenant_id: Tenant identifier
            provider: CRM provider (salesforce/hubspot)
            enabled: Whether integration is active
            credentials: Dict with api_key, api_secret, etc.
            instance_url: Optional CRM instance URL
            sync_interval_minutes: Sync frequency (5-1440)
            sync_batch_size: Records per batch (10-500)
            user_id: User making the change (for audit)
            salesforce_org_id: Salesforce organization ID

        Returns:
            Tuple of (Integration, is_created) where is_created is True for new integrations

        Raises:
            IntegrationValidationError: If configuration is invalid
        """
        # Validate configuration
        self._validate_config(
            enabled, credentials, sync_interval_minutes, sync_batch_size, instance_url
        )

        # Check if integration exists
        existing = await self.get_integration(tenant_id, provider)
        is_update = existing is not None

        # Preserve or generate webhook token
        if is_update:
            try:
                old_creds = await self.decrypt_credentials(existing)
                existing_webhook_token = old_creds.get("webhook_token")
            except Exception:
                existing_webhook_token = None
            if existing_webhook_token:
                credentials["webhook_token"] = existing_webhook_token
            else:
                credentials["webhook_token"] = secrets.token_hex(32)
        else:
            credentials["webhook_token"] = secrets.token_hex(32)

        # Encrypt credentials
        credentials_json = json.dumps(credentials)
        encrypted_creds = await EncryptionService.encrypt(credentials_json, key_id=DEFAULT_KEY_ID)

        if is_update:
            # Update existing
            existing.enabled = enabled
            existing.credentials_encrypted = encrypted_creds
            existing.encryption_key_id = DEFAULT_KEY_ID
            existing.instance_url = instance_url
            existing.sync_interval_minutes = sync_interval_minutes
            existing.sync_batch_size = sync_batch_size
            existing.updated_by = user_id
            if salesforce_org_id:
                existing.salesforce_org_id = salesforce_org_id
            # Reset status on config change
            if not enabled:
                existing.sync_status = IntegrationStatus.IDLE
        else:
            # Create new
            existing = Integration(
                tenant_id=tenant_id,
                provider=provider,
                enabled=enabled,
                credentials_encrypted=encrypted_creds,
                encryption_key_id=DEFAULT_KEY_ID,
                instance_url=instance_url,
                salesforce_org_id=salesforce_org_id,
                sync_interval_minutes=sync_interval_minutes,
                sync_batch_size=sync_batch_size,
                sync_status=IntegrationStatus.IDLE if not enabled else IntegrationStatus.PENDING,
                created_by=user_id,
                updated_by=user_id,
            )
            self.db.add(existing)

        await self.db.commit()
        await self.db.refresh(existing)

        logger.info(
            "Integration %s for tenant=%s provider=%s by user=%s",
            "updated" if is_update else "created",
            tenant_id,
            provider,
            user_id,
        )

        return existing, not is_update

    async def delete_integration(
        self, tenant_id: str, provider: CRMProvider, user_id: str | None = None
    ) -> bool:
        """Delete an integration configuration.

        Args:
            tenant_id: Tenant identifier
            provider: CRM provider type
            user_id: User making the deletion (for audit)

        Returns:
            True if deleted, False if not found
        """
        integration = await self.get_integration(tenant_id, provider)
        if not integration:
            return False

        await self.db.delete(integration)
        await self.db.commit()

        logger.info(
            "Integration deleted for tenant=%s provider=%s by user=%s",
            tenant_id,
            provider,
            user_id,
        )

        return True

    async def test_connection(
        self, tenant_id: str, provider: CRMProvider
    ) -> dict[str, Any]:
        """Test the CRM connection using stored credentials.

        Args:
            tenant_id: Tenant identifier
            provider: CRM provider type

        Returns:
            Test result dict with success, message, and details
        """
        integration = await self.get_integration(tenant_id, provider)
        if not integration:
            return IntegrationService_test_connectionResult.model_validate({
                "success": False,
                "message": f"No {provider.value} integration configured",
                "error_code": "NOT_CONFIGURED",
            })


        if not integration.enabled:
            return IntegrationService_test_connectionResult.model_validate({
                "success": False,
                "message": "Integration is disabled",
                "error_code": "DISABLED",
            })


        try:
            creds_json = await EncryptionService.decrypt(
                integration.credentials_encrypted, integration.encryption_key_id
            )
            credentials = json.loads(creds_json)

            # Perform actual HTTP connection test
            test_result = await self._test_crm_connection(
                provider, credentials, integration.instance_url
            )
            return test_result

        except Exception as e:
            logger.error("Connection test failed for %s: %s", provider, e)
            return IntegrationService_test_connectionResult.model_validate({
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "error_code": "CONNECTION_FAILED",
            })


    async def _test_crm_connection(
        self,
        provider: CRMProvider,
        credentials: dict[str, str],
        instance_url: str | None,
    ) -> dict[str, Any]:
        """Test connection to CRM provider.

        Args:
            provider: CRM provider type
            credentials: Decrypted credentials dict
            instance_url: Optional CRM instance URL

        Returns:
            Test result dict with success, message, and details
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            if provider == CRMProvider.SALESFORCE:
                return await self._test_salesforce_connection(
                    client, credentials, instance_url
                )
            elif provider == CRMProvider.HUBSPOT:
                return await self._test_hubspot_connection(client, credentials)
            else:
                return IntegrationService__test_crm_connectionResult.model_validate({
                    "success": False,
                    "message": f"Unsupported provider: {provider.value}",
                    "error_code": "UNSUPPORTED_PROVIDER",
                })


    async def _test_salesforce_connection(
        self,
        client: httpx.AsyncClient,
        credentials: dict[str, str],
        instance_url: str | None,
    ) -> dict[str, Any]:
        """Test Salesforce API connection using OAuth token.

        Args:
            client: HTTP client
            credentials: Must contain 'api_key' (OAuth access token)
            instance_url: Salesforce instance URL

        Returns:
            Connection test result
        """
        access_token = credentials.get("api_key")
        if not access_token:
            return IntegrationService__test_salesforce_connectionResult.model_validate({
                "success": False,
                "message": "Missing OAuth access token in credentials",
                "error_code": "MISSING_CREDENTIALS",
            })


        # Use provided instance_url or construct from credentials
        base_url = instance_url or credentials.get("instance_url", "")
        if not base_url:
            return IntegrationService__test_salesforce_connectionResult.model_validate({
                "success": False,
                "message": "Salesforce instance URL is required",
                "error_code": "MISSING_INSTANCE_URL",
            })


        try:
            # Test API access by querying Organization info (lightweight call)
            response = await client.get(
                f"{base_url}/services/data/{SALESFORCE_API_VERSION}/query/",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"q": "SELECT Name FROM Organization LIMIT 1"},
            )

            if response.status_code == 200:
                data = response.json()
                org_name = data.get("records", [{}])[0].get("Name", "Unknown")

                return IntegrationService__test_salesforce_connectionResult.model_validate({
                    "success": True,
                    "message": f"Connected to Salesforce: {org_name}",
                    "details": {
                        "accounts_accessible": True,
                        "opportunities_accessible": True,
                        "organization": org_name,
                        "api_version": SALESFORCE_API_VERSION,
                    },
                })


            elif response.status_code == 401:
                return IntegrationService__test_salesforce_connectionResult.model_validate({
                    "success": False,
                    "message": "Authentication failed - token may be expired",
                    "error_code": "AUTH_FAILED",
                })


            else:
                return IntegrationService__test_salesforce_connectionResult.model_validate({
                    "success": False,
                    "message": f"Salesforce API error: {response.status_code}",
                    "error_code": f"API_ERROR_{response.status_code}",
                })


        except httpx.TimeoutException:
            return IntegrationService__test_salesforce_connectionResult.model_validate({
                "success": False,
                "message": "Connection timed out after 30 seconds",
                "error_code": "TIMEOUT",
            })


        except httpx.NetworkError as e:
            return IntegrationService__test_salesforce_connectionResult.model_validate({
                "success": False,
                "message": f"Network error: {str(e)}",
                "error_code": "NETWORK_ERROR",
            })


    async def _test_hubspot_connection(
        self,
        client: httpx.AsyncClient,
        credentials: dict[str, str],
    ) -> dict[str, Any]:
        """Test HubSpot API connection using API key.

        Args:
            client: HTTP client
            credentials: Must contain 'api_key' (HubSpot API key)

        Returns:
            Connection test result
        """
        api_key = credentials.get("api_key")
        if not api_key:
            return IntegrationService__test_hubspot_connectionResult.model_validate({
                "success": False,
                "message": "Missing API key in credentials",
                "error_code": "MISSING_CREDENTIALS",
            })


        try:
            # Test API access by querying account info
            response = await client.get(
                f"https://api.hubapi.com/account-info/{HUBSPOT_API_VERSION}/details",
                headers={"Authorization": f"Bearer {api_key}"},
            )

            if response.status_code == 200:
                data = response.json()
                portal_name = data.get("portalName", "Unknown")

                return IntegrationService__test_hubspot_connectionResult.model_validate({
                    "success": True,
                    "message": f"Connected to HubSpot: {portal_name}",
                    "details": {
                        "accounts_accessible": True,
                        "opportunities_accessible": True,
                        "portal_name": portal_name,
                        "api_version": HUBSPOT_API_VERSION,
                    },
                })


            elif response.status_code == 401:
                return IntegrationService__test_hubspot_connectionResult.model_validate({
                    "success": False,
                    "message": "Authentication failed - API key may be invalid",
                    "error_code": "AUTH_FAILED",
                })


            else:
                return IntegrationService__test_hubspot_connectionResult.model_validate({
                    "success": False,
                    "message": f"HubSpot API error: {response.status_code}",
                    "error_code": f"API_ERROR_{response.status_code}",
                })


        except httpx.TimeoutException:
            return IntegrationService__test_hubspot_connectionResult.model_validate({
                "success": False,
                "message": "Connection timed out after 30 seconds",
                "error_code": "TIMEOUT",
            })


        except httpx.NetworkError as e:
            return IntegrationService__test_hubspot_connectionResult.model_validate({
                "success": False,
                "message": f"Network error: {str(e)}",
                "error_code": "NETWORK_ERROR",
            })


    async def trigger_sync(
        self, tenant_id: str, provider: CRMProvider, user_id: str | None = None
    ) -> dict[str, Any]:
        """Trigger a manual sync for an integration.

        Args:
            tenant_id: Tenant identifier
            provider: CRM provider type
            user_id: User triggering sync (for audit)

        Returns:
            Sync job information
        """
        integration = await self.get_integration(tenant_id, provider)
        if not integration:
            raise IntegrationNotFoundError(f"No {provider.value} integration found")

        if not integration.enabled:
            raise IntegrationValidationError("Integration is disabled")

        # Generate sync job ID and enqueue background task
        sync_id = str(uuid.uuid4())
        queued_at = datetime.now(UTC).isoformat()

        # Mark as pending until the worker starts
        integration.sync_status = IntegrationStatus.PENDING
        await self.db.commit()

        async def _run_sync_job() -> None:
            from value_fabric.shared.identity.context import RequestContext

            from ..database import db_session_for_context
            from .crm_sync_service import CRMSyncService

            context = RequestContext(tenant_id=tenant_id)
            async with db_session_for_context(context) as bg_db:
                bg_integration_service = IntegrationService(bg_db)
                bg_integration = await bg_integration_service.get_integration(tenant_id, provider)
                if not bg_integration:
                    return

                bg_integration.sync_status = IntegrationStatus.RUNNING
                await bg_db.commit()

                try:
                    sync_service = CRMSyncService(bg_db)
                    stats = await sync_service.sync_provider(provider, tenant_id=tenant_id)

                    bg_integration.records_synced = stats["synced"] + stats["updated"]
                    bg_integration.records_updated = stats["updated"]
                    bg_integration.records_failed = stats["failed"]
                    bg_integration.last_sync_at = datetime.now(UTC)

                    if stats["failed"] > 0:
                        bg_integration.sync_status = IntegrationStatus.FAILED
                        bg_integration.last_error_message = "; ".join(stats["errors"][:3]) or "Sync failed"
                    else:
                        bg_integration.sync_status = IntegrationStatus.IDLE
                        bg_integration.last_successful_sync_at = datetime.now(UTC)
                        bg_integration.last_error_message = None
                    await bg_db.commit()
                except Exception as exc:
                    logger.exception(
                        "Background CRM sync job failed: tenant=%s provider=%s sync_id=%s",
                        tenant_id,
                        provider.value,
                        sync_id,
                    )
                    bg_integration.sync_status = IntegrationStatus.FAILED
                    bg_integration.last_sync_at = datetime.now(UTC)
                    bg_integration.last_error_message = str(exc)[:1000]
                    await bg_db.commit()

        try:
            _SYNC_JOBS[sync_id] = asyncio.create_task(_run_sync_job())
        except Exception as exc:
            integration.sync_status = IntegrationStatus.FAILED
            integration.last_error_message = f"Failed to enqueue sync: {exc}"
            await self.db.commit()
            raise IntegrationValidationError(f"Unable to queue sync: {exc}") from exc

        logger.info(
            "Sync queued for tenant=%s provider=%s sync_id=%s by user=%s",
            tenant_id,
            provider.value,
            sync_id,
            user_id,
        )

        return IntegrationService_trigger_syncResult.model_validate({
            "sync_id": sync_id,
            "status": "queued",
            "provider": provider.value,
            "queued_at": queued_at,
        })


    def _validate_config(
        self,
        enabled: bool,
        credentials: dict[str, str],
        sync_interval: int,
        batch_size: int,
        instance_url: str | None = None,
    ) -> None:
        """Validate integration configuration.

        Raises:
            IntegrationValidationError: If any validation fails
        """
        if enabled:
            if not credentials.get("api_key"):
                raise IntegrationValidationError("api_key is required when enabled=True")

        if not (self.MIN_SYNC_INTERVAL <= sync_interval <= self.MAX_SYNC_INTERVAL):
            raise IntegrationValidationError(
                f"sync_interval_minutes must be between {self.MIN_SYNC_INTERVAL} and {self.MAX_SYNC_INTERVAL}"
            )

        if not (self.MIN_BATCH_SIZE <= batch_size <= self.MAX_BATCH_SIZE):
            raise IntegrationValidationError(
                f"sync_batch_size must be between {self.MIN_BATCH_SIZE} and {self.MAX_BATCH_SIZE}"
            )

        if instance_url:
            if not _INSTANCE_URL_PATTERN.match(instance_url):
                raise IntegrationValidationError(
                    f"instance_url must be a valid HTTP/HTTPS URL: {instance_url}"
                )
            # Require HTTPS for production URLs (allow HTTP only for localhost)
            # Match exact localhost or localhost with port (not localhost.something.com)
            localhost_prefix = "http://localhost"
            is_localhost_http = (
                instance_url.startswith(localhost_prefix) and
                (len(instance_url) == len(localhost_prefix) or
                 instance_url[len(localhost_prefix)] in (":", "/"))  # port, path, or exact match
            )
            if instance_url.startswith("http://") and not is_localhost_http:
                raise IntegrationValidationError(
                    f"HTTPS is required for production URLs: {instance_url}"
                )

    async def decrypt_credentials(
        self, integration: Integration
    ) -> dict[str, str]:
        """Decrypt credentials for internal service use.

        Args:
            integration: Integration with encrypted credentials

        Returns:
            Decrypted credentials dict
        """
        creds_json = await EncryptionService.decrypt(
            integration.credentials_encrypted, integration.encryption_key_id
        )
        return json.loads(creds_json)

    async def refresh_salesforce_token(self, integration: Integration) -> dict[str, str]:
        """Refresh Salesforce OAuth access token using refresh token.

        Args:
            integration: Integration with refresh_token_encrypted

        Returns:
            Updated credentials dict with new access token

        Raises:
            IntegrationValidationError: If refresh fails
        """
        if not integration.refresh_token_encrypted:
            raise IntegrationValidationError("No refresh token available for Salesforce")

        try:
            refresh_token = await EncryptionService.decrypt(
                integration.refresh_token_encrypted, integration.encryption_key_id
            )
        except Exception as e:
            raise IntegrationValidationError(f"Failed to decrypt refresh token: {e}") from e

        # Salesforce OAuth token endpoint
        instance_url = integration.instance_url or "https://login.salesforce.com"
        token_url = f"{instance_url}/services/oauth2/token"

        client_id = os.getenv("SALESFORCE_CLIENT_ID")
        client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise IntegrationValidationError(
                "SALESFORCE_CLIENT_ID and SALESFORCE_CLIENT_SECRET must be configured"
            )

        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )

        if response.status_code != 200:
            integration.sync_status = IntegrationStatus.DEGRADED
            integration.last_error_message = f"Token refresh failed: HTTP {response.status_code}"
            await self.db.commit()
            prom = get_metrics()
            if prom:
                prom.increment_crm_salesforce_token_refresh_failed(integration.tenant_id)
            raise IntegrationValidationError(
                f"Token refresh failed: HTTP {response.status_code} - {response.text}"
            )

        token_data = response.json()
        new_access_token = token_data.get("access_token")
        new_instance_url = token_data.get("instance_url")

        if not new_access_token:
            raise IntegrationValidationError("Token refresh response missing access_token")

        # Update credentials with new access token
        credentials = await self.decrypt_credentials(integration)
        credentials["api_key"] = new_access_token
        if new_instance_url:
            credentials["instance_url"] = new_instance_url
            integration.instance_url = new_instance_url

        credentials_json = json.dumps(credentials)
        integration.credentials_encrypted = await EncryptionService.encrypt(
            credentials_json, key_id=integration.encryption_key_id
        )

        # Update refresh token if rotated
        new_refresh_token = token_data.get("refresh_token")
        if new_refresh_token:
            integration.refresh_token_encrypted = await EncryptionService.encrypt(
                new_refresh_token, key_id=integration.encryption_key_id
            )

        integration.sync_status = IntegrationStatus.IDLE
        integration.last_error_message = None
        await self.db.commit()

        logger.info(
            "Salesforce token refreshed for tenant=%s org=%s",
            integration.tenant_id,
            integration.salesforce_org_id or "unknown",
        )

        return credentials
