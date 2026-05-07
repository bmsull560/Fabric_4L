import { execSync } from 'node:child_process';

let out = '';
try {
  out = execSync("rg -n \"^\\s*export\\s+interface\\s+\\w+(Dto|DTO)\\b\" src --glob '!**/api/generated/**'", { encoding: 'utf8' }).trim();
} catch (error) {
  out = error.stdout?.toString().trim() ?? '';
}

if (out) {
  console.error('Found forbidden manual server DTO interfaces in apps/web/src:');
  console.error(out);
  process.exit(1);
}
console.log('No manual server DTO interfaces found.');
