---
description: Autonomous continual agent for reviewing local changes and making small targeted bug fixes or improvements
---

# Autonomous Code Reviewer Agent

Use this workflow to continuously review local code changes and autonomously apply small, targeted bug fixes or improvements without user intervention.

## Activation Criteria

Auto-activate when ANY of:
- [ ] Uncommitted changes in tracked source files (check `git status`)
- [ ] Test failures in modified modules (check `pytest` or similar)
- [ ] Linting/type errors introduced (check `ruff`, `mypy`, `eslint`)
- [ ] Coverage dropped below 80% in modified files

## Review Scope (Priority Order)

**P0 - Fix Immediately (Bugs)**
- [ ] Syntax errors, undefined variables, import failures
- [ ] Null dereferences, off-by-one errors, race conditions
- [ ] Unhandled exceptions, missing error branches
- [ ] Security: injection vulnerabilities, hardcoded secrets, unsafe eval

**P1 - Fix If Time (Fragility)**
- [ ] Missing input validation, type mismatches
- [ ] Resource leaks (files, connections, memory)
- [ ] Hardcoded values that should be configurable
- [ ] Missing retry logic for external calls

**P2 - Fix Opportunistically (Clarity)**
- [ ] Functions >50 lines or >3 nested conditionals
- [ ] Missing type hints on public functions
- [ ] Unclear variable names (length <3 or >20 chars)
- [ ] Duplicate code blocks (2+ occurrences)

**Explicitly SKIP:**
- Refactoring without clear bug/fix purpose
- Feature additions, breaking API changes
- Design pattern debates, pure documentation changes

## Workflow Steps

### 1. Detect Changes (30s)
```bash
git status --short
git diff --name-only
```
- Filter to source files: `.*\.(py|ts|js|go|rs|java)$`
- Exclude: `tests/`, `config/`, `generated/`, `\.env.*`, `\.(json|yaml|toml)$`
- If no files match → EXIT

### 2. Analyze & Categorize (60s)
```bash
git diff <files>
```
For each changed file:
- [ ] Run syntax check: `python -m py_compile` (or language equivalent)
- [ ] Run tests for modified modules only (not full suite)
- [ ] Run linter if config exists (auto-detect `pyproject.toml`, `.eslintrc`, etc.)
- [ ] Check test coverage: fail if <80% on modified lines

Categorize issues found into P0/P1/P2 buckets.

### 3. Generate Fixes (per issue)
For each P0/P1 issue:
- [ ] Identify root cause (not symptom)
- [ ] Generate fix: ≤20 lines changed, ≤1 function modified
- [ ] Ensure no signature/API changes
- [ ] Assign confidence score (0.0-1.0)
- [ ] Skip if confidence <0.85 or requires >20 lines

### 4. Validate (30s per fix)
```bash
git stash push -m "pre-review-stash"
# Apply fix
pytest <relevant-tests> -x --tb=short
# If pass: keep fix; else: discard and report
```

### 5. Apply (10s)
```bash
git add <fixed-files>
git commit -m "fix: [brief description]

- Issue: [specific problem]
- Fix: [specific change]
- Confidence: 0.XX"
```

**Error Handling:**
- If git command fails → log and escalate
- If tests fail after fix → discard fix, report failure
- If linter unavailable → skip linting, continue

## Hard Constraints (Non-Negotiable)

| Constraint | Value | Action if Violated |
|------------|-------|-------------------|
| Lines changed | ≤20 per fix | Escalate to human |
| Confidence | ≥0.85 | Queue for review, don't auto-apply |
| Test breakage | 0 allowed | Discard fix, report failure |
| Files per commit | 1 preferred, ≤3 max | Split into separate commits |
| API changes | None | Never modify signatures |

## Soft Constraints (Best Effort)

- Coverage on modified lines ≥80%
- Cyclomatic complexity increase ≤2
- No new linting warnings introduced

## Output Format

```json
{
  "files_reviewed": ["src/module.py", "src/utils.py"],
  "issues_found": 3,
  "fixes_applied": [
    {
      "file": "src/module.py",
      "line": 42,
      "issue": "UnboundLocalError: variable referenced before assignment",
      "fix": "Initialize variable before conditional branch",
      "confidence": 0.95
    }
  ],
  "tests_passed": true,
  "commit_hash": "abc123"
}
```

## Safety Rules (Violate = Stop)

- [ ] **NO auto-commit** → Stage only, await approval
- [ ] **NO config/secrets** → Skip `.env*`, `config/`, `secrets/`
- [ ] **NO deletions** → Comment out, don't remove (until approved)
- [ ] **NO dependency changes** → Skip `package.json`, `requirements.txt`, etc.
- [ ] **NO test removal** → Never delete tests to "fix" coverage

## Audit Trail (Log Every Action)

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "session_id": "uuid",
  "files_reviewed": ["src/x.py"],
  "issues_found": [{"severity": "P0", "description": "..."}],
  "fixes_proposed": [{"file": "...", "lines": "...", "confidence": 0.9}],
  "fixes_applied": [{"file": "...", "commit": "abc123"}],
  "fixes_rejected": [{"reason": "..."}],
  "escalations": [{"reason": "confidence < 0.85"}]
}
```

## Escalation Triggers (Stop & Ask Human)

Immediate escalation when ANY of:
- [ ] Fix requires >20 lines or >1 function
- [ ] Multiple files need coordinated changes
- [ ] Threading/async/concurrency issues detected
- [ ] Security fix requires architecture/design change
- [ ] Tests fail and fix cannot be determined
- [ ] Confidence <0.85 for any proposed fix
- [ ] Merge conflicts present in working directory
- [ ] Working tree is not clean (untracked files causing issues)

## Example Sessions

**Successful Fix:**
```
[DETECT] 2 modified files: src/parser.py, src/models.py
[ANALYZE] src/parser.py:42 - UnboundLocalError (P0)
[ANALYZE] src/models.py:15 - Missing type hint (P2, skip)
[FIX] parser.py:42 - Initialize 'result' before conditional
[VALIDATE] pytest tests/test_parser.py -x → PASSED (8/8)
[STAGE] git add src/parser.py
[STAGE] git commit -m "fix(parser): initialize result before use"
[COMPLETE] Awaiting approval. 1 P0 fixed, 1 P2 queued.
```

**Escalation:**
```
[DETECT] 3 modified files
[ANALYZE] src/api.py:89 - Race condition in async handler (P0)
[ESCALATE] Concurrency issue requires human review
[COMPLETE] 0 fixes applied. Manual review required.
```

**No Issues:**
```
[DETECT] 1 modified file: src/utils.py
[ANALYZE] Syntax OK, tests pass (12/12), coverage 94%
[COMPLETE] No issues found. No changes needed.
```

## Success Criteria (Definition of Done)

- [ ] All P0 bugs in modified files are either fixed or escalated
- [ ] No test failures introduced by fixes
- [ ] Coverage on modified files ≥80%
- [ ] All changes ≤20 lines per fix
- [ ] Complete audit trail logged
- [ ] User notified of all actions taken or escalations needed
- [ ] Working directory left in clean state (staged changes ready for review)
