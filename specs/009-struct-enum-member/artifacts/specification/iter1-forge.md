# Spec 009 — Struct Accepts Enum as Member

## Overview

Allow `Struct()` to accept `Enum()` instances as member types, in addition to the currently supported `ScalarType`, `StructType`, and `FlagsType`. An Enum member is treated as a named type reference — the Enum type must be a top-level named type in the same module (no inline anonymous Enum, no cross-module references).

This closes the gap identified in spec 008 ("Out of Scope: Enum as a struct/union member type").

### Example

```python
cmd_t = Enum().add_value("IDLE", 0).add_value("READ", 1).add_value("WRITE", 2)

pkt_t = Struct().add_member("cmd", cmd_t).add_member("addr", Bit(16))
```

This generates a struct where the `cmd` field occupies the Enum type's byte-aligned width (1 byte for a 2-bit enum padded to 8 bits), and `addr` occupies 16 bits (2 bytes).

### Key Design Note: Enum Padding

Unlike Flags (which are always byte-aligned: `ceil(flag_count/8)*8` bits) and Struct (which manage their own alignment padding), Enum types have arbitrary bit widths (e.g., 2 bits for 3 values). When used as struct members, Enum fields require per-member byte-alignment padding — the same mechanism used for inline scalars and scalar aliases. A 2-bit enum occupies 1 byte (2 data bits + 6 padding bits) in the struct layout.

## User Stories

- **US-1:** As a hardware engineer, I want to embed an Enum type inside a Struct so that I can model register maps and packet headers containing command opcodes, FSM states, and other enumerated fields alongside scalar data.
- **US-2:** As a firmware developer, I want generated C++ and Python struct wrappers to correctly serialize/deserialize Enum fields so that I can manipulate named enumerated values within structs without manual bit manipulation.
- **US-3:** As a verification engineer, I want generated SystemVerilog structs to include Enum fields as packed sub-types so that I can use named constants in RTL-level struct definitions and testbenches.

## Functional Requirements

### FR-1: DSL Layer — Accept EnumType as Struct Member

`Struct.add_member()` must accept `EnumType` instances in addition to `ScalarType`, `StructType`, and `FlagsType`.

- The `StructMember.type` union becomes `ScalarType | StructType | FlagsType | EnumType`.
- Validation in `add_member()` must allow `EnumType` without raising `ValidationError`.
- An `EnumType` passed to `add_member()` must be a named top-level type (assigned to a module-level variable). Anonymous inline Enum types are rejected during freeze, consistent with how anonymous Struct and Flags are currently rejected.

### FR-2: Freeze Pipeline — Freeze EnumType Members to TypeRefIR

`_freeze_field_type()` in `dsl/freeze.py` must handle `EnumType` instances.

- The type annotation for `type_obj` becomes `ScalarType | StructType | FlagsType | EnumType`.
- If the `EnumType` is found in `type_definition_map` (i.e., it is a named top-level type), freeze it as a `TypeRefIR` pointing to the corresponding `EnumIR`.
- If the `EnumType` is NOT in `type_definition_map` (anonymous), raise `ValidationError` with message: `"inline anonymous enum member types are not supported in this milestone"`.
- No new IR node types are introduced. `FieldTypeIR` remains `ScalarTypeSpecIR | TypeRefIR`.

### FR-3: Freeze Pipeline — Padding Bits for Enum Members

`_freeze_struct_field()` in `dsl/freeze.py` must compute per-member padding for Enum fields.

- Unlike Struct and Flags members (which are already byte-aligned and receive `padding_bits=0`), Enum types have arbitrary bit widths. An Enum member requires padding to the next byte boundary, just like scalar fields.
- When `type_ir` is a `TypeRefIR` and `member.type` is an `EnumType`, the padding is `compute_padding_bits(member.type.width)`.
- Example: A 2-bit enum (3 values) gets 6 padding bits to fill to 1 byte.

### FR-4: Freeze Pipeline — `_serialized_width_from_dsl()` Must Handle EnumType Members

`_serialized_width_from_dsl()` in `dsl/freeze.py` currently handles `ScalarType`, `StructType`, and `FlagsType` when computing serialized width for `Struct.multiple_of()`. It must also handle `EnumType`.

- For an `EnumType` member, the serialized width contribution equals `byte_count(enum.width) * 8` bits — the byte-aligned width of the enum.
- This ensures that `Struct().add_member("cmd", cmd_t).multiple_of(N)` computes trailing alignment correctly, including the Enum member's contribution.

### FR-5: Validation — Allow EnumIR as Struct Field Target

The struct field validation in `validate/engine.py` must accept `EnumIR` as a valid type reference target.

- The current allowlist `(ScalarAliasIR, StructIR, FlagsIR)` for `TypeRefIR` targets is extended to `(ScalarAliasIR, StructIR, FlagsIR, EnumIR)`.
- The error message is updated to include "enum" in the list of accepted types.
- Enum fields inherit the existing cross-module restriction: both the Enum type and the containing Struct must be in the same module.
- No cycle detection changes needed — Enum types cannot contain other types.

### FR-6: SystemVerilog Backend — `_is_sv_composite_ref()` Must Include EnumIR

