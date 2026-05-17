# Frontend Production UI Mock-Data Scanner Contract

This document defines the CI policy that prevents mock/test fixtures from leaking into production UI source code.

## Ownership and discoverability

- **Contract owner:** Frontend Platform + UI Architecture maintainers.
- **Rule implementation:** `frontend/scripts/detect-mock-data.ts`.
- **Rule exceptions manifest:** `frontend/scripts/mock-data-allowlist.json`.
- **CI gate location:** `.github/workflows/pr-checks.yml` in the `frontend-checks` job.
- **Source scope:**
  - `frontend/client/src/pages/**`
  - `frontend/client/src/components/**`

This file is intentionally stored in `docs/platform-contract/` so policy ownership stays close to other frontend-facing platform contract docs.

## Disallowed patterns

The scanner fails CI when any of the following patterns appear in in-scope production UI files:

1. `mockData` identifiers
2. `testData` identifiers
3. `dummy*` identifiers (for example `dummyUser`, `dummyRows`)
4. Imports from `*.mock*` modules
5. Hardcoded array/object literals bound to mock-style identifiers (for example `const mockAccounts = [...]`, `const testPayload = {...}`)

## Exclusions

The scanner excludes the following by default:

- Test/spec/story files:
  - `*.test.ts`, `*.test.tsx`
  - `*.spec.ts`, `*.spec.tsx`
  - `*.stories.ts`, `*.stories.tsx`
- Test/mock folder conventions:
  - `**/__tests__/**`
  - `**/__mocks__/**`
  - `**/fixtures/**`
  - `**/mocks/**`
- Approved mock folders:
  - `frontend/client/src/test/mocks/**`
  - `frontend/test/mocks/**`
- Deprecated UI page folders:
  - `**/_deprecated/**`

## Allowlist / exception semantics

### 1) Preferred: file-scoped allowlist entries

Use `frontend/scripts/mock-data-allowlist.json` with explicit reason fields.

```json
{
  "entries": [
    {
      "path": "client/src/pages/ExamplePage.tsx",
      "ruleId": "mockData-identifier",
      "line": 42,
      "reason": "Temporary launch-blocker workaround; tracked in ENG-1234"
    }
  ]
}
```

Rules:

- `path` and `reason` are required.
- `ruleId` is optional; if omitted, the allowlist entry applies to any scanner rule in that file.
- `line` is optional; if provided, the exception applies to a single line only.
- Keep entries narrow and remove them once remediated.

### 2) Narrow fallback: inline exception comments

If an in-scope file needs a one-off exception, add an inline suppression comment directly on the line above (or the same line):

```ts
// mock-scan: allow <reason>
const data = { ... };
```

Use this sparingly and include a clear reason.

## Local usage

Run locally before pushing:

```bash
cd frontend
pnpm run check:mock-data
```

Violation output format is intentionally actionable:

- `path:line` of the violation
- rule id
- pattern description
- the offending source line
