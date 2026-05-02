"""Chaos engineering tests for dependency failure scenarios.

These tests verify that the Value Fabric system fails closed or degrades safely
when external dependencies (Redis, DB, LLM, external APIs) become unavailable.

Design principles:
- Tests use monkeypatching to simulate failures without requiring live infrastructure
- Tests verify structured error responses, not just exceptions
- Tests ensure tenant isolation is maintained during degraded operation
- Tests ensure no fabricated success responses are returned
"""
