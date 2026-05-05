# Task 4: Add `_validate_reserved_keywords` and format helpers in engine.py — Forge Iteration 1

## Files Changed

- `src/piketype/validate/engine.py` — modified. Added imports from `piketype.validate.keywords` and four new helpers at the bottom of the file:
  - `_format_top_level_msg(*, module_path, kind, identifier, langs)` — FR-3 message for constants, types, module names.
  - `_format_field_msg(*, module_path, kind, type_name, role, identifier, langs)` — FR-3 message for nested identifiers (struct fields, flags flags, enum values).
  - `_module_name_languages(*, basename)` — per-language emitted-form lookup (FR-1.6); SV checks `<basename>_pkg`, C++/Python check the bare basename.
  - `_validate_reserved_keywords(*, repo)` — main pass; iterates in deterministic IR-declaration order; first-fail.
  - `_type_kind(*, type_ir)` — small helper that maps an IR type node to its user-facing kind label (`struct`/`flags`/`enum`/`scalar alias`).

## Key Implementation Decisions

- **Module-name lookup uses a separate helper.** `_module_name_languages` is needed because the per-language emitted form differs (SV: `<base>_pkg`; C++/Python: bare base). The general-purpose `keyword_languages(identifier=...)` from `keywords.py` is used for all other (uniform) cases.
- **Iteration order matches the plan §C-2 spec exactly.** Module-name → constants → types → fields/flags/values. Each level deterministic (declaration order from the frozen IR tuples).
- **First-fail via `raise` in the inner-most loop.** No collection of multiple violations; matches existing engine.py pattern (e.g. `_validate_pad_suffix_reservation`).
- **`_type_kind` instead of inline `isinstance` cascade in `_format_top_level_msg`.** Keeps the top-level-message helper clean and lets the type-kind label be reused if other top-level messages are added later. The constitution prefers pattern matching for IR dispatch but `isinstance` is the existing local idiom in this file (see `_validate_struct_cycles`); used the local idiom for consistency.
- **All new helpers use `*` keyword-only args.** Matches the universal pattern in `engine.py` and the constitution.
- **No call site yet.** This task explicitly does NOT add `_validate_reserved_keywords(repo=repo)` to `validate_repo`. T-005 is the wiring step. Pyright reports a temporary "unused function" warning that resolves in T-005.

## Deviations from Plan

None. The plan §Components C-2 prescribed the helper signatures and iteration order; the implementation follows.

## Tests Added

None at this step (T-005 wires; T-006/T-007 add the smoke fixture/test). Verification:

- `basedpyright src/` reports baseline 100 errors + 1 unused-function warning (`_validate_reserved_keywords`). The 100 baseline errors are pre-existing in the engine.py and other backend files (not introduced by this task). The unused-function warning will resolve when T-005 wires the helper.
- Existing `python -m unittest discover tests` still passes (294 tests, 3 skipped). No behavior change.
