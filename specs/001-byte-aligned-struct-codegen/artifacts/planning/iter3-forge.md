# Implementation Plan: Byte-Aligned Packed Struct Code Generation

**Spec ID:** 001-byte-aligned-struct-codegen  
**Date:** 2026-04-24  

## Architecture Overview

The change introduces per-member byte-aligned padding across the entire pipeline: IR, freeze, validation, and all three backends (SV, C++, Python). The core concept is that every scalar struct member is individually padded to a byte boundary, with padding bits placed on the MSB side. The padding fill policy (zero vs sign-extended) depends on the field's signedness and the consuming operation.

The existing pipeline flow is unchanged: Discovery → DSL → IR (freeze) → Validation → Backends. The change adds new data to the IR, new computation in freeze, new validation rules, and new emission logic in all backends.

## Components

### 1. IR Layer — `ir/nodes.py`

**Changes:**
- Add `padding_bits: int` field to `StructFieldIR` (frozen dataclass). Default 0. Represents the number of byte-alignment bits for this member.
- No changes to `StructIR`, `ScalarTypeSpecIR`, or `TypeRefIR`. `WIDTH` and `BYTE_COUNT` are derived quantities computed by backends, not stored in IR.

**Interfaces:**
- `StructFieldIR.padding_bits` is consumed by all three backend emitters and validation.
- The `signed` flag is already available on `ScalarTypeSpecIR` — backends use this to determine fill policy.

**Dependencies:** None. IR is a pure data model.

### 2. Freeze Layer — `dsl/freeze.py`

**Changes:**
- In `_freeze_struct_field()`: After resolving field type and width, compute `padding_bits` using the centralized integer helper:
  - Scalar field: `padding_bits = (-resolved_width) % 8`
  - Struct-typed field: `padding_bits = 0`
- Pass `padding_bits` to `StructFieldIR` constructor.

**Key logic — centralized integer-only helpers** (new module `ir/layout.py` or added to `ir/nodes.py`):
```python
def byte_count(width: int) -> int:
    """Number of bytes needed to hold `width` data bits."""
    return (width + 7) // 8

def padding_bits(width: int) -> int:
    """Number of MSB padding bits to reach the next byte boundary."""
    return (-width) % 8
```

These integer helpers avoid float division (`math.ceil(w / 8)`) which would silently miscompute for very large widths allowed by FR-13 (unsigned scalars > 64 bits). All freeze logic and backend computations MUST use these centralized helpers — never inline the arithmetic.

**Dependencies:** Requires IR change (step 1) to accept `padding_bits`.

### 3. Validation Layer — `validate/engine.py`

**New rules (3 total):**

1. **FR-11 — `_pad` suffix reservation:** For each struct, check if any field name ends with `_pad`. Reject with `"struct <name> field '<field>' uses reserved '_pad' suffix"`.

2. **FR-13 — Signed scalar width constraint:** For each scalar type (named or inline), if `signed=True` and `resolved_width > 64`, reject with `"signed scalar <name> width <w> exceeds maximum 64-bit signed width"` (named) or `"struct <struct_name> signed field '<field_name>' width <w> exceeds maximum 64-bit signed width"` (inline).

3. **FR-14 — Generated identifier collision:** For each type in a module, compute reserved identifiers (`LP_<UPPER_BASE>_WIDTH`, `LP_<UPPER_BASE>_BYTE_COUNT`, `pack_<base>`, `unpack_<base>`). Check if any user-defined constant name (after SV transform) collides. Reject with `"constant '<const_name>' collides with generated identifier for type '<type_name>'"`.

**Integration:** All three rules run during the existing validation pass in `engine.py`, after IR is frozen.

**Dependencies:** Requires IR (step 1) for field access. Uses existing module-level constant list and type list.

### 4. SV Backend — `backends/sv/emitter.py`

**Changes span 4 areas:**

#### 4a. Synthesizable Package — Struct Typedef (FR-3)
- In `_render_sv_struct()`: For each field with `padding_bits > 0`, emit a `logic [P-1:0] <field_name>_pad;` member immediately above the field. For 1-bit padding, emit `logic <field_name>_pad;`.
- Struct-typed fields (padding_bits == 0) emit no padding member.

