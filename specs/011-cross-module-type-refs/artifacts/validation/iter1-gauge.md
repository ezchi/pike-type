# Gauge Verification — Validation Iteration 1

## Summary

The Forge report is not factually accurate. The required verbatim test-output artifact is zero bytes, several in-scope requirements are deferred against the stated DEFERRED policy, and multiple PASS / PASS (partial) claims overstate actual coverage.

I independently ran `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover tests/`; the current checkout reports 285 tests passing with 1 skipped. That does not fix the Forge report, because its cited artifact at `specs/011-cross-module-type-refs/artifacts/validation/iter1-test-output.txt` contains no test names or pass results.

## PASS claim verification

- FR-1 / AC-7: `src/piketype/loader/python_loader.py:69-100` does implement snapshot/pre-clean/restore semantics, and `tests/test_loader.py:53-75` / `tests/test_loader.py:137-146` exercise sequential cleanup and cross-module identity. However, the cited validation artifact does not prove these tests passed because `iter1-test-output.txt` is empty.
- FR-2: `tests/test_freeze.py:58-78` checks a cross-module field freezes to `TypeRefIR` with module `alpha.piketype.foo`; `src/piketype/dsl/freeze.py:430-433` returns `TypeRefIR(module=module_ref, name=type_name, ...)` when the type object is found. Source supports the claim, but the saved test output does not.
- FR-4 / AC-15 / AC-16: `tests/test_freeze.py:81-140` verifies dependency collection for cross-module `type_ref`, same-module exclusion, and kind sorting. `tests/goldens/gen/cross_module_type_refs/piketype_manifest.json:6-10` contains the claimed `type_ref` dependency. This spot-check supports the code/golden claim.
- FR-9 / AC-2 / AC-3: `tests/test_gen_cross_module.py:74-88` asserts one `import foo_pkg::*;`, `byte_t field1/field2`, `LP_BYTE_WIDTH`, and `unpack_byte(`. The golden has the import and fields at `tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/bar_pkg.sv:5-13` and `unpack_byte` at lines 25 and 27. This supports AC-2/AC-3, not AC-24.
- FR-10 / AC-4: `tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/bar_test_pkg.sv:5-8` has `bar_pkg::*`, `foo_pkg::*`, then `foo_test_pkg::*` contiguously. This supports the golden claim.
- FR-11 / AC-5: `tests/goldens/gen/cross_module_type_refs/py/alpha/piketype/bar_types.py:5-16` has the requested import layout and unqualified `byte_ct` annotations. This supports the golden claim.
- FR-12 / AC-6: default C++ output is present: `tests/goldens/gen/cross_module_type_refs/cpp/alpha/piketype/bar_types.hpp:12` includes `foo_types.hpp`, and lines 20-21 use `::alpha::foo::byte_ct`. The `--namespace=proj::lib` half of AC-6 is not covered by a test or golden.
- AC-24: FAIL. The report claims the golden is byte-identical to the spec Overview's expected snippet, but the spec snippet uses `return {a.field1, a.field2};` and direct slice assignment at `specs/011-cross-module-type-refs/spec.md:93-105`. The golden instead emits `pack_byte(...)` and `unpack_byte(...)` at `tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/bar_pkg.sv:17,25,27`.

## PASS (partial) and PASS (code, not test) verification

- FR-8: The partial label is factually right but the PASS count is too generous. Only `tests/test_validate_engine.py:166-185` covers local-vs-imported type-name collision. The implementation contains branches for imported-vs-imported type names and enum literals at `src/piketype/validate/engine.py:407-460`, but the spec requires four FR-8 unit cases at `specs/011-cross-module-type-refs/spec.md:357-358`; three are missing.
- FR-16: The report is materially incomplete. The spec requires the primary fixture to define `byte_t`, `addr_t`, `cmd_t`, and `perms_t`, and for `bar_t` to use all four at `specs/011-cross-module-type-refs/spec.md:349-352`. The actual fixture only defines `byte_t` in `tests/fixtures/cross_module_type_refs/project/alpha/piketype/foo.py:1-3` and only imports/uses `byte_t` in `tests/fixtures/cross_module_type_refs/project/alpha/piketype/bar.py:1-9`.
- NFR-5 / AC-22: Not a valid PASS (partial). `UV_CACHE_DIR=/tmp/uv-cache uv run basedpyright src/piketype` currently exits 1 with 100 source errors, including new-feature files such as `src/piketype/backends/sv/view.py:370`, `src/piketype/backends/py/emitter.py:49`, and `src/piketype/validate/engine.py:155`. Running the plan's broader `basedpyright src/piketype tests/` reports 368 errors. The spec requires zero errors at `specs/011-cross-module-type-refs/spec.md:371` and `specs/011-cross-module-type-refs/spec.md:398`.
- AC-6: Genuinely partial. Default namespace output is verified by the golden, and `_module_ref_namespace` supports user namespaces at `src/piketype/backends/cpp/view.py:245-254`, but there is no `--namespace=proj::lib` integration test or golden despite AC-6 requiring it.
- AC-8: Partial at best. The report says only scalar is tested, but there is also an enum acceptance test at `tests/test_struct_enum_member.py:329-390`. Struct and flags cross-module acceptance are still untested.
- AC-13: Code exists at `src/piketype/validate/engine.py:407-426`, but no test exercises imported-vs-imported type-name collision. The code path is reachable through `validate_repo`, so it is not dead code, but calling the AC fully PASS is unsupported.
- AC-14: Code exists at `src/piketype/validate/engine.py:428-460`, but no test exercises imported-vs-imported enum literal collision or local-vs-imported enum literal collision. Calling the AC fully PASS is unsupported.

