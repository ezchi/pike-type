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
- FR-6 (`from_bytes`): ~~No change needed~~ Superseded by C-14: signed `from_bytes` now validates padding matches sign extension.
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

## C-3: `from_bytes` Wording Clarification [SPEC UPDATE]

**Issue:** FR-6 stated `from_bytes()` produces a struct with "all padding bits set to zero." This is misleading now that signed fields use sign-extended padding. The SV verification helper class stores only logical field values, not `_pad` members.

**Resolution:** FR-6 `from_bytes()` wording updated to clarify that it extracts field data values only. The helper class does not store `_pad` fields. If the result is materialized as the SV typedef (via `to_slv()`), the standard fill policy applies.

**Rationale:** The wording fix prevents misinterpretation about what padding values exist in the deserialized result. Note: C-14 later changed signed `from_bytes()` to validate padding rather than ignore it; for unsigned fields, padding is still ignored.

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
*(Applied in iteration 1)*

**Issue:** AC-16 currently states: `to_bytes()` for a signed 5-bit value of -1 = `{0x1F}` (upper 3 padding bits zero).

With sign extension: -1 in 5-bit two's complement = `5'b11111`. Sign bit = 1. Padding = `3'b111`. Full byte = `8'b1111_1111` = `0xFF`.

**Resolution:** AC-16 SHALL be updated: `to_bytes()` for a signed 5-bit value of -1 = `{0xFF}` (upper 3 padding bits sign-extended to 1). `from_bytes({0xFF})` validates padding (`3'b111` matches sign bit 1) and decodes as -1. (Note: C-14 later changed signed `from_bytes` to validate padding rather than ignore it.)

A second example for clarity: signed 5-bit value of +5 = `5'b00101`. Sign bit = 0. Padding = `3'b000`. `to_bytes()` = `{0x05}` (same as zero-fill since sign bit is 0).

## C-9: Definitions and FR-1/FR-2 — Padding Fill Policy [SPEC UPDATE]  
*(Added in iteration 2, addressing Gauge finding)*

**Issue:** The Definitions section, FR-1, and FR-2 all described padding as "zero-fill bits," which is no longer universally true for signed scalar fields.

**Resolution:** 
- Definitions: Padding bits redefined as "byte-alignment bits" with fill policy depending on signedness and operation context.
- FR-1: Updated padding description to reference fill policy from Definitions.
- FR-2: Updated to clarify padding count is stored in IR but fill policy is determined by consuming operations.

**Rationale:** The fill value is not an intrinsic property of the padding count — it depends on the signed/unsigned nature of the field and the operation being performed.

## C-10: FR-3 — Padding Fill Semantics in Typedef [SPEC UPDATE]  
*(Added in iteration 2, addressing Gauge finding)*

**Issue:** FR-3 did not explain that generated `_pad` members for signed fields may legally contain non-zero values.

**Resolution:** Added "Padding fill semantics" paragraph to FR-3 explaining that `_pad` is a structural placeholder whose value is set by operations (`unpack`, `to_slv`), not constrained by the typedef.

## C-11: FR-7, FR-8, FR-9 — C++/Python Signed Scalar Serialization [SPEC UPDATE]  
*(Added in iteration 2, addressing Gauge finding)*

**Issue:** FR-7 scalar serialization example only showed zero-padded unsigned. FR-8 and FR-9 said "padding zeros" unconditionally, contradicting the sign-extension requirement.

**Resolution:**
- FR-7: Added signed scalar serialization example and stated sign-extended padding for signed types.
- FR-8: Changed "with MSB padding zeros" to "MSB padding bits are zero for unsigned, sign-extended for signed."
- FR-9: Changed "padding zeros included" to specify signedness-dependent fill.

## C-12: FR-10 — Cross-Language Padding Fill Policy [SPEC UPDATE]  
*(Added in iteration 2, addressing Gauge finding)*

