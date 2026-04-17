"""
Unit tests for Integration Service refinements.

Tests validation logic, edge cases, and error handling.
"""

import pytest
from src.models.account import CRMProvider
from src.services.integration_service import (
    IntegrationService,
    IntegrationValidationError,
)


class TestIntegrationValidation:
    """Test suite for integration configuration validation."""

    def test_validate_config_valid(self):
        """Test valid configuration passes validation."""
        service = IntegrationService(None)  # db not needed for validation
        
        # Should not raise
        service._validate_config(
            enabled=True,
            credentials={"api_key": "valid_key"},
            sync_interval=60,
            batch_size=100,
            instance_url="https://instance.salesforce.com",
        )

    def test_validate_config_missing_api_key_when_enabled(self):
        """Test that enabled=True requires api_key."""
        service = IntegrationService(None)
        
        with pytest.raises(IntegrationValidationError) as exc:
            service._validate_config(
                enabled=True,
                credentials={},  # Missing api_key
                sync_interval=60,
                batch_size=100,
            )
        
        assert "api_key is required" in str(exc.value)

    def test_validate_config_disabled_no_api_key(self):
        """Test that disabled integration doesn't require api_key."""
        service = IntegrationService(None)
        
        # Should not raise - disabled integrations don't need credentials
        service._validate_config(
            enabled=False,
            credentials={},
            sync_interval=60,
            batch_size=100,
        )

    def test_validate_config_invalid_sync_interval(self):
        """Test sync_interval bounds validation."""
        service = IntegrationService(None)
        
        # Too low
        with pytest.raises(IntegrationValidationError) as exc:
            service._validate_config(
                enabled=False,
                credentials={},
                sync_interval=4,  # Below minimum of 5
                batch_size=100,
            )
        assert "between 5 and 1440" in str(exc.value)
        
        # Too high
        with pytest.raises(IntegrationValidationError) as exc:
            service._validate_config(
                enabled=False,
                credentials={},
                sync_interval=1441,  # Above maximum
                batch_size=100,
            )
        assert "between 5 and 1440" in str(exc.value)

    def test_validate_config_invalid_batch_size(self):
        """Test batch_size bounds validation."""
        service = IntegrationService(None)
        
        # Too low
        with pytest.raises(IntegrationValidationError) as exc:
            service._validate_config(
                enabled=False,
                credentials={},
                sync_interval=60,
                batch_size=9,  # Below minimum of 10
            )
        assert "between 10 and 500" in str(exc.value)
        
        # Too high
        with pytest.raises(IntegrationValidationError) as exc:
            service._validate_config(
                enabled=False,
                credentials={},
                sync_interval=60,
                batch_size=501,  # Above maximum
            )
        assert "between 10 and 500" in str(exc.value)

    def test_validate_config_invalid_instance_url(self):
        """Test instance_url format validation."""
        service = IntegrationService(None)
        
        # Invalid URL
        with pytest.raises(IntegrationValidationError) as exc:
            service._validate_config(
                enabled=False,
                credentials={},
                sync_interval=60,
                batch_size=100,
                instance_url="not-a-valid-url",
            )
        assert "valid HTTP/HTTPS URL" in str(exc.value)
        
        # FTP is not allowed
        with pytest.raises(IntegrationValidationError) as exc:
            service._validate_config(
                enabled=False,
                credentials={},
                sync_interval=60,
                batch_size=100,
                instance_url="ftp://example.com",
            )
        assert "valid HTTP/HTTPS URL" in str(exc.value)

    def test_validate_config_valid_instance_urls(self):
        """Test that valid instance URLs pass."""
        service = IntegrationService(None)
        
        valid_urls = [
            "https://instance.salesforce.com",
            "https://api.hubspot.com",
            "http://localhost:8080",
            "https://my-org.my.salesforce.com",
            "https://10.0.0.1:443",
        ]
        
        for url in valid_urls:
            # Should not raise
            service._validate_config(
                enabled=False,
                credentials={},
                sync_interval=60,
                batch_size=100,
                instance_url=url,
            )

    def test_validate_config_none_instance_url(self):
        """Test that None instance_url is allowed."""
        service = IntegrationService(None)
        
        # Should not raise
        service._validate_config(
            enabled=False,
            credentials={},
            sync_interval=60,
            batch_size=100,
            instance_url=None,
        )


class TestEncryptionService:
    """Test suite for encryption service."""

    def test_encryption_roundtrip(self):
        """Test that encrypt/decrypt preserves data."""
        from src.services.encryption_service import EncryptionService
        
        test_data = '{"api_key": "secret123", "api_secret": "supersecret"}'
        
        encrypted = EncryptionService.encrypt(test_data, key_id="v1")
        assert encrypted != test_data.encode()
        assert isinstance(encrypted, bytes)
        
        decrypted = EncryptionService.decrypt(encrypted, key_id="v1")
        assert decrypted == test_data

    def test_encryption_empty_data(self):
        """Test that empty data is handled gracefully."""
        from src.services.encryption_service import EncryptionService
        
        # Empty string returns empty bytes
        assert EncryptionService.encrypt("", key_id="v1") == b""
        assert EncryptionService.decrypt(b"", key_id="v1") == ""

    def test_encryption_different_keys(self):
        """Test that different key_ids produce different ciphertexts."""
        from src.services.encryption_service import EncryptionService
        
        test_data = "sensitive data"
        
        encrypted_v1 = EncryptionService.encrypt(test_data, key_id="v1")
        encrypted_v2 = EncryptionService.encrypt(test_data, key_id="v2")
        
        # Same plaintext, different ciphertexts
        assert encrypted_v1 != encrypted_v2
        
        # But both decrypt correctly with their keys
        assert EncryptionService.decrypt(encrypted_v1, key_id="v1") == test_data
        assert EncryptionService.decrypt(encrypted_v2, key_id="v2") == test_data

    def test_decryption_wrong_key_fails(self):
        """Test that decrypting with wrong key fails appropriately."""
        from src.services.encryption_service import EncryptionService
        
        test_data = "sensitive data"
        encrypted = EncryptionService.encrypt(test_data, key_id="v1")
        
        # Decrypting with wrong key should fail
        with pytest.raises(ValueError) as exc:
            EncryptionService.decrypt(encrypted, key_id="wrong_key")
        
        assert "Failed to decrypt" in str(exc.value)
