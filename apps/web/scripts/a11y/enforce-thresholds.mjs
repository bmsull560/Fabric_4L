import fs from "node:fs/promises";

const reportPath = process.env.A11Y_REPORT_PATH || "./a11y-report.json";
const maxCritical = Number(process.env.A11Y_MAX_CRITICAL ?? 0);
const maxSerious = Number(process.env.A11Y_MAX_SERIOUS ?? 0);
const minRoutesScanned = Number(process.env.A11Y_MIN_ROUTES_SCANNED ?? 4);

const report = JSON.parse(await fs.readFile(reportPath, "utf8"));
const routeCount = report.results?.length ?? 0;
const { critical = 0, serious = 0 } = report.summary ?? {};

if (routeCount < minRoutesScanned) {
  console.error(`A11y gate failed: scanned ${routeCount} routes; minimum required is ${minRoutesScanned}.`);
  process.exit(1);
}

if (critical > maxCritical || serious > maxSerious) {
  console.error(
    `A11y gate failed: critical=${critical} (max ${maxCritical}), serious=${serious} (max ${maxSerious}).`,
  );
  process.exit(1);
}

console.log(
  `A11y gate passed: routes=${routeCount}, critical=${critical}/${maxCritical}, serious=${serious}/${maxSerious}.`,
);
