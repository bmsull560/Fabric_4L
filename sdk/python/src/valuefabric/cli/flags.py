"""Feature flags CLI commands."""

from __future__ import annotations

import typer

from ._utils import get_client, print_object, print_table

app = typer.Typer(help="Feature flags")


@app.command("list")
def list_flags(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    limit: int = typer.Option(100, "--limit", help="Max results"),
    offset: int = typer.Option(0, "--offset", help="Result offset"),
) -> None:
    """List feature flags for the current tenant."""
    client = get_client()
    flags = client.list_feature_flags(limit=limit, offset=offset)
    rows = [f.model_dump(mode="json") for f in flags]
    print_table(
        rows,
        columns=["flag_key", "enabled", "rollout_percentage", "description"],
        json_output=json_output,
    )


@app.command("set")
def set_flag(
    key: str,
    enabled: bool = typer.Option(..., "--enabled/--disabled", help="Enable or disable the flag"),
    rollout_percentage: int = typer.Option(
        100, "--rollout", "-r", help="Rollout percentage (0-100)"
    ),
    description: str | None = typer.Option(None, "--description", "-d"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Create or update a feature flag."""
    client = get_client()
    flag = client.set_feature_flag(
        key,
        enabled,
        rollout_percentage=rollout_percentage,
        description=description,
    )
    print_object(flag.model_dump(mode="json"), json_output=json_output)
