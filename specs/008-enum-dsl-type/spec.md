# Spec 008: Enum() DSL Type — All Languages

## Overview

Implement the `Enum()` DSL type end-to-end across all layers of the piketype pipeline: DSL runtime, frozen IR, freeze logic, validation, SystemVerilog backend, Python backend, C++ backend, manifest serialization, and golden-file integration tests.

This corresponds to v1 delivery order steps 10–11 (Enum in SV, then Enum in Python/C++), collapsed into a single spec since the codebase already supports multi-language generation for all existing types.

## User Stories

**US-1**: As a hardware engineer, I want to define named enumerations in the piketype DSL so that I can express finite-state-machine states and command opcodes as first-class typed constants.

**US-2**: As a verification engineer, I want generated SystemVerilog enum typedefs and helper classes so that I can use named constants in testbenches with pack/unpack/randomize/compare support.

**US-3**: As a software developer, I want generated Python and C++ enum wrappers so that I can work with the same enum definitions in simulation models and controller code, with correct serialization to/from the canonical SV byte layout.

**US-4**: As a piketype user, I want enum types to participate in struct members so that I can compose enums into packet definitions (future milestone — not implemented in this spec, but the IR must not preclude it).

## Functional Requirements

### DSL Runtime

**FR-1**: A new `Enum()` factory function is exported from `piketype.dsl` and returns a mutable `EnumType` DSL object. Source location is captured via `capture_source_info()` at the call site.

**FR-2**: `EnumType.add_value(name: str, value: int | None = None) -> EnumType` appends one enumerator and returns `self` for chaining. Source location is captured at each `add_value()` call.

**FR-3**: Enumerator names must match `^[A-Z][A-Z0-9_]*$` (UPPER_CASE). `add_value()` raises `ValidationError` immediately if the name does not match.

**FR-4**: Enumerator names must be unique within one enum. `add_value()` raises `ValidationError` immediately on duplicate name.

**FR-5**: Explicit enumerator values must be non-negative integers. `add_value()` raises `ValidationError` immediately if `value < 0`.

**FR-6**: Auto-fill numbering: when `value` is `None`, the enumerator receives the previous enumerator's resolved value plus one. If there is no preceding enumerator, the value is `0`. This matches the standard C/C++/SystemVerilog convention. Example: `add_value("A", 0).add_value("B", 2).add_value("C").add_value("D")` yields `A=0, B=2, C=3, D=4`.

**FR-7**: `EnumType` exposes a `width` property returning the minimum number of bits needed to represent the largest enumerator value: `max(1, ceil(log2(max_value + 1)))`. For a single-value enum with value `0`, width is `1`. For an empty enum (no values added yet), width returns `0` — validation will reject this, but the property itself does not raise.

**FR-8**: `Enum` is added to the `__all__` export list in `piketype/dsl/__init__.py`.

### IR Nodes

**FR-9**: A new `EnumValueIR` frozen dataclass is added to `ir/nodes.py`:
- `name: str`
- `source: SourceSpanIR`
- `expr: ExprIR` (the expression representing the value — `IntLiteralExprIR` for literal values)
- `resolved_value: int`

**FR-10**: A new `EnumIR` frozen dataclass is added to `ir/nodes.py`:
- `name: str`
- `source: SourceSpanIR`
- `width_expr: ExprIR` (an `IntLiteralExprIR` holding the computed width)
- `resolved_width: int`
- `values: tuple[EnumValueIR, ...]`

**FR-11**: The `TypeDefIR` type union is updated to include `EnumIR`: `type TypeDefIR = ScalarAliasIR | StructIR | FlagsIR | EnumIR`.

### Freeze

**FR-12**: `build_type_definition_map()` in `dsl/freeze.py` adds `EnumType` to its `isinstance` check so that top-level enum bindings are discovered.

**FR-13**: `freeze_module()` adds an `elif isinstance(value, EnumType)` branch that:
- Resolves auto-fill values into concrete integers.
- Computes width from the maximum resolved value.
- Emits an `EnumIR` node with `IntLiteralExprIR` for both value expressions and width expression.

**FR-14**: The duplicate-binding check in `freeze_module()` includes `EnumType` in its `isinstance` tuple.

### Validation

