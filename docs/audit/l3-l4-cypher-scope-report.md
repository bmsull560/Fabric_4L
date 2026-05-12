# L3/L4 Cypher Scope Audit Report

This audit is produced by:

- `python scripts/ci/check_layer3_cypher_scope.py`

Machine-readable artifact:

- `docs/audit/l3-l4-cypher-scope-report.json`

Classification policy:

- **Safe**: query use is co-located with approved scoped query markers.
- **Unsafe**: known unsafe query construction patterns (inline f-string `session.run`, tenant interpolation, etc.).
- **Unknown**: query could not be proven safe from static analysis and must be explicitly listed in:
  - `config/production-readiness/l3-l4-cypher-unknown-allowlist.json`

CI behavior:

- Any **Unsafe** finding fails CI.
- Any **Unknown** finding missing explicit allowlist entry fails CI.
