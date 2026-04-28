# Specification: Struct `multiple_of(N)` Alignment

**Spec ID:** 003-struct-multiple-of
**Status:** Draft
**Author:** Forge (Claude)

---

## Overview

Add a `multiple_of(N)` method to `StructType` that pads the total serialized struct width to a multiple of `N` bits. Without `multiple_of`, the existing behavior is preserved: each field is independently padded to the next byte boundary, and the struct's total width is the sum of those per-field byte-aligned widths. With `multiple_of(N)`, the struct receives additional trailing padding bits so that the total serialized width is the smallest multiple of `N` that is >= the natural byte-aligned width.

The trailing alignment padding is treated identically to existing per-field padding: it is unsigned, zero-filled on serialization, and ignored (masked/discarded) on deserialization.

---

## User Stories

- **US-1:** As a hardware engineer, I want to define a struct whose total width is a multiple of 32 bits, so that it aligns to a 32-bit bus width in my RTL design.
- **US-2:** As a firmware developer, I want `to_bytes`/`from_bytes` for aligned structs to work the same way as for unaligned structs, so I don't need special handling for the trailing pad.
- **US-3:** As a user, I want validation errors if I pass nonsensical alignment values (e.g., zero, negative, or not a multiple of 8), so I catch mistakes early.

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
- `type(N) is int` — rejects `bool` (which is a subclass of `int` in Python) and non-integer types.
- `N > 0`.
- `N` is a multiple of 8 (alignment must be byte-aligned; sub-byte alignment is not meaningful since all fields are already byte-padded).

If any constraint is violated, raise `ValidationError` with a descriptive message.

**Not required:** `N` does not need to be a power of two. Values like `multiple_of(24)` are valid.

### FR-3: IR representation

Add an `alignment_bits` field to `StructIR`:
- Type: `int`, default `0`.
- When `multiple_of(N)` is set, `alignment_bits` stores the number of trailing padding bits needed to reach the next multiple of `N`.
- Formula: let `natural_width = sum(byte_count(field_data_width) * 8 for field in fields)` (the existing byte-aligned struct width). Then `alignment_bits = (-natural_width) % N`.
- When `alignment_bits == 0`, the struct already satisfies the alignment and no trailing pad is added.

The `alignment_bits` value is computed during freeze and stored on `StructIR`. No new IR node types are needed.

### FR-4: SystemVerilog backend

**`typedef struct packed`:** When `alignment_bits > 0`, the struct definition includes a trailing (lowest-bit) field:
```systemverilog
logic [alignment_bits-1:0] _align_pad;
```
This field appears as the **last** field in the struct packed definition (lowest bits in the packed representation).

**`LP_*_WIDTH` (data-only width):** Unchanged. The data-only width localparam does NOT include alignment padding or per-field padding. It remains the sum of raw data bits across all fields. `pack`/`unpack` continue to operate at this width.

**`LP_*_BYTE_COUNT`:** Updated to include alignment padding bytes. Formula: `(natural_width + alignment_bits) / 8`.

**`pack_*` function:** Unchanged. The pack function operates on data-only width, extracting field data bits from the struct. It does not include per-field padding or alignment padding.

**`unpack_*` function:** Unchanged. The unpack function operates on data-only width, injecting field data bits into the struct. Per-field padding is sign-extended; the alignment pad is zero-filled.

**`to_bytes` / `from_bytes` (verification helper class):** The trailing alignment pad bytes are serialized as zeros in `to_bytes`. In `from_bytes`, the trailing pad bytes are consumed and their content is ignored. The `WIDTH` and byte count in the helper class account for alignment padding.

### FR-5: C++ backend

When `alignment_bits > 0`:
- `to_bytes()` appends `alignment_bits / 8` zero bytes after all field bytes.
- `from_bytes()` consumes and discards the trailing `alignment_bits / 8` bytes, validating that sufficient bytes remain in the input.
- The `BYTE_COUNT` constant accounts for the alignment padding.

No `pack`/`unpack` API exists in C++; only `to_bytes`/`from_bytes` are affected.

### FR-6: Python backend

