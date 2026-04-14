"""Secret management utilities for Value Fabric Platform.

Provides secret rotation detection and hot-reload capabilities
for Kubernetes secrets mounted as files or injected via environment.
"""

from .watcher import SecretWatcher, watch_secret_file
from .reload import register_secret_reload_handler, reload_on_secret_change

__all__ = [
    "SecretWatcher",
    "watch_secret_file",
    "register_secret_reload_handler",
    "reload_on_secret_change",
]
