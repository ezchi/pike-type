# Tasks — Spec 008: Enum() DSL Type

## Task 1: DSL Runtime — EnumType and Enum() factory

**Description**: Create `src/piketype/dsl/enum.py` with `EnumMember` frozen dataclass (`name: str`, `source: SourceInfo`, `value: int | None`), `EnumType` mutable dataclass (`members: list[EnumMember]`, `_explicit_width: int | None`), and `Enum(width: int | None = None)` factory function. Both `Enum()` and `add_value()` capture source location via `capture_source_info()`. Implement eager DSL-time validation: UPPER_CASE name regex (`^[A-Z][A-Z0-9_]*$`), duplicate name check, negative value check, explicit width range [1, 64]. Implement `add_value()` with sequential auto-fill (`prev + 1`). Implement `width` property (explicit or inferred via `max(1, max_value.bit_length())`, returning `0` for empty enums with no explicit width).

**Files**: `src/piketype/dsl/enum.py` (new)

**Dependencies**: None

**Verification**: `basedpyright` passes. Existing tests pass. Manual smoke: `Enum().add_value("A", 0).add_value("B", 2).add_value("C").add_value("D")` yields members with values `[0, 2, 3, 4]`. `Enum(0)` and `Enum(65)` raise `ValidationError`. `add_value("lowercase")` raises.

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

**Description**: Add `EnumValueIR` frozen dataclass (`name: str`, `source: SourceSpanIR`, `expr: ExprIR`, `resolved_value: int`) and `EnumIR` frozen dataclass (`name: str`, `source: SourceSpanIR`, `width_expr: ExprIR`, `resolved_width: int`, `values: tuple[EnumValueIR, ...]`) to `ir/nodes.py`. Update the `TypeDefIR` type union to include `EnumIR`.

**Files**: `src/piketype/ir/nodes.py` (edit)

**Dependencies**: None (can be done in parallel with Task 1)

**Verification**: `basedpyright` passes. Existing tests pass. `EnumIR` and `EnumValueIR` can be instantiated with correct field types.

**Covers**: FR-9, FR-10, FR-11

---

## Task 4: Freeze Logic

**Description**: Edit `dsl/freeze.py` to add `EnumType` to `build_type_definition_map()` isinstance check, add `EnumType` to the duplicate-binding isinstance tuple in `freeze_module()`, and add the `elif isinstance(value, EnumType)` freeze branch. Freeze resolves auto-fill values (sequential: `prev + 1`), computes width (explicit or `max(1, max_value.bit_length())`, `0` for empty), and emits `EnumIR` with `IntLiteralExprIR` for value expressions and width expression.

**Files**: `src/piketype/dsl/freeze.py` (edit)

**Dependencies**: Task 1, Task 3

**Verification**: `basedpyright` passes. Existing tests pass. A fixture with `Enum(8).add_value("A", 0).add_value("B", 5).add_value("C")` freezes to `EnumIR` with `resolved_width=8` and values `[0, 5, 6]`.

**Covers**: FR-12, FR-13, FR-14

---

## Task 5: Validation

**Description**: Edit `validate/engine.py` to add the `EnumIR` validation branch (at least one value, UPPER_CASE names, no duplicate names, no duplicate resolved values, non-negative values, width in [1, 64], values fit within width, name ends with `_t`). Add enum value names to `_validate_generated_identifier_collision()`. Add new `_validate_enum_literal_collision()` for cross-enum and enum-vs-constant name uniqueness.

**Files**: `src/piketype/validate/engine.py` (edit)

**Dependencies**: Task 3

**Verification**: `basedpyright` passes. Existing tests pass. Verification of all validation rules is deferred to Task 12 (negative integration tests), which covers all 13 rejection cases from FR-31.

**Covers**: FR-15, FR-16, FR-17, FR-18, FR-19

---

## Task 6: SV Backend — Synth Package

**Description**: Edit `backends/sv/emitter.py` to add `EnumIR` dispatch in `_render_sv_type_block()`. Implement `_render_sv_enum()` for `typedef enum logic` (with width==1 special case: omit range). Add `EnumIR` branches in `_render_sv_pack_fn()` (identity), `_render_sv_unpack_fn()` (cast), `_data_width()`, and `_type_byte_count()`. Uses inline string building, consistent with existing SV emitter pattern (see plan.md Dependencies note).

**Files**: `src/piketype/backends/sv/emitter.py` (edit)

**Dependencies**: Task 3

**Verification**: `basedpyright` passes. Existing tests pass. Full verification via golden comparison in Task 12.

**Covers**: FR-20

---

## Task 7: SV Backend — Test Package (Helper Class)

**Description**: Add `EnumIR` dispatch in `render_module_test_sv()`. Implement `_render_sv_enum_helper_class()`:
- `localparam int WIDTH`, `localparam int BYTE_COUNT`
- `rand <name> value;` primary state
- `function new(<name> value_in = <first_enumerator>);` — default constructor
- `function automatic <name> to_slv();` — returns `value`
- `function void from_slv(<name> value_in);` — sets `value`
- `task automatic to_bytes(output byte unsigned bytes[]);` — big-endian, MSB zero-pad
- `function void from_bytes(input byte unsigned bytes[]);` — mask padding
- `function void copy(input <base>_ct rhs);`
- `function automatic <base>_ct clone();`
- `function automatic bit compare(input <base>_ct rhs);`
- `function automatic string sprint();` — `"<base>_ct(value=0x%0h)"`

