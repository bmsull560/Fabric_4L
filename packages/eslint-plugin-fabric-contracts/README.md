# eslint-plugin-fabric-contracts

ESLint plugin enforcing [Fabric 4L Canonical Contracts](../../contract.md).

## Installation

```bash
npm install --save-dev eslint-plugin-fabric-contracts
```

## Configuration

Add to your `.eslintrc.js`:

```javascript
module.exports = {
  plugins: ["fabric-contracts"],
  extends: ["plugin:fabric-contracts/recommended"],
};
```

## Rules

This plugin enforces 6 canonical contracts through 12 ESLint rules:

### 1. Tenant Isolation Boundary (§2.1)

| Rule | Description |
|------|-------------|
| `no-tenant-id-parameter` | Disallow tenantId as function parameters |
| `no-req-tenant-access` | Disallow direct req.headers access outside middleware |
| `no-raw-tenant-query` | Disallow raw SQL with tenant_id outside migrations |

### 2. Database Session Boundary (§2.2)

| Rule | Description |
|------|-------------|
| `no-explicit-db-connect` | Disallow explicit db.connect() with tenant identifiers |

### 3. Tool Invocation Boundary (§2.4)

| Rule | Description |
|------|-------------|
| `no-inline-middleware` | Disallow inline middleware (app.use outside pipeline) |
| `no-inline-tool-definition` | Disallow tool definitions outside tools/ directory |
| `no-throw-in-tool` | Disallow throw in tools - use error() helper |

### 4. LLM Output Handling (§2.5)

| Rule | Description |
|------|-------------|
| `no-json-parse-agent-output` | Disallow JSON.parse() on LLM outputs |

### 5. UI State Management (§2.6)

| Rule | Description |
|------|-------------|
| `no-imperative-navigation` | Disallow router.push(), history.push() |
| `no-url-concatenation` | Disallow URL string concatenation |

### 6. Public API Surface (§2.7)

| Rule | Description |
|------|-------------|
| `no-private-imports` | Disallow deep imports bypassing public API |
| `no-circular-dependencies` | Disallow circular dependencies |

## Presets

- `plugin:fabric-contracts/recommended` - All rules enabled
- `plugin:fabric-contracts/service-backend` - Backend-appropriate rules
- `plugin:fabric-contracts/service-frontend` - Frontend-appropriate rules

## See Also

- [Fabric 4L Contract](../../contract.md) - Full canonical contract specification
- [DEPRECATIONS.md](../../DEPRECATIONS.md) - Deprecated patterns and migration guides
