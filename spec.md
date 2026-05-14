# Spec: Fix authorize_action type guard in signal_tools.py

**Status:** Draft  
**Scope:** Single file — `services/layer4-agents/src/tools/signal_tools.py`  
**Type:** Bug fix / correctness

---

## 1. Problem Statement

In `services/layer4-agents/src/tools/signal_tools.py`, the post-`authorize_action` guard uses `isinstance(ctx, type(_ctx))` to validate the return value. This is a structural check against the dynamic runtime type of the input object rather than a direct check against the known `RequestContext` class.

**Why it is wrong:**

- `type(_ctx)` returns the concrete class of `_ctx` at runtime. If `_ctx` is a plain `RequestContext`, the check happens to be equivalent to `isinstance(ctx, RequestContext)` — but only by accident.
- If `authorize_action` is ever changed to return a `RequestContext` subclass, `isinstance(ctx, type(_ctx))` would **fail** even though the return is a valid context, because `type(_ctx)` is the base class and the return is a subclass.
- The intent is "did `authorize_action` return a valid `RequestContext`", which is expressed correctly and unambiguously as `isinstance(ctx, RequestContext)`.

The guard appears in two functions: `get_account_signals` and `create_signal`.

---

## 2. Root Cause

The guard was introduced as a defensive runtime check against `authorize_action` returning an unexpected type. The implementation used `type(_ctx)` (dynamic lookup of the input's concrete class) instead of `RequestContext` (the statically-known expected type). These are equivalent today but diverge if a subclass is ever returned.

---

## 3. Requirements

1. Replace `isinstance(ctx, type(_ctx))` with `isinstance(ctx, RequestContext)` in both occurrences in `signal_tools.py`.
2. Retain the `tenant_id` presence check (`not getattr(ctx, "tenant_id", None)`) — it is a valid runtime safety check independent of the type guard.
3. No other files are changed.
4. All existing tests continue to pass.

---

## 4. Acceptance Criteria

- `get_account_signals`: guard reads `if not isinstance(ctx, RequestContext) or not getattr(ctx, "tenant_id", None):`
- `create_signal`: guard reads `if not isinstance(ctx, RequestContext) or not getattr(ctx, "tenant_id", None):`
- `isinstance(ctx, type(_ctx))` does not appear anywhere in `signal_tools.py`.
- `RequestContext` is already imported at the top of the file — no new imports needed.
- `PYTHONPATH=src python -m pytest tests/` passes in `services/layer2-5-signal-refinery` (no regression).

---

## 5. Implementation Steps

1. In `services/layer4-agents/src/tools/signal_tools.py`, locate the two occurrences of:
   ```python
   if not isinstance(ctx, type(_ctx)) or not getattr(ctx, "tenant_id", None):
   ```
2. Replace each with:
   ```python
   if not isinstance(ctx, RequestContext) or not getattr(ctx, "tenant_id", None):
   ```
3. Confirm `RequestContext` is imported (it is — imported on line 21 from `value_fabric.shared.identity.context`).
4. Run the test suite to confirm no regressions.
