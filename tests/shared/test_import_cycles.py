import pytest
import importlib
import sys
import pkgutil

def test_no_shared_import_cycles():
    """Regression test for circular imports in the shared package."""
    modules_to_test = [
        "value_fabric.shared.boundaries.tenant_boundary",
        "value_fabric.shared.identity.context",
        "value_fabric.shared.identity.rate_limiter",
        "value_fabric.shared.rate_limiting.middleware",
        "value_fabric.shared.rate_limiting.tenant_rate_limiter",
        "value_fabric.shared.identity",
        "value_fabric.shared.rate_limiting",
        "value_fabric.shared.boundaries",
    ]
    
    # Try importing directly
    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            pytest.fail(f"ImportError (likely circular) for {module_name}: {e}")

def test_recursive_import_shared_package():
    """Dynamically discover and import all shared modules to ensure no cycles."""
    import value_fabric.shared
    
    def walk_packages(path, prefix):
        for info in pkgutil.walk_packages(path, prefix):
            try:
                importlib.import_module(info.name)
            except ImportError as e:
                pytest.fail(f"Failed to import {info.name}: {e}")

    walk_packages(value_fabric.shared.__path__, value_fabric.shared.__name__ + '.')
