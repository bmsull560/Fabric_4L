"""CLI configuration management."""

from __future__ import annotations

from pathlib import Path

import toml
import typer
from rich import print as rich_print

app = typer.Typer(help="Manage CLI configuration")

CONFIG_DIR = Path.home() / ".config" / "valuefabric"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_PROFILE = "default"


def _load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    return toml.load(CONFIG_FILE)


def _save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        toml.dump(config, f)


def get_active_profile() -> str:
    config = _load_config()
    return config.get("active_profile", DEFAULT_PROFILE)


def get_profile_config(profile: str | None = None) -> dict:
    config = _load_config()
    profile = profile or config.get("active_profile", DEFAULT_PROFILE)
    return config.get("profiles", {}).get(profile, {})


@app.command("set-url")
def set_url(
    url: str,
    profile: str = typer.Option("default", "--profile", "-p", help="Profile name"),
) -> None:
    """Set the base URL for a profile."""
    config = _load_config()
    config.setdefault("profiles", {}).setdefault(profile, {})["base_url"] = url
    _save_config(config)
    rich_print(f"[green]Base URL set for profile '{profile}': {url}[/green]")


@app.command("set-api-key")
def set_api_key(
    api_key: str,
    profile: str = typer.Option("default", "--profile", "-p", help="Profile name"),
) -> None:
    """Set the API key for a profile."""
    config = _load_config()
    config.setdefault("profiles", {}).setdefault(profile, {})["api_key"] = api_key
    _save_config(config)
    rich_print(f"[green]API key set for profile '{profile}'.[/green]")


@app.command("use-profile")
def use_profile(
    profile: str,
) -> None:
    """Switch the active profile."""
    config = _load_config()
    config["active_profile"] = profile
    _save_config(config)
    rich_print(f"[green]Active profile set to '{profile}'.[/green]")


@app.command("show")
def show_config() -> None:
    """Display the current configuration."""
    config = _load_config()
    active = config.get("active_profile", DEFAULT_PROFILE)
    rich_print(f"[bold]Active profile:[/bold] {active}")
    profiles = config.get("profiles", {})
    for name, values in profiles.items():
        marker = " *" if name == active else ""
        rich_print(f"\n[bold]{name}{marker}[/bold]")
        for key, value in values.items():
            display = value if key != "api_key" else "*" * 8
            rich_print(f"  {key}: {display}")
