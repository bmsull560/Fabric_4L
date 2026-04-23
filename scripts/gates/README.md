# Fabric 4L Gate System

Unified release gate orchestration system with plugin architecture, artifact management, and cryptographic signing.

## Quick Start

```bash
# Install the gate system
pip install -e scripts/gates/

# Start the daemon
gated --port 8888

# Or use the daemon command
gate daemon --port 8888

# List available gates
gate list

# Execute a gate
gate run smoke --profile pr-fast

# Evaluate all gates for release
gate evaluate
```

## Architecture

The gate system consists of:

- **Daemon (`gated`)**: FastAPI service that orchestrates gate execution
- **SDK**: Base classes for implementing gate plugins
- **Plugins**: Individual gate implementations
- **CLI**: Client for interacting with the daemon

## Gate Plugins

| Gate | Severity | Description |
|------|----------|-------------|
| contract | warning | Contract compliance validation |
| smoke | blocker | Cross-layer smoke tests |
| arch | blocker | Architecture conformance |
| security | blocker | Security scanning |
| chaos | critical | Chaos engineering |
| agent | blocker | Agent evaluation |
| state | blocker | State consistency |
| obs | critical | Observability readiness |

## Plugin Development

Create a new gate by implementing the `GatePlugin` base class:

```python
from sdk.plugin import GatePlugin, GateContext
from sdk.models import GateSeverity, GateResult, CheckResult

class MyGate(GatePlugin):
    @property
    def gate_id(self) -> str:
        return "my_gate"
    
    @property
    def severity(self) -> GateSeverity:
        return GateSeverity.CRITICAL
    
    @property
    def expected_artifacts(self) -> list[str]:
        return ["my_gate/report.json"]
    
    def execute(self, ctx: GateContext) -> list[CheckResult]:
        # Run your checks
        return [
            CheckResult(
                name="my_check",
                result=GateResult.PASS,
                value=True,
                threshold=True,
                comparator="eq",
            )
        ]
```

## API Endpoints

- `GET /v1/health` - Health check
- `GET /v1/gates` - List gates
- `POST /v1/gates/{id}/execute` - Execute gate
- `GET /v1/gates/{id}/status/{execution_id}` - Get execution status
- `GET /v1/gates/{id}/artifacts` - Get artifacts
- `POST /v1/evaluate` - Evaluate all gates for release
- `POST /v1/manifest/sign` - Sign release manifest

## Configuration

Create `.fabric/gated.yaml`:

```yaml
daemon:
  bind_addr: 0.0.0.0
  port: 8888
  log_level: INFO
  artifact_store: ./artifacts
  max_concurrent_gates: 5

plugins:
  search_path:
    - scripts/gates/plugins/
    - packs/*/gates/
```
