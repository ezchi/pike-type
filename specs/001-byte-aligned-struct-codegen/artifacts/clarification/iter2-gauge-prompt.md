# Gauge Review: Clarification — Iteration 2

You are the Gauge reviewer for the Steel-Kit Forge-Gauge loop. Your job is to critically review the clarifications and spec updates produced by the Forge.

## Context

**Project:** typist — a Python-based code generation tool that produces SystemVerilog, C++, and Python from a DSL.  
**Spec ID:** 001-byte-aligned-struct-codegen  
**Stage:** Clarification  
**Iteration:** 2

Iteration 1 established sign extension for signed scalar padding in `unpack`, `to_bytes`, and `to_slv`. The Gauge found 5 MAJOR issues:

1. FR-7, FR-8, FR-9 still said "padding zeros" for C++/Python backends
2. Definitions, FR-1, FR-2 still said "zero-fill bits"
3. FR-10 still said "zero-filled"
4. FR-6 `from_bytes()` wording was ambiguous about padding in deserialized result
5. Missing acceptance criteria for signed struct-member `unpack` and cross-language `to_bytes()`

Iteration 2 addresses all 5 findings.

## Files to Review

Read and review these files:

1. **Clarifications:** `specs/001-byte-aligned-struct-codegen/clarifications.md`
2. **Updated spec:** `specs/001-byte-aligned-struct-codegen/spec.md`
3. **Spec diff (iteration 2):** `specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter2-spec-diff.md`
4. **Project constitution:** `.steel/constitution.md`
5. **Previous gauge review:** `specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter1-gauge.md`

## Review Checklist

### Resolution of Iteration 1 Findings
For each of the 5 MAJOR findings from iteration 1, verify:
1. Was the finding correctly addressed?
2. Was the fix applied to all affected sections of spec.md?
3. Are the changes internally consistent?

### Clarifications Review
1. Are all new clarifications (C-9 through C-13) logically sound?
2. Was C-3 correctly reclassified from [NO SPEC CHANGE] to [SPEC UPDATE]?
3. Are all [SPEC UPDATE] clarifications properly reflected in spec.md?

### Spec Consistency Check
1. Search the entire spec.md for any remaining instances of "zero-fill" or "zero-filled" or "padding zeros" that should now reference the signedness-dependent fill policy.
2. Are all cross-references between FRs consistent?
3. Do the new acceptance criteria (AC-21, AC-22) have correct expected values?
4. Is the changelog complete and accurate?

### Missed Issues
1. Are there any remaining sections that use "zero" language when describing padding for signed fields?
2. Are there any contradictions between the updated sections?
3. Are there any edge cases not covered (e.g., signed scalar that is already byte-aligned, i.e., 8-bit signed with 0 padding)?

### Constitution Compliance
1. Does the complete set of changes align with the constitution's principles?

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

Use APPROVE only if there are no CRITICAL or MAJOR findings.