**FR-15**: `validate_repo()` adds an `EnumIR` branch that checks:
- At least one value (reject empty enums).
- All value names match `^[A-Z][A-Z0-9_]*$`.
- No duplicate value names.
- No duplicate resolved values (two enumerators with the same integer are rejected).
- All resolved values are non-negative.
- `resolved_width > 0`.
- `resolved_width <= 64`.
- All resolved values fit within `resolved_width` bits (i.e., `value < 2**resolved_width` for all values).
- `resolved_width` equals the minimum width for the maximum value (consistency check between freeze and validation).
- Enum name ends with `_t`.

**FR-16**: The generated-identifier-collision check adds enum-specific generated identifiers (`LP_<UPPER_BASE>_WIDTH`, `LP_<UPPER_BASE>_BYTE_COUNT`, `pack_<base>`, `unpack_<base>`) to the reserved set.

**FR-17**: SV enum literal collision validation: all enumerator value names across all enums in a module, plus all constant names in the same module, must be unique. SystemVerilog enum literals are injected into the enclosing package scope, so `IDLE` in two different enums or a constant named `IDLE` would produce a compilation error. Validation rejects such collisions with a clear diagnostic.

**FR-18**: Enumerator value names must not collide with generated SV identifiers. The existing generated-identifier-collision check (FR-16) adds `LP_<UPPER_BASE>_WIDTH`, `LP_<UPPER_BASE>_BYTE_COUNT`, `pack_<base>`, `unpack_<base>` to the reserved set. Enum value names (which are UPPER_CASE and live in package scope) must also be checked against this reserved set. For example, an enumerator named `LP_STATE_WIDTH` in a module with `state_t` would collide with the generated localparam.

**FR-19**: Enums with `resolved_width > 64` are rejected. This aligns with the constraint that enum values are non-negative integers representable in a 64-bit unsigned integer.

### SystemVerilog Backend

**FR-20**: The synthesizable package emits:
- `localparam int LP_<UPPER_BASE>_WIDTH = <width>;`
- `localparam int LP_<UPPER_BASE>_BYTE_COUNT = <byte_count>;`
- `typedef enum logic [LP_<UPPER_BASE>_WIDTH-1:0] { <NAME0> = <val0>, ... } <name>;`
- `function automatic logic [LP_<UPPER_BASE>_WIDTH-1:0] pack_<base>(<name> a);` that returns the logic value of `a`.
- `function automatic <name> unpack_<base>(logic [LP_<UPPER_BASE>_WIDTH-1:0] a);` that returns a cast of `a`.

For enums with width == 1, the typedef omits the range: `typedef enum logic { ... } <name>;`.

**FR-21**: The verification test package emits a helper class `<base>_ct` with:
- `localparam int WIDTH = LP_<UPPER_BASE>_WIDTH;`
- `localparam int BYTE_COUNT = LP_<UPPER_BASE>_BYTE_COUNT;`
- `rand <name> value;` as primary state.
- `function new(<name> value_in = <first_enumerator>);` — constructor defaulting to first enumerator.
- `function automatic <name> to_slv();` — returns `value`.
- `function void from_slv(<name> value_in);` — sets `value`.
- `task automatic to_bytes(output byte unsigned bytes[]);` — big-endian byte serialization with MSB zero-padding (consistent with existing scalar/struct/flags helpers).
- `function void from_bytes(input byte unsigned bytes[]);` — big-endian byte deserialization, masking padding bits (consistent with existing helpers).
- `function void copy(input <base>_ct rhs);`
- `function automatic <base>_ct clone();`
- `function automatic bit compare(input <base>_ct rhs);`
- `function automatic string sprint();` — format: `"<base>_ct(value=0x%0h)"`.

### Python Backend

**FR-22**: The Python module emits:
- An `IntEnum` subclass named `<base>_enum_t` (e.g., DSL name `state_t` → enum class `state_enum_t`). The import `from enum import IntEnum` is added at module level.
- Each enumerator as a class member: `<NAME> = <value>`.

**FR-23**: A wrapper class `<base>_ct` is emitted (e.g., DSL name `state_t` → wrapper class `state_ct`) with:
- `WIDTH = <width>` class attribute.
- `BYTE_COUNT = <byte_count>` class attribute.
- `__init__(self, value: <base>_enum_t = <base>_enum_t.<first>)` — stores value; raises `TypeError` if not an instance of the generated `IntEnum`.
- `to_bytes(self) -> bytes` — big-endian, byte-aligned, zero-padded in MSB. Consistent with existing type serialization.
- `from_bytes(cls, data: bytes | bytearray) -> "<base>_ct"` — `@classmethod`. Decodes big-endian bytes, masks padding bits in MSB byte to zero before interpreting the integer value, then validates that the integer matches a known enumerator. Raises `ValueError` for unknown values or byte count mismatch.
- `clone(self) -> "<base>_ct"`.
- `__int__(self) -> int`.
- `__index__(self) -> int`.
- `__eq__(self, other)` — compares by enum value.
- `__repr__(self) -> str`.

