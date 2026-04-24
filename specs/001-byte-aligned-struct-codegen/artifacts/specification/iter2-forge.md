# Specification: Byte-Aligned Packed Struct Code Generation

**Spec ID:** 001-byte-aligned-struct-codegen  
**Status:** Draft  
**Date:** 2026-04-24  

## Overview

Introduce per-member byte-aligned padding for packed structs across all code generation backends (SystemVerilog, C++, Python). Each struct member is individually padded to byte boundaries in the struct typedef, while pack/unpack functions strip/restore padding to enable compact wire-level serialization. This changes the fundamental struct layout model from tightly packed to byte-aligned-per-member.

## Definitions

- **Data width** (`WIDTH`): The sum of all field data bits in a struct, excluding any padding. For scalars, the declared bit width.
- **Storage width**: The total bit width of the byte-aligned representation, including all per-member padding. Equal to `BYTE_COUNT * 8`.
- **Byte count** (`BYTE_COUNT`): The total number of bytes in the byte-aligned representation. For structs: sum of each field's individual byte count. For scalars: `ceil(WIDTH / 8)`.
- **Field byte count**: For a scalar-typed field of width `w`: `ceil(w / 8)`. For a struct-typed field: the inner struct's `BYTE_COUNT` (which already includes its own internal padding).
- **Padding bits**: For a field with data width `w` and field byte count `b`: `(b * 8) - w` zero-fill bits placed on the MSB side.
- **Type base name**: The type name with any `_t` suffix stripped. `foo_t` → `foo`. `bar_t` → `bar`. Used for localparam names (`LP_FOO_WIDTH`) and function names (`pack_foo`).

## User Stories

- **US-1:** As an RTL designer, I want each struct member individually padded to byte alignment in the `typedef struct packed`, so that byte-addressed memory-mapped registers have naturally aligned fields.
- **US-2:** As an RTL designer, I want standalone `pack_<base_name>` and `unpack_<base_name>` functions in the synthesizable SV package, so that I can convert between the padded struct representation and a compact bit vector for wire-level transport.
- **US-3:** As a verification engineer, I want `to_bytes()` and `from_bytes()` in the SV helper class to serialize/deserialize the full byte-aligned representation (including padding), so that byte arrays match the memory-mapped register layout.
- **US-4:** As a firmware developer, I want the C++ generated struct to use minimum-width native types for scalar fields (uint8_t, uint16_t, uint32_t, uint64_t), and `to_bytes()` to produce big-endian byte arrays identical in layout to the SV verification class output.
- **US-5:** As a firmware developer, I want the Python generated struct to produce identical `to_bytes()` output as the SV and C++ backends, so that cross-language serialization is byte-for-byte consistent.

## Functional Requirements

### FR-1: Per-Member Byte-Aligned Padding — Computation at Freeze Time

The DSL `Struct().add_member()` method SHALL continue to record fields without computing padding (padding depends on resolved widths which are not available until freeze).

The freeze pipeline (`dsl/freeze.py`) SHALL compute `padding_bits` for each field and propagate it into the frozen `StructFieldIR`.

**Padding computation rules:**
- For a scalar-typed field of data width `w`: `padding_bits = (ceil(w / 8) * 8) - w`.
- For a struct-typed field referencing inner struct `S`: `padding_bits = (S.BYTE_COUNT * 8) - S.WIDTH`, where `S.BYTE_COUNT` and `S.WIDTH` are the inner struct's byte count and data width respectively.
- Padding bits are zero-fill bits placed on the MSB side of the field in the packed struct.
- A field whose width is already byte-aligned has `padding_bits = 0`.

### FR-2: IR Representation of Padding

`StructFieldIR` SHALL carry a `padding_bits: int` field (frozen, >= 0) representing the number of zero-fill bits added to byte-align this member.

