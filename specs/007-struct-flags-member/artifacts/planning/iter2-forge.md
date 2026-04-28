# Implementation Plan — Spec 007: Struct Accepts Flags as Member

## Overview

This plan covers 11 functional requirements across 4 pipeline stages (DSL → freeze → validation → backends) plus a prerequisite bug fix (SV Flags helper byte layout) and test infrastructure.

## Implementation Order

The changes follow the pipeline's natural data flow. Each step builds on the previous, enabling incremental testing.

### Phase 1: Prerequisite Bug Fix (FR-11)

**Step 1: Fix SV Flags helper `to_bytes()`/`from_bytes()` byte layout**

File: `src/piketype/backends/sv/emitter.py`, function `_render_sv_flags_helper_class()`

Change the bit position calculation in `to_bytes()` from:
```python
bit_pos = num_flags - 1 - idx  # LSB-packed (current, wrong)
```
to:
```python
bit_pos = total_bits - 1 - idx  # MSB-packed (correct, matches typedef)
```

Same change in `from_bytes()`.

**Step 2: Regenerate `flags_basic` golden files**

Run `piketype gen` on the `flags_basic` fixture and update `tests/goldens/gen/flags_basic/sv/alpha/piketype/types_test_pkg.sv`. Only the `_test_pkg` file changes (the `_pkg` synthesizable output is unaffected).

**Verification:** Run existing test suite. All tests must pass with updated goldens. AC-22, AC-23, AC-24.

### Phase 2: DSL and Freeze (FR-1, FR-2, FR-3)

**Step 3: Accept FlagsType in `Struct.add_member()`**

File: `src/piketype/dsl/struct.py`

- Import `FlagsType` from `piketype.dsl.flags`.
- Change `StructMember.type` annotation to `ScalarType | StructType | FlagsType`.
- Change `add_member()` isinstance check to `(ScalarType, StructType, FlagsType)`.
- Update error message to include "flags".

**Step 4: Handle FlagsType in `_freeze_field_type()`**

File: `src/piketype/dsl/freeze.py`

- Add `FlagsType` to the `type_obj` parameter annotation.
- In the function body, after the `type_definition_map` lookup:
  - If `type_obj` is `FlagsType` and not in the map, raise `ValidationError("inline anonymous flags member types are not supported in this milestone")`.
  - If in the map, return `TypeRefIR` (already handled by existing lookup path).

**Step 5: Handle FlagsType in `_serialized_width_from_dsl()`**

File: `src/piketype/dsl/freeze.py`

Add an `elif isinstance(member.type, FlagsType)` branch:
```python
elif isinstance(member.type, FlagsType):
    total += byte_count(len(member.type.flags)) * 8
```

Import `FlagsType` is already present in this file.

**Verification:** Unit test — `Struct().add_member("f", flags_t)` doesn't raise. Freeze produces correct `TypeRefIR`. AC-1, AC-2, AC-4, AC-17.

### Phase 3: Validation (FR-4)

**Step 6: Extend struct field validation allowlist**

File: `src/piketype/validate/engine.py`

Change the isinstance check for TypeRefIR targets from `(ScalarAliasIR, StructIR)` to `(ScalarAliasIR, StructIR, FlagsIR)`. Import `FlagsIR` if not already imported.

**Verification:** AC-3, AC-27.

### Phase 4: SystemVerilog Backend (FR-5, FR-6)

**Step 7: Generalize `_is_sv_struct_ref()` to `_is_sv_composite_ref()`**

File: `src/piketype/backends/sv/emitter.py`

- Rename `_is_sv_struct_ref` to `_is_sv_composite_ref` (or add a new function).
- Change the isinstance check from `StructIR` to `(StructIR, FlagsIR)`.
- Update all call sites (approximately 10+ locations).
- Import `FlagsIR` if not already imported.

This is the key change — all the struct helper class methods (constructor, to_slv, from_slv, to_bytes, from_bytes, copy, compare, sprint) branch on this check. By including FlagsIR, Flags fields are treated as composite types (with helper classes) rather than scalar values.

**Step 8: Update helper field declaration for Flags**

File: `src/piketype/backends/sv/emitter.py`, function `_render_sv_helper_field_decl()`

This function has its own `isinstance(target, StructIR)` check at line 647, separate from `_is_sv_struct_ref()`. It must be updated to also match `FlagsIR`:

```python
if isinstance(target, (StructIR, FlagsIR)):
    return f"{_helper_class_name(target.name)} {field.name};"
```

Without this change, Flags fields would be declared as `flags_t field;` (the typedef) instead of `flags_ct field;` (the helper class), breaking AC-8.

**Verification:** AC-5, AC-6, AC-7, AC-8.

### Phase 5: Python Backend (FR-7, FR-8)

**Step 9: Add FlagsIR handling to `_resolved_type_width()` and `_type_byte_count()`**

File: `src/piketype/backends/py/emitter.py`

In `_resolved_type_width()`:
```python
if isinstance(type_ir, FlagsIR):
    return len(type_ir.fields)
```

In `_type_byte_count()`:
```python
if isinstance(type_ir, FlagsIR):
    return (len(type_ir.fields) + type_ir.alignment_bits) // 8
```

**Step 10: Add FlagsIR handling in struct field emission**

File: `src/piketype/backends/py/emitter.py`

