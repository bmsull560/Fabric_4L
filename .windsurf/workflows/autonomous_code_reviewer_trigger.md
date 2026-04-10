---
description: Auto-trigger code review on save or periodic check
---

# Autonomous Code Reviewer - Auto Trigger

This workflow automatically triggers the code reviewer when conditions are met.

## Triggers

- On file save (if uncommitted changes exist)
- Every 5 minutes (when IDE is active)
- When test failures detected

## Usage

Enable auto-review by adding to `.windsurf/config.yaml`:

```yaml
auto_review:
  enabled: true
  on_save: true
  interval_minutes: 5
  max_fixes_per_session: 3
```

Or run manually:

```
Check for uncommitted changes and run autonomous code reviewer if found
```
