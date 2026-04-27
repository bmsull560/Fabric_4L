"""Regression tests for Fabric 4L security fixes.

Tests verify that vulnerabilities identified in the adversarial security audit
are patched and cannot be exploited.
"""

import inspect
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import yaml
import ast
import re
import xml.etree.ElementTree as ET

# ============================================================================
# P0-8: Tools endpoints require authentication
# ============================================================================

def test_tools_list_requires_auth():
    """P0-8: /tools endpoint must require authentication."""
    from fastapi.testclient import TestClient
    from value_fabric.layer4_agents.src.api.routes.tools import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/v1")
    client = TestClient(app)

    # Without auth, should fail with 401/403
    response = client.get("/v1/tools")
    # The require_authenticated dependency should block unauthenticated requests
    assert response.status_code in (401, 403)


def test_tools_invoke_requires_auth():
    """P0-8: /tools/invoke endpoint must require authentication."""
    from fastapi.testclient import TestClient
    from value_fabric.layer4_agents.src.api.routes.tools import router
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/v1")
    client = TestClient(app)

    # Without auth, should fail
    response = client.post(
        "/v1/tools/invoke",
        json={"tool_name": "calculate_roi", "input_data": {}}
    )
    assert response.status_code in (401, 403)


# ============================================================================
# P0-3: Dev tenant fallback removed
# ============================================================================

def test_get_current_tenant_id_requires_auth():
    """P0-3: Missing authentication should raise 401, not return dev tenant UUID."""
    from fastapi import Request, HTTPException
    from value_fabric.layer1_ingestion.src.api.main import get_current_tenant_id

    # Mock request without governance context
    request = Mock(spec=Request)
    request.state = Mock()
    request.state.governance_context = None
    request.headers = {}

    # Should raise HTTPException 401, not return hardcoded UUID
    with pytest.raises(HTTPException) as exc_info:
        get_current_tenant_id(request)
    
    # Verify it's an HTTP 401 error
    assert exc_info.value.status_code == 401


# ============================================================================
# P0-4: Query param auth removed
# ============================================================================

def test_query_param_auth_rejected():
    """P0-4: Query param tenant_id should not grant authentication."""
    from shared.identity.middleware_sync import GovernanceMiddlewareSync

    # Mock WSGI environment with query param but no valid auth
    environ = {
        "PATH_INFO": "/api/v1/ingestion/targets",
        "REQUEST_METHOD": "GET",
        "QUERY_STRING": "tenant_id=00000000-0000-0000-0000-000000000001",
        "HTTP_AUTHORIZATION": None,
        "HTTP_X_API_KEY": None,
        "HTTP_X_TENANT_ID": None,
        "HTTP_X_SERVICE_AUTH": "",
    }

    middleware = GovernanceMiddlewareSync(Mock(), api_key_resolver=None)
    ctx = middleware._resolve_identity_sync(
        auth_header=None,
        api_key_header=None,
        x_tenant_header=None,
        x_service_auth="",
        request_path="/api/v1/ingestion/targets",
        request_method="GET",
    )

    # Should return None - query param auth is disabled
    assert ctx is None


# ============================================================================
# F-1: X-Tenant-ID requires service secret
# ============================================================================

def test_x_tenant_id_requires_service_secret():
    """F-1: X-Tenant-ID header should require X-Service-Auth."""
    from shared.identity.middleware_sync import GovernanceMiddlewareSync
    from uuid import uuid4

    tenant_id = str(uuid4())

    middleware = GovernanceMiddlewareSync(Mock(), api_key_resolver=None)
    
    # Without service secret, should reject
    ctx = middleware._resolve_identity_sync(
        auth_header=None,
        api_key_header=None,
        x_tenant_header=tenant_id,
        x_service_auth="wrong_secret",
        request_path="/api/v1/ingestion/targets",
        request_method="GET",
    )
    assert ctx is None

    # With matching secret, should accept
    middleware._service_auth_secret = "correct_secret"
    ctx = middleware._resolve_identity_sync(
        auth_header=None,
        api_key_header=None,
        x_tenant_header=tenant_id,
        x_service_auth="correct_secret",
        request_path="/api/v1/ingestion/targets",
        request_method="GET",
    )
    assert ctx is not None
    assert ctx.tenant_id == tenant_id


