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
- **Padding bits**: Byte-alignment bits placed on the MSB side of a field in the packed struct. Count: for scalar-typed fields: `(field_byte_count * 8) - w`. For struct-typed fields: always **0** (the inner struct typedef is already byte-aligned). Fill policy depends on signedness and context: for unsigned scalars, padding is zero-filled; for signed scalars, padding is sign-extended (filled with the field's sign bit) in `unpack`, `to_bytes`, and `to_slv` operations. In the SV `typedef struct packed`, the `_pad` member is a `logic` field whose value is set by operations, not by the typedef itself.
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
- Padding bits are placed on the MSB side of the field in the packed struct. Fill policy is determined by the consuming operation (see Definitions).
- A scalar field whose width is already a multiple of 8 has `padding_bits = 0`.

### FR-2: IR Representation of Padding

`StructFieldIR` SHALL carry a `padding_bits: int` field (frozen, >= 0) representing the number of byte-alignment bits for this member. The fill policy (zero or sign-extended) is determined by the field's signedness and the consuming operation, not stored in IR.

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

**Padding fill semantics:** The `_pad` member in the `typedef struct packed` is a plain `logic` field. Its value is determined by the operation that populates the struct: `unpack` and `to_slv` set it to zero for unsigned fields and to the replicated sign bit for signed fields. The typedef itself does not enforce or constrain the padding value — it is a structural placeholder.

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
    // Initialize result to '0 (unsigned padding starts at 0)
    // Extract data fields from compact vector, LSB first
    // For signed scalar fields: overwrite _pad bits with replicated sign bit (sign extension)
endfunction
```

**pack semantics:** Output vector width = `WIDTH`. Contains only data bits, concatenated MSB-to-LSB in declaration order. For struct-typed fields, recursively call `pack_<inner_base_name>`. For scalar fields, use the field value directly (raw bit pattern, no sign extension).

**unpack semantics:** Input vector width = `WIDTH`. Result is initialized to `'0`. Fields are extracted LSB-first with bit-slice indexing. For struct-typed fields, recursively call `unpack_<inner_base_name>`. For **signed scalar fields with padding_bits > 0**, the corresponding `_pad` field SHALL be set to `{P{field[W-1]}}` (replicate the sign bit), where `P` = padding_bits and `W` = field data width. For **unsigned scalar fields**, padding remains zero.

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

The verification helper class `to_bytes()` task SHALL serialize the full byte-aligned struct (including padding) into a byte array of size `BYTE_COUNT`. Byte order is big-endian (MSB byte first within each field's byte chunk). For **unsigned scalar fields**, padding bits are serialized as zero. For **signed scalar fields**, padding bits are sign-extended (filled with the field's sign bit). `to_bytes()` does NOT read the `_pad` member values from the struct typedef; it computes the byte array from field data values, applying the appropriate padding fill (zero for unsigned, sign-extended for signed).

The `from_bytes()` task SHALL deserialize a byte array of size `BYTE_COUNT` back into the struct type. For **unsigned scalar fields**, padding bits in the input are ignored — any padding value is tolerated. For **signed scalar fields** with `padding_bits > 0`, `from_bytes()` SHALL validate that the padding bits equal the sign extension of the data's sign bit (`{P{data[W-1]}}`); a mismatch SHALL raise an error. Field data values are extracted from the data-bit positions. The SV verification helper class stores only logical field values (not `_pad` members). If the deserialized result is materialized as the SV `typedef struct packed` (e.g., via `to_slv()`), the standard padding fill policy applies: zero for unsigned, sign-extended for signed.

For scalar types, `to_bytes()` serializes the value into `BYTE_COUNT` bytes, big-endian. For **unsigned** scalar types, `from_bytes()` deserializes by extracting only the lower `WIDTH` data bits from the byte array (upper padding bits are masked/ignored). For **signed** scalar types with `padding_bits > 0`, `from_bytes()` SHALL validate that the upper padding bits match the sign extension of the data's sign bit; a mismatch SHALL raise an error.

**Cross-language invariant:** `to_bytes()` output from SV, C++, and Python MUST produce identical byte arrays for the same logical data.

### FR-7: C++ Backend — Native Type Mapping for Scalars

Scalar wrapper classes (`<base_name>_ct`) SHALL use the minimum-width native C++ type for internal storage:
- width 1–8: `std::uint8_t`
- width 9–16: `std::uint16_t`
- width 17–32: `std::uint32_t`
- width 33–64: `std::uint64_t`
- width > 64: `std::vector<std::uint8_t>` (unsigned only; signed > 64 is rejected by FR-13)

Signed scalars (width ≤ 64) use the corresponding signed type (`std::int8_t`, `std::int16_t`, `std::int32_t`, `std::int64_t`).

**Wide scalar storage (> 64 bits):** The `std::vector<std::uint8_t>` stores the value in big-endian byte order with exactly `kByteCount` elements. The wrapper class maintains a **normalized invariant**: the vector always has exactly `kByteCount` elements, and the upper `padding_bits` bits of the MSB byte are always zero. Constructors and setters SHALL enforce this invariant by clearing padding bits on construction. `to_bytes()` returns the internal vector directly (no copy or masking needed — the invariant guarantees padding is zero). `from_bytes()` constructs from the byte vector, masking upper padding bits to enforce the invariant. The wrapper class provides `value_type = std::vector<std::uint8_t>`.

When a scalar alias `foo_t` is used as a struct member in C++, the field type is the generated wrapper class `foo_ct`, not a raw native type. The native type mapping applies to the wrapper class's internal `value_type`.

**Serialization:** `to_bytes()` produces a big-endian byte array of size `kByteCount`. For **unsigned** scalars, padding bits are zero. For **signed** scalars, padding bits are sign-extended (filled with the sign bit). For example, an unsigned 37-bit `foo_ct` with value `0x12_3456_789A` serializes to `{0x12, 0x34, 0x56, 0x78, 0x9A}` (5 bytes, MSB first, upper 3 bits of first byte are zero padding). A signed 4-bit value of -6 (`4'b1010`) serializes to `{0xFA}` (sign-extended padding: `4'b1111`).

**Deserialization:** For **unsigned** scalars, `from_bytes()` extracts only the lower `kWidth` data bits from the byte array; upper padding bits are masked/ignored. For **signed** scalars with `padding_bits > 0`, `from_bytes()` SHALL validate that the upper padding bits match the sign extension of the data's sign bit; a mismatch SHALL throw `std::invalid_argument`. The value is decoded from the two's complement representation of the `kWidth` data bits.

### FR-8: C++ Backend — Struct Padding and Serialization

C++ struct classes SHALL:
- Store `kWidth` (data bits) and `kByteCount` (byte-aligned bytes) as `static constexpr std::size_t`.
- `to_bytes()` serializes the full byte-aligned representation as a big-endian byte vector of size `kByteCount`. Each field is serialized into its individual byte count, concatenated in declaration order. For **unsigned** scalar fields, MSB padding bits are zero. For **signed** scalar fields, MSB padding bits are sign-extended (filled with the field's sign bit).
- `from_bytes()` deserializes from a byte vector of size `kByteCount`. For unsigned scalar fields, padding bits in input are ignored. For signed scalar fields with `padding_bits > 0`, padding bits are validated against the sign extension of the data's sign bit; a mismatch throws `std::invalid_argument`. Field values are extracted from the data bits.
- The byte layout MUST match the SV verification class output exactly.

### FR-9: Python Backend — Struct Padding and Serialization

Python struct dataclasses SHALL:
- Store `WIDTH` (data bits) and `BYTE_COUNT` (byte-aligned bytes) as class variables.
- `to_bytes()` returns a `bytes` object of length `BYTE_COUNT` with the full byte-aligned representation (big-endian). Each field is serialized into its individual byte count, concatenated in declaration order. For **unsigned** scalar fields, padding bits are zero. For **signed** scalar fields, padding bits are sign-extended (filled with the field's sign bit).
- `from_bytes()` accepts `bytes` of length `BYTE_COUNT` and returns the dataclass instance. For unsigned scalar fields, padding bits in input are ignored. For signed scalar fields with `padding_bits > 0`, padding bits are validated against the sign extension of the data's sign bit; a mismatch raises `ValueError`. Field values are extracted from data bits.
- For scalar wrapper classes: for unsigned, `from_bytes()` extracts only the lower `WIDTH` data bits, masking upper padding bits. For signed scalars with `padding_bits > 0`, `from_bytes()` validates that upper padding bits match sign extension; a mismatch raises `ValueError`. The value is decoded from the two's complement representation of the `WIDTH` data bits.
- The byte layout MUST match the SV and C++ output exactly.

### FR-10: Cross-Language Byte-Level Consistency

For any given type and logical data values, all three backends (SV, C++, Python) MUST produce identical `to_bytes()` output. This is the fundamental serialization contract.

Specifically:
1. The same field order (declaration order, MSB first in the byte stream).
2. The same padding placement (MSB side of each member) and fill policy (zero for unsigned scalars, sign-extended for signed scalars).
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

- `to_slv()` SHALL return the padded struct value with `_pad` fields set appropriately: zero for unsigned scalar fields, sign-extended (replicated sign bit) for signed scalar fields. It assembles the typedef from the helper class's field values, filling padding positions based on the field's signedness.
- `from_slv()` SHALL extract field values from the padded struct input, ignoring padding bit values in the input. Padding bits are not stored in the helper class — they exist only in the SV typedef.

These methods are distinct from `pack`/`unpack` (FR-5, which operate on the compact data-width vector) and from `to_bytes`/`from_bytes` (FR-6, which serialize to byte arrays).

### FR-11: Padding Name Collision Validation

The validation layer SHALL reject struct definitions where any field name ends with `_pad`, since the `_pad` suffix is reserved for generated padding members. This validation runs during the existing validation pass in `validate/engine.py`.

Error message: `"struct <struct_name> field '<field_name>' uses reserved '_pad' suffix"`.

### FR-12: Signed Scalars as Struct Members

Signed scalar types used as struct members SHALL be handled consistently:
- **Padding computation:** Same as unsigned — based on bit width, not sign. A signed 8-bit scalar gets 0 padding bits (already byte-aligned).
- **SV `pack`:** Extracts the raw bit pattern. The sign bit is part of the data bits. No sign extension — the output is a compact `WIDTH`-bit vector.
- **SV `unpack`:** For signed scalar fields with `padding_bits > 0`, the `_pad` field SHALL be set to `{P{sign_bit}}` — the sign bit of the data value replicated across all padding bits (sign extension). This ensures the byte-aligned struct representation is directly interpretable as a native signed integer. For fields already byte-aligned (`padding_bits == 0`), no padding exists and no sign extension is needed.
- **`to_bytes` serialization:** Signed scalar fields are serialized with sign-extended padding. The field's data bits plus sign-extended padding bits form a byte-aligned value that is directly interpretable as the corresponding native signed type (`std::int8_t`, `std::int16_t`, etc.). Big-endian byte order.
- **`from_bytes` deserialization:** For signed scalar fields with `padding_bits > 0`, `from_bytes()` SHALL validate that the padding bits in the input match the sign extension of the data's sign bit. If the padding bits do not equal `{P{data[W-1]}}`, `from_bytes()` SHALL raise an error. This detects data corruption where the byte representation is inconsistent with a valid signed value. For signed fields with `padding_bits == 0`, no validation is needed.
- **C++ type mapping:** Uses signed native types per FR-7 (`std::int8_t`, etc.). The sign-extended byte representation maps directly to these types.

**Worked example:** 4-bit signed field `field_1 = 4'b1010` (-6):
- `pack`: extracts `4'b1010` (raw bit pattern)
- `unpack`: `field_1_pad = 4'b1111` (sign bit 1, replicated), `field_1 = 4'b1010`
- `to_bytes`: byte = `8'b1111_1010` = `0xFA` = -6 as `std::int8_t`
- `from_bytes({0xFA})`: padding = `4'b1111`, sign bit = 1, match ✓ → extracts `4'b1010` = -6
- `from_bytes({0x0A})`: padding = `4'b0000`, sign bit = 1, **mismatch → error**

### FR-13: Signed Scalar Width Constraint

**Unsigned** scalar types of any width are supported. For widths > 64, the C++ backend uses `std::vector<std::uint8_t>` as the underlying storage type (see FR-7).

**Signed** scalar types with width > 64 bits are rejected by validation, because there is no practical native C++ signed integer type beyond 64 bits and sign extension semantics for `std::vector<std::uint8_t>` would add unwarranted complexity.

This applies to both:
- **Named signed scalar type aliases** (e.g., `wide_t = LogicSigned(65)`): Error message: `"signed scalar <type_name> width <w> exceeds maximum 64-bit signed width"`.
- **Inline signed anonymous scalars in struct fields** (e.g., `Struct().add_member("field", LogicSigned(65))`): Error message: `"struct <struct_name> signed field '<field_name>' width <w> exceeds maximum 64-bit signed width"`.

Unsigned scalars of any width (including > 64) pass validation. This is a new validation rule.

### FR-14: Generated Identifier Collision Validation

The validation layer SHALL reject modules where user-defined constant names collide with generated localparam or function names. For each type `<name>` (base name `<base>`) in a module, the following identifiers are reserved:
- `LP_<UPPER_BASE>_WIDTH`
- `LP_<UPPER_BASE>_BYTE_COUNT`
- `pack_<base>`
- `unpack_<base>`

If any user-defined constant in the same module has a name (after SV name transformation) that matches a reserved generated identifier, validation SHALL reject with error: `"constant '<const_name>' collides with generated identifier for type '<type_name>'"`.

## Non-Functional Requirements

- **NFR-1: Deterministic output.** Generated code must be byte-for-byte reproducible (per Project Constitution principle 3).
- **NFR-2: Template migration deferred (explicit exception to Constitution principle 5).** The Project Constitution prefers Jinja2 templates for structured output. However, all existing emitters use direct Python code generation, and migrating to templates is a separate effort. This spec grants an explicit exception: new pack/unpack and padding logic SHALL use the same direct code generation approach as existing emitters for consistency. Rationale: introducing templates for a subset of emitter output while the rest uses direct generation would create inconsistency. Template migration for the full emitter pipeline is a separate future initiative.
- **NFR-3: Backward-compatible DSL API.** `Struct().add_member(name, type)` continues to work — padding is implicit, computed at freeze time, not an opt-in flag.
- **NFR-4: Test coverage.** Every new code generation behavior must have at least one test fixture and golden file exercising it, per the project's testing strategy. Validation-only behaviors (FR-11, FR-14) are tested via negative test cases that verify specific error messages and non-zero exit codes, per the project's existing negative test pattern. FR-13 has both a validation component (signed >64 rejected) tested via negative tests, and a code generation component (unsigned >64 accepted) requiring positive golden coverage.
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
- **AC-9:** C++ scalar wrapper classes use minimum-width native types: 13-bit → `uint16_t`, 1-bit → `uint8_t`, 37-bit → `uint64_t`, 128-bit unsigned → `std::vector<std::uint8_t>`.
- **AC-10:** All golden tests pass after changes, including updated golden files for existing fixtures.
- **AC-11:** At least one new test fixture exercises a struct with members requiring non-trivial padding.
- **AC-12:** `from_bytes({0x81, 0x1F, 0xFF, 0x0A, 0x00})` (nonzero padding in unsigned flag_a byte) produces the same struct as `from_bytes({0x01, 0x1F, 0xFF, 0x0A, 0x00})` — unsigned padding bits are ignored on deserialization.
- **AC-13:** A struct with a field named `foo_pad` is rejected by validation with error message containing `"reserved '_pad' suffix"`.
- **AC-14:** `unpack_bar(pack_bar(s))` preserves all data field values of struct `s` (data round-trip identity).
- **AC-15:** Scalar `from_bytes()` for a 13-bit type: `from_bytes({0xFF, 0xFF})` extracts only the lower 13 bits, producing value `0x1FFF` (upper 3 padding bits masked off). This behavior is identical across SV, C++, and Python.
- **AC-16:** A signed 5-bit scalar with value `-1` (two's complement `5'b11111`): `to_bytes()` = `{0xFF}` (1 byte, upper 3 padding bits sign-extended to 1). `from_bytes({0xFF})` validates padding (`3'b111` matches sign bit 1) and decodes as `-1`. A signed 5-bit scalar with value `+5` (`5'b00101`): `to_bytes()` = `{0x05}` (padding bits sign-extended to 0, same as zero-fill). `from_bytes({0x05})` validates padding (`3'b000` matches sign bit 0) and decodes as `+5`.
- **AC-17:** A named **unsigned** scalar type `Logic(128)` passes validation. A named **signed** scalar type `LogicSigned(65)` is rejected by validation with error message containing `"exceeds maximum 64-bit signed width"`.
- **AC-18:** An inline **signed** anonymous scalar `Struct().add_member("field", LogicSigned(65))` is rejected by validation with error message containing `"exceeds maximum 64-bit signed width"`. An inline unsigned `Struct().add_member("field", Logic(128))` passes validation.
- **AC-19:** SV `to_slv()` on a struct with unsigned `_pad` fields returns a value with those padding bits = 0. For signed fields, `to_slv()` returns padding bits sign-extended (replicated sign bit). `from_slv()` with arbitrary padding bit values produces the same field values as `from_slv()` with correctly-filled padding.
- **AC-20:** A module defining both `LP_FOO_WIDTH = Const(42)` and `foo_t = Logic(13)` is rejected by validation with error message containing `"collides with generated identifier"`.
- **AC-21:** A struct with a 4-bit signed scalar member `field_s` having value `-6` (`4'b1010`): `unpack` produces `field_s_pad = 4'b1111` (sign bit replicated) and `field_s = 4'b1010`. For a positive value `+3` (`4'b0011`): `unpack` produces `field_s_pad = 4'b0000` and `field_s = 4'b0011`.
- **AC-22:** A struct with a 4-bit signed scalar member `field_s = -6`: `to_bytes()` serializes the field's byte as `0xFA` (sign-extended) in SV, C++, and Python — all three backends produce identical output.
- **AC-23:** `from_bytes({0x0A})` for a 4-bit signed scalar (data = `4'b1010`, sign bit = 1, padding = `4'b0000` instead of expected `4'b1111`) raises an error in all three backends. `from_bytes({0x1F})` for a signed 5-bit scalar with value -1 (`0x1F` has padding `3'b000` but sign bit = 1) also raises an error.
- **AC-24:** A 65-bit unsigned scalar `wide_t` with value `0x1_FFFF_FFFF_FFFF_FFFF` (all 65 data bits set): `to_bytes()` = `{0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}` (9 bytes, upper 7 padding bits zero). `from_bytes()` of the same 9 bytes returns the same value. `from_bytes({0xFF, 0xFF, ...9 bytes all 0xFF...})` masks the upper 7 padding bits, yielding value `0x1_FFFF_FFFF_FFFF_FFFF`. Round-trip identity holds. Identical output across SV, C++, and Python. C++ wrapper uses `std::vector<std::uint8_t>` as `value_type`.
- **AC-25:** A struct containing a 65-bit unsigned scalar member `data` and a 1-bit `valid` flag: `to_bytes()` concatenates `data.to_bytes()` (9 bytes) + `valid.to_bytes()` (1 byte) = 10 bytes total. Same output across all three backends.

## Out of Scope

- **Unpacked types.** Per Project Constitution constraint 3, all types are packed.
- **User-specified alignment.** Padding is always to byte (8-bit) boundaries. Custom alignment (e.g., 16-bit, 32-bit) is out of scope.
- **Cross-module type references.** Per Project Constitution constraint 4, struct fields referencing types from other modules are rejected.
- **Arbitrary-width constants.** Per Project Constitution constraint 5, constants are restricted to 32/64 bits.
- **Signed scalar widths > 64 bits.** Rejected by validation (FR-13). Unsigned scalars of any width are supported.
- **Jinja2 template migration.** Deferred per NFR-2.

## Changelog

- [Clarification iter1] FR-5: `unpack` now sign-extends `_pad` bits for signed scalar fields instead of zero-filling
- [Clarification iter1] FR-6: `to_bytes` now serializes signed scalar fields with sign-extended padding instead of zero padding
- [Clarification iter1] FR-10a: `to_slv` now uses sign-extended padding for signed scalar fields
- [Clarification iter1] FR-12: Rewrote signed scalar handling to specify sign extension in `unpack` and `to_bytes`, while `pack` remains raw bit extraction
- [Clarification iter1] AC-16: Updated expected `to_bytes()` for signed -1 from `{0x1F}` to `{0xFF}` (sign-extended padding)
- [Clarification iter1] AC-19: Updated to reflect sign-extended padding for signed fields in `to_slv()`
- [Clarification iter2] Definitions: Redefined "padding bits" from "zero-fill" to signedness-dependent fill policy
- [Clarification iter2] FR-1: Updated padding description to reference fill policy from Definitions
- [Clarification iter2] FR-2: Clarified padding count in IR vs fill policy in consuming operations
- [Clarification iter2] FR-3: Added "Padding fill semantics" paragraph explaining `_pad` value set by operations
- [Clarification iter2] FR-6: Clarified `from_bytes()` stores only logical field values, not `_pad` members
- [Clarification iter2] FR-7: Added signed scalar serialization example with sign-extended padding
- [Clarification iter2] FR-8: Updated C++ struct `to_bytes()` to specify sign-extended padding for signed fields
- [Clarification iter2] FR-9: Updated Python struct `to_bytes()` to specify sign-extended padding for signed fields
- [Clarification iter2] FR-10: Updated item 2 from "zero-filled" to signedness-dependent fill policy
- [Clarification iter2] AC-21: Added — verifies `unpack` sign-extends `_pad` for signed struct member
- [Clarification iter2] AC-22: Added — verifies cross-language `to_bytes()` for signed struct member
- [Clarification delta1] FR-6: `from_bytes()` for signed fields now validates sign-extended padding; mismatch raises error
- [Clarification delta1] FR-7: C++ scalar `from_bytes()` for signed scalars validates padding, throws `std::invalid_argument`
- [Clarification delta1] FR-8: C++ struct `from_bytes()` validates signed field padding
- [Clarification delta1] FR-9: Python `from_bytes()` for signed fields validates padding, raises `ValueError`
- [Clarification delta1] FR-12: `from_bytes({0x0A})` example changed from "padding ignored" to "error"
- [Clarification delta1] AC-16: Updated `from_bytes` examples to show validation passing
- [Clarification delta1] AC-23: Added — `from_bytes` with mismatched signed padding raises error
- [Clarification delta2] AC-12: Added "unsigned" qualifier to clarify padding-ignored applies only to unsigned fields
- [Clarification delta3] FR-13: Changed from "reject all >64-bit" to "reject only signed >64-bit"; unsigned scalars of any width now supported
- [Clarification delta3] FR-7: Added width >64 row using `std::vector<std::uint8_t>` (unsigned only) with wide scalar storage description
- [Clarification delta3] AC-9: Added 128-bit unsigned example
- [Clarification delta3] AC-17: Changed from "Logic(65) rejected" to "Logic(128) passes; LogicSigned(65) rejected"
- [Clarification delta3] AC-18: Changed from "Logic(65) inline rejected" to "LogicSigned(65) inline rejected; Logic(128) inline passes"
- [Clarification delta3] Out of Scope: Changed ">64-bit scalars rejected" to "signed >64-bit rejected; unsigned any width supported"
- [Clarification delta4] NFR-4: Removed FR-13 from validation-only list; now has both validation and code-gen components
- [Clarification delta4] FR-7: Added normalized invariant for wide scalar wrapper (padding bits cleared on construction)
- [Clarification delta4] AC-24: Added — 65-bit unsigned scalar round-trip through `to_bytes`/`from_bytes` across all backends
- [Clarification delta4] AC-25: Added — struct containing 65-bit unsigned member serialization
