# Gauge Verification — Validation Stage, Iteration 4

You are the **Gauge** in a validation loop. Iter3 returned REVISE: NFR-4 still incorrectly DEFERRED, FR-3 stale DEFERRED, AC-24 incorrectly PASS. Iter4 reclassified per your reading.

## What changed since iter3

- **FR-3 → PASS**: AC-18 fixture (`tests/fixtures/cross_module_struct_multiple_of/`) was added in iter3 implementation but the validation report still listed it as DEFERRED. iter4 corrects to PASS.
- **AC-24 → FAIL**: the implementation does not match the spec's "Expected" snippet *exactly* — it correctly emits `pack_byte()`/`unpack_byte()` wrappers for cross-module `TypeRefIR` fields, but the spec example showed simplified `{a.field1, a.field2}` without wrappers. Reclassified FAIL with a note about spec-example needing amendment.
- **NFR-4 remains DEFERRED**: test plan provided; static complexity analysis attached; cannot be measured without environment-stable baseline capture.

Net: 45 PASS / 2 FAIL / 1 DEFERRED.

## What to do

1. Read iter3 gauge review at `specs/011-cross-module-type-refs/artifacts/validation/iter3-gauge.md`.
2. Read iter4 validation report at `specs/011-cross-module-type-refs/validation.md`.
3. Read iter4 test output at `specs/011-cross-module-type-refs/artifacts/validation/iter4-test-output.txt`.
4. Verify each iter3 BLOCKING is resolved.

## What to evaluate

- **FR-3 reclassification**: does AC-18 fixture genuinely cover what FR-3 requires (`_serialized_width_from_dsl` walks cross-module DSL objects under `multiple_of`)? Read `tests/fixtures/cross_module_struct_multiple_of/project/alpha/piketype/bar.py` and the corresponding golden `bar_pkg.sv`.
- **AC-24 FAIL acceptance**: agree that "exactly" cannot be met when the spec example was inaccurate? Verify by reading the spec Overview (lines around the "Expected" snippet) and the actual golden `tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/bar_pkg.sv`.
- **NFR-4 DEFERRED legitimacy**: still arguable. The implementation's complexity analysis (constant-factor O(n)) is the only available evidence. Is this a legitimate defer or a hidden FAIL?
- **No regressions**: counts match Summary; no PASS items downgraded silently.

## Output format

```
# Gauge Verification — Validation Iteration 4

## Summary
(2 sentences)

## Iter3 Issue Resolution

For each iter3 BLOCKING (NFR-4 DEFERRED, FR-3 DEFERRED, AC-24 PASS):
- ✓ resolved
- ✗ unresolved (explain)

## New Issues
### BLOCKING
...
### WARNING
...
### NOTE
...

VERDICT: APPROVE
```
or `VERDICT: REVISE`.

If iter3's BLOCKINGs are resolved AND no new BLOCKING emerges, APPROVE. WARNINGs alone do not require revision.

Save to `specs/011-cross-module-type-refs/artifacts/validation/iter4-gauge.md`.