Note: `to_slv()`/`from_slv()` are not included in this milestone. No existing Python wrapper type (Scalar, Struct, Flags) exposes these methods. Adding them only to Enum would break pattern consistency. This is a codebase-wide gap to address in a future cross-cutting milestone.

### C++ Backend

**FR-24**: The C++ header emits:
- `enum class <base>_enum_t : <uint_type> { <NAME0> = <val0>, ... };` where `<uint_type>` is the smallest unsigned integer type that fits `resolved_width` (using the existing `_cpp_scalar_value_type()` helper with `signed=False`). Enum initializer values must use the existing `_cpp_unsigned_literal()` helper to emit properly-suffixed unsigned literals (e.g., `42U`, `12345ULL`), avoiding ill-formed unsuffixed decimal literals for values exceeding `INT64_MAX`.

**FR-25**: A wrapper class `<base>_ct` is emitted with:
- `static constexpr std::size_t WIDTH = <width>;`
- `static constexpr std::size_t BYTE_COUNT = <byte_count>;`
- `using enum_type = <base>_enum_t;`
- `enum_type value;` as public member.
- Default constructor initializing to the first enumerator.
- Explicit constructor from `enum_type`.
- `std::vector<std::uint8_t> to_bytes() const` — big-endian serialization, consistent with existing types.
- `void from_bytes(const std::vector<std::uint8_t>& bytes)` — deserialization. Decodes big-endian bytes, masks padding bits to zero before interpreting the integer, then validates via `validate_value()`. Throws `std::invalid_argument` on byte count mismatch or unknown enum value.
- `<base>_ct clone() const`.
- `operator enum_type() const` — implicit conversion.
- `bool operator==(const <base>_ct& other) const = default;`

**FR-26**: A private `static enum_type validate_value(enum_type v)` function checks against all known enumerators using a switch statement and throws `std::invalid_argument` for unknown values.

Note: `to_slv()`/`from_slv()` are not included in this milestone, consistent with existing C++ wrapper types.

### Manifest

**FR-27**: `_serialize_type_ir()` in `manifest/write_json.py` handles `EnumIR` and emits:
```json
{
  "name": "<name>",
  "kind": "enum",
  "resolved_width": <width>,
  "value_count": <count>,
  "values": [
    {"name": "<NAME0>", "resolved_value": <val0>},
    {"name": "<NAME1>", "resolved_value": <val1>}
  ],
  "source": { "path": "...", "line": ..., "column": ... }
}
```

### Integration Tests

**FR-28**: A fixture `tests/fixtures/enum_basic/project/` contains a minimal repo with one `piketype/` module defining at least two enums:
- One with all explicit values (including non-contiguous values).
- One with mixed explicit and auto-fill values demonstrating gap-filling behavior.

**FR-29**: Golden files in `tests/goldens/gen/enum_basic/` cover all generated outputs: SV package, SV test package, Python module, C++ header, runtime packages, and manifest.

**FR-30**: A test case class in `tests/` runs `piketype gen` on the fixture and compares output byte-for-byte against goldens.

**FR-31**: Negative test cases verify that `piketype gen` fails with appropriate error messages for:
- Enum with no values (empty).
- Enumerator name not UPPER_CASE (e.g., `lower_case`).
- Duplicate enumerator name within one enum.
- Negative explicit value.
- Duplicate resolved values (e.g., two explicit enumerators with value `1`).
- Enum name not ending with `_t`.
- Enumerator name colliding with a constant name in the same module.
- Enumerator name colliding with an enumerator in a different enum in the same module.
- Enumerator name colliding with a generated SV identifier (e.g., `LP_STATE_WIDTH`).
- Enum value requiring width > 64 (e.g., `value=2**64`).