Multiple functions need FlagsIR cases:
- `_render_py_field_annotation()`: Return `<FlagsClassName>` (not nullable).
- `_render_py_field_default()`: Return `field(default_factory=<FlagsClassName>)`.
- `_render_py_struct_field_coercer()`: Validate isinstance, reject None. Add `FlagsIR` branch similar to `StructIR` but without None handling.
- `_render_py_struct_to_bytes()`: Call `self.<field>.to_bytes()` (no None check).
- `_render_py_struct_from_bytes()`: Call `<FlagsClassName>.from_bytes(raw[offset:offset+N])`.

The key distinction from StructIR: Flags fields are NOT nullable. No None checks in to_bytes, no Optional in annotation.

**Verification:** AC-9, AC-10, AC-11, AC-12, AC-15, AC-16.

### Phase 6: C++ Backend (FR-8, FR-9)

**Step 11: Add FlagsIR handling to C++ `_resolved_type_width()` and `_type_byte_count()`**

File: `src/piketype/backends/cpp/emitter.py`

Same pattern as Python (Step 9).

**Step 12: Add FlagsIR handling in C++ struct field emission**

File: `src/piketype/backends/cpp/emitter.py`

Review all struct field emission functions for FlagsIR handling:
- Field type declaration: Use Flags C++ class name.
- `to_bytes()`: Call `<field>.to_bytes()`.
- `from_bytes()`: Call `<field>.from_bytes(...)` — the C++ Flags wrapper uses an instance method (`void from_bytes(const std::vector<std::uint8_t>&)`), not a static factory. The struct must default-construct the Flags field first, then call `from_bytes()` on it. This matches the existing pattern for nested struct fields.
- Reference `BYTE_COUNT`, not `kByteCount`.

**Verification:** AC-13, AC-14, AC-15, AC-16.

### Phase 7: Test Infrastructure (FR-10)

**Step 13: Create test fixture**

File: `tests/fixtures/struct_flags_member/project/alpha/piketype/types.py`

```python
from piketype.dsl import Flags, Struct, Bit

status_t = Flags().add_flag("error").add_flag("warning").add_flag("ready")

report_t = (
    Struct()
    .add_member("status", status_t)
    .add_member("code", Bit(5))
)

aligned_report_t = (
    Struct()
    .add_member("flags", status_t)
    .add_member("data", Bit(3))
    .multiple_of(32)
)
```

This covers: Flags-as-struct-member (report_t) and Flags-with-multiple_of (aligned_report_t).

**Step 14: Generate and commit golden files**

Run `piketype gen` on the fixture. Commit the output tree as golden files in `tests/goldens/gen/struct_flags_member/`.

**Step 15: Add integration test**

File: `tests/test_gen_flags.py` (or new file `tests/test_struct_flags_member.py`)

Add a golden-file test case for `struct_flags_member`. Add idempotency test.

**Step 16: Add Python runtime tests**

File: `tests/test_runtime_bytes.py` (extend existing)

- Round-trip test: Create struct, set flags, to_bytes → from_bytes, verify equality.
- Expected-byte test: Set specific flags, verify exact byte output.
- Multiple_of test: Verify serialized byte count matches expected padded size.

**Step 17: Add cross-module Flags member rejection test**

File: `tests/test_namespace_validation.py` (extend existing)

Add a negative test that creates a Flags type in one module and attempts to use it as a struct member in another module. Verify that validation raises the expected cross-module error.

**Verification:** AC-19, AC-20, AC-21, AC-25, AC-26, AC-27.

## Risk Areas

1. **SV emitter call sites:** `_is_sv_struct_ref()` is called in ~10 locations. Renaming/expanding it requires careful audit of each call site to ensure FlagsIR behaves correctly in all contexts (especially `_is_field_signed()` and padding calculations, which should NOT apply to Flags fields since Flags have `padding_bits == 0`).

2. **Python backend type dispatch:** Several functions use `match`/`case` on `TypeRefIR` and then further dispatch on `type_index[name]`. Each needs a FlagsIR case. Missing a case will produce a runtime error on generation.

3. **C++ backend:** Similar to Python — multiple dispatch points need FlagsIR cases.

## Files Modified

| File | Changes |
|------|---------|
| `src/piketype/dsl/struct.py` | Accept FlagsType (FR-1) |
| `src/piketype/dsl/freeze.py` | Freeze FlagsType fields, width calc (FR-2, FR-3) |
| `src/piketype/validate/engine.py` | Allow FlagsIR target (FR-4) |
| `src/piketype/backends/sv/emitter.py` | Composite ref check, Flags helper fix (FR-5, FR-6, FR-11) |
| `src/piketype/backends/py/emitter.py` | Width/byte-count, field emission (FR-7, FR-8) |
| `src/piketype/backends/cpp/emitter.py` | Width/byte-count, field emission (FR-8, FR-9) |
| `tests/fixtures/struct_flags_member/...` | New fixture (FR-10) |
| `tests/goldens/gen/struct_flags_member/...` | New golden files (FR-10) |
| `tests/goldens/gen/flags_basic/.../types_test_pkg.sv` | Updated golden (FR-11) |
| `tests/test_gen_flags.py` or new test file | Integration test (FR-10) |
| `tests/test_runtime_bytes.py` | Runtime tests (FR-10) |

## Dependency Graph

```
Phase 1 (FR-11 bug fix) → independent, do first
Phase 2 (DSL/freeze) → enables Phase 3
Phase 3 (validation) → enables Phase 4–6
Phase 4 (SV backend) → independent of Phase 5, 6
Phase 5 (Python backend) → independent of Phase 4, 6
Phase 6 (C++ backend) → independent of Phase 4, 5
Phase 7 (tests) → depends on all phases
```

Phases 4, 5, 6 can be done in parallel once Phase 3 is complete.
