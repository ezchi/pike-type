# Tasks — Spec 008: Enum() DSL Type

## Task 1: DSL Runtime — EnumType and Enum() factory

**Description**: Create `src/piketype/dsl/enum.py` with `EnumMember` frozen dataclass, `EnumType` mutable dataclass, and `Enum()` factory function. Implement eager DSL-time validation: UPPER_CASE name regex, duplicate name check, negative value check, explicit width range [1, 64]. Implement `add_value()` with sequential auto-fill (`prev + 1`). Implement `width` property (explicit or inferred via `max(1, max_value.bit_length())`, returning `0` for empty enums with no explicit width).

**Files**: `src/piketype/dsl/enum.py` (new)

**Dependencies**: None

**Verification**: `basedpyright` passes. Existing tests pass.

**Covers**: FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7

---

## Task 2: DSL Export

**Description**: Add `Enum` import and `__all__` entry in `src/piketype/dsl/__init__.py`.

**Files**: `src/piketype/dsl/__init__.py` (edit)

**Dependencies**: Task 1

**Verification**: `from piketype.dsl import Enum` works. `basedpyright` passes.

**Covers**: FR-8

---

## Task 3: IR Nodes — EnumValueIR and EnumIR

**Description**: Add `EnumValueIR` and `EnumIR` frozen dataclasses to `ir/nodes.py`. Update the `TypeDefIR` type union to include `EnumIR`.

**Files**: `src/piketype/ir/nodes.py` (edit)

**Dependencies**: None (can be done in parallel with Task 1)

**Verification**: `basedpyright` passes. Existing tests pass.

**Covers**: FR-9, FR-10, FR-11

---

## Task 4: Freeze Logic

**Description**: Edit `dsl/freeze.py` to add `EnumType` to `build_type_definition_map()` isinstance check, add `EnumType` to the duplicate-binding isinstance tuple in `freeze_module()`, and add the `elif isinstance(value, EnumType)` freeze branch. Freeze resolves auto-fill values, computes width (explicit or inferred, `0` for empty), and emits `EnumIR`.

**Files**: `src/piketype/dsl/freeze.py` (edit)

**Dependencies**: Task 1, Task 3

**Verification**: `basedpyright` passes. Existing tests pass.

**Covers**: FR-12, FR-13, FR-14

---

## Task 5: Validation

**Description**: Edit `validate/engine.py` to add the `EnumIR` validation branch (at least one value, UPPER_CASE names, no duplicate names, no duplicate resolved values, non-negative values, width in [1, 64], values fit within width, name ends with `_t`). Add enum value names to `_validate_generated_identifier_collision()`. Add new `_validate_enum_literal_collision()` for cross-enum and enum-vs-constant name uniqueness.

**Files**: `src/piketype/validate/engine.py` (edit)

**Dependencies**: Task 3

**Verification**: `basedpyright` passes. Existing tests pass.

**Covers**: FR-15, FR-16, FR-17, FR-18, FR-19

---

## Task 6: SV Backend — Synth Package

**Description**: Edit `backends/sv/emitter.py` to add `EnumIR` dispatch in `_render_sv_type_block()`. Implement `_render_sv_enum()` for `typedef enum logic` (with width==1 special case). Add `EnumIR` branches in `_render_sv_pack_fn()` (identity), `_render_sv_unpack_fn()` (cast), `_data_width()`, and `_type_byte_count()`.

**Files**: `src/piketype/backends/sv/emitter.py` (edit)

**Dependencies**: Task 3

**Verification**: `basedpyright` passes. Existing tests pass.

**Covers**: FR-20

---

## Task 7: SV Backend — Test Package (Helper Class)

**Description**: Add `EnumIR` dispatch in `render_module_test_sv()`. Implement `_render_sv_enum_helper_class()` with constructor, `to_slv`, `from_slv`, `to_bytes`, `from_bytes`, `copy`, `clone`, `compare`, `sprint`.

**Files**: `src/piketype/backends/sv/emitter.py` (edit)

