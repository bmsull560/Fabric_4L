"""Tests for secret watcher and hot-reload functionality."""

from pathlib import Path


from .watcher import SecretWatcher, watch_secret_file


class TestSecretWatcher:
    """Tests for SecretWatcher class."""

    def test_watch_file_detects_changes(self, tmp_path: Path):
        """Watcher should detect when a secret file changes."""
        secret_file = tmp_path / "api-key"
        secret_file.write_text("initial-key")

        changes = []

        def on_change(content: str) -> None:
            changes.append(content)

        watcher = SecretWatcher(poll_interval=1)
        watcher.watch_file(secret_file, on_change)

        # Initial check should not trigger callback (no change yet)
        watcher.check_now()
        assert len(changes) == 0

        # Modify the file
        secret_file.write_text("rotated-key")

        # Check should detect change
        watcher.check_now()
        assert len(changes) == 1
        assert changes[0] == "rotated-key"

    def test_watch_file_not_found(self, tmp_path: Path):
        """Watcher should handle missing files gracefully."""
        missing_file = tmp_path / "missing-secret"

        changes = []

        def on_change(content: str) -> None:
            changes.append(content)

        watcher = SecretWatcher()
        result = watcher.watch_file(missing_file, on_change)

        # Should return False for missing file
        assert result is False

        # Should still register for later creation
        assert missing_file in watcher._callbacks

    def test_multiple_callbacks_per_file(self, tmp_path: Path):
        """Multiple callbacks should all be triggered."""
        secret_file = tmp_path / "multi-secret"
        secret_file.write_text("secret-value")

        changes1 = []
        changes2 = []

        def on_change1(content: str) -> None:
            changes1.append(content)

        def on_change2(content: str) -> None:
            changes2.append(content)

        watcher = SecretWatcher()
        watcher.watch_file(secret_file, on_change1)
        watcher.watch_file(secret_file, on_change2)

        # Modify file
        secret_file.write_text("new-value")
        watcher.check_now()

        assert len(changes1) == 1
        assert len(changes2) == 1
        assert changes1[0] == changes2[0] == "new-value"

    def test_no_change_no_callback(self, tmp_path: Path):
        """Callback should not fire if file hasn't changed."""
        secret_file = tmp_path / "static-secret"
        secret_file.write_text("static-value")

        changes = []

        def on_change(content: str) -> None:
            changes.append(content)

        watcher = SecretWatcher()
        watcher.watch_file(secret_file, on_change)

        # Check multiple times without changing file
        watcher.check_now()
        watcher.check_now()
        watcher.check_now()

        assert len(changes) == 0


class TestWatchSecretFile:
    """Tests for watch_secret_file convenience function."""

    def test_returns_watcher(self, tmp_path: Path):
        """Function should return configured watcher."""
        secret_file = tmp_path / "test-secret"
        secret_file.write_text("test-value")

        watcher = watch_secret_file(
            str(secret_file),
            lambda x: None,
            start_immediately=False,
        )

        assert isinstance(watcher, SecretWatcher)
        assert watcher.poll_interval == 30  # default

    def test_custom_poll_interval(self, tmp_path: Path):
        """Custom poll interval should be respected."""
        secret_file = tmp_path / "test-secret"
        secret_file.write_text("test-value")

        watcher = watch_secret_file(
            str(secret_file),
            lambda x: None,
            poll_interval=60,
            start_immediately=False,
        )

        assert watcher.poll_interval == 60
