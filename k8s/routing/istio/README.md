# Routing Stack: Istio (EXPERIMENTAL)

> **Status: EXPERIMENTAL.** This routing variant is rendered and validated in CI
> but is **NOT** production-ready. It depends on a cluster-installed Istio service mesh
> and lacks critical security controls. Use `prod-nginx` for production.

## What this stack defines

- Istio `Gateway` with HTTP→HTTPS redirect and TLS-terminated listeners for
  `__HOST__` (frontend) and `__API_HOST__` (layer APIs).
- `VirtualService` resources binding the gateway to Services rendered by the
  env overlay (path-prefixed `/layer1`..`/layer6`).
- `DestinationRule` resources with `ISTIO_MUTUAL` **(client-side mTLS only)**.

## Critical Security Gaps (NOT IMPLEMENTED)

### Server-Side mTLS: NOT ENFORCED

**WARNING**: `DestinationRule` with `mode: ISTIO_MUTUAL` configures the **client**
to use mTLS. It does **NOT** enforce that servers only accept mTLS connections.

To enforce server-side mTLS, you **must** add:
```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: value-fabric
spec:
  mtls:
    mode: STRICT
```

Without `PeerAuthentication`, plaintext connections are still accepted.

**Status**: NOT IMPLEMENTED. Add before production use.

### Edge Authentication: NOT IMPLEMENTED

No `AuthorizationPolicy` or `RequestAuthentication` configured. Options:
- **JWT Validation**: Use `RequestAuthentication` with JWKS endpoint
- **OAuth2/OIDC**: Use external auth service + `AuthorizationPolicy` header rules
- **mTLS-based**: Use `PeerAuthentication` + `AuthorizationPolicy` with source principals

**Status**: Documented pattern only. Production requires implementation.

### Rate Limiting: NOT IMPLEMENTED

Options:
- **Local rate limiting**: Envoy local rate limit filter
- **Global rate limiting**: Redis-backed rate limiting service
- **Mixer-less**: Use EnvoyFilter with rate limiting WASM

**Status**: Documented pattern only. Production requires implementation.

### Security Headers: NOT FULLY IMPLEMENTED

`DestinationRule` does not support response header manipulation. Requires:
- `EnvoyFilter` to inject security headers (HSTS, X-Frame-Options, etc.)
- OR application-layer header handling

### NetworkPolicy: NOT IMPLEMENTED

No hardened NetworkPolicy included. Must add:
- Allow from `istio-system` namespace only (for ingress gateway)
- Explicit ingress namespace selector

### CORS Enforcement: NOT IMPLEMENTED

Use `VirtualService` CORS policy or application-layer CORS handling.

### WAF / Input Validation: NOT IMPLEMENTED

No WAF at Istio layer. Requires:
- External WAF (Cloudflare, AWS WAF)
- OR custom Envoy WASM filters

## Production Readiness Checklist

Before promoting from EXPERIMENTAL:
- [ ] Add `PeerAuthentication` STRICT mode for server-side mTLS enforcement
- [ ] Implement edge authentication (`AuthorizationPolicy` + `RequestAuthentication`)
- [ ] Implement rate limiting (local or global)
- [ ] Add security headers via `EnvoyFilter` or application layer
- [ ] Harden NetworkPolicy (allow from `istio-system` only)
- [ ] Configure WAF or document external WAF prerequisite
- [ ] Validate TLS 1.0/1.1 rejection at ingress gateway
- [ ] Add CI gates for all security controls

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
