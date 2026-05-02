# MCP Gateway Test Suite

Production-grade test suite for the Fabric MCP Gateway, covering protocol compliance, security, multi-upstream aggregation, resilience, and observability.

## Test Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  E2E Tests (5%)                                             │
├─────────────────────────────────────────────────────────────┤
│  Integration Tests (25%) - Docker-based                   │
├─────────────────────────────────────────────────────────────┤
│  Contract Tests (30%) - Protocol compliance               │
├─────────────────────────────────────────────────────────────┤
│  Unit Tests (40%) - Pure Python                            │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures across all test layers
├── README.md                      # This file
│
├── unit/                          # Pure Python tests (no I/O)
│   ├── conftest.py               # Unit test fixtures
│   └── test_mcp_gateway_unit.py  # Core gateway unit tests
│
├── contract/                      # Protocol compliance tests
│   ├── fixtures/                  # Canned MCP client/server stubs
│   │   ├── __init__.py
│   │   ├── mock_mcp_client.py    # In-process MCP client
│   │   └── mock_mcp_server.py    # Configurable upstream server
│   ├── test_mcp_handshake.py     # Initialize/ping tests
│   └── test_tool_discovery.py    # tools/list tests
│
├── integration/                   # Docker-based real transport tests
│   ├── docker-compose.yml        # Gateway + upstream containers
│   ├── upstreams/                 # Reference MCP server containers
│   ├── test_single_upstream.py   # One backend, full flow
│   └── test_multi_upstream.py    # Aggregation tests
│
├── security/                      # Abuse cases and threat modeling
│   └── test_auth_security.py     # Token validation, tenant isolation
│
├── resilience/                    # Fault injection and degradation
│   └── test_timeouts.py          # Upstream timeout handling
│
└── performance/                   # Load and soak tests
    └── test_latency.py           # Gateway overhead measurement
```

## Running Tests

### Unit Tests (Fast, no dependencies)
```bash
cd value-fabric/shared/mcp_gateway
pytest tests/unit -v
```

### Contract Tests (In-process, no Docker)
```bash
pytest tests/contract -v
```

### Integration Tests (Requires Docker)
```bash
# Start infrastructure
docker compose -f tests/integration/docker-compose.yml up -d

# Run tests
pytest tests/integration -v -m "not slow"

# Cleanup
docker compose -f tests/integration/docker-compose.yml down
```

### Security Tests
```bash
pytest tests/security -v
```

### All Tests
```bash
make mcp-test-all  # See Makefile in repo root
```

## Pytest Markers

| Marker | Description | Usage |
|--------|-------------|-------|
| `unit` | Pure unit tests, no external deps | Fast feedback |
| `contract` | Protocol compliance | API stability |
| `integration` | Docker-based tests | Real transport |
| `security` | Abuse cases | Security posture |
| `resilience` | Fault injection | Production readiness |
| `performance` | Load tests | Capacity planning |
| `slow` | >5 second tests | CI optimization |
| `http` | Streamable HTTP tests | Transport-specific |
| `stdio` | STDIO adapter tests | Local dev |

## Test Coverage Requirements

- **Line Coverage**: >85%
- **Security Paths**: 100%
- **Auth/Authz**: 100%
- **Reliability**: >99% pass rate over 100 CI runs

## Key Test Categories

### 1. Contract Compliance (C-001 through C-305)
- MCP handshake protocol
- Tool/resource/prompt discovery
- Invocation schema validation
- Error handling per MCP spec

### 2. Routing and Aggregation (R-001 through R-204)
- Single upstream routing
- Multi-upstream tool aggregation
- Duplicate name handling
- Backend selection policies

### 3. Authentication and Authorization (A-001 through A-206)
- Token validation (expired, invalid, missing)
- Audience and scope enforcement
- Tenant isolation
- Per-tool access control

### 4. Security Abuse Cases (S-001 through S-203)
- Confused deputy prevention
- Injection attack handling
- Replay attack protection
- Secret redaction

### 5. Resilience (F-001 through F-304)
- Upstream timeout handling
- Circuit breaker behavior
- Partial outage handling
- Retry and backoff

### 6. Observability (O-001 through O-304)
- Structured logging
- Distributed tracing
- Metrics emission
- Audit events

## CI Integration

Tests are organized into GitHub Actions stages:
1. **unit** - Runs on every PR
2. **contract** - Runs on every PR
3. **integration** - Runs after contract passes
4. **security** - Runs after unit passes
5. **resilience** - Runs on schedule and [resilience] tag
6. **performance** - Runs on schedule and [perf] tag

## Fixtures

### Shared Fixtures (conftest.py)
- `sample_tenant_id` - UUID for tenant scoping
- `sample_user_token` - Valid-format JWT
- `sample_tool_manifest` - Tool definition
- `sample_oauth_config` - OAuth 2.1 + PKCE config
- `mock_gateway` - Gateway with mocked dependencies

### Contract Fixtures (contract/fixtures/)
- `MockMCPClient` - In-process MCP protocol client
- `MockMCPServer` - Configurable upstream with behaviors:
  - HEALTHY, SLOW, ERROR, FLAKY, TIMEOUT, GARBAGE

## Writing New Tests

### Unit Test Example
```python
@pytest.mark.unit
async def test_tool_registry_enables_for_tenant(sample_tool_registry):
    """Tool can be enabled for specific tenant."""
    registry = sample_tool_registry
    registry.enable_tool_for_tenant("test_search", "tenant-123")
    
    tool = registry.get_tool("test_search", "tenant-123")
    assert tool is not None
```

### Contract Test Example
```python
@pytest.mark.contract
async def test_tools_list_returns_schema(upstream_server):
    """C-101: tools/list returns properly structured tools."""
    client = MockMCPClient()
    client.set_request_handler(lambda r: upstream_server.handle_request(r))
    
    await client.send_initialize()
    response = await client.send_tools_list()
    
    assert "tools" in response.result
    for tool in response.result["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
```

## Docker Compose Services

The integration tests use these containerized services:

- **mcp-gateway** - Gateway under test
- **upstream-tools** - Healthy tools server
- **upstream-resources** - Resources server
- **upstream-prompts** - Prompts server
- **upstream-faulty** - Configurable faulty server (resilience tests)
- **upstream-slow** - High-latency server (timeout tests)
- **test-runner** - Pytest execution container

## References

- **Plan Document**: `~/.windsurf/plans/mcp-gateway-test-plan-577c80.md`
- **MCP Specification**: 2024-11-05
- **CONTRACT.md**: §2.4 - Tool Invocation Boundary
- **SECURITY.md**: Tenant isolation requirements
