# Kubernetes Routing Security Hardening - Implementation Summary

**Date:** 2026-04-26
**Scope:** Edge authentication, rate limiting, TLS headers, NetworkPolicy hardening
**Status:** IMPLEMENTED

---

## Changes Implemented

### 1. Edge Authentication (oauth2-proxy)

**New Files:**
- `k8s/routing/nginx/oauth2-proxy.yaml` — Deployment, Service, NetworkPolicy
- `k8s/routing/nginx/routing-config.yaml` — Base ConfigMap for Kustomize replacements
- `k8s/deployments/prod-nginx/oauth2-proxy-config.yaml` — Prod OIDC settings
- `k8s/deployments/staging-nginx/oauth2-proxy-config.yaml` — Staging OIDC settings
- `k8s/external-secrets/oauth2-proxy-secrets.yaml` — ExternalSecret template

**Features:**
- Encrypted cookie sessions (no Redis)
- Headers passed: `X-Auth-Request-User`, `X-Auth-Request-Email`, `Authorization`
- Secrets from ExternalSecrets (not hardcoded)
- 2 replicas for HA

### 2. Ingress Security Annotations

**Modified:** `k8s/routing/nginx/ingress.yaml`

Added to both frontend and layer-apis Ingress:
- `nginx.ingress.kubernetes.io/auth-url` — oauth2-proxy auth endpoint
- `nginx.ingress.kubernetes.io/auth-signin` — Login redirect
- `nginx.ingress.kubernetes.io/auth-response-headers` — Identity headers
- `nginx.ingress.kubernetes.io/limit-rps` — 10 req/sec (frontend), 20 req/sec (API)
- `nginx.ingress.kubernetes.io/limit-rpm` — 100 req/min (frontend), 200 req/min (API)
- `nginx.ingress.kubernetes.io/limit-connections` — 5 (frontend), 10 (API)
- `configuration-snippet` with HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy

### 3. NetworkPolicy Hardening

**Modified:** `k8s/base/network-policies/frontend-policy.yml`

- Removed: `namespaceSelector: {}` (blanket ingress allowance)
- Added: `__INGRESS_NAMESPACE__` sentinel for Kustomize replacement
- Only explicitly whitelisted ingress controller namespace allowed

### 4. ClusterIssuer Email Fix

**Modified:** `k8s/routing/nginx/clusterissuer.yaml`
- Changed: `email: platform@example.com` → `email: __ISSUER_EMAIL__`

**Modified:** Deployment hostname-configs
- Added `ingressNamespace` and `issuerEmail` fields

### 5. Kustomization Updates

**Modified:**
- `k8s/routing/nginx/kustomization.yaml` — Added oauth2-proxy, routing-config
- `k8s/deployments/prod-nginx/kustomization.yaml` — Added replacements for auth, email, namespace
- `k8s/deployments/staging-nginx/kustomization.yaml` — Added replacements for auth, email, namespace

### 6. Documentation Updates

**Modified:**
- `k8s/routing/nginx/README.md` — Production-Supported status, security features documented
- `k8s/routing/gateway-api/README.md` — EXPERIMENTAL status, security gaps documented
- `k8s/routing/istio/README.md` — EXPERIMENTAL status, mTLS gap documented

### 7. CI Security Gates

**Modified:** `.github/workflows/k8s-readiness.yml`

Added validation steps:
- `Security checks - placeholder emails` — Fails if `platform@example.com` present
- `Security checks - oauth2-proxy placeholders` — Fails if `__OIDC_`, `CHANGE_ME`, etc. present
- `Security checks - rate limiting and HSTS` — Fails if missing from prod/staging nginx
- `Security checks - NetworkPolicy blanket ingress` — Fails if `namespaceSelector: {}` present

---

## Go/No-Go Matrix (After Implementation)

| Stack | Status | Notes |
|-------|--------|-------|
| **prod-nginx** | ✅ Production-Supported | oauth2-proxy auth, rate limiting, HSTS, hardened NetworkPolicy |
| **staging-nginx** | ✅ Production-Supported | Identical security posture to production |
| **dev-nginx** | ✅ Development-Supported | Same security pattern (may use dev IdP) |
| **Gateway API** | ⏸️ EXPERIMENTAL | Auth/rate limiting documented but NOT implemented |
| **Istio** | ⏸️ EXPERIMENTAL | Auth/mTLS documented but NOT implemented |

