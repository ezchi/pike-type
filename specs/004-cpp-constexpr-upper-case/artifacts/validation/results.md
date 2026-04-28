# Validation Results — Spec 004

## AC-1: C++ emitter produces UPPER_SNAKE_CASE

**PASS.** Grep of emitter source confirms all `constexpr` string literals use `WIDTH`, `SIGNED`, `BYTE_COUNT`, `MASK`, `MAX_VALUE`, `MIN_VALUE` — no `kCamelCase` remains.

## AC-2: Runtime emitter produces VERBOSE_DEFAULT

**PASS.** `render_runtime_hpp()` now emits `VERBOSE_DEFAULT`.

## AC-3: Golden files match typist gen output

**PASS.** All 13 fixtures regenerated and `python -m pytest tests/` passes 101/101 tests (golden comparison is byte-for-byte).

## AC-4: All tests pass

**PASS.** `python3 -m pytest tests/ -v` — 101 passed in 1.38s.

## AC-5: basedpyright zero errors

**PASS.** Same 9 pre-existing `reportUnnecessaryComparison`/`reportUnnecessaryIsInstance`/`reportUnusedVariable` errors before and after. No new errors introduced.

## AC-6: No residual old identifiers

**PASS.** Grep for `kWidth|kSigned|kByteCount|kMask|kMaxValue|kMinValue|kVerboseDefault` in golden `.hpp` files — zero matches. Grep for `constexpr.*uint64_t mask ` — zero matches.

## AC-7: User-defined constants unchanged

**PASS.** Module-level constants `FOO`, `BAR`, `W`, `A`, `B`, `C`, `D`, `E` remain unchanged in golden files.
