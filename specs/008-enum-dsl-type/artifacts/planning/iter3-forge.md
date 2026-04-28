# Implementation Plan — Spec 008: Enum() DSL Type

## Architecture Overview

The Enum type follows the same four-stage pipeline as all existing types (Flags, Struct, Scalar):

```
DSL Runtime → Freeze → IR → Validation → Backends (SV, Py, C++) + Manifest
```

No new architectural layers are needed. Each existing pipeline stage gets a new `EnumType`/`EnumIR` branch that mirrors the existing `FlagsType`/`FlagsIR` pattern.

## Components

### 1. DSL Runtime — `src/piketype/dsl/enum.py` (new file)

**Responsibility**: Mutable enum builder with chained `add_value()` API.

**Interfaces**:
- `Enum(width: int | None = None) -> EnumType` — factory function
- `EnumType.add_value(name: str, value: int | None = None) -> EnumType` — chaining builder
- `EnumType.width -> int` — explicit or inferred width property. Inferred width uses `max(1, max_value.bit_length())` (integer arithmetic, no float rounding).

**Dependencies**: `DslNode` base class, `SourceInfo`/`capture_source_info()`, `ValidationError`

**Pattern reference**: `dsl/flags.py` — identical structure (factory → mutable dataclass → chaining method → width property)

**Eager DSL-time validation** (FR-1 through FR-5):
- `Enum(width)`: Raises `ValidationError` immediately if `width < 1` or `width > 64`.
- `add_value(name)`: Raises `ValidationError` immediately if name doesn't match `^[A-Z][A-Z0-9_]*$`.
- `add_value(name)`: Raises `ValidationError` immediately on duplicate name.
- `add_value(name, value)`: Raises `ValidationError` immediately if `value < 0`.

**Key data**:
- `EnumMember` frozen dataclass: `name: str`, `source: SourceInfo`, `value: int | None`
- `EnumType` mutable dataclass: `members: list[EnumMember]`, `_explicit_width: int | None`

### 2. DSL Export — `src/piketype/dsl/__init__.py` (edit)

**Change**: Add `Enum` to imports and `__all__`.

### 3. IR Nodes — `src/piketype/ir/nodes.py` (edit)

**New nodes**:
- `EnumValueIR(frozen=True, slots=True)`: `name`, `source`, `expr`, `resolved_value`
- `EnumIR(frozen=True, slots=True)`: `name`, `source`, `width_expr`, `resolved_width`, `values`

**Change**: Update `TypeDefIR` union to include `EnumIR`.

**Dependencies**: Existing `SourceSpanIR`, `ExprIR`, `IntLiteralExprIR`

### 4. Freeze Logic — `src/piketype/dsl/freeze.py` (edit)

**Changes**:
- `build_type_definition_map()`: Add `EnumType` to `isinstance` check (line ~97)
- `freeze_module()`: Add `elif isinstance(value, EnumType)` branch (after FlagsType block, line ~169)
  - Resolve auto-fill values (sequential: `prev + 1`)
  - Compute width (explicit or `max(1, max_value.bit_length())` — integer-safe, no float rounding)
  - Emit `EnumIR` with `IntLiteralExprIR` for values and width
- Duplicate-binding check: Add `EnumType` to `isinstance` tuple (line ~123)

**Pattern reference**: The FlagsType freeze block at lines 169–194 — same structure.

### 5. Validation — `src/piketype/validate/engine.py` (edit)

**Changes**:
- Import `EnumIR` and `EnumValueIR`
- Add `if isinstance(type_ir, EnumIR)` block after the FlagsIR block (~line 82):
  - At least one value
  - Value names match `^[A-Z][A-Z0-9_]*$`
  - No duplicate value names
  - No duplicate resolved values
  - All values non-negative
  - `resolved_width` in [1, 64]
  - All values fit within `resolved_width`
  - Name ends with `_t`
- `_validate_generated_identifier_collision()`: Add enum value names to the collision check
- New `_validate_enum_literal_collision()`: Check enum value names across all enums and constants in a module

### 6. SV Backend — `src/piketype/backends/sv/emitter.py` (edit)

**Synth package changes**:
- `_render_sv_type_block()`: Add `EnumIR` branch
- New `_render_sv_enum()`: Emit `typedef enum logic [W-1:0] { ... } <name>;` (or `typedef enum logic { ... } <name>;` when width == 1, omitting the range per FR-20)
- `_render_sv_pack_fn()`: Add `EnumIR` branch (identity: return `a`)
- `_render_sv_unpack_fn()`: Add `EnumIR` branch (cast: return `<name>'(a)`)
- `_data_width()`, `_type_byte_count()`: Add `EnumIR` branches

