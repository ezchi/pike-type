# Specification: Struct `multiple_of(N)` Alignment

**Spec ID:** 003-struct-multiple-of
**Status:** Draft
**Author:** Forge (Claude)

---

## Overview

Add a `multiple_of(N)` method to `StructType` that pads the total serialized struct width to a multiple of `N` bits. Without `multiple_of`, the existing behavior is preserved: each field is independently padded to the next byte boundary, and the struct's total width is the sum of those per-field byte-aligned widths. With `multiple_of(N)`, the struct receives additional trailing padding bits so that the total serialized width is the smallest multiple of `N` that is >= the natural byte-aligned width.

The trailing alignment padding is treated identically to existing per-field padding: it is unsigned, zero-filled on pack/to_bytes, and ignored (masked) on unpack/from_bytes.

---

## User Stories

- **US-1:** As a hardware engineer, I want to define a struct whose total width is a multiple of 32 bits, so that it aligns to a 32-bit bus width in my RTL design.
- **US-2:** As a firmware developer, I want pack/unpack and to_bytes/from_bytes for aligned structs to work the same way as for unaligned structs, so I don't need special handling for the trailing pad.
- **US-3:** As a user, I want validation errors if I pass nonsensical alignment values (e.g., zero, negative, non-power-of-two, or a value that isn't a multiple of 8), so I catch mistakes early.

---

## Functional Requirements

### FR-1: DSL `multiple_of(N)` method

Add a `multiple_of(N: int)` method to `StructType` that:
- Accepts a positive integer `N` representing the alignment granularity in bits.
- Stores the alignment constraint on the `StructType` instance.
- Returns `self` for method chaining, consistent with `add_member`.
- Can be called at most once per struct. A second call raises `ValidationError`.
- Must be called after all `add_member` calls (enforced: calling `add_member` after `multiple_of` raises `ValidationError`).

**Example:**
```python
foo_t = Struct().add_member("a", Bit(5)).add_member("b", Bit(12)).multiple_of(32)
```

### FR-2: Validation constraints on N

The value `N` must satisfy all of the following, checked at DSL construction time (`multiple_of()` call):
- `N` is a positive integer (`N > 0`).
- `N` is a multiple of 8 (alignment must be byte-aligned; sub-byte alignment is not meaningful since all fields are already byte-padded).
- `N >= 8`.

If any constraint is violated, raise `ValidationError` with a descriptive message.

**Not required:** `N` does not need to be a power of two. Values like `multiple_of(24)` are valid.

### FR-3: IR representation

Add an `alignment_bits` field to `StructIR`:
- Type: `int`, default `0`.
- When `multiple_of(N)` is set, `alignment_bits` stores the number of trailing padding bits needed to reach the next multiple of `N`.
- Formula: let `natural_width = sum(byte_count(field) * 8 for field in fields)`. Then `alignment_bits = (-natural_width) % N`.
- When `alignment_bits == 0`, the struct already satisfies the alignment and no trailing pad is added.

The `alignment_bits` value is computed during freeze and stored on `StructIR`. No new IR node types are needed.

### FR-4: SystemVerilog backend

When `alignment_bits > 0`, the generated `typedef struct packed` includes a trailing (bottom) field:
```systemverilog
logic [alignment_bits-1:0] _align_pad;
```
This field appears as the **last** field in the struct packed definition (lowest bits in the packed representation).

**Pack function:** The alignment pad is zero-filled. The pack function concatenates field values and appends `alignment_bits'(0)` at the LSB.

**Unpack function:** The alignment pad bits are ignored (not extracted into any user-visible field).

**to_bytes / from_bytes (verification helper class):** The trailing alignment pad is serialized as zero bytes (or partial byte if alignment_bits is not a multiple of 8 — but per FR-2, N is a multiple of 8, and the natural width is already byte-aligned, so alignment_bits will always be a multiple of 8). During from_bytes, the trailing pad bytes are consumed and their content is ignored.

### FR-5: C++ backend

When `alignment_bits > 0`:
- `to_bytes()` appends `alignment_bits / 8` zero bytes after all field bytes.
- `from_bytes()` consumes and discards the trailing `alignment_bits / 8` bytes, validating that sufficient bytes remain in the input.
- The byte count reported by the struct class accounts for the alignment padding.

### FR-6: Python backend

When `alignment_bits > 0`:
- `to_bytes()` appends `alignment_bits / 8` zero bytes (`b'\x00' * (alignment_bits // 8)`) after all field bytes.
- `from_bytes()` consumes and ignores the trailing `alignment_bits / 8` bytes, raising `ValueError` if the input is too short.
- The `BYTE_COUNT` class attribute accounts for the alignment padding.

### FR-7: Freeze logic

In `dsl/freeze.py`, when freezing a `StructType` that has `multiple_of` set:
1. Compute the natural byte-aligned width (sum of per-field byte-counts * 8).
2. Compute `alignment_bits = (-natural_width) % N`.
3. Pass `alignment_bits` to the `StructIR` constructor.

When `multiple_of` is not set, `alignment_bits` defaults to `0` and no behavior changes.

### FR-8: Validation pass

In `validate/engine.py`, add validation:
- If `alignment_bits > 0`, verify it is a multiple of 8 (this should always be true given FR-2, but defend against implementation bugs).
- No other validation changes needed — existing struct validation passes apply as before.

---

## Non-Functional Requirements

- **NFR-1: Backward compatibility.** Structs without `multiple_of` must produce byte-for-byte identical output to the current implementation. No existing golden files should change.
- **NFR-2: Deterministic output.** The alignment padding calculation is purely arithmetic and introduces no non-determinism.
- **NFR-3: Type safety.** All new fields pass `basedpyright` strict mode with zero errors.

---

## Acceptance Criteria

- **AC-1:** `Struct().add_member("a", Bit(5)).add_member("b", Bit(12)).multiple_of(32)` produces a struct with total serialized width of 32 bits (4 bytes), with 8 bits of trailing alignment padding.
- **AC-2:** `Struct().add_member("a", Bit(5)).add_member("b", Bit(12)).multiple_of(24)` produces a struct with total serialized width of 24 bits (3 bytes), with 0 bits of trailing alignment padding (natural width already satisfies alignment).
- **AC-3:** `multiple_of(0)`, `multiple_of(-1)`, `multiple_of(5)` (not multiple of 8), and `multiple_of(3)` all raise `ValidationError`.
- **AC-4:** Calling `multiple_of` twice raises `ValidationError`.
- **AC-5:** Calling `add_member` after `multiple_of` raises `ValidationError`.
- **AC-6:** All existing golden-file tests pass unchanged.
- **AC-7:** New golden-file test(s) cover the `multiple_of` feature with at least: (a) a struct that needs trailing padding, (b) a struct where natural width already meets the alignment.
- **AC-8:** Pack/unpack round-trips correctly in generated SV, C++, and Python for aligned structs.
- **AC-9:** `to_bytes`/`from_bytes` round-trips correctly in all backends, treating trailing pad as zero-filled unsigned padding.
- **AC-10:** `basedpyright` strict mode passes with zero errors.

---

## Out of Scope

- **Per-field alignment.** This feature aligns the total struct width only, not individual fields.
- **Sub-byte alignment.** `N` must be a multiple of 8; sub-byte alignment granularity is not supported.
- **Nested struct alignment propagation.** If a struct with `multiple_of` is used as a field in another struct, the outer struct sees the aligned width (including trailing pad). No special propagation logic is needed — the IR already accounts for the full byte count.
- **Runtime (dynamic) alignment.** Alignment is a static property set at DSL definition time.

---

## Open Questions

None. The feature is well-defined and self-contained.
