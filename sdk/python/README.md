# Value Fabric Python SDK

Python SDK and CLI for the [Value Fabric](https://github.com/bmsull560/Fabric_4L) Layer 4 Agentic Workflow Engine.

## Installation

```bash
pip install valuefabric-sdk
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

# Get JSON output
vf tenants list --json
```

## Development

```bash
cd sdk/python
pip install -e ".[dev]"
pytest
```

## License

See the repository root `LICENSE` file.
