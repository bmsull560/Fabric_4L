"""Secret management utilities for Value Fabric Platform.

Provides secret rotation detection and hot-reload capabilities
for Kubernetes secrets mounted as files or injected via environment,
and Infisical-based centralised secret loading.
"""

from .watcher import SecretWatcher, watch_secret_file
from .reload import register_secret_reload_handler, reload_on_secret_change
from .infisical import load_infisical_secrets
from .tenant_secrets import TenantSecretsService, ProvisioningResult

__all__ = [
    "SecretWatcher",
    "watch_secret_file",
    "register_secret_reload_handler",
    "reload_on_secret_change",
    "load_infisical_secrets",
    "TenantSecretsService",
    "ProvisioningResult",
]
