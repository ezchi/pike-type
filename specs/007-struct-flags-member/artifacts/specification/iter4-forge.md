# Spec 007 — Struct Accepts Flags as Member

## Overview

Allow `Struct()` to accept `Flags()` instances as member types, in addition to the currently supported `ScalarType` and `StructType`. A Flags member is treated as a named type reference — the Flags type must be a top-level named type in the same module (no inline anonymous Flags, no cross-module references).

### Example

```python
flags_t = Flags().add_flag("invalid").add_flag("overflow").add_flag("timeout")

report_t = Struct().add_member("status", flags_t).add_member("txn_id", Bit(5))
```

This generates a struct where the `status` field occupies the Flags type's byte-aligned width (1 byte for 3 flags), and `txn_id` occupies 5 bits padded to 1 byte (per existing per-member byte alignment).

## User Stories

- **US-1:** As a hardware engineer, I want to embed a Flags type inside a Struct so that I can model real register maps and packet headers that contain both scalar fields and flag bitmasks.
- **US-2:** As a firmware developer, I want generated C++ and Python struct wrappers to correctly serialize/deserialize Flags fields so that I can manipulate individual flags within a struct without manual bit manipulation.
- **US-3:** As a verification engineer, I want generated SystemVerilog structs to include Flags fields as packed sub-types so that I can use them in RTL and testbenches without manual type composition.

## Functional Requirements

### FR-1: DSL Layer — Accept FlagsType as Struct Member

`Struct.add_member()` must accept `FlagsType` instances in addition to `ScalarType` and `StructType`.

- The `StructMember.type` union becomes `ScalarType | StructType | FlagsType`.
- Validation in `add_member()` must allow `FlagsType` without raising `ValidationError`.
- A `FlagsType` passed to `add_member()` must be a named top-level type (assigned to a module-level variable). Anonymous inline Flags are rejected during freeze, consistent with how anonymous inline Structs are currently rejected.

### FR-2: Freeze Pipeline — Freeze FlagsType Members to TypeRefIR

`_freeze_field_type()` in `dsl/freeze.py` must handle `FlagsType` instances.

- If the `FlagsType` is found in `type_definition_map` (i.e., it is a named top-level type), freeze it as a `TypeRefIR` pointing to the corresponding `FlagsIR`.
- If the `FlagsType` is NOT in `type_definition_map` (anonymous), raise `ValidationError` with message: `"inline anonymous flags member types are not supported in this milestone"`.
- No new IR node types are introduced. `FieldTypeIR` remains `ScalarTypeSpecIR | TypeRefIR`.

### FR-3: Freeze Pipeline — `_serialized_width_from_dsl()` Must Handle FlagsType Members

`_serialized_width_from_dsl()` in `dsl/freeze.py` currently computes serialized width for `Struct.multiple_of()` by iterating struct members and handling only `ScalarType` and `StructType`. It must also handle `FlagsType` members.

- For a `FlagsType` member, the serialized width contribution equals the Flags type's byte-aligned width: `ceil(flag_count / 8) * 8` bits (i.e., `byte_count(flag_count) * 8`).
- This ensures that `Struct().add_member("flags", flags_t).multiple_of(N)` computes trailing alignment correctly, including the Flags member's contribution.

### FR-4: Validation — Allow FlagsIR as Struct Field Target

The struct field validation in `validate/engine.py` must accept `FlagsIR` as a valid type reference target.

- The current allowlist `(ScalarAliasIR, StructIR)` for `TypeRefIR` targets is extended to `(ScalarAliasIR, StructIR, FlagsIR)`.
- Flags fields inherit the existing cross-module restriction: both the Flags type and the containing Struct must be in the same module.
- No cycle detection changes needed — Flags types cannot contain other types, so Flags-as-struct-member cannot introduce cycles.

### FR-5: SystemVerilog Backend — Emit Flags Fields in Structs

The SV backend must correctly emit Flags fields within structs.

- **Struct typedef:** The Flags field is rendered using its type name (already handled by `TypeRefIR` path — `_render_sv_struct_field_type()` returns `field_type.name`).
- **Pack function:** `pack_<struct>()` calls `pack_<flags>()` for Flags fields (already handled by the generic `TypeRefIR` → `pack_{inner_base}()` path).
- **Unpack function:** `unpack_<struct>()` calls `unpack_<flags>()` for Flags fields (already handled by the generic `TypeRefIR` → `unpack_{inner_base}()` path).
- **Dependency ordering:** The Flags type definition must appear before the Struct definition in the generated package. The current type output order is sorted by `(source.line, name)`. For conventional DSL usage — where the Flags object is assigned to a module-level variable before being passed to `add_member()` — source-line order naturally places the Flags type first. This is not a topological sort; it relies on the convention that DSL types are defined at module scope in sequential order. Edge cases (same-line definitions, helper-function-constructed objects) are not addressed by this spec and are pre-existing limitations.

