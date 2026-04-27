# Delta Revision — Iteration 3 (Delta 1)

## User Feedback
"in FR-12 Signed Scalars as Struct Members section, the example `from_bytes({0x0A})` should raise error, as the 4-bit data is signed type, top 4-bit padding should be sign-extended."

## Changes Made

### spec.md — FR-12 `from_bytes` bullet
- **Before:** "Extracts only the lower `WIDTH` data bits and decodes from two's complement. Padding bits in the input (whether zero or sign-extended) are ignored."
- **After:** Validates that padding bits match sign extension of data's sign bit; mismatch raises error.

### spec.md — FR-12 worked example
- **Before:** `from_bytes({0x0A})`: extracts `4'b1010` = -6 ✓ (padding ignored)
- **After:** `from_bytes({0x0A})`: padding = `4'b0000`, sign bit = 1, **mismatch → error**

### spec.md — FR-6 `from_bytes` (SV verification)
- **Before:** "Padding bits in the input byte array are ignored"
- **After:** Unsigned: padding ignored. Signed with padding_bits > 0: validates sign extension, mismatch raises error.

### spec.md — FR-6 scalar `from_bytes`
- **Before:** "from_bytes() deserializes by extracting only the lower `WIDTH` data bits from the byte array (upper padding bits are masked/ignored)."
- **After:** Unsigned: masked/ignored. Signed with padding_bits > 0: validates padding matches sign extension; mismatch raises error.

### spec.md — FR-7 C++ scalar `from_bytes`
- **Before:** "Upper padding bits in the input are masked/ignored."
- **After:** Unsigned: masked/ignored. Signed with padding_bits > 0: validates, throws `std::invalid_argument`.

### spec.md — FR-8 C++ struct `from_bytes`
- **Before:** "Padding bits in input are ignored"
- **After:** Unsigned: ignored. Signed with padding_bits > 0: validated, throws `std::invalid_argument`.

### spec.md — FR-9 Python `from_bytes`
- **Before:** "Padding bits in input are ignored" / "masking upper padding bits"
- **After:** Unsigned: ignored/masked. Signed with padding_bits > 0: validated, raises `ValueError`.

### spec.md — AC-16
- Updated `from_bytes` examples to show validation passing (not just masking).

### spec.md — AC-23 (new)
- `from_bytes({0x0A})` for 4-bit signed scalar raises error (padding mismatch).
- `from_bytes({0x1F})` for 5-bit signed scalar with value -1 raises error (padding mismatch).

### clarifications.md — C-14 (new)
- Added clarification documenting the change with rationale.

### spec.md — Changelog
- Added 7 entries for delta 1 changes.

## Sections NOT Modified
- Definitions, FR-1, FR-2, FR-3, FR-4, FR-5 (unpack/pack unchanged)
- FR-10, FR-10a, FR-11, FR-13, FR-14
- NFR-1 through NFR-6
- AC-1 through AC-15, AC-17 through AC-22 (except AC-16 updated)
- Out of Scope
- All previous clarifications C-1 through C-13
