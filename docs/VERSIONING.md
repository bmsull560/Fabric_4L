# Versioning and Release Policy

## Semantic Versioning

This project follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR** version (X.y.z): Incompatible API changes
- **MINOR** version (x.Y.z): Added functionality (backwards-compatible)
- **PATCH** version (x.y.Z): Backwards-compatible bug fixes

## Version Format

### Application Versions

```
<semver>-<git_sha>-<build_id>
```

Example: `1.4.2-a1b2c3d-20250415.3`

### Container Images

```
registry/org/service:<semver>-<sha>
```

Example: `ghcr.io/services/layer4-agents:1.4.2-a1b2c3d`

### Helm Charts

Chart version matches application version with strict schema validation.

## Release Cadence

| Environment | Trigger | Approval |
|-------------|---------|----------|
| **Development** | Auto-deploy on `main` merge | None |
| **Staging** | Promote from dev on RC tag | Automated (CI gate) |
| **Production** | Promote from staging | Manual + evidence bundle |

## Git Tagging

- All releases tagged: `v<semver>` (e.g., `v1.4.2`)
- Tags must be GPG-signed by release maintainer
- Annotated tags with changelog reference

## Changelog Generation

Changelogs generated from [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: new feature
fix: bug fix
docs: documentation
style: formatting
refactor: code restructuring
test: test additions
chore: maintenance
security: security fix (triggers patch release)
breaking: breaking change (triggers major release)
```

## Backward Compatibility

### Breaking Changes

- Require ADR (Architecture Decision Record)
- Require migration guide in `docs/migrations/`
- Require deprecation period (min 1 minor version)
- Contract tests must enforce compatibility

### Deprecation Process

1. Mark feature deprecated in code with `@deprecated`
2. Add deprecation notice to CHANGELOG
3. Log runtime warnings when deprecated feature used
4. Remove after minimum 1 major version cycle

## Release Checklist

- [ ] All tests pass (unit, integration, contract, e2e)
- [ ] Security scans clean (SAST/SCA/container)
- [ ] SBOMs generated and signed
- [ ] Provenance attestations created
- [ ] Changelog generated and reviewed
- [ ] Migration guide updated (if breaking changes)
- [ ] Git tag signed and pushed
- [ ] Container images signed with Cosign
- [ ] Helm charts signed and published
- [ ] Staging deployment validated
- [ ] Manual approval for production

## Build Identifiers

Immutable build identifiers ensure traceability:

| Component | Identifier | Source |
|-----------|-----------|--------|
| Git SHA | `a1b2c3d` | `git rev-parse --short HEAD` |
| Build ID | `20250415.3` | CI run number |
| Timestamp | `2025-04-15T10:30:00Z` | CI start time (UTC) |
| Builder | `github-actions` | CI platform |

## Emergency Releases

For critical security fixes:

1. Branch from latest release tag: `hotfix/v1.4.2-security`
2. Apply minimal fix with security test
3. Fast-track through CI (skip non-essential stages)
4. Expedited review (single security maintainer approval)
5. Deploy to production with automatic rollback on failure
6. Post-incident review within 48 hours

## Version API

Runtime version endpoint:

```
GET /health/version
{
  "version": "1.4.2-a1b2c3d-20250415.3",
  "semver": "1.4.2",
  "git_sha": "a1b2c3d",
  "build_id": "20250415.3",
  "build_time": "2025-04-15T10:30:00Z"
}
```

---

**Last Updated**: 2026-04-15
**Version**: 1.0.0
**Owner**: Platform Engineering
