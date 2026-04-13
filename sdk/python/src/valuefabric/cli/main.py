"""Entrypoint for the ``vf`` CLI."""

from __future__ import annotations

import typer

from .api_keys import app as api_keys_app
from .config import app as config_app
from .flags import app as flags_app
from .health import app as health_app
from .models import app as models_app
from .tenants import app as tenants_app
from .users import app as users_app
from .workflows import app as workflows_app

app = typer.Typer(name="vf", help="Value Fabric SDK CLI")

app.add_typer(config_app, name="config", help="Manage CLI configuration")
app.add_typer(tenants_app, name="tenants", help="Tenant management")
app.add_typer(users_app, name="users", help="User management")
app.add_typer(api_keys_app, name="api-keys", help="API key management")
app.add_typer(workflows_app, name="workflows", help="Workflow management")
app.add_typer(models_app, name="models", help="Model registry")
app.add_typer(flags_app, name="feature-flags", help="Feature flags")
app.add_typer(health_app, name="health", help="Health checks")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
