# Implementation Plan — Spec 003: Struct `multiple_of(N)` Alignment

## Overview

This plan follows the constitution's 7-step process for adding a new feature: DSL → IR → freeze → validate → backends → fixture → test. Each step is a self-contained unit that can be committed independently.

---

## Step 1: DSL — Add `multiple_of(N)` to `StructType`

**File:** `src/typist/dsl/struct.py`

**Changes:**
1. Add `_alignment: int | None` field to `StructType.__init__` (initialized to `None`).
2. Add `_alignment_locked: bool` field (initialized to `False`) — tracks whether `multiple_of` has been called.
3. Add `multiple_of(self, n: int) -> StructType` method:
   - Validate: `type(n) is int` (rejects `bool`), `n > 0`, `n % 8 == 0`.
   - Validate: `_alignment_locked` is `False` (no duplicate calls).
   - Set `self._alignment = n`, `self._alignment_locked = True`.
   - Return `self`.
4. Guard `add_member`: if `self._alignment_locked`, raise `ValidationError`.

**No other files change in this step.**

---

## Step 2: IR — Add `alignment_bits` to `StructIR`

**File:** `src/typist/ir/nodes.py`

**Changes:**
1. Add `alignment_bits: int = 0` field to `StructIR` dataclass (after `fields`).

This is a backward-compatible addition — default `0` means no alignment, so all existing IR construction is unaffected.

---

## Step 3: Freeze — Compute `alignment_bits` during struct freeze

**File:** `src/typist/dsl/freeze.py`

