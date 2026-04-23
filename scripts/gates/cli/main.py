#!/usr/bin/env python3
"""CLI client for gate daemon."""

import asyncio
import json
import sys
from pathlib import Path

import click
import httpx


GATE_DAEMON_URL = "http://localhost:8888"


@click.group()
@click.option("--url", default=GATE_DAEMON_URL, help="Gate daemon URL")
@click.pass_context
def cli(ctx, url):
    """Gate CLI - Unified release gate client."""
    ctx.ensure_object(dict)
    ctx.obj["url"] = url


@cli.command()
@click.pass_context
def health(ctx):
    """Check daemon health."""
    url = ctx.obj["url"]
    response = httpx.get(f"{url}/v1/health")
    click.echo(json.dumps(response.json(), indent=2))


@cli.command()
@click.pass_context
def list(ctx):
    """List all registered gates."""
    url = ctx.obj["url"]
    response = httpx.get(f"{url}/v1/gates")
    data = response.json()
    
    click.echo("Registered Gates:")
    click.echo("-" * 60)
    for gate in data.get("gates", []):
        click.echo(f"  {gate['gate_id']:<15} [{gate['severity']:^8}]")
        for artifact in gate.get("artifacts", []):
            click.echo(f"    → {artifact}")


@cli.command()
@click.argument("gate_id")
@click.option("--profile", default="pr-fast", help="Execution profile")
@click.option("--trace-id", help="Trace ID for observability")
@click.pass_context
def run(ctx, gate_id, profile, trace_id):
    """Execute a gate."""
    url = ctx.obj["url"]
    
    payload = {"profile": profile}
    if trace_id:
        payload["trace_id"] = trace_id
    
    click.echo(f"Executing gate: {gate_id} (profile: {profile})")
    
    response = httpx.post(
        f"{url}/v1/gates/{gate_id}/execute",
        json=payload,
        timeout=300.0,
    )
    
    if response.status_code != 200:
        click.echo(f"Error: {response.status_code}", err=True)
        click.echo(response.text, err=True)
        sys.exit(1)
    
    data = response.json()
    click.echo(f"Execution ID: {data['execution_id']}")
    click.echo(f"Status: {data['status']}")
    
    # Poll for results
    execution_id = data["execution_id"]
    click.echo("Waiting for completion...")
    
    while True:
        status_resp = httpx.get(f"{url}/v1/gates/{gate_id}/status/{execution_id}")
        status_data = status_resp.json()
        
        if status_data["status"] == "completed":
            click.echo("\nResults:")
            for result in status_data["results"]:
                symbol = "✓" if result["result"] == "pass" else "✗"
                click.echo(f"  {symbol} {result['name']}: {result['result']}")
                if result.get("message"):
                    click.echo(f"    {result['message']}")
            
            # Show artifacts
            if status_data["artifacts"]:
                click.echo(f"\nArtifacts: {len(status_data['artifacts'])}")
                for artifact in status_data["artifacts"]:
                    click.echo(f"  → {artifact['path']}")
            
            # Exit code based on results
            failures = [r for r in status_data["results"] if r["result"] in ("fail", "error")]
            if failures:
                sys.exit(1)
            break
        
        asyncio.sleep(1)


@cli.command()
@click.option("--profile", default="pr-fast", help="Execution profile")
@click.option("--block-on-missing/--no-block-on-missing", default=True)
@click.pass_context
def evaluate(ctx, profile, block_on_missing):
    """Evaluate all gates for release."""
    url = ctx.obj["url"]
    
    payload = {
        "profile": profile,
        "block_on_missing": block_on_missing,
    }
    
    click.echo("Evaluating release policy...")
    
    response = httpx.post(
        f"{url}/v1/evaluate",
        json=payload,
        timeout=60.0,
    )
    
    data = response.json()
    
    click.echo(f"\nResult: {data['result'].upper()}")
    click.echo(f"Blocks Release: {data['blocks_release']}")
    click.echo(f"Gates Evaluated: {data['gates_evaluated']}")
    
    click.echo("\nGate Results:")
    click.echo("-" * 60)
    for gate in data["gate_results"]:
        symbol = "✓" if not gate["blocks_release"] else "✗"
        status = gate["result"].upper()
        click.echo(f"  {symbol} {gate['gate_id']:<15} [{status}]")
        if gate.get("reason"):
            click.echo(f"      {gate['reason']}")
    
    if data["blocks_release"]:
        sys.exit(1)


@cli.command()
@click.option("--config", type=click.Path(), help="Daemon config file")
@click.option("--port", default=8888, help="Daemon port")
@click.option("--host", default="0.0.0.0", help="Daemon host")
def daemon(config, port, host):
    """Start the gate daemon."""
    import uvicorn
    from gated.main import app
    
    click.echo(f"Starting gate daemon on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    cli()
