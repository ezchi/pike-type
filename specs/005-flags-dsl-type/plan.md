# Implementation Plan — Spec 005: Flags() DSL Type

## Approach

Follow the constitution's "Adding a New Type or Feature" recipe (§Development Guidelines). Implementation proceeds layer by layer: DSL → IR → Freeze → Validate → Backends → Manifest → Tests. Each layer is independently testable.

## Phase 1: Core Type Pipeline (DSL → IR → Freeze → Validate)

### Step 1: IR Node Definitions
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
    alignment_bits: int = 0
```

Update the `TypeDefIR` union (line 132):
```python
type TypeDefIR = ScalarAliasIR | StructIR | FlagsIR
```

### Step 2: DSL Node
**Files:** `src/typist/dsl/flags.py` (NEW), `src/typist/dsl/__init__.py`

Create `FlagsType(DslNode)` with `add_flag(name: str) -> FlagsType`. Follow `StructType` pattern:
- Mutable dataclass with `slots=True`
- `flags: list[FlagMember]` tracking ordered flags
- Eager snake_case validation, duplicate name checks
- `Flags()` factory function using `capture_source_info()`

Export `Flags` from `__init__.py`.

### Step 3: Freeze Pipeline
**Files:** `src/typist/dsl/freeze.py`

Three integration points:
1. `build_type_definition_map()` (line 94): Add `FlagsType` to the `isinstance` check.
2. `freeze_module()` (line 120): Add `FlagsType` to the `isinstance` check. Add a new elif block after the `StructType` handler (~line 143-165) to freeze `FlagsType` → `FlagsIR`.
3. Compute `alignment_bits = (-len(flags)) % 8` during freeze.

### Step 4: Validation
**Files:** `src/typist/validate/engine.py`

Add `FlagsIR` validation in `validate_repo()`:
- Type name must end with `_t` (shared with existing check)
- At least 1 flag
- No duplicate flag names
- No `_pad` suffix on flag names
- No reserved API names: `value`, `to_bytes`, `from_bytes`, `clone`, `width`, `byte_count`
- Flag count ≤ 64

Also update `_validate_pad_suffix_reservation()` to handle `FlagsIR`.

## Phase 2: Backend Emission

### Step 5: SystemVerilog Backend
**Files:** `src/typist/backends/sv/emitter.py`

Add `FlagsIR` import and dispatch in `_render_sv_type_block()` (line ~108).

New functions:
- `_render_sv_flags()` — `typedef struct packed` with 1-bit `logic` fields + trailing `_align_pad`
- Update `_render_sv_pack_fn()` — concatenate flag bits (data-only width)
- Update `_render_sv_unpack_fn()` — extract flag bits from packed vector
- Update width/byte-count helpers for `FlagsIR`

### Step 6: SystemVerilog Test Package
**Files:** `src/typist/backends/sv/emitter.py` (test section, line ~243)

Add `FlagsIR` dispatch in `render_module_test_sv()`. Generate a test helper class with `to_bytes()`/`from_bytes()` following the Struct helper pattern.

### Step 7: C++ Backend
**Files:** `src/typist/backends/cpp/emitter.py`

Add `FlagsIR` import and dispatch in `render_module_hpp()` (line ~81).

New function `_render_cpp_flags()`:
- Class with `value_type` (uint8/16/32/64_t), public `value`
- Per-flag `static constexpr` masks (UPPER_SNAKE_CASE, literal hex)
- Per-flag `get_<name>()`/`set_<name>()` methods
- `to_bytes()` with literal padding mask
- `from_bytes()` (instance method) with size validation and padding mask
- Custom `operator==` with padding mask
- `clone()` returning copy

### Step 8: Python Backend
**Files:** `src/typist/backends/py/emitter.py`

Add `FlagsIR` import and dispatch in `render_module_py()` (line ~67).

New function `_render_py_flags()`:
- Class with `WIDTH`, `BYTE_COUNT` class variables
- `__init__` setting `self._value = 0`
- Per-flag Python property (getter/setter on `_value`)
- `to_bytes()` with literal padding mask
- `@classmethod from_bytes()` with size validation and padding mask
- `__eq__` with masked comparison
- `clone()`

### Step 9: Manifest
**Files:** `src/typist/manifest/write_json.py`

Add `FlagsIR` import (line 8). Restructure the type serialization ternary (lines 56-80) into explicit `isinstance` checks with a `FlagsIR` case producing:
```json
{"name": "...", "kind": "flags", "flag_count": N, "flag_names": [...], "source": {...}}
```

## Phase 3: Testing

### Step 10: Fixture
**Files:** `tests/fixtures/flags_basic/project/alpha/typist/types.py` (NEW)

DSL module with 5 flag types:
- `single_t` — 1 flag
- `triple_t` — 3 flags (a, b, c)
- `byte_t` — 8 flags (no padding)
- `wide_t` — 9 flags (16-bit storage)
- `very_wide_t` — 33 flags (64-bit storage)

### Step 11: Generate Golden Files
Run `typist gen` on the fixture. Copy `gen/` output to `tests/goldens/gen/flags_basic/`.

### Step 12: Integration Tests
**Files:** `tests/test_gen_flags.py` (NEW)

Test cases following `test_struct_multiple_of.py` pattern:
- `test_generates_flags_golden` — golden file comparison
- `test_idempotent` — second run produces identical output
- `test_runtime_round_trip_*` — Python runtime tests per fixture type (explicit byte vectors)
- `test_runtime_nonzero_padding` — FR-24 item 6
- `test_runtime_from_bytes_wrong_size` — FR-26
- `test_dsl_validation_*` — negative tests for FR-25 (0 flags, >64, duplicates, bad names, reserved names, etc.)

## File Change Summary

| File | Action | Phase |
|------|--------|-------|
| `src/typist/ir/nodes.py` | Modify (add FlagFieldIR, FlagsIR, update TypeDefIR) | 1 |
| `src/typist/dsl/flags.py` | Create (FlagsType, Flags factory) | 1 |
| `src/typist/dsl/__init__.py` | Modify (add Flags export) | 1 |
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

1. **TypeDefIR union change ripples.** Adding `FlagsIR` to the union means every `match`/`isinstance` check on `TypeDefIR` in the codebase must handle the new variant. Mitigation: `basedpyright` strict mode will flag unhandled cases.

2. **SV pack/unpack data-only width.** The `_data_width()` and `_render_sv_width_value()` helpers currently only handle `ScalarAliasIR` and `StructIR`. They need `FlagsIR` branches. Mitigation: pattern matching with `case _` fallback will catch this.

3. **Large golden files for 33-flag type.** The C++ class will have 33 mask constants, 33 getters, 33 setters. Mitigation: this is expected and acceptable for golden file testing.
