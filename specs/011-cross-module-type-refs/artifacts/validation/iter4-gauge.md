# Gauge Verification — Validation Iteration 4

## Summary

Iter4 resolves the stale FR-3 classification and correctly downgrades AC-24 to FAIL, but it still leaves NFR-4 incorrectly DEFERRED. The validation report also has a factual count mismatch: the Results tables contain 44 PASS / 3 FAIL / 1 DEFERRED, not the Summary's 45 PASS / 2 FAIL / 1 DEFERRED.

## Iter3 Issue Resolution

- ✗ unresolved - NFR-4 DEFERRED. The spec makes NFR-4 an in-scope performance requirement (`spec.md:370`), and the Out of Scope list (`spec.md:420-428`) does not include performance measurement, baseline capture, or environment stability. The plan explicitly says the benchmark baseline is captured and committed as `tests/perf_baseline.json` (`plan.md:310-320`), but that file is absent and `tests/test_perf_gen.py:56-58` skips when it is missing. Static O(n) complexity analysis is useful risk evidence, but it does not satisfy the DEFERRED policy for an in-scope NFR. This remains a hidden FAIL unless the perf gate is measured or the spec/plan is amended.
- ✓ resolved - FR-3 DEFERRED. The `cross_module_struct_multiple_of` fixture now genuinely covers a cross-module DSL object under `.multiple_of(32)`: `bar.py` imports `byte_t` from `foo.py` and uses it for three members before applying `.multiple_of(32)` (`tests/fixtures/cross_module_struct_multiple_of/project/alpha/piketype/bar.py:3-11`). The golden proves the expected 24-bit data width, 4-byte aligned byte count, and trailing `_align_pad` (`tests/goldens/gen/cross_module_struct_multiple_of/sv/alpha/piketype/bar_pkg.sv:8-15`), and `CrossModuleStructMultipleOfIntegrationTest` byte-compares the generated tree and asserts those alignment markers (`tests/test_gen_cross_module.py:118-138`). I also reran `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover tests/ -v`; it passed with 292 tests and 1 skip.
- ✓ resolved - AC-24 PASS. AC-24 is correctly FAIL now. The spec's Expected snippet requires `return {a.field1, a.field2};` and direct unpack slices (`spec.md:93-104`), while the actual golden emits `pack_byte(...)` and `unpack_byte(...)` wrappers (`tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/bar_pkg.sv:20-37`). That mismatch violates AC-24's "exactly" wording even though the implementation is semantically consistent with the SV struct pack/unpack macro behavior (`src/piketype/backends/sv/templates/_macros.j2:99-100`, `src/piketype/backends/sv/templates/_macros.j2:127-129`).

## New Issues

### BLOCKING

- The Summary counts are wrong. Counting the Results tables gives 17 FR PASS, 5 NFR PASS, 22 AC PASS, 3 FAIL rows (`NFR-5`, `AC-22`, `AC-24`), and 1 DEFERRED row (`NFR-4`): 44 PASS / 3 FAIL / 1 DEFERRED. The report claims 45 PASS / 2 FAIL / 1 DEFERRED while also claiming a 48-item total, so it is internally inconsistent. Treating `NFR-5 / AC-22` as one combined failure would contradict the separate NFR and AC rows and the stated 17 FR + 7 NFR + 24 AC total.

### WARNING

- `validation.md` still has stale test-output evidence. The Test Execution table reports 292 pass / 1 skip, and `iter4-test-output.txt` plus my live rerun both show `Ran 292 tests`, but the report points to `iter1-test-output.txt` and AC-20 still says `285 tests, 0 failures` (`validation.md:24`, `validation.md:29`, `validation.md:90`).

### NOTE

- No silent PASS downgrade was found. The FR-3 change to PASS and AC-24 change to FAIL are both explicit in the report, and the cross-module `multiple_of()` fixture evidence is real.
- The implementation's performance complexity argument is plausible, but plausibility is not validation. The current artifact proves only that the perf gate exists and skips without a committed baseline.

VERDICT: REVISE
