# Gauge Review — Iteration 2

### ISSUE-1: SV helper width semantics still contradict themselves
**Severity:** BLOCKING
**Section:** FR-4: SystemVerilog backend
**Description:** FR-4 says `LP_*_WIDTH` is data-only and excludes padding, then says the helper class `WIDTH` accounts for alignment padding. Current helper classes use `WIDTH = LP_*_WIDTH`, so this is ambiguous. Fix by explicitly defining helper `WIDTH` as data-only and `BYTE_COUNT` as serialized byte count.

### ISSUE-2: Nested struct width calculation is underspecified and conflicts with existing behavior
**Severity:** BLOCKING
**Section:** FR-3, FR-7, Out of Scope
**Description:** The formula `byte_count(field_data_width)` is wrong for struct-typed fields. Existing nested structs use the nested struct's serialized byte count, not `byte_count(data_width)`. Fix by defining a recursive `serialized_field_byte_count`.

### ISSUE-3: `from_bytes` size semantics are not explicit
**Severity:** WARNING
**Section:** FR-5, FR-6
**Description:** `from_bytes` should require exactly `BYTE_COUNT` bytes, consistent with existing behavior.

### ISSUE-4: Backend test acceptance is too vague for SV and C++
**Severity:** WARNING
**Section:** AC-9, AC-10
**Description:** "Round-trip correctly" is not a concrete test method. Clarify how round-trips are verified.

### ISSUE-5: Template-first is stated but not acceptance-tested
**Severity:** NOTE
**Section:** FR-9
**Description:** Current backends use inline string construction, not templates. Template migration is a separate effort.

VERDICT: REVISE
