# Gauge Review — Task Breakdown Stage, Iteration 2

You are the **Gauge** in a Forge-Gauge dual-LLM task-breakdown loop. Iter1 issued REVISE: 2 BLOCKING (AC-7 part-2, NFR-3 verification) plus 3 WARNINGs (T32 file list, R8 docstring, basedpyright CI commitment).

## What changed since iter1

- **B1 fix:** Added new task **T26b** "Same-process IR identity test (AC-7 part 2)" — loads `cross_module_type_refs` twice in one process, compares `RepoIR` deeply.
- **B2 fix:** Added NFR-3 dependency check to T37 final integration check (`git diff develop -- pyproject.toml` shows no new runtime deps).
- **W1 fix:** Added `tests/test_namespace_validation.py` to T32's file list.
- **W2 fix:** Added R8 invariant docstring requirement to T12's description.
- **W3 fix:** Updated plan's AC-22 basedpyright section to drop the CI commitment (repo has no CI), and instead require basedpyright as part of every commit's integration check task.

## What to do

1. Read iter1 review at `specs/011-cross-module-type-refs/artifacts/task_breakdown/iter1-gauge.md`.
2. Read updated tasks at `specs/011-cross-module-type-refs/tasks.md`.
3. Read updated plan at `specs/011-cross-module-type-refs/plan.md`.
4. Verify each iter1 BLOCKING / WARNING is resolved.
5. Look for new issues.

## What to evaluate

- **B1:** Read T26b. Does it concretely test AC-7's same-process IR identity?
- **B2:** Read T37's NFR-3 line. Is the check concrete?
- **W1-W3:** Each resolution applied?
- **No regressions** — coverage table intact.

## Output format

```
# Gauge Review — Task Breakdown Iteration 2

## Summary
(2 sentences)

## Iter1 Issue Resolution

For each iter1 BLOCKING (B1, B2) and WARNING (W1, W2, W3):
- ✓ resolved
- ✗ unresolved (explain)
- ~ partial (explain)

## New Issues

### BLOCKING
...

### WARNING
...

### NOTE
...

## Strengths
...

VERDICT: APPROVE
```
or `VERDICT: REVISE`.

Save to `specs/011-cross-module-type-refs/artifacts/task_breakdown/iter2-gauge.md`.
