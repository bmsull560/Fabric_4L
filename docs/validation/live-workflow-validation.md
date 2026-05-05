# Live Workflow Validation

`docker-compose.live.yml` is the canonical local/Bunnyshell live validation stack for Fabric_4L. It combines the frontend with the full backend-integrated L1-L6 stack so Playwright can exercise real user workflows against live services instead of mocked or partial environments.

## Purpose

- Keep [docker-compose.backend-integrated.yml](/workspaces/Fabric_4L/docker-compose.backend-integrated.yml) as the backend-only validation stack.
- Keep [docker-compose.release-smoke.yml](/workspaces/Fabric_4L/docker-compose.release-smoke.yml) as the release-smoke backend stack.
- Keep [docker-compose.dev.yml](/workspaces/Fabric_4L/docker-compose.dev.yml) as the partial developer stack.
- Keep [docker-compose.e2e.yml](/workspaces/Fabric_4L/docker-compose.e2e.yml) as the deterministic minimal Playwright backend.
- Use [docker-compose.live.yml](/workspaces/Fabric_4L/docker-compose.live.yml) for live workflow validation and Bunnyshell imports.

## Stack Contents

- Frontend: `frontend` from `apps/web`
- Backend layers: `layer1`, `layer1-worker`, `layer2`, `layer3`, `layer4`, `layer5`, `layer5-migrate`, `layer6`
- Backing stores: `postgres`, `redis`, `neo4j`, `minio`, `minio-init`
- Optional seed service: `live-seed` under the `seed` profile

## Frontend Runtime

The frontend runs its existing Vite dev server on container port `3001` and is published on host port `3001` for live validation.

- Public frontend URL: `http://localhost:3001`
- Internal frontend health URL: `http://frontend:3001`

The Vite proxy is configured to route live API traffic to Docker service names inside the live stack.

Important:

- This repo still uses `VITE_API_BASE` for the browser path prefix.
- `VITE_API_BASE_URL` is now supported as the Layer 4 proxy target override and defaults to `http://localhost:8004` for local development.
- `VITE_USE_MOCKS` is forced to `false` in the live stack.
- `VITE_ENABLE_MOCK_FALLBACK` is forced to `false` in the live stack.

## Ports

Published host ports for live validation:

- Frontend: `3001 -> 3001`
- Layer 4: `8004 -> 8000`

Internal-only services in `docker-compose.live.yml`:

- Layer 1
- Layer 2
- Layer 3
- Layer 5
- Layer 6
- postgres
- redis
- neo4j
- minio
- minio-init

## Start The Live Stack

From repo root:

```bash
docker compose -f docker-compose.live.yml config
docker compose -f docker-compose.live.yml up -d
docker compose -f docker-compose.live.yml ps
```

## Health Verification

```bash
curl http://localhost:5173
curl http://localhost:3001
curl http://localhost:8004/health
```

Layer 1, Layer 2, Layer 3, Layer 5, and Layer 6 remain internal in the live stack. If you need to inspect them locally, either use `docker compose exec` inside the network or temporarily add debug port mappings.

## Seed Path

Manual live seed from the frontend workspace:

```bash
cd apps/web
PLAYWRIGHT_BACKEND_URL=http://localhost:8004 pnpm run seed:e2e
```

Or use the compose one-off service:

```bash
docker compose -f docker-compose.live.yml --profile seed run --rm live-seed
```

The seed path is intended to create or reconcile the live validation tenant and deterministic test actors, including:

- admin user
- sales user
- reviewer user
- read-only user
- prospect account
- value pack
- evidence
- benchmarks
- formulas
- approval/export-safe test state

The seed service is not started automatically.

## Playwright Live Commands

From `apps/web`:

```bash
PLAYWRIGHT_LIVE_MODE=true \
PLAYWRIGHT_LIVE_FRONTEND_URL=http://localhost:3001 \
PLAYWRIGHT_BACKEND_URL=http://localhost:8004 \
pnpm run test:e2e:live:p0
```

Available scripts in [apps/web/package.json](/workspaces/Fabric_4L/apps/web/package.json):

- `test:e2e:live`
- `test:e2e:live:p0`
- `test:e2e:live:golden-path`

These scripts map the live URLs into the existing Playwright contract using:

- `PLAYWRIGHT_BASE_URL`
- `PLAYWRIGHT_BACKEND_URL`

They fail closed if any of these are missing:

- `PLAYWRIGHT_LIVE_MODE`
- `PLAYWRIGHT_LIVE_FRONTEND_URL`
- `PLAYWRIGHT_BACKEND_URL`

## Bunnyshell Usage

Import [docker-compose.live.yml](/workspaces/Fabric_4L/docker-compose.live.yml) into Bunnyshell for live workflow validation.

Bunnyshell should detect:

- `frontend`
- `layer1`
- `layer1-worker`
- `layer2`
- `layer3`
- `layer4`
- `layer5`
- `layer5-migrate`
- `layer6`
- `postgres`
- `redis`
- `neo4j`
- `minio`
- `minio-init`

If Playwright is running outside the Bunnyshell environment, override with the public URLs exposed by Bunnyshell rather than Docker-internal names:

- `PLAYWRIGHT_LIVE_FRONTEND_URL=https://<frontend-public-url>`
- `PLAYWRIGHT_BACKEND_URL=https://<layer4-public-url>`

Browser traffic should still go through the frontend public URL so the Vite proxy can route requests to the live backend services.

## Required Environment Variables

Frontend live stack settings:

```env
VITE_API_BASE=/api/v1
VITE_API_BASE_URL=http://layer4:8000
```

Local development fallback remains:

```env
VITE_API_BASE_URL=http://localhost:8004
```

Playwright live validation settings:

```env
PLAYWRIGHT_LIVE_MODE=true
PLAYWRIGHT_LIVE_FRONTEND_URL=http://localhost:3001
PLAYWRIGHT_BACKEND_URL=http://localhost:8004
```

## PASS / FAIL / BLOCKED Rules

- `PASS`: compose resolves, the required services become healthy, seed succeeds if invoked, and the targeted Playwright live suite completes without failures.
- `FAIL`: compose resolves but one or more required services, seed steps, or Playwright live tests fail.
- `BLOCKED`: compose foundation exists, but runtime health validation or Playwright live execution was not performed or could not be completed in the current environment.

## Validation Report

| Check | Result |
| --- | --- |
| compose config valid | Pending runtime validation command |
| frontend included | Yes |
| L1–L6 included | Yes |
| backing stores included | Yes |
| frontend port | 3001 |
| Vite proxy env-driven | Yes |
| local dev fallback preserved | Yes |
| health checks defined | Yes |
| seed path documented | Yes |
| Playwright live command documented | Yes |
| runtime health validation | Blocked |
| Playwright live execution | Blocked |
| Bunnyshell import target | `docker-compose.live.yml` |

## Scope Note

This setup creates the live stack required to run validation. It does not imply that live workflows already pass.
