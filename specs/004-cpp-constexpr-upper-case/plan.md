# Implementation Plan — Spec 004: C++ constexpr UPPER_SNAKE_CASE

## Strategy

This is a mechanical rename affecting two Python emitter files and all C++ golden files. The approach is straightforward: modify the emitters, regenerate goldens, verify tests pass.

## Implementation Steps

### Step 1: Rename constants in C++ emitter (`src/typist/backends/cpp/emitter.py`)

**1a. Scalar alias class statics** — In `_render_cpp_scalar_alias()` (lines ~130–332):
- Replace all `kWidth` → `WIDTH` in string literals
- Replace all `kSigned` → `SIGNED` in string literals
- Replace all `kByteCount` → `BYTE_COUNT` in string literals
- Replace all `kMask` → `MASK` in string literals
- Replace all `kMaxValue` → `MAX_VALUE` in string literals
- Replace all `kMinValue` → `MIN_VALUE` in string literals

This covers declarations and all references in `to_bytes`, `from_bytes`, `validate_value`, constructors, and initializer lists.

**1b. Struct class statics** — In `_render_cpp_struct()` (lines ~340–420):
- Replace `kWidth` → `WIDTH` in string literals
- Replace `kByteCount` → `BYTE_COUNT` in string literals

**1c. Helper function local constants** — In `_render_narrow_inline_helpers()` (lines ~582–733):
- Replace `kMaxValue` → `MAX_VALUE` in string literals
- Replace `kMinValue` → `MIN_VALUE` in string literals
- Replace `mask` → `MASK` in string literals (both declarations and references: `constexpr std::uint64_t mask`, `bits & mask`, `~mask`, `bits &= mask`, etc.)

### Step 2: Rename constant in runtime emitter (`src/typist/backends/runtime/emitter.py`)

In `render_runtime_hpp()` (line ~66):
- Replace `kVerboseDefault` → `VERBOSE_DEFAULT`

### Step 3: Regenerate golden files

Run `typist gen` against each fixture to regenerate all C++ golden output under `tests/goldens/gen/`. Copy the fresh `gen/` tree over the committed goldens.

### Step 4: Verify

- Run `python -m pytest tests/` — all tests must pass
- Run `basedpyright` — zero errors
- Grep golden `.hpp` files for any remaining `kCamelCase` constexpr — must find none

## Files Modified

| File | Change |
|------|--------|
| `src/typist/backends/cpp/emitter.py` | Rename all `k`-prefixed and lowercase `constexpr` names to `UPPER_SNAKE_CASE` in string literals |
| `src/typist/backends/runtime/emitter.py` | Rename `kVerboseDefault` → `VERBOSE_DEFAULT` |
| `tests/goldens/gen/*/cpp/**/*.hpp` | Regenerated to match new emitter output |

## Risk Assessment

**Low risk.** This is a pure string-literal rename in emitter code. No logic changes, no IR changes, no DSL changes. The golden-file test suite provides full regression coverage.

## Dependencies

None. This change is self-contained within the C++ backend emitter and runtime emitter.
