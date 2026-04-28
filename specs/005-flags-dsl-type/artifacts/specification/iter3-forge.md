# Spec 005 — Flags() DSL Type

## Overview

Add a `Flags()` DSL type that represents a packed bit-field register. Each flag is a single-bit `logic` field. Unlike `Struct().add_member()`, `add_flag()` does not pad each field individually — flags are packed contiguously, and only a single trailing `_align_pad` is emitted to reach the next byte boundary.

All three backends (SystemVerilog, C++, Python) generate code with `to_bytes()`/`from_bytes()` round-trip support. **Note:** The byte-level layout differs from `Struct()` — Flags places data bits in the MSB positions (matching hardware register conventions), whereas Struct per-field padding places data in the LSB positions for unsigned scalars.

## User Stories

- **US-1:** As a hardware engineer, I want to define a register of named 1-bit flags in the Python DSL, so that I can generate packed SystemVerilog types with explicit flag names instead of anonymous bit vectors.
- **US-2:** As a firmware developer, I want generated C++ flag classes with typed getter/setter methods and static bitmask constants, so that I can manipulate hardware registers safely without manual bit-twiddling.
- **US-3:** As a verification engineer, I want generated Python flag classes with `to_bytes()`/`from_bytes()` round-trip support, so that I can build and parse register values in testbenches.

## Functional Requirements

### DSL Layer

**FR-1:** A new `Flags()` factory function returns a mutable `FlagsType` DSL node. It is defined in `src/typist/dsl/flags.py` and exported from `src/typist/dsl/__init__.py`.

**FR-2:** `FlagsType.add_flag(name: str) -> FlagsType` appends a 1-bit flag and returns self for chaining. The name must match `^[a-z][a-z0-9_]*$` (snake_case). Duplicate flag names within the same `FlagsType` raise `ValidationError`.

**FR-3:** `FlagsType` tracks the ordered list of flags. The `width` of a `FlagsType` equals the number of flags (one bit per flag).

**FR-4:** `FlagsType` is a valid top-level DSL object (like `StructType` and `ScalarType`). It participates in the loader, freeze, and validation pipelines.

### IR Layer

**FR-5:** A new `FlagsIR` frozen dataclass in `ir/nodes.py`:
```python
@dataclass(frozen=True, slots=True)
class FlagFieldIR:
    name: str
    source: SourceSpanIR

@dataclass(frozen=True, slots=True)
class FlagsIR:
    name: str
    source: SourceSpanIR
    fields: tuple[FlagFieldIR, ...]
    alignment_bits: int  # trailing padding to byte boundary
```

**FR-6:** `FlagsIR` is added to the `TypeDefIR` union: `type TypeDefIR = ScalarAliasIR | StructIR | FlagsIR`.

**FR-7:** `alignment_bits` is computed automatically during freeze as `(-len(fields)) % 8`. No user-facing `multiple_of()` method is needed — flags always pad to byte boundary.

### Freeze Pipeline

**FR-8:** `freeze.py` handles `FlagsType` in `freeze_module()`: iterates over the flags list, freezes each to `FlagFieldIR`, computes `alignment_bits`, and produces a `FlagsIR`.

**FR-9:** `build_type_definition_map()` recognizes `FlagsType` alongside `ScalarType` and `StructType`.

### Validation

**FR-10:** `validate/engine.py` validates `FlagsIR`:
- Name must end with `_t`.
- At least 1 flag required.
- No duplicate flag names.
- Flag names must not end with `_pad` (reserved for generated padding).
- Flag names must not collide with generated class API names. Reserved names: `value`, `to_bytes`, `from_bytes`, `clone`, `width`, `byte_count`.
- Total flag count must not exceed 64.

### Bit Layout Convention

**FR-11 (bit layout):** All backends use an MSB-first, big-endian bit layout. This is the natural layout for hardware flag registers: the first declared flag occupies the most significant bit, and padding fills the least significant bits of the last byte.

**This intentionally differs from Struct per-field layout**, where unsigned scalar data occupies the LSBs and padding fills the MSBs of each field's byte allocation. For Flags, the motivation is that hardware register flag indices conventionally start from the MSB.

For `my_flags_t = Flags().add_flag("a").add_flag("b").add_flag("c")` (3 flags, `BYTE_COUNT = 1`):

| Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
|-------|-------|-------|-------|-------|-------|-------|-------|
| a     | b     | c     | pad   | pad   | pad   | pad   | pad   |

- `{a=1, b=0, c=1}` serializes to `0xA0` (binary `10100000`).
- `{a=1, b=1, c=1}` serializes to `0xE0` (binary `11100000`).

### SystemVerilog Backend