## DEFERRED legitimacy

- NFR-4: Invalid DEFERRED. Performance is an explicit NFR at `specs/011-cross-module-type-refs/spec.md:370` and is not in the Out of Scope list at `specs/011-cross-module-type-refs/spec.md:420-428`. Missing `tests/perf_baseline.json` is not an out-of-scope dependency under the stated policy. This should be FAIL until measured or the spec is changed.
- FR-3 + AC-18: Invalid DEFERRED. FR-3 is core functionality and explicitly says a fixture must exercise cross-module `multiple_of()` width contribution at `specs/011-cross-module-type-refs/spec.md:172-176`; AC-18 requires golden comparison at `specs/011-cross-module-type-refs/spec.md:394`. No `tests/fixtures/cross_module_struct_multiple_of/` or matching golden exists. This should be FAIL.
- AC-19: Invalid DEFERRED. The Python runtime byte-value test is explicitly required at `specs/011-cross-module-type-refs/spec.md:395` and the runtime test is listed under FR-16 at line 362. The report itself admits golden comparison can pass with a lockstep semantic bug. This is in-scope regression risk, not a legitimate deferral.

## Missing coverage

Every FR-1..FR-16, NFR-1..NFR-7, and AC-1..AC-24 appears in the validation report table. There are no silently omitted identifiers.

Coverage is still missing or overstated for FR-16 primary fixture contents, FR-8's three untested collision sub-cases, AC-6 `--namespace`, AC-8 struct/flags target kinds, AC-10 exact node-list/deterministic-rotation checks, AC-13, AC-14, AC-18, AC-19, AC-22, and AC-24.

## Test validity

- `tests/test_gen_cross_module.py::test_generates_expected_outputs` is a real byte-for-byte tree comparison (`tests/test_gen_cross_module.py:50-59`). It is valid for the files in the current small fixture, but the fixture does not satisfy FR-16.
- `tests/test_gen_cross_module.py::test_bar_pkg_uses_cross_module_byte_t` is a real content assertion (`tests/test_gen_cross_module.py:74-88`). It validates AC-2/AC-3 for scalar refs only.
- `tests/test_validate_engine.py::test_two_node_cross_module_cycle` is weak. It constructs a real two-node cycle, but it only asserts the generic phrase at `tests/test_validate_engine.py:158-160`; it does not verify that every node is named or that lexicographic rotation is deterministic as AC-10 requires.
- `tests/test_no_inline_imports.py` is a substantive AST check with negative and positive cases (`tests/test_no_inline_imports.py:171-254`) and live-source scanning. It is not trivially true.
- `tests/test_validate_engine.py::test_local_vs_imported_type_name` is a valid single-branch FR-8 test (`tests/test_validate_engine.py:166-185`), but it does not exercise the other three required collision rules.

## Self-check

The Summary count matches the table content: PASS=44, FAIL=0, DEFERRED=4, TOTAL=48. The count is internally consistent but misleading because several PASS entries should be downgraded and the DEFERRED items violate the policy.

## Issues

### BLOCKING

- `specs/011-cross-module-type-refs/artifacts/validation/iter1-test-output.txt` is zero bytes. Therefore the report's claims that specific tests exist in the suite output and passed are unsupported by the required artifact.
- NFR-4 is marked DEFERRED even though it is an explicit in-scope NFR and not listed in Out of Scope. It must be FAIL or actually measured.
- FR-3 + AC-18 are marked DEFERRED even though cross-module `multiple_of()` is core FR functionality and the spec requires a fixture/golden.
- AC-19 is marked DEFERRED even though the runtime byte-value test is explicitly required and the report admits golden lockstep can hide the bug.
- FR-16 is marked PASS (partial), but the primary fixture is missing the required struct, enum, and flags cross-module references.
- NFR-5 / AC-22 are marked PASS (partial), but `basedpyright` fails in the current checkout.
- AC-24 is marked PASS, but the committed `bar_pkg.sv` does not match the spec Overview expected snippet exactly.

### WARNING

- AC-6 lacks the required `--namespace=proj::lib` generated-output test/golden.
- AC-8 lacks struct and flags target-kind acceptance tests.
- AC-10 lacks exact cycle-node and deterministic-rotation assertions.
- AC-13 and AC-14 are code-only, with no direct tests despite FR-16 requiring the collision cases.
- Several line citations are stale or imprecise, e.g. `src/piketype/commands/gen.py:32-34` does not contain the unconditional basename check; the check is at lines 38-40.

### NOTE

- I independently verified the current test suite can pass with `UV_CACHE_DIR=/tmp/uv-cache uv run python -m unittest discover tests/` (285 tests, 1 skipped). The Forge still needs to populate the required validation artifact.
- `git diff develop -- tests/goldens/` shows only additions under `tests/goldens/gen/cross_module_type_refs/`, supporting the NFR-1 existing-golden claim.
- `git diff develop -- pyproject.toml` shows no dependency changes, supporting NFR-3.

VERDICT: REVISE
