# Zero Trust Validation Summary

Generated: 2026-04-14T11:20:35Z

- [pass] ZT-1.1 default deny policy exists — deny-all policy found
- [pass] ZT-1.2 kustomization includes deny-all — deny-all.yml referenced
- [pass] ZT-1.3 layer allowlist policies present — all expected per-layer policies exist
- [pass] ZT-2.1 tenant isolation primitives — TenantScopedMixin/TenantScopedCypher/tenant_cache_key found
- [pass] ZT-2.2 identity-to-tenant resolution path — middleware tenant resolution controls found
- [pass] ZT-2.3 tenant claim negative tests exist — jwt tests cover invalid tenant claim paths
- [pass] ZT-3.1 service authn paths — Bearer + API key support found
- [pass] ZT-3.2 authz dependency controls — role/permission checks found
- [pass] ZT-3.3 strong JWT secret policy — JWT secret enforcement found

Totals: pass=9, fail=0
