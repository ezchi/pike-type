# Delta Gauge Review: Clarification — Iteration 5 (Delta 3)

**Provider:** codex (gpt-5.5)  
**Date:** 2026-04-24  

## Findings

1. **MAJOR**: NFR-4 still lists FR-13 as "validation-only" but FR-13 now enables positive code generation for unsigned >64-bit scalars. Remove FR-13 from the validation-only list and require positive golden coverage.

2. **MAJOR**: Missing acceptance coverage for wide scalar serialization. AC-9 only checks C++ type mapping, AC-17/18 only check validation. Need an AC for >64-bit unsigned scalar round-trip through `to_bytes()`/`from_bytes()` across SV, C++, and Python. Use a non-byte-aligned width like 65 bits to prove MSB padding zeroing/masking, and cover a struct member containing that scalar.

3. **MAJOR**: FR-7 says the wide C++ wrapper stores `std::vector<std::uint8_t>` and `to_bytes()` returns it directly, while also requiring zero MSB padding. That invariant is underspecified. The spec must say whether constructors/setters normalize length and clear padding bits, or whether `to_bytes()` returns a masked copy.

No unrelated sections were modified. SV and Python wide scalar handling are covered by existing generic semantics.

VERDICT: REVISE
