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

## Architecture

This application follows the enterprise SaaS architecture patterns defined in the Fabric 4L platform.

## Important Notes

- This is the **canonical** frontend location as of Phase 5 cleanup
- Previous location `frontend/client/` has been migrated here
- Do not import from `prototypes/` in production code