### FR-6: SystemVerilog Backend — Helper Class Flags Field Handling

The SV struct helper class (`_render_sv_struct_helper_class`) must correctly handle Flags-typed fields.

- **Field declaration:** A Flags field in the helper class is declared as the Flags helper class type (e.g., `my_flags_ct flags_field;`), using the same `_helper_class_name()` mapping. This parallels how nested struct fields use their helper class type.
- **Constructor:** A Flags field is initialized with `new()`, the same as nested struct fields.
- **`_is_sv_struct_ref()`** currently checks `isinstance(type_index[name], StructIR)`. This must be generalized to also recognize `FlagsIR` targets. A new helper (or expanded check) is needed: `_is_sv_composite_ref()` that returns true for both `StructIR` and `FlagsIR`. All call sites that branch on "struct ref vs scalar" must use this expanded check.
- **`to_slv()`:** For Flags fields, assigns the typedef field directly: `packed_value.<field> = <field>.to_slv();` — the same pattern as nested struct fields. Does NOT call `pack_<flags>()`, which returns data-width-only bits and would produce incorrect padding. The Flags helper's `to_slv()` already returns the full typedef including alignment padding.
- **`from_slv()`:** For Flags fields, delegates directly: `<field>.from_slv(value_in.<field>);` — the same pattern as nested struct fields. Does NOT call `unpack_<flags>()`. The Flags helper's `from_slv()` already accepts the full typedef.
- **`to_bytes()`:** For Flags fields, delegates to the Flags helper's `to_bytes()` task, which appends its bytes into a temporary array. The struct helper then copies those bytes into its output array — the same delegation pattern as nested struct fields. Note: the SV Flags helper `to_bytes()` uses a data-bit-only encoding (flags in LSB positions), which differs from the Python/C++ Flags wrapper encoding (flags in MSB positions matching the typedef). This is a pre-existing inconsistency in the Flags helper implementation (spec 005), not introduced by spec 007. Within each backend, the struct helper and the Flags helper produce mutually consistent bytes, so delegation is correct. Fixing the cross-backend byte layout divergence is out of scope.
- **`from_bytes()`:** For Flags fields, copies the relevant byte slice into a temporary `field_bytes` array and calls `<field>.from_bytes(field_bytes)` — the same pattern as nested struct fields. Does NOT use packed part-select syntax on dynamic arrays.
- **`copy()`:** For Flags fields, delegates to `<field>.copy(rhs.<field>)` — same as nested struct fields.
- **`compare()`:** For Flags fields, delegates to `<field>.compare(rhs.<field>)` — same as nested struct fields.

### FR-7: Python Backend — Emit Flags Fields in Struct Wrappers

The Python backend must correctly handle Flags fields in generated struct wrapper classes.

- **Field annotation:** A Flags field is typed as the Flags wrapper class name (e.g., `flags_ct`). Unlike Struct fields, Flags fields are NOT nullable — they always have a value (default: all flags cleared).
- **Field default:** `field(default_factory=<FlagsClassName>)` — a fresh Flags instance with all flags cleared.
- **Field coercer:** Validates the value is an instance of the Flags wrapper class. Does not accept `None`. Raises `TypeError` if the value is not the correct Flags class.
- **to_bytes():** Calls `self.<field_name>.to_bytes()` — same pattern as nested Struct fields but without the None check.
- **from_bytes():** Calls `<FlagsClassName>.from_bytes(raw[offset:offset + N])` where N is the Flags type's byte count.

### FR-8: Python and C++ Backend — Width and Byte Count Resolution for FlagsIR

Both the Python and C++ backends have `_resolved_type_width()` and `_type_byte_count()` helper functions that currently assume all non-`ScalarAliasIR` types are struct-like (iterating `.fields` and accessing `field.type_ir`). This fails for `FlagsIR` because `FlagFieldIR` has no `type_ir` attribute.

- **`_resolved_type_width()`** in both backends must handle `FlagsIR`: the data width equals the number of flags (`len(type_ir.fields)`), since each flag is 1 bit.
- **`_type_byte_count()`** in both backends must handle `FlagsIR`: the byte count equals `ceil((len(type_ir.fields) + type_ir.alignment_bits) / 8)`, which simplifies to `(len(type_ir.fields) + type_ir.alignment_bits) // 8` since alignment guarantees byte-alignment.

### FR-9: C++ Backend — Emit Flags Fields in Struct Wrappers

The C++ backend must correctly handle Flags fields in generated struct header/source files.

- **Field declaration:** The Flags field type is the Flags C++ class name.
- **Pack/unpack:** Calls the Flags type's `to_bytes()` / `from_bytes()` methods within the Struct's serialization logic.
- **Byte count:** Uses the Flags type's `BYTE_COUNT` constant.

