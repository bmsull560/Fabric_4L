import { globSync, readFileSync } from 'node:fs';
import path from 'node:path';

const GENERATED_GLOB = 'src/api/generated/**/index.ts';
const TYPES_GLOB = 'src/types/**/*.ts';

function normalizeContractName(name) {
  return name.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
}

function collectGeneratedSchemaNames() {
  const names = new Set();
  for (const file of globSync(GENERATED_GLOB, { cwd: process.cwd() })) {
    const content = readFileSync(file, 'utf8');
    const matches = content.matchAll(/components\['schemas'\]\['([^']+)'\]/g);
    for (const match of matches) {
      names.add(normalizeContractName(match[1]));
    }
  }
  return names;
}

function collectManualDtoDeclarations() {
  const declarations = [];
  const dtoPattern = /^\s*export\s+(?:interface|type)\s+(\w+(?:Dto|DTO))\b/gm;

  for (const file of globSync(TYPES_GLOB, { cwd: process.cwd() })) {
    const content = readFileSync(file, 'utf8');
    for (const match of content.matchAll(dtoPattern)) {
      const symbol = match[1];
      const logicalName = symbol.replace(/^Api/, '').replace(/(?:Dto|DTO)$/, '');
      declarations.push({
        file,
        symbol,
        normalized: normalizeContractName(logicalName),
      });
    }
  }

  return declarations;
}

const generatedNames = collectGeneratedSchemaNames();
const duplicateDtos = collectManualDtoDeclarations().filter((dto) => generatedNames.has(dto.normalized));

if (duplicateDtos.length > 0) {
  console.error('Found hand-authored DTOs in apps/web/src/types that duplicate generated OpenAPI schemas:');
  for (const dto of duplicateDtos) {
    console.error(`  - ${path.posix.normalize(dto.file)} :: ${dto.symbol}`);
  }
  console.error('\nUse generated types from src/api/generated or @/api/generated instead of redefining server DTOs.');
  process.exit(1);
}

console.log('No duplicate hand-authored server DTO interfaces/types found in apps/web/src/types.');
