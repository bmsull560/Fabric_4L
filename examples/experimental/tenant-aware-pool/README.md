# Tenant-Aware Connection Pool (Experimental)

> **Status:** Experimental — non-blocking, cannot be cited as enforced canon.

This directory is reserved for future exploration of tiered tenant isolation using
dedicated schemas or dedicated database instances per tenant. The current **Enforced
Canon** for tenant isolation is PostgreSQL Row-Level Security via `SET LOCAL app.tenant_id`,
as ratified in `contract.md` Section 2.2 (2026-04-25).

## Background

The original platform contract specified a `TenantAwarePool` that would route
connections based on tenant tier (shared / dedicated schema / dedicated database).
After evaluation, the team ratified shared-schema RLS as the canonical pattern
because it covers 100% of current tenants with the simplest operational model.

## When This Becomes Relevant

Tiered isolation may be revisited if:

- A tenant requires regulatory data residency in a separate database.
- Performance isolation demands exceed what RLS + connection pooling can provide.
- The platform scales beyond ~500 tenants on a single PostgreSQL cluster.

## Checklist

- [ ] Performance benchmark vs RLS
- [ ] Connection overhead analysis
- [ ] Migration milestone set

## Governance Rule

> Experimental examples are non-blocking and cannot be cited as enforced canon.
> Code in this directory is not subject to contract-compliance CI gates.
> Sunset rule: If no active migration milestone within 12 months, this proposal
> is demoted to "Rejected Alternatives" and removed.

## Owner

Platform Engineering
