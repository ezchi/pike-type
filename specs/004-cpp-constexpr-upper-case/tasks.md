# Tasks — Spec 004: C++ constexpr UPPER_SNAKE_CASE

## Task 1: Rename constexpr names in C++ emitter

**File:** `src/typist/backends/cpp/emitter.py`

Replace all `kCamelCase` and lowercase `constexpr` identifier strings with `UPPER_SNAKE_CASE`:

- `kWidth` → `WIDTH`
- `kSigned` → `SIGNED`
- `kByteCount` → `BYTE_COUNT`
- `kMask` → `MASK`
- `kMaxValue` → `MAX_VALUE`
- `kMinValue` → `MIN_VALUE`
- `mask` → `MASK` (in encode/decode helper string literals only)

Affects functions: `_render_cpp_scalar_alias`, `_render_cpp_struct`, `_render_narrow_inline_helpers`.

**AC coverage:** AC-1, AC-6

## Task 2: Rename constexpr name in runtime emitter

**File:** `src/typist/backends/runtime/emitter.py`

Replace `kVerboseDefault` → `VERBOSE_DEFAULT` in `render_runtime_hpp()`.

**AC coverage:** AC-2

## Task 3: Regenerate golden files

Run `typist gen` against all 13 fixtures and overwrite golden directories under `tests/goldens/gen/`.

**AC coverage:** AC-3, AC-5, AC-6, AC-7

## Task 4: Run tests and verify

- Run `python3 -m pytest tests/ -v` — all must pass (AC-4)
- Run `basedpyright` on modified files — zero errors (AC-5)
- Grep golden `.hpp` files for residual old identifiers — zero matches (AC-6)

**AC coverage:** AC-3, AC-4, AC-5, AC-6
