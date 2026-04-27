import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const appSource = readFileSync(resolve(__dirname, 'App.tsx'), 'utf8');

describe('App governance routing definitions', () => {
  it('maps /governance/evidence to GovernanceEvidencePage and not DecisionTrace', () => {
    expect(appSource).toContain('<Route path="/governance/evidence">');
    expect(appSource).toContain('<GovernanceEvidencePage />');
    expect(appSource).not.toContain('<Route path="/governance/evidence">\n        <AuthenticatedRoute {...tierProps}>\n          <DecisionTrace />');
  });

  it('maps /governance/compliance to GovernanceCompliancePage', () => {
    expect(appSource).toContain('<Route path="/governance/compliance">');
    expect(appSource).toContain('<GovernanceCompliancePage />');
  });

  it('maps audit routes to audit-specific pages', () => {
    expect(appSource).toContain('<Route path="/governance/audit/log">');
    expect(appSource).toContain('<GovernanceAuditLogPage />');
    expect(appSource).toContain('<Route path="/governance/audit/changes">');
    expect(appSource).toContain('<GovernanceAuditChangesPage />');
  });
});
