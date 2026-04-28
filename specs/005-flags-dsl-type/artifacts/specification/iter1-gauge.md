# Gauge Review — Iteration 1

## Findings

1. **BLOCKING** — `pack_<name>()` / `unpack_<name>()` are ambiguous. Do they operate on `WIDTH` bits or byte-aligned `WIDTH + alignment_bits` bits? This conflicts with FR-13 which says `WIDTH` is only flag count. Existing `Struct()` pack/unpack excludes padding. Fix this before implementation.

2. **BLOCKING** — Python `_value` bit layout is underspecified. C++ masks imply `a,b,c == 0xE0`, but Python could easily be implemented as compact `0x07` and still pass round-trip tests. Add explicit byte vectors for all backends.

3. **BLOCKING** — Python `from_bytes(data) -> None` contradicts existing generated Python scalar/struct patterns, where `from_bytes` is a `@classmethod` returning a new wrapper instance. This must be aligned.

4. **BLOCKING** — Valid snake_case flag names can still generate invalid code or collisions: `class`, `from`, `logic`, `to_bytes`, `from_bytes`, `clone`, etc. Validation only reserves `_pad`. That is insufficient for three-language codegen.

5. **WARNING** — Edge coverage is incomplete. The prompt explicitly calls out 1 flag and 64 flags; the spec only requires "fewer than 8" and "more than 8". Exactly 64 is a critical `std::uint64_t` / `1 << 63` boundary and needs a positive test.

6. **WARNING** — Testing only mentions golden/idempotency. AC-4 requires runtime round-trip behavior in all backends. Goldens do not prove semantics. At minimum, add Python runtime tests with fixed vectors; ideally also compile generated C++.

7. **NOTE** — The C++ mask formula is correct for MSB-first byte-aligned flags. Specify generated literal suffixes/casts for 64-bit masks to avoid unsafe `1 << 63` implementations.

VERDICT: REVISE
