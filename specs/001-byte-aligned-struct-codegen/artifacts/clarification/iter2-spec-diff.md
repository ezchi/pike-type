# Spec Diff — Iteration 2

Addresses all 5 MAJOR findings from Gauge iteration 1.

## Definitions — "Padding bits" (before → after)

**Before:** "Zero-fill bits placed on the MSB side of a field..."

**After:** "Byte-alignment bits placed on the MSB side of a field... Fill policy depends on signedness and context: for unsigned scalars, padding is zero-filled; for signed scalars, padding is sign-extended..."

## FR-1 — Padding computation rules bullet 3 (before → after)

**Before:** "Padding bits are zero-fill bits placed on the MSB side of the field in the packed struct."

**After:** "Padding bits are placed on the MSB side of the field in the packed struct. Fill policy is determined by the consuming operation (see Definitions)."

## FR-2 — IR description (before → after)

**Before:** "`StructFieldIR` SHALL carry a `padding_bits: int` field (frozen, >= 0) representing the number of zero-fill bits added to byte-align this member."

**After:** "`StructFieldIR` SHALL carry a `padding_bits: int` field (frozen, >= 0) representing the number of byte-alignment bits for this member. The fill policy (zero or sign-extended) is determined by the field's signedness and the consuming operation, not stored in IR."

## FR-3 — Added "Padding fill semantics" paragraph

**Added:** New paragraph after padding member naming explaining that `_pad` is a structural placeholder whose value is set by operations (`unpack`, `to_slv`), not constrained by the typedef.

## FR-6 — `from_bytes()` (before → after)

**Before:** "the deserialized struct will have all padding bits set to zero regardless of input padding values."

**After:** "field data values are extracted from the data-bit positions only. The SV verification helper class stores only logical field values (not `_pad` members). If the deserialized result is materialized as the SV `typedef struct packed` (e.g., via `to_slv()`), the standard padding fill policy applies."

## FR-7 — Scalar serialization (before → after)

**Before:** "upper 3 bits of first byte are zero padding" (only unsigned example)

**After:** Adds: "For **unsigned** scalars, padding bits are zero. For **signed** scalars, padding bits are sign-extended." Plus signed 4-bit example.

## FR-8 — C++ struct `to_bytes()` (before → after)

**Before:** "with MSB padding zeros"

**After:** "For **unsigned** scalar fields, MSB padding bits are zero. For **signed** scalar fields, MSB padding bits are sign-extended."

## FR-9 — Python struct `to_bytes()` (before → after)

**Before:** "big-endian, padding zeros included"

**After:** "For **unsigned** scalar fields, padding bits are zero. For **signed** scalar fields, padding bits are sign-extended."

## FR-10 — Item 2 (before → after)

**Before:** "The same padding placement (MSB side of each member, zero-filled)."

**After:** "The same padding placement (MSB side of each member) and fill policy (zero for unsigned scalars, sign-extended for signed scalars)."

## AC-21 (new)

Verifies `unpack` sign-extends `_pad` for signed 4-bit struct member (negative and positive cases).

## AC-22 (new)

Verifies `to_bytes()` for signed struct member produces identical sign-extended output across SV, C++, and Python.
