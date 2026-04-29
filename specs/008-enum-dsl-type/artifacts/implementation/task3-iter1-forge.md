# Task 3: IR Nodes — Forge Iteration 1

## Files Changed
- `src/piketype/ir/nodes.py` — modified. Added `EnumValueIR`, `EnumIR` frozen dataclasses. Updated `TypeDefIR` union.

## Key Implementation Decisions
- `EnumValueIR` follows `ConstIR` pattern: `name`, `source`, `expr`, `resolved_value`.
- `EnumIR` stores `width_expr` and `resolved_width` (both set by freeze, whether explicit or inferred).
- `TypeDefIR` union now: `ScalarAliasIR | StructIR | FlagsIR | EnumIR`.

## Deviations from Plan
- None.

## Tests Added
- None (IR nodes verified by downstream usage in Tasks 4+).
