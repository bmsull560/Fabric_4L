"""Provenance manifest generation for exported case packages."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from shared.identity.context import RequestContext

from ..config.settings import settings


def build_export_provenance_manifest(
    *,
    case_id: str,
    workflow_result: dict[str, Any],
    actor_context: RequestContext | None,
    export_id: str,
) -> dict[str, Any]:
    """Build provenance manifest JSON for case exports."""
    output = workflow_result.get("output", {})
    metadata = workflow_result.get("metadata", {})

    truth_object_ids = output.get("truth_object_ids", []) or metadata.get("truth_object_ids", [])
    source_refs = output.get("source_references", []) or metadata.get("source_references", [])
    sdes_bundle = output.get("generate_sdes", {}) or metadata.get("sdes", {})

    workflow_id = (
        workflow_result.get("workflow_id")
        or metadata.get("workflow_id")
        or case_id
    )

    now = datetime.now(UTC).isoformat()

    return {
        "export_id": export_id,
        "case_id": case_id,
        "workflow_id": workflow_id,
        "truth_object_ids": truth_object_ids,
        "source_references": source_refs,
        "sdes_references": {
            "canonical_case_id": sdes_bundle.get("canonical_case_id"),
            "account_id": sdes_bundle.get("account_id"),
            "signals": [item.get("id") for item in sdes_bundle.get("signals", [])],
            "drivers": [item.get("id") for item in sdes_bundle.get("drivers", [])],
            "evidence": [item.get("id") for item in sdes_bundle.get("evidence", [])],
            "stakeholders": [item.get("id") for item in sdes_bundle.get("stakeholders", [])],
        },
        "model_versions": {
            "openai_model": settings.openai_model,
            "anthropic_model": settings.anthropic_model,
            "layer4_app_version": settings.app_version,
        },
        "tool_versions": {
            "export_document": "1.0.0",
        },
        "timestamps": {
            "manifest_generated_at": now,
            "workflow_created_at": workflow_result.get("created_at"),
            "workflow_completed_at": workflow_result.get("completed_at"),
        },
        "actor": {
            "user_id": actor_context.user_id if actor_context else None,
            "api_key_id": actor_context.api_key_id if actor_context else None,
            "roles": actor_context.roles if actor_context else [],
            "identity_source": actor_context.source if actor_context else "unknown",
        },
        "tenant": {
            "tenant_id": str(actor_context.tenant_id) if actor_context else None,
        },
    }
