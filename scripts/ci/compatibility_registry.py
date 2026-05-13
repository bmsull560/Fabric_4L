#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "docs/governance/compatibility-debt-registry.md"

TABLE_ROW_RE = re.compile(
    r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|$"
)
ISO_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


@dataclass(frozen=True)
class RegistryEntry:
    shim_id: str
    path: str
    shim_type: str
    owner: str
    reason: str
    target_removal_date: str
    review_metadata: str
    removal_ticket: str
    line_number: int

    @property
    def normalized_path(self) -> str:
        return self.path.strip().strip("/")

    @property
    def target_removal_date_obj(self) -> dt.date:
        return dt.date.fromisoformat(self.target_removal_date)


def parse_registry(path: Path = REGISTRY_PATH) -> list[RegistryEntry]:
    entries: list[RegistryEntry] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = TABLE_ROW_RE.match(line.strip())
        if not match:
            continue
        entries.append(
            RegistryEntry(
                shim_id=match.group(1).strip(),
                path=match.group(2).strip(),
                shim_type=match.group(3).strip(),
                owner=match.group(4).strip(),
                reason=match.group(5).strip(),
                target_removal_date=match.group(6).strip(),
                review_metadata=match.group(7).strip(),
                removal_ticket=match.group(8).strip(),
                line_number=line_number,
            )
        )
    return entries


def path_is_covered(path: str, entries: list[RegistryEntry]) -> bool:
    normalized = path.replace("\\", "/").strip("/")
    for entry in entries:
        candidate = entry.normalized_path
        if not candidate:
            continue
        if normalized == candidate:
            return True
        if candidate.endswith("/") and normalized.startswith(candidate):
            return True
        if normalized.startswith(candidate.rstrip("/") + "/"):
            return True
    return False


def has_platform_architecture_approval(review_metadata: str) -> bool:
    return "platform architecture" in review_metadata.lower() and bool(ISO_DATE_RE.search(review_metadata))
