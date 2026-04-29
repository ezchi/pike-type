# Delta Revision — Iteration 3

## User Feedback

> FR-7, it should also allow user to set the width. for example, `Enum(3)`, should set the width of enum to 3-bit. if the user set width is not enough to represent the max value of the enum, raise error. if the width is not specified, `Enum()`, work out the minimum number of bits needed.

## Changes Made

### 1. FR-1 (spec.md) — Enum() factory signature
- **Before**: `Enum()` takes no arguments.
- **After**: `Enum(width: int | None = None)` accepts an optional explicit width. When `None`, width is inferred.

### 2. FR-7 (spec.md) — Width property behavior
- **Before**: Width is always inferred from `max(1, ceil(log2(max_value + 1)))`.
- **After**: If user provides explicit width via `Enum(width)`, that is stored and used. The `width` property returns the explicit width if set, otherwise the inferred minimum. Validation rejects if explicit width is too small for the largest value.

### 3. FR-5 (spec.md) — DSL-time width validation
- **Added**: `Enum()` raises `ValidationError` immediately if `width` is provided and `width < 1` or `width > 64`.

### 4. FR-13 (spec.md) — Freeze uses explicit or inferred width
- **Before**: Freeze always computes width from max value.
- **After**: If `EnumType` has an explicit width, freeze uses it; otherwise infers.

### 5. FR-15 (spec.md) — Validation checks explicit width sufficiency
- **Before**: Only checks `resolved_width` equals minimum width.
- **After**: Checks all values fit within `resolved_width` (whether explicit or inferred). Removes the consistency check that `resolved_width` must equal the minimum — it can now be larger.

### 6. FR-10 (spec.md) — EnumIR stores whether width was explicit
- **No change needed**: `EnumIR` already stores `width_expr` and `resolved_width`. An explicit width just changes the value of `resolved_width` (it may be larger than the minimum). The IR doesn't need to distinguish explicit vs inferred — the resolved value is what backends use.

### 7. clarifications.md — New CLR-7 added

### 8. Changelog — New entry added

## Sections NOT Modified

- FR-2, FR-3, FR-4, FR-6, FR-8 (DSL add_value and export)
- FR-9, FR-11 (IR nodes — EnumValueIR, TypeDefIR union)
- FR-12, FR-14 (freeze discovery and duplicate check)
- FR-16, FR-17, FR-18, FR-19 (validation collision checks, width > 64 rejection)
- FR-20 through FR-27 (all backends and manifest — they consume `resolved_width` which works regardless of how it was determined)
- FR-28 through FR-32 (tests — existing tests are unaffected; new test cases added)
- All NFRs, US-1 through US-4
- Out of Scope, Open Questions
