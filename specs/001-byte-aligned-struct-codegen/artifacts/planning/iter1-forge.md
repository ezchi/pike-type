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
- In `_freeze_struct_field()`: After resolving field type and width, compute `padding_bits`:
  - Scalar field: `padding_bits = (ceil(resolved_width / 8) * 8) - resolved_width`
  - Struct-typed field: `padding_bits = 0`
- Pass `padding_bits` to `StructFieldIR` constructor.

**Key logic:**
```python
import math
def _compute_padding_bits(resolved_width: int) -> int:
    return (math.ceil(resolved_width / 8) * 8) - resolved_width
```

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
1. Verify cross-language byte-level consistency (FR-10) — SV, C++, Python produce identical `to_bytes()` for same data.
2. Add struct fixture with signed members for AC-21/22/23.
3. Add wide scalar fixture (65-bit unsigned) for AC-24/25.
4. Run full test suite, update all goldens, verify idempotency.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Existing golden files break en masse | High | Medium | Update goldens incrementally per phase. Each phase is self-contained and testable. |
| Bit-offset arithmetic errors in pack/unpack | Medium | High | Use the spec's worked examples as unit test vectors. Verify round-trip invariant `pack(unpack(v)) == v`. |
| Sign-extension logic subtle bugs (off-by-one in bit indices) | Medium | High | Test both positive and negative values, boundary cases (e.g., min/max for each width). |
| Wide scalar (> 64-bit) C++ wrapper complexity | Medium | Medium | Keep API minimal — constructor, to_bytes, from_bytes. No arithmetic operators. |
| `from_bytes` signed validation false positives | Low | High | Test with known-good and known-bad padding values. Verify `to_bytes(from_bytes(x))` identity for valid data. |
| basedpyright strict mode regressions | Medium | Low | Run `basedpyright` after each phase. Address type errors immediately. |

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

### Cross-Language Verification

For each golden fixture, all three backend outputs (`sv/`, `cpp/`, `py/`) are generated and compared byte-for-byte against goldens. The golden files themselves serve as the cross-language consistency proof — if SV, C++, and Python golden files all encode the same `to_bytes()` logic for the same data, FR-10 is satisfied.

### Idempotency

Existing idempotency test pattern: run `typist gen` twice, verify identical output. This continues to work unchanged.
