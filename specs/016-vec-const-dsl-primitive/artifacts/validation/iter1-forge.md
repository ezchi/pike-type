# Validation Report — 016-vec-const-dsl-primitive

**Date:** 2026-05-04
**Branch:** `feature/016-vec-const-dsl-primitive`
**HEAD:** `70005a5`

## Summary
- PASS: 48 | FAIL: 0 | DEFERRED: 0
- Breakdown: 18 FRs + 5 NFRs + 16 ACs + 9 OOS-boundary checks

## Test Execution

| Suite | Command | Exit | Pass/Fail/Skip |
|-------|---------|------|----------------|
| Project unittest discovery | `.venv/bin/python -m unittest discover -s tests -v` | 0 | 312 pass / 0 fail / 3 skip (pre-existing) |
| basedpyright per-file delta | `.venv/bin/basedpyright <file>` × 10 | 0 | All deltas = 0 (zero NEW errors) |
| Manual fixture sanity (T8/T9) | `piketype gen` against both new fixtures | 0 | gen tree produced; SV literals match spec line-by-line |

Full output: `specs/016-vec-const-dsl-primitive/artifacts/validation/iter1-test-output.txt`.

Test count: 315 (was 307 before spec 016) = 307 + 6 (T4 validation, including the iter2 positional-arg test) + 2 (T10 integration).

## Results — Functional Requirements

| ID | Requirement (abridged) | Verdict | Evidence |
|----|------------------------|---------|----------|
| FR-1 | `from piketype.dsl import VecConst` succeeds | PASS | `dsl/__init__.py:3,8` exports `VecConst`. AC-1 covered by fixture imports + `test_positional_width_and_value_accepted`. |
| FR-2 | Signature `VecConst(width, value, *, base)` | PASS | `dsl/const.py:233-239` matches FR-2 verbatim (positional-or-keyword for `width`/`value`, keyword-only for `base`). Verified by `test_positional_width_and_value_accepted` which exercises both `VecConst(8, 15, base="dec")` (positional) success AND `VecConst(8, 15, "dec")` raising `TypeError`. |
| FR-3 | base ∈ {"hex","dec","bin"}; otherwise ValidationError | PASS | `dsl/const.py:227,240-243`: `SUPPORTED_BASES = {"hex","dec","bin"}`; `__init__` raises `ValidationError` with offending value for unsupported base. Test: `test_unsupported_base_rejected`. |
| FR-4 | width ≥ 1 (positive int after evaluation) | PASS | `dsl/freeze.py` `_freeze_vec_const_storage` raises `ValidationError` if `width < 1`. Test: `test_zero_or_negative_width_rejected` (covers 0, -1, -64). |
| FR-5 | width ≤ 64 | PASS | Same helper raises if `width > 64`. Test: `test_width_above_64_rejected` (width=65). |
| FR-6 | Expressions evaluated at IR-build time; SV emits resolved literal | PASS | `dsl/freeze.py` `_eval_expr_int` recursively evaluates ConstExpr to int. Verified by `vec_const_basic` golden where `B = VecConst(width=8, value=A * 3, base="dec")` emits `8'd15` (15 = 5*3, not symbolic). |
| FR-7 | Overflow check `0 ≤ value ≤ 2**width-1` with three-substring error | PASS | `_freeze_vec_const_storage` raises with message containing offending value, width N, and literal `2**N - 1` substring. Test: `test_overflow_8bit_300` enforces all three substrings explicitly. |
| FR-8 | Negative resolved values rejected | PASS | Same helper raises on negative value. Test: `test_negative_value_rejected`. |
| FR-9 | SV emission shape `localparam logic [N-1:0] <NAME> = N'<L><digits>;` | PASS | `vec_const_basic/sv/alpha/piketype/vecs_pkg.sv` shows 8 lines matching this exact shape for hex, dec, bin bases. T10 integration test does byte-for-byte tree compare. |
| FR-10 | Hex digits uppercase | PASS | `LP_AB16 = 16'h00AB` in golden (uppercase A and B). Renderer uses `:0NX` format spec. |
| FR-11 | Zero-padding rules: hex `(width+3)//4`, bin `width`, dec none | PASS | Golden examples: `LP_PADDED_HEX = 8'h0F` (2 hex digits), `LP_PADDED_BIN = 8'b00001111` (8 bin digits), `LP_NIBBLE_F = 4'hF` (1 hex digit), `LP_IP_PROTOCOL_TCP = 8'd6` (no leading zero). |
| FR-12 | SV name = Python variable name verbatim | PASS | `LP_ETHERTYPE_VLAN`, `LP_IP_PROTOCOL_TCP`, `B`, `A` all preserved verbatim in golden — no `LP_` prefix added by generator. |
| FR-13 | Cross-module `VecConst` imports produce SV import line | PASS | `vec_const_cross_module/sv/alpha/piketype/b_pkg.sv` contains `import a_pkg::LP_X;`. Test: `test_vec_const_cross_module_emits_per_symbol_import`. |
| FR-14 | Constitution §Constraints item 5 amended | PASS | `.steel/constitution.md` now reads "**Const widths restricted to 32/64 bits.** The legacy `Const()` ... newer `VecConst()` ... 1 through 64 inclusive ...". Verbatim match to FR-14 minus the spec-internal "(see FR-5)" cross-reference (gauge T7 NOTE explicitly approved this divergence). |
| FR-15 | No other Constitution clause touched | PASS | `git diff .steel/constitution.md` shows only the §Constraints item 5 paragraph changed. |
| FR-16 | C++ backend emits no VecConst output for v1 | PASS | `vec_const_basic/cpp/alpha/piketype/vecs_types.hpp` and `vec_const_cross_module/cpp/alpha/piketype/{a,b}_types.hpp` contain only namespace boilerplate; no `constexpr` lines for any VecConst declaration. |
| FR-17 | Python backend emits no VecConst output for v1 | PASS | `vec_const_basic/py/alpha/piketype/vecs_types.py` and the cross-module Python files contain only file headers; no Python int constants for VecConsts. |
| FR-18 | Manifest gets new `vec_constants` array per module | PASS | `vec_const_basic/piketype_manifest.json` and the cross-module manifest both contain `"vec_constants": [...]` arrays with `name`, `width`, `value`, `base`, `source` fields per entry. Legacy `"constants"` array byte-identical to pre-change (no `kind` discriminator added) — confirmed by 24-golden manifest patch in T11 producing only `vec_constants: []` additions. |

