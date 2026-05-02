"""Composite prospect context endpoint.

Aggregates cross-layer context (Layer1/2/3/5 + CRM) for a prospect into a
single frontend-friendly schema.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from value_fabric.shared.security.dil_auth import get_verified_tenant_id

from ...integration.layer1_client import Layer1IngestionClient
from ...integration.layer2_client import Layer2ExtractionClient
from ...integration.layer3_client import Layer3Client, Layer3ClientError
from ...integration.layer5_client import Layer5GroundTruthClient

router = APIRouter(prefix="/prospects", tags=["prospects"])


class ContextField(BaseModel):
    value: Any = None
    inferred: bool = False
    needs_confirmation: bool = False
    source: str


class ProspectContextResponse(BaseModel):
    prospect_id: str
    company_profile: ContextField
    contact_role: ContextField
    crm_match: ContextField
    confidence_flags: list[dict[str, Any]] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=lambda: ["confirm", "adjust", "edit"])


@router.get("/{prospect_id}/context", response_model=ProspectContextResponse)
async def get_prospect_context(
    prospect_id: str,
    tenant_id: str = Depends(get_verified_tenant_id),
) -> ProspectContextResponse:
    """Assemble a composite context payload for a prospect.

    Explicitly returns inferred/needs_confirmation/source per UI expectations.
    """
    layer3 = Layer3Client(base_url=os.getenv("LAYER3_URL", "http://layer3-knowledge:8000"), tenant_id=tenant_id)
    layer1 = Layer1IngestionClient(base_url=os.getenv("LAYER1_URL", "http://layer1-ingestion:8000"))
    layer2 = Layer2ExtractionClient(base_url=os.getenv("LAYER2_URL", "http://layer2-extraction:8000"))
    layer5 = Layer5GroundTruthClient(base_url=os.getenv("LAYER5_GROUND_TRUTH_URL", "http://layer5-ground-truth:8005"), tenant_id=tenant_id)

    try:
        profile_data: dict[str, Any] | None = None
        try:
            profile_data = await layer3.get_entity(prospect_id, tenant_id=tenant_id)
        except Layer3ClientError:
            profile_data = None

        company_profile = ContextField(
            value=profile_data or {},
            inferred=profile_data is None,
            needs_confirmation=profile_data is None,
            source="layer3_knowledge_graph" if profile_data else "layer3_unavailable",
        )

        role_value = "unknown"
        role_inferred = True
        role_needs_confirmation = True

        role_hint = (profile_data or {}).get("title") or (profile_data or {}).get("role")
        if role_hint:
            role_value = role_hint
            role_needs_confirmation = False
        else:
            extraction = await layer2.extract_financial_metrics(
                document_text=f"Infer contact role for prospect {prospect_id}",
                metrics=["contact_role"],
            )
            maybe_role = extraction.get("contact_role") or extraction.get("metrics", {}).get("contact_role")
            if maybe_role:
                role_value = maybe_role

        contact_role = ContextField(
            value=role_value,
            inferred=role_inferred,
            needs_confirmation=role_needs_confirmation,
            source="layer2_extraction" if role_needs_confirmation else "layer3_knowledge_graph",
        )

        truths = await layer5.list_truths(organization_id=tenant_id, claim_type=None, status="APPROVED", limit=25)
        truth_items = truths.get("items", []) if isinstance(truths, dict) else []

        # Layer 1 client is included for completeness; if no ingestion metadata exists,
        # keep an explicit inferred match state.
        crm_ingestion_source = "layer1_ingestion"
        if profile_data and profile_data.get("crm_id"):
            crm_value: dict[str, Any] = {"matched": True, "record_id": profile_data.get("crm_id")}
            crm_inferred = False
            crm_needs_confirmation = False
            crm_ingestion_source = "layer3_knowledge_graph"
        else:
            crm_value = {"matched": False, "record_id": None}
            crm_inferred = True
            crm_needs_confirmation = True

        crm_match = ContextField(
            value=crm_value,
            inferred=crm_inferred,
            needs_confirmation=crm_needs_confirmation,
            source=crm_ingestion_source,
        )

        confidence_flags = [
            {
                "name": "company_profile_completeness",
                "inferred": company_profile.inferred,
                "needs_confirmation": company_profile.needs_confirmation,
                "source": company_profile.source,
            },
            {
                "name": "contact_role_confidence",
                "inferred": contact_role.inferred,
                "needs_confirmation": contact_role.needs_confirmation,
                "source": contact_role.source,
            },
            {
                "name": "crm_match_confidence",
                "inferred": crm_match.inferred,
                "needs_confirmation": crm_match.needs_confirmation,
                "source": crm_match.source,
            },
            {
                "name": "ground_truth_available",
                "inferred": len(truth_items) == 0,
                "needs_confirmation": len(truth_items) == 0,
                "source": "layer5_ground_truth",
            },
        ]

        return ProspectContextResponse(
            prospect_id=prospect_id,
            company_profile=company_profile,
            contact_role=contact_role,
            crm_match=crm_match,
            confidence_flags=confidence_flags,
        )
    finally:
        await layer1.close()
        await layer2.close()
        await layer3.close()
        await layer5.close()
