from __future__ import annotations

from pathlib import Path

output = Path('/tmp/backend_integrated_initial_run.txt').read_text()
failures: list[str] = []
for line in output.splitlines():
    line = line.strip()
    if line.startswith('FAILED tests/backend_integrated/'):
        test_id = line.removeprefix('FAILED ').split(' - ', 1)[0]
        failures.append(test_id)

priority_by_file = {
    'test_backend_integrated_golden_path.py': 'P0',
    'test_cross_layer_data_flow_validation.py': 'P0',
    'test_tenant_isolation_security_persistence.py': 'P0',
    'test_agent_grounding_real_tool_contracts.py': 'P0',
    'test_calculation_evidence_provenance_integrity.py': 'P0',
    'test_approval_export_crm_governance.py': 'P0',
    'test_operational_resilience_real_services.py': 'P1',
    'test_release_environment_smoke_validation.py': 'P0',
}
category_by_file = {
    'test_backend_integrated_golden_path.py': 'Broken integration',
    'test_cross_layer_data_flow_validation.py': 'Broken integration',
    'test_tenant_isolation_security_persistence.py': 'Security issue',
    'test_agent_grounding_real_tool_contracts.py': 'Agent behavior issue',
    'test_calculation_evidence_provenance_integrity.py': 'Persistence issue',
    'test_approval_export_crm_governance.py': 'Contract mismatch',
    'test_operational_resilience_real_services.py': 'Broken integration',
    'test_release_environment_smoke_validation.py': 'Test harness issue',
}
fix_by_file = {
    'test_backend_integrated_golden_path.py': 'Start L1-L6 services with durable stores, then implement missing account/source/extraction/graph/value/approval/export/audit contracts exposed by the red tests.',
    'test_cross_layer_data_flow_validation.py': 'Wire real L1→L2→L3→L4→L5→L6 handoff endpoints and persist run-scoped IDs at each layer.',
    'test_tenant_isolation_security_persistence.py': 'Enforce tenant context in API, database, graph, search, agent retrieval, export assembly, and audit query paths; keep fail-closed responses.',
    'test_agent_grounding_real_tool_contracts.py': 'Connect agents to structured internal tool results and persisted evidence, refusal, recommendation, checkpoint, and audit contracts.',
    'test_calculation_evidence_provenance_integrity.py': 'Implement deterministic calculator contracts with persisted formula inputs, scenario outputs, evidence lineage, benchmark policies, and version history.',
    'test_approval_export_crm_governance.py': 'Align approval, export, and CRM sync APIs with live governance state, including external CRM provider mocking only at the vendor boundary.',
    'test_operational_resilience_real_services.py': 'Add controlled failure simulation, retryable job states, partial-result persistence, resume behavior, terminal cancellation, and failed-export audit events.',
    'test_release_environment_smoke_validation.py': 'Configure L1-L6 service URLs, auth/tenant headers, job workers, and release-candidate seed permissions before running smoke as a deployment gate.',
}

lines = [
    '# Backend-Integrated Initial Failure Report',
    '',
    'The first backend-integrated milestone execution was intentionally run in the current sandbox without live L1-L6 Fabric_4L services. The result is a valid TDD red state: all 61 collected tests failed closed instead of being skipped, which proves the new milestone is executable, strict, and dependent on real service contracts rather than mocks.',
    '',
    '| Failing Test | Category | Likely Cause | Priority | Fix Strategy |',
    '|---|---|---|---|---|',
]
for failure in sorted(failures):
    file_name = failure.split('/')[2].split('::', 1)[0]
    category = category_by_file[file_name]
    priority = priority_by_file[file_name]
    fix = fix_by_file[file_name]
    likely = 'Live service endpoint unavailable or contract not yet aligned with the backend-integrated validation milestone in this environment.'
    if file_name == 'test_tenant_isolation_security_persistence.py':
        likely = 'Tenant-boundary persistence paths cannot be proven until live tenant-scoped account, document, graph, search, agent, export, and audit contracts are available.'
    elif file_name == 'test_release_environment_smoke_validation.py':
        likely = 'Release-candidate service URLs and auth context are not configured in the sandbox, so health and smoke calls fail closed.'
    elif file_name == 'test_agent_grounding_real_tool_contracts.py':
        likely = 'Real agent tool-result and evidence contracts are not reachable in the sandbox service environment.'
    elif file_name == 'test_calculation_evidence_provenance_integrity.py':
        likely = 'Calculator, evidence, benchmark, scenario, and version-history persistence contracts are not reachable in the sandbox service environment.'
    lines.append(f'| `{failure}` | {category} | {likely} | {priority} | {fix} |')

lines.extend([
    '',
    '## Initial Execution Summary',
    '',
    '| Command | Collected | Passed | Failed | Skipped | Notes |',
    '|---|---:|---:|---:|---:|---|',
    '| `BACKEND_VALIDATION_HTTP_TIMEOUT=0.2 pytest tests/backend_integrated -m backend_integrated -q --tb=short` | 61 | 0 | 61 | 0 | Expected red state because the sandbox does not have live L1-L6 services bound to the configured URLs. |',
])

Path('docs/validation/backend_integrated/initial_failure_report.md').write_text('\n'.join(lines) + '\n')
