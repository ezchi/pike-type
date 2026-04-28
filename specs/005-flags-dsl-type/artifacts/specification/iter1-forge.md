# Spec 005 — Flags() DSL Type

## Overview

Add a `Flags()` DSL type that represents a packed bit-field register. Each flag is a single-bit `logic` field. Unlike `Struct().add_member()`, `add_flag()` does not pad each field individually — flags are packed contiguously, and only a single trailing `_align_pad` is emitted to reach the next byte boundary.

The generated outputs for all three backends (SystemVerilog, C++, Python) follow the same serialization contract as `Struct()`: big-endian, byte-aligned, with `to_bytes()`/`from_bytes()` round-trip support.

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
- Total flag count must not exceed 64.

### SystemVerilog Backend

**FR-11:** `FlagsIR` generates a `typedef struct packed` with one `logic` field per flag, plus a trailing `logic [N-1:0] _align_pad` when `alignment_bits > 0`. Fields are listed in declaration order (first flag = MSB).

Example (3 flags):
```systemverilog
typedef struct packed {
    logic a;
    logic b;
    logic c;
    logic [4:0] _align_pad;
} my_flags_t;
```

**FR-12:** `pack_<name>()` and `unpack_<name>()` functions are generated, treating the flags + padding as a contiguous bit vector. Padding bits are zero on pack and ignored on unpack (same as `Struct()` unsigned padding).

**FR-13:** A test helper class is generated (in `_test_pkg`) with `to_bytes()` / `from_bytes()` support, following the same pattern as `Struct()` test helpers. The `WIDTH` is the number of flags (not the byte-aligned width). The `BYTE_COUNT` is `ceil(flags / 8)`.

### C++ Backend

**FR-14:** `FlagsIR` generates a C++ class named `<name>_ct` (e.g., `my_flags_ct`). The underlying storage is the smallest unsigned integer type that fits the byte-aligned width: `std::uint8_t` (1-8 flags), `std::uint16_t` (9-16), `std::uint32_t` (17-32), `std::uint64_t` (33-64).

**FR-15:** The class exposes:
- `static constexpr std::size_t WIDTH = <num_flags>;`
- `static constexpr std::size_t BYTE_COUNT = <ceil(flags/8)>;`
- `using value_type = std::uint{N}_t;`
- Per-flag static constexpr mask: `static constexpr value_type <FLAG_NAME>_MASK = <hex_value>;` where the mask is `1 << (BYTE_COUNT*8 - 1 - flag_index)` (big-endian bit order, MSB-first).
- Per-flag getter: `bool get_<flag_name>() const { return (value & <FLAG_NAME>_MASK) != 0; }`
- Per-flag setter: `void set_<flag_name>(bool v) { if (v) value |= <FLAG_NAME>_MASK; else value &= ~<FLAG_NAME>_MASK; }`
- `value_type value = 0;` — public member holding the packed bits.

**FR-16:** The class has `to_bytes()`, `from_bytes()`, `clone()`, and `operator==` following the same pattern as scalar alias classes. Padding bits in the LSB positions are zeroed on `to_bytes()` and masked out on `from_bytes()`.

**FR-17:** If flag count exceeds 64, validation rejects it (FR-10). The C++ backend does not need to handle this case.

### Python Backend

**FR-18:** `FlagsIR` generates a Python class named `<name>_ct` with:
- `WIDTH: int = <num_flags>`
- `BYTE_COUNT: int = <ceil(flags/8)>`
- Per-flag property with getter/setter (backed by an internal integer `_value`).
- `to_bytes() -> bytes` — big-endian serialization of `_value` with padding bits zeroed.
- `from_bytes(data: bytes) -> None` — big-endian deserialization, masking out padding bits.
- `clone() -> <name>_ct` — deep copy.
- `__eq__` — value-based equality.

### Testing

**FR-19:** A new fixture `tests/fixtures/flags_basic/` with a DSL module defining at least:
- A flags type with fewer than 8 flags (needs padding).
- A flags type with exactly 8 flags (no padding).
- A flags type with more than 8 flags (multi-byte).

**FR-20:** Golden files in `tests/goldens/gen/flags_basic/` for all three backends.

**FR-21:** An integration test in `tests/test_gen_flags.py` that:
1. Runs `typist gen` on the fixture.
2. Compares output byte-for-byte against golden files.
3. Tests idempotency (second run produces identical output).

## Non-Functional Requirements

**NFR-1:** Output is deterministic and byte-for-byte reproducible (constitution principle 3).

**NFR-2:** Flags are always unsigned. Signed flags are not meaningful and not supported.

**NFR-3:** No cross-module flag type references in this milestone (consistent with constraint 4).

**NFR-4:** No `multiple_of()` on `FlagsType` — byte alignment is automatic and sufficient.

## Acceptance Criteria

- **AC-1:** `Flags().add_flag("a").add_flag("b").add_flag("c")` creates a `FlagsType` with `width == 3`.
- **AC-2:** The generated SystemVerilog `typedef struct packed` has 3 `logic` fields and a `logic [4:0] _align_pad`.
- **AC-3:** The generated C++ class uses `std::uint8_t` storage with `A_MASK = 0x80U`, `B_MASK = 0x40U`, `C_MASK = 0x20U`, and correct getter/setter methods.
- **AC-4:** `to_bytes()` / `from_bytes()` round-trips work correctly in all three backends.
- **AC-5:** A flags type with exactly 8 flags produces no `_align_pad` field and uses `std::uint8_t`.
- **AC-6:** A flags type with 9-16 flags produces `std::uint16_t` storage and correct padding.
- **AC-7:** Validation rejects: 0 flags, >64 flags, duplicate flag names, non-snake_case names, names ending in `_pad`, type name not ending in `_t`.
- **AC-8:** Golden-file integration tests pass for all three backends.
- **AC-9:** `typist gen` is idempotent for flags fixtures.
- **AC-10:** `basedpyright` strict mode passes with zero errors on all new code.

## Out of Scope

- Flags wider than 64 bits (rejected by validation).
- Signed flags.
- `multiple_of()` for flags (automatic byte alignment only).
- Flags as struct members (cross-type nesting — future milestone).
- Named flag values / enumerations.
- Bit-range flags (multi-bit fields within a flags type).

## Open Questions

None — all design decisions are resolved in this specification.
