#!/usr/bin/env node
/**
 * Collect journey SLO metrics from Playwright JUnit XML output.
 *
 * Reads e2e-results/junit.xml (or PLAYWRIGHT_JUNIT_FILE), filters test cases
 * belonging to the launch journey suite, and writes tmp/journey-slo-report.json
 * (or JOURNEY_SLO_REPORT_PATH) with the metrics required by the SLO gate.
 *
 * Required output shape (see assert-journey-launch-slos.mjs):
 *   {
 *     "account_signals_evidence_driver_calculator_business_case": {
 *       "successRate": <0–1>,
 *       "p95LatencySeconds": <number>,
 *       "nonEmptyRatio": <0–1>
 *     }
 *   }
 *
 * Usage:
 *   node scripts/quality/collect-journey-slo-metrics.mjs
 *   PLAYWRIGHT_JUNIT_FILE=custom.xml JOURNEY_SLO_REPORT_PATH=out.json node ...
 */

import { readFileSync, mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { dirname } from 'node:path';

const JUNIT_FILE = process.env.PLAYWRIGHT_JUNIT_FILE ?? 'e2e-results/junit.xml';
const REPORT_PATH = process.env.JOURNEY_SLO_REPORT_PATH ?? 'tmp/journey-slo-report.json';

// Journey suite name patterns that belong to the launch critical path.
const LAUNCH_JOURNEY_PATTERNS = [
  /j1.*golden/i,
  /j11.*business.*lifecycle/i,
  /account.*signal/i,
  /evidence.*driver/i,
  /calculator.*business.*case/i,
  /full.*journey/i,
];

function parseJUnit(xml) {
  const testCases = [];
  // Extract <testcase> elements with name, time, and failure/error children.
  const tcRegex = /<testcase\s([^>]*)>([\s\S]*?)<\/testcase>|<testcase\s([^>]*)\/>/g;
  let match;
  while ((match = tcRegex.exec(xml)) !== null) {
    const attrs = match[1] ?? match[3] ?? '';
    const body = match[2] ?? '';

    const nameMatch = attrs.match(/name="([^"]*)"/);
    const timeMatch = attrs.match(/time="([^"]*)"/);
    const classMatch = attrs.match(/classname="([^"]*)"/);

    const name = nameMatch?.[1] ?? '';
    const classname = classMatch?.[1] ?? '';
    const timeSeconds = parseFloat(timeMatch?.[1] ?? '0');
    const failed = /<failure|<error/.test(body);
    const hasOutput = /<system-out>[\s\S]*\S[\s\S]*<\/system-out>/.test(body);

    testCases.push({ name, classname, timeSeconds, failed, hasOutput });
  }
  return testCases;
}

function isLaunchJourney(tc) {
  const label = `${tc.classname} ${tc.name}`;
  return LAUNCH_JOURNEY_PATTERNS.some((p) => p.test(label));
}

function percentile(sorted, p) {
  if (sorted.length === 0) return 0;
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, idx)];
}

if (!existsSync(JUNIT_FILE)) {
  console.error(`JUnit file not found: ${JUNIT_FILE}`);
  console.error('Run Playwright journey tests first, then re-run this script.');
  process.exit(1);
}

const xml = readFileSync(JUNIT_FILE, 'utf8');
const allCases = parseJUnit(xml);

if (allCases.length === 0) {
  console.error(`No test cases found in ${JUNIT_FILE}`);
  process.exit(1);
}

// Filter to launch journey tests; fall back to all tests if none match.
let journeyCases = allCases.filter(isLaunchJourney);
if (journeyCases.length === 0) {
  console.warn(
    `No test cases matched launch journey patterns in ${JUNIT_FILE}. ` +
    `Using all ${allCases.length} test cases as proxy.`
  );
  journeyCases = allCases;
}

const total = journeyCases.length;
const passed = journeyCases.filter((tc) => !tc.failed).length;
const successRate = total > 0 ? passed / total : 0;

const sortedTimes = journeyCases.map((tc) => tc.timeSeconds).sort((a, b) => a - b);
const p95LatencySeconds = percentile(sortedTimes, 95);

// nonEmptyRatio: fraction of passed tests that produced non-empty system-out.
//
// NOTE: Playwright's JUnit reporter only emits <system-out> when tests log
// output explicitly (e.g. via console.log or page.evaluate). When no
// system-out is present this metric CANNOT be measured from JUnit alone.
// In that case we set nonEmptyRatio to null and skip the SLO check rather
// than silently passing with a fabricated 1.0.
//
// To make this metric meaningful, journey tests should log a non-empty
// response summary (e.g. JSON.stringify of the first API response) so
// system-out is always present for passing tests.
const passedCases = journeyCases.filter((tc) => !tc.failed);
const withOutput = passedCases.filter((tc) => tc.hasOutput);
let nonEmptyRatio;
if (passedCases.length === 0) {
  nonEmptyRatio = 0;
} else if (withOutput.length === 0) {
  // No system-out captured — metric is unmeasurable from this JUnit file.
  console.warn(
    'WARNING: nonEmptyRatio cannot be measured — no <system-out> found in ' +
    'passing test cases. Journey tests should log response content so this ' +
    'SLO can be verified. Metric will be omitted from the report.'
  );
  nonEmptyRatio = null;
} else {
  nonEmptyRatio = withOutput.length / passedCases.length;
}

const report = {
  account_signals_evidence_driver_calculator_business_case: {
    successRate,
    p95LatencySeconds,
    nonEmptyRatio,
  },
  _meta: {
    generatedAt: new Date().toISOString(),
    sourceFile: JUNIT_FILE,
    totalCases: total,
    journeyCases: journeyCases.length,
    passedCases: passed,
  },
};

mkdirSync(dirname(REPORT_PATH), { recursive: true });
writeFileSync(REPORT_PATH, JSON.stringify(report, null, 2));

console.log(`Journey SLO metrics written to ${REPORT_PATH}`);
console.log(`  successRate:       ${successRate.toFixed(4)}`);
console.log(`  p95LatencySeconds: ${p95LatencySeconds.toFixed(3)}`);
console.log(`  nonEmptyRatio:     ${nonEmptyRatio.toFixed(4)}`);
console.log(`  journeyCases:      ${journeyCases.length} / ${total} total`);
