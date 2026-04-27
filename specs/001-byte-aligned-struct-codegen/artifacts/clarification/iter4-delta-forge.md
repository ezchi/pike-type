# Delta Revision — Iteration 4 (Delta 2)

## Gauge Feedback (from iter3 delta gauge)
1. MAJOR: C-1, C-3, C-8 in clarifications.md have stale wording about `from_bytes` ignoring padding for signed fields, contradicting C-14.
2. MINOR: AC-12 says "padding bits are ignored" without specifying unsigned.

## Changes Made

### clarifications.md — C-1 impact list
- **Before:** "FR-6 (`from_bytes`): No change needed — `from_bytes` already extracts only data bits, ignoring padding values."
- **After:** "FR-6 (`from_bytes`): ~~No change needed~~ Superseded by C-14: signed `from_bytes` now validates padding matches sign extension."

### clarifications.md — C-3 rationale
- **Before:** "The `from_bytes()` data extraction is unchanged — it still ignores padding."
- **After:** Added note that C-14 later changed signed `from_bytes()` to validate padding; unsigned still ignored.

### clarifications.md — C-8 resolution
- **Before:** "`from_bytes({0xFF})` masks to 5 bits and decodes as -1 (same result as before — `from_bytes` ignores padding)."
- **After:** "`from_bytes({0xFF})` validates padding (`3'b111` matches sign bit 1) and decodes as -1."

### spec.md — AC-12
- **Before:** "padding bits are ignored on deserialization"
- **After:** "unsigned padding bits are ignored on deserialization"

### spec.md — Changelog
- Added entry for AC-12 wording fix.

## Sections NOT Modified
- All FR-* sections (already correct from iter3 delta)
- All other ACs (AC-1–AC-11, AC-13–AC-22, AC-23)
- All other clarifications (C-2, C-4–C-7, C-9–C-14)
- Definitions, NFR, Out of Scope
