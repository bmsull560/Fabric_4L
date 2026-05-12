# Contributor Dependency Workflows Reference

This reference maps the approved dependency workflows across the monorepo and explains the lockfile guardrails enforced in pre-commit and CI.

## JavaScript / TypeScript workspaces (pnpm only)

Use **pnpm** for all workspace package management.

### Canonical commands

```bash
corepack enable
corepack prepare pnpm@10.18.1 --activate
pnpm install --frozen-lockfile
pnpm --dir apps/web install --frozen-lockfile
```

### Prohibited commands

Do not run `npm install`, `npm ci`, or `yarn install` in this repository.

### Canonical lockfiles

- `pnpm-lock.yaml` (repo root)
- `apps/web/pnpm-lock.yaml`

## Python services (uv + service-local tooling)

Each maintained Python service follows a service-local dependency boundary. Use `uv` with service-local `pyproject.toml` / `uv.lock` as the source of truth.

### Canonical lockfiles

- `services/layer1-ingestion/uv.lock`
- `services/layer2-extraction/uv.lock`
- `services/layer3-knowledge/uv.lock`
- `services/layer4-agents/uv.lock`
- `services/layer5-ground-truth/uv.lock`
- `services/layer6-benchmarks/uv.lock`

### Recommended workflow pattern

```bash
cd services/<layer-service>
uv sync
uv lock
```

Use service-specific tooling (for example, `pytest`, layer Make targets, or service scripts) after syncing dependencies.

## Guardrails: lockfile policy enforcement

Lockfile policies are enforced by `scripts/ci/check_package_manager_policy.mjs`.

The guard rejects:

1. Any changed `package-lock.json` or `yarn.lock` file.
2. Any changed `pnpm-lock.yaml` or `uv.lock` outside approved paths.

Approved lockfile churn paths are intentionally narrow to prevent accidental cross-workspace dependency drift.

## Where the guard runs

- **CI**: `pnpm run check:package-manager-policy`
- **pre-commit**: local hook `package-manager-and-lockfile-policy`
