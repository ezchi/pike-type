# Implementation Plan — Spec 009: Struct Accepts Enum as Member

## Architecture Overview

The change extends the existing struct-member pipeline to accept `EnumType` as a fourth member type. No new pipeline stages or architectural layers are needed. Each existing stage gets `EnumType`/`EnumIR` added to its type dispatch, following the identical pattern used by spec 007 (Flags as Struct member).

```
DSL (struct.py) → Freeze (freeze.py) → IR (unchanged) → Validation (engine.py) → Backends (sv/py/cpp)
```

## Components

### 1. DSL Layer — `src/piketype/dsl/struct.py` (edit)

**Changes** (FR-1):
- Import `EnumType` from `piketype.dsl.enum`
- `StructMember.type` annotation: `ScalarType | StructType | FlagsType` → `ScalarType | StructType | FlagsType | EnumType`
- `add_member()` parameter type annotation: add `EnumType` to the union
- `add_member()` isinstance check (line 56): add `EnumType` to the tuple
- `add_member()` error message (line 57): update to include "enum"

**Risk**: Low — pure type union expansion, no logic change.

### 2. Freeze Pipeline — `src/piketype/dsl/freeze.py` (edit)

**Changes** (FR-2, FR-3, FR-4):

a. `_freeze_field_type()` (line 343):
   - Type annotation for `type_obj`: add `EnumType`
   - Add anonymous rejection: `if isinstance(type_obj, EnumType): raise ValidationError("inline anonymous enum member types are not supported in this milestone")`
   - Named EnumType already handled by the `type_definition_map` lookup that returns `TypeRefIR` before the anonymous checks.

b. `_freeze_struct_field()` (line 327):
   - Add `elif isinstance(member.type, EnumType):` branch after the `ScalarType` check inside the `TypeRefIR` padding computation:
     ```python
     elif isinstance(member.type, EnumType):
         pad = compute_padding_bits(member.type.width)
     ```
   - Import `EnumType` at top of file.

c. `_serialized_width_from_dsl()` (line 287):
   - Add `elif isinstance(member.type, EnumType):` branch:
     ```python
     elif isinstance(member.type, EnumType):
         total += byte_count(member.type.width) * 8
     ```

**Risk**: Medium — padding computation is the key correctness-sensitive change. The `EnumType.width` property must return the correct bit width (already implemented in spec 008).

### 3. Validation — `src/piketype/validate/engine.py` (edit)

**Changes** (FR-5):
- Line 80: extend `isinstance(target, (ScalarAliasIR, StructIR, FlagsIR))` to include `EnumIR`
- Line 82-83: update error message from "scalar alias, struct, or flags" to "scalar alias, struct, flags, or enum"
- Import `EnumIR` if not already imported.

**Risk**: Low — single tuple expansion.

### 4. SV Backend — `src/piketype/backends/sv/emitter.py` (edit)

**Changes** (FR-6, FR-7):

a. `_is_sv_composite_ref()` (line 942):
   - `(StructIR, FlagsIR)` → `(StructIR, FlagsIR, EnumIR)`
   - This propagates to all helper class methods (constructor, to_slv, from_slv, to_bytes, from_bytes, copy, compare, sprint) automatically.

b. `_render_sv_helper_field_decl()` (line 760):
   - `isinstance(target, (StructIR, FlagsIR))` → `isinstance(target, (StructIR, FlagsIR, EnumIR))`

c. Import `EnumIR` if not already in the import list.

**Risk**: Low — the generic composite-ref machinery already handles all delegation. Adding EnumIR to the tuple is sufficient.

### 5. Python Backend — `src/piketype/backends/py/emitter.py` (edit)

**Changes** (FR-9):

a. `_render_py_struct_field_coercer()` (line 508):
   - Add `elif isinstance(target, EnumIR):` branch after the `FlagsIR` branch (line 525-532), with strict type checking:
     ```python
     elif isinstance(target, EnumIR):
         lines.extend([
             f"        if isinstance(value, {class_name}):",
             "            return value",
             f'        raise TypeError("{owner_name}.{field_ir.name} must be {class_name}")',
         ])
     ```

**Risk**: Low — identical pattern to the FlagsIR branch. Field annotation, default, to_bytes, and from_bytes already work via generic TypeRefIR paths.

### 6. C++ Backend — `src/piketype/backends/cpp/emitter.py` (edit)

**Changes** (FR-11, FR-12):

a. `_render_cpp_struct_pack_step()` (line 701):
   - `isinstance(target, (StructIR, ScalarAliasIR, FlagsIR))` → add `EnumIR`

b. `_render_cpp_struct_unpack_step()` (line 745):
   - `isinstance(target, (StructIR, ScalarAliasIR, FlagsIR))` → add `EnumIR`

c. Add `_is_enum_ref()` helper after `_is_flags_ref()` (line 1046):
   ```python
   def _is_enum_ref(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> bool:
       return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], EnumIR)
   ```

d. Clone method (line 598-600): add `or _is_enum_ref(field_type=field_ir.type_ir, type_index=type_index)`

**Risk**: Low — tuple expansion and new helper following existing pattern.

### 7. Test Fixture — `tests/fixtures/struct_enum_member/` (new)

**New files** (FR-14):
- `tests/fixtures/struct_enum_member/project/.git/` — empty directory as repo marker (required by `find_repo_root()`)
- `tests/fixtures/struct_enum_member/project/alpha/piketype/types.py` — DSL fixture with:
  - `cmd_t` enum (2-bit, 3 values: IDLE=0, READ=1, WRITE=2)
  - `pkt_t` struct with `cmd_t` enum member + `Bit(8)` scalar
  - `aligned_pkt_t` struct with `cmd_t` enum member + `Bit(8)` scalar + `multiple_of(32)`

