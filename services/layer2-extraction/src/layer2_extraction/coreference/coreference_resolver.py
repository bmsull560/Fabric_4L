"""Coreference resolver for Layer 2 extraction."""

from __future__ import annotations

from typing import Any


class CoreferenceResolver:
    """Resolve coreferences in extracted entities.

    Deduplicates entities by (name, entity_type) — case-insensitive.
    When duplicates are found, provenance metadata from all duplicates is
    merged into the canonical (first-seen) entity.

    ``are_semantically_equivalent`` remains False — semantic equivalence
    requires embedding infrastructure not available at extraction time.
    """

    def resolve(self, entities: list[Any]) -> list[Any]:
        """Deduplicate entities by normalised (name, entity_type).

        The first occurrence of each (name, type) pair is kept as the
        canonical entity.  Subsequent duplicates have their provenance
        merged into the canonical entity's ``provenance`` list (if the
        attribute exists) before being discarded.

        **Caller contract:** all entities in the list must belong to the
        same tenant.  Passing a mixed-tenant list is a programming error —
        this method raises ``ValueError`` if a duplicate entity carries a
        ``tenant_id`` that differs from the canonical entity's ``tenant_id``.
        Partition by tenant before calling ``resolve()``.

        Args:
            entities: Raw extracted entities.  Each entity is expected to
                expose ``name`` and ``entity_type`` attributes (or dict
                keys).  Entities that lack both are passed through unchanged.

        Returns:
            Deduplicated list preserving original insertion order of the
            canonical representatives.

        Raises:
            ValueError: If two entities share (name, entity_type) but have
                different ``tenant_id`` values.
        """
        seen: dict[tuple[str, str], int] = {}  # key -> index in `result`
        result: list[Any] = []

        for entity in entities:
            name, etype = self._get_key_fields(entity)
            if name is None and etype is None:
                # Can't deduplicate without identity fields — pass through.
                result.append(entity)
                continue

            key = (name or "", etype or "")
            if key not in seen:
                seen[key] = len(result)
                result.append(entity)
            else:
                # Guard against cross-tenant merges before touching provenance.
                canonical = result[seen[key]]
                self._assert_same_tenant(canonical, entity, key)
                self._merge_provenance(canonical, entity)

        return result

    def are_semantically_equivalent(self, entity1: Any, entity2: Any) -> bool:
        """Return whether two entities are semantically equivalent.

        Always returns False — semantic equivalence requires embedding
        infrastructure (vector similarity) that is not available at
        extraction time.  Use a downstream enrichment step for this.
        """
        return False

    # ── Internal helpers ──────────────────────────────────────────────────

    @staticmethod
    def _get_key_fields(entity: Any) -> tuple[str | None, str | None]:
        """Extract normalised (name, entity_type) from an entity.

        Supports both attribute-style objects and dict-style entities.
        """
        if isinstance(entity, dict):
            name = entity.get("name") or entity.get("entity_name")
            etype = entity.get("entity_type") or entity.get("type")
        else:
            name = getattr(entity, "name", None) or getattr(entity, "entity_name", None)
            etype = getattr(entity, "entity_type", None) or getattr(entity, "type", None)

        norm_name = " ".join(str(name).lower().split()) if name is not None else None
        norm_type = str(etype).lower().strip() if etype is not None else None
        return norm_name, norm_type

    @staticmethod
    def _get_tenant_id(entity: Any) -> str | None:
        """Extract tenant_id from an entity (dict or attribute-style)."""
        if isinstance(entity, dict):
            return entity.get("tenant_id")
        return getattr(entity, "tenant_id", None)

    @staticmethod
    def _assert_same_tenant(
        canonical: Any, duplicate: Any, key: tuple[str, str]
    ) -> None:
        """Raise ValueError if canonical and duplicate belong to different tenants.

        A cross-tenant merge would silently drop one tenant's entity and
        contaminate the other's provenance.  Callers must partition by
        tenant before calling resolve().
        """
        canonical_tid = CoreferenceResolver._get_tenant_id(canonical)
        duplicate_tid = CoreferenceResolver._get_tenant_id(duplicate)
        if (
            canonical_tid is not None
            and duplicate_tid is not None
            and canonical_tid != duplicate_tid
        ):
            raise ValueError(
                f"Cross-tenant merge detected for entity key {key!r}: "
                f"canonical tenant_id={canonical_tid!r} vs "
                f"duplicate tenant_id={duplicate_tid!r}. "
                "Partition entities by tenant before calling resolve()."
            )

    @staticmethod
    def _merge_provenance(canonical: Any, duplicate: Any) -> None:
        """Merge provenance metadata from *duplicate* into *canonical*.

        Appends items from ``duplicate.provenance`` (or ``duplicate["provenance"]``)
        into ``canonical.provenance`` (or ``canonical["provenance"]``).
        No-ops silently when neither entity has a provenance field.
        """
        if isinstance(canonical, dict) and isinstance(duplicate, dict):
            dup_prov = duplicate.get("provenance")
            if dup_prov is not None:
                existing = canonical.setdefault("provenance", [])
                if isinstance(dup_prov, list):
                    existing.extend(dup_prov)
                else:
                    existing.append(dup_prov)
        else:
            dup_prov = getattr(duplicate, "provenance", None)
            if dup_prov is not None:
                existing = getattr(canonical, "provenance", None)
                if existing is not None and isinstance(existing, list):
                    if isinstance(dup_prov, list):
                        existing.extend(dup_prov)
                    else:
                        existing.append(dup_prov)
