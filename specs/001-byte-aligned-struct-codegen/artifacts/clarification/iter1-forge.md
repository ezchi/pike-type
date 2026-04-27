# Clarifications: 001-byte-aligned-struct-codegen

**Spec ID:** 001-byte-aligned-struct-codegen  
**Date:** 2026-04-24  

---

## C-1: Signed Scalar Padding in `unpack` — Sign Extension [SPEC UPDATE]

**Ambiguity:** FR-12 states "No sign extension occurs during pack/unpack" and FR-5 states `unpack` initializes the result to `'0` (all padding bits = 0). For signed scalars used as struct members, this creates a broken cross-language mapping: a 4-bit signed value `4'b1010` (-6) padded with zeros becomes `8'b0000_1010` (+10), which is incorrect when C++ reads the byte as `std::int8_t`.

**Resolution:** `unpack` SHALL sign-extend the padding bits for signed scalar fields. `pack` continues to extract the raw bit pattern unchanged.

**Rationale:** The purpose of byte-aligned padding is to enable natural mapping to native C types. For signed scalars, the native type is `std::int8_t`/`int16_t`/etc. A byte read from HW must be directly interpretable as the signed native type. Sign extension of padding achieves this: a 4-bit signed `4'b1010` (-6) becomes `8'b1111_1010` (-6 as `int8_t`).

**Impact:**
- FR-5 (`unpack`): For signed scalar fields, the `_pad` bits must be filled with the field's sign bit, not zero.
- FR-12: Remove "No sign extension occurs during pack/unpack" — `pack` still has no sign extension, but `unpack` now does.
- FR-3 (SV typedef): The `_pad` field semantics change for signed fields — it carries the sign bit value, not always zero.
- FR-6 (`to_bytes`): Serialization of signed fields must emit sign-extended padding bytes, not zero-padded.
- FR-8, FR-9 (C++/Python `to_bytes`): Same — sign-extended padding for signed fields.
- FR-6 (`from_bytes`): No change needed — `from_bytes` already extracts only data bits, ignoring padding values.
- AC-4: `unpack_bar` still works (bar_t has no signed fields in the example).
- AC-16: Needs update — the `to_bytes()` for a signed -1 value should now produce sign-extended padding.

**Worked example:**
- SV 4-bit signed `field_1 = 4'b1010` (-6 in two's complement)
- `pack`: extracts `4'b1010` as raw bit pattern (unchanged)
- `unpack`: `field_1_pad = 4'b1111` (sign bit = 1, extended to pad width), `field_1 = 4'b1010`
- Combined byte: `8'b1111_1010` = `0xFA` = -6 as `std::int8_t` — correct
- Positive case: `field_1 = 4'b0110` (+6), `field_1_pad = 4'b0000`, byte = `0x06` = +6 as `std::int8_t` — correct

## C-2: `to_bytes` Padding for Signed Fields [SPEC UPDATE]

**Ambiguity:** FR-6 says "Padding bits are always serialized as zero." This contradicts the sign-extension requirement for signed fields established in C-1.

**Resolution:** `to_bytes()` SHALL serialize signed scalar fields with sign-extended padding (matching the `unpack` behavior). Unsigned fields continue to use zero-padded bytes. This ensures the byte stream is directly interpretable as native signed integers.

**Rationale:** If `to_bytes()` zero-fills padding but the `_pad` field in the SV typedef is sign-extended (via `unpack`), then `to_bytes()` and `to_slv()` would produce inconsistent representations. The byte stream must match the sign-extended struct representation.

**Impact:** FR-6, FR-8, FR-9, AC-16.

## C-3: `from_bytes` for Signed Fields — No Change Needed [NO SPEC CHANGE]

**Clarification:** `from_bytes()` already extracts only the `WIDTH` data bits and decodes from two's complement. The sign-extension change in C-1/C-2 does not affect `from_bytes()` — it still ignores padding bits in the input. Whether the input padding is zero or sign-extended, the extracted data bits and decoded signed value are the same.

**Rationale:** `from_bytes({0xFA})` for a 4-bit signed field extracts `4'b1010` = -6. `from_bytes({0x0A})` also extracts `4'b1010` = -6. Padding bits don't affect the result.

## C-4: `pack` Semantics for Signed Fields — No Change Needed [NO SPEC CHANGE]

**Clarification:** `pack` continues to extract the raw bit pattern for all fields, signed or unsigned. The sign bit is part of the data bits. `pack` does not perform sign extension because it produces a compact data-width vector with no padding.

**Rationale:** The pack output width = `WIDTH` (data bits only, no padding). There is no room for sign extension and no need — the compact vector preserves the exact bit pattern.

## C-5: `to_slv` for Signed Fields [SPEC UPDATE]

**Ambiguity:** FR-10a says `to_slv()` returns the padded struct with "all `_pad` fields set to zero." For signed fields, this should now use sign extension per C-1.

**Resolution:** `to_slv()` SHALL set `_pad` fields using sign extension for signed scalar fields, and zero for unsigned scalar fields.

**Impact:** FR-10a, AC-19.

## C-6: Round-Trip Invariant with Sign Extension [NO SPEC CHANGE]

**Clarification:** The round-trip invariant `pack(unpack(v)) == v` (FR-5) still holds. `unpack` places data bits into the correct field positions and sign-extends padding. `pack` then extracts only the data bits, discarding padding. The sign-extended padding does not affect the packed output.

**Verification:** For `field_1 = 4'b1010`:
- `unpack`: `{field_1_pad=4'b1111, field_1=4'b1010}` — sign-extended
- `pack`: extracts `field_1 = 4'b1010` — data bits only
- Round-trip: `4'b1010` → unpack → pack → `4'b1010` ✓

## C-7: Unsigned Fields Unchanged [NO SPEC CHANGE]

**Clarification:** All behaviors for unsigned scalar fields remain exactly as specified. Zero-fill padding in `unpack`, zero padding in `to_bytes`, zero `_pad` in `to_slv`. The sign-extension changes in C-1/C-2/C-5 apply exclusively to signed scalar fields.

## C-8: AC-16 Update Needed [SPEC UPDATE]

**Issue:** AC-16 currently states: `to_bytes()` for a signed 5-bit value of -1 = `{0x1F}` (upper 3 padding bits zero).

With sign extension: -1 in 5-bit two's complement = `5'b11111`. Sign bit = 1. Padding = `3'b111`. Full byte = `8'b1111_1111` = `0xFF`.

**Resolution:** AC-16 SHALL be updated: `to_bytes()` for a signed 5-bit value of -1 = `{0xFF}` (upper 3 padding bits sign-extended to 1). `from_bytes({0xFF})` masks to 5 bits and decodes as -1 (same result as before — `from_bytes` ignores padding).

A second example for clarity: signed 5-bit value of +5 = `5'b00101`. Sign bit = 0. Padding = `3'b000`. `to_bytes()` = `{0x05}` (same as zero-fill since sign bit is 0).
