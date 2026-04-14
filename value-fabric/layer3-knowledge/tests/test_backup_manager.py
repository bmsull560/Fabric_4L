"""Tests for backup manager storage, retention, integrity, and restore drills."""

import hashlib
import json
from datetime import datetime, timedelta

import pytest

from src.backup.backup_manager import (
    BackupConfig,
    BackupManager,
    BackupMetadata,
    BackupRequest,
    BackupStatus,
    BackupType,
    RestoreRequest,
    StorageType,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("storage_type", "config_field", "bucket_key", "bucket_value"),
    [
        (StorageType.LOCAL, None, None, None),
        (StorageType.S3, "s3_config", "bucket", "unit-test-bucket"),
        (StorageType.GCS, "gcs_config", "bucket", "unit-test-bucket"),
        (StorageType.AZURE, "azure_config", "container", "unit-test-container"),
        (StorageType.FTP, "ftp_config", "site", "unit-test-site"),
    ],
)
async def test_storage_backends_store_list_retrieve_delete(
    tmp_path,
    storage_type,
    config_field,
    bucket_key,
    bucket_value,
):
    """All storage backends must support CRUD backup operations."""
    kwargs = {
        "backup_directory": str(tmp_path / "backups"),
        "storage_type": storage_type,
        "auto_cleanup": False,
    }
    if config_field:
        kwargs[config_field] = {
            "root_directory": str(tmp_path / storage_type.value),
            bucket_key: bucket_value,
        }

    manager = BackupManager(BackupConfig(**kwargs))
    backup_id = "backup_storage_test"
    raw_data = b"backup-payload"

    stored_path = await manager.storage.store_backup(backup_id, raw_data)
    assert stored_path

    backup_ids = await manager.storage.list_backups()
    assert backup_id in backup_ids

    loaded_data = await manager.storage.retrieve_backup(backup_id)
    assert loaded_data == raw_data

    info = await manager.storage.get_backup_info(backup_id)
    assert info["backup_id"] == backup_id
    assert info["size_bytes"] == len(raw_data)
    assert info["checksum"]

    deleted = await manager.storage.delete_backup(backup_id)
    assert deleted is True
    assert backup_id not in await manager.storage.list_backups()


@pytest.mark.asyncio
async def test_backup_creation_listing_restore_and_delete(tmp_path):
    """Backup lifecycle should succeed end to end."""
    manager = BackupManager(
        BackupConfig(
            backup_directory=str(tmp_path / "backups"),
            storage_type=StorageType.LOCAL,
            auto_cleanup=False,
        )
    )

    backup_response = await manager.create_backup(BackupRequest(backup_type=BackupType.FULL))

    assert backup_response.status == BackupStatus.COMPLETED
    assert backup_response.backup_id

    listed_backups = await manager.list_backups()
    assert len(listed_backups) == 1
    assert listed_backups[0].backup_id == backup_response.backup_id

    restore_response = await manager.restore_backup(
        RestoreRequest(backup_id=backup_response.backup_id)
    )
    assert restore_response.status == "completed"
    assert restore_response.entities_restored >= 1

    deleted = await manager.delete_backup(backup_response.backup_id)
    assert deleted is True
    assert await manager.list_backups() == []


@pytest.mark.asyncio
async def test_backup_integrity_check_fails_when_payload_corrupted(tmp_path):
    """Restore must fail if stored bytes do not match recorded checksum."""
    manager = BackupManager(
        BackupConfig(
            backup_directory=str(tmp_path / "backups"),
            storage_type=StorageType.LOCAL,
            auto_cleanup=False,
        )
    )

    backup_response = await manager.create_backup(BackupRequest(backup_type=BackupType.FULL))
    backup_file = tmp_path / "backups" / f"{backup_response.backup_id}.backup"
    backup_file.write_bytes(b"corrupted")

    restore_response = await manager.restore_backup(
        RestoreRequest(backup_id=backup_response.backup_id)
    )
    assert restore_response.status == "failed"
    assert restore_response.error is not None
    assert "checksum" in restore_response.error.lower()


@pytest.mark.asyncio
async def test_retention_policy_enforced_by_age_and_count(tmp_path):
    """Cleanup should delete backups older than retention and over max_backups."""
    manager = BackupManager(
        BackupConfig(
            backup_directory=str(tmp_path / "backups"),
            storage_type=StorageType.LOCAL,
            auto_cleanup=False,
            max_backups=1,
        )
    )

    now = datetime.utcnow()
    old = BackupMetadata(
        backup_id="old_backup",
        backup_type=BackupType.FULL,
        created_at=now - timedelta(days=10),
        status=BackupStatus.COMPLETED,
        retention_days=1,
        storage_type=StorageType.LOCAL,
    )
    newer = BackupMetadata(
        backup_id="newer_backup",
        backup_type=BackupType.FULL,
        created_at=now - timedelta(days=1),
        status=BackupStatus.COMPLETED,
        retention_days=30,
        storage_type=StorageType.LOCAL,
    )
    newest = BackupMetadata(
        backup_id="newest_backup",
        backup_type=BackupType.FULL,
        created_at=now,
        status=BackupStatus.COMPLETED,
        retention_days=30,
        storage_type=StorageType.LOCAL,
    )

    for backup in (old, newer, newest):
        await manager.storage.store_backup(backup.backup_id, b"payload")
        backup.file_path = str(tmp_path / "backups" / f"{backup.backup_id}.backup")

    manager.backup_history = [old, newer, newest]

    deleted_count = await manager._cleanup_old_backups()

    assert deleted_count == 2
    remaining_ids = {backup.backup_id for backup in manager.backup_history}
    assert remaining_ids == {"newest_backup"}


@pytest.mark.asyncio
async def test_restore_drill_supports_point_in_time(tmp_path):
    """Restore drill should run in dry-run mode and support PITR filtering."""
    manager = BackupManager(
        BackupConfig(
            backup_directory=str(tmp_path / "backups"),
            storage_type=StorageType.LOCAL,
            auto_cleanup=False,
            compression_enabled=False,
        )
    )

    backup_response = await manager.create_backup(BackupRequest(backup_type=BackupType.FULL))
    backup_id = backup_response.backup_id
    backup_file = tmp_path / "backups" / f"{backup_id}.backup"

    payload = {
        "type": "full",
        "timestamp": datetime.utcnow().isoformat(),
        "entities": [
            {"id": "e1", "changed_at": "2024-01-01T00:00:00"},
            {"id": "e2", "changed_at": "2025-01-01T00:00:00"},
        ],
        "relationships": [
            {
                "source": "e1",
                "target": "e2",
                "type": "REL",
                "changed_at": "2025-01-01T00:00:00",
            }
        ],
        "schema": {},
    }
    raw = json.dumps(payload).encode("utf-8")
    backup_file.write_bytes(raw)
    metadata_file = tmp_path / "backups" / f"{backup_id}.metadata.json"
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    metadata["checksum"] = hashlib.sha256(raw).hexdigest()
    metadata_file.write_text(json.dumps(metadata), encoding="utf-8")
    manager.backup_history[0].checksum = metadata["checksum"]

    drill_response = await manager.run_restore_drill(
        backup_id=backup_id,
        point_in_time=datetime.fromisoformat("2024-06-01T00:00:00"),
    )

    assert drill_response["drill_status"] == "passed"
    assert drill_response["restore_status"] == "dry_run_completed"
    assert drill_response["entities_restored"] == 1
