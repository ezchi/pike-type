# Gauge Verification Prompt — Validation, Iteration 1

You are the **Gauge** in the validation loop. Your job is to **independently verify** the Forge's claims, not rubber-stamp.

## Inputs

- **Validation report:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/validation.md`
- **Specification:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/spec.md`
- **Plan:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/plan.md`
- **Verbatim test output:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/artifacts/validation/iter1-test-output.txt`
- **Constitution:** `/Users/ezchi/Projects/pike-type/.steel/constitution.md`
- **Modified source files** (for spot-checks):
  - `src/piketype/ir/nodes.py` (new VecConstIR/VecConstImportIR + ModuleIR fields)
  - `src/piketype/dsl/const.py` (new VecConst class)
  - `src/piketype/dsl/freeze.py` (freeze logic)
  - `src/piketype/backends/sv/view.py` (SV emission)
  - `src/piketype/backends/sv/templates/module_synth.j2` (SV template)
  - `src/piketype/manifest/write_json.py` (manifest array)
  - `src/piketype/validate/engine.py` (vec-only-module fix)
  - `.steel/constitution.md` (§Constraints item 5)
- **New tests + fixtures + goldens:**
  - `tests/test_vec_const_validation.py`
  - `tests/test_gen_vec_const.py`
  - `tests/fixtures/vec_const_basic/`, `tests/fixtures/vec_const_cross_module/`
  - `tests/goldens/gen/vec_const_basic/`, `tests/goldens/gen/vec_const_cross_module/`

## Forge's Summary

**PASS: 48 | FAIL: 0 | DEFERRED: 0** — 18 FRs + 5 NFRs + 16 ACs + 9 OOS-boundary checks all PASS.

## Required Verification Checks

### 1. PASS-claim spot-checks (read the cited files/lines)

- **FR-2** (signature): open `dsl/const.py:233-239`. Confirm `def __init__(self, width, value, *, base):` — positional-or-keyword for width/value, keyword-only for base. Confirm `test_positional_width_and_value_accepted` exercises both `VecConst(8, 15, base="dec")` (positional success) AND `VecConst(8, 15, "dec")` (TypeError).
- **FR-3** (base validation): `dsl/const.py:227,240-243` — `SUPPORTED_BASES` and the `__init__` check.
- **FR-7** (three-substring contract): open `dsl/freeze.py` `_freeze_vec_const_storage` and confirm the error messages for overflow and negative-value contain ALL THREE: offending value, width N, and the literal substring `2**N - 1`.
- **AC-2** golden line: `tests/goldens/gen/vec_const_basic/sv/alpha/piketype/vecs_pkg.sv` line containing `LP_ETHERTYPE_VLAN = 16'h8100`.
- **AC-3** golden line: same file, line `B = 8'd15` (NOT a symbolic A*3).
- **AC-9, AC-10**: `LP_PADDED_HEX = 8'h0F`, `LP_PADDED_BIN = 8'b00001111`, `LP_AB16 = 16'h00AB` lines in golden.
- **AC-11**: `tests/goldens/gen/vec_const_cross_module/sv/alpha/piketype/b_pkg.sv` contains `import a_pkg::LP_X;`.
- **FR-16, FR-17**: open `tests/goldens/gen/vec_const_basic/cpp/alpha/piketype/vecs_types.hpp` and `vecs_types.py`. Confirm NO output lines for any VecConst (only namespace boilerplate / file headers).
- **FR-18**: open `tests/goldens/gen/vec_const_basic/piketype_manifest.json`. Confirm `"vec_constants"` array present per module with the 5 fields.

### 2. Test execution validity

- The test output file claims `Ran 315 tests in 6.025s` and `OK (skipped=3)`. Verify by reading `iter1-test-output.txt` final lines.
- Confirm the 8 new VecConst-specific tests (6 in `test_vec_const_validation` + 2 in `test_gen_vec_const`) ran and passed.

### 3. Constitution check

- Open `.steel/constitution.md`. Confirm §Constraints item 5 has been amended per FR-14 (legacy `Const()` 32/64; new `VecConst()` 1..64). Confirm no other Constitution clause was modified.

### 4. DEFERRED audit

- The Forge claims zero DEFERRED items. Confirm there are no requirements that should have been deferred (i.e., no in-scope items silently treated as PASS without evidence).

### 5. Self-check correctness

- The Forge's Summary says PASS: 48. Recount from the Results tables. The breakdown line claims 18 FRs + 5 NFRs + 16 ACs + 9 OOS = 48. Verify.

### 6. Adversarial reading

- Look for unfalsifiable language ("ensures", "appropriately") without evidence.
- Look for tests cited as PASS evidence but that don't actually exercise the requirement (e.g., a test that asserts a string contains a substring without verifying the substring is non-empty).
- Look for missing-coverage items: any FR/NFR/AC from the spec not addressed in the report.

## Output

### Issues
**BLOCKING / WARNING / NOTE**, with file:line cites where possible.

### Verdict

End with **EXACTLY** one of:

```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

Approve only if zero BLOCKING issues remain.

## Important

- Be adversarial — do not take the report's word for any spot-checkable claim.
- The user explicitly approved scope. Do NOT re-litigate clarification decisions (reject signed / verbatim naming / Option A manifest / width 64 / per-symbol cross-module imports).
- Per memory `feedback_minimal_change_preserve_scope.md`, do NOT push for scope expansion (e.g., adding C++/Py emission, lifting width cap).
- The Constitution is the highest authority.
