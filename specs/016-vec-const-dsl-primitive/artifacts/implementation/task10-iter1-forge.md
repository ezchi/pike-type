# Task 10: Add integration test tests/test_gen_vec_const.py — Forge Iteration 1

## Files Changed
- `tests/test_gen_vec_const.py` — new.

## Key Implementation Decisions
- Modeled on `tests/test_gen_const_sv.py` (golden-file integration test pattern per Constitution §Testing).
- Two test methods:
  - `test_vec_const_basic_generates_expected_tree` — covers AC-1, AC-2, AC-3, AC-9, AC-10 via byte-for-byte tree compare.
  - `test_vec_const_cross_module_emits_per_symbol_import` — covers AC-11. Tree compare PLUS an explicit substring assertion `import a_pkg::LP_X;` in `b_pkg.sv` for diagnostic clarity (so future regressions surface this specific line as the failing assertion).
- Reused (duplicated, not imported) the `_copy_tree` and `_assert_trees_equal` helpers from `test_gen_const_sv.py` for self-containment. Could be refactored to a shared `tests/_helpers.py` later, but matches existing pattern (each test file currently duplicates these helpers).
- Uses `unittest.TestCase` per Constitution §Testing. No pytest fixtures, no parametrize.

## Deviations from Plan
- None.

## Verification
- `.venv/bin/python -m unittest tests.test_gen_vec_const -v`:
  - `test_vec_const_basic_generates_expected_tree ... ok`
  - `test_vec_const_cross_module_emits_per_symbol_import ... ok`
  - `Ran 2 tests in 0.196s`, `OK`.

## Tests Added
- `tests/test_gen_vec_const.py::GenVecConstIntegrationTest::test_vec_const_basic_generates_expected_tree`
- `tests/test_gen_vec_const.py::GenVecConstIntegrationTest::test_vec_const_cross_module_emits_per_symbol_import`
