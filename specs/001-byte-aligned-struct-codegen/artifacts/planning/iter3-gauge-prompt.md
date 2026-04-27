# Gauge Review: Planning — Iteration 3

You are the Gauge reviewer. This iteration addresses the 2 remaining MAJOR findings from iteration 2.

## Previous Findings (iter2)
1. MAJOR: "Value vector in golden files" is not executable coverage — need runtime tests
2. MAJOR: Byte-order migration mitigation depends on goldens, not executed checks

## Changes Made
1. Added "Executable Runtime Tests (Python)" section with `tests/test_runtime_bytes.py`:
   - Imports generated Python modules, instantiates objects with known values
   - Calls `to_bytes()` and asserts exact byte sequences from the spec
   - Calls `from_bytes()` and asserts round-trip identity
   - Tests signed `from_bytes()` with mismatched padding → `ValueError`
   - Includes full test vector table (6 positive, 3 signed validation)
2. Documented why only Python runtime tests: project has no C++ build or SV simulation in test pipeline. C++/SV verified via golden comparison.
3. Updated AC coverage matrix: "value vector" → "Py runtime" referencing executed tests
4. Updated Phase 6 to create `tests/test_runtime_bytes.py` as first step
5. Updated byte-order risk mitigation to reference runtime tests as primary regression anchor

## Files to Review
1. **Updated plan:** `specs/001-byte-aligned-struct-codegen/plan.md`
2. **Specification:** `specs/001-byte-aligned-struct-codegen/spec.md` (for AC verification)
3. **Constitution:** `.steel/constitution.md` (testing strategy alignment)

## Review Checklist
1. Do the changes resolve both MAJOR findings?
2. Is `tests/test_runtime_bytes.py` a concrete and adequate executable verification strategy?
3. Is the justification for Python-only runtime tests sound?
4. Does the byte-order mitigation now have executable teeth?
5. Any remaining gaps?

End with `VERDICT: APPROVE` or `VERDICT: REVISE`.
