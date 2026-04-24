# Tasks: Byte-Aligned Packed Struct Code Generation

**Spec ID:** 001-byte-aligned-struct-codegen  
**Date:** 2026-04-24  

---

## Phase 1: IR + Freeze + Validation (Foundation)

### Task 1: Add centralized layout helpers

**Description:** Create integer-only helper functions for byte-count and padding-bits computation. These MUST be used by freeze and all backends — never inline the arithmetic.

**Files to modify:**
- `src/typist/ir/nodes.py` — add `byte_count(width)` and `padding_bits(width)` functions

**Dependencies:** None  

**Verification:**
- `byte_count(1) == 1`, `byte_count(8) == 1`, `byte_count(9) == 2`, `byte_count(64) == 8`, `byte_count(65) == 9`, `byte_count(128) == 16`
- `padding_bits(1) == 7`, `padding_bits(8) == 0`, `padding_bits(13) == 3`, `padding_bits(65) == 7`
- basedpyright passes on modified file

### Task 2: Add `padding_bits` field to `StructFieldIR`

**Description:** Add `padding_bits: int` field (default 0) to the frozen `StructFieldIR` dataclass. This is consumed by freeze, validation, and all backend emitters.

**Files to modify:**
- `src/typist/ir/nodes.py` — add field to `StructFieldIR`

**Dependencies:** Task 1  

**Verification:**
- `StructFieldIR` constructor accepts `padding_bits` keyword
- Default value is 0
- basedpyright passes

### Task 3: Compute `padding_bits` in freeze pipeline

**Description:** In `_freeze_struct_field()`, compute padding using the centralized helper: scalar fields get `(-resolved_width) % 8`, struct-typed fields get 0. Pass to `StructFieldIR` constructor.

**Files to modify:**
- `src/typist/dsl/freeze.py` — update `_freeze_struct_field()`

**Dependencies:** Task 1, Task 2  

**Verification:**
- 1-bit field → padding_bits=7
- 13-bit field → padding_bits=3
- 8-bit field → padding_bits=0
- Struct-typed field → padding_bits=0
- basedpyright passes

### Task 4: Add validation rule — `_pad` suffix reservation (FR-11)

**Description:** Reject struct fields whose name ends with `_pad`. Run during existing validation pass.

**Files to modify:**
- `src/typist/validate/engine.py` — add `_pad` suffix check

**Dependencies:** Task 2  

**Verification:**
- Field `foo_pad` → error containing `"reserved '_pad' suffix"`
- Field `foo` → no error
- basedpyright passes

### Task 5: Add validation rule — signed scalar width >64 (FR-13)

**Description:** Reject signed scalar types with width > 64. Accept unsigned scalars of any width. Apply to both named aliases and inline struct fields.

**Files to modify:**
- `src/typist/validate/engine.py` — add signed width constraint

**Dependencies:** Task 2  

**Verification:**
- `LogicSigned(65)` named → error containing `"exceeds maximum 64-bit signed width"`
- `LogicSigned(65)` inline → error containing `"exceeds maximum 64-bit signed width"`
- `Logic(128)` named → no error
- `Logic(128)` inline → no error
- basedpyright passes

### Task 6: Add validation rule — generated identifier collision (FR-14)

**Description:** For each type in a module, check if any user-defined constant name (after SV transform) collides with reserved generated identifiers: `LP_<UPPER>_WIDTH`, `LP_<UPPER>_BYTE_COUNT`, `pack_<base>`, `unpack_<base>`.

**Files to modify:**
- `src/typist/validate/engine.py` — add identifier collision check

**Dependencies:** Task 2  

**Verification:**
- Module with `LP_FOO_WIDTH = Const(42)` and `foo_t = Logic(13)` → error containing `"collides with generated identifier"`
- Module with no collisions → no error
- basedpyright passes

### Task 7: Add negative test fixtures for validation rules

**Description:** Create test fixture repos and test cases for FR-11, FR-13, FR-14 negative validation.

**Files to create:**
- `tests/fixtures/struct_pad_collision/project/typist/types.py` — struct with `_pad` field
- `tests/fixtures/scalar_signed_wide/project/typist/types.py` — LogicSigned(65)
- `tests/fixtures/const_collision/project/typist/types.py` — constant name collision
- Test cases in appropriate test file

**Dependencies:** Tasks 4, 5, 6  