---

## Security Controls Summary

| Control | nginx-default | Gateway API | Istio | Status |
|---------|---------------|-------------|-------|--------|
| Edge Authentication | oauth2-proxy | NOT IMPLEMENTED | NOT IMPLEMENTED | nginx ✅ |
| Rate Limiting | 10-20 RPS | NOT IMPLEMENTED | NOT IMPLEMENTED | nginx ✅ |
| HSTS Headers | ✅ | NOT IMPLEMENTED | NOT IMPLEMENTED | nginx ✅ |
| X-Frame-Options | ✅ | NOT IMPLEMENTED | NOT IMPLEMENTED | nginx ✅ |
| Referrer-Policy | ✅ | NOT IMPLEMENTED | NOT IMPLEMENTED | nginx ✅ |
| NetworkPolicy (hardened) | ✅ | NOT IMPLEMENTED | NOT IMPLEMENTED | nginx ✅ |
| mTLS (server-side) | N/A | N/A | NOT ENFORCED | Experimental |
| WAF | External required | External required | External required | Documented |

---

## Required Production Prerequisites

Before deploying `prod-nginx` or `staging-nginx` to production:

1. **OIDC Provider configured** (Auth0, Okta, Keycloak, etc.)
2. **ExternalSecrets backend configured** (Vault, Azure KV, etc.)
3. **Ingress controller namespace known** (typically `ingress-nginx`)
4. **Valid issuer email** (not `platform@example.com`)
5. **DNS A records** pointing to LoadBalancer IP
6. **DNSSEC enabled** at DNS provider
7. **External WAF** (Cloudflare, AWS WAF) OR ModSecurity in NGINX controller

---

## CI Gates

The following checks will FAIL the build if violations detected:

1. ❌ Placeholder emails (`platform@example.com`) in prod/staging
2. ❌ Placeholder auth values (`__OIDC_*`, `CHANGE_ME`) in prod/staging
3. ❌ Missing rate limiting annotations in prod/staging nginx
4. ❌ Missing HSTS headers in prod/staging nginx
5. ❌ Blanket namespace ingress (`namespaceSelector: {}`) in any manifest

---

## Deferred to Future Slices

These items were intentionally NOT implemented in this slice:

1. **Redis-backed sessions** — Documented as follow-up for centralized revocation
2. **Gateway API auth** — Requires controller-specific implementation
3. **Istio mTLS STRICT** — Requires `PeerAuthentication` resource
4. **ModSecurity WAF** — Requires NGINX controller ConfigMap changes
5. **CSP (Content Security Policy)** — Requires app-layer coordination

---

## Verification Commands

```bash
# Render and validate nginx (no external dependencies required)
kustomize build k8s/deployments/prod-nginx --load-restrictor=LoadRestrictionsNone | \
  kubeconform -strict -summary -

# Check for placeholder emails
grep -r "platform@example.com" /tmp/k8s-renders/prod*.yaml || echo "OK: No placeholders"

# Check for rate limiting
grep "limit-rps" /tmp/k8s-renders/prod-nginx.yaml || echo "FAIL: Missing rate limiting"

# Check for HSTS
grep "Strict-Transport-Security" /tmp/k8s-renders/prod-nginx.yaml || echo "FAIL: Missing HSTS"

# Check for blanket ingress
grep -A1 'namespaceSelector:' /tmp/k8s-renders/prod-nginx.yaml | grep '{}' && \
  echo "FAIL: Blanket ingress found" || echo "OK: No blanket ingress"
```

---

## Acceptance Criteria Status

- [x] `prod-nginx` and `staging-nginx` are production-supported with auth, rate limiting, TLS, headers, NetworkPolicy
- [x] `staging-nginx` is a true production mirror (identical auth pattern, no security degradation)
- [x] No rendered supported deployment contains `platform@example.com`
- [x] No supported deployment allows ingress from every namespace (`namespaceSelector: {}`)
- [x] `nginx-default` has HSTS and rate limiting in rendered output
- [x] oauth2-proxy deployed with encrypted cookie sessions only (no Redis)
- [x] Secrets not hardcoded in manifests; placeholder auth values fail CI
- [x] Gateway API and Istio remain experimental with documented security gaps
- [x] No backend services (Layer1-L6) exposed via external routes
- [x] Security expectations documented in each routing README
