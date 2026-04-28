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

**FR-6**: Auto-fill numbering: when `value` is `None`, the enumerator receives the smallest non-negative integer not yet used by any prior enumerator (explicit or auto-filled) in declaration order. The first auto-filled value with no prior explicit values is `0`.

**FR-7**: `EnumType` exposes a `width` property returning the minimum number of bits needed to represent the largest enumerator value: `max(1, ceil(log2(max_value + 1)))`. For a single-value enum with value `0`, width is `1`.

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
- No duplicate resolved values.
- All resolved values are non-negative.
- `resolved_width > 0`.
- Enum name ends with `_t`.

**FR-16**: The generated-identifier-collision check adds enum-specific generated identifiers (`LP_<UPPER_BASE>_WIDTH`, `LP_<UPPER_BASE>_BYTE_COUNT`, `pack_<base>`, `unpack_<base>`) to the reserved set.

**FR-17**: Enums with `resolved_width > 64` are rejected. This aligns with the constraint that enum values are non-negative integers representable in a 64-bit unsigned integer.

### SystemVerilog Backend

**FR-18**: The synthesizable package emits:
- `localparam int LP_<UPPER_BASE>_WIDTH = <width>;`
- `localparam int LP_<UPPER_BASE>_BYTE_COUNT = <byte_count>;`
- `typedef enum logic [LP_<UPPER_BASE>_WIDTH-1:0] { <NAME0> = <val0>, ... } <name>;`
- `function automatic logic [LP_<UPPER_BASE>_WIDTH-1:0] pack_<base>(<name> a);` that returns `a` (identity cast).
- `function automatic <name> unpack_<base>(logic [LP_<UPPER_BASE>_WIDTH-1:0] a);` that returns a cast of `a`.

For enums with width == 1, the typedef omits the range: `typedef enum logic { ... } <name>;`.

**FR-19**: The verification test package emits a helper class `<base>_ct` with:
- `localparam int WIDTH = LP_<UPPER_BASE>_WIDTH;`
- `localparam int BYTE_COUNT = LP_<UPPER_BASE>_BYTE_COUNT;`
- `rand <name> value;` as primary state.
- `function new(<name> value_in = <first_value>);` — constructor defaulting to first enumerator.
- `function automatic <name> to_slv();` — returns `value`.
- `function void from_slv(<name> value_in);` — sets `value`.
- `task automatic to_bytes(output byte unsigned bytes[]);` — big-endian byte serialization with MSB zero-padding.
- `function void from_bytes(input byte unsigned bytes[]);` — big-endian byte deserialization, masking padding bits.
- `function void copy(input <base>_ct rhs);`
- `function automatic <base>_ct clone();`
- `function automatic bit compare(input <base>_ct rhs);`
- `function automatic string sprint();` — `"<base>_ct(value=<NAME>)"` using `name()` conversion.

### Python Backend

**FR-20**: The Python module emits:
- An `IntEnum` subclass named `<name>` (the original DSL name, e.g., `state_t`). Import `from enum import IntEnum` is added.
- Each enumerator as a class member: `<NAME> = <value>`.

**FR-21**: A wrapper class `<base>_ct` is emitted with:
- `WIDTH = <width>` class attribute.
- `BYTE_COUNT = <byte_count>` class attribute.
- `__init__(self, value: <name> = <name>.<first>)` — stores value; raises `TypeError` if not an instance of the generated `IntEnum`.
- `to_bytes(self) -> bytes` — big-endian, byte-aligned, zero-padded in MSB.
- `from_bytes(cls, data: bytes | bytearray) -> "<base>_ct"` — rejects unknown values (values not in the enum).
- `clone(self) -> "<base>_ct"`.
- `__int__(self) -> int`.
- `__index__(self) -> int`.
- `__eq__(self, other)` — compares by value.
- `__repr__(self) -> str`.

### C++ Backend

**FR-22**: The C++ header emits:
- `enum class <name> : <uint_type> { <NAME0> = <val0>, ... };` where `<uint_type>` is the smallest unsigned integer type that fits `resolved_width` (e.g., `std::uint8_t` for width <= 8).

**FR-23**: A wrapper class `<base>_ct` is emitted with:
- `static constexpr std::size_t WIDTH = <width>;`
- `static constexpr std::size_t BYTE_COUNT = <byte_count>;`
- `using enum_type = <name>;`
- `enum_type value;` as public member.
- Default constructor initializing to the first enumerator.
- Explicit constructor from `enum_type`.
- `std::vector<std::uint8_t> to_bytes() const` — big-endian serialization.
- `void from_bytes(const std::vector<std::uint8_t>& bytes)` — deserialization, rejects unknown values via `validate_value()`.
- `<base>_ct clone() const`.
- `operator enum_type() const` — implicit conversion.
- `bool operator==(const <base>_ct& other) const = default;`

