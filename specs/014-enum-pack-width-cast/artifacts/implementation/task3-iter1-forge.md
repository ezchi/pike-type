# Task 3: Run pre-commit verification gates — Forge Iteration 1

## Files Changed
- None. Task 3 is verification-only; it produces no file changes
  (other than this artifact).

## Key Implementation Decisions
- **Compared against `develop`, not `master`.** The plan's Phase 3
  Gates 5 and 6 say `git diff --stat master ...`. This is wrong for
  this branch: the feature branched from `develop` (per
  `.steel/config.json:git.baseBranch`), and `master` is several specs
  behind. Comparing against `master` includes all of specs 011-013's
  diffs, which is noise. The correct base for diff-scope gates is
  `develop`. The plan should be amended in retrospect.
- **Treated basedpyright as a regression guard, not an absolute gate**
  per NFR-3 wording ("continues to pass... effectively a regression
  guard, not a new gate"). The current `develop` baseline has 100
  pre-existing basedpyright errors (verified by checking out
  `develop` `src/piketype/` and running basedpyright). My change does
  not touch Python at all, so the error count is unchanged: no
  regression introduced.

## Deviations from Plan
- **Gate 5 / Gate 6 base ref:** the plan said `master`; I used
  `develop` because the feature branch is rooted in develop. Plan
  amendment recommended.
- **Gate 2 (basedpyright):** ran the gate, but did not treat the
  pre-existing 100 errors as blocking this feature, because (a) NFR-3
  explicitly frames this gate as a regression guard, and (b) the
  errors exist before my one-line template edit which adds no
  Python. Pre-existing baseline issues are out of scope for this
  feature.

## Verification Gate Results

### Gate 1 — Full unittest suite
```
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
```
Result: `Ran 303 tests in 5.826s` / `OK (skipped=3)`. **PASS.**

### Gate 2 — basedpyright strict
```
.venv/bin/python -m basedpyright src/piketype/
```
Result: `100 errors, 0 warnings, 0 notes`. Same count on
`develop` baseline (verified). **PASS** (no regression introduced).
Pre-existing baseline drift documented for retrospect.

### Gate 3 — Bug-line absence
```
grep -r "return logic'(a);" tests/goldens/gen/ | wc -l
```
Result: `0`. Expected: `0`. **PASS.** (Spec AC-1.)

### Gate 4 — Fix-line presence count
```
grep -r "return LP_[A-Z_]*_WIDTH'(a);" tests/goldens/gen/ | wc -l
```
Result: `8`. Expected: `8`. Distribution:
```
tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/foo_pkg.sv:46:    return LP_CMD_WIDTH'(a);
tests/goldens/gen/cross_module_type_refs_namespace_proj/sv/alpha/piketype/foo_pkg.sv:46:    return LP_CMD_WIDTH'(a);
tests/goldens/gen/keyword_enum_value_while_passes/sv/alpha/piketype/types_pkg.sv:13:    return LP_STATE_WIDTH'(a);
tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_pkg.sv:13:    return LP_CMD_WIDTH'(a);
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv:13:    return LP_COLOR_WIDTH'(a);
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv:26:    return LP_CMD_WIDTH'(a);
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv:39:    return LP_FLAG_WIDTH'(a);
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv:52:    return LP_BIG_WIDTH'(a);
```
**PASS.** (Spec AC-2 — every match accounted for; total = 8.)

### Gate 5 — Python diff scope (vs `develop`)
```
git diff --stat develop -- src/piketype/
```
Result:
```
 src/piketype/backends/sv/templates/_macros.j2 | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```
**PASS.** Exactly one file, exactly the template. (Spec AC-5.)

### Gate 6 — Golden diff scope (vs `develop`)
```
git diff --stat develop -- tests/goldens/gen/
```
Result:
```
 .../cross_module_type_refs/.../foo_pkg.sv                | 2 +-
 .../cross_module_type_refs_namespace_proj/.../foo_pkg.sv | 2 +-
 tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv | 8 ++++----
 .../keyword_enum_value_while_passes/.../types_pkg.sv     | 2 +-
 .../struct_enum_member/.../types_pkg.sv                  | 2 +-
 5 files changed, 8 insertions(+), 8 deletions(-)
```
**PASS.** Exactly the 5 enumerated files, total of 8 line changes.
(Spec AC-6, AC-7.)

### Gate 6b — `_test_pkg.sv` diff scope (vs `develop`)
```
git diff --stat develop -- 'tests/goldens/gen/**/*_test_pkg.sv'
```
Result: empty. **PASS.** (Spec AC-6.)

### Gate 7 — Idempotency / byte parity
Picked `cross_module_type_refs_namespace_proj` (exercises `--namespace`
flag path). Re-ran the regen against a fresh temp directory, then
`diff -r` against the committed golden subtree:
```
diff -r tests/goldens/gen/cross_module_type_refs_namespace_proj/sv \
        /tmp/pike-014-idem/cross_module_type_refs_namespace_proj/gen/sv
```
Result: empty. **PASS.** Byte-parity holds at HEAD.

### Gate 8 — Verilator lint (optional)
Skipped per plan ("optional but recommended"). The committed unittest
suite includes the project's standard golden-comparison tests; their
passing in Gate 1 covers AC-9 in the same way it covers it for prior
specs.

## Summary

All required gates (1, 3, 4, 5, 6, 6b, 7) pass. Gate 2 reports a
pre-existing baseline failure that is not a regression introduced by
this feature; treated as PASS per NFR-3's regression-guard framing.
Gate 8 is optional; skipped.

**Implementation is committable.** The single forge commit produced in
iteration 1 (`forge(implementation): tasks 1-2 iteration 1 output
[iteration 1]`) holds byte parity, scopes correctly, and passes the
test suite.
