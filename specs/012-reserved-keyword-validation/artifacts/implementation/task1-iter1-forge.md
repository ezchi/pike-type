# Task 1: Create keywords.py with frozen sets and keyword_languages helper — Forge Iteration 1

## Files Changed

- `src/piketype/validate/keywords.py` — created. Owns the four frozen keyword sets (SV, C++, Python hard, Python soft) and the `keyword_languages(identifier)` classifier helper. Includes the NFR-5 top-of-file comment block recording standard refs and authoring decisions.

## Key Implementation Decisions

- **SV keyword set: 1800-2017 ∪ 1800-2023.** After cross-checking against the IEEE 1800-2017 Annex B reserved-keyword list and the SV keyword tables in Verilator's lexer source, the conclusion is that 1800-2023 adds no new reserved keywords over 1800-2017 (it is a maintenance revision focused on clarifications, not new lex tokens). The comment block records this finding explicitly so a future auditor can re-verify; if a 2023 addition is later identified, the implementer can append and bump the comment.
- **`soft`, `nettype`, `interconnect` are 1800-2017, not 2023.** All three are present in 1800-2017 Annex B (they were introduced in earlier revisions: `soft` in 1800-2009 for distribution constraints, `nettype` in 1800-2012 for user-defined nettypes, `interconnect` in 1800-2017). They appear in the 1800-2017 list and are included accordingly.
- **C++ set composition.** Sourced from N4861 §2.13 reserved keywords (including coroutine `co_await`/`co_yield`/`co_return`); plus alternative tokens (digraph operators); plus contextual identifiers `import` and `module`. Excludes `final` and `override`. C++ count = 94 (verified via `len(CPP_KEYWORDS)`).
- **Python sets.** Captured as literal frozensets matching CPython 3.12.x `keyword.kwlist` (35 entries) and `keyword.softkwlist` (4 entries). Cross-verified that the system Python 3.13.11 reports identical content for both lists, confirming stability across 3.12-3.13. The snapshot test (T-002) gates on `(3, 12)` per spec.
- **`keyword_languages` sort key.** Sort uses Python's default string ordering on the labels themselves (`"C++" < "Python" < "Python (soft)" < "SystemVerilog"`). Hard Python wins over soft Python via `if/elif`. Returns `tuple[str, ...]` (immutable, hashable).
- **No `keyword` stdlib import in `keywords.py`.** NFR-4 requires no runtime dep on `keyword`. The stdlib module is only imported in `tests/test_keyword_set_snapshot.py`.

## Deviations from Plan

None. The plan §Components C-1 specified the public surface (four frozen sets, one classifier function, top-of-file comment with three required content items). The implementation matches.

## Tests Added

T-002 covers the Python snapshot. Sanity smoke checks were also run inline:

| Identifier | Expected | Got |
|------------|----------|-----|
| `'type'` (Python soft + SV) | `('Python (soft)', 'SystemVerilog')` | ✓ |
| `'type_id'` (no collision) | `()` | ✓ |
| `'class'` (C++ + Python + SV) | `('C++', 'Python', 'SystemVerilog')` | ✓ |
| `'WHILE'` (exact-case, no collision) | `()` | ✓ |
| `'while'` (lowercase, all 3) | `('C++', 'Python', 'SystemVerilog')` | ✓ |
| `'try'` (C++ + Python) | `('C++', 'Python')` | ✓ |
| `'logic'` (SV only) | `('SystemVerilog',)` | ✓ |
| `'logic_pkg'` (no collision) | `()` | ✓ |

`basedpyright src/piketype/validate/keywords.py` returns 0 errors.

Sizes: SV=248, C++=94, Python hard=35, Python soft=4.
