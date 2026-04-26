# Routing Stack: Gateway API (EXPERIMENTAL)

> **Status: EXPERIMENTAL.** This routing variant is rendered and validated in CI
> but is **not** the default production deployment path. It depends on a
> cluster-installed Gateway API controller and CRDs that are not assumed to
> exist by the Value Fabric platform contract. Use `prod-nginx` for production.

## What this stack defines

- `gateway.networking.k8s.io/v1` `Gateway` with HTTP + HTTPS listeners for
  `__HOST__` (frontend) and `__API_HOST__` (layer APIs).
- `gateway.networking.k8s.io/v1` `HTTPRoute` resources binding listeners to
  Services rendered by the env overlay.
- cert-manager `Certificate` resources providing `frontend-tls` and `layer-apis-tls`.

This stack does **not** import `../../base`. It is composed under
`k8s/deployments/prod-gateway-api/`.

## Required cluster prerequisites

- Gateway API CRDs v1.0+ installed:
  ```bash
  kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
  ```
- A `GatewayClass` controller. The reference manifests assume `envoy-gateway`;
  swap in your controller's class name in `gateway.yaml` if different (e.g.
  `cilium`, `contour`, `istio`).
  - Envoy Gateway: https://gateway.envoyproxy.io/
- cert-manager v1.13+ with Gateway API support enabled (or use the Gateway shim).
- DNS A records for `__HOST__` and `__API_HOST__` pointing at the Gateway's
  external IP / LoadBalancer.

## Apply

```bash
kustomize build k8s/deployments/prod-gateway-api | kubectl apply -f -
```

## Validation

```bash
kustomize build k8s/deployments/prod-gateway-api | \
  kubeconform -strict -summary \
    -schema-location default \
    -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
    -

kubectl -n value-fabric get gateway,httproute,certificate
```

## Troubleshooting

- **Gateway `Programmed: False`**: verify the controller for `gatewayClassName` is installed and watching the namespace.
- **HTTPRoute `Accepted: False`**: backend Service does not exist or is in a different namespace; verify the env overlay rendered the matching Service.
- **Sentinel `__HOST__` visible in cluster**: deployment overlay's `replacements:` did not run.
