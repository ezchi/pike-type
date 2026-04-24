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
- **Field byte count**: For a scalar-typed field of width `w`: `ceil(w / 8)`. For a struct-typed field: the inner struct's `BYTE_COUNT`.
- **Padding bits**: Zero-fill bits placed on the MSB side of a field in the packed struct. For scalar-typed fields: `(field_byte_count * 8) - w`. For struct-typed fields: always **0** (the inner struct typedef is already byte-aligned, so no additional padding is emitted).
- **Type base name**: The type name with one trailing `_t` suffix stripped. All type names are required to end in `_t` per the Project Constitution naming convention. `foo_t` → `foo`. `bar_t` → `bar`. Used for localparam names (`LP_FOO_WIDTH`) and function names (`pack_foo`).

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
- For a struct-typed field: `padding_bits = 0`. The inner struct's typedef is already byte-aligned (its total bit width equals `BYTE_COUNT * 8`), so no additional padding is emitted in the outer struct.
- Padding bits are zero-fill bits placed on the MSB side of the field in the packed struct.
- A scalar field whose width is already a multiple of 8 has `padding_bits = 0`.

### FR-2: IR Representation of Padding

`StructFieldIR` SHALL carry a `padding_bits: int` field (frozen, >= 0) representing the number of zero-fill bits added to byte-align this member.

Derived quantities (NOT stored in IR — computed by backends):
- `WIDTH` = sum of all field data widths. For scalar fields: `resolved_width`. For struct-typed fields: the inner struct's `WIDTH`.
- `BYTE_COUNT` = sum of each field's individual byte count. For scalar fields: `ceil(resolved_width / 8)`. For struct-typed fields: the inner struct's `BYTE_COUNT`.

### FR-3: SystemVerilog Synthesizable Package — Struct Typedef

The SV `typedef struct packed` SHALL include explicit padding members for scalar fields that require padding.

For each field with `padding_bits > 0`:
- Emit `logic [P-1:0] <field_name>_pad;` immediately above (MSB side of) the field, where `P = padding_bits`.
- For 1-bit padding, emit `logic <field_name>_pad;`.

Fields with `padding_bits == 0` (including all struct-typed fields) have no padding member emitted.

**Padding member naming:** `<field_name>_pad`. The `_pad` suffix is reserved. See FR-11 for collision validation.

**Example** (for `bar_t` with fields: flag_a=1-bit, field_1=13-bit foo_t scalar, status=4-bit, flag_b=1-bit):
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

**Nested struct example** (for `outer_t` containing `inner_t` where `inner_t` has BYTE_COUNT=2):
```systemverilog
typedef struct packed {
   inner_t     payload;    // no padding — inner_t is already byte-aligned (16 bits = 2 bytes)
   logic [6:0] tag_pad;
   logic       tag;        // 1-bit, padded to 8 bits
} outer_t;
```

### FR-4: SystemVerilog Synthesizable Package — Width and Byte Count Localparams

For every type (scalar or struct), emit in the synthesizable package:
```systemverilog
localparam int LP_<UPPER_BASE_NAME>_WIDTH = <width>;
localparam int LP_<UPPER_BASE_NAME>_BYTE_COUNT = <byte_count>;
```

Where `<UPPER_BASE_NAME>` is the type base name (one trailing `_t` stripped) in UPPER_SNAKE_CASE.

For scalar types, the typedef SHALL reference the width localparam. The existing `bit` vs `logic` and `signed` qualifiers SHALL be preserved:
```systemverilog
// unsigned logic scalar
typedef logic [LP_FOO_WIDTH-1:0] foo_t;

// signed logic scalar
typedef logic signed [LP_MASK_WIDTH-1:0] mask_t;

// bit scalar
typedef bit [LP_FLAG_WIDTH-1:0] flag_t;
```

**Semantics:**
- `WIDTH` = total data bits (excludes padding).
- `BYTE_COUNT` = total bytes in byte-aligned representation (includes padding). For scalars: `ceil(WIDTH / 8)`.

