# Tasks — Spec 007: Struct Accepts Flags as Member

## Task 1: Fix SV Flags helper `to_bytes()`/`from_bytes()` byte layout (FR-11)

**File:** `src/piketype/backends/sv/emitter.py`, function `_render_sv_flags_helper_class()`

**Changes:**
- In `to_bytes()` generation (line ~578-580): Change bit position from `num_flags - 1 - idx` to `total_bits - 1 - idx`.
- In `from_bytes()` generation (line ~601-603): Same change.

**Test:** Run `python -m pytest tests/test_gen_flags.py` — will fail until goldens updated.

**ACs:** AC-22, AC-23.

---

## Task 2: Regenerate `flags_basic` golden files (FR-11)

**Commands:**
```bash
cd /tmp && cp -r /Users/ezchi/Projects/pike-type/tests/fixtures/flags_basic/project . && cd project && piketype gen
```
Copy updated `gen/` output to `tests/goldens/gen/flags_basic/`.

Only `sv/alpha/piketype/types_test_pkg.sv` should change. Verify `_pkg.sv` is unchanged.

**Test:** `python -m pytest tests/test_gen_flags.py` — all flags tests pass.

**ACs:** AC-24, AC-26.

---

## Task 3: Accept FlagsType in `Struct.add_member()` (FR-1)

**File:** `src/piketype/dsl/struct.py`

**Changes:**
- Add import: `from piketype.dsl.flags import FlagsType`
- Change `StructMember.type` annotation: `ScalarType | StructType | FlagsType`
- Change `add_member()` parameter annotation: `type: ScalarType | StructType | FlagsType`
- Change isinstance check (line 55): `(ScalarType, StructType, FlagsType)`
- Update error message: `"struct member type must be a scalar, struct, or flags type in this milestone"`

**Test:** Manual — `Struct().add_member("f", Flags().add_flag("a"))` doesn't raise.

**ACs:** AC-1.

---

## Task 4: Handle FlagsType in `_freeze_field_type()` (FR-2)

**File:** `src/piketype/dsl/freeze.py`

**Changes:**
- Update `_freeze_field_type()` parameter annotation to include `FlagsType`.
- Add FlagsType to the anonymous-type rejection branch:
  ```python
  if isinstance(type_obj, (StructType, FlagsType)):
      raise ValidationError("inline anonymous ... member types are not supported in this milestone")
  ```
  (The named-type path via `type_definition_map` lookup already works generically.)

**Test:** Freeze a module with `Struct().add_member("f", named_flags_t)` — produces `TypeRefIR`.

**ACs:** AC-2, AC-4.

---

## Task 5: Handle FlagsType in `_serialized_width_from_dsl()` (FR-3)

**File:** `src/piketype/dsl/freeze.py`

**Changes:**
- Add `elif isinstance(member.type, FlagsType):` branch in `_serialized_width_from_dsl()`:
  ```python
  elif isinstance(member.type, FlagsType):
      total += byte_count(len(member.type.flags)) * 8
  ```

**Test:** `Struct().add_member("f", flags_3).multiple_of(32)` computes correct alignment.

**ACs:** AC-17, AC-18.

---

## Task 6: Extend validation allowlist for FlagsIR (FR-4)

**File:** `src/piketype/validate/engine.py`

**Changes:**
- Import `FlagsIR` if not already imported.
- Change struct field TypeRefIR target check from `(ScalarAliasIR, StructIR)` to `(ScalarAliasIR, StructIR, FlagsIR)`.
- Update error message to include "flags".

**Test:** Validation passes for a struct with a Flags member from the same module.

**ACs:** AC-3.

---

## Task 7: Generalize `_is_sv_struct_ref()` to include FlagsIR (FR-5, FR-6)

**File:** `src/piketype/backends/sv/emitter.py`

**Changes:**
- Rename `_is_sv_struct_ref` to `_is_sv_composite_ref` (or add FlagsIR to the check).
- Change: `isinstance(type_index[field_type.name], StructIR)` → `isinstance(type_index[field_type.name], (StructIR, FlagsIR))`.
- Import `FlagsIR`.
- Update all ~10 call sites that reference `_is_sv_struct_ref`.

**ACs:** AC-5, AC-6, AC-7, AC-8 (partial).

---

## Task 8: Fix `_render_sv_helper_field_decl()` for FlagsIR (FR-6)

**File:** `src/piketype/backends/sv/emitter.py`

**Changes:**
- At line 647, change `isinstance(target, StructIR)` to `isinstance(target, (StructIR, FlagsIR))`.
- This ensures Flags fields are declared as `<flags_helper_class> field;` not `flags_t field;`.

