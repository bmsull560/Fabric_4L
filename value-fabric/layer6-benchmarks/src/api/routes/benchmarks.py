"""Benchmark domain routes for Layer 6 API."""

from typing import List

from fastapi import APIRouter, Depends

from .. import main as handlers
from ..deps import industry_filter, segment_filter

router = APIRouter(prefix="/v1/benchmarks", tags=["benchmarks"])


@router.get("/datasets", response_model=List[handlers.DatasetSummary])
async def list_datasets(
    industry: str | None = Depends(industry_filter),
    segment: str | None = Depends(segment_filter),
):
    return await handlers.list_datasets(industry=industry, segment=segment)


@router.get("/datasets/{dataset_id}", response_model=handlers.DatasetDetail)
async def get_dataset(dataset_id: str):
    return await handlers.get_dataset(dataset_id)


@router.post("/compare", response_model=handlers.ComparisonResponse)
async def compare(payload: handlers.ComparisonRequestPayload):
    return await handlers.compare(payload)


@router.post("/validate", response_model=handlers.ValidationResponse)
async def validate(payload: handlers.ValidationRequestPayload):
    return await handlers.validate(payload)


@router.get("/industries")
async def list_industries():
    return await handlers.list_industries()
