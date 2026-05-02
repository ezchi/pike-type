# Task 7: Create tests/test_validate_keywords.py + smoke test — Forge Iteration 1

## Files Changed

- `tests/test_validate_keywords.py` — new. Imports `FIXTURES_DIR`, `GOLDENS_DIR`, `PROJECT_ROOT`, `assert_trees_equal`, `copy_tree` from `tests.test_gen_const_sv` (verified those names are top-level there). Defines `KeywordValidationTest(unittest.TestCase)` with a local `run_piketype` method matching the shape of the existing helper. First test method: `test_keyword_near_miss_type_id_passes`.

## Key Implementation Decisions

- **Local `run_piketype` instead of a shared module-level helper.** Mirrors the existing pattern in `test_gen_const_sv.py:45`. Refactoring the helper into a shared module is intentionally out of scope (plan-corrections note in `tasks.md`).
- **Test docstring quotes the AC.** Each test method's docstring leads with the AC reference so a future reader can trace test-to-spec without leaving the file.
- **Single test in this commit.** Negative tests for the other ACs are added in T-017 alongside the corresponding fixtures from T-009..T-016.

## Deviations from Plan

None.

## Tests Added

`test_keyword_near_miss_type_id_passes` covers AC-7. Verification:

- `.venv/bin/python -m unittest tests.test_validate_keywords -v` → 1 test, OK.
- Full suite: 295 tests, 3 skipped.
- `basedpyright tests/test_validate_keywords.py` clean (no new errors over baseline).