**FR-32**: Additional positive test coverage (can be in the `enum_basic` fixture or a second fixture):
- Auto-fill sequential behavior: explicit `0, 2` then two auto-fills → `0, 2, 3, 4`.
- Single-value enum (width = 1).
- Large enum value near 64-bit boundary (e.g., `2**63`).

## Non-Functional Requirements

**NFR-1**: All generated output must be byte-for-byte deterministic given the same inputs.

**NFR-2**: `basedpyright` strict mode must pass with zero new errors after the changes.

**NFR-3**: All existing tests must continue to pass (no regressions).

**NFR-4**: The implementation follows the existing patterns: frozen dataclasses for IR, mutable dataclasses with `slots=True` for DSL, `match`/`case` for IR dispatch, keyword-only arguments for helpers.

**NFR-5**: Byte serialization uses big-endian byte order with MSB zero-padding, consistent with all existing type implementations (Scalar, Struct, Flags). This follows the established codebase convention.

## Acceptance Criteria

- **AC-1**: `Enum()` is importable from `piketype.dsl` and supports chained `add_value()` calls.
- **AC-2**: `add_value()` rejects non-UPPER_CASE names, duplicate names, and negative values at DSL construction time.
- **AC-3**: Auto-fill numbering assigns the previous enumerator's value plus one (or `0` for the first enumerator), matching C/SV convention.
- **AC-4**: `EnumIR` and `EnumValueIR` are frozen dataclasses in `ir/nodes.py`; `TypeDefIR` includes `EnumIR`.
- **AC-5**: `freeze_module()` correctly freezes `EnumType` into `EnumIR` with resolved auto-fill values and computed width.
- **AC-6**: `validate_repo()` rejects empty enums, non-UPPER_CASE value names, duplicate value names, duplicate resolved values, negative values, width > 64, values exceeding width, and enums not ending with `_t`.
- **AC-7**: Validation rejects modules where enumerator names collide with constant names, enumerator names from other enums, or generated SV identifiers (e.g., `LP_*_WIDTH`) in the same module.
- **AC-8**: SV synthesizable package emits correct `typedef enum logic` with `localparam`, `pack_`, and `unpack_` functions.
- **AC-9**: SV test package emits a helper class with constructor, `to_slv`, `from_slv`, `to_bytes`, `from_bytes`, `copy`, `clone`, `compare`, and `sprint`.
- **AC-10**: Python module emits `IntEnum` subclass named `<base>_enum_t` and `<base>_ct` wrapper class with `to_bytes`, `from_bytes`, `clone`, `__int__`, `__eq__`, `__repr__`.
- **AC-11**: C++ header emits `enum class <base>_enum_t` with correct underlying type and `<base>_ct` wrapper class with `to_bytes`, `from_bytes`, `clone`, `operator==`, implicit conversion.
- **AC-12**: C++ `from_bytes` and `validate_value` reject values not matching any enumerator.
- **AC-13**: Python `from_bytes` rejects values not matching any enumerator.
- **AC-14**: Manifest includes enum entries with `kind: "enum"`, `resolved_width`, `value_count`, and `values` array with name/resolved_value pairs.
- **AC-15**: Golden-file integration test passes byte-for-byte for the `enum_basic` fixture.
- **AC-16**: Negative integration tests pass for all invalid-input cases (FR-31).
- **AC-17**: All existing tests pass without regressions.
- **AC-18**: `basedpyright` strict mode passes with zero new errors.

## Out of Scope

- Enum as a struct/union member type (future milestone — current `Struct().add_member()` will reject `EnumType` as it is not in its accepted type tuple).
- Enum expressions referencing `Const()` values.
- Enum value aliases (multiple names for the same integer — explicitly rejected by FR-15 duplicate-value check).
- Sparse enum ranges or gap detection/warning.
- `to_slv()`/`from_slv()` in Python/C++ wrappers (no existing type has these; codebase-wide gap for a future milestone).
- `SoftwareView` overrides for enum fields.

## Open Questions

None — all design decisions are resolved by the v1 product spec, existing codebase patterns, and this spec's explicit choices.

## Changelog

- [Clarification iter1] FR-6: Changed auto-fill from "smallest unused non-negative integer" to "previous value + 1" (sequential increment) to match v1 product spec and C/SV convention.
- [Clarification iter1] AC-3: Updated wording to match corrected FR-6 auto-fill semantics.
- [Clarification iter1] FR-32: Updated test example from `0, 2, 1, 3` to `0, 2, 3, 4` to match corrected FR-6.
