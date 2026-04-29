# Gauge Code Review — Tasks 1-3 (DSL + IR Nodes + Export)

## Role

You are the Gauge — strict code reviewer.

## What was implemented

**Task 1**: `src/piketype/dsl/enum.py` — new file with `EnumMember`, `EnumType`, `Enum()` factory.
**Task 2**: `src/piketype/dsl/__init__.py` — added `Enum` export.
**Task 3**: `src/piketype/ir/nodes.py` — added `EnumValueIR`, `EnumIR`, updated `TypeDefIR`.

## Files to Review

1. `src/piketype/dsl/enum.py` — the main new file
2. `src/piketype/dsl/__init__.py` — the export change
3. `src/piketype/ir/nodes.py` — the IR node additions

## Reference Files (for pattern comparison)

4. `src/piketype/dsl/flags.py` — the pattern Task 1 should follow
5. `src/piketype/dsl/base.py` — DslNode base class
6. `src/piketype/dsl/source_info.py` — source capture

## Spec Requirements to Check

- FR-1: `Enum(width: int | None = None)` factory with `capture_source_info()`, width validation [1, 64]
- FR-2: `add_value(name, value)` with source capture, returns self
- FR-3: UPPER_CASE regex `^[A-Z][A-Z0-9_]*$`, immediate ValidationError
- FR-4: Duplicate name check, immediate ValidationError
- FR-5: Negative value check, immediate ValidationError
- FR-6: Auto-fill: previous + 1, first is 0
- FR-7: Width property: explicit or `max(1, max_value.bit_length())`, 0 for empty
- FR-8: Exported from `piketype.dsl`
- FR-9: `EnumValueIR` with name, source, expr, resolved_value
- FR-10: `EnumIR` with name, source, width_expr, resolved_width, values
- FR-11: `TypeDefIR` includes `EnumIR`

## Code Review Checklist

1. **Correctness**: Does enum.py correctly implement all FR-1 through FR-7?
2. **Code quality**: Clean, follows flags.py pattern?
3. **Constitution compliance**: `from __future__ import annotations`, frozen/mutable dataclasses with slots, etc.
4. **Error handling**: Eager validation at DSL time?
5. **No scope creep**: Only what's needed for Tasks 1-3?

## Output Format

List issues with severity: BLOCKING / WARNING / NOTE.

End with exactly:
```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```
