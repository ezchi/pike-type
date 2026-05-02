# Gauge Factual Verification — Validation Stage, Iteration 1

You are the **Gauge** in the Forge-Gauge validation loop. Your job is NOT
to rubber-stamp the validation report. You must independently verify
that the Forge's PASS/FAIL/DEFERRED claims are factually correct.

## Inputs

1. **Validation report under review**:
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/validation.md`

2. **Spec** (the contract):
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/spec.md`

3. **Plan**:
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/plan.md`

4. **Verbatim test output** (full unittest log):
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/artifacts/validation/iter1-test-output.txt`

5. **The actual code** — read these files yourself:
   - `/Users/ezchi/Projects/pike-type/src/piketype/backends/sv/templates/_macros.j2`
     (verify line 98 reads `    return LP_{{ view.upper_base }}_WIDTH'(a);`)
   - `/Users/ezchi/Projects/pike-type/tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv`
     (verify lines 13, 26, 39, 52 read `return LP_<UPPER>_WIDTH'(a);`)
   - The 4 other affected goldens listed in spec FR-3.1.

## Verification Tasks

### Task A — Verify PASS claims (must be adversarial)

For every PASS in the validation report, do the following:
1. Identify the specific evidence the Forge cites (a grep result, a
   test name, a line number).
2. Re-execute that grep / re-read that file / re-locate that test in
   the test output.
3. Confirm the evidence actually supports the claim. If not, flag the
   PASS as unsupported.

Examples to spot-check:

- **FR-1.1 PASS** cites `_macros.j2:98`. Read line 98 yourself; does
  it actually contain `return LP_{{ view.upper_base }}_WIDTH'(a);`?
- **AC-1 PASS** claims `grep -r "return logic'(a);" tests/goldens/gen/`
  returns 0. Verify by re-running the grep.
- **AC-2 PASS** claims exactly 8 matches of
  `return LP_[A-Z_]*_WIDTH'(a);` in goldens. Verify by re-running.
- **AC-3 PASS** cites `defs_pkg.sv:39`. Read that line; is it really
  `    return LP_FLAG_WIDTH'(a);`? Does the line above declare
  `LP_FLAG_WIDTH = 1`?
- **FR-3.1 PASS** cites `test_idempotent` and
  `test_enum_basic_idempotent`. Find these in the test output and
  confirm they passed.
- **NFR-6 PASS** cites "Ran 303 tests... OK (skipped=3)". Verify by
  reading the test output's last lines.

### Task B — Verify FAIL claims

The report lists 0 FAILs. Verify there are no requirements the Forge
silently let pass that should actually have failed.

### Task C — Verify DEFERRED legitimacy

The report defers NFR-5 and AC-10 (Verilator delta lint). Apply the
DEFERRED policy:

1. Is the dependency truly out-of-scope per the spec? — Yes. Spec
   "Out of Scope" section excludes "Lint-clean behaviour against tools
   other than Verilator" and the plan's Phase 3 Gate 8 explicitly
   marks the Verilator gate as "Optional but recommended".
   Clarification C-1 explicitly rejected adding an SV-execution
   harness.
2. Is the code path isolated? — Yes. The Verilator delta is a check
   on already-emitted text; the in-scope code (the template edit and
   the goldens) is independently validated by the unit tests.
3. Does the test plan describe how to validate later? — Yes (the
   report includes a concrete shell snippet).

If you disagree on any of these, downgrade the verdict to FAIL.

### Task D — Identify missing coverage

Scan spec.md for any FR/NFR/AC not represented in the validation
report's tables. Flag any gap.

### Task E — Test validity

Are the tests cited as evidence actually testing what they claim?
For example:

- `test_enum_basic` in `test_gen_enum.py` — does it actually byte-compare the
  regenerated golden to the committed golden? Read the test source to
  confirm; do not just trust the test name.
- `test_idempotent` in `test_gen_cross_module.py` — same check.

If a cited test is a no-op or trivially passing, flag it as invalid
evidence.

### Task F — Self-check arithmetic

The report's Final Summary says "25 PASS, 0 FAIL, 2 DEFERRED" after
self-correction from "24 PASS / 1 DEFERRED". Recount the verdicts in
the tables yourself and confirm the final count is correct.

## Output Format

```
# Gauge Verification — Validation Stage, Iteration 1

## Summary
(Top-line judgement.)

## Findings

### Disputed PASS claims
(For each: which item, what the Forge claimed, what you found,
specific file/line/test that contradicts.)

### Disputed FAIL claims
(If any.)

### Disputed DEFERRED items
(If any — apply the DEFERRED policy.)

### Missing coverage
(Any FR/NFR/AC not in the report at all.)

### Test validity issues
(Any cited test that doesn't actually test the claim.)

### Arithmetic
(Did the verdict counts add up?)

## Verdict

VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

Be adversarial. End with the verdict line verbatim.
