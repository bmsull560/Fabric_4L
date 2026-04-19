"""
Pack Variable Loader — Phase 2 of the Canonical Contract Migration.

Connects pack-level variables.json definitions to the Layer 4 Variable Registry
(IVariableRegistry / Neo4jVariableRegistry). This is the bridge that makes pack
variables first-class citizens in the registry, enabling:

  - test_pack_variables_loadable  (Phase 1 data fix + this loader)
  - test_formula_variable_references_valid  (registry validates formula refs)
  - test_manifest_variable_counts  (registry count == manifest declared count)

Usage:
    loader = PackVariableLoader(registry=variable_registry_service)
    result = await loader.load_pack(pack_id="financial-services-v1")
    # All variables now in Neo4j Variable Registry with full provenance
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..interfaces.variable_registry import (
    IVariableRegistry,
    Variable,
    VariableDataType,
    VariableSourceBinding,
    VariableSourceType,
    VariableValidationRule,
)

logger = logging.getLogger(__name__)

# Default path to packs directory — resolved relative to repo root at runtime
_DEFAULT_PACKS_DIR = Path(__file__).parents[7] / "packs"

# Mapping from pack variable type strings to VariableDataType enum
_TYPE_MAP: dict[str, VariableDataType] = {
    "currency": VariableDataType.DECIMAL,
    "usd": VariableDataType.DECIMAL,
    "percentage": VariableDataType.DECIMAL,
    "percent": VariableDataType.DECIMAL,
    "integer": VariableDataType.INTEGER,
    "count": VariableDataType.INTEGER,
    "number": VariableDataType.DECIMAL,
    "decimal": VariableDataType.DECIMAL,
    "string": VariableDataType.STRING,
    "boolean": VariableDataType.BOOLEAN,
    "date": VariableDataType.DATE,
}


@dataclass
class PackLoadResult:
    """Result of loading a single pack's variables into the registry."""

    pack_id: str
    variables_loaded: int
    variables_skipped: int  # Already existed in registry
    variables_failed: int
    errors: list[str] = field(default_factory=list)
    loaded_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def success(self) -> bool:
        return self.variables_failed == 0

    def summary(self) -> str:
        return (
            f"Pack '{self.pack_id}': loaded={self.variables_loaded}, "
            f"skipped={self.variables_skipped}, failed={self.variables_failed}"
        )


