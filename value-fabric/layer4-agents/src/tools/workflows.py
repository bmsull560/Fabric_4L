"""
Workflow tools that chain multiple operations.
"""

import logging
from uuid import UUID
from fastapi import HTTPException, status

from shared.identity.context import RequestContext
from .knowledge import get_entity, update_entity
from .analytics import compute_metrics

logger = logging.getLogger(__name__)


async def analyze_entity(
    tenant_id: UUID,
    entity_id: str,
    context: RequestContext | None = None
) -> dict:
    """Analyze entity by getting data and computing metrics.
    
    Args:
        tenant_id: Tenant UUID
        entity_id: Entity identifier
        context: Request context (optional)
    
    Returns:
        Analysis results
    """
    # Get entity (maintains tenant context)
    entity_data = await get_entity(tenant_id=tenant_id, entity_id=entity_id)
    
    if not entity_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found"
        )
    
    # Compute metrics (maintains tenant context)
    metrics = await compute_metrics(tenant_id=tenant_id, entity_data=entity_data)
    
    return {
        "entity": entity_data,
        "metrics": metrics
    }


async def read_and_update(
    tenant_id: UUID,
    entity_id: str,
    context: RequestContext | None = None
) -> dict:
    """Read entity and update it (requires write permission).
    
    Args:
        tenant_id: Tenant UUID
        entity_id: Entity identifier
        context: Request context (required for permission check)
    
    Returns:
        Updated entity
    
    Raises:
        HTTPException: If no write permission
    """
    # Get entity
    entity_data = await get_entity(tenant_id=tenant_id, entity_id=entity_id)
    
    if not entity_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found"
        )
    
    # Update entity (permission check happens here)
    updated = await update_entity(
        tenant_id=tenant_id,
        entity_id=entity_id,
        updates={"analyzed": True},
        context=context
    )
    
    return updated
