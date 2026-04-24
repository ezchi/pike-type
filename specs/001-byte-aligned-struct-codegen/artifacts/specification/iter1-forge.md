# Specification: Byte-Aligned Packed Struct Code Generation

**Spec ID:** 001-byte-aligned-struct-codegen  
**Status:** Draft  
**Date:** 2026-04-24  

## Overview

Introduce per-member byte-aligned padding for packed structs across all code generation backends (SystemVerilog, C++, Python). Each struct member is individually padded to byte boundaries in the struct typedef, while pack/unpack functions strip/restore padding to enable compact wire-level serialization. This changes the fundamental struct layout model from tightly packed to byte-aligned-per-member.

## User Stories

- **US-1:** As an RTL designer, I want each struct member individually padded to byte alignment in the `typedef struct packed`, so that byte-addressed memory-mapped registers have naturally aligned fields.
- **US-2:** As an RTL designer, I want standalone `pack_<type>` and `unpack_<type>` functions in the synthesizable SV package, so that I can convert between the padded struct representation and a compact bit vector for wire-level transport.
- **US-3:** As a verification engineer, I want `to_bytes()` and `from_bytes()` in the SV helper class to serialize/deserialize the full byte-aligned representation (including padding), so that byte arrays match the memory-mapped register layout.
- **US-4:** As a firmware developer, I want the C++ generated struct to use minimum-width native types for scalar fields (uint8_t, uint16_t, uint32_t, uint64_t), and `to_bytes()` to produce big-endian byte arrays identical in layout to the SV verification class output.
- **US-5:** As a firmware developer, I want the Python generated struct to produce identical `to_bytes()` output as the SV and C++ backends, so that cross-language serialization is byte-for-byte consistent.

## Functional Requirements

### FR-1: Per-Member Byte-Aligned Padding in DSL

The `Struct().add_member()` DSL method SHALL automatically compute padding bits needed to round each member up to byte alignment. Padding metadata is recorded per-member and propagated through the freeze pipeline to IR.

**Details:**
- A member of width `w` receives `(ceil(w/8) * 8) - w` padding bits.
- Padding bits are conceptually placed above (MSB side of) the member data bits in the packed struct.
- Scalar types (non-struct) are padded individually.
- Struct-typed members are padded based on the struct's total byte-aligned size (its `BYTE_COUNT * 8`), not its `WIDTH`.

### FR-2: IR Representation of Padding

`StructFieldIR` SHALL carry a `padding_bits: int` field (frozen, >= 0) representing the number of zero-fill bits added to byte-align this member.

`StructIR` does NOT store total width/byte_count — these are derived:
- `WIDTH` = sum of all field `resolved_width` values (data bits only, no padding).
- `BYTE_COUNT` = sum of `ceil(field.resolved_width / 8)` for each field (i.e., sum of per-member byte-aligned sizes).

### FR-3: SystemVerilog Synthesizable Package — Struct Typedef

The SV `typedef struct packed` SHALL include explicit padding members.

For each field with `padding_bits > 0`:
- Emit `logic [P-1:0] <field_name>_pad;` immediately above the field, where `P = padding_bits`.
- For 1-bit padding, emit `logic <field_name>_pad;`.

Fields with `padding_bits == 0` have no padding member.

**Example:**
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
localparam int LP_<UPPER_NAME>_WIDTH = <width>;
localparam int LP_<UPPER_NAME>_BYTE_COUNT = <byte_count>;
```

For scalar types: `typedef logic [LP_<UPPER_NAME>_WIDTH-1:0] <name>;`

**Semantics:**
- `WIDTH` = total data bits (excludes padding).
- `BYTE_COUNT` = total bytes when each member is byte-aligned (includes padding). For scalars: `ceil(WIDTH / 8)`.

### FR-5: SystemVerilog Synthesizable Package — pack/unpack Functions

For every type, emit standalone functions in the synthesizable package:

```systemverilog
function logic [LP_<UPPER_NAME>_WIDTH-1:0] pack_<name>(<name> a);
    // Concatenate only data fields (no padding), MSB first
endfunction

function <name> unpack_<name>(logic [LP_<UPPER_NAME>_WIDTH-1:0] a);
    // Initialize result to '0 (all padding = 0)
    // Extract data fields from compact vector, LSB first
endfunction
```

**pack semantics:** Output vector width = `WIDTH`. Contains only data bits, concatenated MSB-to-LSB in declaration order. For struct-typed fields, recursively call `pack_<field_type>`.

**unpack semantics:** Input vector width = `WIDTH`. Result is initialized to `'0` to zero-fill all padding. Fields are extracted LSB-first with bit-slice indexing. For struct-typed fields, recursively call `unpack_<field_type>`.

For scalar types, pack/unpack are identity functions (pass-through).

### FR-6: SystemVerilog Verification Package — to_bytes / from_bytes

The verification helper class `to_bytes()` task SHALL serialize the full byte-aligned struct (including padding) into a byte array of size `BYTE_COUNT`. Byte order is big-endian (MSB byte first).

The `from_bytes()` task SHALL deserialize a byte array of size `BYTE_COUNT` back into the struct type.

**Cross-language invariant:** `to_bytes()` output from SV, C++, and Python MUST produce identical byte arrays for the same logical data.

### FR-7: C++ Backend — Native Type Mapping for Scalars

Scalar types with width <= 64 bits SHALL be mapped to the minimum-width native C++ unsigned type:
- width 1–8: `std::uint8_t`
- width 9–16: `std::uint16_t`
- width 17–32: `std::uint32_t`
- width 33–64: `std::uint64_t`

