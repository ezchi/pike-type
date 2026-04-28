# Tasks — Spec 005: Flags() DSL Type

## Task 1: IR Node Definitions
**Files:** `src/typist/ir/nodes.py`
**Depends on:** nothing
**ACs:** none directly (foundation for all other tasks)

- [ ] Add `FlagFieldIR` frozen dataclass with `name: str`, `source: SourceSpanIR`
- [ ] Add `FlagsIR` frozen dataclass with `name`, `source`, `fields: tuple[FlagFieldIR, ...]`, `alignment_bits: int = 0`
- [ ] Update `TypeDefIR` union to include `FlagsIR`
- [ ] Run `uv run basedpyright` — expect new errors in downstream files (unhandled FlagsIR cases); that's expected and will be fixed in later tasks

## Task 2: DSL Node + Export
**Files:** `src/typist/dsl/flags.py` (NEW), `src/typist/dsl/__init__.py`
**Depends on:** Task 1
**ACs:** AC-1

- [ ] Create `FlagMember` frozen dataclass: `name: str`, `source: SourceInfo`
- [ ] Create `FlagsType(DslNode)` mutable dataclass with `flags: list[FlagMember]`
- [ ] Implement `add_flag(name: str) -> FlagsType` with eager snake_case and duplicate-name validation
- [ ] Implement `width` property returning `len(self.flags)`
- [ ] Create `Flags()` factory function using `capture_source_info()`
- [ ] Export `Flags` from `src/typist/dsl/__init__.py` and add to `__all__`

## Task 3: Freeze Pipeline
**Files:** `src/typist/dsl/freeze.py`
**Depends on:** Task 1, Task 2
**ACs:** none directly

- [ ] Import `FlagsType` and `FlagsIR`, `FlagFieldIR`
- [ ] Add `FlagsType` to `isinstance` check in `build_type_definition_map()` (line ~94)
- [ ] Add `FlagsType` to `isinstance` check in `freeze_module()` (line ~120)
- [ ] Add `elif isinstance(value, FlagsType):` block in `freeze_module()` to freeze flags → `FlagsIR`
- [ ] Compute `alignment_bits = (-len(value.flags)) % 8`

## Task 4: Validation
**Files:** `src/typist/validate/engine.py`
**Depends on:** Task 1
**ACs:** AC-7

- [ ] Import `FlagsIR`
- [ ] Add `FlagsIR` validation in `validate_repo()`:
  - Type name ends with `_t`
  - At least 1 flag
  - No duplicate flag names
  - No `_pad` suffix
  - No reserved API names: `value`, `to_bytes`, `from_bytes`, `clone`, `width`, `byte_count`
  - Flag count ≤ 64
- [ ] Update `_validate_pad_suffix_reservation()` to handle `FlagsIR`

## Task 5: SystemVerilog Backend — Package
**Files:** `src/typist/backends/sv/emitter.py`
**Depends on:** Task 1
**ACs:** AC-2, AC-5 (SV side: no `_align_pad` for exactly 8 flags)

- [ ] Import `FlagsIR`, `FlagFieldIR`
- [ ] Add `FlagsIR` case in `_render_sv_type_block()`
- [ ] Implement `_render_sv_flags()` — `typedef struct packed` with `logic` per flag + conditional `_align_pad` only when `alignment_bits > 0` (AC-5: 8 flags → no `_align_pad`)
- [ ] Extend `_render_sv_pack_fn()` for `FlagsIR` — concatenate flag bits (data-only width)
- [ ] Extend `_render_sv_unpack_fn()` for `FlagsIR` — extract flag bits, zero `_align_pad`
- [ ] Extend `_data_width()` for `FlagsIR` — return `len(type_ir.fields)`
- [ ] Extend `_type_byte_count()` for `FlagsIR` — return `byte_count(len(type_ir.fields))`

## Task 6: SystemVerilog Backend — Test Package
**Files:** `src/typist/backends/sv/emitter.py` (test section)
**Depends on:** Task 5
**ACs:** none directly (SV test helpers)

- [ ] Add `FlagsIR` dispatch in `render_module_test_sv()`
- [ ] Implement flags test helper class with:
  - `to_bytes()` — cast struct to bit vector, serialize big-endian
  - `from_bytes()` — init to `'0`, assign only flag fields from input bytes (padding stays zero)

## Task 7: C++ Backend
**Files:** `src/typist/backends/cpp/emitter.py`
**Depends on:** Task 1
**ACs:** AC-3, AC-5, AC-6, AC-12

