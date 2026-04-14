import { chromium } from "@playwright/test";

const baseUrl = process.env.A11Y_BASE_URL || "http://127.0.0.1:4173";
const axeScriptUrl =
  process.env.AXE_SCRIPT_URL ||
  "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js";
const routes = ["/", "/home", "/login", "/discover/accounts"];

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

let hasCriticalViolations = false;

for (const route of routes) {
  const url = `${baseUrl}${route}`;
  await page.goto(url, { waitUntil: "networkidle" });
  await page.addScriptTag({ url: axeScriptUrl });

  const results = await page.evaluate(async () => {
    // @ts-ignore injected by script tag
    return window.axe.run(document, {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21aa"],
      },
    });
  });

  const criticalViolations = results.violations.filter(
    (violation) => violation.impact === "critical",
  );

  if (criticalViolations.length > 0) {
    hasCriticalViolations = true;
    console.error(`\nCritical accessibility violations found on ${url}:`);
    for (const violation of criticalViolations) {
      console.error(`- [${violation.id}] ${violation.help}`);
      for (const node of violation.nodes) {
        console.error(`  selector: ${node.target.join(", ")}`);
      }
    }
  } else {
    console.log(`No critical violations on ${url}`);
  }
}

await browser.close();

if (hasCriticalViolations) {
  console.error("\nAccessibility scan failed due to critical violations.");
  process.exit(1);
}

console.log("\nAccessibility scan passed with no critical violations.");
