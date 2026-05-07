export const SYNTHETIC_TENANT = {
  tenantId: 'tenant-synthetic-ci',
  accountId: 'acct-synthetic-alpha',
  accountName: 'Synthetic Alpha Manufacturing',
  signals: [
    { id: 'sig-001', title: 'Manual reconciliation backlog growing 22% QoQ', confidence: 0.91 },
    { id: 'sig-002', title: 'ERP upgrade planned in Q3', confidence: 0.87 },
  ],
  evidence: [
    { id: 'ev-001', claim: '12 FTEs spend >20h/week on manual close activities', source: 'finance-discovery-call.md' },
    { id: 'ev-002', claim: 'Current DSO is 58 days and target is 45 days', source: 'controller-review-notes.md' },
  ],
  driver: {
    id: 'drv-001',
    name: 'Working capital improvement',
    benchmark: '8-12 day DSO reduction',
  },
  calculator: {
    conservativeRoi: 1.9,
    expectedRoi: 2.8,
    optimisticRoi: 3.6,
    paybackMonths: 9,
  },
  businessCase: {
    id: 'bc-001',
    title: 'Synthetic Alpha AP/AR Automation Business Case',
    annualValueUsd: 2850000,
  },
} as const;