#### 4b. Synthesizable Package — Localparams (FR-4)
- For every type (scalar and struct), emit `LP_<UPPER_BASE>_WIDTH` and `LP_<UPPER_BASE>_BYTE_COUNT`.
- WIDTH: for scalars = resolved_width; for structs = sum of field data widths (recursive).
- BYTE_COUNT: for scalars = ceil(WIDTH/8); for structs = sum of per-field byte counts.
- Scalar typedefs reference the WIDTH localparam: `typedef logic [LP_FOO_WIDTH-1:0] foo_t;`

#### 4c. Synthesizable Package — pack/unpack Functions (FR-5)
- For each type, emit `pack_<base>` and `unpack_<base>` functions.
- **Scalar types:** Identity pass-through.
- **Struct types:**
  - `pack`: Concatenate data fields only (skip `_pad`), MSB-first. Recursively call `pack_<inner>` for struct-typed fields.
  - `unpack`: Initialize result to `'0`. Extract fields LSB-first with bit-slice indexing. For signed scalar fields with padding: set `_pad = {P{field[W-1]}}`. For unsigned: padding stays 0.

#### 4d. Verification Package — to_bytes/from_bytes/to_slv/from_slv (FR-6, FR-10a)
- **`to_bytes()`:** Serialize per-field into individual byte counts. Unsigned: zero-pad MSB. Signed: sign-extend padding. Concatenate in declaration order.
- **`from_bytes()`:** Extract per-field from byte slices. Unsigned: mask padding. Signed: validate sign extension, error on mismatch.
- **`to_slv()`:** Assemble typedef with `_pad` fields — zero for unsigned, sign-extended for signed.
- **`from_slv()`:** Extract field values from typedef, ignore padding values.

**Width/offset computation helper:** Add a helper function that computes per-field bit offsets within the padded typedef (storage width), accounting for padding members. This replaces the current contiguous-packing assumption.

### 5. C++ Backend — `backends/cpp/emitter.py`

**Changes:**

#### 5a. Scalar Wrapper Classes (FR-7)
- Existing type mapping (width 1-64) unchanged.
- **New:** Width > 64 → `std::vector<std::uint8_t>` (unsigned only). Add `value_type` typedef, normalized invariant (length = `kByteCount`, MSB padding cleared), `to_bytes()` returns vector directly, `from_bytes()` masks padding.
- This applies to both **named scalar aliases** (e.g., `wide_t = Logic(128)`) and **inline anonymous scalars** in struct fields (e.g., `Struct().add_member("data", Logic(128))`). The C++ emitter must handle the >64-bit case for inline `ScalarTypeSpecIR` fields, not just named `ScalarAliasIR` types.
- Add `kWidth`, `kByteCount` static constexpr.
- **Serialization:** Unsigned: zero MSB padding. Signed (≤64): sign-extend padding.
- **Deserialization:** Unsigned: mask padding. Signed: validate sign extension, throw `std::invalid_argument` on mismatch.

#### 5b. Struct Classes (FR-8)
- Add `kWidth`, `kByteCount` static constexpr.
- `to_bytes()`: Per-field serialization into individual byte counts with signedness-dependent padding fill. Concatenate in declaration order.
- `from_bytes()`: Per-field extraction with validation for signed fields.

### 6. Python Backend — `backends/py/emitter.py`

**Changes:**

#### 6a. Scalar Wrapper Classes (FR-9)
- Add `WIDTH`, `BYTE_COUNT` class variables.
- `to_bytes()`: Big-endian, unsigned: zero-pad. Signed: sign-extend.
- `from_bytes()`: Unsigned: mask. Signed: validate sign extension, raise `ValueError`.
- Python `int` handles arbitrary width — no special type for > 64 bits.

#### 6b. Struct Dataclasses (FR-9)
- Add `WIDTH`, `BYTE_COUNT` class variables.
- `to_bytes()`: Per-field serialization with signedness-dependent padding.
- `from_bytes()`: Per-field extraction with signed validation.

## Data Model