Derived quantities (NOT stored in IR — computed by backends):
- `WIDTH` = sum of all field data widths (each field's `resolved_width`, no padding).
- `BYTE_COUNT` = sum of each field's individual byte count. For scalar fields: `ceil(resolved_width / 8)`. For struct-typed fields: the inner struct's `BYTE_COUNT`.

### FR-3: SystemVerilog Synthesizable Package — Struct Typedef

The SV `typedef struct packed` SHALL include explicit padding members.

For each field with `padding_bits > 0`:
- Emit `logic [P-1:0] <field_name>_pad;` immediately above (MSB side of) the field, where `P = padding_bits`.
- For 1-bit padding, emit `logic <field_name>_pad;`.

Fields with `padding_bits == 0` have no padding member emitted.

**Padding member naming:** `<field_name>_pad`. The `_pad` suffix is reserved. See FR-11 for collision validation.

**Example** (for `bar_t` with fields: flag_a=1-bit, field_1=13-bit foo_t, status=4-bit, flag_b=1-bit):
```systemverilog
typedef struct packed {
   logic [6:0] flag_a_pad;
   logic       flag_a;
   logic [2:0] field_1_pad;
   foo_t       field_1;
   logic [3:0] status_pad;
   logic [3:0] status;
   logic [6:0] flag_b_pad;
   logic       flag_b;
} bar_t;
```

### FR-4: SystemVerilog Synthesizable Package — Width and Byte Count Localparams

For every type (scalar or struct), emit in the synthesizable package:
```systemverilog
localparam int LP_<UPPER_BASE_NAME>_WIDTH = <width>;
localparam int LP_<UPPER_BASE_NAME>_BYTE_COUNT = <byte_count>;
```

Where `<UPPER_BASE_NAME>` is the type base name (suffix-stripped) in UPPER_SNAKE_CASE.

For scalar types, the typedef SHALL reference the width localparam:
```systemverilog
typedef logic [LP_<UPPER_BASE_NAME>_WIDTH-1:0] <name>;
```

The existing `bit` vs `logic` and `signed` qualifiers in scalar typedefs SHALL be preserved. For signed scalars: `typedef logic signed [LP_<UPPER_BASE_NAME>_WIDTH-1:0] <name>;`.

**Semantics:**
- `WIDTH` = total data bits (excludes padding).
- `BYTE_COUNT` = total bytes in byte-aligned representation (includes padding). For scalars: `ceil(WIDTH / 8)`.

**Examples:**
- `foo_t` (Logic(13)): `LP_FOO_WIDTH = 13`, `LP_FOO_BYTE_COUNT = 2`
- `bar_t` (struct with flag_a=1, field_1=13, status=4, flag_b=1): `LP_BAR_WIDTH = 19`, `LP_BAR_BYTE_COUNT = 5`

### FR-5: SystemVerilog Synthesizable Package — pack/unpack Functions

For every type, emit standalone functions in the synthesizable package:

```systemverilog
function logic [LP_<UPPER_BASE_NAME>_WIDTH-1:0] pack_<base_name>(<type_name> a);
    // Concatenate only data fields (no padding), MSB first in declaration order
endfunction

function <type_name> unpack_<base_name>(logic [LP_<UPPER_BASE_NAME>_WIDTH-1:0] a);
    // Initialize result to '0 (all padding bits = 0)
    // Extract data fields from compact vector, LSB first
endfunction
```

**pack semantics:** Output vector width = `WIDTH`. Contains only data bits, concatenated MSB-to-LSB in declaration order. For struct-typed fields, recursively call `pack_<inner_base_name>`. For scalar fields, use the field value directly.

**unpack semantics:** Input vector width = `WIDTH`. Result is initialized to `'0` to zero-fill all padding. Fields are extracted LSB-first with bit-slice indexing. For struct-typed fields, recursively call `unpack_<inner_base_name>`.

For scalar types, pack/unpack are identity functions (pass-through):
```systemverilog
function logic [LP_FOO_WIDTH-1:0] pack_foo(foo_t a);
    return a;
endfunction

function foo_t unpack_foo(logic [LP_FOO_WIDTH-1:0] a);
    return a;
endfunction
```

**Round-trip invariant:** `pack_<name>(unpack_<name>(v)) == v` for any valid `WIDTH`-bit vector `v`.

### FR-6: SystemVerilog Verification Package — to_bytes / from_bytes

The verification helper class `to_bytes()` task SHALL serialize the full byte-aligned struct (including padding) into a byte array of size `BYTE_COUNT`. Byte order is big-endian (MSB byte first).

The `from_bytes()` task SHALL deserialize a byte array of size `BYTE_COUNT` back into the struct type. Padding bits in the input byte array are ignored — the deserialized struct will have all padding bits set to zero regardless of input padding values.

**Cross-language invariant:** `to_bytes()` output from SV, C++, and Python MUST produce identical byte arrays for the same logical data.

### FR-7: C++ Backend — Native Type Mapping for Scalars

Scalar types with width <= 64 bits SHALL be mapped to the minimum-width native C++ unsigned type:
- width 1–8: `std::uint8_t`
- width 9–16: `std::uint16_t`
- width 17–32: `std::uint32_t`
- width 33–64: `std::uint64_t`

Signed scalars use the corresponding signed type (`std::int8_t`, `std::int16_t`, `std::int32_t`, `std::int64_t`).

Scalar widths > 64 bits are rejected by existing validation (constant width constraint). No action needed.

**Serialization:** `to_bytes()` produces a big-endian byte array of size `BYTE_COUNT`. For example, a 37-bit value `0x12_3456_789A` serializes to `{0x12, 0x34, 0x56, 0x78, 0x9A}` (5 bytes, MSB first, padded to byte count with leading zero bits).

### FR-8: C++ Backend — Struct Padding and Serialization

C++ struct classes SHALL:
- Store `kWidth` (data bits) and `kByteCount` (byte-aligned bytes) as `static constexpr std::size_t`.
- `to_bytes()` serializes the full byte-aligned representation (with padding zeros) as a big-endian byte vector of size `kByteCount`. Each field is serialized into its individual byte count, with MSB padding zeros, concatenated in declaration order.
- `from_bytes()` deserializes from a byte vector of size `kByteCount`. Padding bits in input are ignored — field values are extracted from the data bits only.
- The byte layout MUST match the SV verification class output exactly.

### FR-9: Python Backend — Struct Padding and Serialization

Python struct dataclasses SHALL:
- Store `WIDTH` (data bits) and `BYTE_COUNT` (byte-aligned bytes) as class variables.
- `to_bytes()` returns a `bytes` object of length `BYTE_COUNT` with the full byte-aligned representation (big-endian, padding zeros included). Each field serialized into its individual byte count, concatenated in declaration order.
- `from_bytes()` accepts `bytes` of length `BYTE_COUNT` and returns the dataclass instance. Padding bits in input are ignored — field values are extracted from data bits only.
- The byte layout MUST match the SV and C++ output exactly.

### FR-10: Cross-Language Byte-Level Consistency

For any given type and logical data values, all three backends (SV, C++, Python) MUST produce identical `to_bytes()` output. This is the fundamental serialization contract.

Specifically:
1. The same field order (declaration order, MSB first in the byte stream).
2. The same padding placement (MSB side of each member, zero-filled).
3. The same total byte count.
4. Big-endian byte order throughout.

**Worked example** for `bar_t` with `flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0`:

| Field    | Data bits | Data width | Byte count | Padded byte(s) (hex)  |
|----------|-----------|------------|------------|-----------------------|
| flag_a   | 1         | 1          | 1          | `0x01`                |
| field_1  | 0x1FFF    | 13         | 2          | `0x1F`, `0xFF`        |
| status   | 0xA       | 4          | 1          | `0x0A`                |
| flag_b   | 0         | 1          | 1          | `0x00`                |

`to_bytes()` = `{0x01, 0x1F, 0xFF, 0x0A, 0x00}` (5 bytes, big-endian, MSB first per field).

`pack_bar()` = `19'b1_1_1111_1111_1111_1010_0` = `19'h1_FFFA` (only data bits, MSB to LSB: flag_a, field_1, status, flag_b).

### FR-11: Padding Name Collision Validation

The validation layer SHALL reject struct definitions where any field name ends with `_pad`, since the `_pad` suffix is reserved for generated padding members. This validation runs during the existing validation pass in `validate/engine.py`.

Error message: `"struct <struct_name> field '<field_name>' uses reserved '_pad' suffix"`.

### FR-12: Signed Scalars as Struct Members

Signed scalar types used as struct members SHALL be handled consistently:
- **Padding:** Computed the same as unsigned — based on bit width, not sign. A signed 8-bit scalar gets 0 padding bits (already byte-aligned).
- **SV pack/unpack:** The sign bit is part of the data bits. `pack` extracts the raw bit pattern; `unpack` restores it. No sign extension occurs during pack/unpack.
- **to_bytes serialization:** The field's raw bit pattern (two's complement) is serialized into its byte count, big-endian, same as unsigned. The sign is encoded in the MSB of the data bits.
- **C++ type mapping:** Uses signed native types per FR-7 (`std::int8_t`, etc.).