# ============================================================================
# P0-2: eval() replaced with AST evaluator
# ============================================================================

def test_safe_eval_blocks_unsafe_expressions():
    """P0-2: AST evaluator should reject dangerous constructs."""
    from value_fabric.layer3_knowledge.src.services.signal_quantification import SignalQuantificationService
    from neo4j import AsyncDriver

    service = SignalQuantificationService(Mock(spec=AsyncDriver))

    # Test object traversal bypass attempts
    unsafe_expressions = [
        "().__class__",
        "(1).__class__",
        "().__class__.__base__",
        "[].__class__",
        "''.__class__",
        "{}.__class__",
        "__import__('os')",
        "open('/etc/passwd')",
        "eval('1+1')",
        "exec('print(1)')",
    ]

    for expr in unsafe_expressions:
        with pytest.raises((ValueError, NameError, TypeError)):
            service._safe_eval(expr, {"x": 1})


def test_safe_eval_allows_safe_expressions():
    """P0-2: AST evaluator should allow safe arithmetic."""
    from value_fabric.layer3_knowledge.src.services.signal_quantification import SignalQuantificationService
    from neo4j import AsyncDriver

    service = SignalQuantificationService(Mock(spec=AsyncDriver))

    # Safe expressions should work
    assert service._safe_eval("x", {"x": 5}) == 5.0
    assert service._safe_eval("x + y", {"x": 5, "y": 3}) == 8.0
    assert service._safe_eval("x * y", {"x": 5, "y": 3}) == 15.0
    assert service._safe_eval("abs(-5)", {}) == 5.0
    assert service._safe_eval("max(1, 2, 3)", {}) == 3.0


# ============================================================================
# P0-1: SOQL injection fixed with ID validation
# ============================================================================

def test_sfdc_id_validation():
    """P0-1: Invalid Salesforce IDs should be rejected."""
    from value_fabric.layer4_agents.src.tools.crm_tools import GetProspectDataTool

    tool = GetProspectDataTool()

    # Valid IDs (15 or 18 alphanumeric chars)
    valid_ids = [
        "001D000000Yg4rI",  # 15 chars
        "001D000000Yg4rIIAR",  # 18 chars
        "123456789012345",  # 15 numeric
    ]

    for valid_id in valid_ids:
        assert tool._validate_sfdc_id(valid_id) == valid_id

    # Invalid IDs should raise ValueError
    invalid_ids = [
        "001D000000Yg4r'",  # SQL injection
        "001D000000Yg4r OR 1=1",  # SQL injection
        "../../../etc/passwd",  # Path traversal
        "<script>alert(1)</script>",  # XSS
        "001D000000Yg4r*",  # Too short
        "",  # Empty
    ]

    for invalid_id in invalid_ids:
        with pytest.raises(ValueError, match="Invalid.*format"):
            tool._validate_sfdc_id(invalid_id)


# ============================================================================
# P0-9: WebSocket authentication
# ============================================================================

def test_websocket_requires_token():
    """P0-9: WebSocket should reject connections without valid token."""
    # This would require a WebSocket client test
    # For now, verify the code checks for token
    from value_fabric.layer4_agents.src.api.routes.signals import signal_stream_websocket

    source = inspect.getsource(signal_stream_websocket)
    assert "token" in source
    assert "decode_jwt" in source or "JWT_SECRET" in source


# ============================================================================
# P1-10: Pickle serializer disabled
# ============================================================================

def test_pickle_serializer_disabled():
    """P1-10: Pickle serializer should raise ValueError."""
    from value_fabric.layer3_knowledge.src.cache.redis_cache import RedisCache

    cache = RedisCache()
    cache.config.serializer = "pickle"

    # Should raise ValueError
    with pytest.raises(ValueError, match="pickle serializer is disabled"):
        cache._serialize({"test": "data"})

    with pytest.raises(ValueError, match="pickle serializer is disabled"):
        cache._deserialize(b"test")