**Examples:**
- `foo_t` (Logic(13)): `LP_FOO_WIDTH = 13`, `LP_FOO_BYTE_COUNT = 2`
- `bar_t` (struct: flag_a=1, field_1=13, status=4, flag_b=1): `LP_BAR_WIDTH = 19`, `LP_BAR_BYTE_COUNT = 5`
- `outer_t` (struct: payload=inner_t with WIDTH=6/BYTE_COUNT=2, tag=1): `LP_OUTER_WIDTH = 7` (6+1), `LP_OUTER_BYTE_COUNT = 3` (2+1)

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

**Worked example** for `bar_t` with `flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0`:

`pack_bar(a)` = `{a.flag_a, pack_foo(a.field_1), a.status, a.flag_b}`
= `{1'b1, 13'h1FFF, 4'hA, 1'b0}`
= `19'h7_FFF4`

Bit layout (MSB to LSB):
```
bit 18:    flag_a  = 1
bit 17–5:  field_1 = 1_1111_1111_1111
bit 4–1:   status  = 1010
bit 0:     flag_b  = 0
```
Binary: `1_1111_1111_1111_1010_0` = `19'h7FFF4`

### FR-6: SystemVerilog Verification Package — to_bytes / from_bytes

The verification helper class `to_bytes()` task SHALL serialize the full byte-aligned struct (including padding) into a byte array of size `BYTE_COUNT`. Byte order is big-endian (MSB byte first within each field's byte chunk). Padding bits are always serialized as zero — `to_bytes()` does NOT read the `_pad` member values from the struct typedef; it computes the byte array from field data values and fills padding positions with zero.

The `from_bytes()` task SHALL deserialize a byte array of size `BYTE_COUNT` back into the struct type. Padding bits in the input byte array are ignored — the deserialized struct will have all padding bits set to zero regardless of input padding values.

For scalar types, `to_bytes()` serializes the value into `BYTE_COUNT` bytes, big-endian. `from_bytes()` deserializes by extracting only the lower `WIDTH` data bits from the byte array (upper padding bits are masked/ignored).

**Cross-language invariant:** `to_bytes()` output from SV, C++, and Python MUST produce identical byte arrays for the same logical data.

### FR-7: C++ Backend — Native Type Mapping for Scalars

Scalar wrapper classes (`<base_name>_ct`) SHALL use the minimum-width native C++ type for internal storage:
- width 1–8: `std::uint8_t`
- width 9–16: `std::uint16_t`
- width 17–32: `std::uint32_t`
- width 33–64: `std::uint64_t`

Signed scalars use the corresponding signed type (`std::int8_t`, `std::int16_t`, `std::int32_t`, `std::int64_t`).

When a scalar alias `foo_t` is used as a struct member in C++, the field type is the generated wrapper class `foo_ct`, not a raw native type. The native type mapping applies to the wrapper class's internal `value_type`.

**Serialization:** `to_bytes()` produces a big-endian byte array of size `kByteCount`. For example, a 37-bit `foo_ct` with value `0x12_3456_789A` serializes to `{0x12, 0x34, 0x56, 0x78, 0x9A}` (5 bytes, MSB first, upper 3 bits of first byte are zero padding).

**Deserialization:** `from_bytes()` extracts only the lower `kWidth` data bits from the byte array. Upper padding bits in the input are masked/ignored. For signed scalars, the value is decoded from the two's complement representation of the `kWidth` data bits (not the full byte array).

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
- For scalar wrapper classes: `from_bytes()` extracts only the lower `WIDTH` data bits, masking upper padding bits. For signed scalars, the value is decoded from the two's complement representation of the `WIDTH` data bits.
- The byte layout MUST match the SV and C++ output exactly.

### FR-10: Cross-Language Byte-Level Consistency

For any given type and logical data values, all three backends (SV, C++, Python) MUST produce identical `to_bytes()` output. This is the fundamental serialization contract.

Specifically:
1. The same field order (declaration order, MSB first in the byte stream).
2. The same padding placement (MSB side of each member, zero-filled).
3. The same total byte count.
4. Big-endian byte order within each field's byte chunk.

**Worked example** for `bar_t` with `flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0`:

| Field    | Data width | Byte count | Data value | Padded byte(s) (hex)  |
|----------|------------|------------|------------|-----------------------|
| flag_a   | 1          | 1          | 1          | `0x01`                |
| field_1  | 13         | 2          | 0x1FFF     | `0x1F`, `0xFF`        |
| status   | 4          | 1          | 0xA        | `0x0A`                |
| flag_b   | 1          | 1          | 0          | `0x00`                |

`to_bytes()` = `{0x01, 0x1F, 0xFF, 0x0A, 0x00}` (5 bytes total).

**Nested struct worked example** — `outer_t` contains `inner_t` (WIDTH=6, BYTE_COUNT=2) and `tag` (1-bit scalar):

Assume `inner_t` has fields `x=1` (1-bit, byte_count=1) and `y=0x1F` (5-bit, byte_count=1).
- `inner_t.to_bytes()` = `{0x01, 0x1F}` (2 bytes)
- `tag = 1`
- `outer_t.to_bytes()` = `{0x01, 0x1F, 0x01}` (3 bytes: inner's 2 bytes + tag's 1 byte)
- `pack_outer(a)` = `{pack_inner(a.payload), a.tag}` = `{6'h3F, 1'b1}` = `7'h7F`

### FR-10a: SystemVerilog Verification Package — to_slv / from_slv

The existing `to_slv()` and `from_slv()` methods in the SV verification helper class operate on the full padded struct typedef (storage width). With byte-aligned padding:

- `to_slv()` SHALL return the padded struct value with all `_pad` fields set to zero. It assembles the typedef from the helper class's field values, zero-filling padding positions.
- `from_slv()` SHALL extract field values from the padded struct input, ignoring padding bit values in the input. Padding bits are not stored in the helper class — they exist only in the SV typedef.

These methods are distinct from `pack`/`unpack` (FR-5, which operate on the compact data-width vector) and from `to_bytes`/`from_bytes` (FR-6, which serialize to byte arrays).

### FR-11: Padding Name Collision Validation

The validation layer SHALL reject struct definitions where any field name ends with `_pad`, since the `_pad` suffix is reserved for generated padding members. This validation runs during the existing validation pass in `validate/engine.py`.

Error message: `"struct <struct_name> field '<field_name>' uses reserved '_pad' suffix"`.

### FR-12: Signed Scalars as Struct Members

Signed scalar types used as struct members SHALL be handled consistently:
- **Padding:** Computed the same as unsigned — based on bit width, not sign. A signed 8-bit scalar gets 0 padding bits (already byte-aligned).
- **SV pack/unpack:** The sign bit is part of the data bits. `pack` extracts the raw bit pattern; `unpack` restores it. No sign extension occurs during pack/unpack.
- **to_bytes serialization:** The field's raw bit pattern (two's complement) is serialized into its byte count, big-endian, same as unsigned. The sign is encoded in the MSB of the data bits.
- **C++ type mapping:** Uses signed native types per FR-7 (`std::int8_t`, etc.).

