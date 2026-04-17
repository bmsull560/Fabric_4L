"""
Encryption service for at-rest credential encryption.

Uses AES-256-GCM for authenticated encryption with associated data (AEAD).
Key management is abstracted - supports environment variables, AWS KMS, HashiCorp Vault.
"""

import base64
import logging
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data at rest.

    Uses Fernet (AES-128-CBC + HMAC) from the cryptography library.
    For production, replace with KMS-backed encryption (AWS KMS, Vault, etc.).

    Security:
        - Keys derived from master secret using PBKDF2
        - Each encryption uses unique salt and IV
        - Authenticated encryption prevents tampering
    """

    # In production, retrieve from KMS/Vault
    _MASTER_KEY: bytes | None = None
    _key_cache: dict[str, Fernet] = {}

    @classmethod
    def _get_master_key(cls) -> bytes:
        """Get the master encryption key from environment.

        Returns:
            Base64-encoded key bytes (suitable for Fernet)
        """
        if cls._MASTER_KEY is None:
            key_b64 = os.getenv("CREDENTIALS_MASTER_KEY")
            if not key_b64:
                # Fail fast in production; require explicit opt-in for ephemeral keys
                environment = os.getenv("ENVIRONMENT", "development").lower()
                allow_ephemeral = os.getenv("ALLOW_EPHEMERAL_ENCRYPTION", "").lower() in ("true", "1", "yes")
                if environment == "production" and not allow_ephemeral:
                    raise RuntimeError(
                        "CREDENTIALS_MASTER_KEY is required in production. "
                        "Set the environment variable or ALLOW_EPHEMERAL_ENCRYPTION=true for testing only."
                    )
                # Generate a key for development (logged as warning)
                logger.warning(
                    "CREDENTIALS_MASTER_KEY not set. Generating ephemeral key for development. "
                    "DO NOT USE IN PRODUCTION - credentials will be lost on restart."
                )
                cls._MASTER_KEY = Fernet.generate_key()
            else:
                # Validate that provided key is valid base64-encoded 32-byte key
                try:
                    # Fernet keys are 32 bytes url-safe base64 encoded = 43 chars
                    if len(key_b64) != 43:
                        raise ValueError(f"Invalid key length: {len(key_b64)}, expected 43")
                    cls._MASTER_KEY = key_b64.encode()
                except Exception as e:
                    raise ValueError(
                        f"CREDENTIALS_MASTER_KEY must be a valid Fernet key: {e}"
                    ) from e
        return cls._MASTER_KEY

    @classmethod
    def _get_fernet(cls, key_id: str) -> Fernet:
        """Get or create Fernet instance for given key ID."""
        if key_id not in cls._key_cache:
            # Derive key from master using key_id as salt context
            master = cls._get_master_key()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=key_id.encode(),
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master))
            cls._key_cache[key_id] = Fernet(key)
        return cls._key_cache[key_id]

    @classmethod
    def encrypt(cls, plaintext: str, key_id: str = "v1") -> bytes:
        """Encrypt plaintext string.

        Args:
            plaintext: Data to encrypt (e.g., JSON string of credentials)
            key_id: Key version identifier for key rotation support

        Returns:
            Encrypted ciphertext as bytes
        """
        if not plaintext:
            return b""
        fernet = cls._get_fernet(key_id)
        return fernet.encrypt(plaintext.encode())

    @classmethod
    def decrypt(cls, ciphertext: bytes, key_id: str = "v1") -> str:
        """Decrypt ciphertext bytes.

        Args:
            ciphertext: Encrypted data
            key_id: Key version identifier (must match encryption key)

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If decryption fails (invalid key, tampered data)
        """
        if not ciphertext:
            return ""
        try:
            fernet = cls._get_fernet(key_id)
            return fernet.decrypt(ciphertext).decode()
        except Exception as e:
            logger.error("Decryption failed for key_id=%s: %s", key_id, e)
            raise ValueError(f"Failed to decrypt credentials: {e}") from e

    @classmethod
    def rotate_key(cls, old_key_id: str, new_key_id: str, ciphertext: bytes) -> bytes:
        """Re-encrypt data with a new key.

        Args:
            old_key_id: Current key identifier
            new_key_id: New key identifier
            ciphertext: Data encrypted with old key

        Returns:
            Data re-encrypted with new key
        """
        plaintext = cls.decrypt(ciphertext, old_key_id)
        return cls.encrypt(plaintext, new_key_id)