**Verification:**
- Each negative fixture triggers the expected error message
- Each test exits with non-zero exit code
- Tests pass in test suite

### Task 8: Update existing golden files for IR change

**Description:** The `padding_bits` field in `StructFieldIR` may affect serialized IR or any output that depends on IR shape. Regenerate all existing golden files and verify byte-for-byte match.

**Files to modify:**
- `tests/goldens/gen/struct_sv_basic/` — all backends
- `tests/goldens/gen/scalar_sv_basic/` — all backends
- `tests/goldens/gen/nested_struct_sv_basic/` — all backends

**Dependencies:** Tasks 1, 2, 3  

**Verification:**
- `typist gen` on each existing fixture produces updated output
- All existing golden tests pass
- Idempotency check passes

---

## Phase 2: SV Backend — Synthesizable Package

### Task 9: Emit WIDTH and BYTE_COUNT localparams (FR-4)

**Description:** For every type (scalar and struct), emit `LP_<UPPER_BASE>_WIDTH` and `LP_<UPPER_BASE>_BYTE_COUNT` localparams. Scalar typedefs reference the WIDTH localparam.

**Files to modify:**
- `src/typist/backends/sv/emitter.py` — add localparam emission

**Dependencies:** Tasks 1, 2, 3  

**Verification:**
- `foo_t` (Logic(13)) → `LP_FOO_WIDTH = 13`, `LP_FOO_BYTE_COUNT = 2`
- `bar_t` (struct) → `LP_BAR_WIDTH = 19`, `LP_BAR_BYTE_COUNT = 5`
- Scalar typedef uses `LP_FOO_WIDTH-1:0` in range
- basedpyright passes

### Task 10: Emit `_pad` members in struct typedef (FR-3)

**Description:** For each struct field with `padding_bits > 0`, emit `logic [P-1:0] <field_name>_pad;` immediately above the field. 1-bit padding uses `logic <field_name>_pad;`. Struct-typed fields get no padding.

**Files to modify:**
- `src/typist/backends/sv/emitter.py` — modify `_render_sv_struct()`

**Dependencies:** Tasks 2, 3, 9  

**Verification:**
- `bar_t` typedef includes `flag_a_pad[6:0]`, `field_1_pad[2:0]`, `status_pad[3:0]`, `flag_b_pad[6:0]`
- Nested struct: no `payload_pad` for struct-typed field
- basedpyright passes

### Task 11: Emit pack/unpack functions (FR-5)

**Description:** Emit `pack_<base>` and `unpack_<base>` standalone functions in the synthesizable package. Scalar types get identity pass-through. Struct types: pack concatenates data fields MSB-first; unpack extracts LSB-first with sign extension for signed fields.

**Files to modify:**
- `src/typist/backends/sv/emitter.py` — add pack/unpack emission

**Dependencies:** Tasks 9, 10  

**Verification:**
- Scalar: `pack_foo(a)` returns `a`; `unpack_foo(a)` returns `a`
- Struct: `pack_bar` concatenates `{a.flag_a, pack_foo(a.field_1), a.status, a.flag_b}`
- `unpack_bar` initializes to `'0`, extracts fields, sign-extends `_pad` for signed fields
- basedpyright passes

### Task 12: Update SV golden files and add `struct_padded` fixture

**Description:** Update all existing SV golden files for the new synthesizable package output. Create new `struct_padded` fixture with mixed-width members (1, 13, 4, 1 bits).

**Files to modify/create:**
- `tests/goldens/gen/*/sv/` — update all existing SV goldens
- `tests/fixtures/struct_padded/project/typist/types.py` — new fixture
- `tests/goldens/gen/struct_padded/sv/` — new golden

**Dependencies:** Tasks 9, 10, 11  

**Verification:**
- All SV golden tests pass
- `struct_padded` golden shows `_pad` members, localparams, pack/unpack functions

---

## Phase 3: SV Backend — Verification Package

### Task 13: Rewrite SV `to_slv()` / `from_slv()` with padding (FR-10a)

**Description:** Rewrite the verification helper class methods: `to_slv()` assembles typedef with `_pad` fields (zero for unsigned, sign-extended for signed). `from_slv()` extracts field values, ignoring padding.

**Files to modify:**
- `src/typist/backends/sv/emitter.py` — modify verification helper class emission

**Dependencies:** Tasks 9, 10  