**FR-12:** `FlagsIR` generates a `typedef struct packed` with one `logic` field per flag, plus a trailing `logic [N-1:0] _align_pad` when `alignment_bits > 0`. Fields are listed in declaration order (first flag = MSB).

Example (3 flags):
```systemverilog
typedef struct packed {
    logic a;
    logic b;
    logic c;
    logic [4:0] _align_pad;
} my_flags_t;
```

**FR-13:** `pack_<name>()` and `unpack_<name>()` operate on the data-only width (`LP_<NAME>_WIDTH`), consistent with existing Struct pack/unpack. `LP_<NAME>_WIDTH` equals the number of flags (not the byte-aligned width).

Signatures:
```systemverilog
function automatic logic [LP_MY_FLAGS_WIDTH-1:0] pack_my_flags(my_flags_t a);
  return {a.a, a.b, a.c};  // concatenate flag bits only, no padding
endfunction

function automatic my_flags_t unpack_my_flags(logic [LP_MY_FLAGS_WIDTH-1:0] a);
  my_flags_t result;
  result = '0;  // zero all fields including _align_pad
  // extract flag bits from LSB to MSB
  result.c = a[0];
  result.b = a[1];
  result.a = a[2];
  return result;
endfunction
```

**FR-14:** A test helper class is generated (in `_test_pkg`) with `to_bytes()` / `from_bytes()` support, following the same pattern as `Struct()` test helpers. `WIDTH` is the number of flags (data bits only). `BYTE_COUNT` is `ceil(flags / 8)`.

The test helper `to_bytes()` serializes the entire struct packed value (flags + padding) as big-endian bytes. `from_bytes()` deserializes the bytes back into the struct, zero-filling the padding bits.

### C++ Backend

**FR-15:** `FlagsIR` generates a C++ class named `<name>_ct` (e.g., `my_flags_ct`). The underlying storage is the smallest unsigned integer type that fits the byte-aligned width: `std::uint8_t` (1-8 flags), `std::uint16_t` (9-16), `std::uint32_t` (17-32), `std::uint64_t` (33-64).

**FR-16:** The class exposes:
- `static constexpr std::size_t WIDTH = <num_flags>;`
- `static constexpr std::size_t BYTE_COUNT = <ceil(flags/8)>;`
- `using value_type = std::uint{N}_t;`
- Per-flag static constexpr mask using UPPER_SNAKE_CASE: `static constexpr value_type <FLAG_NAME>_MASK = <hex_literal>;` where the mask is `1 << (BYTE_COUNT*8 - 1 - flag_index)` in big-endian MSB-first order. Mask literals use the `U` suffix for 8/16/32-bit types and `ULL` suffix for 64-bit types (to avoid undefined behavior from shifting into the sign bit).
- Per-flag getter: `bool get_<flag_name>() const { return (value & <FLAG_NAME>_MASK) != 0; }`
- Per-flag setter: `void set_<flag_name>(bool v) { if (v) value |= <FLAG_NAME>_MASK; else value &= static_cast<value_type>(~<FLAG_NAME>_MASK); }`
- `value_type value = 0;` — public member holding the packed bits.

Example (3 flags, `std::uint8_t`):
```cpp
static constexpr value_type A_MASK = 0x80U;
static constexpr value_type B_MASK = 0x40U;
static constexpr value_type C_MASK = 0x20U;
```

**FR-17:** The class has `to_bytes()`, `from_bytes()`, `clone()`, and `operator==`:

- `to_bytes()`: zeroes padding bits in the LSB positions before serializing as big-endian bytes. Masking: `value & DATA_MASK` where `DATA_MASK` has the top `WIDTH` bits set and bottom `alignment_bits` bits clear.
- `from_bytes()`: deserializes big-endian bytes, then masks out padding bits with `DATA_MASK`.
- `clone()`: returns a copy with the same `value`.
- `operator==`: uses `= default` (compares raw `value`), consistent with existing scalar alias pattern. Padding bits are always zeroed by `from_bytes()` and initialization, so raw comparison is correct for well-formed instances.

**FR-18:** If flag count exceeds 64, validation rejects it (FR-10). The C++ backend does not need to handle this case.

### Python Backend

**FR-19:** `FlagsIR` generates a Python class named `<name>_ct` with:
- `WIDTH: int = <num_flags>` (class variable)
- `BYTE_COUNT: int = <ceil(flags/8)>` (class variable)
- `__init__(self) -> None`: initializes `self._value: int = 0`.
- Per-flag property with getter/setter (backed by `self._value`).
  - Getter: `return bool(self._value & <mask>)` where mask follows the same MSB-first layout as C++.
  - Setter: sets or clears the corresponding bit in `_value`.
