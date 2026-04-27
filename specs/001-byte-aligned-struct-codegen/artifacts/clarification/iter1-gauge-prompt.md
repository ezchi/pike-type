# Gauge Review: Clarification — Iteration 1

You are the Gauge reviewer for the Steel-Kit Forge-Gauge loop. Your job is to critically review the clarifications and spec updates produced by the Forge.

## Context

**Project:** typist — a Python-based code generation tool that produces SystemVerilog, C++, and Python from a DSL.  
**Spec ID:** 001-byte-aligned-struct-codegen  
**Stage:** Clarification  
**Iteration:** 1

The user requested clarification on signed scalar handling: `pack` extracts the raw bit pattern (unchanged), but `unpack` should perform sign extension to the `_pad` field. This enables C++ to use `std::int8_t` etc. directly from the byte-aligned representation.

## Files to Review

Read and review these files:

1. **Clarifications:** `specs/001-byte-aligned-struct-codegen/clarifications.md`
2. **Updated spec:** `specs/001-byte-aligned-struct-codegen/spec.md`
3. **Spec diff:** `specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter1-spec-diff.md`
4. **Project constitution:** `.steel/constitution.md`

## Review Checklist

### Clarifications Review
1. Are all clarifications (C-1 through C-8) logically sound and internally consistent?
2. Are the [SPEC UPDATE] vs [NO SPEC CHANGE] classifications correct?
3. Are the worked examples mathematically correct? Verify the bit patterns and hex values.
4. Does C-1 (sign extension in unpack) correctly address the user's requirement?
5. Is the rationale for sign extension sound — does it actually enable correct C++ `std::int8_t` mapping?
6. Is C-6 (round-trip invariant) correct — does `pack(unpack(v)) == v` still hold with sign extension?

### Spec Update Review
For each [SPEC UPDATE] clarification (C-1, C-2, C-5, C-8), verify:
1. Was the change correctly applied to spec.md?
2. Is the updated requirement consistent with the rest of the spec?
3. Were any unrelated sections modified?
4. Does the changelog entry accurately describe the change?
5. Were any requirements silently dropped or weakened?

### Missed Updates
1. Are there clarifications marked [NO SPEC CHANGE] that should actually update the spec?
2. Are there any sections of the spec affected by the sign-extension change that were NOT updated?
3. Do the C++ backend (FR-7, FR-8) and Python backend (FR-9) sections need updates for sign-extended `to_bytes()`?
4. Does FR-3 (SV typedef) need an update to describe that `_pad` fields for signed members may contain non-zero values?
5. Does the worked example in FR-10 need updating (it uses unsigned fields, so probably not)?
6. Are any acceptance criteria missing for the new signed behavior (beyond AC-16)?

### Constitution Compliance
1. Does the sign-extension change align with the constitution's principles (deterministic output, correctness over convenience, etc.)?
2. Are there any constitution constraints that conflict with the proposed changes?

## Output Format

For each finding, state:
- **Section**: which part of the review
- **Severity**: CRITICAL / MAJOR / MINOR / INFO
- **Finding**: what you found
- **Recommendation**: what should change

End with exactly one of:
```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

Use APPROVE only if there are no CRITICAL or MAJOR findings. Use REVISE if any CRITICAL or MAJOR findings exist.
