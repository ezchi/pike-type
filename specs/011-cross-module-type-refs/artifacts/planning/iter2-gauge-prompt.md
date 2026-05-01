# Gauge Review — Planning Stage, Iteration 2

You are the **Gauge** in a Forge-Gauge dual-LLM planning loop. Iter1 issued REVISE: 3 BLOCKING (view-model strings, AC-6 namespace coverage, NFR-4/AC-22 unverifiable) plus 4 WARNINGs.

## What changed since iter1

- **B1 fix:** Backend view models redesigned to carry **semantic parts only** (basenames, dotted module names, class names, include paths). Templates render the literal `import`, `#include`, and `from ... import` keywords. Explicit principle statement added before the SV/Python/C++ component sections.
- **B2 fix:** Added a dedicated `--namespace=proj::lib` integration test covering AC-6's user-namespace path, with goldens at `tests/goldens/gen/cross_module_type_refs_namespace_proj/`.
- **B3 fix:** Added concrete NFR-4 perf gate (`tests/test_perf_gen.py` with `tests/perf_baseline.json`) and AC-22 basedpyright gate.
- **W1 fix:** FR-8 spelled out as four sub-cases (local-vs-imported type, imported-vs-imported type, imported-vs-imported enum literal, local-vs-imported enum literal).
- **W2 fix:** Loader shim removed; `load_module_from_path` is deleted in Commit A; all callers migrated atomically; `load_or_get_module` raises `RuntimeError` if called outside `prepare_run`.
- **W3 fix:** C++ qualification reads `field_ir.type_ir.module` directly; no separate module index needed.
- **W4 fix:** AC-23 test now has named positive cases (legitimate `.join`/`.format`/`%` patterns that must NOT be flagged).
- New **R8** risk added documenting the structural invariant that cross-module `TypeRefIR` never targets `ScalarTypeSpecIR`.

## What to do

1. Read iter1 review at `specs/011-cross-module-type-refs/artifacts/planning/iter1-gauge.md`.
2. Read updated plan at `specs/011-cross-module-type-refs/plan.md`.
3. Verify each iter1 BLOCKING / WARNING is resolved.
4. Look for new issues.

## What to evaluate

- **B1 fix:** Read the updated SV/Python/C++ component sections. Confirm view-model fields carry only semantic parts. Confirm templates carry the literal keywords. Confirm AC-23 will not flag the planned view models.
- **B2 fix:** Confirm AC-6's `--namespace=proj::lib` path is now covered with concrete fixture/goldens.
- **B3 fix:** NFR-4 perf gate — is `tests/test_perf_gen.py` concrete enough? Does the `perf_baseline.json` capture process work given the spec memory note that the perf gate is currently open?
- **W1-W4:** Each resolution applied?
- **No regressions** from earlier resolutions (CL-1 through CL-10 still reflected).

## Output format

```
# Gauge Review — Planning Iteration 2

## Summary
(2-3 sentences)

## Iter1 Issue Resolution

For each iter1 BLOCKING (B1, B2, B3) and WARNING (W1, W2, W3, W4):
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

If iter1's BLOCKING items are all resolved AND no new BLOCKING emerges, APPROVE. WARNINGs alone do not require revision.

Save to `specs/011-cross-module-type-refs/artifacts/planning/iter2-gauge.md`.
