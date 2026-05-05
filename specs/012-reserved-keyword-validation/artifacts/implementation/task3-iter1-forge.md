# Task 3: Commit A — verify byte parity — Forge Iteration 1

## Files Changed

None. Verification-only task.

## Verification Results

- `basedpyright src/piketype/` → 0 errors, 0 warnings, 0 notes.
- `basedpyright tests/test_keyword_set_snapshot.py` → 0 errors.
- `.venv/bin/python -m unittest discover tests` → 294 tests, OK (3 skipped — including the 2 from `test_keyword_set_snapshot.py` due to running on Python 3.13).
- `git status --short` shows only the two new files (`src/piketype/validate/keywords.py`, `tests/test_keyword_set_snapshot.py`) plus the unrelated untracked `.gemini/` directory inherited from the working tree.

## Conventional Commit

`feat(validate): add reserved-keyword sets and snapshot unit test`

## Deviations from Plan

None.
