from __future__ import annotations

import logging

import pytest

from layer2_extraction.startup.dependency_verifier import DependencyRule, verify_startup_dependencies


def test_production_fails_closed_for_required_dependency() -> None:
    with pytest.raises(RuntimeError, match="missing_dependency_for_tests"):
        verify_startup_dependencies(
            [
                DependencyRule(
                    module="missing_dependency_for_tests",
                    required_in_prod=True,
                    remediation="pip install missing_dependency_for_tests",
                )
            ],
            environment="production",
        )


def test_development_allows_missing_optional_dependency(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)

    verify_startup_dependencies(
        [
            DependencyRule(
                module="missing_dev_dependency_for_tests",
                required_in_prod=False,
                remediation="pip install missing_dev_dependency_for_tests",
            )
        ],
        environment="development",
    )

    assert "missing_dev_dependency_for_tests" in caplog.text
    assert "Remediation" in caplog.text
