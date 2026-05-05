# Operator Prerequisites

Production manifests depend on cluster-scoped operators that must be installed
before applying `k8s/envs/prod`.

Required install order:

1. CloudNativePG operator `1.25.0`, providing `clusters.postgresql.cnpg.io`.
2. Spotahome Redis Operator `1.3.0`, providing `redisfailovers.databases.spotahome.com`.
3. Apply `k8s/envs/prod` only after both CRDs are present.

Preflight checks:

```sh
kubectl get crd clusters.postgresql.cnpg.io
kubectl get crd redisfailovers.databases.spotahome.com
```
