# Delta Revision — Iteration 5 (Delta 3)

## User Feedback
"for FR-13, it scalar types with width > 64 should be supported and only support unsigned type for width > 64. in c++, use std::vector<uint8_t> as underlying type."

## Changes Made

### spec.md — FR-13: Scalar Width Constraint → Signed Scalar Width Constraint
- **Before:** "the validation layer SHALL reject scalar widths > 64 unconditionally"
- **After:** Unsigned scalars of any width supported. Signed scalars > 64 bits rejected. Error messages changed to include "signed" qualifier.

### spec.md — FR-7: C++ Type Mapping
- **Before:** 4 tiers (1–8, 9–16, 17–32, 33–64)
- **After:** 5 tiers (added width > 64: `std::vector<std::uint8_t>`, unsigned only). Added "Wide scalar storage" paragraph.

### spec.md — AC-9
- **Before:** 3 examples (13-bit, 1-bit, 37-bit)
- **After:** Added 128-bit unsigned → `std::vector<std::uint8_t>`

### spec.md — AC-17
- **Before:** "Logic(65) is rejected"
- **After:** "Logic(128) passes; LogicSigned(65) rejected with 'exceeds maximum 64-bit signed width'"

### spec.md — AC-18
- **Before:** "Logic(65) inline rejected"
- **After:** "LogicSigned(65) inline rejected; Logic(128) inline passes"

### spec.md — Out of Scope
- **Before:** "Scalar widths > 64 bits. Rejected unconditionally."
- **After:** "Signed scalar widths > 64 bits. Rejected by validation. Unsigned scalars of any width are supported."

### clarifications.md — C-15 (new)
- Documents the change with full rationale.

### spec.md — Changelog
- 6 entries for delta 3.

## Sections NOT Modified
- Definitions, FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-8, FR-9, FR-10, FR-10a, FR-11, FR-12, FR-14
- NFR-1 through NFR-6
- AC-1 through AC-8, AC-10 through AC-16, AC-19 through AC-23
- All previous clarifications C-1 through C-14
