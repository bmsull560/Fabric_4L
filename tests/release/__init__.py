"""Release policy gate tests.

These tests enforce release-readiness policies that must pass before a release-candidate
can be promoted. They inspect policy files, deprecation registers, and repository state
without reading secret values.

Design principles:
- Tests parse machine-readable policy/config files structurally
- Tests do not read secret values or real credentials
- Tests block release-candidate on P0/P1 violations
- Tests are self-documenting about what policy they enforce
"""
