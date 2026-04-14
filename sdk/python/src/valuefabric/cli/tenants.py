"""Tenant CLI commands."""

from __future__ import annotations

import typer

from ._utils import get_client, print_object, print_table

app = typer.Typer(help="Tenant management")


@app.command("list")
def list_tenants(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    limit: int = typer.Option(100, "--limit", help="Max results"),
    offset: int = typer.Option(0, "--offset", help="Result offset"),
) -> None:
    """List tenants."""
    client = get_client()
    tenants = client.list_tenants(limit=limit, offset=offset)
    rows = [t.model_dump(mode="json") for t in tenants]
    print_table(
        rows,
        columns=["id", "name", "slug", "status", "created_at"],
        json_output=json_output,
    )


@app.command("get")
def get_tenant(
    tenant_id: str,
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Get a tenant by ID."""
    client = get_client()
    tenant = client.get_tenant(tenant_id)
    print_object(tenant.model_dump(mode="json"), json_output=json_output)
