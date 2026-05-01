# Gauge Verification — Validation Stage, Iteration 5 (final)

You are the **Gauge** in a validation loop. This is iter5 — the last iteration in the configured budget. Iter4 issued REVISE: NFR-4 still incorrectly DEFERRED, summary counts wrong (44 vs claimed 45), test output / AC-20 count stale.

## What changed since iter4

- **NFR-4 → FAIL**: per gauge's strict DEFERRED policy reading.
- **Summary**: 44 PASS / 4 FAIL / 0 DEFERRED (matches the table content).
- **AC-20** count corrected 285 → 292.
- **Test output reference** updated to `iter4-test-output.txt`.

## What to do

1. Read iter4 gauge review at `specs/011-cross-module-type-refs/artifacts/validation/iter4-gauge.md`.
2. Read iter5 validation report at `specs/011-cross-module-type-refs/validation.md`.
3. Verify each iter4 BLOCKING/WARNING is resolved.
4. Recount the verdicts in the FR/NFR/AC tables and confirm Summary matches.

## What to evaluate

- Do the table counts match the Summary line (44/4/0)?
- Is NFR-4 marked FAIL?
- Are stale references (iter1-test-output, 285) cleaned up?
- AC-20 = 292?

## Output format

```
# Gauge Verification — Validation Iteration 5

## Summary
(2 sentences)

## Iter4 Issue Resolution

For each iter4 BLOCKING (NFR-4 DEFERRED, Summary count) and WARNING (stale references):
- ✓ resolved
- ✗ unresolved

## Self-check
(does the Summary count match the table content?)

## New Issues
### BLOCKING
...

VERDICT: APPROVE
```
or `VERDICT: REVISE`.

This is the last iteration. APPROVE if iter4's issues are resolved AND no new BLOCKING.

Save to `specs/011-cross-module-type-refs/artifacts/validation/iter5-gauge.md`.
