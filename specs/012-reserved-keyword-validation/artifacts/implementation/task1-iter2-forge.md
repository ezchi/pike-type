# Task 1 — Forge Iteration 2 (REVISE response)

## Files Changed

- `src/piketype/validate/keywords.py` — modified. `keyword_languages(identifier: str)` → `keyword_languages(*, identifier: str)`. Single-line signature change to match the project's universal keyword-only convention for helpers (Constitution § Coding Standards / Python).

## Key Implementation Decisions

- **Accept Gauge feedback.** The Gauge correctly flagged the missing `*` per the constitution's "Keyword-only arguments for helper functions" rule. Existing helpers in `validate/engine.py` (e.g. `_validate_const_storage`, `_validate_struct_cycles`, `_validate_pad_suffix_reservation`, `_validate_alignment_bits`) all use `*` even for single-argument signatures. Aligning with that universal pattern.
- **Call-site impact.** The engine wiring in T-004 will use `keyword_languages(identifier=name)`. Updated mental model accordingly; the actual code change happens in T-004.

## Deviations from Plan

None. The plan §C-1 specified "keyword-only function args" matching the constitution.

## Tests Added

None changed; existing snapshot test still passes (skipped on Python 3.13). Sanity smoke checks re-run after the signature change:

```
keyword_languages(identifier='type')  -> ('Python (soft)', 'SystemVerilog')
keyword_languages(identifier='WHILE') -> ()
keyword_languages(identifier='for')   -> ('C++', 'Python', 'SystemVerilog')
```

`basedpyright` clean.
