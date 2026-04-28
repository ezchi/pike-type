# Spec 007 — Struct Accepts Flags as Member

## Overview

Allow `Struct()` to accept `Flags()` instances as member types, in addition to the currently supported `ScalarType` and `StructType`. A Flags member is treated as a named type reference — the Flags type must be a top-level named type in the same module (no inline anonymous Flags, no cross-module references).

### Example

```python
flags_t = Flags().add_flag("invalid").add_flag("overflow").add_flag("timeout")

report_t = Struct().add_member("status", flags_t).add_member("txn_id", Bit(5))
```

This generates a struct where the `status` field occupies the Flags type's byte-aligned width, and `txn_id` occupies 5 bits with the struct's own alignment padding applied afterward.

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

### FR-3: Validation — Allow FlagsIR as Struct Field Target

The struct field validation in `validate/engine.py` must accept `FlagsIR` as a valid type reference target.

- The current allowlist `(ScalarAliasIR, StructIR)` for `TypeRefIR` targets is extended to `(ScalarAliasIR, StructIR, FlagsIR)`.
- Flags fields inherit the existing cross-module restriction: both the Flags type and the containing Struct must be in the same module.
- No cycle detection changes needed — Flags types cannot contain other types, so Flags-as-struct-member cannot introduce cycles.

### FR-4: SystemVerilog Backend — Emit Flags Fields in Structs

The SV backend must correctly emit Flags fields within structs.

- **Struct typedef:** The Flags field is rendered using its type name (already handled by `TypeRefIR` path — `_render_sv_struct_field_type()` returns `field_type.name`).
- **Pack function:** `pack_<struct>()` calls `pack_<flags>()` for Flags fields (already handled by the generic `TypeRefIR` → `pack_{inner_base}()` path).
- **Unpack function:** `unpack_<struct>()` calls `unpack_<flags>()` for Flags fields (already handled by the generic `TypeRefIR` → `unpack_{inner_base}()` path).
- **Dependency ordering:** The Flags type definition must appear before the Struct definition in the generated package. The existing dependency-first ordering handles this since the Struct references the Flags type.

### FR-5: Python Backend — Emit Flags Fields in Struct Wrappers

The Python backend must correctly handle Flags fields in generated struct wrapper classes.

- **Field annotation:** A Flags field is typed as the Flags wrapper class name (e.g., `flags_ct`). Unlike Struct fields, Flags fields are NOT nullable — they always have a value (default: all flags cleared).
- **Field default:** `field(default_factory=<FlagsClassName>)` — a fresh Flags instance with all flags cleared.
- **Field coercer:** Validates the value is an instance of the Flags wrapper class. Does not accept `None`.
- **to_bytes():** Calls `self.<field_name>.to_bytes()` — same pattern as nested Struct fields but without the None check.
- **from_bytes():** Calls `<FlagsClassName>.from_bytes(raw[offset:offset + N])` where N is the Flags type's byte count.
- **Byte count:** `_type_byte_count()` must handle `FlagsIR` — the byte count equals `ceil(len(fields) + alignment_bits) / 8`, which equals `(len(fields) + alignment_bits) // 8` since alignment guarantees byte-alignment.

### FR-6: C++ Backend — Emit Flags Fields in Struct Wrappers

The C++ backend must correctly handle Flags fields in generated struct header/source files.

- **Field declaration:** The Flags field type is the Flags C++ class name.
- **Pack/unpack:** Calls the Flags type's `to_bytes()` / `from_bytes()` methods within the Struct's serialization logic.
- **Byte count:** Uses the Flags type's `kByteCount` constant.

### FR-7: Test Fixture and Golden Files

A new test fixture and corresponding golden files must be created.

- **Fixture:** `tests/fixtures/struct_flags_member/project/alpha/piketype/types.py` containing a Flags type and a Struct type that uses the Flags type as a member.
- **Golden files:** Expected SV, Python, and C++ output in `tests/goldens/gen/struct_flags_member/`.
- **Integration test:** A new test case in the appropriate test file that runs `piketype gen` on the fixture and compares output against goldens.
- **Round-trip test:** Verify that serialization (to_bytes) and deserialization (from_bytes) round-trip correctly for a struct containing a Flags member, in all generated backends.

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
- **AC-8:** The Python backend generates a Struct wrapper class where the Flags field is typed as the Flags wrapper class (not nullable).
- **AC-9:** The Python Struct wrapper's `to_bytes()` correctly serializes the Flags field.
- **AC-10:** The Python Struct wrapper's `from_bytes()` correctly deserializes the Flags field.
- **AC-11:** The C++ backend generates a Struct class where the Flags field uses the Flags C++ class type.
- **AC-12:** The C++ Struct's pack/unpack correctly calls the Flags type's serialization methods.
- **AC-13:** Golden-file integration tests pass for a fixture containing a Struct with a Flags member.
- **AC-14:** The `piketype gen` output is idempotent — running twice produces identical output.
- **AC-15:** Existing tests (all 139 tests from the prior milestone) continue to pass without modification.

## Out of Scope

- Cross-module Flags references in Struct members (blocked by existing milestone constraint).
- Flags types containing other types (Flags remain single-bit boolean fields only).
- Array/vector of Flags as a Struct member.
- Flags as a top-level scalar alias target.
- Default flag values for Flags members within a Struct (all flags default to cleared).
- Runtime type — only generated wrappers are affected, not a shared runtime library.

## Open Questions

None — the design is straightforward extension of existing type reference mechanisms.