```
StructFieldIR (frozen dataclass)
├── name: str
├── source: str
├── type_ir: FieldTypeIR  (ScalarTypeSpecIR | TypeRefIR)
├── rand: bool
└── padding_bits: int  ← NEW (>= 0)

Derived (computed by backends, not stored):
├── field_byte_count: ceil(resolved_width / 8) for scalars, inner BYTE_COUNT for structs
├── WIDTH (struct): sum of field data widths
└── BYTE_COUNT (struct): sum of field byte counts
```

## API Design

No public API changes. `Struct().add_member(name, type)` continues to work unchanged (NFR-3). Padding is computed automatically during freeze.

## Dependencies

- **External:** None new. Only stdlib + Jinja2 (NFR-5).
- **Internal:** Each phase depends on the prior:
  1. IR node change → enables freeze to store padding
  2. Freeze change → populates padding in IR
  3. Validation → consumes IR with padding
  4. Backends → consume IR with padding

## Implementation Strategy — Phased Approach

### Phase 1: IR + Freeze + Validation (Foundation)
1. Add `padding_bits` to `StructFieldIR` in `ir/nodes.py`.
2. Compute `padding_bits` in `dsl/freeze.py` `_freeze_struct_field()`.
3. Add validation rules in `validate/engine.py`:
   - FR-11: `_pad` suffix reservation
   - FR-13: Signed >64-bit rejection
   - FR-14: Generated identifier collision
4. Update existing golden files (StructFieldIR now carries `padding_bits`).
5. Add negative test fixtures for FR-11, FR-13, FR-14.

### Phase 2: SV Backend — Synthesizable Package
1. Emit localparams `LP_<BASE>_WIDTH` and `LP_<BASE>_BYTE_COUNT` (FR-4).
2. Modify struct typedef to include `_pad` members (FR-3).
3. Emit `pack_<base>` and `unpack_<base>` functions (FR-5) with sign-extension for signed fields.
4. Update existing SV golden files. Add new fixture for non-trivial padding.

### Phase 3: SV Backend — Verification Package
1. Rewrite `to_slv()` / `from_slv()` with per-field padding (FR-10a).
2. Rewrite `to_bytes()` / `from_bytes()` with per-field byte serialization (FR-6).
3. Implement signed padding validation in `from_bytes()`.
4. Update golden files.

### Phase 4: C++ Backend
1. Add `kWidth`, `kByteCount` to scalar and struct wrapper classes (FR-7, FR-8).
2. Implement wide scalar support (`std::vector<std::uint8_t>` for > 64-bit unsigned) (FR-7).
3. Rewrite `to_bytes()` / `from_bytes()` with per-field byte serialization and signed validation (FR-8).
4. Update C++ golden files. Add wide scalar fixture.

### Phase 5: Python Backend
1. Add `WIDTH`, `BYTE_COUNT` to scalar and struct classes (FR-9).
2. Rewrite `to_bytes()` / `from_bytes()` with per-field byte serialization and signed validation (FR-9).
3. Update Python golden files.

### Phase 6: Cross-Language Verification + Final Testing
1. Create `tests/test_runtime_bytes.py` — executable Python runtime tests that import generated Python modules and verify `to_bytes()`/`from_bytes()` with spec-derived test vectors. This is the primary executable verification of FR-10 byte-level consistency.
2. Add struct fixture with signed members for AC-21/22/23.
3. Add wide scalar fixture (65-bit unsigned) for AC-24/25.
4. Run full test suite (golden + runtime), update all goldens, verify idempotency.
5. Run `basedpyright` on all modified files to verify NFR-6.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Existing golden files break en masse | High | Medium | Update goldens incrementally per phase. Each phase is self-contained and testable. |
| Bit-offset arithmetic errors in pack/unpack | Medium | High | Use the spec's worked examples as unit test vectors. Verify round-trip invariant `pack(unpack(v)) == v`. |
| Sign-extension logic subtle bugs (off-by-one in bit indices) | Medium | High | Test both positive and negative values, boundary cases (e.g., min/max for each width). |
| Wide scalar (> 64-bit) C++ wrapper complexity | Medium | Medium | Keep API minimal — constructor, to_bytes, from_bytes. No arithmetic operators. |
| `from_bytes` signed validation false positives | Low | High | Test with known-good and known-bad padding values. Verify `to_bytes(from_bytes(x))` identity for valid data. |
| basedpyright strict mode regressions | Medium | Low | Run `basedpyright` after each phase. Address type errors immediately. |
| **Byte-order migration (little→big endian)** | **High** | **High** | **The existing Python and C++ backends use little-endian serialization. The spec requires big-endian. Mitigation: (1) All golden files MUST be regenerated. (2) `tests/test_runtime_bytes.py` provides executed Python runtime tests with fixed test vectors (13-bit unsigned `{0x1F, 0xFF}`, signed 4-bit -6 `{0xFA}`, 65-bit unsigned `{0x01, 0xFF...}`). These tests will FAIL if byte order is wrong — this is the primary regression anchor. (3) C++/SV correctness verified via golden file comparison against manually validated expected output.** |

