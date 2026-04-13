"""Health check CLI command."""

from __future__ import annotations

import typer

from ._utils import get_client, print_object


def health(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Check API health."""
    client = get_client()
    result = client.health()
    print_object(result.model_dump(mode="json"), json_output=json_output)