class PackVariableLoader:
    """
    Loads pack variables.json definitions into the IVariableRegistry.

    Designed to be called:
      - At application startup (load all published packs)
      - When a new pack is activated (load single pack)
      - During CI/CD (validate all packs against registry schema)
    """

    def __init__(
        self,
        registry: IVariableRegistry,
        packs_dir: Path | str | None = None,
    ) -> None:
        self._registry = registry
        self._packs_dir = Path(packs_dir) if packs_dir else _DEFAULT_PACKS_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def load_all_packs(self) -> list[PackLoadResult]:
        """Load variables from all packs listed in pack-manifest.json."""
        manifest_path = self._packs_dir / "pack-manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"pack-manifest.json not found at {manifest_path}")

        with open(manifest_path) as f:
            manifest = json.load(f)

        results: list[PackLoadResult] = []
        for pack_entry in manifest.get("packs", []):
            pack_id = pack_entry["pack_id"]
            try:
                result = await self.load_pack(pack_id)
                results.append(result)
                logger.info(result.summary())
            except Exception as exc:
                logger.error(f"Failed to load pack '{pack_id}': {exc}")
                results.append(
                    PackLoadResult(
                        pack_id=pack_id,
                        variables_loaded=0,
                        variables_skipped=0,
                        variables_failed=1,
                        errors=[str(exc)],
                    )
                )
        return results

    async def load_pack(self, pack_id: str) -> PackLoadResult:
        """
        Load all variables from a single pack into the Variable Registry.

        Args:
            pack_id: The pack identifier (e.g. "financial-services-v1")

        Returns:
            PackLoadResult with counts and any errors
        """
        pack_dir_name = pack_id.replace("-v1", "").replace("-v2", "").replace("-v3", "")
        variables_path = self._packs_dir / pack_dir_name / "variables.json"

        if not variables_path.exists():
            raise FileNotFoundError(
                f"variables.json not found for pack '{pack_id}' at {variables_path}"
            )

        with open(variables_path) as f:
            data = json.load(f)

        raw_variables: list[dict[str, Any]] = data.get("variables", [])
        loaded = skipped = failed = 0
        errors: list[str] = []

        for raw_var in raw_variables:
            try:
                variable = self._build_variable(raw_var, pack_id)

                # Check if already registered (idempotent load)
                existing = await self._registry.get_variable(variable.variable_id)
                if existing is not None:
                    skipped += 1
                    continue

                await self._registry.register_variable(variable)
                loaded += 1

            except Exception as exc:
                var_id = raw_var.get("variable_id", "unknown")
                msg = f"Failed to register variable '{var_id}': {exc}"
                logger.warning(msg)
                errors.append(msg)
                failed += 1

        return PackLoadResult(
            pack_id=pack_id,
            variables_loaded=loaded,
            variables_skipped=skipped,
            variables_failed=failed,
            errors=errors,
        )

    async def validate_pack_references(self, pack_id: str) -> list[str]:
        """
        Validate that all formula variable references in a pack resolve
        to registered variables. Returns a list of error messages (empty = valid).
        """
        pack_dir_name = pack_id.replace("-v1", "").replace("-v2", "").replace("-v3", "")
        formulas_path = self._packs_dir / pack_dir_name / "formulas.json"
        variables_path = self._packs_dir / pack_dir_name / "variables.json"

        if not formulas_path.exists() or not variables_path.exists():
            return [f"Missing formulas.json or variables.json for pack '{pack_id}'"]

        with open(variables_path) as f:
            var_data = json.load(f)
        with open(formulas_path) as f:
            formula_data = json.load(f)

        # Build set of valid variable names from the pack file
        valid_names = {v["variable_name"] for v in var_data.get("variables", [])}

        errors: list[str] = []
        for formula in formula_data.get("formulas", []):
            formula_id = formula.get("formula_id", "unknown")
            refs = formula.get("expression", {}).get("variables", [])
            for ref in refs:
                if ref not in valid_names:
                    errors.append(
                        f"[{pack_id}] Formula '{formula_id}' references "
                        f"undefined variable '{ref}'"
                    )
        return errors

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_variable(self, raw: dict[str, Any], pack_id: str) -> Variable:
        """
        Convert a raw pack variables.json entry into a typed Variable object.

        Field mapping (pack JSON → Variable):
          variable_id   → variable_id
          canonicalName → name (canonical, normalized)
          display_name  → description (human-readable label)
          unit/type     → data_type (mapped via _TYPE_MAP)
          pack_id       → applicable_packs
        """
        variable_id = raw["variable_id"]
        canonical_name = raw.get("canonicalName") or raw.get("variable_name", "")
        display_name = raw.get("display_name") or raw.get("name") or canonical_name
        description = raw.get("description") or display_name
        raw_type = (raw.get("unit") or raw.get("type") or "string").lower()
        data_type = _TYPE_MAP.get(raw_type, VariableDataType.STRING)

        # Source binding: pack-defined variables are USER_INPUT by default
        # (the user provides the actual value at runtime; the pack defines the schema)
        source_binding = VariableSourceBinding(
            source_type=VariableSourceType.USER_INPUT,
            source_location=f"pack:{pack_id}:{variable_id}",
            fallback_value=raw.get("default_value"),
            is_required=raw.get("required", True),
        )

        # Build validation rules from pack metadata if present
        validation_rules: list[VariableValidationRule] = []
        if "min_value" in raw or "max_value" in raw:
            params: dict[str, Any] = {}
            if "min_value" in raw:
                params["min"] = raw["min_value"]
            if "max_value" in raw:
                params["max"] = raw["max_value"]
            validation_rules.append(
                VariableValidationRule(
                    rule_type="range",
                    parameters=params,
                    error_message=(
                        f"Value for '{canonical_name}' must be between "
                        f"{params.get('min', '-∞')} and {params.get('max', '+∞')}"
                    ),
                )
            )

        return Variable(
            variable_id=variable_id,
            name=canonical_name,
            description=description,
            data_type=data_type,
            source_binding=source_binding,
            validation_rules=validation_rules,
            industry=raw.get("industry"),
            applicable_packs=[pack_id],
            version=raw.get("version", "1.0.0"),
            is_active=raw.get("is_active", True),
        )
