"""URL path normalization for Prometheus metric labels.

Prevents unbounded metric cardinality by collapsing high-entropy path segments
(UUIDs, numeric IDs, hex hashes) to placeholders before they become label
values on `http_requests_total` / `http_request_duration_seconds`.
"""

from __future__ import annotations

import re
from collections.abc import Mapping


class PathNormalizer:
    """Normalize URL paths to low-cardinality route templates.

    Strategy:
      1. Match against caller-provided ``known_routes`` (exact-match first).
      2. Collapse UUIDs, long hex hashes, and numeric IDs to ``{id}`` / ``{hash}``.
      3. Cap segment depth to ``max_segments`` to bound cardinality of unknown paths.

    Args:
        known_routes: Optional mapping of literal path → canonical template.
            Used for known service routes (e.g. ``/api/v1/truths/{truth_id}`` →
            ``/api/v1/truths/{id}``). Lookup is exact-match after trailing-slash
            strip.
        max_segments: Maximum number of segments retained for unknown paths.
            Anything deeper is truncated and suffixed with ``/{...}``.
    """

    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    HASH_PATTERN = re.compile(r"^[0-9a-f]{32,}$", re.IGNORECASE)
    NUMERIC_PATTERN = re.compile(r"^\d+$")

    def __init__(
        self,
        known_routes: Mapping[str, str] | None = None,
        max_segments: int = 6,
    ) -> None:
        self._known_routes: dict[str, str] = dict(known_routes or {})
        self._max_segments = max_segments

    def normalize(self, path: str) -> str:
        if not path or path == "/":
            return "/"

        path = path.rstrip("/") or "/"
        if path in self._known_routes:
            return self._known_routes[path]

        segments = path.split("/")
        normalized: list[str] = []

        for segment in segments:
            if not segment:
                continue

            if self.UUID_PATTERN.match(segment):
                normalized.append("{id}")
            elif self.HASH_PATTERN.match(segment):
                normalized.append("{hash}")
            elif self.NUMERIC_PATTERN.match(segment):
                # Preserve API version segments like "v1" — treat numeric only
                # as ID when previous token isn't a version letter.
                if segment == "1" and normalized and normalized[-1] == "v":
                    normalized.append(segment)
                else:
                    normalized.append("{id}")
            else:
                normalized.append(segment)

        if len(normalized) > self._max_segments:
            return "/" + "/".join(normalized[: self._max_segments]) + "/{...}"
        return "/" + "/".join(normalized)