**FR-24**: A private `static enum_type validate_value(enum_type v)` function checks against all known enumerators and throws `std::invalid_argument` for unknown values.

### Manifest

**FR-25**: `_serialize_type_ir()` in `manifest/write_json.py` handles `EnumIR` and emits:
```json
{
  "name": "<name>",
  "kind": "enum",
  "resolved_width": <width>,
  "value_count": <count>,
  "value_names": ["<NAME0>", "<NAME1>", ...],
  "source": { "path": "...", "line": ..., "column": ... }
}
```

### Integration Tests

**FR-26**: A fixture `tests/fixtures/enum_basic/project/` contains a minimal repo with one `piketype/` module defining at least two enums:
- One with all explicit values.
- One with mixed explicit and auto-fill values.

**FR-27**: Golden files in `tests/goldens/gen/enum_basic/` cover all generated outputs: SV package, SV test package, Python module, C++ header, runtime packages, and manifest.

**FR-28**: A test case class in `tests/` runs `piketype gen` on the fixture and compares output byte-for-byte against goldens.

**FR-29**: Negative test cases verify that `piketype gen` fails with appropriate error messages for:
- Enum with no values (empty).
- Enumerator name not UPPER_CASE.
- Duplicate enumerator name.
- Negative explicit value.
- Duplicate resolved values (e.g., two explicit values with the same integer).

## Non-Functional Requirements

**NFR-1**: All generated output must be byte-for-byte deterministic given the same input.

**NFR-2**: `basedpyright` strict mode must pass with zero new errors after the changes.

**NFR-3**: All existing tests must continue to pass (no regressions).

**NFR-4**: The implementation follows the existing patterns: frozen dataclasses for IR, mutable dataclasses with `slots=True` for DSL, `match`/`case` for IR dispatch, keyword-only arguments for helpers.

## Acceptance Criteria

- **AC-1**: `Enum()` is importable from `piketype.dsl` and supports chained `add_value()` calls.
- **AC-2**: `add_value()` rejects non-UPPER_CASE names, duplicate names, and negative values at DSL construction time.
- **AC-3**: Auto-fill numbering assigns the smallest unused non-negative integer.
- **AC-4**: `EnumIR` and `EnumValueIR` are frozen dataclasses in `ir/nodes.py`; `TypeDefIR` includes `EnumIR`.
- **AC-5**: `freeze_module()` correctly freezes `EnumType` into `EnumIR` with resolved auto-fill values and computed width.
- **AC-6**: `validate_repo()` rejects empty enums, non-UPPER_CASE value names, duplicate value names, duplicate resolved values, negative values, and enums not ending with `_t`.
- **AC-7**: SV synthesizable package emits correct `typedef enum logic` with `localparam`, `pack_`, and `unpack_` functions.
- **AC-8**: SV test package emits a helper class with constructor, `to_slv`, `from_slv`, `to_bytes`, `from_bytes`, `copy`, `clone`, `compare`, and `sprint`.
- **AC-9**: Python module emits `IntEnum` subclass and `_ct` wrapper class with `to_bytes`, `from_bytes`, `clone`, `__int__`, `__eq__`, `__repr__`.
- **AC-10**: C++ header emits `enum class` with correct underlying type and `_ct` wrapper class with `to_bytes`, `from_bytes`, `clone`, `operator==`, implicit conversion.
- **AC-11**: C++ `from_bytes` and `validate_value` reject values not matching any enumerator.
- **AC-12**: Python `from_bytes` rejects values not matching any enumerator.
- **AC-13**: Manifest includes enum entries with `kind: "enum"`, `resolved_width`, `value_count`, and `value_names`.
- **AC-14**: Golden-file integration test passes byte-for-byte for the `enum_basic` fixture.
- **AC-15**: Negative integration tests pass for all invalid-input cases (FR-29).
- **AC-16**: All existing tests pass without regressions.
- **AC-17**: `basedpyright` strict mode passes with zero new errors.

## Out of Scope

- Enum as a struct/union member type (future milestone).
- Enum expressions referencing `Const()` values.
- Enum value aliases (multiple names for the same integer).
- Sparse enum ranges or gap detection/warning.
- Enum-to-string runtime helper in generated software (Python enum `name` attribute suffices; C++ would need an explicit map).
- `SoftwareView` overrides for enum fields.

## Open Questions

None — all design decisions are resolved by the v1 product spec and existing codebase patterns.
