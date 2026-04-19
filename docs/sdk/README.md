# Value Fabric Python SDK

Official Python SDK and CLI for the Value Fabric Platform.

## Installation

### From PyPI (Recommended)

```bash
pip install valuefabric
```

### From GitHub Packages

```bash
pip install valuefabric --index-url https://pypi.pkg.github.com/bmsull560
```

### From Source

```bash
git clone https://github.com/bmsull560/Fabric_4L.git
cd Fabric_4L/sdk/python
pip install -e ".[dev]"
```

## Quick Start

### CLI Usage

Check platform health:

```bash
vf health
```

Authenticate:

```bash
vf auth login
```

Search entities:

```bash
vf search "CRM integration" --entity-type Capability
```

Run a workflow:

```bash
vf workflows run business-case --input '{"account_id": "123", "capability_id": "cap-456"}'
```

### Python SDK Usage

```python
from valuefabric import Client

# Initialize client
client = Client(base_url="https://api.valuefabric.com")

# Authenticate
client.auth.login(username="user", password="pass")

# Check health
health = client.health()
print(f"Platform status: {health.status}")

# Search entities
results = client.search(
    query="CRM integration",
    entity_types=["Capability"],
    hybrid=True
)

# Run workflow
workflow = client.workflows.run(
    workflow_type="business-case",
    input_data={"account_id": "123"}
)
```

## Configuration

The SDK reads configuration from environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `VF_API_URL` | Base URL for Value Fabric API | `http://localhost:8004` |
| `VF_API_KEY` | API key for authentication | - |
| `VF_TENANT_ID` | Default tenant ID | - |
| `VF_TIMEOUT` | Request timeout in seconds | `30` |

## CLI Commands

| Command | Description |
|---------|-------------|
| `vf health` | Check API health status |
| `vf auth login` | Authenticate with credentials |
| `vf auth logout` | Clear authentication |
| `vf config show` | Display current configuration |
| `vf workflows list` | List available workflows |
| `vf workflows run` | Execute a workflow |
| `vf workflows status` | Check workflow status |
| `vf search` | Hybrid entity search |
| `vf models list` | List model registry entries |
| `vf feature-flags list` | List feature flags |
| `vf tenants list` | List accessible tenants |
| `vf users list` | List users |
| `vf api-keys list` | Manage API keys |

## Generated Client

The SDK includes auto-generated clients from OpenAPI specifications:

- **L3 Client** (`valuefabric.generated.l3_client`): Knowledge Graph API
- **L4 Client** (`valuefabric.generated.l4_client`): Agent Workflow API

These are used internally by the main `Client` class but can be accessed directly:

```python
from valuefabric.generated.l4_client import Client as L4Client

client = L4Client(base_url="http://localhost:8004")
workflows = client.workflows_list()
```

## Development

### Running Tests

```bash
cd sdk/python
pip install -e ".[dev]"
pytest tests/ -v
```

### Regenerating from OpenAPI

```bash
cd sdk/python
python scripts/generate_from_openapi.py
```

### Building Distribution

```bash
cd sdk/python
python -m build
```

## CI/CD Integration

The SDK is automatically regenerated when OpenAPI specs change:

1. `.github/workflows/regenerate-sdk.yml` - Regenerates SDK from OpenAPI specs
2. `.github/workflows/publish-sdk.yml` - Publishes to PyPI and GitHub Packages
3. `.github/workflows/build-deploy.yml` - Includes SDK generation in build pipeline

## Version Compatibility

| SDK Version | Platform Version | Python |
|-------------|------------------|--------|
| 0.1.x | 1.0.x | 3.10+ |

## License

Proprietary - See [LICENSE](../../LICENSE)

## Support

- Documentation: [docs.valuefabric.com](https://docs.valuefabric.com)
- Issues: [GitHub Issues](https://github.com/bmsull560/Fabric_4L/issues)