- `to_bytes() -> bytes` — serializes `_value` as big-endian bytes with padding bits zeroed: `(self._value & <data_mask>).to_bytes(BYTE_COUNT, "big")`.
- `@classmethod from_bytes(cls, data: bytes | bytearray) -> "<class_name>"` — constructs a new instance, deserializes the big-endian bytes, masks out padding bits, and sets `_value`.
- `clone() -> <class_name>` — returns a new instance with the same `_value` (masked).
- `__eq__` — compares `_value` masked with `DATA_MASK`.

**FR-20:** The internal `_value` integer uses the same bit positions as the C++ `value` member. For 3 flags in a 1-byte type: `a` is bit 7 (mask `0x80`), `b` is bit 6 (mask `0x40`), `c` is bit 5 (mask `0x20`).

### Testing

**FR-21:** A new fixture `tests/fixtures/flags_basic/` with a DSL module defining at least:
- A flags type with 1 flag (7 padding bits, `std::uint8_t`).
- A flags type with 3 flags (5 padding bits, `std::uint8_t`).
- A flags type with exactly 8 flags (no padding, `std::uint8_t`).
- A flags type with 9 flags (7 padding bits, `std::uint16_t`).

**FR-22:** Golden files in `tests/goldens/gen/flags_basic/` for all three backends.

**FR-23:** An integration test in `tests/test_gen_flags.py` that:
1. Runs `typist gen` on the fixture.
2. Compares output byte-for-byte against golden files.
3. Tests idempotency (second run produces identical output).

**FR-24:** Python runtime round-trip tests in `tests/test_gen_flags.py` that:
1. Import the generated Python flags module.
2. Create instances, set individual flags via properties.
3. Call `to_bytes()` and verify the exact byte values match expected big-endian encoding (e.g., `{a=True, b=False, c=True}` → `b'\xa0'`).
4. Call `from_bytes()` on known byte vectors and verify flag property values.
5. Verify round-trip: `from_bytes(instance.to_bytes())` produces an equal instance.

## Non-Functional Requirements

**NFR-1:** Output is deterministic and byte-for-byte reproducible (constitution principle 3).

**NFR-2:** Flags are always unsigned. Signed flags are not meaningful and not supported.

**NFR-3:** No cross-module flag type references in this milestone (consistent with constraint 4).

**NFR-4:** No `multiple_of()` on `FlagsType` — byte alignment is automatic and sufficient.

## Acceptance Criteria

- **AC-1:** `Flags().add_flag("a").add_flag("b").add_flag("c")` creates a `FlagsType` with `width == 3`.
- **AC-2:** The generated SystemVerilog `typedef struct packed` has 3 `logic` fields and a `logic [4:0] _align_pad`.
- **AC-3:** The generated C++ class uses `std::uint8_t` storage with `A_MASK = 0x80U`, `B_MASK = 0x40U`, `C_MASK = 0x20U`, and correct getter/setter methods.
- **AC-4:** Python runtime tests verify `to_bytes()` / `from_bytes()` round-trips with explicit byte vectors for all fixture flag types.
- **AC-5:** A flags type with exactly 8 flags produces no `_align_pad` field and uses `std::uint8_t`.
- **AC-6:** A flags type with 9 flags produces `std::uint16_t` storage with 7 padding bits and correct masks.
- **AC-7:** Validation rejects: 0 flags, >64 flags, duplicate flag names, non-snake_case names, names ending in `_pad`, reserved API names (`value`, `to_bytes`, etc.), type name not ending in `_t`.
- **AC-8:** Golden-file integration tests pass for all three backends.
- **AC-9:** `typist gen` is idempotent for flags fixtures.
- **AC-10:** `basedpyright` strict mode passes with zero errors on all new code.
- **AC-11:** A 1-flag type serializes correctly: `{flag=True}` → `b'\x80'`, `{flag=False}` → `b'\x00'`.

## Out of Scope

- Flags wider than 64 bits (rejected by validation).
- Signed flags.
- `multiple_of()` for flags (automatic byte alignment only).
- Flags as struct members (cross-type nesting — future milestone).
- Named flag values / enumerations.
- Bit-range flags (multi-bit fields within a flags type).
- **Comprehensive language keyword reservation.** This spec reserves a minimal set of names that collide with the generated class API (FR-10). Broader language keyword checks (SV keywords, C++ keywords, Python keywords) should be addressed in a separate cross-cutting spec covering all type definitions, not just Flags.
- **C++/SV compile-time or simulation verification.** The project's current test infrastructure uses Python golden-file comparison and Python runtime tests. Adding C++ compilation or SV simulation tests is outside the scope of this feature.

## Open Questions

None — all design decisions are resolved in this specification.
