# Testing

## Backend

### Run Tests

```bash
cd services/api
pip install -e .
pytest app/tests -v
```

### Test Coverage

- `test_health.py` - Health and metrics endpoints
- `test_accounts.py` - CRUD and summary
- `test_roi.py` - Deterministic ROI calculation and divide-by-zero safety
- `test_governance.py` - Review queue, gates, decisions
- `test_tenant_isolation.py` - Cross-tenant blocking
- `test_agents.py` - Run lifecycle (create, get, cancel)

## Frontend

### Run Tests

```bash
cd apps/web
npm install
npm run test
npm run check
```

### Test Strategy

- Vitest + React Testing Library
- Contract tests for API boundaries
- Component tests for UI primitives
- Accessibility scans

## Contract Tests

Frontend contract tests in `apps/web/src/api/__tests__/contract/` validate API shape compatibility.

## CI/CD

GitHub Actions workflows exist for:
- PR checks
- Security gates
- Smoke tests
- Contract compliance
