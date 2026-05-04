# Threat Model

Value Fabric threat model covering multi-tenant SaaS attack surfaces.

For full details, see:

- [Security Model](docs/core-concepts/security-model.md)
- [Multi-Tenancy Security](docs/security/multi-tenancy.md)
- [SECURITY.md](SECURITY.md)
- [Compliance Controls](docs/compliance/control-matrix.md)

## Key Threat Categories

1. **Cross-Tenant Data Leakage** — Mitigated by PostgreSQL RLS on all tables
2. **Authentication Bypass** — JWT + API key dual-auth via GovernanceMiddleware
3. **LLM Prompt Injection** — Input validation via SecurityMiddleware
4. **Credential Exposure** — Vault integration, ExternalSecrets Operator
5. **Supply Chain** — SLSA provenance, Dependabot, Trivy scanning
