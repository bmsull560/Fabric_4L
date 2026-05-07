import { describe, it, expect } from 'vitest';
import { getMissingActionContextMessage } from './useAgentEvents';

describe('getMissingActionContextMessage', () => {
  it('requires account across workspace variants', () => {
    expect(getMissingActionContextMessage({ activeTab: 'signals' })).toContain('account');
    expect(getMissingActionContextMessage({ activeTab: 'evidence' })).toContain('account');
  });

  it('requires signal selection on signals route variant', () => {
    expect(getMissingActionContextMessage({ activeTab: 'signals', accountId: 'acc-1' })).toContain('signal');
    expect(getMissingActionContextMessage({ activeTab: 'signals', accountId: 'acc-1', selectedSignalId: 'sig-1' })).toBeUndefined();
  });

  it('requires evidence selection on evidence route variant', () => {
    expect(getMissingActionContextMessage({ activeTab: 'evidence', accountId: 'acc-1' })).toContain('evidence');
    expect(getMissingActionContextMessage({ activeTab: 'evidence', accountId: 'acc-1', selectedEvidenceId: 'ev-1' })).toBeUndefined();
  });
});