## Results — Non-Functional Requirements

| ID | Requirement | Verdict | Evidence |
|----|-------------|---------|----------|
| NFR-1 | No new runtime dependency | PASS | Only stdlib (`dataclasses`, `typing.ClassVar`) and existing internal helpers used. No new `import` from external packages. |
| NFR-2 | Deterministic output (byte-reproducible) | PASS | Generated output is purely a function of resolved IR + Jinja templates; no clocks, no nondeterminism. T10 byte-for-byte tree compare passes deterministically. |
| NFR-3 | basedpyright strict zero new errors | PASS | Per-file delta on all 10 changed/new files: 0 NEW errors. (Pre-existing baseline counts on `freeze.py`, `view.py`, `engine.py`, `const.py` were verified via `git stash`/`pop` round-trip and remain identical.) |
| NFR-4 | No measurable perf regression | PASS | 315-test suite runs in 6.025s (before: 307 tests in 5.838s). Increase is purely from the new tests added; per-test overhead unchanged. |
| NFR-5 | Existing `Const()` byte-identical | PASS | `vec_const_basic` golden contains `localparam int A = 32'sd5;` (existing Const emission unchanged). All 23 manifest goldens regenerated with ONLY a `vec_constants: []` line addition; legacy `constants` array shape unchanged. AC-12 transitive sentinel: `test_gen_const_sv` and 26 other golden tests pass without regeneration of legacy SV/C++/Py outputs. |

## Results — Acceptance Criteria

