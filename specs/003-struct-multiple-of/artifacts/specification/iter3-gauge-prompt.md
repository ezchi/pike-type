# Gauge Review: Specification 003 — Struct `multiple_of(N)` Alignment (Iteration 3)

You are a strict technical reviewer (the "Gauge"). This is iteration 3. The spec was revised based on iteration 2 feedback.

## Changes from iteration 2

1. **ISSUE-1 (BLOCKING) — SV helper WIDTH contradiction:** Fixed. FR-4 now explicitly states: helper `WIDTH` = data-only (= `LP_*_WIDTH`), unchanged. Helper `BYTE_COUNT` = serialized byte count (= `LP_*_BYTE_COUNT`), updated. AC-1 now specifies both helper `WIDTH=17` and `BYTE_COUNT=4`.
2. **ISSUE-2 (BLOCKING) — Nested struct width formula:** Fixed. FR-3 now defines a recursive serialized width calculation: scalar fields use `byte_count(data_width) * 8`, struct-ref fields use the target struct's total serialized width (including its own alignment_bits). FR-7 mirrors this. Out-of-scope section updated to reference FR-3's recursive definition.
3. **ISSUE-3 (WARNING) — from_bytes size semantics:** Fixed. FR-5 and FR-6 now explicitly state `from_bytes()` requires exactly `BYTE_COUNT` bytes, consistent with existing behavior.
4. **ISSUE-4 (WARNING) — Backend test acceptance vague:** Fixed. AC-9 clarified that SV pack/unpack are verified via golden-file comparison. AC-10 describes a concrete Python runtime round-trip test methodology.
5. **ISSUE-5 (NOTE) — Template-first not acceptance-tested:** Addressed in FR-9. Current backends use inline string construction for struct generation. This feature follows the existing pattern. Template migration is explicitly out of scope.

## Project Constitution (highest authority)

Read the file at: `.steel/constitution.md`

## Specification to Review

Read the file at: `specs/003-struct-multiple-of/spec.md`

## Review Checklist

1. **Completeness**: All pipeline layers covered?
2. **Clarity**: Unambiguous for an implementer?
3. **Testability**: Concrete, measurable acceptance criteria?
4. **Consistency**: Aligned with constitution and existing patterns?
5. **Feasibility**: Implementable with current architecture?
6. **Iteration 2 fixes**: All BLOCKING issues resolved?

## Issues Format

```
### ISSUE-N: <title>
**Severity:** BLOCKING / WARNING / NOTE
**Section:** <which section>
**Description:** <what's wrong and how to fix it>
```

## Verdict

End with exactly: `VERDICT: APPROVE` or `VERDICT: REVISE`
Only REVISE if BLOCKING issues remain.
