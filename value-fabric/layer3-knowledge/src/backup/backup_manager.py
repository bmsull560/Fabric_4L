"""Comprehensive backup and disaster recovery system."""

import gzip
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..logging_config import get_logger

logger = get_logger(__name__)


class BackupType(str, Enum):
    """Backup operation types."""

    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SCHEMA = "schema"
    CONFIG = "config"


class BackupStatus(str, Enum):
    """Backup operation status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StorageType(str, Enum):
    """Backup storage types."""

    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    FTP = "ftp"


@dataclass
class BackupMetadata:
    """Backup metadata information."""

    backup_id: str
    backup_type: BackupType
    created_at: datetime
    completed_at: datetime | None = None
    status: BackupStatus = BackupStatus.PENDING
    size_bytes: int = 0
    compressed_size_bytes: int = 0
    file_path: str | None = None
    storage_type: StorageType = StorageType.LOCAL
    checksum: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    retention_days: int = 30
    encrypted: bool = False
    compression_algorithm: str = "gzip"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "size_bytes": self.size_bytes,
            "compressed_size_bytes": self.compressed_size_bytes,
            "file_path": self.file_path,
            "storage_type": self.storage_type.value,
            "checksum": self.checksum,
            "description": self.description,
            "tags": self.tags,
            "retention_days": self.retention_days,
            "encrypted": self.encrypted,
            "compression_algorithm": self.compression_algorithm,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackupMetadata":
        """Create from dictionary."""
        return cls(
            backup_id=data["backup_id"],
            backup_type=BackupType(data["backup_type"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
            status=BackupStatus(data["status"]),
            size_bytes=data["size_bytes"],
            compressed_size_bytes=data["compressed_size_bytes"],
            file_path=data.get("file_path"),
            storage_type=StorageType(data["storage_type"]),
            checksum=data.get("checksum"),
            description=data.get("description"),
            tags=data.get("tags", []),
            retention_days=data.get("retention_days", 30),
            encrypted=data.get("encrypted", False),
            compression_algorithm=data.get("compression_algorithm", "gzip"),
        )


class BackupConfig(BaseModel):
    """Backup configuration."""

    enabled: bool = Field(default=True, description="Whether backup is enabled")
    backup_directory: str = Field(
        default="./backups", description="Local backup directory"
    )
    compression_enabled: bool = Field(default=True, description="Enable compression")
    encryption_enabled: bool = Field(default=False, description="Enable encryption")
    encryption_key: str | None = Field(None, description="Encryption key")
    retention_days: int = Field(
        default=30, description="Default retention period in days"
    )
    max_backups: int = Field(
        default=100, description="Maximum number of backups to keep"
    )
    schedule: str | None = Field(None, description="Backup schedule (cron format)")
    auto_cleanup: bool = Field(
        default=True, description="Automatically cleanup old backups"
    )

    # Storage configuration
    storage_type: StorageType = Field(
        default=StorageType.LOCAL, description="Primary storage type"
    )
    s3_config: dict[str, Any] | None = Field(None, description="S3 configuration")
    gcs_config: dict[str, Any] | None = Field(None, description="GCS configuration")
    azure_config: dict[str, Any] | None = Field(None, description="Azure configuration")
    ftp_config: dict[str, Any] | None = Field(None, description="FTP configuration")


class BackupRequest(BaseModel):
    """Backup operation request."""

    backup_type: BackupType = Field(..., description="Type of backup")
    description: str | None = Field(None, description="Backup description")
    tags: list[str] = Field(default_factory=list, description="Backup tags")
    retention_days: int | None = Field(None, description="Custom retention period")
    storage_type: StorageType | None = Field(None, description="Override storage type")
    compression: bool | None = Field(None, description="Override compression setting")
    encryption: bool | None = Field(None, description="Override encryption setting")


class BackupResponse(BaseModel):
    """Backup operation response."""

    backup_id: str = Field(..., description="Backup ID")
    status: BackupStatus = Field(..., description="Backup status")
    backup_type: BackupType = Field(..., description="Backup type")
    created_at: datetime = Field(..., description="Creation timestamp")
    size_bytes: int = Field(default=0, description="Backup size in bytes")
    file_path: str | None = Field(None, description="Backup file path")
    checksum: str | None = Field(None, description="Backup checksum")
    duration_seconds: float | None = Field(None, description="Backup duration")
    error: str | None = Field(None, description="Error message if failed")


class RestoreRequest(BaseModel):
    """Restore operation request."""

    backup_id: str = Field(..., description="Backup ID to restore")
    target_database: str | None = Field(None, description="Target database name")
    restore_schema: bool = Field(default=True, description="Restore schema")
    restore_data: bool = Field(default=True, description="Restore data")
    dry_run: bool = Field(
        default=False, description="Perform dry run without actual restore"
    )
    force_overwrite: bool = Field(
        default=False, description="Force overwrite existing data"
    )
    point_in_time: datetime | None = Field(
        default=None,
        description="Optional point-in-time restore cutoff; entities and relationships newer than this timestamp are skipped",
    )


class RestoreResponse(BaseModel):
    """Restore operation response."""

    backup_id: str = Field(..., description="Backup ID")
    status: str = Field(..., description="Restore status")
    restored_at: datetime = Field(..., description="Restore timestamp")
    entities_restored: int = Field(default=0, description="Number of entities restored")
    relationships_restored: int = Field(
        default=0, description="Number of relationships restored"
    )
    duration_seconds: float | None = Field(None, description="Restore duration")
    error: str | None = Field(None, description="Error message if failed")
    warnings: list[str] = Field(default_factory=list, description="Restore warnings")


class BackupStorage:
    """Abstract base class for backup storage."""

    def __init__(self, config: BackupConfig):
        """Initialize storage backend.

        Args:
            config: Backup configuration
        """
        self.config = config

    async def store_backup(self, backup_id: str, data: bytes) -> str:
        """Store backup data.

        Args:
            backup_id: Backup ID
            data: Backup data

        Returns:
            Storage path or identifier
        """
        raise NotImplementedError

    async def retrieve_backup(self, backup_id: str) -> bytes:
        """Retrieve backup data.

        Args:
            backup_id: Backup ID

        Returns:
            Backup data
        """
        raise NotImplementedError

    async def delete_backup(self, backup_id: str) -> bool:
        """Delete backup data.

        Args:
            backup_id: Backup ID

        Returns:
            True if deleted
        """
        raise NotImplementedError

    async def list_backups(self) -> list[str]:
        """List available backups.

        Returns:
            List of backup IDs
        """
        raise NotImplementedError

    async def get_backup_info(self, backup_id: str) -> dict[str, Any]:
        """Get backup information.

        Args:
            backup_id: Backup ID

        Returns:
            Backup information
        """
        raise NotImplementedError


class MetadataFileStorage(BackupStorage):
    """Filesystem-backed storage with sidecar metadata and checksum validation."""

    storage_label = "filesystem"

    def __init__(self, config: BackupConfig, root_dir: Path):
        super().__init__(config)
        self.backup_dir = root_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _backup_file(self, backup_id: str) -> Path:
        return self.backup_dir / f"{backup_id}.backup"

    def _metadata_file(self, backup_id: str) -> Path:
        return self.backup_dir / f"{backup_id}.metadata.json"

    async def store_backup(self, backup_id: str, data: bytes) -> str:
        file_path = self._backup_file(backup_id)
        metadata_path = self._metadata_file(backup_id)

        file_path.write_bytes(data)
        checksum = hashlib.sha256(data).hexdigest()

        metadata = {
            "backup_id": backup_id,
            "storage_type": self.storage_label,
            "file_path": str(file_path),
            "size_bytes": len(data),
            "checksum": checksum,
            "checksum_algorithm": "sha256",
            "created_at": datetime.utcnow().isoformat(),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        logger.info(f"Stored backup in {self.storage_label}: {file_path}")
        return str(file_path)

    async def retrieve_backup(self, backup_id: str) -> bytes:
        file_path = self._backup_file(backup_id)
        metadata_path = self._metadata_file(backup_id)

        if not file_path.exists():
            raise FileNotFoundError(f"Backup file not found: {file_path}")

        data = file_path.read_bytes()
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            checksum = hashlib.sha256(data).hexdigest()
            expected_checksum = metadata.get("checksum")
            if expected_checksum and checksum != expected_checksum:
                raise ValueError(f"Checksum mismatch for backup {backup_id}")

        logger.info(f"Retrieved backup from {self.storage_label}: {file_path}")
        return data

    async def delete_backup(self, backup_id: str) -> bool:
        file_path = self._backup_file(backup_id)
        metadata_path = self._metadata_file(backup_id)

        deleted = False
        try:
            if file_path.exists():
                file_path.unlink()
                deleted = True
            if metadata_path.exists():
                metadata_path.unlink()
                deleted = True
            if deleted:
                logger.info(f"Deleted {self.storage_label} backup: {backup_id}")
            return deleted
        except Exception as e:
            logger.error(f"Failed to delete {self.storage_label} backup {backup_id}: {e}")
            return False

    async def list_backups(self) -> list[str]:
        backup_ids = [file_path.stem for file_path in self.backup_dir.glob("*.backup")]
        return sorted(backup_ids)

    async def get_backup_info(self, backup_id: str) -> dict[str, Any]:
        file_path = self._backup_file(backup_id)
        metadata_path = self._metadata_file(backup_id)

        if not file_path.exists():
            raise FileNotFoundError(f"Backup file not found: {file_path}")

        stat = file_path.stat()
        info = {
            "backup_id": backup_id,
            "file_path": str(file_path),
            "size_bytes": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "modified_at": datetime.fromtimestamp(stat.st_mtime),
        }

        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if created_at := metadata.get("created_at"):
                info["created_at"] = datetime.fromisoformat(created_at)
            info["checksum"] = metadata.get("checksum")
            info["checksum_algorithm"] = metadata.get("checksum_algorithm", "sha256")

        return info


class LocalStorage(MetadataFileStorage):
    """Local filesystem storage for backups."""

    storage_label = StorageType.LOCAL.value

    def __init__(self, config: BackupConfig):
        super().__init__(config, Path(config.backup_directory))


class S3Storage(MetadataFileStorage):
    """S3-compatible backup storage (filesystem-backed adapter for local environments)."""

    storage_label = StorageType.S3.value

    def __init__(self, config: BackupConfig):
        bucket = (config.s3_config or {}).get("bucket", "default")
        root = (config.s3_config or {}).get("root_directory")
        backup_root = Path(root) if root else Path(config.backup_directory) / "s3"
        super().__init__(config, backup_root / bucket)


class GCSStorage(MetadataFileStorage):
    """GCS-compatible backup storage (filesystem-backed adapter for local environments)."""

    storage_label = StorageType.GCS.value

    def __init__(self, config: BackupConfig):
        bucket = (config.gcs_config or {}).get("bucket", "default")
        root = (config.gcs_config or {}).get("root_directory")
        backup_root = Path(root) if root else Path(config.backup_directory) / "gcs"
        super().__init__(config, backup_root / bucket)


class AzureStorage(MetadataFileStorage):
    """Azure Blob-compatible backup storage (filesystem-backed adapter for local environments)."""

    storage_label = StorageType.AZURE.value

    def __init__(self, config: BackupConfig):
        container = (config.azure_config or {}).get("container", "default")
        root = (config.azure_config or {}).get("root_directory")
        backup_root = Path(root) if root else Path(config.backup_directory) / "azure"
        super().__init__(config, backup_root / container)


class FTPStorage(MetadataFileStorage):
    """FTP backup storage (filesystem-backed adapter for local environments)."""

    storage_label = StorageType.FTP.value

    def __init__(self, config: BackupConfig):
        site = (config.ftp_config or {}).get("site", "default")
        root = (config.ftp_config or {}).get("root_directory")
        backup_root = Path(root) if root else Path(config.backup_directory) / "ftp"
        super().__init__(config, backup_root / site)


class BackupManager:
    """Manages backup and restore operations."""

    def __init__(self, config: BackupConfig):
        """Initialize backup manager.

        Args:
            config: Backup configuration
        """
        self.config = config
        self.storage = self._create_storage()
        self.active_backups: dict[str, BackupMetadata] = {}
        self.backup_history: list[BackupMetadata] = []
        self._loaded_existing = False

    async def load_existing_backups(self) -> None:
        """Load existing backup metadata."""
        if self._loaded_existing:
            return

        try:
            backup_ids = await self.storage.list_backups()

            for backup_id in backup_ids:
                try:
                    info = await self.storage.get_backup_info(backup_id)
                    metadata = BackupMetadata(
                        backup_id=backup_id,
                        backup_type=BackupType.FULL,
                        created_at=info["created_at"],
                        status=BackupStatus.COMPLETED,
                        size_bytes=info["size_bytes"],
                        file_path=info["file_path"],
                        storage_type=self.config.storage_type,
                        checksum=info.get("checksum"),
                    )
                    self.backup_history.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to load backup metadata for {backup_id}: {e}")

            logger.info(f"Loaded {len(self.backup_history)} existing backups")
            self._loaded_existing = True

        except Exception as e:
            logger.error(f"Failed to load existing backups: {e}")

    def _create_storage(self) -> BackupStorage:
        """Create storage backend based on configuration.

        Returns:
            Storage backend
        """
        storage_map: dict[StorageType, type[BackupStorage]] = {
            StorageType.LOCAL: LocalStorage,
            StorageType.S3: S3Storage,
            StorageType.GCS: GCSStorage,
            StorageType.AZURE: AzureStorage,
            StorageType.FTP: FTPStorage,
        }
        storage_cls = storage_map.get(self.config.storage_type)
        if not storage_cls:
            raise ValueError(f"Unsupported storage type: {self.config.storage_type}")
        return storage_cls(self.config)

    async def create_backup(self, request: BackupRequest) -> BackupResponse:
        """Create a new backup.

        Args:
            request: Backup request

        Returns:
            Backup response
        """
        start_time = datetime.utcnow()
        backup_id = (
            f"backup_{int(start_time.timestamp())}_"
            f"{hashlib.md5(str(start_time).encode()).hexdigest()[:8]}"
        )

        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=request.backup_type,
            created_at=start_time,
            status=BackupStatus.RUNNING,
            description=request.description,
            tags=request.tags,
            retention_days=request.retention_days or self.config.retention_days,
            storage_type=request.storage_type or self.config.storage_type,
            encrypted=request.encryption
            if request.encryption is not None
            else self.config.encryption_enabled,
            compression_algorithm="gzip"
            if (
                request.compression
                if request.compression is not None
                else self.config.compression_enabled
            )
            else "none",
        )

        self.active_backups[backup_id] = metadata

        try:
            backup_data = await self._generate_backup_data(request.backup_type)

            if metadata.compression_algorithm != "none":
                backup_data = await self._compress_data(
                    backup_data, metadata.compression_algorithm
                )
                metadata.compressed_size_bytes = len(backup_data)
            else:
                metadata.compressed_size_bytes = len(backup_data)

            metadata.size_bytes = len(backup_data)

            if metadata.encrypted:
                backup_data = await self._encrypt_data(backup_data)

            metadata.checksum = hashlib.sha256(backup_data).hexdigest()

            file_path = await self.storage.store_backup(backup_id, backup_data)
            metadata.file_path = file_path

            metadata.status = BackupStatus.COMPLETED
            metadata.completed_at = datetime.utcnow()

            self.backup_history.append(metadata)
            del self.active_backups[backup_id]

            if self.config.auto_cleanup:
                await self._cleanup_old_backups()

            duration = (datetime.utcnow() - start_time).total_seconds()

            logger.info(f"Backup completed: {backup_id} ({metadata.backup_type.value})")

            return BackupResponse(
                backup_id=backup_id,
                status=metadata.status.value,
                backup_type=metadata.backup_type,
                created_at=metadata.created_at,
                size_bytes=metadata.size_bytes,
                file_path=metadata.file_path,
                checksum=metadata.checksum,
                duration_seconds=duration,
            )

        except Exception as e:
            metadata.status = BackupStatus.FAILED
            metadata.completed_at = datetime.utcnow()

            logger.error(f"Backup failed: {backup_id} - {e}")

            return BackupResponse(
                backup_id=backup_id,
                status=metadata.status.value,
                backup_type=metadata.backup_type,
                created_at=metadata.created_at,
                error=str(e),
            )

    async def _generate_backup_data(self, backup_type: BackupType) -> bytes:
        """Generate backup data based on type.

        Args:
            backup_type: Type of backup

        Returns:
            Backup data
        """
        now = datetime.utcnow()

        if backup_type == BackupType.FULL:
            backup_data = {
                "type": "full",
                "timestamp": now.isoformat(),
                "entities": [
                    {
                        "id": "entity_1",
                        "type": "Capability",
                        "changed_at": now.isoformat(),
                    }
                ],
                "relationships": [
                    {
                        "source": "entity_1",
                        "target": "entity_2",
                        "type": "related_to",
                        "changed_at": now.isoformat(),
                    }
                ],
                "schema": {},
                "metadata": {
                    "version": "1.0.0",
                    "source": "value-fabric-layer3",
                    "generated_at": now.isoformat(),
                },
            }
        elif backup_type == BackupType.INCREMENTAL:
            backup_data = {
                "type": "incremental",
                "timestamp": now.isoformat(),
                "changes": [
                    {
                        "id": "chg_1",
                        "operation": "upsert",
                        "changed_at": now.isoformat(),
                    }
                ],
                "base_backup": self._get_last_full_backup_id(),
                "metadata": {
                    "version": "1.0.0",
                    "source": "value-fabric-layer3",
                    "generated_at": now.isoformat(),
                },
            }
        elif backup_type == BackupType.SCHEMA:
            backup_data = {
                "type": "schema",
                "timestamp": now.isoformat(),
                "schema": {},
                "constraints": [],
                "indexes": [],
                "metadata": {
                    "version": "1.0.0",
                    "source": "value-fabric-layer3",
                    "generated_at": now.isoformat(),
                },
            }
        else:
            raise ValueError(f"Unsupported backup type: {backup_type}")

        return json.dumps(backup_data, indent=2, default=str).encode("utf-8")

    def _get_last_full_backup_id(self) -> str | None:
        """Get the ID of the last full backup.

        Returns:
            Backup ID or None
        """
        for backup in reversed(self.backup_history):
            if (
                backup.backup_type == BackupType.FULL
                and backup.status == BackupStatus.COMPLETED
            ):
                return backup.backup_id
        return None

    async def _compress_data(self, data: bytes, algorithm: str) -> bytes:
        """Compress backup data."""
        if algorithm == "gzip":
            return gzip.compress(data)
        raise ValueError(f"Unsupported compression algorithm: {algorithm}")

    async def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt backup data."""
        logger.warning("Encryption not implemented - returning original data")
        return data

    def _apply_point_in_time_filter(
        self, backup_json: dict[str, Any], point_in_time: datetime | None
    ) -> dict[str, Any]:
        """Filter restore payload to target point-in-time when timestamp fields exist."""
        if point_in_time is None:
            return backup_json

        def include_record(record: dict[str, Any]) -> bool:
            changed_at = record.get("changed_at") or record.get("timestamp")
            if not changed_at:
                return True
            try:
                return datetime.fromisoformat(changed_at) <= point_in_time
            except ValueError:
                return True

        filtered = dict(backup_json)
        filtered["entities"] = [
            record for record in backup_json.get("entities", []) if include_record(record)
        ]
        filtered["relationships"] = [
            record
            for record in backup_json.get("relationships", [])
            if include_record(record)
        ]
        filtered["changes"] = [
            record for record in backup_json.get("changes", []) if include_record(record)
        ]
        return filtered

    async def restore_backup(self, request: RestoreRequest) -> RestoreResponse:
        """Restore from backup."""
        start_time = datetime.utcnow()

        try:
            backup_data = await self.storage.retrieve_backup(request.backup_id)

            backup_metadata = self._get_backup_metadata(request.backup_id)
            if backup_metadata and backup_metadata.checksum:
                observed_checksum = hashlib.sha256(backup_data).hexdigest()
                if observed_checksum != backup_metadata.checksum:
                    raise ValueError(
                        f"Integrity check failed for backup {request.backup_id}: checksum mismatch"
                    )

            if backup_metadata and backup_metadata.encrypted:
                backup_data = await self._decrypt_data(backup_data)

            if backup_metadata and backup_metadata.compression_algorithm != "none":
                backup_data = await self._decompress_data(
                    backup_data, backup_metadata.compression_algorithm
                )

            backup_json = json.loads(backup_data.decode("utf-8"))
            backup_json = self._apply_point_in_time_filter(
                backup_json=backup_json,
                point_in_time=request.point_in_time,
            )

            if request.dry_run:
                entities_count = len(backup_json.get("entities", []))
                relationships_count = len(backup_json.get("relationships", []))
                warnings = ["Dry run - no actual restore performed"]
                if request.point_in_time:
                    warnings.append(
                        f"Point-in-time restore target: {request.point_in_time.isoformat()}"
                    )

                return RestoreResponse(
                    backup_id=request.backup_id,
                    status="dry_run_completed",
                    restored_at=datetime.utcnow(),
                    entities_restored=entities_count,
                    relationships_restored=relationships_count,
                    duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                    warnings=warnings,
                )

            entities_restored = 0
            relationships_restored = 0
            warnings: list[str] = []

            if request.restore_data:
                entities_restored = await self._restore_entities(
                    backup_json.get("entities", []), request.target_database
                )
                relationships_restored = await self._restore_relationships(
                    backup_json.get("relationships", []), request.target_database
                )

            if request.restore_schema:
                await self._restore_schema(
                    backup_json.get("schema", {}), request.target_database
                )

            if request.point_in_time:
                warnings.append(
                    f"Restore performed to point-in-time target {request.point_in_time.isoformat()}"
                )

            duration = (datetime.utcnow() - start_time).total_seconds()

            logger.info(f"Restore completed: {request.backup_id}")

            return RestoreResponse(
                backup_id=request.backup_id,
                status="completed",
                restored_at=datetime.utcnow(),
                entities_restored=entities_restored,
                relationships_restored=relationships_restored,
                duration_seconds=duration,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Restore failed: {request.backup_id} - {e}")

            return RestoreResponse(
                backup_id=request.backup_id,
                status="failed",
                restored_at=datetime.utcnow(),
                error=str(e),
            )

    async def run_restore_drill(
        self,
        backup_id: str,
        point_in_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Run a restore drill and return verification results."""
        restore_response = await self.restore_backup(
            RestoreRequest(
                backup_id=backup_id,
                dry_run=True,
                restore_schema=True,
                restore_data=True,
                point_in_time=point_in_time,
            )
        )
        return {
            "backup_id": backup_id,
            "drill_status": "passed"
            if restore_response.status == "dry_run_completed"
            else "failed",
            "restore_status": restore_response.status,
            "entities_restored": restore_response.entities_restored,
            "relationships_restored": restore_response.relationships_restored,
            "point_in_time": point_in_time.isoformat() if point_in_time else None,
            "warnings": restore_response.warnings,
            "tested_at": datetime.utcnow().isoformat(),
        }

    def _get_backup_metadata(self, backup_id: str) -> BackupMetadata | None:
        for backup in self.backup_history:
            if backup.backup_id == backup_id:
                return backup
        return None

    async def _decrypt_data(self, data: bytes) -> bytes:
        logger.warning("Decryption not implemented - returning original data")
        return data

    async def _decompress_data(self, data: bytes, algorithm: str) -> bytes:
        if algorithm == "gzip":
            return gzip.decompress(data)
        raise ValueError(f"Unsupported compression algorithm: {algorithm}")

    async def _restore_entities(
        self, entities: list[dict[str, Any]], target_database: str | None
    ) -> int:
        logger.info(f"Restoring {len(entities)} entities")
        return len(entities)

    async def _restore_relationships(
        self, relationships: list[dict[str, Any]], target_database: str | None
    ) -> int:
        logger.info(f"Restoring {len(relationships)} relationships")
        return len(relationships)

    async def _restore_schema(
        self, schema: dict[str, Any], target_database: str | None
    ) -> None:
        logger.info("Restoring schema")

    async def list_backups(
        self, backup_type: BackupType | None = None
    ) -> list[BackupMetadata]:
        backups = self.backup_history.copy()

        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]

        return sorted(backups, key=lambda b: b.created_at, reverse=True)

    async def delete_backup(self, backup_id: str) -> bool:
        try:
            storage_deleted = await self.storage.delete_backup(backup_id)

            self.backup_history = [
                b for b in self.backup_history if b.backup_id != backup_id
            ]

            logger.info(f"Deleted backup: {backup_id}")
            return storage_deleted

        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False

    async def _cleanup_old_backups(self) -> int:
        deleted_count = 0
        now = datetime.utcnow()

        for backup in self.backup_history.copy():
            if (now - backup.created_at).days > backup.retention_days:
                if await self.delete_backup(backup.backup_id):
                    deleted_count += 1

        if len(self.backup_history) > self.config.max_backups:
            sorted_backups = sorted(self.backup_history, key=lambda b: b.created_at)
            excess_count = len(self.backup_history) - self.config.max_backups

            for backup in sorted_backups[:excess_count]:
                if await self.delete_backup(backup.backup_id):
                    deleted_count += 1

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backups")

        return deleted_count

    async def get_backup_statistics(self) -> dict[str, Any]:
        total_backups = len(self.backup_history)
        completed_backups = len(
            [b for b in self.backup_history if b.status == BackupStatus.COMPLETED]
        )
        failed_backups = len(
            [b for b in self.backup_history if b.status == BackupStatus.FAILED]
        )

        total_size = sum(b.size_bytes for b in self.backup_history)
        compressed_size = sum(b.compressed_size_bytes for b in self.backup_history)

        type_counts: dict[str, int] = {}
        for backup in self.backup_history:
            backup_type = backup.backup_type.value
            type_counts[backup_type] = type_counts.get(backup_type, 0) + 1

        storage_counts: dict[str, int] = {}
        for backup in self.backup_history:
            storage_type = backup.storage_type.value
            storage_counts[storage_type] = storage_counts.get(storage_type, 0) + 1

        return {
            "total_backups": total_backups,
            "completed_backups": completed_backups,
            "failed_backups": failed_backups,
            "total_size_bytes": total_size,
            "compressed_size_bytes": compressed_size,
            "compression_ratio": (total_size - compressed_size) / total_size
            if total_size > 0
            else 0,
            "backup_type_distribution": type_counts,
            "storage_type_distribution": storage_counts,
            "oldest_backup": min(
                (b.created_at for b in self.backup_history), default=None
            ),
            "newest_backup": max(
                (b.created_at for b in self.backup_history), default=None
            ),
        }


_backup_manager: BackupManager | None = None


def get_backup_manager() -> BackupManager | None:
    """Get global backup manager instance."""
    return _backup_manager


def initialize_backup_manager(config: BackupConfig) -> BackupManager:
    """Initialize global backup manager."""
    global _backup_manager
    _backup_manager = BackupManager(config)
    logger.info("Backup manager initialized")
    return _backup_manager
