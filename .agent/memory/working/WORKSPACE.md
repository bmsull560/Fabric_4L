# Workspace (live task state)

## Current task
PR 375 remediation: fix Layer 2 tenant propagation/job-store compatibility and the auth `uuid` runtime error.

## Status
In progress. Source changes applied; validation narrowed to file-level analyzer checks.

## What was done
- Added the missing `uuid` import in `services/api/app/routers/auth.py`
- Made `services/layer2-extraction/src/layer2_extraction/integration/job_store.py` compatible with the SSE tests (`set`/`get`/`delete`, optional `source_url`, `created_at`)
- Tightened `build_job_store()` to fail closed in production without `REDIS_URL`
- Threaded `tenant_id` through the Layer 2 extraction pipeline and job mutation helper
- Added tenant-aware artifact reads and job deletion cleanup
- Fixed the SSE test async-fixture annotation and the Redis ping type narrowing in Layer 2

## Next step
Review remaining analyzer noise from third-party stub gaps only if it blocks the PR review flow.
