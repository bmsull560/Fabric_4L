#!/usr/bin/env node
import { readFileSync } from 'node:fs';

const reportPath = process.env.JOURNEY_SLO_REPORT_PATH ?? 'tmp/journey-slo-report.json';
const report = JSON.parse(readFileSync(reportPath, 'utf8'));
const launch = report.account_signals_evidence_driver_calculator_business_case;

if (!launch) {
  console.error(`Missing launch journey in ${reportPath}`);
  process.exit(1);
}

const failures = [];
if (launch.successRate < 0.99) failures.push(`successRate ${launch.successRate} < 0.99`);
if (launch.p95LatencySeconds > 12) failures.push(`p95LatencySeconds ${launch.p95LatencySeconds} > 12`);
if (launch.nonEmptyRatio === null || launch.nonEmptyRatio === undefined) {
  console.warn('WARNING: nonEmptyRatio not measured — journey tests did not emit system-out. Skipping check.');
} else if (launch.nonEmptyRatio < 1) {
  failures.push(`nonEmptyRatio ${launch.nonEmptyRatio} < 1`);
}

if (failures.length) {
  console.error(`Journey SLO gate failed (${reportPath}):`);
  for (const failure of failures) console.error(` - ${failure}`);
  process.exit(1);
}

console.log(`Journey SLO gate passed (${reportPath}).`);
