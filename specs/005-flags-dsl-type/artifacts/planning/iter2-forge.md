# Implementation Plan — Spec 005: Flags() DSL Type

## Approach

Follow the constitution's "Adding a New Type or Feature" recipe (§Development Guidelines). Implementation proceeds layer by layer: DSL → IR → Freeze → Validate → Backends → Manifest → Tests. Each layer is independently testable.

**Template-first justification:** All existing backends (`sv/emitter.py`, `cpp/emitter.py`, `py/emitter.py`) use inline string building, not Jinja2 templates. The Flags emitter code follows this established pattern for consistency. Migrating backends to templates is a separate cross-cutting effort.

## Phase 1: Core Type Pipeline (DSL → IR → Freeze → Validate)

### Step 1: DSL Node
**Files:** `src/typist/dsl/flags.py` (NEW), `src/typist/dsl/__init__.py`

Create `FlagsType(DslNode)` following the `StructType` pattern:
- Mutable dataclass with `slots=True`
- `FlagMember` frozen dataclass: `name: str`, `source: SourceInfo`
- `flags: list[FlagMember]` tracking ordered flags
- `add_flag(name: str) -> FlagsType` — appends flag, returns self for chaining. Eager snake_case validation and duplicate name checks (raises `ValidationError`).
- `width` property returning `len(self.flags)` (FR-3, AC-1).
- `Flags()` factory function using `capture_source_info()`

Export `Flags` from `__init__.py`, add to `__all__`.

### Step 2: IR Node Definitions
**Files:** `src/typist/ir/nodes.py`

Add `FlagFieldIR` and `FlagsIR` frozen dataclasses after `StructIR` (line ~130):
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
    alignment_bits: int = 0  # default 0, consistent with StructIR
```

Note: `alignment_bits` has a default of `0`, matching `StructIR`. The freeze layer always computes and passes the correct value explicitly.

Update the `TypeDefIR` union (line 132):
```python
type TypeDefIR = ScalarAliasIR | StructIR | FlagsIR
```

### Step 3: Freeze Pipeline
**Files:** `src/typist/dsl/freeze.py`

Three integration points:
1. `build_type_definition_map()` (line 94): Add `FlagsType` to the `isinstance(value, (ScalarType, StructType))` check.
2. `freeze_module()` (line 120): Add `FlagsType` to the `isinstance(value, (Const, ScalarType, StructType))` check. Add a new `elif isinstance(value, FlagsType):` block after the `StructType` handler (~line 143-165) to:
   - Create `FlagFieldIR` for each flag in the list
   - Compute `alignment_bits = (-len(value.flags)) % 8`
   - Produce a `FlagsIR` node
3. No changes needed to `_freeze_struct_field()` or `_freeze_field_type()` — Flags fields are not struct-typed.

### Step 4: Validation
**Files:** `src/typist/validate/engine.py`

Add `FlagsIR` validation in `validate_repo()`:
- Import `FlagsIR` from `ir.nodes`
- Add `isinstance(type_ir, FlagsIR)` case in the type loop
- Type name must end with `_t` (reuse existing check)
- At least 1 flag
- No duplicate flag names
- No `_pad` suffix on flag names (update `_validate_pad_suffix_reservation()`)
- No reserved API names: `value`, `to_bytes`, `from_bytes`, `clone`, `width`, `byte_count`
- Flag count ≤ 64

## Phase 2: Backend Emission

### Step 5: SystemVerilog Backend — Package
**Files:** `src/typist/backends/sv/emitter.py`

Add `FlagsIR` import and dispatch in `_render_sv_type_block()` (line ~108).

New/modified functions:
- `_render_sv_flags()` — `typedef struct packed` with 1-bit `logic` fields + trailing `_align_pad` when `alignment_bits > 0`
- Extend `_render_sv_pack_fn()` — for `FlagsIR`: return `{a.flag1, a.flag2, ...}` (data-only width, concatenate flag bits)
- Extend `_render_sv_unpack_fn()` — for `FlagsIR`: extract flag bits from packed vector (LSB to MSB), zero `_align_pad`
- Extend `_data_width()` — return `len(type_ir.fields)` for `FlagsIR`
- Extend `_type_byte_count()` — return `byte_count(len(type_ir.fields))` for `FlagsIR`

### Step 6: SystemVerilog Backend — Test Package
**Files:** `src/typist/backends/sv/emitter.py` (test section, line ~243)

Add `FlagsIR` dispatch in `render_module_test_sv()`.

**Flags-specific test helper approach:** Unlike Struct (which serializes per-field with individual byte-aligned fields), the Flags test helper casts the entire `typedef struct packed` value to a `logic [BYTE_COUNT*8-1:0]` bit vector, then serializes it big-endian byte-by-byte. This is simpler than the Struct pattern:
- `to_bytes()`: cast struct to bit vector, extract bytes MSB-first
- `from_bytes()`: reassemble bytes into bit vector, cast back to struct type. The `_align_pad` field is automatically zeroed because `from_bytes()` only populates flag bits.

### Step 7: C++ Backend
**Files:** `src/typist/backends/cpp/emitter.py`

Add `FlagsIR` import and dispatch in `render_module_hpp()` (line ~81).

New function `_render_cpp_flags(*, type_ir: FlagsIR) -> list[str]`:
- Class `<name>_ct` with `using value_type = std::uint{N}_t;`
- `static constexpr WIDTH`, `BYTE_COUNT`
- Per-flag `static constexpr value_type <FLAG>_MASK = <hex>;` (UPPER_SNAKE_CASE, `U`/`ULL` suffix)
- Per-flag `bool get_<flag>() const` / `void set_<flag>(bool v)`
- `value_type value = 0;` public member
- `to_bytes()` — serialize `value & <literal_data_mask>` big-endian
- `from_bytes(const std::vector<std::uint8_t>&)` — validate size, deserialize, mask padding
- Custom `operator==` — masked comparison with literal hex mask
- `clone()` — return copy

### Step 8: Python Backend
**Files:** `src/typist/backends/py/emitter.py`

Add `FlagsIR` import and dispatch in `render_module_py()` (line ~67).

New function `_render_py_flags(*, type_ir: FlagsIR) -> list[str]`:
- Class `<name>_ct` with `WIDTH`, `BYTE_COUNT` class variables
- `__init__` setting `self._value = 0`
- Per-flag `@property` with getter/setter on `_value` bits
- `to_bytes()` — `(self._value & <data_mask>).to_bytes(BYTE_COUNT, "big")`
- `@classmethod from_bytes(cls, data)` — validate size, deserialize, mask padding
- `__eq__` — masked comparison
- `clone()` — new instance with same masked `_value`

### Step 9: Manifest
**Files:** `src/typist/manifest/write_json.py`

Import `FlagsIR`. Restructure the type serialization ternary (lines 56-80) into a helper or explicit `isinstance` chain with `FlagsIR` case producing:
```json
{"name": "...", "kind": "flags", "flag_count": N, "flag_names": ["a", "b", ...], "source": {...}}
```

## Phase 3: Testing & Verification

### Step 10: Fixture
**Files:** `tests/fixtures/flags_basic/project/alpha/typist/types.py` (NEW)

DSL module with 5 flag types:
```python
from typist.dsl import Flags