### 8. Golden Files — `tests/goldens/gen/struct_enum_member/` (new)

Generated by running `piketype gen` on the fixture after implementation. Expected files (matching existing golden structure):
- `sv/alpha/piketype/types_pkg.sv`
- `sv/alpha/piketype/types_test_pkg.sv`
- `sv/runtime/piketype_runtime_pkg.sv`
- `py/alpha/piketype/types_types.py`
- `py/alpha/piketype/__init__.py`
- `py/alpha/__init__.py`
- `py/__init__.py`
- `py/runtime/__init__.py`
- `py/runtime/piketype_runtime.py`
- `cpp/alpha/piketype/types_types.hpp`
- `cpp/runtime/piketype_runtime.hpp`
- `cpp/runtime/piketype_runtime.cpp`
- `piketype_manifest.json`

### 9. Integration Tests — `tests/test_struct_enum_member.py` (new)

**Test classes** (following `test_struct_flags_member.py` pattern):

a. `StructEnumMemberDSLTest` — DSL acceptance:
   - `test_add_enum_member_accepted` (AC-1)
   - `test_add_enum_member_rejects_non_type` (existing behavior still works)

b. `StructEnumMemberFreezeTest` — Freeze/validation:
   - `test_freeze_produces_type_ref_ir` (AC-2)
   - `test_freeze_padding_bits_2bit` (AC-3) — 2-bit enum → padding_bits=6
   - `test_freeze_padding_bits_8bit` (AC-3) — 8-bit enum → padding_bits=0
   - `test_freeze_rejects_anonymous_enum` (AC-5, AC-23)

c. `StructEnumMemberGoldenTest` — Golden file comparison:
   - `test_golden_match` (AC-6–9, AC-10, AC-14, AC-15, AC-19) — golden content includes C++ `.clone()` call on enum field
   - `test_idempotent` (AC-20)

d. `StructEnumMemberPyRuntimeTest` — Python runtime:
   - `test_round_trip` (AC-12, AC-13)
   - `test_expected_bytes` (AC-18) — e.g., `cmd=WRITE, data=0xFF` → `b'\x02\xff'`
   - `test_multiple_of_byte_count` (AC-16, AC-17)
   - `test_coercer_rejects_none` (AC-11) — asserts `TypeError` when assigning `None`
   - `test_coercer_rejects_raw_enum` (AC-11) — asserts `TypeError` when assigning a raw `IntEnum` value (e.g., `cmd_enum_t.WRITE`) instead of the wrapper class

e. `StructEnumMemberNegativeTest` — Cross-module rejection (AC-22, AC-24):
   - Construct two `FrozenModule` IR objects inline: module A with an `EnumIR`, module B with a `StructIR` whose field has a `TypeRefIR` pointing to module A's enum. Call `validate_repo()` and assert `ValidationError` with "cross-module" message. No fixture needed — pure IR construction in test code.

## Implementation Order

1. **DSL layer** (struct.py) — unblocks all downstream changes
2. **Freeze pipeline** (freeze.py) — padding + serialized width + anonymous rejection
3. **Validation** (engine.py) — allow EnumIR target
4. **SV backend** (sv/emitter.py) — composite ref + field decl
5. **Python backend** (py/emitter.py) — coercer
6. **C++ backend** (cpp/emitter.py) — pack/unpack/clone
7. **Test fixture** — create DSL input
8. **Generate goldens** — run piketype gen, capture output
9. **Integration tests** — golden comparison + runtime tests
10. **Regression check** — run full test suite + `basedpyright` strict mode

## Dependencies

```
DSL (1) → Freeze (2) → Validation (3) → Backends (4,5,6) → Fixture (7) → Goldens (8) → Tests (9) → Regression (10)
```

Backends (4, 5, 6) can be done in any order after validation. Tests (9) depend on goldens (8) which depend on all code changes.

## Risk Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| Enum padding computation incorrect | Medium | Concrete byte examples in spec; runtime expected-bytes test |
| `_serialized_width_from_dsl()` misses EnumType | Medium | `multiple_of()` test fixture exercises this path |
| Backend generic paths silently skip EnumIR | Low | Golden file comparison catches any emission gap |
| Cross-module rejection test gap | Low | Inline test using two-module fixture |

## Estimated Scope

- **6 files edited** (struct.py, freeze.py, engine.py, sv/emitter.py, py/emitter.py, cpp/emitter.py)
- **~2 new files** (fixture types.py, test_struct_enum_member.py)
- **~10 golden files** (generated)
- **~20 lines of production code** changed (mostly tuple expansions)
- **~200 lines of test code** new

## Changelog

- [Gauge iter1] Fixed golden file paths to match actual structure (`sv/alpha/piketype/types_pkg.sv`, etc.)
- [Gauge iter1] Added `.git/` repo marker to fixture.
- [Gauge iter1] Added `test_coercer_rejects_raw_enum` for AC-11 (raw IntEnum rejection).
- [Gauge iter1] Added `test_freeze_padding_bits_8bit` for AC-3 (0 padding case).
- [Gauge iter1] AC-15 mapped to golden content check (C++ clone method).
- [Gauge iter1] Cross-module test specified as inline IR construction (no fixture needed).
- [Gauge iter1] Added `basedpyright` to regression step.
