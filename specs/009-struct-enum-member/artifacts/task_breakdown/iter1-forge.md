# Task Breakdown — Spec 009: Struct Accepts Enum as Member

## Task 1: DSL Layer — Accept EnumType in Struct

**File**: `src/piketype/dsl/struct.py`
**FR**: FR-1 | **AC**: AC-1

**Steps**:
1. Add `from piketype.dsl.enum import EnumType` to imports.
2. Update `StructMember.type` annotation to `ScalarType | StructType | FlagsType | EnumType`.
3. Update `add_member()` parameter `type` annotation to include `EnumType`.
4. Update `isinstance` check (line 56) to `(ScalarType, StructType, FlagsType, EnumType)`.
5. Update error message (line 57) to include "enum".

**Verification**: `python -c "from piketype.dsl import Struct, Enum, Bit; e = Enum().add_value('A',0); Struct().add_member('x', e)"` succeeds.

---

## Task 2: Freeze Pipeline — EnumType Field Handling

**File**: `src/piketype/dsl/freeze.py`
**FR**: FR-2, FR-3, FR-4 | **AC**: AC-2, AC-3, AC-5

**Steps**:
1. In `_freeze_field_type()` (line 343): update `type_obj` annotation to include `EnumType`. Add `if isinstance(type_obj, EnumType): raise ValidationError("inline anonymous enum member types are not supported in this milestone")` after the FlagsType check.
2. In `_freeze_struct_field()` (line 327-331): add `elif isinstance(member.type, EnumType): pad = compute_padding_bits(member.type.width)` inside the `TypeRefIR` padding block, between the ScalarType check and the `else: pad = 0`.
3. In `_serialized_width_from_dsl()` (line 287-301): add `elif isinstance(member.type, EnumType): total += byte_count(member.type.width) * 8` after the FlagsType branch.
4. Add `from piketype.dsl.enum import EnumType` to imports if not present.

**Verification**: Create a test script that freezes a struct with an enum member, verify `TypeRefIR` output and correct `padding_bits`.

---

## Task 3: Validation — Allow EnumIR as Struct Field Target

**File**: `src/piketype/validate/engine.py`
**FR**: FR-5 | **AC**: AC-4, AC-22

**Steps**:
1. Line 80: change `isinstance(target, (ScalarAliasIR, StructIR, FlagsIR))` to `isinstance(target, (ScalarAliasIR, StructIR, FlagsIR, EnumIR))`.
2. Lines 82-83: update error message from `"must reference a scalar alias, struct, or flags in this milestone"` to `"must reference a scalar alias, struct, flags, or enum in this milestone"`.

**Verification**: Run `piketype gen` on an enum-containing struct fixture; no validation error.

---

## Task 4: SV Backend — Composite Ref and Field Declaration

**File**: `src/piketype/backends/sv/emitter.py`
**FR**: FR-6, FR-7 | **AC**: AC-6, AC-7, AC-8, AC-9

**Steps**:
1. `_is_sv_composite_ref()` (line 942): change `(StructIR, FlagsIR)` to `(StructIR, FlagsIR, EnumIR)`.
2. `_render_sv_helper_field_decl()` (line 760): change `isinstance(target, (StructIR, FlagsIR))` to `isinstance(target, (StructIR, FlagsIR, EnumIR))`.

**Verification**: Run `piketype gen` on fixture, inspect SV output for enum field in struct typedef and helper class.

---

## Task 5: Python Backend — Enum Field Coercer

**File**: `src/piketype/backends/py/emitter.py`
**FR**: FR-9 | **AC**: AC-10, AC-11, AC-12, AC-13

**Steps**:
1. In `_render_py_struct_field_coercer()` after the `elif isinstance(target, FlagsIR):` block (line 525-532), add:
   ```python
   elif isinstance(target, EnumIR):
       lines.extend([
           f"        if isinstance(value, {class_name}):",
           "            return value",
           f'        raise TypeError("{owner_name}.{field_ir.name} must be {class_name}")',
       ])
   ```

