## Summary

- Describe what changed and why.

## Change Type

- [ ] Feature
- [ ] Bug fix
- [ ] Documentation
- [ ] Refactor/maintenance

## Release & Policy Checklist (Required)

- [ ] If API behavior/contracts changed, I updated `contracts/openapi/` and/or `contracts/jsonschema/`.
- [ ] If API changes are breaking, I created/updated a major version and included migration guidance.
- [ ] If deprecating APIs, I documented deprecation start and sunset dates per `docs/api-versioning-policy.md`.
- [ ] I reviewed DR expectations in `docs/reliability/dr-policy.md` and updated recovery docs if service criticality changed.
- [ ] For resilience-impacting changes, I updated or validated DR runbooks in `docs/runbooks/`.

## Validation

- [ ] `make verify`
- [ ] `make evals` (required for agent/skill prompt changes)

## Risks / Rollback

- Known risks:
- Rollback plan:
