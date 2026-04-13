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

- **No secrets in code.** All credentials use environment variables. See `value-fabric/.env.example`.
- **API keys use HMAC-SHA256** (not bcrypt) for throughput; bcrypt is reserved for user passwords.
- **JWT tokens** are short-lived and signed with `JWT_SECRET`.
- **Audit logs** are append-only and protected by a database trigger that prevents UPDATE/DELETE.
- **RBAC** is enforced via `GovernanceMiddleware` in `value-fabric/shared/identity/`.
- **CI uses short-lived OIDC credentials** — no long-lived secrets stored in GitHub Actions.

## Dependency management

Dependabot is configured (`.github/dependabot.yml`) to automatically open PRs for
dependency updates across Python, Node, and GitHub Actions ecosystems. All dependency
updates go through the standard PR review and CI gate process.
