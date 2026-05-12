from value_fabric.layer3.services.compat_metrics import (
    get_compat_metrics_snapshot,
    record_deprecated_legacy_field_usage,
    record_deprecated_route_hit,
)


def test_compat_metrics_are_segmented_by_tenant_and_app_client() -> None:
    record_deprecated_route_hit("/v1/query", tenant_id="tenant-a", app_client="web")
    record_deprecated_legacy_field_usage("search_type=fulltext", tenant_id="tenant-a", app_client="web")

    snapshot = get_compat_metrics_snapshot()
    assert snapshot["route_hits"]["/v1/query|tenant-a|web"] >= 1
    assert snapshot["legacy_field_hits"]["search_type=fulltext|tenant-a|web"] >= 1
