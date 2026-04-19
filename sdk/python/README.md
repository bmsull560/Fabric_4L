# Value Fabric Python SDK

[![PyPI](https://img.shields.io/pypi/v/valuefabric)](https://pypi.org/project/valuefabric/)

Python SDK and CLI for the [Value Fabric](https://github.com/bmsull560/Fabric_4L) Layer 4 Agentic Workflow Engine.

## Installation

```bash
pip install valuefabric
```

## Quick Start

### Python SDK

```python
from valuefabric import ValueFabricClient

# Authenticate with an API key
client = ValueFabricClient(
    base_url="https://api.valuefabric.io",
    api_key="vf_your_api_key",
)

# List tenants
for tenant in client.list_tenants():
    print(tenant.name)

# Invite a user
user = client.invite_user("alice@example.com", role="analyst")
print(user.id)

# Execute a workflow
result = client.execute_workflow(
    workflow_type="roi_calculator",
    tenant_id="tenant-001",
    user_id="user-001",
)
print(result["workflow_instance_id"])
```

### JWT Authentication

```python
client = ValueFabricClient(
    base_url="https://api.valuefabric.io",
    jwt_token="eyJhbG...",
)
```

### Async Support

All SDK methods have an async counterpart prefixed with `a`:

```python
import asyncio

async def main():
    async with ValueFabricClient(base_url="...", api_key="...") as client:
        tenants = await client.alist_tenants()
        print(tenants)

asyncio.run(main())
```

## CLI

Install the SDK to get the `vf` command:

```bash
# Configure credentials
vf config set-url https://api.valuefabric.io
vf config set-api-key vf_your_api_key

# Health check
vf health

# List tenants
vf tenants list

# Invite a user
vf users invite alice@example.com --role analyst

# Execute a workflow
vf workflows execute roi_calculator --tenant-id t1 --user-id u1

# List feature flags
vf feature-flags list

# Search entities (hybrid: BM25 + vector + graph)
vf search "AI platform" --limit 5

# Search with entity type filter
vf search "machine learning" --type Capability

# Get JSON output
vf tenants list --json
vf search "query" --json
```

## Generated Clients

The SDK includes auto-generated clients from OpenAPI specifications:

```python
from valuefabric.generated import L3Client, L4Client
from valuefabric.generated.l3 import SearchRequest

# L3 Knowledge Graph client
l3 = L3Client(base_url="http://localhost:8001", api_key="your-key")
response = l3.search(SearchRequest(query="AI platform"))

# L4 Agents client  
l4 = L4Client(base_url="http://localhost:8000", api_key="your-key")
health = l4.health()
```

## Regenerating from OpenAPI

```bash
cd sdk/python
python scripts/generate_from_openapi.py
```

## Development

```bash
cd sdk/python
pip install -e ".[dev]"
pytest
```

## License

See the repository root `LICENSE` file.
