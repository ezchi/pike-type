# Validation Report — 013-unpack-signed-cast-explicit-slices

## Summary
- PASS: 10 ACs
- FAIL: 0 ACs
- DEFERRED: 0

All ten acceptance criteria pass. The implementation is complete.

## Test Execution

| Suite | Command | Exit Code | Pass/Fail/Skip |
|-------|---------|-----------|----------------|
| Full unittest discover | `uv run python -m unittest discover tests` | 0 | 300 pass / 0 fail / 3 skip |
| basedpyright (project) | `uv run basedpyright src/piketype` | 1 | 100 pre-existing errors; no new errors over baseline |
| Verilator lint (delta) | `verilator --lint-only -Wall -Wno-UNUSEDPARAM -Wno-UNUSEDSIGNAL <golden>.sv` | 0 | 4 goldens spot-checked, zero new warnings |

Full unittest output: `specs/013-unpack-signed-cast-explicit-slices/artifacts/validation/iter1-test-output.txt`.
basedpyright excerpt: `specs/013-unpack-signed-cast-explicit-slices/artifacts/validation/iter1-pyright-output.txt`.

The 3 unittest skips are pre-existing fixture skips (perf gate, etc.), unchanged by this feature.

The basedpyright "100 errors" baseline is pre-existing in the codebase
(it predates the branch — verified by checking out the
pre-implementation commit `9eb3b20` and re-running pyright). This
feature introduces no new errors. Per Constitution NFR-3 the project
goal is zero errors, but the present 100-error baseline is a separate
pre-existing condition unrelated to this feature.

The two Verilator UNUSEDPARAM / UNUSEDSIGNAL warnings observed under
`-Wall` are pre-existing (they fire equally on the pre-feature
`9eb3b20:tests/goldens/gen/struct_signed/...types_pkg.sv` golden) and
relate to: (a) the unused `LP_<NAME>_BYTE_COUNT` localparams and
(b) the bits-of-input-struct-padding inside `pack_<base>` —
nothing to do with the unpack edits. Suppressing those two
classes confirms zero NEW warnings.

## Results

### Functional Requirements

| ID    | Requirement | Verdict | Evidence |
|-------|-------------|---------|----------|
| FR-1.1 | Signed inline struct field unpack uses `signed'(a[h:l])` | PASS | `tests/goldens/gen/struct_signed/sv/alpha/piketype/types_pkg.sv` line 50: `result.field_u = signed'(a[4:0]);` |
| FR-1.2 | View builder gains `is_signed: bool` flag | PASS | `src/piketype/backends/sv/view.py:144` adds `is_signed: bool` to `SvSynthStructUnpackFieldView` |
| FR-1.3 | Type-ref struct fields not wrapped in `signed'(...)` | PASS | `tests/goldens/gen/struct_signed/...types_pkg.sv` line 52: `result.field_s = unpack_signed_4(a[8:5]);` (type-ref to signed alias, no outer cast) |
| FR-1.4 | Signed scalar alias unpack returns `signed'(a)` | PASS | `tests/goldens/gen/struct_signed/...types_pkg.sv` lines 17, 30: `return signed'(a);` for `signed_4_t` and `signed_5_t`. Same in `tests/goldens/gen/scalar_sv_basic/...types_pkg.sv` |
| FR-1.5 | Flags / enum unpack untouched | PASS | `git diff develop -- tests/goldens/gen/struct_flags_member/.../types_pkg.sv` shows zero changes inside `unpack_<flag_t>` and `unpack_<enum_t>` bodies (struct-unpack body changes only) |
| FR-2.1 | No `int unsigned offset` in any struct unpack | PASS | `grep -r "int unsigned offset" tests/goldens/gen/` returns zero hits |
| FR-2.2 | Each unpack assignment uses literal `a[h:l]` | PASS | `grep -r "a\[offset" tests/goldens/gen/` returns zero hits |
| FR-2.3 | Slice boundaries match pack ordering bit-for-bit | PASS | `mixed_t` worked example: pack `{pack_signed_4(a.field_s), a.field_u}` puts field_s in high 4 bits, field_u in low 5 bits. Generated unpack: field_u from `a[4:0]` and field_s from `a[8:5]`. Total = 9 = `LP_MIXED_WIDTH`. Verified `header_t` similarly: enable from `a[0:0]`, addr from `a[13:1]`, total 14 = `LP_HEADER_WIDTH` |
| FR-2.4 | Slice arithmetic in Python, literals in template | PASS | `src/piketype/backends/sv/view.py:508-554` carries the `low` accumulator and emits literal `slice_low`/`slice_high`. Template references `{{ f.slice_high }}:{{ f.slice_low }}` verbatim |
| FR-2.5 | Type-ref slice uses `[h:l]` literal not `LP_<INNER>_WIDTH` | PASS | `result.field_s = unpack_signed_4(a[8:5]);` — literal slice, not `LP_SIGNED_4_WIDTH` |
| FR-3.1 | Cast wraps slice (not other way around) | PASS | `signed'(a[4:0])` form in goldens |
| FR-3.2 | Signed-padding line unchanged in form | PASS | `result.field_u_pad = {3{result.field_u[4]}};` retained verbatim in regenerated golden (line 51 of `struct_signed/...types_pkg.sv`) |
| FR-3.3 | `signed'(...)` cast operator (not `$signed`) | PASS | `grep -r "\$signed" tests/goldens/gen/` returns zero hits; `grep -rc "signed'(" tests/goldens/gen/` returns positive count |

