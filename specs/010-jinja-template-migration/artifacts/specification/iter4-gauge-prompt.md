# Gauge Review Prompt — Specification Iteration 4

You are the **Gauge** in a dual-agent Forge-Gauge loop.

This is **iteration 4**. Iteration 3 returned `VERDICT: REVISE` with these issues:

1. BLOCKING — AC-F5 wheel-filename glob: spec used `piketype-*.whl` but the project name is `pike-type`, which `setuptools` normalizes to `pike_type-*.whl` in the wheel filename.
2. WARNING — FR-21 pattern 2 only matches `byte_count` arithmetic when `byte_count` is on the left side of the operator; it must be symmetric to also catch e.g. `2 * byte_count`.

Both fixes were stated to be surgical edits. No other content was changed in iter4.

## Inputs to Review

1. **Specification under review:** `specs/010-jinja-template-migration/spec.md` (iteration 4).
2. **Iteration-3 review for context:** `specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md`.

## Review Instructions

1. Confirm only the two iter3 issues were touched. If anything else was modified or regressed, flag it. (You may diff iter3-forge against iter4-forge in the artifacts directory.)
2. Confirm AC-F5 now uses the correct wheel filename pattern (`pike_type-*.whl`) and that the surrounding sentence is consistent.
3. Confirm FR-21 pattern 2 is now symmetric (either `byte_count` on the left or on the right of an arithmetic operator).
4. Reconfirm that no new BLOCKING issue exists and that the spec is approvable.

Apply the same severity scheme: `BLOCKING`, `WARNING`, `NOTE`. End with exactly one of `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after the verdict line.

If the only outstanding items are existing Open Questions Q-1..Q-4 (which are properly framed and will be addressed in clarification), APPROVE.
