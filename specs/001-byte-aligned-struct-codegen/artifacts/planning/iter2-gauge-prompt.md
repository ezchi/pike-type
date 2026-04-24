# Gauge Review: Planning — Iteration 2

You are the Gauge reviewer. This iteration addresses all 4 findings from iteration 1.

## Previous Findings (iter1)
1. MAJOR: Missing AC coverage matrix and executable value-vector tests
2. MAJOR: Float division in padding computation — need integer-only helpers
3. MAJOR: Missing byte-order migration risk (existing backends use little-endian)
4. MINOR: Inline wide unsigned struct members not called out

## Changes Made
1. Added full AC-1 through AC-25 coverage matrix with test type and fixture mapping
2. Replaced `math.ceil(w/8)` with centralized integer helpers: `(width+7)//8` and `(-width)%8`
3. Added byte-order migration risk with High/High severity and fixed test vectors
4. Added explicit note about inline anonymous scalars >64-bit in C++ backend section
5. Rewrote cross-language verification to note golden comparison alone is insufficient — added value-vector strategy

## Files to Review
1. **Updated plan:** `specs/001-byte-aligned-struct-codegen/plan.md`
2. **Specification:** `specs/001-byte-aligned-struct-codegen/spec.md`
3. **Constitution:** `.steel/constitution.md`

## Review Checklist
1. Do the changes resolve all 4 findings?
2. Is the AC coverage matrix complete (all 25 ACs mapped)?
3. Are the integer helpers correct for arbitrary-width scalars?
4. Is the byte-order migration risk adequately mitigated?
5. Are there any remaining gaps?

End with `VERDICT: APPROVE` or `VERDICT: REVISE`.