### FR-13: Scalar Width Constraint

Scalar types with width > 64 bits have no native C++ type mapping. Since the code generation pipeline always emits all three backends (SV, C++, Python) with no backend selector, the validation layer SHALL reject scalar widths > 64 unconditionally.

This applies to both:
- **Named scalar type aliases** (e.g., `wide_t = Logic(65)`): Error message: `"scalar <type_name> width <w> exceeds maximum 64-bit width"`.
- **Inline anonymous scalars in struct fields** (e.g., `Struct().add_member("field", Logic(65))`): Error message: `"struct <struct_name> field '<field_name>' width <w> exceeds maximum 64-bit width"`.

This is a new validation rule. The existing codebase does not reject >64-bit scalars.

## Non-Functional Requirements

- **NFR-1: Deterministic output.** Generated code must be byte-for-byte reproducible (per Project Constitution principle 3).
- **NFR-2: Template migration deferred (explicit exception to Constitution principle 5).** The Project Constitution prefers Jinja2 templates for structured output. However, all existing emitters use direct Python code generation, and migrating to templates is a separate effort. This spec grants an explicit exception: new pack/unpack and padding logic SHALL use the same direct code generation approach as existing emitters for consistency. Rationale: introducing templates for a subset of emitter output while the rest uses direct generation would create inconsistency. Template migration for the full emitter pipeline is a separate future initiative.
- **NFR-3: Backward-compatible DSL API.** `Struct().add_member(name, type)` continues to work — padding is implicit, computed at freeze time, not an opt-in flag.
- **NFR-4: Golden-file coverage.** Every new behavior must have at least one test fixture and golden file exercising it, per the project's testing strategy.
- **NFR-5: No external dependencies.** Implementation must use only stdlib + Jinja2 (per Project Constitution constraint 6).
- **NFR-6: basedpyright strict compliance.** All new/modified Python code must pass basedpyright strict mode with zero errors.

