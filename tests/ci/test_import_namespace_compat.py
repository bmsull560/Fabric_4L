import importlib


def test_value_fabric_namespace_import_still_resolves() -> None:
    module = importlib.import_module("value_fabric")
    assert module is not None


def test_value_fabric_shared_import_still_resolves() -> None:
    module = importlib.import_module("value_fabric.shared")
    assert module is not None