**Changes:**
1. In the `freeze_module` function, where `StructIR` is constructed (lines 151-163):
   - After freezing all fields, compute `natural_width`:
     - For each field: if scalar, `byte_count(data_width) * 8`. If struct-ref, look up the target `StructIR` and use its total serialized width (sum of per-field byte-counts * 8 + target's own `alignment_bits`).
   - If `value._alignment is not None`: compute `alignment_bits = (-natural_width) % value._alignment`.
   - Otherwise: `alignment_bits = 0`.
   - Pass `alignment_bits=alignment_bits` to `StructIR(...)`.

2. To support the recursive width calculation, we need the target struct's `alignment_bits`. This means structs must be frozen in dependency order (which they already are — the constitution guarantees dependency-first ordering). We'll build a local map of `struct_name -> StructIR` during freeze to look up inner struct alignment_bits.

**Key concern:** The current `freeze_module` freezes all structs in a single pass over `module.__dict__`. If struct A references struct B (both in the same module), we need B's `StructIR` to be available when freezing A. The existing code relies on declaration order, and the constitution says ordering is dependency-first. The fix: build a `frozen_structs: dict[int, StructIR]` keyed by `id(value)` and look up targets during alignment computation.

---

## Step 4: Validate — Add `alignment_bits` integrity check

**File:** `src/typist/validate/engine.py`

**Changes:**
1. Add `_validate_alignment_bits` function:
   - For each `StructIR` in each module: if `alignment_bits > 0`, assert `alignment_bits % 8 == 0`.
   - Error message: `"struct {name} alignment_bits {n} is not a multiple of 8"`.
2. Call it from `validate_repo` after `_validate_generated_identifier_collision`.

---

## Step 5: Backends — Update SV, C++, Python emitters

### Step 5a: SV synthesizable package (`src/typist/backends/sv/emitter.py`)

**`_render_sv_struct` (line 137):**
- After the field loop (line 147), if `type_ir.alignment_bits > 0`:
  - Add `logic [alignment_bits-1:0] _align_pad;` as the last field.

**`_type_byte_count` (line 625):**
- For `StructIR`: add `type_ir.alignment_bits // 8` to the sum.

**`_render_sv_pack_fn` (line 163):**
- No change. Pack operates on data-only width. `_data_width` is unchanged.

**`_render_sv_unpack_fn` (line 191):**
- No change. Unpack operates on data-only width.

### Step 5b: SV verification package (`src/typist/backends/sv/emitter.py`)

**`_render_sv_struct_helper_class` (line 351):**
- `to_slv()` (line 374): After all fields, if `alignment_bits > 0`: `packed_value._align_pad = '0;`
- `from_slv()` (line 391): No change (we don't extract `_align_pad` into any user field).
- `to_bytes` (line 399): After all field steps, append zero bytes for alignment padding:
  ```
  for (int i = 0; i < alignment_bytes; i++) bytes[byte_idx + i] = 8'h00;
  byte_idx += alignment_bytes;
  ```
- `from_bytes` (line 411): After all field steps, advance `byte_idx` by alignment_bytes (consume and ignore).

### Step 5c: C++ backend (`src/typist/backends/cpp/emitter.py`)

**`_type_byte_count` (line 782):**
- For `StructIR`: add `type_ir.alignment_bits // 8` to the sum.

**`_render_cpp_struct` (line 340):**
- `kByteCount` at line 349 already uses `_type_byte_count`, so it automatically picks up the alignment.
- `to_bytes()` (line 358): After all pack steps, append zero bytes:
  ```cpp
  for (std::size_t i = 0; i < alignment_bytes; ++i) result.push_back(0);
  ```
- `from_bytes()` (line 370): The offset tracking already advances past all field bytes. After all unpack steps, the offset will be at `kByteCount - alignment_bytes`. No explicit skip needed because the size validation at the top already ensures the full buffer is consumed.

Actually, looking more carefully: the from_bytes validates `bytes.size() == kByteCount` at the top and then unpacks fields. Since the alignment bytes are at the end and we only read field bytes, the offset will end at `kByteCount - alignment_bytes`. That's fine — the alignment bytes are implicitly ignored because we validated size upfront and don't read past the fields.

### Step 5d: Python backend (`src/typist/backends/py/emitter.py`)

**`_type_byte_count` (line 565):**
- For `StructIR`: add `type_ir.alignment_bits // 8` to the sum.

**`_render_py_struct` (line 301):**
- `BYTE_COUNT` at line 312 already uses the `_field_byte_count` sum inline. Need to add `type_ir.alignment_bits // 8` to this sum.

**`_render_py_struct_to_bytes` (line 350):**
- After all field steps, if `alignment_bits > 0`: `result.extend(b'\x00' * alignment_bytes)`.

**`_render_py_struct_from_bytes` (line 399):**
- Validates `len(raw) != BYTE_COUNT` at the top. After all field steps, the offset lands at `BYTE_COUNT - alignment_bytes`. The alignment bytes are implicitly ignored. No explicit skip needed.

---

## Step 6: Test fixtures

**New fixture:** `tests/fixtures/struct_multiple_of/project/typist/types.py`

```python
from typist import Struct, Bit, UBit

# Case (a): struct that needs trailing padding
aligned_t = Struct().add_member("a", Bit(5)).add_member("b", Bit(12)).multiple_of(32)

# Case (b): struct where natural width already meets alignment
no_extra_pad_t = Struct().add_member("a", Bit(5)).add_member("b", Bit(12)).multiple_of(24)

# Case (c): nested — inner aligned struct as field in outer struct
inner_t = Struct().add_member("x", UBit(3)).multiple_of(16)
outer_t = Struct().add_member("inner", inner_t).add_member("y", Bit(8))
```

**Golden files:** Generate and commit golden outputs for all 3 backends (SV, C++, Python) under `tests/goldens/gen/struct_multiple_of/`.

---

## Step 7: Tests

**Golden-file integration test:** Add `test_struct_multiple_of` case to the existing test infrastructure.

**Negative unit tests:** New `tests/test_struct_multiple_of.py` with:
- `test_multiple_of_zero` — `ValidationError`
- `test_multiple_of_negative` — `ValidationError`
- `test_multiple_of_not_multiple_of_8` — `ValidationError("must be a multiple of 8")`
- `test_multiple_of_bool` — `ValidationError`
- `test_multiple_of_twice` — `ValidationError("already set")`
- `test_add_member_after_multiple_of` — `ValidationError`

**Runtime round-trip test:** After generating the Python module, import it and verify `to_bytes`/`from_bytes` round-trip with correct byte count.

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Freeze order for nested structs with alignment | Constitution guarantees dependency-first ordering; verify with test case (c) |
| Existing golden files break | `alignment_bits=0` default means no output change for existing structs |
| Type checker errors | `alignment_bits: int = 0` on frozen dataclass is basedpyright-safe |

## Execution Order

Steps 1-4 (DSL → IR → freeze → validate) should be done first as a foundation. Steps 5a-5d (backends) are independent of each other and can be done in any order. Steps 6-7 (fixtures + tests) come last.