**ACs:** AC-8.

---

## Task 9: Add FlagsIR to Python `_resolved_type_width()` and `_type_byte_count()` (FR-8)

**File:** `src/piketype/backends/py/emitter.py`

**Changes:**
- In `_resolved_type_width()`: Add `if isinstance(type_ir, FlagsIR): return len(type_ir.fields)` before the existing fallthrough.
- In `_type_byte_count()`: Add `if isinstance(type_ir, FlagsIR): return (len(type_ir.fields) + type_ir.alignment_bits) // 8`.
- Import `FlagsIR`.

**ACs:** AC-15, AC-16.

---

## Task 10: Add FlagsIR handling in Python struct field emission (FR-7)

**File:** `src/piketype/backends/py/emitter.py`

**Changes in multiple functions:**
- `_render_py_field_annotation()`: Add FlagsIR branch returning class name (not nullable).
- `_render_py_field_default()`: Return `field(default_factory=<FlagsClassName>)`.
- `_render_py_struct_field_coercer()`: Add FlagsIR branch — isinstance check, reject None, raise TypeError.
- `_render_py_struct_to_bytes()`: Add FlagsIR branch — call `self.<field>.to_bytes()` (no None check).
- `_render_py_struct_from_bytes()`: Add FlagsIR branch — call `<FlagsClass>.from_bytes(raw[offset:offset+N])`.

**ACs:** AC-9, AC-10, AC-11, AC-12.

---

## Task 11: Add FlagsIR to C++ `_resolved_type_width()` and `_type_byte_count()` (FR-8)

**File:** `src/piketype/backends/cpp/emitter.py`

**Changes:** Same pattern as Task 9.

**ACs:** AC-15, AC-16.

---

## Task 12: Add FlagsIR handling in C++ struct field emission (FR-9)

**File:** `src/piketype/backends/cpp/emitter.py`

**Changes:**
- Field declaration: Use Flags C++ class name for FlagsIR TypeRefIR targets.
- `to_bytes()`: Call `<field>.to_bytes()` for Flags fields.
- `from_bytes()`: Default-construct field, then call `<field>.from_bytes(...)` (instance method, not static).
- Reference `BYTE_COUNT` constant.

**ACs:** AC-13, AC-14.

---

## Task 13: Create test fixture (FR-10)

**File:** `tests/fixtures/struct_flags_member/project/alpha/piketype/types.py`

**Content:**
```python
from piketype.dsl import Flags, Struct, Bit

status_t = Flags().add_flag("error").add_flag("warning").add_flag("ready")

report_t = (
    Struct()
    .add_member("status", status_t)
    .add_member("code", Bit(5))
)

aligned_report_t = (
    Struct()
    .add_member("flags", status_t)
    .add_member("data", Bit(3))
    .multiple_of(32)
)
```

---

## Task 14: Generate golden files and add integration test (FR-10)

Run `piketype gen` on the fixture, commit output as goldens. Add integration test case and idempotency test.

**ACs:** AC-20, AC-21.

---

## Task 15: Add Python runtime tests (FR-10)

**File:** `tests/test_runtime_bytes.py` (extend existing)

**Tests:**
- Round-trip: Create struct, set flags, to_bytes → from_bytes, verify equality.
- Expected bytes: Set specific flags, verify exact byte output value.
- Multiple_of: Verify `aligned_report_t` serialized byte count = 4 (32 bits).

**ACs:** AC-19, AC-25.

---

## Task 16: Add cross-module Flags member rejection test (FR-4, AC-27)

**File:** `tests/test_namespace_validation.py` (extend existing)

**Test:** Create a Flags type in one module and attempt to use it as a struct member in another module via the validation pipeline. Assert `ValidationError` with cross-module error message.

**ACs:** AC-27.

---

## Task 17: Final verification

Run full test suite: `python -m pytest`. All tests pass.

**ACs:** AC-26 (existing tests pass).

---

## Execution Order

```
Task 1 → Task 2 (FR-11 bug fix, golden update)
Task 3 → Task 4 → Task 5 (DSL + freeze)
Task 6 (validation)
Task 7 → Task 8 (SV backend)
Task 9 → Task 10 (Python backend)
Task 11 → Task 12 (C++ backend)
Task 13 → Task 14 → Task 15 → Task 16 → Task 17 (tests)
```

Tasks 3–6 depend on Tasks 1–2. Tasks 7–12 depend on Task 6. Tasks 13–17 depend on all prior tasks.