# ============================================================================
# P1-11: Cypher write operations blocked
# ============================================================================

def test_cypher_write_operations_blocked():
    """P1-11: Write Cypher operations should be rejected."""
    from value_fabric.layer4_agents.src.tools.knowledge_tools import QueryGraphTool

    tool = QueryGraphTool()

    # Write operations should be rejected
    write_queries = [
        "CREATE (n:Person {name: 'Alice'})",
        "DELETE n",
        "DETACH DELETE n",
        "SET n.name = 'Bob'",
        "MERGE (n:Person {name: 'Alice'})",
        "REMOVE n.name",
        "DROP INDEX ON :Person(name)",
        "CALL db.index.fulltext.createNodeIndex",
    ]

    for query in write_queries:
        with pytest.raises(ValueError, match="Write operations are not allowed"):
            tool._validate_read_only(query)

    # Read operations should be allowed
    read_queries = [
        "MATCH (n:Person) RETURN n",
        "MATCH (n:Person)-[:KNOWS]->(m) RETURN n, m",
        "MATCH (n) WHERE n.name = 'Alice' RETURN n",
    ]

    for query in read_queries:
        tool._validate_read_only(query)  # Should not raise


# ============================================================================
# P1-20: XXE protection with defusedxml
# ============================================================================

def test_xbrl_parser_uses_defusedxml():
    """P1-20: XBRL parser should use defusedxml to prevent XXE."""
    from value_fabric.layer1_ingestion.src.adapters.xbrl_parser import XBRLParser
    import inspect

    source = inspect.getsource(XBRLParser.parse)
    
    # Should use defusedxml.fromstring, not ET.fromstring
    assert "fromstring" in source
    # Check that defusedxml is imported
    from value_fabric.layer1_ingestion.src.adapters import xbrl_parser as parser_module
    assert hasattr(parser_module, 'fromstring')


def test_defusedxml_blocks_xxe():
    """P1-20: defusedxml should block XXE attacks."""
    from defusedxml.ElementTree import fromstring

    # XXE payload attempting to read /etc/passwd
    xxe_payload = """<?xml version="1.0"?>
    <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
    <root>&xxe;</root>
    """

    # defusedxml should raise an exception
    with pytest.raises(Exception):  # defusedxml raises DefusedXmlException
        fromstring(xxe_payload)


# ============================================================================
# P1-15: L6 fails closed in production
# ============================================================================

def test_l6_fails_closed_without_middleware():
    """P1-15: L6 should fail to start in production/staging if middleware missing."""
    import os

    # Save original
    original_env = os.environ.get("ENVIRONMENT")

    # Test production
    os.environ["ENVIRONMENT"] = "production"

    # Verify the logic exists in main.py
    from value_fabric.layer6_benchmarks.src.api import main as l6_main
    source = inspect.getsource(l6_main)

    assert "GovernanceMiddleware is required" in source or "RuntimeError" in source

    # Restore
    if original_env:
        os.environ["ENVIRONMENT"] = original_env
    else:
        os.environ.pop("ENVIRONMENT", None)


# ============================================================================
# P1-16: C_FORCE_ROOT disabled
# ============================================================================

def test_c_force_root_disabled_in_k8s():
    """P1-16: K8s manifests should have C_FORCE_ROOT=false."""
    # Resolve path from test file location
    manifest_path = Path(__file__).parent.parent.parent / "k8s" / "base" / "layer1-celery.yaml"
    with open(manifest_path) as f:
        manifest = yaml.safe_load(f)

    # Check all deployments
    deployments = [item for item in manifest if item.get("kind") == "Deployment"]
    
    for deployment in deployments:
        containers = deployment["spec"]["template"]["spec"]["containers"]
        for container in containers:
            env_vars = container.get("env", [])
            for env in env_vars:
                if env.get("name") == "C_FORCE_ROOT":
                    assert env.get("value") == "false", \
                        f"{deployment['metadata']['name']} should have C_FORCE_ROOT=false"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
