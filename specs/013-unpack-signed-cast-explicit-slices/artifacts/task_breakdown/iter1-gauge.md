Ripgrep is not available. Falling back to GrepTool.
MCP issues detected. Run /mcp list for status.# Gauge Review — Task Breakdown, Iteration 1

## Summary
The proposed task list provides a robust, atomic, and byte-parity-preserving path for implementing Spec 013. The division into two commits—one for non-breaking view model extensions (T-001) and one for the template update and golden refresh (T-002)—correctly manages the transition while keeping the test suite green. The implementation notes are highly detailed and correctly reflect the specific edge cases (such as the mutual exclusivity of type-ref and signed casts) defined in the clarifications.

## Plan-to-Task Coverage
- C-1 (`SvSynthStructUnpackFieldView`): covered-by T-001.
- C-2 (`_build_struct_pack_unpack`): covered-by T-001.
- C-3.1 (scalar_alias macro): covered-by T-002.
- C-3.2 (struct macro): covered-by T-002.
- C-4 (golden refresh): covered-by T-002.
- C-5 (view-test alignment): covered-by T-002 verify (confirmed as no-op).

## AC Traceability
- AC-1 (offset removal): Verified by T-002 grep check.
- AC-2 (literal slices): Verified by T-002 grep check.
- AC-3 (parity preservation): Verified by T-002 hand-verification on `header_t`.
- AC-4 (signed-inline field): Verified by T-002 grep on `struct_signed` golden.
- AC-5 (signed scalar alias): Verified by T-002 grep on scalar goldens.
- AC-6 (type-ref consistency): Verified by T-002 spot-check on type-ref fields.
- AC-7 (unittest green): Verified at the end of both T-001 and T-002.
- AC-8 (basedpyright green): Verified at the end of both T-001 and T-002.
- AC-9 (Verilator delta): Explicitly deferred to the validation stage as per project standards.
- AC-10 (part-select 1-bit): Verified by T-002 hand-verification (e.g., `flag_t`).

## Issues

### BLOCKING
None.

### WARNING
None.

### NOTE
- **T-002 Golden Refresh:** While the manual refresh pattern is clearly described, it is worth noting that if the implementer discovers an existing `piketype gen --update-goldens` or similar flag during the "identify" step, they should prioritize it to ensure consistency with repo tooling.

## Constitution Alignment
The tasks are in strict alignment with the Project Constitution. They uphold the **Single source of truth** (Principle 1) by deriving all changes from the view model, preserve **Immutable boundaries** (Principle 2) by avoiding IR changes, and ensure **Deterministic output** (Principle 3) by pre-computing bit-slices. The move from simulation-time `offset` accumulators to codegen-time literals strongly supports **Correctness over convenience** (Principle 4).

## Verdict
VERDICT: APPROVE
