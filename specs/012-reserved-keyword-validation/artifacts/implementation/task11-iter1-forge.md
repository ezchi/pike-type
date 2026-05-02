# Task 11: Negative fixture — constant `for` (AC-5) — Forge Iteration 1

## Files Changed

- `tests/fixtures/keyword_constant_for/project/.git/HEAD` — repo-root marker.
- `tests/fixtures/keyword_constant_for/project/alpha/piketype/types.py` — installs a constant binding named `for` via `sys.modules[__name__].__dict__['for'] = Const(3)`.

## Key Implementation Decisions

- **`for` is a Python hard keyword.** `for = Const(3)` is a Python syntax error. The DSL freeze step walks `module.__dict__.items()` (verified at `src/piketype/dsl/freeze.py:79`), accepting any binding name including hard keywords. Installing the binding via `sys.modules[__name__].__dict__['for']` is the only path to exercise the AC-5 example identifier.
- A comment in the fixture explains why this otherwise-unusual idiom is necessary, so a future maintainer doesn't try to "fix" it.
- Single-constant module is sufficient (constants don't have a min-count rule).

## Deviations from Plan

The plan says "create a fixture with a top-level constant named `for`". The plan implicitly assumed a normal binding. Implementation uses `__dict__` install because Python's grammar forbids the normal form. Plan amendment note for retrospect: any DSL identifier that is also a Python hard keyword needs the `__dict__` workaround.

## Tests Added

`test_constant_for_is_rejected` (T-017). Manual run confirms `constant 'for' is a reserved keyword in target language(s): C++, Python, SystemVerilog`.