The `_is_sv_composite_ref()` helper in `sv/emitter.py` determines whether a struct field uses a helper class (composite type) or a raw value (scalar). It currently checks `isinstance(type_index[name], (StructIR, FlagsIR))`.

- Extend to `isinstance(type_index[name], (StructIR, FlagsIR, EnumIR))`.
- This single change propagates correct behavior to all struct helper class methods: constructor (`new()`), `to_slv()`, `from_slv()`, `to_bytes()`, `from_bytes()`, `copy()`, `compare()`, and `sprint()` — they all branch on `_is_sv_composite_ref()`.

### FR-7: SystemVerilog Backend — Helper Field Declaration for Enum

`_render_sv_helper_field_decl()` in `sv/emitter.py` currently checks `isinstance(target, (StructIR, FlagsIR))` to decide between helper class declaration (no `rand`) and raw typedef declaration (with `rand`).

- Extend to `isinstance(target, (StructIR, FlagsIR, EnumIR))`.
- An Enum field in the struct helper class is declared as the Enum helper class type (e.g., `cmd_ct cmd;`), not the raw enum typedef. The Enum helper class handles its own `rand` on its internal `value` field.

### FR-8: SystemVerilog Backend — Struct Typedef and Pack/Unpack

The SV struct typedef and synthesizable pack/unpack functions already handle `TypeRefIR` generically:

- **Struct typedef:** `TypeRefIR` fields render using `field_type.name` — the enum typedef name. The enum field width includes padding via the `_pad` suffix field.
- **Pack function:** `pack_<struct>()` calls `pack_<enum>()` for enum fields (generic `TypeRefIR` → `pack_{inner_base}()` path).
- **Unpack function:** `unpack_<struct>()` calls `unpack_<enum>()` for enum fields (generic `TypeRefIR` → `unpack_{inner_base}()` path).

No changes needed in these areas — they work for any `TypeRefIR` target.

### FR-9: Python Backend — Enum Field Coercer

The Python backend field coercer (`_render_py_struct_field_coercer`) dispatches on the target type for `TypeRefIR` fields. Currently: `StructIR` → accept None; `FlagsIR` → strict type check; else (ScalarAliasIR) → type check or construct.

- Add an explicit `elif isinstance(target, EnumIR)` branch with strict type checking, matching the Flags pattern:
  ```python
  if isinstance(value, <EnumWrapperClass>):
      return value
  raise TypeError(...)
  ```
- Enum fields do not accept `None` (non-nullable, same as Flags).
- The coercer does not attempt construction from raw values — only the wrapper class is accepted.

### FR-10: Python Backend — Field Annotation and Default

The existing Python backend generic `TypeRefIR` paths already produce correct output for Enum:

- **Field annotation:** Non-`StructIR` `TypeRefIR` targets return the wrapper class name (not nullable). Enum fields are typed as `cmd_ct` (not `cmd_ct | None`). No change needed.
- **Field default:** `field(default_factory=<ClassName>)` constructs a wrapper instance defaulting to the first enumerator. No change needed.
- **to_bytes:** `TypeRefIR` path calls `self.<field>.to_bytes()`. The None check applies only to `StructIR` targets. Enum fields serialize directly. No change needed.
- **from_bytes:** `TypeRefIR` path calls `<ClassName>.from_bytes(raw[offset:offset+N])`. No change needed.

### FR-11: C++ Backend — Pack/Unpack Must Include EnumIR

The C++ struct pack/unpack steps (`_render_cpp_struct_pack_step` and `_render_cpp_struct_unpack_step`) check `isinstance(target, (StructIR, ScalarAliasIR, FlagsIR))` for `TypeRefIR` fields.

- Extend to `isinstance(target, (StructIR, ScalarAliasIR, FlagsIR, EnumIR))`.
- The generic `.to_bytes()` / `.from_bytes()` delegation already handles Enum wrapper classes correctly.

### FR-12: C++ Backend — Clone Must Include Enum Refs

The C++ struct `clone()` method checks `_is_struct_ref or _is_scalar_ref or _is_flags_ref` to decide whether to call `.clone()` on a field.

- Add `_is_enum_ref()` helper: `isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], EnumIR)`.
- Add `or _is_enum_ref(...)` to the clone condition.

### FR-13: C++ Backend — Field Type, Default, Width/Byte Count

The existing C++ backend generic `TypeRefIR` paths already handle Enum:

- **Field type:** `TypeRefIR` → `_type_class_name(type_index[name].name)` → e.g., `cmd_ct`. No change needed.
- **Field default:** `TypeRefIR` → `{}` (default-constructed). No change needed.
- **`_resolved_type_width()`:** Already has `EnumIR` branch returning `type_ir.resolved_width` (added in spec 008). No change needed.
- **`_type_byte_count()`:** Already has `EnumIR` branch returning `byte_count(type_ir.resolved_width)` (added in spec 008). No change needed.

### FR-14: Test Fixture and Golden Files

A new test fixture and corresponding golden files must be created.

