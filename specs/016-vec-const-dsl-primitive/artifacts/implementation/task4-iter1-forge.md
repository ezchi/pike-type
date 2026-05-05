# Task 4: Validation negative tests for VecConst — Forge Iteration 1

## Files Changed
- `tests/test_vec_const_validation.py` — new. 5 `unittest.TestCase` methods.

## Key Implementation Decisions
- Tests target `_freeze_vec_const_storage` directly (the freeze-time validation path) for AC-4..AC-7 (overflow, negative, width range), and `VecConst.__init__` directly for AC-8 (base validation).
- AC-4 uses three separate `assertIn` calls to enforce FR-7's three-substring contract: `"300"`, `"8"`, and `"2**8 - 1"` must ALL appear in the error message.
- AC-6 uses `subTest` to cover three bad widths (`0`, `-1`, `-64`) with a single test method (cheaper than three near-identical methods; Constitution §Testing prohibits `parametrize` but `subTest` is plain unittest).
- All tests use `unittest.TestCase` per Constitution §Testing. No pytest fixtures.
- Imports: `VecConst` from public `piketype.dsl`; `_freeze_vec_const_storage` from `piketype.dsl.freeze` (private but stable for our purposes); `ValidationError` from `piketype.errors`; `SourceSpanIR` from `piketype.ir.nodes` for the dummy source.

## Deviations from Plan
- Plan said 5 separate methods. I used `subTest` for AC-6 (three width values: 0, -1, -64). This is a minor convenience deviation — 5 method names still appear (4 + 1 with subTest), so the test count and naming are intact. No semantic deviation.

## Verification
- `.venv/bin/python -m unittest tests.test_vec_const_validation -v`:
  - All 5 tests `ok`.
  - `Ran 5 tests in 0.000s`, `OK`.

## Tests Added
- `test_overflow_8bit_300` (AC-4)
- `test_negative_value_rejected` (AC-5)
- `test_zero_or_negative_width_rejected` (AC-6)
- `test_width_above_64_rejected` (AC-7)
- `test_unsupported_base_rejected` (AC-8)
