# Task 2: Add Python snapshot unit test — Forge Iteration 1

## Files Changed

- `tests/test_keyword_set_snapshot.py` — created. NFR-3 unit test asserting that the Python keyword snapshots in `piketype.validate.keywords` match the live `keyword` module under CPython 3.12.x. Skips on other minor versions.

## Key Implementation Decisions

- **Skip rather than fail on non-3.12.** `@unittest.skipUnless(sys.version_info[:2] == (3, 12), reason)`. Drift on a different Python minor version is an expected condition (the snapshot was captured for 3.12); failing would noise-up CI on environments running 3.13/3.14.
- **Two test methods, not one.** Splitting hard vs. soft keeps failure messages tight: a future drift in just one of the two lists points the maintainer at the right snapshot to update.
- **Skip reason includes the running version.** The skip message tells a maintainer the live interpreter version, which speeds up investigation if the snapshot is stale.

## Deviations from Plan

None.

## Tests Added

The file *is* the test. Verification:

- `.venv/bin/python -m unittest tests.test_keyword_set_snapshot -v` → 2 tests, both skipped (running on Python 3.13.11; expected per the skip guard).
- `basedpyright tests/test_keyword_set_snapshot.py` → 0 errors.

Cross-check against system Python 3.14.4: `keyword.kwlist` and `keyword.softkwlist` content matches the snapshot byte-for-byte. (The skip would not be triggered if and only if the test were run under 3.12; on 3.12 the assertion would pass since the kwlist content is identical to what 3.13/3.14 report.)
