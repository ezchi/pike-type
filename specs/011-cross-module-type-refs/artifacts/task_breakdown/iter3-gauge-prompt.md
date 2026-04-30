# Gauge Review — Task Breakdown Stage, Iteration 3

You are the **Gauge** in a Forge-Gauge dual-LLM task-breakdown loop. Iter2 issued REVISE: 2 WARNINGs (basedpyright not in every integration task; stale CI wording in plan).

## What changed since iter2

- T11, T17, T28, T35 verification criteria now explicitly include `basedpyright src/piketype tests/` zero errors.
- Plan wording about CI rewritten: "CI runs the full suite each push" → "implementer runs the full suite at integration-check tasks"; perf gate also de-CI-d.
- Task count corrected: 37 → 38 (T1-T37 + T26b).

## What to do

1. Read iter2 review at `specs/011-cross-module-type-refs/artifacts/task_breakdown/iter2-gauge.md`.
2. Read updated tasks at `specs/011-cross-module-type-refs/tasks.md`.
3. Read updated plan at `specs/011-cross-module-type-refs/plan.md`.
4. Verify each iter2 WARNING is resolved.

## What to evaluate

- Does T11/T17/T28/T35 each say `basedpyright src/piketype tests/` in description AND verification?
- Plan no longer says "CI runs"?
- Task count consistent (38)?

## Output format

```
# Gauge Review — Task Breakdown Iteration 3

## Summary
(1-2 sentences)

## Iter2 Issue Resolution

For each iter2 WARNING:
- ✓ resolved
- ✗ unresolved (explain)

## New Issues

### BLOCKING
...

### WARNING
...

### NOTE
...

VERDICT: APPROVE
```
or `VERDICT: REVISE`.

Save to `specs/011-cross-module-type-refs/artifacts/task_breakdown/iter3-gauge.md`.