## Acceptance Criteria

- **AC-1:** A struct with mixed-width members (1-bit, 13-bit, 4-bit, 1-bit) generates an SV typedef with per-member padding: `flag_a_pad[6:0]`, `field_1_pad[2:0]`, `status_pad[3:0]`, `flag_b_pad[6:0]`.
- **AC-2:** `LP_BAR_WIDTH = 19` (1+13+4+1). `LP_BAR_BYTE_COUNT = 5` (1+2+1+1).
- **AC-3:** `pack_bar({flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0})` returns `19'h7FFF4`.
- **AC-4:** `unpack_bar(19'h7FFF4)` returns a `bar_t` with `flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0` and all `_pad` fields = `0`.
- **AC-5:** `pack_bar(unpack_bar(v)) == v` for any valid 19-bit vector `v`.
- **AC-6:** `to_bytes()` for the example above returns `{0x01, 0x1F, 0xFF, 0x0A, 0x00}` in SV, C++, and Python.
- **AC-7:** Nested struct `outer_t` containing `inner_t` (BYTE_COUNT=2, WIDTH=6) and `tag` (1-bit): `LP_OUTER_WIDTH = 7`, `LP_OUTER_BYTE_COUNT = 3`. No `payload_pad` emitted in SV typedef. `outer_t.to_bytes()` = `{inner.to_bytes()[0], inner.to_bytes()[1], 0x01}` (3 bytes).
- **AC-8:** Scalar types emit `LP_FOO_WIDTH = 13`, `LP_FOO_BYTE_COUNT = 2`, and identity `pack_foo`/`unpack_foo` functions.
- **AC-9:** C++ scalar wrapper classes use minimum-width native types: 13-bit → `uint16_t`, 1-bit → `uint8_t`, 37-bit → `uint64_t`.
- **AC-10:** All golden tests pass after changes, including updated golden files for existing fixtures.
- **AC-11:** At least one new test fixture exercises a struct with members requiring non-trivial padding.
- **AC-12:** `from_bytes({0x81, 0x1F, 0xFF, 0x0A, 0x00})` (nonzero padding in flag_a byte) produces the same struct as `from_bytes({0x01, 0x1F, 0xFF, 0x0A, 0x00})` — padding bits are ignored on deserialization.
- **AC-13:** A struct with a field named `foo_pad` is rejected by validation with error message containing `"reserved '_pad' suffix"`.
- **AC-14:** `unpack_bar(pack_bar(s))` preserves all data field values of struct `s` (data round-trip identity).
- **AC-15:** Scalar `from_bytes()` for a 13-bit type: `from_bytes({0xFF, 0xFF})` extracts only the lower 13 bits, producing value `0x1FFF` (upper 3 padding bits masked off). This behavior is identical across SV, C++, and Python.
- **AC-16:** A signed 5-bit scalar with value `-1` (two's complement `5'b11111`): `to_bytes()` = `{0x1F}` (1 byte, upper 3 padding bits zero). `from_bytes({0xFF})` masks to 5 bits and decodes as `-1`.
- **AC-17:** A scalar type defined as `Logic(65)` is rejected by validation with error message containing `"exceeds maximum 64-bit width"`.

## Out of Scope

- **Unpacked types.** Per Project Constitution constraint 3, all types are packed.
- **User-specified alignment.** Padding is always to byte (8-bit) boundaries. Custom alignment (e.g., 16-bit, 32-bit) is out of scope.
- **Cross-module type references.** Per Project Constitution constraint 4, struct fields referencing types from other modules are rejected.
- **Arbitrary-width constants.** Per Project Constitution constraint 5, constants are restricted to 32/64 bits.
- **Scalar widths > 64 bits.** Rejected unconditionally by new validation (FR-13). Existing >64-bit code paths in emitters are not modified or removed — they become dead code guarded by the new validation gate.
- **Jinja2 template migration.** Deferred per NFR-2.