**Verification:**
- `to_slv()` output for unsigned fields has zero `_pad`
- `to_slv()` for signed fields has sign-extended `_pad`
- `from_slv()` ignores padding values
- basedpyright passes

### Task 14: Rewrite SV `to_bytes()` / `from_bytes()` with per-field serialization (FR-6)

**Description:** Serialize per-field into individual byte counts (big-endian). Unsigned: zero-pad MSB. Signed: sign-extend. `from_bytes()` validates signed padding, errors on mismatch.

**Files to modify:**
- `src/typist/backends/sv/emitter.py` — modify verification helper class emission

**Dependencies:** Task 13  

**Verification:**
- `bar_t.to_bytes()` produces `{0x01, 0x1F, 0xFF, 0x0A, 0x00}` for worked example
- `from_bytes()` with mismatched signed padding triggers error
- basedpyright passes

### Task 15: Update SV verification golden files

**Description:** Update all SV verification (test_pkg) golden files for rewritten to_slv/from_slv/to_bytes/from_bytes.

**Files to modify:**
- `tests/goldens/gen/*/sv/` — update test_pkg goldens

**Dependencies:** Tasks 13, 14  

**Verification:**
- All SV golden tests pass

---

## Phase 4: C++ Backend

### Task 16: Add `kWidth` / `kByteCount` to C++ scalar and struct classes (FR-7, FR-8)

**Description:** Add `static constexpr std::size_t kWidth` and `kByteCount` to all generated C++ wrapper classes (scalar and struct).

**Files to modify:**
- `src/typist/backends/cpp/emitter.py` — add constants to class generation

**Dependencies:** Tasks 1, 2, 3  

**Verification:**
- 13-bit scalar: `kWidth = 13`, `kByteCount = 2`
- Struct: `kWidth = 19`, `kByteCount = 5`
- basedpyright passes

### Task 17: Implement wide scalar C++ support (FR-7, >64-bit)

**Description:** For unsigned scalars with width > 64, use `std::vector<std::uint8_t>` as `value_type`. Implement normalized invariant (vector length = `kByteCount`, MSB padding cleared). Handle both named aliases and inline anonymous scalars.

**Files to modify:**
- `src/typist/backends/cpp/emitter.py` — add wide scalar wrapper class generation

**Dependencies:** Task 16  

**Verification:**
- 128-bit unsigned: `value_type = std::vector<std::uint8_t>`
- Constructor clears MSB padding bits
- `to_bytes()` returns vector directly
- `from_bytes()` masks padding
- basedpyright passes

### Task 18: Rewrite C++ `to_bytes()` / `from_bytes()` (FR-7, FR-8)

**Description:** Per-field byte serialization (big-endian) with signedness-dependent padding fill. Signed validation throws `std::invalid_argument` on mismatch.

**Files to modify:**
- `src/typist/backends/cpp/emitter.py` — rewrite serialization in scalar and struct classes

**Dependencies:** Tasks 16, 17  

**Verification:**
- Unsigned: zero MSB padding in `to_bytes()`
- Signed: sign-extended padding in `to_bytes()`
- `from_bytes()` validates signed padding
- basedpyright passes

### Task 19: Update C++ golden files and add wide scalar fixture

**Description:** Update all existing C++ golden files. Create `scalar_wide` fixture (65-bit and 128-bit unsigned) and `struct_wide` fixture (65-bit member + 1-bit flag).

**Files to modify/create:**
- `tests/goldens/gen/*/cpp/` — update all existing C++ goldens
- `tests/fixtures/scalar_wide/project/typist/types.py` — new fixture
- `tests/fixtures/struct_wide/project/typist/types.py` — new fixture
- `tests/goldens/gen/scalar_wide/cpp/` — new golden
- `tests/goldens/gen/struct_wide/cpp/` — new golden

**Dependencies:** Tasks 16, 17, 18  

**Verification:**
- All C++ golden tests pass
- Wide scalar golden shows `std::vector<std::uint8_t>` type

---

## Phase 5: Python Backend

### Task 20: Add `WIDTH` / `BYTE_COUNT` to Python scalar and struct classes (FR-9)

**Description:** Add `WIDTH` and `BYTE_COUNT` class variables to all generated Python wrapper classes.

**Files to modify:**
- `src/typist/backends/py/emitter.py` — add class variables

**Dependencies:** Tasks 1, 2, 3  