Signed scalars use the corresponding signed type (`std::int8_t`, etc.).

**Serialization:** `to_bytes()` produces a big-endian byte array of size `BYTE_COUNT`. For example, a 37-bit value `0x12_3456_789A` serializes to `{0x12, 0x34, 0x56, 0x78, 0x9A}` (5 bytes, MSB first).

### FR-8: C++ Backend — Struct Padding and Serialization

C++ struct classes SHALL:
- Store `kWidth` (data bits) and `kByteCount` (byte-aligned bytes) as `static constexpr std::size_t`.
- `to_bytes()` serializes the full byte-aligned representation (with padding zeros) as a big-endian byte vector of size `kByteCount`.
- `from_bytes()` deserializes from a byte vector of size `kByteCount`.
- The byte layout MUST match the SV verification class output exactly.

### FR-9: Python Backend — Struct Padding and Serialization

Python struct dataclasses SHALL:
- Store `WIDTH` (data bits) and `BYTE_COUNT` (byte-aligned bytes) as class variables.
- `to_bytes()` returns a `bytes` object of length `BYTE_COUNT` with the full byte-aligned representation (big-endian, padding zeros included).
- `from_bytes()` accepts `bytes` of length `BYTE_COUNT` and returns the dataclass instance.
- The byte layout MUST match the SV and C++ output exactly.

### FR-10: Cross-Language Byte-Level Consistency

For any given type and logical data values, all three backends (SV, C++, Python) MUST produce identical `to_bytes()` output. This is the fundamental serialization contract.

Specifically:
1. The same field order (declaration order, MSB first in the byte stream).
2. The same padding placement (MSB side of each member).
3. The same total byte count.
4. Big-endian byte order throughout.

## Non-Functional Requirements

- **NFR-1: Deterministic output.** Generated code must be byte-for-byte reproducible (per Project Constitution principle 3).
- **NFR-2: Template-first generation.** New struct rendering logic should use Jinja2 templates where the output has meaningful structure (per Project Constitution principle 5). Existing direct code generation may remain for this iteration but templates are preferred for new pack/unpack and padding logic.
- **NFR-3: Backward-compatible DSL API.** `Struct().add_member(name, type)` continues to work — padding is implicit, not an opt-in flag.
- **NFR-4: Golden-file coverage.** Every new behavior must have at least one test fixture and golden file exercising it, per the project's testing strategy.
- **NFR-5: No external dependencies.** Implementation must use only stdlib + Jinja2 (per Project Constitution constraint 6).
- **NFR-6: basedpyright strict compliance.** All new/modified Python code must pass basedpyright strict mode with zero errors.

## Acceptance Criteria

- **AC-1:** A struct with mixed-width members (e.g., 1-bit, 13-bit, 4-bit, 1-bit) generates an SV typedef with per-member padding and correct padding widths.
- **AC-2:** `LP_<NAME>_WIDTH` equals the sum of data bits (no padding). `LP_<NAME>_BYTE_COUNT` equals the sum of per-member byte-aligned sizes.
- **AC-3:** `pack_<name>()` produces a vector of width `WIDTH` containing only data bits.
- **AC-4:** `unpack_<name>()` produces a struct with all padding bits set to 0.
- **AC-5:** `pack(unpack(v)) == v` for any valid packed vector `v` (round-trip identity).
- **AC-6:** SV `to_bytes()` output for any struct matches C++ `to_bytes()` output matches Python `to_bytes()` output for the same logical values.
- **AC-7:** Nested structs (struct containing struct) correctly apply padding at each level.
- **AC-8:** Scalar types emit `LP_<NAME>_WIDTH`, `LP_<NAME>_BYTE_COUNT`, and identity `pack_<name>`/`unpack_<name>` functions.
- **AC-9:** C++ scalar fields use minimum-width native types (`uint8_t` for <=8 bits, etc.).
- **AC-10:** All golden tests pass after changes, including updated golden files for existing fixtures.
- **AC-11:** At least one new test fixture exercises a struct with members requiring non-trivial padding (e.g., 1-bit, 13-bit fields).

## Out of Scope

- **Unpacked types.** Per Project Constitution constraint 3, all types are packed.
- **User-specified alignment.** Padding is always to byte (8-bit) boundaries. Custom alignment (e.g., 16-bit, 32-bit) is out of scope.
- **Cross-module type references.** Per Project Constitution constraint 4, struct fields referencing types from other modules are rejected.
- **Arbitrary-width constants.** Per Project Constitution constraint 5, constants are restricted to 32/64 bits.
- **Signed struct fields.** Signed scalars as struct members are not addressed in this spec (existing behavior preserved).
- **Runtime/build backend changes.** Changes are limited to the sv, cpp, and py emitter backends.

## Open Questions

- **[NEEDS CLARIFICATION] OQ-1:** The requirements example shows `status_padding` as the padding member name, but also `flag_a_padding`. The spec standardizes on `<field_name>_pad` for brevity and consistency with the `_t` / `_ct` naming conventions. Confirm this naming choice.
- **[NEEDS CLARIFICATION] OQ-2:** For struct-typed fields nested inside another struct, should the outer struct's padding be computed based on the inner struct's `WIDTH` (data bits) or `BYTE_COUNT * 8` (byte-aligned size)? The spec assumes `BYTE_COUNT * 8` since the inner struct is already byte-aligned in its own typedef. Confirm.
- **[NEEDS CLARIFICATION] OQ-3:** The requirements example has a typo (`LP_BAR_BYTE_COUNe`). Confirming the correct name is `LP_<NAME>_BYTE_COUNT`.