## Testing Strategy

### Positive Golden Tests (per NFR-4)

| Fixture | Purpose | ACs covered |
|---------|---------|-------------|
| `struct_sv_basic` (updated) | Existing struct with contiguous fields — verify padding is added | AC-1, AC-2, AC-10 |
| `scalar_sv_basic` (updated) | Existing scalar — verify LP_WIDTH/LP_BYTE_COUNT added | AC-8, AC-10 |
| `nested_struct_sv_basic` (updated) | Nested struct — verify no padding on struct-typed fields | AC-7, AC-10 |
| `struct_padded` (new) | Struct with mixed-width members (1, 13, 4, 1 bits) | AC-1–6, AC-11 |
| `struct_signed` (new) | Struct with signed scalar members | AC-21, AC-22 |
| `scalar_wide` (new) | 65-bit unsigned scalar and 128-bit unsigned scalar | AC-24, AC-9 |
| `struct_wide` (new) | Struct with 65-bit unsigned member + 1-bit flag | AC-25 |

### Negative Tests (per NFR-4)

| Test case | Rule | Expected error |
|-----------|------|----------------|
| Field named `foo_pad` | FR-11 | `"reserved '_pad' suffix"` |
| `LogicSigned(65)` named | FR-13 | `"exceeds maximum 64-bit signed width"` |
| `LogicSigned(65)` inline | FR-13 | `"exceeds maximum 64-bit signed width"` |
| Constant name collision | FR-14 | `"collides with generated identifier"` |

### Executable Runtime Tests (Python)

Golden file comparison verifies generated source structure but does NOT prove runtime correctness. To close this gap, add **executed Python runtime tests** that import the generated Python modules and run value-vector checks.

**New test file:** `tests/test_runtime_bytes.py` (unittest.TestCase)

This test:
1. Runs `typist gen` on each fixture to produce generated Python code.
2. Imports the generated Python module.
3. Instantiates struct/scalar objects with known values.
4. Calls `to_bytes()` and asserts exact byte sequences from the spec.
5. Calls `from_bytes()` with the same bytes and asserts round-trip identity.
6. For signed fields: calls `from_bytes()` with mismatched padding and asserts `ValueError`.

**Executed test vectors** (derived from spec worked examples):

| Object | Values | Expected `to_bytes()` |
|--------|--------|-----------------------|
| `bar_t(flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0)` | unsigned fields | `b'\x01\x1f\xff\x0a\x00'` |
| Signed 5-bit scalar `-1` | `5'b11111` | `b'\xff'` |
| Signed 5-bit scalar `+5` | `5'b00101` | `b'\x05'` |
| Signed 4-bit struct member `-6` | `4'b1010` | byte `0xFA` |
| 65-bit unsigned `0x1_FFFF_FFFF_FFFF_FFFF` | all bits set | `b'\x01' + b'\xff' * 8` |
| Nested struct `outer_t` | inner + tag=1 | `b'\x01\x1f\x01'` |

