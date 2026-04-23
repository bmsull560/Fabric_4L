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
    assemble_output = output.get("assemble_document", {})
    case_metadata = assemble_output.get("case_metadata", {})

    truth_object_ids = case_metadata.get("truth_object_ids", [])
    source_refs = case_metadata.get("claim_traceability", [])
    threshold_decisions = case_metadata.get("threshold_decisions", [])

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
        "threshold_decisions": threshold_decisions,
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
