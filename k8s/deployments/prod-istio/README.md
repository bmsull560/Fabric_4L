# Deployment: prod-istio (EXPERIMENTAL)

> **Status: EXPERIMENTAL.** Render-only in CI. Requires Istio service mesh that
> is not assumed by the Value Fabric platform contract. Use `prod-nginx` for
> production.

Composes `envs/prod` + `routing/istio`.

## Apply (operator opt-in)

```bash
# Install Istio and label the namespace for sidecar injection first.
kustomize build k8s/deployments/prod-istio | kubectl apply -f -
```

## Hosts

| Field | Value |
|---|---|
| Frontend host | `app.value-fabric.example.com` |
| API host | `api.value-fabric.example.com` |

## Render-only validation

```bash
kustomize build k8s/deployments/prod-istio | kubeconform -strict -summary \
  -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  -
```

## Required cluster prerequisites

See `k8s/routing/istio/README.md`.