**Verification**: Run `piketype gen` on fixture, inspect Python output for enum field coercer.

---

## Task 6: C++ Backend — Pack/Unpack/Clone for Enum

**File**: `src/piketype/backends/cpp/emitter.py`
**FR**: FR-11, FR-12 | **AC**: AC-14, AC-15

**Steps**:
1. `_render_cpp_struct_pack_step()` (line 701): change `isinstance(target, (StructIR, ScalarAliasIR, FlagsIR))` to `isinstance(target, (StructIR, ScalarAliasIR, FlagsIR, EnumIR))`.
2. `_render_cpp_struct_unpack_step()` (line 745): change `isinstance(target, (StructIR, ScalarAliasIR, FlagsIR))` to `isinstance(target, (StructIR, ScalarAliasIR, FlagsIR, EnumIR))`.
3. Add `_is_enum_ref()` helper after `_is_flags_ref()`:
   ```python
   def _is_enum_ref(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> bool:
       return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], EnumIR)
   ```
4. Clone method (line 598-600): add `or _is_enum_ref(field_type=field_ir.type_ir, type_index=type_index)` to the condition.

**Verification**: Run `piketype gen` on fixture, inspect C++ output for enum field handling.

---

## Task 7: Test Fixture

**Files**: `tests/fixtures/struct_enum_member/project/` (new)
**FR**: FR-14

**Steps**:
1. Create `tests/fixtures/struct_enum_member/project/.git/` (empty dir as repo marker).
2. Create `tests/fixtures/struct_enum_member/project/alpha/piketype/types.py` with:
   ```python
   from piketype.dsl import Bit, Enum, Struct
   
   cmd_t = Enum().add_value("IDLE", 0).add_value("READ", 1).add_value("WRITE", 2)
   
   pkt_t = Struct().add_member("cmd", cmd_t).add_member("data", Bit(8))
   
   aligned_pkt_t = (
       Struct()
       .add_member("cmd", cmd_t)
       .add_member("data", Bit(8))
       .multiple_of(32)
   )
   ```

**Verification**: File exists and is valid Python.

---

## Task 8: Generate Golden Files

**Files**: `tests/goldens/gen/struct_enum_member/` (new)
**FR**: FR-14

**Steps**:
1. Run `piketype gen` on the fixture to generate output.
2. Copy the generated `gen/` tree to `tests/goldens/gen/struct_enum_member/`.
3. Verify golden files include expected enum field patterns (check SV typedef, helper class, Python wrapper, C++ class).

**Verification**: Golden files exist and contain enum field references.

---

## Task 9: Integration and Runtime Tests

**File**: `tests/test_struct_enum_member.py` (new)
**FR**: FR-14 | **AC**: AC-1–5, AC-11, AC-12, AC-13, AC-16–24

**Steps**:
1. Create `tests/test_struct_enum_member.py` following `test_struct_flags_member.py` structure.
2. Implement test classes:
   - `StructEnumMemberDSLTest`: `test_add_enum_member_accepted`
   - `StructEnumMemberFreezeTest`: `test_freeze_produces_type_ref_ir`, `test_freeze_padding_bits_2bit`, `test_freeze_padding_bits_8bit`, `test_freeze_rejects_anonymous_enum`
   - `StructEnumMemberGoldenTest`: `test_golden_match`, `test_idempotent`
   - `StructEnumMemberPyRuntimeTest`: `test_round_trip`, `test_expected_bytes`, `test_multiple_of_byte_count`, `test_coercer_rejects_none`, `test_coercer_rejects_raw_enum`
   - `StructEnumMemberNegativeTest`: `test_cross_module_enum_rejected` (inline IR construction with `RepoIR`)

**Verification**: `python -m pytest tests/test_struct_enum_member.py` passes.

---

## Task 10: Regression Check

**Steps**:
1. Run `python -m pytest tests/` — all existing tests pass.
2. Run `basedpyright` strict mode — zero new errors.

**Verification**: All tests pass, no type errors.
