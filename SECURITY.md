# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| Latest on `main` | ✅ |
| Tagged releases (last 2 minor versions) | ✅ |
| Older versions | ❌ |

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report security issues privately:

1. Go to the repository's **Security** tab → **Report a vulnerability**, or
2. Email the maintainer directly (see GitHub profile).

Please include:

- A description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept (if safe to share)
- Affected versions or components
- Any suggested mitigations (optional)

## Response timeline

| Stage | Target |
|-------|--------|
| Acknowledgement | Within 48 hours |
| Initial assessment | Within 5 business days |
| Patch or mitigation | Within 30 days for critical/high; 90 days for medium/low |
| Public disclosure | Coordinated with reporter after patch is available |

## Security design principles

- **No secrets in code.** All credentials use environment variables. See `.env.example`.
- **JWT secret policy is environment-aware.** `JWT_SECRET` may use a local fallback only in
  development/test-like environments (`ENVIRONMENT`/`APP_ENV` of `dev`, `development`,
  `local`, `test`, `testing`, or `ci`). In non-dev environments, startup hard-fails if
  `JWT_SECRET` is unset/empty or left as `changeme-in-production`.
- **API keys use HMAC-SHA256** (not bcrypt) for throughput; bcrypt is reserved for user passwords.
- **JWT tokens** are short-lived and support `HS256`, `RS256`, or `ES256` with `kid` headers.
- **Key rotation** supports active + previous key verification (`JWT_ACTIVE_KID`, `JWT_PREVIOUS_KID`) during rollout windows.
- **Asymmetric mode** uses `JWT_PRIVATE_KEY_PEM` for signing and `JWT_PUBLIC_KEY_PEM`/`JWT_PREVIOUS_PUBLIC_KEY_PEM` for verification and JWKS discovery.
- **Audit logs** are append-only and protected by a database trigger that prevents UPDATE/DELETE.
- **RBAC** is enforced via `GovernanceMiddleware` in `packages/shared/src/value_fabric/shared/identity/`.
- **CI uses short-lived OIDC credentials** — no long-lived secrets stored in GitHub Actions.

## Dependency management

Dependabot is configured (`.github/dependabot.yml`) to automatically open PRs for
dependency updates across Python, Node, and GitHub Actions ecosystems. All dependency
updates go through the standard PR review and CI gate process.

## SBOM policy

- CI generates a **CycloneDX SBOM** for every service/frontend container build in
  `.github/workflows/security-gates.yml`.
- SBOM files are uploaded as GitHub Actions artifacts (`sbom-<layer>`).
- The pipeline is gated to fail if SBOM generation or artifact upload fails.
