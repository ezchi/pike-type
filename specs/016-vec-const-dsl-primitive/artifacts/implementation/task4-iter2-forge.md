# Task 4: Validation negative tests for VecConst — Forge Iteration 2

## Files Changed (in this iteration only)
- `src/piketype/dsl/const.py` — modified. `VecConst.__init__` signature changed from all-keyword to positional-or-keyword for `width` and `value`, keyword-only for `base`. This matches FR-2 verbatim (the spec's `*` separator was after `value`, before `base`).
- `tests/test_vec_const_validation.py` — added `test_positional_width_and_value_accepted` (6th test method) verifying:
  - `VecConst(8, 15, base="dec")` succeeds (width and value accepted positionally)
  - `VecConst(8, 15, "dec")` raises `TypeError` (base remains keyword-only)

## Key Implementation Decisions
- The iter1 implementation had `def __init__(self, *, width, value, base):` which made all three keyword-only — over-restrictive vs FR-2.
- Iter2 fix: `def __init__(self, width, value, *, base):` matches FR-2 exactly.
- Added a positive test for positional usage to lock the signature contract.

## Deviations from Plan
- iter1 had a defect (over-restrictive signature). Gauge iter1 caught it. Iter2 fixes it.

## Verification
- `.venv/bin/python -m unittest tests.test_vec_const_validation -v`: 6 tests, all pass.

## Tests Added (cumulative)
- `test_overflow_8bit_300` (AC-4)
- `test_negative_value_rejected` (AC-5)
- `test_zero_or_negative_width_rejected` (AC-6)
- `test_width_above_64_rejected` (AC-7)
- `test_unsupported_base_rejected` (AC-8)
- `test_positional_width_and_value_accepted` (FR-2 signature contract — added in iter2)