**Signed validation tests:**
| Input bytes | Type | Expected |
|-------------|------|----------|
| `b'\x0a'` for 4-bit signed | padding mismatch | `ValueError` |
| `b'\x1f'` for 5-bit signed -1 | padding mismatch | `ValueError` |
| `b'\x81\x1f\xff\x0a\x00'` for `bar_t` | unsigned padding nonzero | Accepted (same struct) |

**Why only Python runtime tests:** The project test pipeline (per Constitution) uses `unittest` + golden files. There is no C++ build/execute step and no SV simulation framework in the test suite. C++ and SV correctness is verified by golden file comparison — the generated code must match byte-for-byte expected output that was manually validated against the spec. The Python runtime tests serve as the executable cross-language anchor: if the Python implementation produces correct bytes for the spec's test vectors, and the C++/SV golden files encode structurally identical logic (verified by golden comparison), cross-language consistency (FR-10) is established.

### Idempotency

Existing idempotency test pattern: run `typist gen` twice, verify identical output. This continues to work unchanged.

### AC Coverage Matrix

Every acceptance criterion MUST map to at least one concrete test:

| AC | Test Type | Fixture / Test Case |
|----|-----------|---------------------|
| AC-1 | Golden | `struct_padded` — SV typedef with `_pad` members |
| AC-2 | Golden | `struct_padded` — LP_BAR_WIDTH=19, LP_BAR_BYTE_COUNT=5 |
| AC-3 | Golden + Py runtime | `struct_padded` — pack function body, verify `19'h7FFF4` in golden |
| AC-4 | Golden + Py runtime | `struct_padded` — unpack function body, verify `_pad` = 0 for unsigned |
| AC-5 | Golden | `struct_padded` — pack/unpack round-trip (verified by function structure) |
| AC-6 | Golden + Py runtime | `struct_padded` — to_bytes `{0x01, 0x1F, 0xFF, 0x0A, 0x00}` across SV/C++/Py |
| AC-7 | Golden | `nested_struct_sv_basic` — no `payload_pad`, BYTE_COUNT=3 |
| AC-8 | Golden | `scalar_sv_basic` — LP_FOO_WIDTH, LP_FOO_BYTE_COUNT, identity pack/unpack |
| AC-9 | Golden | `scalar_sv_basic` + `scalar_wide` — C++ type mapping |
| AC-10 | Golden | All existing fixtures updated and passing |
| AC-11 | Golden | `struct_padded` (new fixture with non-trivial padding) |
| AC-12 | Golden + Py runtime | `struct_padded` — from_bytes with nonzero unsigned padding accepted |
| AC-13 | Negative | `struct_pad_collision` — `_pad` suffix rejected |
| AC-14 | Golden + Py runtime | `struct_padded` — unpack(pack(s)) preserves all data fields |
| AC-15 | Golden + Py runtime | `scalar_sv_basic` — from_bytes mask for 13-bit scalar |
| AC-16 | Golden + Py runtime | `struct_signed` — signed 5-bit to_bytes/from_bytes with validation |
| AC-17 | Negative + positive | `scalar_wide` passes (unsigned 128-bit); `scalar_signed_wide` fails (signed 65-bit) |
| AC-18 | Negative + positive | Inline LogicSigned(65) rejected; inline Logic(128) passes |
| AC-19 | Golden + Py runtime | `struct_signed` — to_slv sign-extended padding, from_slv ignores padding |
| AC-20 | Negative | `const_collision` — identifier collision rejected |
| AC-21 | Golden + Py runtime | `struct_signed` — unpack sign-extends _pad for signed 4-bit member |
| AC-22 | Golden + Py runtime | `struct_signed` — to_bytes `0xFA` for signed -6, same across all backends |
| AC-23 | Golden + Py runtime | `struct_signed` — from_bytes with mismatched signed padding raises error |
| AC-24 | Golden + Py runtime | `scalar_wide` — 65-bit unsigned round-trip, padding masking |
| AC-25 | Golden + Py runtime | `struct_wide` — struct with 65-bit member + 1-bit flag = 10 bytes |

"Py runtime" tests are executed in `tests/test_runtime_bytes.py` — they import the generated Python code and call `to_bytes()`/`from_bytes()` with specific values, asserting exact byte sequences from the spec. These are the executable verification layer on top of golden file comparison.