**Issue:** FR-10 item 2 said padding placement is "zero-filled," which contradicts signed field behavior.

**Resolution:** FR-10 item 2 now says: "The same padding placement (MSB side of each member) and fill policy (zero for unsigned scalars, sign-extended for signed scalars)."

## C-13: Missing Acceptance Criteria for Signed Struct Member [SPEC UPDATE]  
*(Added in iteration 2, addressing Gauge finding)*

**Issue:** No acceptance criterion verified the user's primary requirement: signed struct-member `unpack` sign-extends `_pad`. No cross-language signed struct `to_bytes()` AC existed.

**Resolution:** Added:
- AC-21: Verifies `unpack` sets `_pad` to replicated sign bit for a signed 4-bit struct member (negative and positive cases).
- AC-22: Verifies `to_bytes()` for a signed struct member produces identical sign-extended output across SV, C++, and Python.

## C-14: `from_bytes` Signed Padding Validation [SPEC UPDATE]  
*(Added in delta 1, per user feedback)*

**User feedback:** "in FR-12 Signed Scalars as Struct Members section, the example `from_bytes({0x0A})` should raise error, as the 4-bit data is signed type, top 4-bit padding should be sign-extended."

**Issue:** `from_bytes()` previously ignored padding bits for all fields, including signed scalars. For a 4-bit signed field, `from_bytes({0x0A})` would silently accept `0x0A` (padding = `4'b0000`, sign bit = 1) — this is an inconsistent byte representation that should not be tolerated.

**Resolution:** `from_bytes()` for signed scalar fields with `padding_bits > 0` SHALL validate that the padding bits in the input match the sign extension of the data's sign bit (`{P{data[W-1]}}`). A mismatch SHALL raise an error:
- SV: error via assertion or task return
- C++: `std::invalid_argument`
- Python: `ValueError`

Unsigned fields remain unchanged — padding is ignored.

**Rationale:** The byte-aligned representation of a signed scalar is a native signed integer (e.g., `std::int8_t`). A valid signed value has its sign bit extended into the padding bits. If the padding doesn't match, the byte stream is corrupt or misinterpreted. Detecting this immediately is a correctness guard (Constitution principle 4: "correctness over convenience").

**Impact:** FR-6, FR-7, FR-8, FR-9, FR-12 (example + bullet), AC-16, new AC-23.

## C-15: Wide Unsigned Scalars (> 64 bits) [SPEC UPDATE]  
*(Added in delta 3, per user feedback)*

**User feedback:** "for FR-13, it scalar types with width > 64 should be supported and only support unsigned type for width > 64. in c++, use std::vector<uint8_t> as underlying type."

**Issue:** FR-13 rejected all scalar widths > 64 unconditionally, because there was no C++ native type mapping. The user wants to support arbitrary-width unsigned scalars using `std::vector<std::uint8_t>` as the C++ storage type.

**Resolution:**
- FR-13 changed from "reject all >64" to "reject only signed >64". Unsigned scalars of any width are now allowed.
- FR-7 adds a new storage tier: width > 64 → `std::vector<std::uint8_t>` (unsigned only). The vector stores the value in big-endian byte order with `kByteCount` elements. `to_bytes()` returns this vector directly. `from_bytes()` constructs from the byte vector, masking upper padding bits.
- Signed >64 is still rejected: no practical native C++ signed type exists beyond 64 bits, and sign extension on `std::vector<std::uint8_t>` would add unwarranted complexity.
- SV: no change needed — `logic [N-1:0]` works for any width.
- Python: no change needed — Python `int` handles arbitrary width natively.

**Rationale:** Many hardware register interfaces use wide data paths (128-bit, 256-bit, 512-bit). Rejecting these at the tool level forces users to split fields manually, which is error-prone. `std::vector<std::uint8_t>` is the natural C++ container for arbitrary-width byte-aligned data.

**Impact:** FR-13, FR-7, AC-9, AC-17, AC-18, Out of Scope.