**Files**: `src/piketype/backends/sv/emitter.py` (edit)

**Dependencies**: Task 6

**Verification**: `basedpyright` passes. Existing tests pass. Full verification via golden comparison in Task 12.

**Covers**: FR-21

---

## Task 8: Python Backend

**Description**: Edit `backends/py/emitter.py` to add `EnumIR` dispatch in `render_module_py()` (with `from enum import IntEnum` when enums present). Implement `_render_py_enum()` emitting:
- `IntEnum` subclass `<base>_enum_t` with `<NAME> = <value>` members
- Wrapper class `<base>_ct` with:
  - `WIDTH`, `BYTE_COUNT` class attributes
  - `__init__(self, value: <base>_enum_t = <base>_enum_t.<first>)` — stores value; raises `TypeError` if not correct `IntEnum`
  - `to_bytes(self) -> bytes` — big-endian, byte-aligned, MSB zero-pad
  - `from_bytes(cls, data)` — `@classmethod`, masks MSB padding, rejects unknown values (`ValueError`)
  - `clone()`, `__int__()`, `__index__()`, `__eq__()`, `__repr__()`
- Add `EnumIR` branches to `_resolved_type_width()` and `_type_byte_count()`.

**Files**: `src/piketype/backends/py/emitter.py` (edit)

**Dependencies**: Task 3

**Verification**: `basedpyright` passes. Existing tests pass. Full verification via golden comparison in Task 12.

**Covers**: FR-22, FR-23

---

## Task 9: C++ Backend

**Description**: Edit `backends/cpp/emitter.py` to add `EnumIR` dispatch in `render_module_hpp()`. Implement `_render_cpp_enum()` emitting:
- `enum class <base>_enum_t : <uint_type> { ... };` using `_cpp_unsigned_literal()` for values
- Wrapper class `<base>_ct` with:
  - `static constexpr std::size_t WIDTH`, `BYTE_COUNT`
  - `using enum_type = <base>_enum_t;`
  - `enum_type value;` public member
  - Default constructor (first enumerator), explicit constructor from `enum_type`
  - `to_bytes()`, `from_bytes()` (masks padding, validates via `validate_value()`)
  - `clone()`, `operator enum_type()`, `operator== = default`
- Private `validate_value()` — switch on known enumerators, throws `std::invalid_argument`
- Add `EnumIR` branches to `_resolved_type_width()` and `_type_byte_count()`.

**Files**: `src/piketype/backends/cpp/emitter.py` (edit)

**Dependencies**: Task 3

**Verification**: `basedpyright` passes. Existing tests pass. Full verification via golden comparison in Task 12.

**Covers**: FR-24, FR-25, FR-26

---

## Task 10: Manifest

**Description**: Edit `manifest/write_json.py` to import `EnumIR` and add the `EnumIR` branch in `_serialize_type_ir()`. Update type annotation. Emit `kind: "enum"`, `resolved_width`, `value_count`, `values` array with `name`/`resolved_value` pairs, and `source` object (path, line, column) — matching existing type serialization pattern.

**Files**: `src/piketype/manifest/write_json.py` (edit)

**Dependencies**: Task 3

**Verification**: `basedpyright` passes. Existing tests pass. Full verification via golden comparison in Task 12.

**Covers**: FR-27

---

## Task 11: Test Fixture and Golden Files

**Description**: Create `tests/fixtures/enum_basic/project/` with `.git/` marker and `foo/piketype/defs.py` containing four enums: `color_t` (explicit: RED=0, GREEN=5, BLUE=10), `cmd_t` (explicit width 8, NOP=0, READ=5, WRITE=6 auto, RESET=7 auto), `flag_t` (single value SET=0, width 1), `big_t` (SMALL=0, LARGE=2**63). Run `piketype gen` to generate outputs. Copy generated `gen/` tree to `tests/goldens/gen/enum_basic/`.

**Files**: `tests/fixtures/enum_basic/project/` (new tree), `tests/goldens/gen/enum_basic/` (new tree)

**Dependencies**: Task 1–10 (all pipeline code must be complete)

**Verification**: `piketype gen` succeeds on the fixture. Golden files exist and are byte-for-byte reproducible.

**Covers**: FR-28, FR-29

---

## Task 12: Integration and Negative Tests

**Description**: Create `tests/test_gen_enum.py` with `unittest.TestCase`. Implement:
- **Golden tests**: `test_enum_basic` (golden comparison), `test_enum_basic_idempotent` (run twice).
- **13 negative tests** (one per FR-31 case): empty enum, non-UPPER_CASE name, duplicate name, negative value, duplicate resolved values, name not `_t`, enumerator collides with constant, collides with other enum's enumerator, collides with generated SV identifier, width > 64, explicit width too small, explicit width < 1, explicit width > 64. Each creates a minimal fixture, runs `piketype gen`, asserts non-zero exit + expected error substring.
- **Python runtime round-trip tests** (following existing flags test pattern): Import generated Python `_enum_t` and `_ct` wrapper from golden output. Test `to_bytes()`/`from_bytes()` with explicit byte vectors. Test `from_bytes()` rejects unknown values. Test constructor rejects non-enum-member. Test `clone()`, `__eq__()`, `__int__()`, `__repr__()`.

**Files**: `tests/test_gen_enum.py` (new)

**Dependencies**: Task 11

**Verification**: All new tests pass. All existing tests pass. `basedpyright` passes.

**Covers**: FR-30, FR-31, FR-32, AC-1 through AC-18