**Verification:**
- 13-bit scalar: `WIDTH = 13`, `BYTE_COUNT = 2`
- Struct: `WIDTH = 19`, `BYTE_COUNT = 5`
- basedpyright passes

### Task 21: Rewrite Python `to_bytes()` / `from_bytes()` (FR-9)

**Description:** Per-field byte serialization (big-endian) with signedness-dependent padding fill. Signed validation raises `ValueError` on mismatch. Works for arbitrary-width unsigned scalars (Python `int` handles it natively).

**Files to modify:**
- `src/typist/backends/py/emitter.py` — rewrite serialization in scalar and struct classes

**Dependencies:** Task 20  

**Verification:**
- Unsigned: zero MSB padding in `to_bytes()`
- Signed: sign-extended padding in `to_bytes()`
- `from_bytes()` validates signed padding
- Arbitrary-width unsigned (>64) works correctly
- basedpyright passes

### Task 22: Update Python golden files

**Description:** Update all existing Python golden files. Add goldens for new fixtures (`struct_padded`, `struct_signed`, `scalar_wide`, `struct_wide`).

**Files to modify:**
- `tests/goldens/gen/*/py/` — update all existing Python goldens
- `tests/goldens/gen/struct_padded/py/` — new golden
- `tests/goldens/gen/struct_signed/py/` — new golden
- `tests/goldens/gen/scalar_wide/py/` — new golden
- `tests/goldens/gen/struct_wide/py/` — new golden

**Dependencies:** Tasks 20, 21  

**Verification:**
- All Python golden tests pass

---

## Phase 6: Cross-Language Verification + Final Testing

### Task 23: Create `struct_signed` test fixture

**Description:** Create fixture with signed scalar struct members (4-bit signed, 5-bit signed) for AC-16/21/22/23.

**Files to create:**
- `tests/fixtures/struct_signed/project/typist/types.py`
- `tests/goldens/gen/struct_signed/sv/` — SV golden
- `tests/goldens/gen/struct_signed/cpp/` — C++ golden

**Dependencies:** Tasks 11, 14, 18, 21  

**Verification:**
- SV golden shows sign-extended `_pad` in unpack, sign-extended to_bytes
- C++ golden shows sign-extended serialization
- All three backend goldens consistent

### Task 24: Complete all golden files for new fixtures

**Description:** Ensure all new fixtures (`struct_padded`, `struct_signed`, `scalar_wide`, `struct_wide`) have complete golden files across all three backends plus test packages.

**Files to create/verify:**
- Complete golden trees for all new fixtures across sv/, cpp/, py/ directories

**Dependencies:** Tasks 12, 15, 19, 22, 23  

**Verification:**
- `typist gen` on each fixture produces output matching goldens
- All golden tests pass

### Task 25: Create `tests/test_runtime_bytes.py` — executable Python runtime tests

**Description:** Create unittest-based test file that imports generated Python modules and verifies `to_bytes()`/`from_bytes()` with spec-derived test vectors. This is the primary executable verification of cross-language byte consistency (FR-10).

**Test vectors from spec:**
- `bar_t(flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0)` → `b'\x01\x1f\xff\x0a\x00'`
- Signed 5-bit `-1` → `b'\xff'`; signed 5-bit `+5` → `b'\x05'`
- Signed 4-bit `-6` → `b'\xfa'`
- 65-bit unsigned all-ones → `b'\x01' + b'\xff' * 8`
- `from_bytes({0x0A})` for 4-bit signed → `ValueError`
- `from_bytes({0x81, ...})` for unsigned → accepted (padding ignored)

**Files to create:**
- `tests/test_runtime_bytes.py`

**Dependencies:** Tasks 22, 24  

**Verification:**
- All runtime tests pass
- Tests fail if byte order is wrong (regression anchor)

### Task 26: Run full test suite and basedpyright

**Description:** Final verification: run all golden tests, negative tests, runtime tests, idempotency tests, and basedpyright strict mode on all modified files.

**Files to check:**
- All modified source files under `src/typist/`
- All test files

**Dependencies:** Tasks 24, 25  

**Verification:**
- All golden tests pass (AC-10)
- All negative tests pass (AC-13, AC-17, AC-18, AC-20)
- All runtime tests pass (AC-6, AC-12, AC-15, AC-16, AC-22, AC-23, AC-24, AC-25)
- Idempotency tests pass
- basedpyright strict mode: zero errors (NFR-6)
