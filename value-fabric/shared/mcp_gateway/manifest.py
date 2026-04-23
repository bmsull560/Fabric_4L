"""Tool manifest signing and verification (ETDI - External Tool Description with Integrity).

Implements manifest signing using JSON Web Signature (JWS) to ensure
tool provenance and prevent supply chain attacks.

Reference:
    - JWS: https://tools.ietf.org/html/rfc7515
    - ETDI: External Tool Description with Integrity (emerging standard)
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from dataclasses import asdict
from typing import Any

from .mcp_types import ManifestValidationError, ToolManifest

logger = logging.getLogger(__name__)


class ManifestVerifier:
    """Verify tool manifest signatures using JWS.
    
    Ensures tools are cryptographically signed by trusted publishers,
    preventing supply chain attacks through compromised tool definitions.
    
    Example:
        >>> verifier = ManifestVerifier(public_key_pem)
        >>> manifest = ToolManifest(
        ...     tool_name="search",
        ...     version="1.0.0",
        ...     description="Search tool",
        ...     endpoint="https://search.example.com",
        ...     signature="eyJhbG..."
        ... )
        >>> if verifier.verify_manifest(manifest):
        ...     print("Manifest signature valid - tool is authentic")
        ... else:
        ...     raise ManifestValidationError("Invalid signature!")
    """
    
    def __init__(self, public_key: str | None = None):
        """Initialize with optional public key.
        
        Args:
            public_key: PEM-encoded RSA public key for signature verification
        """
        self.public_key = public_key
    
    @staticmethod
    def verify_manifest(manifest: ToolManifest, public_key: str | None = None) -> bool:
        """Verify the JWS signature of a tool manifest.
        
        Args:
            manifest: Tool manifest with signature
            public_key: Optional public key (uses instance key if not provided)
            
        Returns:
            True if signature is valid
            
        Raises:
            ManifestValidationError: If signature format is invalid
            
        Note:
            This is a placeholder implementation. Production should use:
            - python-jose or PyJWT for JWS verification
            - RSA signatures with SHA-256
            - Key rotation support via JWKS
        """
        if not manifest.signature:
            logger.warning(f"Manifest for tool '{manifest.tool_name}' has no signature")
            return False
        
        key = public_key or ManifestVerifier._get_trusted_key()
        if not key:
            logger.error("No public key available for manifest verification")
            raise ManifestValidationError("Cannot verify manifest - no trusted key available")
        
        try:
            # In production, use python-jose:
            # from jose import jws
            # payload = jws.verify(manifest.signature, key, algorithms=["RS256"])
            
            # Placeholder: Parse JWS structure and verify
            return ManifestVerifier._verify_jws(manifest.signature, key, manifest)
            
        except Exception as e:
            logger.error(f"Manifest signature verification failed: {e}")
            return False
    
    @staticmethod
    def _verify_jws(signature: str, public_key: str, manifest: ToolManifest) -> bool:
        """Verify JWS signature (placeholder implementation).
        
        Production implementation should:
        1. Parse JWS header to get algorithm
        2. Verify signature using public key
        3. Verify payload matches manifest content
        4. Check key ID (kid) matches expected issuer
        
        Args:
            signature: JWS compact serialization string
            public_key: PEM-encoded public key
            manifest: Manifest to verify against payload
            
        Returns:
            True if signature is valid
        """
        # Placeholder: In production, implement proper JWS verification
        # For now, simulate verification success if signature is non-empty
        
        if not signature:
            return False
        
        # Parse JWS compact serialization
        try:
            parts = signature.split(".")
            if len(parts) != 3:
                logger.error("Invalid JWS format - expected 3 parts")
                return False
            
            header_b64, payload_b64, signature_b64 = parts
            
            # Decode header to get algorithm
            header_json = base64.urlsafe_b64decode(header_b64 + "==").decode()
            header = json.loads(header_json)
            algorithm = header.get("alg", "none")
            
            if algorithm == "none":
                logger.warning("JWS uses 'none' algorithm - not secure!")
                return False
            
            # Decode payload
            payload_json = base64.urlsafe_b64decode(payload_b64 + "==").decode()
            payload = json.loads(payload_json)
            
            # Verify payload matches manifest
            if payload.get("tool_name") != manifest.tool_name:
                logger.error("Manifest name mismatch in JWS payload")
                return False
            
            if payload.get("version") != manifest.version:
                logger.error("Manifest version mismatch in JWS payload")
                return False
            
            # In production: Verify signature using RSA
            # For now, log that we would verify and return True for non-empty sigs
            logger.info(
                f"JWS verification would use algorithm: {algorithm}",
                extra={"tool_name": manifest.tool_name, "algorithm": algorithm}
            )
            
            # TODO: Implement actual RSA verification
            # from cryptography.hazmat.primitives import hashes, serialization
            # from cryptography.hazmat.primitives.asymmetric import padding
            # key = serialization.load_pem_public_key(public_key.encode())
            # key.verify(signature_bytes, signing_input, padding.PKCS1v15(), hashes.SHA256())
            
            return True  # Placeholder - assume valid
            
        except Exception as e:
            logger.error(f"JWS parsing/verification failed: {e}")
            return False
    
    @staticmethod
    def _get_trusted_key() -> str | None:
        """Get trusted public key for manifest verification.
        
        In production, this would:
        1. Load from environment variable
        2. Fetch from JWKS endpoint
        3. Use key from configured trust store
        
        Returns:
            PEM-encoded public key or None
        """
        import os
        
        # Try environment variable first
        key_path = os.getenv("MCP_MANIFEST_PUBLIC_KEY_PATH")
        if key_path:
            try:
                with open(key_path) as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to load public key from {key_path}: {e}")
        
        # Try direct key in environment
        key_pem = os.getenv("MCP_MANIFEST_PUBLIC_KEY")
        if key_pem:
            return key_pem
        
        return None
    
    @classmethod
    def compute_manifest_hash(cls, manifest: ToolManifest) -> str:
        """Compute canonical hash of manifest content (for signing).
        
        Creates a deterministic hash of the manifest fields,
        excluding the signature itself.
        
        Args:
            manifest: Tool manifest
            
        Returns:
            SHA-256 hash of canonical manifest representation
        """
        # Create canonical representation (sorted keys, no signature)
        manifest_dict = asdict(manifest)
        manifest_dict.pop("signature", None)
        
        canonical = json.dumps(manifest_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


class ManifestSigner:
    """Sign tool manifests using JWS.
    
    Used by tool publishers to sign manifests before distribution.
    
    Example:
        >>> signer = ManifestSigner(private_key_pem)
        >>> manifest = ToolManifest(
        ...     tool_name="search",
        ...     version="1.0.0",
        ...     description="Search tool",
        ...     endpoint="https://search.example.com"
        ... )
        >>> signed = signer.sign_manifest(manifest)
        >>> print(signed.signature)  # JWS string
    """
    
    def __init__(self, private_key: str, key_id: str | None = None):
        """Initialize with private key for signing.
        
        Args:
            private_key: PEM-encoded RSA private key
            key_id: Optional key identifier for JWS header
        """
        self.private_key = private_key
        self.key_id = key_id
    
    def sign_manifest(self, manifest: ToolManifest) -> ToolManifest:
        """Sign a tool manifest and return signed copy.
        
        Args:
            manifest: Unsigned manifest
            
        Returns:
            New manifest with signature field populated
            
        Raises:
            ManifestValidationError: If signing fails
        """
        try:
            # Create JWS payload from manifest
            payload = self._create_payload(manifest)
            
            # Create JWS header
            header = {"alg": "RS256", "typ": "JWT"}
            if self.key_id:
                header["kid"] = self.key_id
            
            # In production, use python-jose or PyJWT:
            # import jwt
            # token = jwt.encode(payload, self.private_key, algorithm="RS256", headers=header)
            
            # Placeholder: Create JWS compact serialization
            signature = self._create_jws(header, payload)
            
            # Return new manifest with signature
            return ToolManifest(
                tool_name=manifest.tool_name,
                version=manifest.version,
                description=manifest.description,
                endpoint=manifest.endpoint,
                capabilities=manifest.capabilities,
                required_scopes=manifest.required_scopes,
                signature=signature,
                tenant_scoped=manifest.tenant_scoped,
            )
            
        except Exception as e:
            logger.error(f"Failed to sign manifest: {e}")
            raise ManifestValidationError(f"Failed to sign manifest: {e}") from e
    
    def _create_payload(self, manifest: ToolManifest) -> dict[str, Any]:
        """Create JWS payload from manifest.
        
        Args:
            manifest: Tool manifest
            
        Returns:
            Dictionary payload for JWS
        """
        from datetime import datetime
        
        return {
            "tool_name": manifest.tool_name,
            "version": manifest.version,
            "description": manifest.description,
            "endpoint": manifest.endpoint,
            "capabilities": manifest.capabilities,
            "required_scopes": manifest.required_scopes,
            "tenant_scoped": manifest.tenant_scoped,
            "iat": int(datetime.utcnow().timestamp()),
        }
    
    def _create_jws(self, header: dict, payload: dict) -> str:
        """Create JWS compact serialization (placeholder).
        
        Args:
            header: JWS header
            payload: JWS payload
            
        Returns:
            JWS compact serialization string
        """
        # Placeholder: In production, use proper JWS library
        # For now, create base64-encoded mock signature
        
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).decode().rstrip("=")
        
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip("=")
        
        # In production: Sign with RSA private key
        # For now: Create a placeholder signature
        signing_input = f"{header_b64}.{payload_b64}".encode()
        
        # TODO: Implement proper RSA signing
        # from cryptography.hazmat.primitives import hashes, serialization
        # from cryptography.hazmat.primitives.asymmetric import padding
        # key = serialization.load_pem_private_key(self.private_key.encode(), password=None)
        # signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        # signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        
        # Placeholder signature
        signature_hash = hashlib.sha256(signing_input).hexdigest()[:32]
        signature_b64 = base64.urlsafe_b64encode(
            f"placeholder_sig_{signature_hash}".encode()
        ).decode().rstrip("=")
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"