**Test package changes**:
- `render_module_test_sv()`: Add `EnumIR` dispatch
- New `_render_sv_enum_helper_class()`: Emit `<base>_ct` class with `to_slv`, `from_slv`, `to_bytes`, `from_bytes`, `copy`, `clone`, `compare`, `sprint`

**Pattern reference**: `_render_sv_scalar_helper_class()` — similar single-value storage pattern.

### 7. Python Backend — `src/piketype/backends/py/emitter.py` (edit)

**Changes**:
- `render_module_py()`: Add `EnumIR` dispatch; add `from enum import IntEnum` when enums present
- New `_render_py_enum()`: Emit `IntEnum` subclass (`<base>_enum_t`) + wrapper class (`<base>_ct`)
- `_resolved_type_width()`, `_type_byte_count()`: Add `EnumIR` branches

**Pattern reference**: `_render_py_flags()` — similar class-based wrapper pattern.

### 8. C++ Backend — `src/piketype/backends/cpp/emitter.py` (edit)

**Changes**:
- `render_module_hpp()`: Add `EnumIR` dispatch
- New `_render_cpp_enum()`: Emit `enum class <base>_enum_t : <uint_type> { ... };` using `_cpp_unsigned_literal()` for enum initializer values (required for values exceeding `INT64_MAX`, e.g., `2**63`), plus wrapper class `<base>_ct`
- `_resolved_type_width()`, `_type_byte_count()`: Add `EnumIR` branches

**Pattern reference**: `_render_cpp_flags()` — similar wrapper class pattern.

### 9. Manifest — `src/piketype/manifest/write_json.py` (edit)

**Changes**:
- Import `EnumIR`
- `_serialize_type_ir()`: Add `EnumIR` branch emitting `kind: "enum"`, `resolved_width`, `value_count`, `values` array
- Update type annotation to include `EnumIR`

### 10. Test Fixtures & Goldens (new files)

**New fixture**: `tests/fixtures/enum_basic/project/` — minimal repo with `piketype/` module containing two enums.

**New goldens**: `tests/goldens/gen/enum_basic/` — all generated outputs.

**New test class**: `tests/test_gen_enum.py` — golden comparison + negative tests.

## Data Model

```
DSL (mutable)                    IR (frozen)
─────────────                    ───────────
EnumMember                       EnumValueIR
  name: str                        name: str
  source: SourceInfo               source: SourceSpanIR
  value: int | None                expr: ExprIR
                                   resolved_value: int
EnumType(DslNode)                EnumIR
  members: list[EnumMember]        name: str
  _explicit_width: int | None      source: SourceSpanIR
                                   width_expr: ExprIR
                                   resolved_width: int
                                   values: tuple[EnumValueIR, ...]
```

## API Design

### DSL API (user-facing)

```python
# Inferred width (2 bits for values 0–3)
state_t = (
    Enum()
    .add_value("IDLE", 0)
    .add_value("ACTIVE", 1)
    .add_value("DONE", 2)
    .add_value("ERROR", 3)
)

# Explicit width (8 bits for protocol compatibility)
cmd_t = (
    Enum(8)
    .add_value("NOP", 0)
    .add_value("READ", 1)
    .add_value("WRITE", 2)
)

# Auto-fill (sequential from previous + 1)
status_t = (
    Enum()
    .add_value("OK")        # 0
    .add_value("WARN")      # 1
    .add_value("ERR", 10)   # 10
    .add_value("FATAL")     # 11
)
```

### Internal API (no new public interfaces beyond the DSL)

All internal wiring uses existing patterns: freeze produces `EnumIR`, validation inspects `EnumIR`, backends dispatch on `isinstance(type_ir, EnumIR)`.

## Dependencies

No new external dependencies. Everything uses existing stdlib + Jinja2.

**Note on templates vs inline**: The constitution requires Jinja2 templates for generated output with meaningful structure. However, all existing backend emitters (SV, Py, C++) use inline string building. Enum emission follows the same inline pattern for consistency with the existing codebase. Migrating to Jinja2 templates is a separate cross-cutting improvement that should apply to all type emitters simultaneously, not piecemeal.

## Implementation Strategy

### Phase 1: Core Pipeline (DSL → IR → Freeze → Validation)

