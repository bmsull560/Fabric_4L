import fs from "node:fs";
import path from "node:path";

const policyPath = path.resolve("src/governance/legacyRemovalPolicy.ts");
const policyRaw = fs.readFileSync(policyPath, "utf8");
const match = policyRaw.match(/LEGACY_REMOVAL_DATE\s*=\s*"(\d{4}-\d{2}-\d{2})"/);
if (!match) {
  throw new Error(`Unable to parse LEGACY_REMOVAL_DATE from ${policyPath}`);
}
const cutoffDate = new Date(`${match[1]}T00:00:00.000Z`);
const now = new Date();

const checks = [
  {
    label: "@/api/legacy imports",
    include: [".ts", ".tsx"],
    matcher: /from\s+["']@\/api\/legacy["']/g,
    exclude: ["src/api/legacy.ts"],
  },
  {
    label: "@/components/WfPrimitives imports",
    include: [".ts", ".tsx"],
    matcher: /from\s+["']@\/components\/WfPrimitives["']/g,
    exclude: ["src/components/WfPrimitives.tsx", "src/components/WfPrimitives.test.tsx"],
  },
  {
    label: "deprecated session helpers",
    include: [".ts", ".tsx"],
    matcher: /\b(getSessionSnapshot|persistSession\s*\(|SessionSnapshot\b)\b/g,
    exclude: ["src/services/sessionService.ts", "src/services/sessionService.test.ts", "src/test/authSessionTestUtils.ts", "src/services/authClient.test.ts", "src/services/authClient.ts"],
  },
];

function walk(dir) {
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === "node_modules" || entry.name === "dist" || entry.name === ".git") continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}

const root = path.resolve("src");
const files = walk(root);
const findings = [];
for (const check of checks) {
  for (const file of files) {
    const rel = path.relative(path.resolve('.'), file).replaceAll('\\', '/');
    if (check.exclude.includes(rel)) continue;
    if (!check.include.some((ext) => rel.endsWith(ext))) continue;
    const raw = fs.readFileSync(file, "utf8");
    if (check.matcher.test(raw)) findings.push(`${check.label}: ${rel}`);
  }
}

if (findings.length === 0) {
  console.log(`Legacy removal check passed. No deprecated imports/usages detected.`);
  process.exit(0);
}

if (now <= cutoffDate) {
  console.warn(`Legacy removal grace period active until ${match[1]}. Remaining usages:`);
  for (const finding of findings) console.warn(` - ${finding}`);
  process.exit(0);
}

console.error(`Legacy removal deadline ${match[1]} has passed. Remove deprecated usages:`);
for (const finding of findings) console.error(` - ${finding}`);
process.exit(1);