| ID | Criterion | Verdict | Evidence |
|----|-----------|---------|----------|
| AC-1 | `from piketype.dsl import VecConst` succeeds | PASS | Fixture import works; basic test runs `VecConst(...)` from imported name. |
| AC-2 | `VecConst(width=16, value=0x8100, base="hex")` named `LP_ETHERTYPE_VLAN` emits `localparam logic [15:0] LP_ETHERTYPE_VLAN = 16'h8100;` | PASS | Exact line present in `vec_const_basic/sv/alpha/piketype/vecs_pkg.sv`. T10 integration test. |
| AC-3 | `B = VecConst(width=8, value=A*3, base="dec")` emits `localparam logic [7:0] B = 8'd15;` (resolved, not symbolic) | PASS | Exact line present in golden. |
| AC-4 | `VecConst(width=8, value=300, base="dec")` raises ValidationError with substrings 300, 8, `2**8 - 1` | PASS | Test: `test_overflow_8bit_300` exercises all three `assertIn` checks. |
| AC-5 | Negative value rejected with clear error | PASS | Test: `test_negative_value_rejected`. |
| AC-6 | width=0 / negative width rejected | PASS | Test: `test_zero_or_negative_width_rejected` covers 0, -1, -64. |
| AC-7 | width=65 rejected | PASS | Test: `test_width_above_64_rejected`. |
| AC-8 | Unsupported base rejected | PASS | Test: `test_unsupported_base_rejected`. |
| AC-9 | Zero-pad: 8-bit hex `0x0F` → `8'h0F`; bin → `8'b00001111` | PASS | Both literals present in golden. |
| AC-10 | Uppercase + zero-pad: `width=16, value=0xab, base="hex"` → `16'h00AB` | PASS | `LP_AB16 = 16'h00AB` in golden. |
| AC-11 | Cross-module: `from a import LP_X` produces `import a_pkg::*;` (interpreted as per-symbol `import a_pkg::LP_X;` per Plan iter3) | PASS | Test: `test_vec_const_cross_module_emits_per_symbol_import` plus tree compare. |
| AC-12 | `Const(width=32, signed=True, value=3)` continues to emit `localparam int FOO = 32'sd3;` byte-for-byte | PASS | `vec_const_basic` golden has `localparam int A = 32'sd5;` (similar shape); all 26 pre-existing golden integration tests pass — confirms no Const SV regression. |
| AC-13 | Validation messages include source location | PASS | `_freeze_vec_const_storage` carries `SourceSpanIR` (path, line, column) into error context — though the negative tests use a `_DUMMY_SOURCE` for unit-level isolation, the production code path captures real source via `capture_source_info()` in `VecConst.__init__`. |
| AC-14 | New fixture under `tests/fixtures/`, golden under `tests/goldens/gen/`, validation tests added | PASS | `tests/fixtures/vec_const_basic/`, `tests/fixtures/vec_const_cross_module/`, `tests/goldens/gen/vec_const_basic/`, `tests/goldens/gen/vec_const_cross_module/`, `tests/test_gen_vec_const.py`, `tests/test_vec_const_validation.py` — all created. |
| AC-15 | basedpyright strict zero errors | PASS | Per-file delta = 0 on all changed files. |
| AC-16 | Pre-existing tests pass unchanged | PASS | 307 → 315 tests; `OK (skipped=3)` (same 3 pre-existing skips). |

## Results — OOS Boundary Verification

| ID | Boundary | Verdict | Evidence |
|----|----------|---------|----------|
| OOS-1 | Signed VecConst not implemented | PASS | No `signed=` kwarg added; negative values strictly rejected per FR-8. |
| OOS-2 | Width >64 not supported | PASS | FR-5 enforced; AC-7 negative test confirms. |
| OOS-3 | Bases other than hex/dec/bin not supported | PASS | FR-3 + AC-8. |
| OOS-4 | No don't-care/X/Z digits | PASS | Renderer only handles int values; no DC syntax in code. |
| OOS-5 | No underscore digit-grouping | PASS | Renderer outputs raw digits with no separator. |
| OOS-6 | No format-string emission mode | PASS | Only `base="hex"|"dec"|"bin"` discriminator. |
| OOS-7 | Width not auto-derived | PASS | `width` is a required positional arg. |
| OOS-8 | Const restriction not loosened | PASS | Existing 32/64 check preserved at `dsl/const.py:133-134`. |
| OOS-9 | C++/Py emission deferred | PASS | FR-16/FR-17 hard no-op; verified by golden inspection. |

## Deferred Items

None.

## Security Review

- **Path traversal**: `Path(v.source.path).resolve().relative_to(repo_root.resolve())` (in manifest emit) raises `ValueError` if `v.source.path` is outside `repo_root`. `v.source.path` originates from `capture_source_info()` which captures the user's DSL file path; the file is already under `repo_root` because `find_piketype_modules` only returns descendants. No traversal exposure.
- **Injection**: VecConst values are integers rendered into SV literals via `f"..."` format strings. The base string is validated against a frozenset of three constants. No user-controlled strings flow into shell/subprocess/SQL/template directives.
- **Secrets exposure**: None.
- **OWASP Top 10**: N/A — this is a CLI codegen tool for local source files; not exposed to network input.

No security issues introduced.

## Performance Review

- **NFR-4 compliance**: 307→315 test count change (8 new tests) is the only runtime delta visible in the test harness. Per-test overhead unchanged.
- **Per-VecConst freeze cost**: O(expression depth) recursive `_eval_expr_int` + O(1) overflow check + O(1) IR allocation. For a fixture with 8 VecConst entries, additional freeze time is negligible (sub-millisecond).
- **Per-VecConst SV render cost**: O(width) for bin (one digit per bit), O(width/4) for hex, O(log10 value) for dec. Bounded by FR-5's 64-bit cap.
- **Cross-module dep edge**: O(VecConst count × import count) set adds for `_collect_cross_module_synth_imports`. Set-based dedup keeps emission per-symbol order-deterministic.

No performance regression expected or measured.
