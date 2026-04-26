# Routing Stack: Istio (EXPERIMENTAL)

> **Status: EXPERIMENTAL.** This routing variant is rendered and validated in CI
> but is **not** the default production deployment path. It depends on a
> cluster-installed Istio service mesh that is not assumed to exist by the
> Value Fabric platform contract. Use `prod-nginx` for production.

## What this stack defines

- Istio `Gateway` with HTTP→HTTPS redirect and TLS-terminated listeners for
  `__HOST__` (frontend) and `__API_HOST__` (layer APIs).
- `VirtualService` resources binding the gateway to Services rendered by the
  env overlay (path-prefixed `/layer1`..`/layer6`).
- `DestinationRule` resources enforcing automatic mTLS (`ISTIO_MUTUAL`) and
  setting connection-pool / outlier-detection defaults.

This stack does **not** import `../../base`. It is composed under
`k8s/deployments/prod-istio/`.

## Required cluster prerequisites

- **Istio** 1.20+ installed (https://istio.io/latest/docs/setup/install/).
- The `value-fabric` namespace labeled for sidecar injection:
  ```bash
  kubectl label namespace value-fabric istio-injection=enabled
  ```
- TLS Secrets `frontend-tls` and `layer-apis-tls` present **in the
  `istio-system` namespace** (Istio Gateway requirement). Operators typically
  use cert-manager with the `istio-csr` integration or sync Secrets across
  namespaces.
- DNS A records for `__HOST__` and `__API_HOST__` pointing at the
  `istio-ingressgateway` external IP / LoadBalancer.

## Apply

```bash
kustomize build k8s/deployments/prod-istio | kubectl apply -f -
```

## Validation

```bash
kustomize build k8s/deployments/prod-istio | \
  kubeconform -strict -summary \
    -schema-location default \
    -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
    -

kubectl -n value-fabric get gateway,virtualservice,destinationrule
istioctl analyze -n value-fabric
```

## Troubleshooting

- **503 from gateway**: VirtualService backend Service may not exist or be in
  a different namespace. `istioctl proxy-config routes <ingressgateway-pod>`.
- **TLS handshake failure**: `frontend-tls` / `layer-apis-tls` Secrets must be
  in `istio-system`, not `value-fabric`.
- **Sidecar not injected**: namespace label missing or pods predate label.
- **Sentinel `__HOST__` visible in cluster**: deployment overlay's
  `replacements:` did not run.
