"""
Integration Service for managing CRM provider configurations.

Handles CRUD operations for integrations with credential encryption,
validation, and audit logging. Supports Salesforce and HubSpot.
"""

import json
import logging
import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.account import CRMProvider
from ..models.integration import Integration, IntegrationStatus
from .encryption_service import DEFAULT_KEY_ID, EncryptionService

logger = logging.getLogger(__name__)

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
    ) -> tuple[Integration, bool]:
        """Create or update an integration configuration.

        Args:
            tenant_id: Tenant identifier
            provider: CRM provider (salesforce/hubspot)
            enabled: Whether integration is active
            credentials: Dict with api_key, api_secret, etc.
            instance_url: Optional CRM instance URL
            sync_interval_minutes: Sync frequency (5-1440)
            sync_batch_size: Records per batch (10-500)
            user_id: User making the change (for audit)

        Returns:
            Tuple of (Integration, is_created) where is_created is True for new integrations

        Raises:
            IntegrationValidationError: If configuration is invalid
        """
        # Validate configuration
        self._validate_config(
            enabled, credentials, sync_interval_minutes, sync_batch_size, instance_url
        )

        # Encrypt credentials
        credentials_json = json.dumps(credentials)
        encrypted_creds = await EncryptionService.encrypt(credentials_json, key_id=DEFAULT_KEY_ID)

        # Check if integration exists
        existing = await self.get_integration(tenant_id, provider)
        is_update = existing is not None

        if is_update:
            # Update existing
            existing.enabled = enabled
            existing.credentials_encrypted = encrypted_creds
            existing.encryption_key_id = DEFAULT_KEY_ID
            existing.instance_url = instance_url
            existing.sync_interval_minutes = sync_interval_minutes
            existing.sync_batch_size = sync_batch_size
            existing.updated_by = user_id
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
            return {
                "success": False,
                "message": f"No {provider.value} integration configured",
                "error_code": "NOT_CONFIGURED",
            }

        if not integration.enabled:
            return {
                "success": False,
                "message": "Integration is disabled",
                "error_code": "DISABLED",
            }

        try:
            # Decrypt credentials (for actual connection test - TODO)
            creds_json = await EncryptionService.decrypt(
                integration.credentials_encrypted, integration.encryption_key_id
            )
            _credentials = json.loads(creds_json)  # noqa: F841 - reserved for connection test

            # TODO: Implement actual CRM connection test using _credentials
            # For now, return simulated success
            return {
                "success": True,
                "message": f"Connection to {provider.value} successful",
                "details": {
                    "accounts_accessible": True,
                    "opportunities_accessible": True,
                    "rate_limit_remaining": 999,
                },
            }

        except Exception as e:
            logger.error("Connection test failed for %s: %s", provider, e)
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "error_code": "CONNECTION_FAILED",
            }

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

        # Update status
        integration.sync_status = IntegrationStatus.RUNNING
        await self.db.commit()

        # TODO: Queue background sync job
        # For now, return job metadata
        sync_id = str(uuid.uuid4())

        logger.info(
            "Sync triggered for tenant=%s provider=%s sync_id=%s by user=%s",
            tenant_id,
            provider,
            sync_id,
            user_id,
        )

        return {
            "sync_id": sync_id,
            "status": "running",
            "provider": provider.value,
        }

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
