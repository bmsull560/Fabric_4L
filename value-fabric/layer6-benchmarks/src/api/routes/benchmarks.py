"""Benchmark domain routes for Layer 6 API."""

from typing import List

from fastapi import APIRouter, Depends

from ..deps import industry_filter, segment_filter
from ..schemas import (
    ComparisonRequestPayload,
    ComparisonResponse,
    DatasetDetail,
    DatasetSummary,
    ValidationRequestPayload,
    ValidationResponse,
)

router = APIRouter(prefix="/v1/benchmarks", tags=["benchmarks"])


@router.get("/datasets", response_model=List[DatasetSummary])
async def list_datasets(
    industry: str | None = Depends(industry_filter),
    segment: str | None = Depends(segment_filter),
):
    from .. import main as handlers
    return await handlers.list_datasets(industry=industry, segment=segment)


@router.get("/datasets/{dataset_id}", response_model=DatasetDetail)
async def get_dataset(dataset_id: str):
    from .. import main as handlers
    return await handlers.get_dataset(dataset_id)


@router.post("/compare", response_model=ComparisonResponse)
async def compare(payload: ComparisonRequestPayload):
    from .. import main as handlers
    return await handlers.compare(payload)


@router.post("/validate", response_model=ValidationResponse)
async def validate(payload: ValidationRequestPayload):
    from .. import main as handlers
    return await handlers.validate(payload)


@router.get("/industries")
async def list_industries():
    from .. import main as handlers
    return await handlers.list_industries()
