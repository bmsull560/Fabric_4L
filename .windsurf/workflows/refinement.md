---
description: Reflect on completed work and make concrete improvements to raise quality
---

# Refinement Workflow

This workflow transforms "working" code into production-grade output through systematic inspection and direct fixes.

## When to Use

- Code is functional but feels rough or incomplete
- Before marking a task as complete
- After implementing a feature and verifying it works
- When code review reveals quality gaps
- Periodic cleanup of technical debt
- Preparing code for handoff or release

## When to Stop

- Diminishing returns: remaining issues are cosmetic
- Risk of breaking working functionality exceeds benefit
- Time budget exhausted (refinement can be infinite)
- Code is now "obviously correct" to a fresh reader

## Steps

1. **Inspect the Implementation**
   // turbo
   - Read all files touched by the recent work
   - Identify the core logic, edge cases, and error handling
   - Look for TODO comments, FIXME markers, or placeholders
   - Check test coverage; if <80% or missing edge cases, strengthen tests first

2. **Identify Weaknesses**
   Scan for these specific issues with detection methods:
   - **Incorrectness**: Unit tests fail, assertions missing, validation logic absent
   - **Incompleteness**: Uncovered branches in tests, missing None checks, partial error handling
   - **Fragility**: Hardcoded strings/numbers, no retry loops, direct dependency instantiation
   - **Inelegance**: Functions >50 lines, nested conditionals >3 levels, duplicate code blocks
   - **Performance**: Loops calling external services, unbounded queries, no caching
   - **Maintainability**: Missing type hints, unclear variable names, no docstrings, magic numbers

3. **Prioritize Fixes**
   - P0: Bugs and incorrect behavior (fix immediately)
   - P1: Fragility that will cause production issues
   - P2: Maintainability and clarity improvements
   - P3: Performance and elegance refinements

4. **Make Concrete Fixes by Category**

   **Incorrectness** (P0): Add missing validation, fix logic errors, add assertions
   **Incompleteness** (P0): Handle the edge case, add the missing error branch, complete partial impl
   **Fragility** (P1): Replace hardcoded values with constants, add retry logic with backoff, inject dependencies
   **Inelegance** (P2): Extract function when code repeats 2+ times, flatten nested conditionals early-return pattern, rename unclear vars (length >20 or <3 chars), split functions >50 lines
   **Performance** (P3): Batch external calls, add caching, make I/O async
   **Maintainability** (P2): Add type hints to public functions, add docstrings to non-obvious logic, replace magic numbers with named constants

5. **Verify Improvements**
   // turbo
   - Run all tests to ensure nothing broke
   - Test edge cases that were previously unhandled
   - Review the diff to confirm changes are focused (<100 lines ideally)
   - Ensure the code is now "obviously correct" to a fresh reader
   - Check test coverage improved or stayed same

6. **Final Polish**
   - Check file organization and imports
   - Verify consistent style with surrounding codebase
   - Ensure no debug code or print statements remain
   - Confirm all TODOs are resolved or ticketed
   - Commit changes with descriptive message: "Refine: [specific improvement made]"

## Success Criteria (Definition of Done)

- Code passes all tests including new edge cases
- No P0 or P1 issues remain
- At least one measurable improvement made (coverage up, complexity down, clarity up)
- Changes are focused and reviewable in <15 minutes
- Code is "obviously correct" without needing explanation

## Concrete Actions Checklist

Use this to ensure you're making direct improvements, not just analyzing:

- [ ] Fixed at least one bug or incorrect behavior
- [ ] Added validation for at least one edge case
- [ ] Improved at least one variable or function name
- [ ] Extracted or simplified at least one complex block
- [ ] Added or strengthened at least one test
- [ ] Removed at least one piece of dead code
- [ ] Improved error handling in at least one location
- [ ] Committed with descriptive message explaining the refinement

## Anti-Patterns to Avoid

- **Don't**: Write lengthy explanations of what's wrong without fixing it
- **Don't**: Suggest refactorings that don't address actual problems
- **Don't**: Add abstractions that increase complexity
- **Don't**: Ignore flaky tests or work around them
- **Don't**: Leave TODOs for "future cleanup"

## Example Commands

"Refine the error handling in the ingestion pipeline"
"Harden the state machine against race conditions"
"Clean up the API response formatting code"
"Strengthen tests for the knowledge graph queries"
"Polish the agent workflow implementation"
"Remove technical debt from the extraction layer"
