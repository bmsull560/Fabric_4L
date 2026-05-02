# Frontend Directory - OBSOLETE

**Status:** This directory is obsolete and should not be used for development.

**Canonical Frontend Root:** `apps/web/`

**Migration Date:** 2026-05-02

**Reason for Obsolescence:**
The frontend has been migrated from `frontend/client` to `apps/web` as part of Phase 5 frontend move. All active development now occurs in `apps/web`.

**Contents:**
- This directory contains legacy frontend artifacts from the pre-migration structure
- No active development should occur in this directory
- Files here are retained for reference only and may be removed in a future cleanup

**For Development:**
- Use `apps/web/` for all frontend development
- Run `cd apps/web && pnpm install` to install dependencies
- Run `cd apps/web && pnpm dev` to start the development server

**Scripts Updated:**
The following scripts have been updated to use `apps/web` instead of `frontend/client`:
- `scripts/extract-routes-audit.py`
- `scripts/check_ui_duplicate_filenames.py`
- `scripts/check-route-audit-freshness.py`
- `scripts/analyze-hooks-audit.py`
- `scripts/ci/check_navigation_patterns.py`

**CI/Makefile:**
- Makefile and GitHub workflows have been updated to reference `apps/web`
- No active CI/Makefile targets reference `frontend/client`
