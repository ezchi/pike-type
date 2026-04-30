# Gauge Verification — Validation Iteration 3

## Summary

Iter3 materially fixes the FR-16, AC-6, AC-18, and AC-19 evidence gaps: the fixtures, goldens, namespace test, multiple_of test, and generated-code runtime test are real, and the live unittest suite passes 292 tests with 1 skip.

The validation report is still not factually acceptable. It keeps NFR-4 as a "legitimate" DEFERRED despite the spec and the DEFERRED policy, keeps FR-3 DEFERRED with a stale "no integration test" claim even though the integration fixture now exists, and still marks AC-24 PASS while admitting the output does not match the exact snippet required by the spec.

## Iter1/Iter2 Issue Resolution

- ✓ resolved - Test output zero bytes. `iter3-test-output.txt` is non-empty and reports `Ran 292 tests` / `OK (skipped=1)`. I also reran `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover tests/ -v`; it passed with 292 tests and 1 skip. Warning: the artifact is 6 lines, not the 292-line verbose output described in the prompt, and `validation.md` still points at `iter1-test-output.txt`.
- ✓ resolved - FR-16. The primary `foo.py` now defines `byte_t`, `addr_t`, `cmd_t`, and `perms_t`; `bar.py` imports and references all four. The SV golden has cross-module `byte_t`, `addr_t`, `cmd_t`, and `perms_t` fields in `bar_t`.
- ✓ resolved - AC-6. `tests/goldens/gen/cross_module_type_refs_namespace_proj/` exists, `bar_types.hpp` contains `::proj::lib::foo::byte_ct field1`, and `CrossModuleNamespaceIntegrationTest` generates with `--namespace=proj::lib` and byte-compares the golden tree.
- ~ partial - FR-3 / AC-18. AC-18 itself is resolved: the `cross_module_struct_multiple_of` fixture and golden exist, the test asserts `LP_BAR_WIDTH = 24`, `LP_BAR_BYTE_COUNT = 4`, and `_align_pad`, and the live suite passes. FR-3 is not resolved in the validation report because `validation.md` still marks it DEFERRED and falsely says no integration test was added.
- ✓ resolved - AC-19. `tests/test_runtime_py_cross_module.py` adds the generated Python golden root to `sys.path` and imports `alpha.piketype.foo_types` / `alpha.piketype.bar_types` via `importlib.import_module`, so it executes generated code, not stubs. Warning: it checks the first two bytes of a 6-byte expanded fixture rather than the original literal `b"\xab\xcd"` two-field snippet.
- ✓ resolved - AC-22 / NFR-5 classification. The report now marks basedpyright as FAIL, and `UV_CACHE_DIR=/tmp/uv-cache uv run basedpyright src/piketype` exits 1 with exactly 100 errors. The baseline count in the report is not exact: analyzing an exported `develop` tree with the current environment reports 65 errors, so this branch is +35 errors under that comparison, not "62 plus 19".
- ✗ unresolved - NFR-4. Iter1 correctly flagged this invalid DEFERRED. It is still DEFERRED, and `validation.md` explicitly admits NFR-4 is in-scope and not listed in Out of Scope. Under the stated policy, that must be FAIL unless measured.
- ✗ unresolved - AC-24. The spec requires the reproducer to match the Expected snippet exactly. `validation.md` still marks PASS while admitting the implementation emits `{pack_byte(...), ...}` rather than the exact `{a.field1, a.field2}` form.

## New Issues

### BLOCKING

- NFR-4 is still incorrectly DEFERRED. The spec defines NFR-4 as a hard performance requirement, and the Out of Scope list does not include performance. The report's rationale is "not believed to regress" plus environment-dependent baseline capture; that does not satisfy the DEFERRED policy.
- FR-3 is incorrectly DEFERRED in the report. The report says no integration test was added and gives a test plan to add `tests/fixtures/cross_module_struct_multiple_of/`, but that fixture, golden tree, and integration tests already exist. The correct classification should be PASS if the new AC-18 evidence is accepted, not DEFERRED.
- AC-24 remains incorrectly PASS. The report explicitly says the output is only semantically identical and the spec example should be updated. That is not a PASS for an AC requiring exact snippet match.

### WARNING

- The iter3 saved test output is non-empty, but it is not the verbose `-v` output implied by `validation.md`; it contains dot output only. `validation.md` also cites `iter1-test-output.txt` and says AC-20 has 285 tests, both stale for iter3.
- The basedpyright failure is real, but the report's baseline arithmetic is inaccurate in my check: current branch is 100 errors; exported `develop` checked through the current environment is 65 errors. The errors are static typing/lint categories and tests pass, but full correctness impact from every new type-check error is UNKNOWN.
- AC-19's runtime test is real and valuable, but it no longer asserts the exact two-byte `bar_t(...).to_bytes() == b"\xab\xcd"` shape written in the spec because the primary fixture now has additional fields.

### NOTE

- No live test regression found: `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover tests/ -v` passed with 292 tests and 1 skip.
- The FR-16 spot-check passed: all four type kinds are present in the fixture and goldens.
- The AC-6 spot-check passed: the namespace golden exists and the integration test loads it.
- The AC-18 spot-check passed: 24 data bits plus 8 alignment bits produces 4 bytes, and `_align_pad` is present.
- The AC-19 spot-check passed for generated-code execution through the golden import path.

VERDICT: REVISE
