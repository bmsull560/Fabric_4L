"""User CLI commands."""

from __future__ import annotations

import typer

from ._utils import get_client, print_object, print_table

app = typer.Typer(help="User management")


@app.command("list")
def list_users(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    limit: int = typer.Option(100, "--limit", help="Max results"),
    offset: int = typer.Option(0, "--offset", help="Result offset"),
) -> None:
    """List users in the current tenant."""
    client = get_client()
    users = client.list_users(limit=limit, offset=offset)
    rows = [u.model_dump(mode="json") for u in users]
    print_table(
        rows,
        columns=["id", "email", "display_name", "role", "status", "created_at"],
        json_output=json_output,
    )


@app.command("invite")
def invite_user(
    email: str,
    role: str = typer.Option("analyst", "--role", "-r", help="Role to assign"),
    display_name: str | None = typer.Option(None, "--display-name", help="Display name"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Invite a user to the current tenant."""
    client = get_client()
    user = client.invite_user(email, role, display_name=display_name)
    print_object(user.model_dump(mode="json"), json_output=json_output)
