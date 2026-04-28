# Implementation Plan — Spec 003: Struct `multiple_of(N)` Alignment

## Overview

This plan follows the constitution's 7-step process: DSL → IR → freeze → validate → backends → fixture → test.

---

## Step 1: DSL — Add `multiple_of(N)` to `StructType`

**File:** `src/typist/dsl/struct.py`

**Changes:**
1. Add `_alignment: int | None` as a declared dataclass field on `StructType` (required because `slots=True` generates `__slots__` from annotations).
2. Initialize `self._alignment = None` in `__init__`.
3. Add `multiple_of(self, n: int) -> StructType` method:
   - Validate: `type(n) is not int or isinstance(n, bool)` → reject bool and non-int.
   - Validate: `n > 0`.
   - Validate: `n % 8 == 0`.
   - Validate: `self._alignment is None` (no duplicate calls).
   - Set `self._alignment = n`.
   - Return `self`.
4. Guard `add_member`: at the top, `if self._alignment is not None: raise ValidationError("cannot add members after multiple_of()")`.

**No `_alignment_locked` needed** — `_alignment is not None` is the lock.

---

## Step 2: IR — Add `alignment_bits` to `StructIR`

**File:** `src/typist/ir/nodes.py`

**Changes:**
1. Add `alignment_bits: int = 0` field to `StructIR` frozen dataclass (after `fields`).

Backward-compatible — default `0` means existing IR construction is unaffected.

---

## Step 3: Freeze — Compute `alignment_bits` during struct freeze

**File:** `src/typist/dsl/freeze.py`

**Design:** Compute alignment from the **mutable DSL objects** before constructing `StructIR`. This avoids any dependency on freeze ordering or IR availability.

**New helper functions:**

```python
def _compute_alignment_bits(struct_type: StructType) -> int:
    """Compute trailing alignment padding bits for a struct."""
    if struct_type._alignment is None:
        return 0
    natural_width = _serialized_width_from_dsl(struct_type)
    return (-natural_width) % struct_type._alignment

def _serialized_width_from_dsl(struct_type: StructType) -> int:
    """Compute serialized bit width of a struct from DSL objects (recursive)."""
    total = 0
    for member in struct_type.members:
        if isinstance(member.type, ScalarType):
            total += byte_count(member.type.width_value) * 8
        elif isinstance(member.type, StructType):
            inner_width = _serialized_width_from_dsl(member.type)
            inner_align = _compute_alignment_bits(member.type)
            total += inner_width + inner_align
    return total
```

**Key insight:** This works on DSL `StructType` objects, not IR. `ScalarType` always has `width_value` (both inline and named aliases — the DSL `StructMember.type` is always the actual `ScalarType` or `StructType` object, even for named aliases). This is ordering-independent and handles all field type variants.

**Integration:** In `freeze_module`, where `StructIR` is constructed (line ~151-163):
```python
alignment_bits = _compute_alignment_bits(value)
local_types.append(StructIR(..., alignment_bits=alignment_bits))
```

---

## Step 4: Validate — Add `alignment_bits` integrity check

**File:** `src/typist/validate/engine.py`

**Changes:**
1. Add `_validate_alignment_bits` function:
   - For each `StructIR`: if `alignment_bits > 0`, assert `alignment_bits % 8 == 0`.
2. Call it from `validate_repo` after `_validate_generated_identifier_collision` (line 83).

---

## Step 5: Backends — Update SV, C++, Python emitters

### Step 5a: SV synthesizable package (`src/typist/backends/sv/emitter.py`)

**`_render_sv_struct` (line 137):**
- After field loop (before closing `}}`), if `type_ir.alignment_bits > 0`:
  - Add `logic [alignment_bits-1:0] _align_pad;` (or `logic _align_pad;` if 1 bit).

**`_type_byte_count` (line 625):**
- For `StructIR`: return `sum(field_byte_counts) + type_ir.alignment_bits // 8`.

### Step 5b: SV verification package (same file)

