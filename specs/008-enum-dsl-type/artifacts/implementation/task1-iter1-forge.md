# Task 1: DSL Runtime — Forge Iteration 1

## Files Changed
- `src/piketype/dsl/enum.py` — created (was placeholder). Full EnumMember, EnumType, Enum() factory.

## Key Implementation Decisions
- `EnumMember` stores `value: int | None` — `None` means auto-fill, resolved later by freeze.
- `_resolve_max_value()` resolves auto-fill sequentially to compute width, but doesn't store results — freeze does the definitive resolution.
- Width uses `max_value.bit_length()` (integer-safe, no float).

## Deviations from Plan
- None.

## Tests Added
- None (integration tests in Task 12).
