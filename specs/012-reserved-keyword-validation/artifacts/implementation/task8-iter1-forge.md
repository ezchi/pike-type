# Task 8: Commit B — verify byte parity — Forge Iteration 1

## Files Changed

None — verification-only task.

## Verification Results

- `basedpyright src/ tests/test_validate_keywords.py tests/test_keyword_set_snapshot.py` → 100 errors total, all pre-existing in `engine.py`/backends. No new errors introduced by commit B; the temporary unused-function warning from T-004 is gone (T-005 wired the helper).
- `.venv/bin/python -m unittest discover tests` → 295 tests, OK (3 skipped — 2 from `test_keyword_set_snapshot.py` due to running on Python 3.13, 1 unrelated pre-existing skip).
- `git diff --stat <commit-A-sha>..HEAD` (after staging commit B) shows: `engine.py` modified; `test_validate_keywords.py` new; `tests/fixtures/keyword_near_miss/` new; `tests/goldens/gen/keyword_near_miss/` new (13 generated files); 4 forge artifacts new. No other changes.
- All existing goldens under `tests/goldens/gen/<other cases>/` unchanged (`git diff` shows zero lines).

## Conventional Commits

T-004+T-005 squashed into commit B-1: `feat(validate): wire reserved-keyword check into validate_repo`.
T-006+T-007 squashed into commit B-2: `test(validate): add keyword-validation smoke fixture and test`.

## Deviations from Plan

None.
