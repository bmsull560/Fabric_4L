# Fabric 4L Web Application

This is the canonical frontend application for the Fabric 4L platform.

## Location

`apps/web/` - The production frontend application root.

## Quick Start

```bash
cd apps/web
pnpm install
pnpm run dev
```

## Available Scripts

- `pnpm run dev` - Start development server
- `pnpm run build` - Build for production
- `pnpm run check` - TypeScript type checking
- `pnpm run test` - Run unit tests
- `pnpm run test:e2e` - Run Playwright E2E tests
- `pnpm run lint` - Run ESLint
- `pnpm run test:frontend-hygiene` - Enforce frontend hygiene checks (no merge markers, no direct route-string concatenation in React components, no stale cleanup-summary verification markers)

## Architecture

This application follows the enterprise SaaS architecture patterns defined in the Fabric 4L platform.

## Important Notes

- This is the **canonical** frontend location as of Phase 5 cleanup
- Previous location `frontend/client/` has been migrated here
- Do not import from `prototypes/` in production code


## Navigation and Route Hygiene

- Build links and navigation targets via centralized helpers (`useNavigation`, `getStatePath`, `resolveWorkspacePath`) instead of inline string concatenation in components.
- Avoid patterns such as `'/accounts/' + accountId` or `` `/accounts/${accountId}` `` directly inside React components; route assembly belongs in the navigation layer.
- CI enforces this with `pnpm run test:frontend-hygiene`, which also blocks unresolved merge-conflict markers in `src/**` and stale `claim not verified` notes in `FRONTEND_CLEANUP_SUMMARY.md`.
