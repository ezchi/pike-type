# Gauge Review — Planning Stage, Iteration 3

You are the **Gauge** in a Forge-Gauge dual-LLM planning loop. Iter2 issued REVISE: 1 BLOCKING (basedpyright `--strict` flag invalid) plus 3 WARNINGs.

## What changed since iter2

- **B1 fix:** AC-22 gate command updated to `basedpyright src/piketype tests/` (strict mode is configured in `pyproject.toml:[tool.basedpyright].typeCheckingMode = "strict"`).
- **W1 fix:** Perf gate now iterates every fixture in `tests/fixtures/`, not just one. Fails on >5% total or >10% per-fixture regression.
- **W2 fix:** Testing strategy summary now says "four FR-8 collision sub-cases" matching the detailed list.
- **W3 fix:** Commit D wording rewritten — same-module synth import is rendered by the template using `module.ref.basename` directly; no view-model field carries a rendered line.

## What to do

1. Read iter2 review at `specs/011-cross-module-type-refs/artifacts/planning/iter2-gauge.md`.
2. Read updated plan at `specs/011-cross-module-type-refs/plan.md`.
3. Verify each iter2 BLOCKING / WARNING is resolved.
4. Look for new issues.

## What to evaluate

- **B1:** Is `basedpyright src/piketype tests/` the correct invocation? Verify against `pyproject.toml`.
- **W1:** Does the perf gate now match NFR-4's "existing fixture suite" wording?
- **W2:** Does the testing strategy summary line agree with the detailed component list?
- **W3:** Does Commit D wording match the Components section's no-rendered-line policy?
- **No regressions** from earlier resolutions.

## Output format

```
# Gauge Review — Planning Iteration 3

## Summary
(2 sentences)

## Iter2 Issue Resolution

For each iter2 BLOCKING (B1) and WARNING (W1, W2, W3):
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

If iter2's BLOCKING is resolved AND no new BLOCKING emerges, APPROVE.

Save to `specs/011-cross-module-type-refs/artifacts/planning/iter3-gauge.md`.
