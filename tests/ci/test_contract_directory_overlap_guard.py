from pathlib import Path


def test_no_overlapping_contract_modules_between_singular_and_plural_directories() -> None:
    """Prevent duplicate module basenames across tests/contract and tests/contracts."""
    singular = Path("tests/contract")
    plural = Path("tests/contracts")

    if not singular.exists() or not plural.exists():
        return

    singular_names = {p.name for p in singular.rglob("test_*.py")}
    plural_names = {p.name for p in plural.rglob("test_*.py")}
    overlap = sorted(singular_names & plural_names)

    assert not overlap, (
        "Duplicate contract module basenames found across tests/contract and "
        f"tests/contracts: {', '.join(overlap)}. Consolidate into tests/contract/."
    )
