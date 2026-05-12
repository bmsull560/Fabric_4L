# Alerting / Alertmanager Source-of-Truth Matrix

This runbook defines the **authoritative edit paths** for alerting by environment.
Only these paths should be edited directly.

## Canonical per environment

| Environment | Alertmanager source of truth | Prometheus alert rules source of truth |
|---|---|---|
| Dev | `monitoring/alertmanager/alertmanager.yml` | `monitoring/alerting/rules.yml` |
| Staging | `monitoring/alertmanager/alertmanager-enhanced.yml` | `monitoring/alerting/rules.yml` |
| Prod | `monitoring/alertmanager/alertmanager-production.yml` | `monitoring/alerting/rules-production.yml` |

## Alternates (non-authoritative)

- `monitoring/alerting/alertmanager.yml` — **deprecated** legacy duplicate path. Do not edit.
- `k8s/monitoring-alertmanager.yml` — **derived compatibility manifest**. Regenerate from `k8s/base/monitoring-alertmanager.yml`; do not hand edit.
- `k8s/alertmanager.yml` — **deprecated** and blocked in CI.

## CI enforcement

- `scripts/ci/check_deprecated_alertmanager_manifest.py` fails when deprecated manifests reappear.
- The same check blocks PRs that edit non-authoritative duplicates unless the regeneration signal file is also changed.

## Regeneration expectation

When you intentionally regenerate compatibility artifacts, include the regeneration command/script update in the same PR so CI can verify intent.
