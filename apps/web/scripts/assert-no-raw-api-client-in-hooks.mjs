import { execSync } from 'node:child_process';

let out = '';
try {
  out = execSync(
    "rg -n \"apiClient\\.(get|post|put|patch|delete)\\(\" src/hooks --glob '!**/*.test.*' --glob '!**/*.spec.*'",
    { encoding: 'utf8' }
  ).trim();
} catch (error) {
  // rg exits 1 when no matches are found, which is the desired state.
  out = error.stdout?.toString().trim() ?? '';
}

if (out) {
  console.error('Found forbidden raw apiClient calls in apps/web/src/hooks:');
  console.error(out);
  console.error('');
  console.error('All hooks must use typed wrappers from @/api/typedClient.ts:');
  console.error('  apiGet<T>, apiPost<T>, apiPut<T>, apiPatch<T>, apiDelete<T>');
  console.error('');
  console.error('Raw apiClient calls bypass the explicit-generic requirement and reintroduce unsafe casts.');
  process.exit(1);
}

console.log('No raw apiClient calls found in src/hooks. Typed-wrapper mandate upheld.');
