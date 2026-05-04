"""Secret file watcher for detecting Kubernetes secret rotations.

Monitors secret files mounted from Kubernetes secrets and triggers
callbacks when secrets are updated (rotation detection).
"""

import hashlib
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class SecretFile:
    """Represents a watched secret file with its metadata."""

    path: Path
    last_hash: str
    last_modified: float


class SecretWatcher:
    """Watches secret files for changes and triggers callbacks.

    Kubernetes updates secrets by updating files in mounted volumes.
    This watcher detects changes by comparing file hashes.

    Usage:
        watcher = SecretWatcher(poll_interval=30)
        watcher.watch_file("/secrets/api-key", on_api_key_change)
        watcher.start()
    """

    def __init__(self, poll_interval: int = 30):
        """Initialize the secret watcher.

        Args:
            poll_interval: Seconds between file checks (default: 30)
        """
        self.poll_interval = poll_interval
        self._watched_files: dict[Path, SecretFile] = {}
        self._callbacks: dict[Path, list[Callable[[str], None]]] = {}
        self._running = False
        self._last_check: float = 0

    def watch_file(
        self,
        path: str | Path,
        callback: Callable[[str], None],
        *,
        read_on_register: bool = True,
    ) -> bool:
        """Register a file to watch and its change callback.

        Args:
            path: Path to the secret file
            callback: Function to call when secret changes, receives new content
            read_on_register: Whether to read initial hash immediately

        Returns:
            True if file exists and was registered, False otherwise
        """
        file_path = Path(path)

        if not file_path.exists():
            logger.warning(f"Secret file not found, will watch if created: {file_path}")
            # Still register so we can detect if it's created later
            self._callbacks[file_path] = [callback]
            self._watched_files[file_path] = SecretFile(
                path=file_path, last_hash="", last_modified=0
            )
            return False

        if read_on_register:
            try:
                content = file_path.read_text()
                file_hash = hashlib.sha256(content.encode()).hexdigest()
                mtime = file_path.stat().st_mtime
            except Exception as e:
                logger.error(f"Failed to read secret file {file_path}: {e}")
                return False
        else:
            file_hash = ""
            mtime = 0

        self._watched_files[file_path] = SecretFile(
            path=file_path, last_hash=file_hash, last_modified=mtime
        )

        if file_path not in self._callbacks:
            self._callbacks[file_path] = []
        self._callbacks[file_path].append(callback)

        logger.info(f"Watching secret file: {file_path}")
        return True

    def check_now(self) -> list[tuple[Path, str]]:
        """Check all watched files immediately for changes.

        Returns:
            List of (path, new_content) tuples for changed files
        """
        changed = []

        for file_path, secret_file in list(self._watched_files.items()):
            try:
                if not file_path.exists():
                    # File was deleted - skip but keep watching
                    continue

                current_mtime = file_path.stat().st_mtime

                # Quick check: if mtime hasn't changed, skip hash calculation
                if current_mtime == secret_file.last_modified and secret_file.last_hash:
                    continue

                # Read and hash content
                content = file_path.read_text()
                current_hash = hashlib.sha256(content.encode()).hexdigest()

                if current_hash != secret_file.last_hash:
                    logger.info(f"Secret file changed: {file_path}")
                    secret_file.last_hash = current_hash
                    secret_file.last_modified = current_mtime
                    changed.append((file_path, content))

                    # Trigger callbacks
                    for callback in self._callbacks.get(file_path, []):
                        try:
                            callback(content)
                        except Exception as e:
                            logger.error(f"Secret change callback failed for {file_path}: {e}")

            except Exception as e:
                logger.error(f"Error checking secret file {file_path}: {e}")

        return changed

    async def run_async(self) -> None:
        """Run the watcher loop asynchronously.

        This is a coroutine that should be run with asyncio.create_task().
        """
        import asyncio

        self._running = True
        logger.info(f"Secret watcher started (poll_interval={self.poll_interval}s)")

        while self._running:
            self.check_now()
            self._last_check = time.time()

            try:
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break

        logger.info("Secret watcher stopped")

    def stop(self) -> None:
        """Stop the watcher loop."""
        self._running = False


def watch_secret_file(
    path: str,
    callback: Callable[[str], None],
    *,
    poll_interval: int = 30,
    start_immediately: bool = True,
) -> SecretWatcher:
    """Convenience function to create and start watching a single file.

    Args:
        path: Path to the secret file
        callback: Function to call when secret changes
        poll_interval: Seconds between checks
        start_immediately: Whether to start the watcher immediately

    Returns:
        Configured SecretWatcher instance
    """
    watcher = SecretWatcher(poll_interval=poll_interval)
    watcher.watch_file(path, callback)

    if start_immediately:
        import asyncio

        asyncio.create_task(watcher.run_async())

    return watcher
