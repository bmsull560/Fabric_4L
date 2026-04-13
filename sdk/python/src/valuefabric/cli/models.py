"""Model registry CLI commands."""

from __future__ import annotations

import typer

from ._utils import get_client, print_object, print_table

app = typer.Typer(help="Model registry")


@app.command("list")
def list_models(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    stage: str | None = typer.Option(None, "--stage", help="Filter by stage"),
) -> None:
    """List registered model versions."""
    client = get_client()
    models = client.list_models(stage=stage)
    rows = [m.model_dump(mode="json") for m in models]
    print_table(
        rows,
        columns=["id", "provider", "model_name", "model_version", "stage", "created_at"],
        json_output=json_output,
    )


@app.command("promote")
def promote_model(
    model_id: str,
    to_stage: str = typer.Option(..., "--to", help="Target stage"),
    reason: str | None = typer.Option(None, "--reason", help="Promotion reason"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Promote a model version to a new stage."""
    client = get_client()
    model = client.promote_model(model_id, to_stage, reason=reason)
    print_object(model.model_dump(mode="json"), json_output=json_output)