**Dependencies**: Task 6

**Verification**: `basedpyright` passes. Existing tests pass.

**Covers**: FR-21

---

## Task 8: Python Backend

**Description**: Edit `backends/py/emitter.py` to add `EnumIR` dispatch in `render_module_py()` (with `from enum import IntEnum` when enums present). Implement `_render_py_enum()` emitting `IntEnum` subclass (`<base>_enum_t`) and wrapper class (`<base>_ct`) with `to_bytes`, `from_bytes` (mask padding, reject unknown), `clone`, `__int__`, `__index__`, `__eq__`, `__repr__`. Add `EnumIR` branches to `_resolved_type_width()` and `_type_byte_count()`.

**Files**: `src/piketype/backends/py/emitter.py` (edit)

**Dependencies**: Task 3

**Verification**: `basedpyright` passes. Existing tests pass.

**Covers**: FR-22, FR-23

---

## Task 9: C++ Backend

**Description**: Edit `backends/cpp/emitter.py` to add `EnumIR` dispatch in `render_module_hpp()`. Implement `_render_cpp_enum()` emitting `enum class <base>_enum_t : <uint_type>` (using `_cpp_unsigned_literal()` for initializer values) and wrapper class `<base>_ct` with `to_bytes`, `from_bytes` (mask padding, reject unknown via `validate_value()` switch), `clone`, `operator==`, implicit conversion. Add `EnumIR` branches to `_resolved_type_width()` and `_type_byte_count()`.

**Files**: `src/piketype/backends/cpp/emitter.py` (edit)

**Dependencies**: Task 3

**Verification**: `basedpyright` passes. Existing tests pass.

**Covers**: FR-24, FR-25, FR-26

---

## Task 10: Manifest

**Description**: Edit `manifest/write_json.py` to import `EnumIR` and add the `EnumIR` branch in `_serialize_type_ir()`. Update type annotation. Emit `kind: "enum"`, `resolved_width`, `value_count`, `values` array with `name`/`resolved_value` pairs.

**Files**: `src/piketype/manifest/write_json.py` (edit)

**Dependencies**: Task 3

**Verification**: `basedpyright` passes. Existing tests pass.

**Covers**: FR-27

---

## Task 11: Test Fixture and Golden Files

**Description**: Create `tests/fixtures/enum_basic/project/` with `.git/` marker and `foo/piketype/defs.py` containing four enums: `color_t` (explicit non-contiguous), `cmd_t` (mixed auto-fill + explicit width 8), `flag_t` (single value, width 1), `big_t` (large 2**63 value). Run `piketype gen` to generate outputs. Copy generated `gen/` tree to `tests/goldens/gen/enum_basic/`.

**Files**: `tests/fixtures/enum_basic/project/` (new tree), `tests/goldens/gen/enum_basic/` (new tree)

**Dependencies**: Task 1–10 (all pipeline code must be complete)

**Verification**: `piketype gen` succeeds on the fixture. Golden files exist and are byte-for-byte reproducible.

**Covers**: FR-28, FR-29

---

## Task 12: Integration and Negative Tests

**Description**: Create `tests/test_gen_enum.py` with `unittest.TestCase`. Implement `test_enum_basic` (golden comparison), `test_enum_basic_idempotent` (run twice), and 13 negative test methods (one per FR-31 case: empty enum, non-UPPER_CASE name, duplicate name, negative value, duplicate resolved values, name not `_t`, enumerator collides with constant, collides with other enum's enumerator, collides with generated SV identifier, width > 64, explicit width too small, explicit width < 1, explicit width > 64). Each negative test creates a minimal fixture, runs `piketype gen`, and asserts non-zero exit + expected error substring.

**Files**: `tests/test_gen_enum.py` (new)

**Dependencies**: Task 11

**Verification**: All new tests pass. All existing tests pass. `basedpyright` passes.

**Covers**: FR-30, FR-31, FR-32, AC-1 through AC-18
