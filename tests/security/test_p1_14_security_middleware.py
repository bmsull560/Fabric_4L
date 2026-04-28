"""Regression tests for P1-14: SecurityMiddleware skip lists.

These tests verify that critical ingestion/extraction endpoints are not
in the SecurityMiddleware skip lists.
"""

import pytest


class TestSecurityMiddlewareCoverage:
    """Test that SecurityMiddleware validates all untrusted input paths."""

    def test_layer1_no_ingest_in_skip_list(self):
        """L1: /v1/ingest paths must NOT be in skip_validation_paths."""
        # Import the config from L1 main.py
        from value_fabric.layer1_ingestion.src.api.main import _security_config_l1

        skip_paths = _security_config_l1.skip_validation_paths

        # These paths must be validated (NOT in skip list)
        assert "/v1/ingest" not in skip_paths, "/v1/ingest must be validated"
        assert "/v1/ingest/batch" not in skip_paths, "/v1/ingest/batch must be validated"
        assert "/v1/batch/ingest" not in skip_paths, "/v1/batch/ingest must be validated"

        # These paths are OK to skip
        assert "/health" in skip_paths
        assert "/metrics" in skip_paths

    def test_layer2_no_extract_in_skip_list(self):
        """L2: /v1/extract paths must NOT be in skip_validation_paths."""
        from value_fabric.layer2_extraction.src.layer2_extraction.api.main import (
            _security_config_l2,
        )

        skip_paths = _security_config_l2.skip_validation_paths

        # These paths must be validated
        assert "/v1/extract" not in skip_paths, "/v1/extract must be validated"
        assert "/v1/extract/batch" not in skip_paths, "/v1/extract/batch must be validated"
        assert "/v1/nl-query" not in skip_paths, "/v1/nl-query must be validated"

        # These paths are OK to skip
        assert "/health" in skip_paths
        assert "/metrics" in skip_paths

    def test_layer3_no_query_in_skip_list(self):
        """L3: /v1/query paths must NOT be in skip_validation_paths."""
        from value_fabric.layer3_knowledge.src.api.main import _security_config_l3

        skip_paths = _security_config_l3.skip_validation_paths

        # These paths must be validated
        assert "/v1/query" not in skip_paths, "/v1/query must be validated"
        assert "/v1/query/graph" not in skip_paths, "/v1/query/graph must be validated"
        assert "/v1/graph/query" not in skip_paths, "/v1/graph/query must be validated"

        # These paths are OK to skip
        assert "/health" in skip_paths
        assert "/metrics" in skip_paths

    def test_layer4_no_agent_in_skip_list(self):
        """L4: /agents/v1 paths must NOT be in skip_validation_paths."""
        from value_fabric.layer4_agents.src.api.main import _security_config_l4

        skip_paths = _security_config_l4.skip_validation_paths

        # These paths must be validated
        assert "/agents/v1/workflows" not in skip_paths, "/agents/v1/workflows must be validated"
        assert "/agents/v1/skills" not in skip_paths, "/agents/v1/skills must be validated"
        assert "/agents/v1/analyze" not in skip_paths, "/agents/v1/analyze must be validated"

        # These paths are OK to skip
        assert "/health" in skip_paths
        assert "/metrics" in skip_paths

    def test_security_middleware_has_strict_mode(self):
        """All layers must have strict_mode=True."""
        from value_fabric.layer1_ingestion.src.api.main import _security_config_l1
        from value_fabric.layer2_extraction.src.layer2_extraction.api.main import (
            _security_config_l2,
        )
        from value_fabric.layer3_knowledge.src.api.main import _security_config_l3
        from value_fabric.layer4_agents.src.api.main import _security_config_l4

        assert _security_config_l1.strict_mode is True
        assert _security_config_l2.strict_mode is True
        assert _security_config_l3.strict_mode is True
        assert _security_config_l4.strict_mode is True
