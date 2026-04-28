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

This covers declarations and all references in constructors, initializer lists, `to_bytes`, `from_bytes`, `validate_value`, and wide-scalar `validate_value`.

**1b. Struct class statics** — In `_render_cpp_struct()` (lines ~340–420):
- Replace `kWidth` → `WIDTH` in string literals
- Replace `kByteCount` → `BYTE_COUNT` in string literals

**1c. Helper function local constants** — In `_render_narrow_inline_helpers()` (lines ~582–733):
- Replace `kMaxValue` → `MAX_VALUE` in string literals (validate helpers)
- Replace `kMinValue` → `MIN_VALUE` in string literals (validate helpers)
- Replace `mask` → `MASK` in string literals for both declarations and all references:
  - `constexpr std::uint64_t mask` → `constexpr std::uint64_t MASK`
  - `bits & mask` → `bits & MASK`
  - `~mask` → `~MASK`
  - `bits &= mask` → `bits &= MASK`
  - `bits = data_bits;` line (unchanged, not a `mask` reference)

### Step 2: Rename constant in runtime emitter (`src/typist/backends/runtime/emitter.py`)

In `render_runtime_hpp()` (line ~66):
- Replace `kVerboseDefault` → `VERBOSE_DEFAULT`

### Step 3: Regenerate golden files

The test suite runs `typist gen` against fixtures and compares output to golden directories. To regenerate goldens, run each fixture through the CLI the same way tests do:

```bash
# Standard fixtures (no extra args):
for fixture in const_sv_basic const_cpp_explicit_uint32 const_cpp_wide const_expr_basic \
               scalar_sv_basic scalar_wide struct_sv_basic struct_padded struct_signed \
               nested_struct_sv_basic struct_multiple_of; do
  cd /tmp && rm -rf regen && mkdir regen
  cp -r tests/fixtures/$fixture/project regen/project
  PYTHONPATH=src python -m typist.cli gen regen/project/alpha/typist/*.py
  cp -r regen/project/gen/* tests/goldens/gen/$fixture/
done

# Namespace override fixture (requires --namespace):
cd /tmp && rm -rf regen && mkdir regen
cp -r tests/fixtures/namespace_override/project regen/project
PYTHONPATH=src python -m typist.cli gen --namespace foo::bar regen/project/alpha/typist/constants.py
cp -r regen/project/gen/* tests/goldens/gen/namespace_override/
```

Alternatively, run the test suite after modifying the emitters — tests will fail — then copy the generated output from the temp directories. In practice, since we modify the emitter and the test runs the emitter, the simplest approach is to run `typist gen` for each fixture and overwrite goldens.

### Step 4: Verify

Run all three verification checks:

```bash
# 4a. Full test suite
python -m pytest tests/ -v

# 4b. Type checker
basedpyright src/typist/backends/cpp/emitter.py src/typist/backends/runtime/emitter.py

# 4c. Exhaustive grep for old identifiers in golden .hpp files
# Must return zero matches:
grep -rn 'kWidth\|kSigned\|kByteCount\|kMask\|kMaxValue\|kMinValue\|kVerboseDefault' tests/goldens/gen/ --include='*.hpp'

# 4d. Grep for lowercase `constexpr ... mask` (non-UPPER_SNAKE_CASE):
grep -rn 'constexpr.*uint64_t mask ' tests/goldens/gen/ --include='*.hpp'
# Must return zero matches.
```

## Files Modified

| File | Change |
|------|--------|
| `src/typist/backends/cpp/emitter.py` | Rename all `k`-prefixed and lowercase `constexpr` names to `UPPER_SNAKE_CASE` in string literals |
| `src/typist/backends/runtime/emitter.py` | Rename `kVerboseDefault` → `VERBOSE_DEFAULT` |
| `tests/goldens/gen/*/cpp/**/*.hpp` | Regenerated to match new emitter output |
| `tests/goldens/gen/*/cpp/**/typist_runtime.hpp` | Regenerated runtime header |

## Risk Assessment

**Low risk.** This is a pure string-literal rename in emitter code. No logic changes, no IR changes, no DSL changes. The golden-file test suite provides full regression coverage.

## Dependencies

None. This change is self-contained within the C++ backend emitter and runtime emitter.
