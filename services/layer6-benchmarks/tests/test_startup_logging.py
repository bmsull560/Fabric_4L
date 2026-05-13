from src.api.startup_logging import config_fingerprint, emit_startup_metadata


def test_config_fingerprint_is_stable() -> None:
    left = config_fingerprint({"a": 1, "b": "x"})
    right = config_fingerprint({"b": "x", "a": 1})
    assert left == right
    assert len(left) == 16


def test_emit_startup_metadata_logs_version_and_build(caplog) -> None:
    with caplog.at_level("INFO", logger="layer6.startup"):
        emit_startup_metadata(
            service="layer6-benchmarks",
            version="1.2.3",
            build_sha="abc123",
            config={"feature_flag": "on"},
        )

    assert any(
        rec.name == "layer6.startup"
        and getattr(rec, "service", None) == "layer6-benchmarks"
        and getattr(rec, "version", None) == "1.2.3"
        and getattr(rec, "build_sha", None) == "abc123"
        and getattr(rec, "config_fingerprint", None)
        for rec in caplog.records
    )
