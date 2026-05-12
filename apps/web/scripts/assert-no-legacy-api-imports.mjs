#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { extname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const webRoot = resolve(__dirname, "..");
const srcRoot = resolve(webRoot, "src");

const SOURCE_EXTENSIONS = new Set([".ts", ".tsx", ".js", ".jsx"]);
const APPROVED_TEST_PATH_FRAGMENT = "src/api/__tests__/migration/";
const importRegex = /(?:import|export)\s+(?:[^;]*?\s+from\s+)?["']([^"']+)["']/g;
const dynamicImportRegex = /import\(\s*["']([^"']+)["']\s*\)/g;
const forbiddenExact = new Set(["@/api/legacy", "@/api/legacy.ts"]);
const forbiddenSuffixes = ["/api/legacy", "/api/legacy.ts"];

const { readdirSync, statSync } = await import("node:fs");

function walk(dir) {
  const files = [];
  for (const entry of readdirSync(dir)) {
    if (entry === "node_modules" || entry === "dist" || entry.startsWith(".")) continue;
    const fullPath = resolve(dir, entry);
    const stats = statSync(fullPath);
    if (stats.isDirectory()) {
      files.push(...walk(fullPath));
      continue;
    }
    if (SOURCE_EXTENSIONS.has(extname(entry))) {
      files.push(fullPath);
    }
  }
  return files;
}

function isLegacyImport(specifier) {
  if (forbiddenExact.has(specifier)) return true;
  return forbiddenSuffixes.some((suffix) => specifier.endsWith(suffix));
}

const violations = [];
for (const filePath of walk(srcRoot)) {
  const relPath = relative(webRoot, filePath);
  const contents = readFileSync(filePath, "utf8");

  const check = (regex) => {
    regex.lastIndex = 0;
    let match;
    while ((match = regex.exec(contents)) !== null) {
      const specifier = match[1];
      if (!isLegacyImport(specifier)) continue;
      if (relPath.includes(APPROVED_TEST_PATH_FRAGMENT)) continue;
      const line = contents.slice(0, match.index).split(/\r?\n/).length;
      violations.push(`${relPath}:${line} imports forbidden legacy API module '${specifier}'`);
    }
  };

  check(importRegex);
  check(dynamicImportRegex);
}

if (violations.length > 0) {
  console.error("Legacy API import gate failed:\n");
  for (const violation of violations) {
    console.error(`- ${violation}`);
  }
  console.error(
    `\nAllowed scope: ${APPROVED_TEST_PATH_FRAGMENT}* (explicit migration tests only).`,
  );
  process.exit(1);
}

console.log("Legacy API import gate passed.");
