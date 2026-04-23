"""Local key signing implementation."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .manifest import ManifestSigner, SignedManifest


class LocalKeySigner(ManifestSigner):
    """Sign manifests with local Ed25519 key."""
    
    def __init__(self, key_path: Optional[Path] = None, key_id: str = "fabric-local"):
        super().__init__(key_id)
        self.key_path = key_path or Path.home() / ".fabric" / "signing.key"
        self.logger = logging.getLogger("gated.signing.local")
        self._private_key = None
        self._public_key = None
    
    def _load_or_generate_key(self) -> tuple:
        """Load existing key or generate new one."""
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        except ImportError:
            self.logger.error("cryptography package required for signing")
            raise
        
        if self.key_path.exists():
            # Load existing key
            key_bytes = self.key_path.read_bytes()
            private_key = Ed25519PrivateKey.from_private_bytes(key_bytes[:32])
            self.logger.info(f"Loaded signing key from {self.key_path}")
        else:
            # Generate new key
            private_key = Ed25519PrivateKey.generate()
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save private key
            private_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
            self.key_path.write_bytes(private_bytes)
            self.key_path.chmod(0o600)
            
            # Save public key
            public_key = private_key.public_key()
            public_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            public_path = self.key_path.with_suffix(".pub")
            public_path.write_bytes(public_bytes)
            
            self.logger.info(f"Generated new signing key: {self.key_path}")
        
        self._private_key = private_key
        self._public_key = private_key.public_key()
        
        return private_key, self._public_key
    
    def sign(self, manifest: SignedManifest) -> SignedManifest:
        """Sign manifest with local key."""
        from cryptography.hazmat.primitives import serialization
        
        private_key, public_key = self._load_or_generate_key()
        
        # Create canonical JSON for signing
        content = manifest.to_json()
        content_bytes = content.encode("utf-8")
        
        # Sign
        signature = private_key.sign(content_bytes)
        
        # Get public key bytes for inclusion
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        
        manifest.signatures = {
            "primary": {
                "algorithm": "ed25519",
                "key_id": self.key_id,
                "public_key": public_bytes.hex(),
                "signature": signature.hex(),
                "signed_at": datetime.utcnow().isoformat(),
            }
        }
        
        self.logger.info(f"Signed manifest for {manifest.release_id}")
        
        return manifest
    
    def verify(self, manifest: SignedManifest) -> bool:
        """Verify manifest signature."""
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            from cryptography.exceptions import InvalidSignature
        except ImportError:
            self.logger.error("cryptography package required for verification")
            return False
        
        sig_data = manifest.signatures.get("primary")
        if not sig_data:
            self.logger.error("No signature found")
            return False
        
        if sig_data.get("algorithm") != "ed25519":
            self.logger.error(f"Unsupported algorithm: {sig_data.get('algorithm')}")
            return False
        
        try:
            # Reconstruct public key
            public_bytes = bytes.fromhex(sig_data["public_key"])
            public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
            
            # Get signature
            signature = bytes.fromhex(sig_data["signature"])
            
            # Get canonical content (without signature)
            temp_manifest = SignedManifest(
                manifest_version=manifest.manifest_version,
                release_id=manifest.release_id,
                commit=manifest.commit,
                branch=manifest.branch,
                timestamp=manifest.timestamp,
                profile=manifest.profile,
                gates=manifest.gates,
                verdict=manifest.verdict,
            )
            content = temp_manifest.to_json()
            content_bytes = content.encode("utf-8")
            
            # Verify
            public_key.verify(signature, content_bytes)
            
            self.logger.info(f"Verified manifest for {manifest.release_id}")
            return True
            
        except InvalidSignature:
            self.logger.error("Signature verification failed")
            return False
        except Exception as e:
            self.logger.error(f"Verification error: {e}")
            return False
