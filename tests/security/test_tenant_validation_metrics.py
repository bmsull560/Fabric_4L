"""Test tenant validation metrics tracking invariants."""

from value_fabric.layer4 import database_facade as database


def test_tenant_validation_metrics_round_trip_and_reset():
    """Metrics counters should increment during validation and reset deterministically."""
    database.reset_tenant_validation_metrics()

    ok_tenant = "550e8400-e29b-41d4-a716-446655440000"
    assert database.validate_tenant_id(ok_tenant) == ok_tenant

    metrics = database.get_tenant_validation_metrics()
    assert metrics["validations_total"] >= 1

    database.reset_tenant_validation_metrics()
    reset = database.get_tenant_validation_metrics()
    assert reset == {
        "validations_total": 0,
        "validation_failures": 0,
        "uuid_format_errors": 0,
        "missing_context_errors": 0,
        "empty_tenant_errors": 0,
    }


def test_layer4_database_import_path_is_stable_facade():
    """Guard: tests rely on value_fabric.layer4.database_facade facade staying stable."""
    assert database.__name__ == "value_fabric.layer4.database_facade"
    assert hasattr(database, "validate_tenant_id")
    assert hasattr(database, "get_tenant_validation_metrics")
