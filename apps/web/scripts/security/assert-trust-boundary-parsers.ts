#!/usr/bin/env tsx
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  formatViolations,
  scanRepository,
} from "../../src/lib/quality/trustBoundaryGuard";

const __dirname = dirname(fileURLToPath(import.meta.url));
const webRoot = resolve(__dirname, "..", "..");

const violations = scanRepository({ webRoot });
const message = formatViolations(violations);

if (violations.length > 0) {
  console.error(message);
  process.exit(1);
}

console.log(message);