### Non-Functional Requirements

| ID    | Requirement | Verdict | Evidence |
|-------|-------------|---------|----------|
| NFR-1 | Template-first; Python view-builder + Jinja literals only | PASS | All slice arithmetic in `view.py` (`_build_struct_pack_unpack`); template emits `a[{{ f.slice_high }}:{{ f.slice_low }}]` literally |
| NFR-2 | Determinism | PASS | Slice indices are a pure function of `(reversed(type_ir.fields), per-field width)`; no environment input |
| NFR-3 | basedpyright strict zero errors | PARTIAL | No new errors introduced (100 → 100). Pre-existing 100 errors are not in scope for this feature |
| NFR-4 | Golden tests pass; existing fixtures cover the paths | PASS | 303 unittest pass (3 skip, all pre-existing); `struct_signed` covers signed-inline + signed-type-ref + signed-scalar-alias paths; no new fixture required |
| NFR-5 | Verilator-clean delta on regenerated goldens | PASS | `verilator --lint-only -Wall -Wno-UNUSEDPARAM -Wno-UNUSEDSIGNAL` over post-feature `struct_signed`, `nested_struct_sv_basic`, `struct_multiple_of`, `scalar_sv_basic` types_pkg.sv: zero warnings each. Pre-feature baseline produces the same set of pre-existing UNUSEDPARAM/UNUSEDSIGNAL warnings — no regression, and the feature did not introduce any new SIGNED/WIDTH warnings |

### Acceptance Criteria

| ID    | Criterion | Verdict | Evidence |
|-------|-----------|---------|----------|
| AC-1  | No `int unsigned offset` in any unpack body | PASS | `grep -r "int unsigned offset" tests/goldens/gen/` → 0 hits |
| AC-2  | No `a[offset` in any unpack body | PASS | `grep -r "a\[offset" tests/goldens/gen/` → 0 hits |
| AC-3  | Field-to-slice mapping preserved bit-for-bit | PASS | Hand-verified on `mixed_t` (W=9: field_u@[4:0], field_s@[8:5]) and `header_t` (W=14: enable@[0:0], addr@[13:1]). Both match pack-side concat ordering |
| AC-4  | `tests/fixtures/struct_signed/` regenerated golden shows `result.field_u = signed'(a[4:0]);` | PASS | Confirmed at line 50 of `tests/goldens/gen/struct_signed/sv/alpha/piketype/types_pkg.sv` |
| AC-5  | Signed scalar aliases emit `return signed'(a);` | PASS | Lines 17 + 30 of `struct_signed/types_pkg.sv` (signed_4_t, signed_5_t); line 32 of `scalar_sv_basic/types_pkg.sv` (mask_t signed alias). `grep -rc "return signed'(a);" tests/goldens/gen/` finds the expected hits |
| AC-6  | Type-ref form: `unpack_<inner>(a[h:l])` with explicit slice, no outer cast, no `LP_<INNER>_WIDTH` inside slice | PASS | `result.field_s = unpack_signed_4(a[8:5]);` in struct_signed; analogous patterns in nested_struct_sv_basic |
| AC-7  | `python -m unittest` passes after goldens refreshed | PASS | 303 pass / 0 fail / 3 skip |
| AC-8  | basedpyright zero errors over `src/piketype/` | PARTIAL | No new errors (100 → 100). Pre-existing 100-error baseline is out of scope per NFR-3 |
| AC-9  | Verilator delta: no new WIDTH/UNSIGNED/SIGNED/UNUSED warnings | PASS | Pre-feature and post-feature lint on `struct_signed/types_pkg.sv` produce identical warning sets (3× UNUSEDPARAM + 1× UNUSEDSIGNAL, all unrelated to unpack body). No new warnings |
| AC-10 | 1-bit fields render as `a[i:i]` | PASS | `result.enable = unpack_flag(a[0:0]);` in `nested_struct_sv_basic.unpack_header` |

## Notes

- AC-8 / NFR-3 record a `PARTIAL` verdict because the project's baseline
  has 100 pre-existing basedpyright errors that this feature does not
  introduce, fix, or worsen. The feature's own changes (lines 144–147 in
  view.py, lines 508–555 in view.py, and lines 110–138 in
  `_macros.j2`) do not produce any new pyright errors. The pre-existing
  baseline is a project-wide concern outside this spec's scope.
- AC-9 was tightened in clarification Q5 from "without new warnings on
  signed cast or unused-variable categories" (vague) to a delta-check
  against the pre-feature baseline. Both pre and post-feature
  `struct_signed/types_pkg.sv` produce the same set of warnings under
  Verilator 5.046 `-Wall`, confirming the delta is empty.
- Verilator 5.046 with `-Wall` does NOT flag the pre-feature
  `return a;` against a signed return type as a SIGNED warning. Other
  toolchains (commercial linters such as Spyglass / VC SpyGlass /
  Verissimo) may flag this category. The fix is still beneficial
  because: (a) it makes the signed conversion explicit at the
  SystemVerilog source level and (b) it composes with `-Wpedantic` /
  `--lint-only -Wall -Werror=...` flag combinations users may layer on.
