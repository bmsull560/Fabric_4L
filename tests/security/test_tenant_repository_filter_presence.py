"""Repository-level tenant filter presence assertions for list/read/search operations."""

from __future__ import annotations

<<<<<<< HEAD
from pathlib import Path
=======
import inspect

from value_fabric.layer3.services import product_service as l3_product_service
from value_fabric.layer6.repositories.benchmark_repository import BenchmarkRepository

>>>>>>> 315e84c14c9306363c718c22c8cb7a292d514eee

import pytest

pytestmark = [pytest.mark.security, pytest.mark.tenant_boundary, pytest.mark.tenant_matrix]

<<<<<<< HEAD
REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_l2_job_store_list_read_tenant_filters_present() -> None:
    source = _read("services/layer2-extraction/src/layer2_extraction/integration/job_store.py")
    assert "def get_job(" in source
    assert "tenant_id is not None and job.tenant_id != tenant_id" in source
    assert "def list_jobs(" in source
    assert "if j.tenant_id == tenant_id" in source


def test_l3_product_service_list_read_tenant_filters_present() -> None:
    source = _read("services/layer3-knowledge/src/services/product_service.py")
    assert "def get_product(" in source
    assert "tenant_id: $tenant_id" in source
    assert "def list_products(" in source
    assert "p.tenant_id = $tenant_id" in source


def test_l6_benchmark_repository_list_read_tenant_filters_present() -> None:
    source = _read("services/layer6-benchmarks/src/repositories/benchmark_repository.py")
    assert "def _tx_get_dataset(" in source
    assert "tenant_id: $tenant_id" in source
    assert "def _tx_list_datasets(" in source
    assert "d.tenant_id = $tenant_id" in source
=======

def test_l2_job_store_list_read_tenant_filters_present() -> None:
    from layer2_extraction.integration.job_store import InMemoryJobStore

    read_source = inspect.getsource(InMemoryJobStore.get_job)
    list_source = inspect.getsource(InMemoryJobStore.list_jobs)
    assert "job.tenant_id != tenant_id" in read_source
    assert "j.tenant_id == tenant_id" in list_source


def test_l3_product_service_list_read_search_tenant_filters_present() -> None:
    read_source = inspect.getsource(l3_product_service.ProductService.get_product)
    list_source = inspect.getsource(l3_product_service.ProductService.list_products)
    search_source = inspect.getsource(l3_product_service.ProductService.search_products)

    assert "tenant_id: $tenant_id" in read_source
    assert "p.tenant_id = $tenant_id" in list_source
    assert "p.tenant_id = $tenant_id" in search_source


def test_l6_benchmark_repository_list_read_tenant_filters_present() -> None:
    read_source = inspect.getsource(BenchmarkRepository._tx_get_dataset)
    list_source = inspect.getsource(BenchmarkRepository._tx_list_datasets)

    assert "tenant_id: $tenant_id" in read_source
    assert "d.tenant_id = $tenant_id" in list_source
>>>>>>> 315e84c14c9306363c718c22c8cb7a292d514eee
