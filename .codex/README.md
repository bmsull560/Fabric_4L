# Codex Workspace Bridge

This folder documents how Codex should interpret the repository's existing `.windsurf/`
workspace.

## Intent

`.windsurf/` is the project's assistant-runtime source of truth. Codex cannot automatically
execute that runtime, but it can use the files as local project guidance.

## Mapping

- `.windsurf/AGENTS.md` -> agent roles, boundaries, and task framing reference
- `.windsurf/CONTEXT.md` -> context assembly and conflict-checking reference
- `.windsurf/MEMORY.md` -> memory/documentation conventions reference
- `.windsurf/rules/` -> policy and safety reference
- `.windsurf/skills/` -> reusable playbook reference
- `.windsurf/workflows/` -> orchestration playbook reference
- `.windsurf/mcp/` -> reference manifests only; not automatically active in Codex

## Practical Rule

For Codex sessions in this repo, prefer:

1. Root `AGENTS.md`
2. `packages/platform-contract/CONTRACT.md`
3. Relevant `.windsurf/` documents for additional local guidance

If these sources conflict, follow the higher item in the list.