- [ ] Import `FlagsIR`, `FlagFieldIR`
- [ ] Add `FlagsIR` dispatch in `render_module_hpp()`
- [ ] Implement `_render_cpp_flags()`:
  - Class with `value_type`, `WIDTH`, `BYTE_COUNT`
  - Per-flag `static constexpr` masks (UPPER_SNAKE_CASE, `U`/`ULL` suffix)
  - Per-flag `get_<name>()`/`set_<name>()` methods
  - `to_bytes()` with literal data mask
  - `from_bytes()` (instance method) with size validation + padding mask
  - Custom `operator==` with padding mask
  - `clone()`

## Task 8: Python Backend
**Files:** `src/typist/backends/py/emitter.py`
**Depends on:** Task 1
**ACs:** AC-4, AC-11, AC-13, AC-14

- [ ] Import `FlagsIR`, `FlagFieldIR`
- [ ] Add `FlagsIR` dispatch in `render_module_py()`
- [ ] Implement `_render_py_flags()`:
  - Class with `WIDTH`, `BYTE_COUNT`, `__init__` setting `_value = 0`
  - Per-flag `@property` with getter/setter
  - `to_bytes()` with literal data mask
  - `@classmethod from_bytes()` with size validation + padding mask
  - `__eq__` with masked comparison
  - `clone()`

## Task 9: Manifest
**Files:** `src/typist/manifest/write_json.py`
**Depends on:** Task 1
**ACs:** AC-15

- [ ] Import `FlagsIR`
- [ ] Add `FlagsIR` case in type serialization with `kind: "flags"`, `flag_count`, `flag_names`

## Task 10: Fixture + Golden Files
**Files:** `tests/fixtures/flags_basic/...` (NEW), `tests/goldens/gen/flags_basic/...` (NEW)
**Depends on:** Tasks 2-9 (all pipeline code must be in place)
**ACs:** AC-8

- [ ] Create fixture DSL module with 5 flag types: single_t (1), triple_t (3), byte_t (8), wide_t (9), very_wide_t (33)
- [ ] Initialize fixture as git repo
- [ ] Run `uv run typist gen` on fixture
- [ ] Copy generated output to `tests/goldens/gen/flags_basic/`
- [ ] Verify golden files look correct

## Task 11: Integration + Runtime Tests
**Files:** `tests/test_gen_flags.py` (NEW)
**Depends on:** Task 10
**ACs:** AC-1, AC-4, AC-7, AC-8, AC-9, AC-11, AC-13, AC-14

- [ ] Golden file comparison test
- [ ] Idempotency test
- [ ] Python runtime round-trip tests with explicit byte vectors for all 5 types:
  - single_t: `{flag=True}` → `b'\x80'`
  - triple_t: `{a=True, b=False, c=True}` → `b'\xa0'`
  - byte_t: all-on → `b'\xff'`
  - wide_t: f0-only → `b'\x80\x00'`
  - very_wide_t: f0-only → `b'\x80\x00\x00\x00\x00'`
- [ ] Nonzero padding masking test (AC-14)
- [ ] Wrong byte count test (AC-13)
- [ ] DSL-layer negative tests (duplicates, non-snake_case names — tested via direct `add_flag()` calls)
- [ ] IR validation negative tests (0 flags, >64 flags, `_pad` suffix, reserved API names like `value`/`to_bytes`, missing `_t` — tested via `validate_repo()` or `typist gen` CLI)
- [ ] Direct `Flags().add_flag("a").add_flag("b").add_flag("c").width == 3` test (AC-1)

## Task 12: Static Type Check + Final Verification
**Depends on:** Tasks 1-11
**ACs:** AC-10

- [ ] Run `uv run basedpyright` — verify zero errors
- [ ] Run `uv run python3 -m pytest tests/test_gen_flags.py -v` — all tests pass
- [ ] Run full test suite to check for regressions

## Dependency Graph

```
Task 1 (IR) ──┬── Task 2 (DSL) ──── Task 3 (Freeze)
              ├── Task 4 (Validation)
              ├── Task 5 (SV pkg) ── Task 6 (SV test)
              ├── Task 7 (C++)
              ├── Task 8 (Python)
              └── Task 9 (Manifest)
                      │
              Tasks 2-9 ──── Task 10 (Fixture/Goldens) ── Task 11 (Tests) ── Task 12 (Verify)
```

Tasks 4, 5, 7, 8, 9 can run in parallel after Task 1. Task 3 requires Tasks 1+2.
