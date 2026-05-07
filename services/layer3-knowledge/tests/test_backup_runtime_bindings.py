from value_fabric.layer3.backup.backup_manager import BackupConfig, BackupManager, LocalStorage


def test_backup_manager_uses_concrete_storage(tmp_path):
    config = BackupConfig(backup_directory=str(tmp_path))
    manager = BackupManager(config)
    assert isinstance(manager.storage, LocalStorage)