### FR-10: Test Fixture and Golden Files

A new test fixture and corresponding golden files must be created.

- **Fixture:** `tests/fixtures/struct_flags_member/project/alpha/piketype/types.py` containing a Flags type and a Struct type that uses the Flags type as a member.
- **Golden files:** Expected SV, Python, and C++ output in `tests/goldens/gen/struct_flags_member/`.
- **Integration test:** A new test case in the appropriate test file that runs `piketype gen` on the fixture and compares output against goldens.
- **Python runtime test — round-trip:** Verify Python runtime round-trip (to_bytes → from_bytes) for a struct containing a Flags member.
- **Python runtime test — expected bytes:** Verify that `to_bytes()` on a struct with a Flags member produces specific expected byte values (not just round-trip consistency). This catches symmetric encode/decode bugs.
- **Python runtime test — `multiple_of()` with Flags:** If the fixture includes a `multiple_of()` struct with a Flags member, verify the serialized byte count matches the expected padded size.
- SV and C++ correctness is verified via golden-file comparison only (no compilation/simulation required), consistent with existing test infrastructure.

## Non-Functional Requirements

- **NFR-1: No new IR node types.** The change reuses `TypeRefIR` for Flags references, avoiding IR schema bloat.
- **NFR-2: Backward compatible.** Existing Struct definitions with only scalar and struct members continue to work unchanged. Existing Flags definitions used standalone continue to work unchanged.
- **NFR-3: Deterministic output.** Generated code containing Flags-as-struct-member is byte-for-byte reproducible.
- **NFR-4: Same-module constraint.** Cross-module Flags references in struct members are rejected, consistent with the existing cross-module restriction for all type references.

## Acceptance Criteria

- **AC-1:** `Struct().add_member("status", flags_t)` does not raise an error when `flags_t` is a `FlagsType` instance.
- **AC-2:** Freezing a Struct with a Flags member produces a `StructIR` whose field has a `TypeRefIR` pointing to the `FlagsIR`.
- **AC-3:** Validation passes for a Struct containing a named Flags member from the same module.
- **AC-4:** Validation rejects an anonymous (unnamed) Flags instance used as a Struct member.
- **AC-5:** The SV backend generates a `typedef struct packed` where the Flags field uses the Flags type name.
- **AC-6:** The SV `pack_<struct>()` function calls `pack_<flags>()` for the Flags field.
- **AC-7:** The SV `unpack_<struct>()` function calls `unpack_<flags>()` for the Flags field.
- **AC-8:** The SV struct helper class declares the Flags field using the Flags helper class type, initializes it with `new()`, and delegates `to_bytes()`/`from_bytes()`/`to_slv()`/`from_slv()`/`copy()`/`compare()` to the Flags helper class.
- **AC-9:** The Python backend generates a Struct wrapper class where the Flags field is typed as the Flags wrapper class (not nullable).
- **AC-10:** The Python Struct wrapper's field coercer rejects `None` for Flags fields and raises `TypeError` for incorrect types.
- **AC-11:** The Python Struct wrapper's `to_bytes()` correctly serializes the Flags field.
- **AC-12:** The Python Struct wrapper's `from_bytes()` correctly deserializes the Flags field.
- **AC-13:** The C++ backend generates a Struct class where the Flags field uses the Flags C++ class type and references `BYTE_COUNT` (not `kByteCount`).
- **AC-14:** The C++ Struct's pack/unpack correctly calls the Flags type's serialization methods.
- **AC-15:** `_resolved_type_width()` in both Python and C++ backends returns the correct data width for `FlagsIR` (number of flags).
- **AC-16:** `_type_byte_count()` in both Python and C++ backends returns the correct byte count for `FlagsIR`.
- **AC-17:** `_serialized_width_from_dsl()` correctly includes FlagsType member width when computing `multiple_of()` alignment.
- **AC-18:** A Struct with both a Flags member and `multiple_of()` produces correct trailing alignment padding that accounts for the Flags member's byte-aligned width.
- **AC-19:** Python runtime test verifies `to_bytes()` produces specific expected byte values for a struct with a Flags member (not just round-trip consistency).
- **AC-20:** Golden-file integration tests pass for a fixture containing a Struct with a Flags member.
- **AC-21:** The `piketype gen` output is idempotent — running twice produces identical output.
- **AC-22:** The existing test suite continues to pass without modification.

## Out of Scope

- Cross-module Flags references in Struct members (blocked by existing milestone constraint).
- Flags types containing other types (Flags remain single-bit boolean fields only).
- Array/vector of Flags as a Struct member.
- Flags as a top-level scalar alias target.
- Default flag values for Flags members within a Struct (all flags default to cleared).
- Runtime type — only generated wrappers are affected, not a shared runtime library.

## Open Questions

None — the design is straightforward extension of existing type reference mechanisms.