single_t = Flags().add_flag("flag")
triple_t = Flags().add_flag("a").add_flag("b").add_flag("c")
byte_t = Flags().add_flag("f0").add_flag("f1").add_flag("f2").add_flag("f3").add_flag("f4").add_flag("f5").add_flag("f6").add_flag("f7")
wide_t = Flags().add_flag("f0").add_flag("f1").add_flag("f2").add_flag("f3").add_flag("f4").add_flag("f5").add_flag("f6").add_flag("f7").add_flag("f8")
very_wide_t = Flags().add_flag("f0")...  # 33 flags total
```

### Step 11: Generate Golden Files
Run `uv run python3 -m typist gen` on the fixture. Copy `gen/` output to `tests/goldens/gen/flags_basic/`.

### Step 12: Integration Tests
**Files:** `tests/test_gen_flags.py` (NEW)

Test cases:
- `test_generates_flags_golden` — golden file comparison
- `test_idempotent` — second run produces identical output
- `test_runtime_round_trip_single` — 1-flag Python runtime test
- `test_runtime_round_trip_triple` — 3-flag Python runtime test with explicit bytes
- `test_runtime_round_trip_byte` — 8-flag Python runtime test
- `test_runtime_round_trip_wide` — 9-flag Python runtime test
- `test_runtime_round_trip_very_wide` — 33-flag Python runtime test
- `test_runtime_nonzero_padding` — from_bytes with garbage padding bits → masked
- `test_runtime_from_bytes_wrong_size` — ValueError on wrong byte count
- `test_dsl_duplicate_flag` — ValidationError
- `test_dsl_bad_name` — ValidationError for non-snake_case
- `test_dsl_reserved_name` — ValidationError for `value`, `to_bytes`, etc.
- `test_validation_zero_flags` — ValidationError for 0 flags
- `test_validation_too_many_flags` — ValidationError for >64 flags
- `test_validation_pad_suffix` — ValidationError for `_pad` suffix
- `test_validation_missing_t_suffix` — ValidationError for type name without `_t`

### Step 13: Static Type Checking
Run `uv run basedpyright` on the full codebase. Verify zero errors in strict mode (AC-10).

## File Change Summary

| File | Action | Phase |
|------|--------|-------|
| `src/typist/dsl/flags.py` | Create (FlagsType, FlagMember, Flags factory) | 1 |
| `src/typist/dsl/__init__.py` | Modify (add Flags export) | 1 |
| `src/typist/ir/nodes.py` | Modify (add FlagFieldIR, FlagsIR, update TypeDefIR) | 1 |
| `src/typist/dsl/freeze.py` | Modify (3 integration points) | 1 |
| `src/typist/validate/engine.py` | Modify (add FlagsIR validation) | 1 |
| `src/typist/backends/sv/emitter.py` | Modify (typedef, pack/unpack, test helper) | 2 |
| `src/typist/backends/cpp/emitter.py` | Modify (flags class generation) | 2 |
| `src/typist/backends/py/emitter.py` | Modify (flags class generation) | 2 |
| `src/typist/manifest/write_json.py` | Modify (add flags manifest kind) | 2 |
| `tests/fixtures/flags_basic/...` | Create (fixture DSL module) | 3 |
| `tests/goldens/gen/flags_basic/...` | Create (golden output files) | 3 |
| `tests/test_gen_flags.py` | Create (integration + runtime + negative tests) | 3 |

## Risks and Mitigations

1. **TypeDefIR union change ripples.** Adding `FlagsIR` to the union means every `match`/`isinstance` check on `TypeDefIR` must handle the new variant. Mitigation: `basedpyright` strict mode will flag unhandled cases at step 13.

2. **Large golden files for 33-flag type.** The C++ class will have 33 mask constants, 33 getters, 33 setters. This is expected and acceptable for golden file testing.

3. **SV test helper differs from Struct pattern.** Flags uses whole-struct bit-vector serialization rather than per-field byte-aligned serialization. Mitigation: explicitly documented in Step 6; the approach is simpler for flags.