- **Fixture:** `tests/fixtures/struct_enum_member/project/alpha/piketype/types.py` containing an Enum type and a Struct type that uses the Enum as a member.
- **The fixture must include:**
  - A Struct with an Enum member and a scalar member.
  - A Struct with an Enum member and `multiple_of()` to verify alignment padding accounts for the Enum.
  - An Enum with non-byte-aligned width (e.g., 2-bit, 3 values) to exercise the per-member padding logic.
- **Golden files:** Expected SV, Python, and C++ output in `tests/goldens/gen/struct_enum_member/`.
- **Integration test:** A new test case in the appropriate test file that runs `piketype gen` on the fixture and compares output against goldens.
- **Python runtime test — round-trip:** Verify Python runtime round-trip (`to_bytes` → `from_bytes`) for a struct containing an Enum member.
- **Python runtime test — expected bytes:** Verify that `to_bytes()` on a struct with an Enum member produces specific expected byte values (not just round-trip consistency). This catches symmetric encode/decode bugs.
- **Python runtime test — `multiple_of()` with Enum:** Verify the serialized byte count matches the expected padded size for a `multiple_of()` struct with an Enum member.
- SV and C++ correctness is verified via golden-file comparison only, consistent with existing test infrastructure.

## Non-Functional Requirements

- **NFR-1: No new IR node types.** The change reuses `TypeRefIR` for Enum references, consistent with the Struct/Flags/ScalarAlias member pattern.
- **NFR-2: Backward compatible.** Existing Struct definitions with scalar, struct, and flags members continue to work unchanged. Existing standalone Enum definitions continue to work unchanged.
- **NFR-3: Deterministic output.** Generated code containing Enum-as-struct-member is byte-for-byte reproducible.
- **NFR-4: Same-module constraint.** Cross-module Enum references in struct members are rejected, consistent with the existing cross-module restriction for all type references.

## Acceptance Criteria

- **AC-1:** `Struct().add_member("cmd", cmd_t)` does not raise an error when `cmd_t` is an `EnumType` instance.
- **AC-2:** Freezing a Struct with an Enum member produces a `StructIR` whose field has a `TypeRefIR` pointing to the `EnumIR`.
- **AC-3:** The frozen `StructFieldIR` for an Enum member has correct `padding_bits` (e.g., 6 for a 2-bit enum, 0 for an 8-bit enum).
- **AC-4:** Validation passes for a Struct containing a named Enum member from the same module.
- **AC-5:** Freeze rejects an anonymous (unnamed) Enum instance used as a Struct member with `ValidationError`.
- **AC-6:** The SV backend generates a `typedef struct packed` where the Enum field uses the Enum type name with correct padding.
- **AC-7:** The SV `pack_<struct>()` function calls `pack_<enum>()` for the Enum field.
- **AC-8:** The SV `unpack_<struct>()` function calls `unpack_<enum>()` for the Enum field.
- **AC-9:** The SV struct helper class declares the Enum field using the Enum helper class type (e.g., `cmd_ct cmd;`), initializes it with `new()`, and delegates `to_slv()`/`from_slv()`/`to_bytes()`/`from_bytes()`/`copy()`/`compare()`/`sprint()` to the Enum helper class.
- **AC-10:** The Python backend generates a Struct wrapper class where the Enum field is typed as the Enum wrapper class (not nullable).
- **AC-11:** The Python Struct wrapper's field coercer rejects `None` for Enum fields and raises `TypeError` for incorrect types.
- **AC-12:** The Python Struct wrapper's `to_bytes()` correctly serializes the Enum field.
- **AC-13:** The Python Struct wrapper's `from_bytes()` correctly deserializes the Enum field.
- **AC-14:** The C++ backend generates a Struct class where the Enum field uses the Enum C++ wrapper class type and delegates `to_bytes()`/`from_bytes()` correctly.
- **AC-15:** The C++ Struct's clone method calls `.clone()` on the Enum field.
- **AC-16:** `_serialized_width_from_dsl()` correctly includes EnumType member width when computing `multiple_of()` alignment.
- **AC-17:** A Struct with both an Enum member and `multiple_of()` produces correct trailing alignment padding that accounts for the Enum member's byte-aligned width.
- **AC-18:** Python runtime test verifies `to_bytes()` produces specific expected byte values for a struct with an Enum member (not just round-trip consistency).
- **AC-19:** Golden-file integration tests pass for a fixture containing a Struct with an Enum member.
- **AC-20:** The `piketype gen` output is idempotent — running twice produces identical output.
- **AC-21:** The existing test suite continues to pass (no regressions).
- **AC-22:** Validation rejects a Struct member referencing an Enum type from a different module with the existing cross-module error message.

## Out of Scope

- Cross-module Enum references in Struct members (blocked by existing milestone constraint).
- Enum as a Flags member or scalar alias target.
- Array/vector of Enum as a Struct member.
- Default enum values for Enum members within a Struct (the Enum defaults to its first enumerator).
- `to_slv()`/`from_slv()` in Python/C++ wrappers (codebase-wide gap for a future milestone).

## Open Questions

None — the design follows the established Flags-as-struct-member pattern (spec 007) with the additional padding consideration for non-byte-aligned enum widths.
