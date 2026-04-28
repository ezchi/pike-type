# Gauge Review — Iteration 3

### ISSUE-1: Existing padding behavior misstated
**Severity:** WARNING
**Section:** Overview / FR-4
**Description:** The overview says trailing alignment padding is "treated identically to existing per-field padding" and describes existing padding as unsigned, zero-filled, and ignored. That is false for signed per-field padding, which is sign-extended and validated. Fix the overview wording: trailing alignment padding is always zero-filled and ignored, unlike signed per-field padding.

### ISSUE-2: Nested alignment lacks explicit acceptance coverage
**Severity:** WARNING
**Section:** Acceptance Criteria
**Description:** FR-3/FR-7 correctly define recursive serialized width for struct-ref fields. AC-8 does not require a nested aligned-struct fixture. Add one acceptance case.

Iteration 2 blocking issues are resolved. The WIDTH/BYTE_COUNT contradiction is fixed, and the recursive nested width formula is now explicit enough to implement.

VERDICT: APPROVE
