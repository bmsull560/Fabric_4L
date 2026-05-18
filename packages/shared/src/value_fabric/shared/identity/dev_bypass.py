"""Development auth bypass — permanently disabled.

``DevAuthBypassMiddleware`` has been removed (F-23). The class injected a
synthetic super_admin RequestContext on every request with no authentication.
Dead security-sensitive code must not exist in the codebase even if nominally
disabled, because accidental direct instantiation bypasses all guards.

``maybe_install_dev_bypass`` is retained as a no-op compatibility shim so
existing ``main.py`` call sites do not need to be updated immediately.
"""

from __future__ import annotations

import logging

from starlette.types import ASGIApp

from value_fabric.shared.identity.auth_mode import is_dev_bypass_enabled

logger = logging.getLogger(__name__)


def maybe_install_dev_bypass(app: ASGIApp) -> bool:  # noqa: ARG001
    """No-op compatibility shim — dev auth bypass is permanently disabled.

    If ``DEV_AUTH_BYPASS`` is set in the environment, a CRITICAL log is emitted
    to alert operators that the variable has no effect and should be removed.
    """
    if is_dev_bypass_enabled():
        logger.critical(
            "SECURITY: DEV_AUTH_BYPASS is set but dev auth bypass has been "
            "permanently removed from the platform. "
            "Unset DEV_AUTH_BYPASS and ALLOW_DEV_AUTH_BYPASS immediately."
        )
    return False