**`_render_sv_struct_helper_class` (line 351):**
- `to_slv()`: After all fields, add `packed_value._align_pad = '0;`.
- `to_bytes`: After all field steps, if `alignment_bits > 0`: write zero bytes for alignment padding.
- `from_bytes`: After all field steps, advance `byte_idx` past alignment bytes (consume and ignore).

### Step 5c: C++ backend (`src/typist/backends/cpp/emitter.py`)

**`_type_byte_count` (line 782):**
- For `StructIR`: return `sum(field_byte_counts) + type_ir.alignment_bits // 8`.

**`_render_cpp_struct` (line 340):**
- `to_bytes()`: After all pack steps, if `alignment_bits > 0`: `for (...) result.push_back(0);`.
- `from_bytes()`: Size validation already at top. Alignment bytes are implicitly ignored at the tail.

### Step 5d: Python backend (`src/typist/backends/py/emitter.py`)

**`_type_byte_count` (line 565):**
- For `StructIR`: return `sum(field_byte_counts) + type_ir.alignment_bits // 8`.

**`_render_py_struct` (line 301):**
- `struct_byte_count` computation (line 305-307): add `type_ir.alignment_bits // 8`.

**`_render_py_struct_to_bytes` (line 350):**
- After all field steps: `result.extend(b'\\x00' * {alignment_bytes})`.

**`_render_py_struct_from_bytes` (line 399):**
- Size validation at top. Alignment bytes implicitly ignored at tail.

---

## Step 6: Test fixtures

**Fixture:** `tests/fixtures/struct_multiple_of/project/alpha/typist/types.py`

```python
from typist.dsl import Logic, Struct

# Case (a): struct that needs trailing padding (natural=24, aligned=32)
inner_t = Logic(3)
aligned_t = (
    Struct()
    .add_member("a", Logic(5))
    .add_member("b", Logic(12))
    .multiple_of(32)
)

# Case (b): struct where natural width already meets alignment (24 % 24 == 0)
no_extra_pad_t = (
    Struct()
    .add_member("a", Logic(5))
    .add_member("b", Logic(12))
    .multiple_of(24)
)

# Case (c): nested — inner aligned struct as field in outer struct
inner_aligned_t = (
    Struct()
    .add_member("x", inner_t)
    .multiple_of(16)
)
outer_t = (
    Struct()
    .add_member("inner", inner_aligned_t)
    .add_member("y", Logic(8))
)
```

**Golden files:** Run `typist gen`, verify output, commit to `tests/goldens/gen/struct_multiple_of/`.

---

## Step 7: Tests

**Golden-file integration test:** Add `test_struct_multiple_of` to the existing test infrastructure.

**Negative unit tests:** `tests/test_struct_multiple_of.py`

| Test method | Input | Expected error substring |
|---|---|---|
| `test_multiple_of_zero` | `multiple_of(0)` | `"must be positive"` |
| `test_multiple_of_negative` | `multiple_of(-8)` | `"must be positive"` |
| `test_multiple_of_not_multiple_of_8_val_5` | `multiple_of(5)` | `"must be a multiple of 8"` |
| `test_multiple_of_not_multiple_of_8_val_3` | `multiple_of(3)` | `"must be a multiple of 8"` |
| `test_multiple_of_bool` | `multiple_of(True)` | `"must be int"` |
| `test_multiple_of_twice` | `.multiple_of(32).multiple_of(64)` | `"already set"` |
| `test_add_member_after_multiple_of` | `.multiple_of(32).add_member(...)` | `"cannot add"` |

**Runtime round-trip test:** After `typist gen`, import generated Python module, verify `to_bytes`/`from_bytes` round-trip with correct byte count for the aligned struct.

---

## Execution Order

1. Steps 1-2: DSL + IR (foundation)
2. Step 3: Freeze (connects DSL to IR)
3. Step 4: Validate (safety net)
4. Steps 5a-5d: Backends (independent of each other)
5. Steps 6-7: Fixtures + tests (verification)
