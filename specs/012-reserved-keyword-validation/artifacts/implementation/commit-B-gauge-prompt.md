# Gauge Code Review Prompt — Commit B (Tasks T-004..T-008)

You are the Gauge for the implementation stage. The Forge committed code for spec `012-reserved-keyword-validation`, commit B. Produce **five separate VERDICT lines** — one per task.

You are NOT a cheerleader. Be strict. Reference file:line. Empty findings is a valid review when the code is clean.

## Inputs

1. Spec — `specs/012-reserved-keyword-validation/spec.md`
2. Plan — `specs/012-reserved-keyword-validation/plan.md`
3. Tasks — `specs/012-reserved-keyword-validation/tasks.md` (T-004..T-008)
4. Constitution — `.steel/constitution.md` § Coding Standards / Python and § Testing
5. Forge artifacts — `specs/012-reserved-keyword-validation/artifacts/implementation/task{4,5,6,7,8}-iter1-forge.md`
6. Code under review:
   - `src/piketype/validate/engine.py` (modified — new helpers + wire call)
   - `tests/fixtures/keyword_near_miss/project/alpha/piketype/types.py` (new)
   - `tests/goldens/gen/keyword_near_miss/...` (new — 13 generated files)
   - `tests/test_validate_keywords.py` (new)
7. Diff: `git log --oneline -5` from `/Users/ezchi/Projects/pike-type` shows commits `a1bbf7a` (B-1: T-004+T-005) and `c2ac696` (B-2: T-006+T-007+T-008). Inspect both via `git show <sha>`.

## Per-task review checklist

### T-004 — `_validate_reserved_keywords` and format helpers

1. Are the four new functions present at the bottom of `engine.py`? (`_format_top_level_msg`, `_format_field_msg`, `_module_name_languages`, `_validate_reserved_keywords`, `_type_kind`).
2. All keyword-only args (`*`)?
3. Iteration order matches plan §C-2: module-name (FR-1.6) → constants → types (full name) → fields/flags/values?
4. Module-name check uses `module.ref.basename` (per plan), not `python_module_name`?
5. Per-language emitted-form lookup in `_module_name_languages`: `<basename>_pkg` for SV, bare `basename` for C++/Python? Hard-Python-vs-soft-Python tiebreaker correct?
6. Error message shape strictly matches FR-3 normative format?
7. First-fail (`raise` in inner-most loop)? No collection?
8. New imports correct (CPP_KEYWORDS, PY_HARD_KEYWORDS, PY_SOFT_KEYWORDS, SV_KEYWORDS, keyword_languages)?

### T-005 — Wire + scan + repair

1. `_validate_reserved_keywords(repo=repo)` is the LAST line of `validate_repo` (after `_validate_cross_module_name_conflicts`)?
2. Atomic — no intermediate broken commits?
3. Forge claims zero incidental fixture breakage. Verify by running `python -m unittest discover tests`.
4. The placement matches FR-9 (structural validations first).

### T-006 — Positive smoke fixture

1. Fixture file `tests/fixtures/keyword_near_miss/project/alpha/piketype/types.py` defines `near_miss_t` with `type_id` field?
2. Two-field struct (avoids min-field structural rule firing first)?
3. Golden tree under `tests/goldens/gen/keyword_near_miss/` is a complete generated tree (SV, C++, Python, manifest, runtime)?
4. Any unrelated existing goldens modified? (Should be NO.)

### T-007 — `tests/test_validate_keywords.py`

1. Imports shared helpers from `tests.test_gen_const_sv` (FIXTURES_DIR, GOLDENS_DIR, PROJECT_ROOT, copy_tree, assert_trees_equal)?
2. `KeywordValidationTest(unittest.TestCase)` with local `run_piketype` matching the existing pattern?
3. `test_keyword_near_miss_type_id_passes` follows the positive-test convention (returncode == 0, assert_trees_equal)?
4. `from __future__ import annotations` present?

### T-008 — Verify byte parity (verification only)

1. Forge claims pyright at baseline (no new errors over baseline).
2. Forge claims 295 tests OK (3 skipped).
3. Forge claims no existing goldens modified.
4. Confirm by inspecting `git diff --stat` of commit B vs. commit A.

## Output format

```
# Gauge Code Review — Commit B

## Per-task assessment

### T-004 — `_validate_reserved_keywords` + format helpers
(Findings.)
VERDICT-T004: APPROVE | REVISE

### T-005 — Wire + scan + repair
(Findings.)
VERDICT-T005: APPROVE | REVISE

### T-006 — Positive smoke fixture
(Findings.)
VERDICT-T006: APPROVE | REVISE

### T-007 — Test file + smoke test
(Findings.)
VERDICT-T007: APPROVE | REVISE

### T-008 — Byte parity verification
(Findings.)
VERDICT-T008: APPROVE | REVISE

## Cross-task observations
```

Each VERDICT line is parsed verbatim. Use `VERDICT-T004:`, `VERDICT-T005:`, `VERDICT-T006:`, `VERDICT-T007:`, `VERDICT-T008:` exactly.
