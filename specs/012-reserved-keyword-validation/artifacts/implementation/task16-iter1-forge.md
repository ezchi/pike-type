# Task 16: Ordering fixture — lowercase enum value `for` (AC-11) — Forge Iteration 1

## Files Changed

- `tests/fixtures/keyword_enum_ordering_for/project/.git/HEAD` — marker.
- `tests/fixtures/keyword_enum_ordering_for/project/alpha/piketype/types.py` — enum with values `IDLE` and `for` (lowercase).

## Key Implementation Decisions

- The lowercase `for` violates the existing UPPER_CASE structural rule. That rule fires at DSL-construction time inside `Enum.add_value`, which is even earlier than the validate-stage UPPER_CASE check (the DSL also has its own UPPER_CASE guard). The structural-defect error is `enum value name must be UPPER_CASE, got 'for'`. The keyword-validation error wording (`reserved keyword in target language(s)`) does not appear, confirming AC-11.
- The test asserts both `assertIn("UPPER_CASE", result.stderr)` and `assertNotIn("reserved keyword", result.stderr)` to pin the precedence.

## Deviations from Plan

The plan assumed AC-11 verification would hit the validate-stage UPPER_CASE rule (`engine.py:128`). In practice the DSL-stage UPPER_CASE rule fires earlier. Both rules satisfy AC-11 ("structural check fires before keyword check"); the DSL-stage error is just an even-stronger demonstration of correct precedence. No spec change required.

## Tests Added

`test_uppercase_check_fires_before_keyword_check` (T-017). Both assertions hold.