When `alignment_bits > 0`:
- `to_bytes()` appends `alignment_bits / 8` zero bytes (`b'\x00' * (alignment_bits // 8)`) after all field bytes.
- `from_bytes()` consumes and ignores the trailing `alignment_bits / 8` bytes, raising `ValueError` if the input is too short.
- The `BYTE_COUNT` class attribute accounts for the alignment padding.

No `pack`/`unpack` API exists in Python; only `to_bytes`/`from_bytes` are affected.

### FR-7: Freeze logic

In `dsl/freeze.py`, when freezing a `StructType` that has `multiple_of` set:
1. Compute the natural byte-aligned width: sum of `byte_count(field_data_width) * 8` for each field.
2. Compute `alignment_bits = (-natural_width) % N`.
3. Pass `alignment_bits` to the `StructIR` constructor.

When `multiple_of` is not set, `alignment_bits` defaults to `0` and no behavior changes.

### FR-8: Validation pass

In `validate/engine.py`, add validation:
- If `alignment_bits > 0`, verify it is a multiple of 8 (this should always be true given FR-2, but defend against implementation bugs).
- No other validation changes needed — existing struct validation passes apply as before.

### FR-9: Implementation approach

All backend output changes must follow the project's template-first generation principle. Backend emitters prepare view-model data (including `alignment_bits`) and templates handle presentation. Existing Jinja2 templates are extended where applicable; new templates are created only if the existing structure doesn't accommodate the change.

---

## Non-Functional Requirements

- **NFR-1: Backward compatibility.** Structs without `multiple_of` must produce byte-for-byte identical output to the current implementation. No existing golden files should change.
- **NFR-2: Deterministic output.** The alignment padding calculation is purely arithmetic and introduces no non-determinism.
- **NFR-3: Type safety.** All new fields pass `basedpyright` strict mode with zero errors.

---

## Acceptance Criteria

- **AC-1:** `Struct().add_member("a", Bit(5)).add_member("b", Bit(12)).multiple_of(32)` produces a struct with total serialized width of 32 bits (4 bytes), with 8 bits of trailing alignment padding. The SV `LP_*_WIDTH` remains 17 (data-only). `LP_*_BYTE_COUNT` becomes 4.
- **AC-2:** `Struct().add_member("a", Bit(5)).add_member("b", Bit(12)).multiple_of(24)` produces a struct with total serialized width of 24 bits (3 bytes), with 0 bits of trailing alignment padding (natural width already satisfies alignment).
- **AC-3:** `multiple_of(0)`, `multiple_of(-1)`, `multiple_of(5)` (not multiple of 8), and `multiple_of(3)` all raise `ValidationError`.
- **AC-4:** `multiple_of(True)` raises `ValidationError` (bool rejected).
- **AC-5:** Calling `multiple_of` twice raises `ValidationError`.
- **AC-6:** Calling `add_member` after `multiple_of` raises `ValidationError`.
- **AC-7:** All existing golden-file tests pass unchanged.
- **AC-8:** New golden-file test(s) cover the `multiple_of` feature with at least: (a) a struct that needs trailing padding, (b) a struct where natural width already meets the alignment.
- **AC-9:** SV `pack`/`unpack` round-trip correctly for aligned structs (data-only width, alignment pad excluded).
- **AC-10:** `to_bytes`/`from_bytes` round-trips correctly in all backends (SV, C++, Python), treating trailing pad as zero-filled unsigned padding.
- **AC-11:** `basedpyright` strict mode passes with zero errors.
- **AC-12:** Negative tests exist as `unittest.TestCase` methods covering: invalid `N` values (AC-3, AC-4), duplicate `multiple_of` (AC-5), and `add_member` after `multiple_of` (AC-6), each asserting `ValidationError` with a descriptive message substring.

---

## Out of Scope

- **Per-field alignment.** This feature aligns the total struct width only, not individual fields.
- **Sub-byte alignment.** `N` must be a multiple of 8; sub-byte alignment granularity is not supported.
- **Nested struct alignment propagation.** If a struct with `multiple_of` is used as a field in another struct, the outer struct sees the aligned width (including trailing pad). No special propagation logic is needed — the IR already accounts for the full byte count.
- **Runtime (dynamic) alignment.** Alignment is a static property set at DSL definition time.

---

## Open Questions

None. The feature is well-defined and self-contained.
