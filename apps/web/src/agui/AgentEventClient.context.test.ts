import { describe, it, expect } from 'vitest';
import { buildRightRailContextEnvelope } from './AgentEventClient';

describe('buildRightRailContextEnvelope', () => {
  it('includes required context for signals route variant', () => {
    expect(buildRightRailContextEnvelope({
      activeTab: 'signals',
      accountId: 'acc-1',
      selectedSignalId: 'sig-1',
      selectedEvidenceId: undefined,
    })).toEqual({
      accountId: 'acc-1',
      signalId: 'sig-1',
      evidenceId: null,
      workspaceTab: 'signals',
    });
  });

  it('includes required context for evidence route variant', () => {
    expect(buildRightRailContextEnvelope({
      activeTab: 'evidence',
      accountId: 'acc-2',
      selectedEvidenceId: 'ev-1',
    })).toEqual({
      accountId: 'acc-2',
      signalId: null,
      evidenceId: 'ev-1',
      workspaceTab: 'evidence',
    });
  });

  it('always includes workspace tab for generic variants', () => {
    expect(buildRightRailContextEnvelope({ activeTab: 'stakeholders' })).toEqual({
      accountId: null,
      signalId: null,
      evidenceId: null,
      workspaceTab: 'stakeholders',
    });
  });
});
