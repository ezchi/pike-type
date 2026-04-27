# Gauge Review: Clarification — Iteration 1

**Provider:** codex (gpt-5.5)  
**Date:** 2026-04-24  

## Findings

**Section**: Spec Update Review  
**Severity**: MAJOR  
**Finding**: C-2 says FR-8 and FR-9 are impacted, but `spec.md` still requires C++ and Python struct `to_bytes()` to use padding zeros. FR-7 also still describes scalar serialization with zero padding only. This contradicts FR-6, FR-12, AC-16, and the cross-language invariant.  
**Recommendation**: Update FR-7, FR-8, and FR-9 so signed scalar `to_bytes()` uses sign-extended padding, while unsigned remains zero-padded.

**Section**: Missed Updates  
**Severity**: MAJOR  
**Finding**: The Definitions, FR-1, and FR-2 still define padding as "zero-fill bits." That is now false for signed scalar fields after `unpack`, `to_slv`, and `to_bytes`. FR-3 also does not explain that generated `_pad` members for signed fields may legally be non-zero.  
**Recommendation**: Redefine padding as MSB-side byte-alignment bits whose fill policy depends on signedness and operation. Update FR-3 to state signed `_pad` fields may contain replicated sign bits.

**Section**: Missed Updates  
**Severity**: MAJOR  
**Finding**: FR-10 still says cross-language padding placement is "zero-filled." That directly conflicts with the new signed-field serialization rule.  
**Recommendation**: Change FR-10 item 2 to require identical padding placement and fill policy: zero for unsigned scalar fields, sign-extended for signed scalar fields.

**Section**: Clarifications Review  
**Severity**: MAJOR  
**Finding**: C-3 is incorrectly classified as `[NO SPEC CHANGE]`. FR-6 still says `from_bytes()` produces a deserialized struct with all padding bits zero. That wording is now ambiguous or wrong for signed fields unless `from_bytes()` only stores logical field values and never materializes `_pad` fields.  
**Recommendation**: Update FR-6 to explicitly define `from_bytes()` output semantics for signed fields: either it stores only logical values, or any materialized padded struct must use the same signed padding policy as `to_slv`/`unpack`.

**Section**: Acceptance Criteria  
**Severity**: MAJOR  
**Finding**: AC-16 covers signed scalar `to_bytes()`, and AC-19 covers `to_slv()`, but there is no acceptance criterion for the user's primary requirement: signed struct-member `unpack` must sign-extend `_pad`. There is also no explicit C++/Python signed struct `to_bytes()` acceptance case.  
**Recommendation**: Add ACs for a struct containing a non-byte-wide signed field, verifying `unpack` sets signed `_pad` bits to the sign bit and SV/C++/Python `to_bytes()` all emit the same sign-extended bytes.

**Section**: Clarifications Review  
**Severity**: INFO  
**Finding**: The worked examples are mathematically correct. `4'b1010` sign-extends to `8'b1111_1010` = `0xFA`, and signed 5-bit `-1` sign-extends to `0xFF`. C-6 is also correct: `pack(unpack(v)) == v` still holds because `pack` discards padding.  
**Recommendation**: No change needed for the arithmetic examples.

VERDICT: REVISE