1. **`dsl/enum.py`**: Implement `EnumMember`, `EnumType`, `Enum()` factory.
2. **`dsl/__init__.py`**: Export `Enum`.
3. **`ir/nodes.py`**: Add `EnumValueIR`, `EnumIR`, update `TypeDefIR`.
4. **`dsl/freeze.py`**: Add `EnumType` to discovery/freeze/duplicate checks.
5. **`validate/engine.py`**: Add `EnumIR` validation + collision checks.

**Checkpoint**: `basedpyright` passes, existing tests pass. Can verify enum DSL construction and freeze via unit-level assertions if needed, but primary verification is through integration tests in Phase 3.

### Phase 2: All Backends + Manifest

6. **`backends/sv/emitter.py`**: Synth package + test package enum emission.
7. **`backends/py/emitter.py`**: Python `IntEnum` + wrapper class emission.
8. **`backends/cpp/emitter.py`**: C++ `enum class` + wrapper class emission.
9. **`manifest/write_json.py`**: Enum serialization.

**Checkpoint**: `basedpyright` passes, existing tests pass, can manually run `piketype gen` on a test fixture.

### Phase 3: Tests

10. **Fixture**: Create `tests/fixtures/enum_basic/`.
11. **Run gen**: Generate golden outputs.
12. **Golden files**: Commit to `tests/goldens/gen/enum_basic/`.
13. **Test class**: `tests/test_gen_enum.py` with golden comparison + all negative tests.

**Checkpoint**: All tests pass including new enum tests.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| SV enum literal scope collisions missed | Low | High (broken SV output) | FR-17/FR-18 validation catches at gen time; negative tests verify |
| Auto-fill producing duplicate values silently | Low | High (broken output) | FR-15 validation rejects duplicates after freeze; negative test for this case |
| C++ `enum class` underlying type mismatch | Low | Medium | Reuse existing `_cpp_scalar_value_type()` helper; golden-file comparison catches |
| `basedpyright` type errors from `TypeDefIR` union expansion | Medium | Low | Add `EnumIR` to all `isinstance` dispatch chains; fix incrementally |
| Explicit width + auto-fill edge case (width too small after auto-fill reaches high values) | Low | Medium | Post-freeze validation checks all values fit; negative test covers this |

## Testing Strategy

### Golden-File Integration Tests (`test_gen_enum.py`)

- **`test_enum_basic`**: Full gen pipeline on `enum_basic` fixture. Byte-for-byte comparison of all outputs (SV, SV test, Py, C++, manifest, runtime).
- **`test_enum_basic_idempotent`**: Run gen twice, verify identical output.

### Negative Tests (same file, separate methods)

One `assertIn(expected_error, stderr)` + `assertNotEqual(0, returncode)` per case:
- Empty enum
- Non-UPPER_CASE name
- Duplicate name
- Negative value
- Duplicate resolved values
- Name not ending `_t`
- Enumerator collides with constant
- Enumerator collides with enumerator in another enum
- Enumerator collides with generated SV identifier
- Width > 64 (via value `2**64`)
- Explicit width too small
- Explicit width < 1
- Explicit width > 64

### Fixture Design

`tests/fixtures/enum_basic/project/foo/piketype/defs.py`:
```python
from piketype.dsl import Enum

# Explicit values, non-contiguous (FR-28)
color_t = (
    Enum()
    .add_value("RED", 0)
    .add_value("GREEN", 5)
    .add_value("BLUE", 10)
)

# Mixed explicit + auto-fill with gap, sequential behavior (FR-28, FR-32)
# Demonstrates: explicit 0, explicit 5, auto-fill 6, auto-fill 7
# Also tests explicit width larger than minimum (8-bit for values 0-7)
cmd_t = (
    Enum(8)
    .add_value("NOP", 0)
    .add_value("READ", 5)
    .add_value("WRITE")    # 6 (prev + 1)
    .add_value("RESET")    # 7 (prev + 1)
)

# Single-value enum, width = 1 (FR-32)
flag_t = (
    Enum()
    .add_value("SET", 0)
)

# Large value near 64-bit boundary (FR-32)
big_t = (
    Enum()
    .add_value("SMALL", 0)
    .add_value("LARGE", 2**63)
)
```

This covers: non-contiguous values, sequential auto-fill with gap (prev + 1 after explicit 5), explicit width larger than minimum (8-bit for values 0–7 needs only 3 bits), single-value width=1, and large 64-bit values (`2**63` requires `_cpp_unsigned_literal()` in C++).
