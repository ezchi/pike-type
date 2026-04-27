# Delta Gauge Review: Clarification — Iteration 3 (Delta 1)

You are the Gauge reviewer. This is a **delta review** — review ONLY the changes made in response to user feedback, not the full clarifications.

## User Feedback
"in FR-12 Signed Scalars as Struct Members section, the example `from_bytes({0x0A})` should raise error, as the 4-bit data is signed type, top 4-bit padding should be sign-extended."

## Summary of Change
`from_bytes()` for signed scalar fields now validates that padding bits match sign extension. Previously, padding was ignored for all fields (signed and unsigned). Now:
- **Unsigned fields**: padding still ignored (no change)
- **Signed fields with padding_bits > 0**: padding validated against `{P{data[W-1]}}`; mismatch raises error

Error types:
- SV: error via assertion or task return
- C++: `std::invalid_argument`
- Python: `ValueError`

## Files to Review

Read these files:
1. **Delta artifact:** `specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter3-delta-forge.md` (lists all changes and unmodified sections)
2. **Updated spec:** `specs/001-byte-aligned-struct-codegen/spec.md`
3. **Updated clarifications:** `specs/001-byte-aligned-struct-codegen/clarifications.md` (see C-14)
4. **Constitution:** `.steel/constitution.md`

## Review Checklist

1. Does each change correctly address the user's feedback (signed `from_bytes` should error on padding mismatch)?
2. Were any unrelated sections modified? (If so: REVISE)
3. Are the changes consistent with the rest of the spec and the constitution?
4. Was spec.md changelog updated correctly?
5. Is the user feedback fully addressed (no items left unaddressed)?
6. Are the error types appropriate for each backend (C++ exception, Python exception, SV)?
7. Is AC-23 correct — do the examples show valid padding mismatches?
8. Does the change introduce any contradiction with existing ACs (especially AC-12 for unsigned)?
9. Is the `from_slv()` behavior consistent — it still ignores padding per AC-19, which is acceptable since `from_slv` is SV-internal while `from_bytes` is the cross-language contract.

## Output Format

For each finding, state:
- **Section**: which part
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