## Non-Functional Requirements

- **NFR-1: Deterministic output.** Generated code must be byte-for-byte reproducible (per Project Constitution principle 3).
- **NFR-2: Template migration deferred.** The Project Constitution prefers Jinja2 templates for structured output. However, all existing emitters use direct Python code generation, and migrating to templates is a separate effort. This spec explicitly defers template adoption — new pack/unpack and padding logic SHALL use the same direct code generation approach as existing emitters for consistency. Template migration is a separate future initiative.
- **NFR-3: Backward-compatible DSL API.** `Struct().add_member(name, type)` continues to work — padding is implicit, computed at freeze time, not an opt-in flag.
- **NFR-4: Golden-file coverage.** Every new behavior must have at least one test fixture and golden file exercising it, per the project's testing strategy.
- **NFR-5: No external dependencies.** Implementation must use only stdlib + Jinja2 (per Project Constitution constraint 6).
- **NFR-6: basedpyright strict compliance.** All new/modified Python code must pass basedpyright strict mode with zero errors.

## Acceptance Criteria

- **AC-1:** A struct with mixed-width members (1-bit, 13-bit, 4-bit, 1-bit) generates an SV typedef with per-member padding: `flag_a_pad[6:0]`, `field_1_pad[2:0]`, `status_pad[3:0]`, `flag_b_pad[6:0]`.
- **AC-2:** `LP_BAR_WIDTH = 19` (1+13+4+1). `LP_BAR_BYTE_COUNT = 5` (1+2+1+1).
- **AC-3:** `pack_bar({flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0})` returns `19'h1_FFFA`.
- **AC-4:** `unpack_bar(19'h1_FFFA)` returns a `bar_t` with all `_pad` fields set to `0`.
- **AC-5:** `pack_bar(unpack_bar(v)) == v` for any valid 19-bit vector `v`.
- **AC-6:** `to_bytes()` for the example above returns `{0x01, 0x1F, 0xFF, 0x0A, 0x00}` in SV, C++, and Python.
- **AC-7:** Nested structs: if `outer_t` contains `inner_t` (which has `BYTE_COUNT=3`), `outer_t`'s serialization of the `inner` field occupies exactly 3 bytes, matching `inner_t.to_bytes()`.
- **AC-8:** Scalar types emit `LP_FOO_WIDTH = 13`, `LP_FOO_BYTE_COUNT = 2`, and identity `pack_foo`/`unpack_foo` functions.
- **AC-9:** C++ scalar fields use minimum-width native types: 13-bit → `uint16_t`, 1-bit → `uint8_t`, 37-bit → `uint64_t`.
- **AC-10:** All golden tests pass after changes, including updated golden files for existing fixtures.
- **AC-11:** At least one new test fixture exercises a struct with members requiring non-trivial padding.
- **AC-12:** `from_bytes({0x81, 0x1F, 0xFF, 0x0A, 0x00})` (nonzero padding in flag_a byte) produces the same struct as `from_bytes({0x01, 0x1F, 0xFF, 0x0A, 0x00})` — padding bits are ignored.
- **AC-13:** A struct with a field named `foo_pad` is rejected by validation with an appropriate error message.
- **AC-14:** `unpack_bar(pack_bar(s))` preserves all data field values of struct `s` (data round-trip identity).

## Out of Scope

- **Unpacked types.** Per Project Constitution constraint 3, all types are packed.
- **User-specified alignment.** Padding is always to byte (8-bit) boundaries. Custom alignment (e.g., 16-bit, 32-bit) is out of scope.
- **Cross-module type references.** Per Project Constitution constraint 4, struct fields referencing types from other modules are rejected.
- **Arbitrary-width constants.** Per Project Constitution constraint 5, constants are restricted to 32/64 bits.
- **Scalar widths > 64 bits.** Rejected by existing validation. No changes needed.
- **Runtime/build backend changes.** Changes are limited to the sv, cpp, and py emitter backends.
- **Jinja2 template migration.** Deferred per NFR-2.
