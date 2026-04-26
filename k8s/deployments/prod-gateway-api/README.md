# Deployment: prod-gateway-api (EXPERIMENTAL)

> **Status: EXPERIMENTAL.** Render-only in CI. Requires cluster-specific Gateway
> API controller and CRDs that are not assumed by the Value Fabric platform
> contract. Use `prod-nginx` for production.

Composes `envs/prod` + `routing/gateway-api`.

## Apply (operator opt-in)

```bash
# Install Gateway API CRDs and a controller (e.g. Envoy Gateway) first.
kustomize build k8s/deployments/prod-gateway-api | kubectl apply -f -
```

## Hosts

| Field | Value |
|---|---|
| Frontend host | `app.value-fabric.example.com` |
| API host | `api.value-fabric.example.com` |

## Render-only validation

```bash
kustomize build k8s/deployments/prod-gateway-api | kubeconform -strict -summary \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  -
```

## Required cluster prerequisites

See `k8s/routing/gateway-api/README.md`.
