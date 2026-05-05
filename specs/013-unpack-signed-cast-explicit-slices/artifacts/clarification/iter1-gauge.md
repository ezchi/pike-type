Ripgrep is not available. Falling back to GrepTool.
MCP issues detected. Run /mcp list for status.(node:47882) [DEP0190] DeprecationWarning: Passing args to a child process with shell option true can lead to security vulnerabilities, as the arguments are not escaped, only concatenated.
(Use `node --trace-deprecation ...` to show where the warning was created)
# Gauge Review — Clarification, Iteration 1

## Summary
The clarification iteration successfully identifies that the existing `struct_signed` fixture covers the signed-inline-field requirement, which allows for reduced churn. However, the spec update is incomplete and inconsistent regarding the resolution of OQ-3, and the documentation of the spec changes in the diff and summary table is contradictory.

## Spec-Diff Audit
- Change 1 (NFR-4): applied-correctly.
- Change 2 (AC-4): applied-correctly.
- Change 3 (AC-9): applied-correctly.
- MISSING: The promised strike of "new fixture" language in the "Out of Scope" or "Open Questions" summary was not applied; `spec.md` line 269 still explicitly states "OQ-3 → new fixture, do not edit existing fixtures", directly contradicting the updated AC-4 (line 217).

## Clarification Audit
- Q1: factually correct. Verified `mixed_t` in `struct_signed/types.py` declares `field_u = Logic(5, signed=True)` and the existing golden indeed uses the `offset` accumulator for it.
- Q2: factually correct. The slice-arithmetic formula matches the existing template's accumulator logic when iterating the field list in reverse.
- Q3: factually correct. The categories of affected goldens are sound; confirmed that `cross_module_type_refs` contains structs (`addr_t`, `bar_t`) and is thus affected.
- Q4: factually correct. SystemVerilog bit indexing on packed signed values is identity-preserving; no change to the padding line is required.
- Q5: factually correct. Loosening AC-9 to a delta-check is rigorous and provides a clear mechanism for implementation-stage validation.
- Q6: factually correct. The implementation contract for `is_signed` is consistent with the requirements in FR-1.1 and FR-1.3.

## Issues

### BLOCKING
- **Contradictory Resolution of OQ-3.** `spec.md` line 269 in the "Open Questions" summary still says "OQ-3 → new fixture, do not edit existing fixtures.", while the updated AC-4 (line 217) correctly states "OQ-3 is resolved by reusing the existing fixture, not by creating a new one." This internal inconsistency must be resolved to prevent confusion during the implementation and testing phases.
- **Contradictory Spec-Update Documentation.** `clarifications.md` claims in its summary table that the "Out of Scope" section was amended to strike "new fixture" language, but `artifacts/clarification/iter1-spec-diff.md` explicitly states that section is "unchanged". Neither document correctly identifies that the summary in "Open Questions" was the actual target of the strike.

### WARNING
- **Implicit View Model Requirements.** While Q2 is noted as an implementation detail, the `SvSynthStructUnpackFieldView` dataclass in `view.py` is currently missing the `slice_high` and `slice_low` fields required by NFR-1. The clarification should have explicitly noted the need to add these fields to the dataclass to ensure the implementation phase doesn't miss this structural requirement.

### NOTE
- None.

## Constitution Alignment
The move toward pre-computing slice indices in Python aligns with the "Backend Python prepares view models; templates handle presentation only" principle. The use of explicit signed casts supports the "Correctness over convenience" principle by addressing lint warnings at the source.

## Verdict
VERDICT: REVISE
