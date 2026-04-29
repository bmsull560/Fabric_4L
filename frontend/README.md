# Frontend Development

## Package manager

This frontend uses **pnpm** as the canonical package manager.

- Use `pnpm-lock.yaml` as the single lockfile.
- Do not use `npm install` or commit `package-lock.json`.

## Quick start

```bash
cd frontend
pnpm install
pnpm dev
```

## Common commands

```bash
pnpm check
pnpm test
pnpm build
pnpm exec playwright test
```

## Accessibility testing and CI gates

Accessibility testing is split into two levels:

- **Component-level (Vitest):** `pnpm run test:a11y:components`
- **Page-level (Playwright + axe):** `pnpm run test:a11y:pages`
- **Threshold enforcement (CI gate):** `pnpm run test:a11y:gate`

The CI workflow `.github/workflows/pr-checks.yml` runs these checks in the Frontend job.
The page-level report is emitted as `frontend/a11y-report.json` during CI execution.
