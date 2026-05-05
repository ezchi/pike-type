# Task 5: Wire validator + scan + repair (atomic) — Forge Iteration 1

## Files Changed

- `src/piketype/validate/engine.py` — modified. Added the wire call as the last line of `validate_repo`:

  ```python
  _validate_reserved_keywords(repo=repo)
  ```

## Sub-step results

- **Sub-step 1 (Wire).** Added the single call site. No other changes.
- **Sub-step 2 (Scan).** Ran `.venv/bin/python -m unittest discover tests` after wiring. Result: 294 tests, OK (3 skipped). No incidental fixture breakage detected.
- **Sub-step 3 (Repair).** No-op — sub-step 2 produced zero failures.

## Key Implementation Decisions

- **Single atomic commit.** The full task fits in one commit because the wire change is a single line and the scan revealed no breakage. There is no intermediate broken state.
- **Placement at the end of `validate_repo`.** After `_validate_repo_struct_cycles` and `_validate_cross_module_name_conflicts`, matching plan §C-2 and FR-9 ("structural validations first, then keyword validation"). This ensures that any structural defect (duplicate field name, missing `_t`, non-UPPER_CASE enum value) fires its own error before the keyword check sees the offending identifier.

## Deviations from Plan

None.

## Tests Added

None new — T-006/T-007 add the smoke fixture and test. Verification:

- Pyright back to baseline (100 errors, all pre-existing in engine.py and other backend files; no new errors introduced by the wire change).
- `python -m unittest discover tests` → 294 tests, OK (3 skipped).
