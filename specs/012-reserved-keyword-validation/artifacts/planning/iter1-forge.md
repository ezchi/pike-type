# Implementation Plan — 012-reserved-keyword-validation

**Spec:** `specs/012-reserved-keyword-validation/spec.md` (post-clarification)
**Branch:** `feature/012-reserved-keyword-validation`
**Status:** draft (planning iteration 1)

## Architecture Overview

A single new validation pass, `_validate_reserved_keywords`, is added to `validate_repo` in `src/piketype/validate/engine.py`. It runs **after** all existing structural and cross-module validations and **before** any backend emission, consuming only frozen IR. The pass loads three frozen keyword sets — one per target language — from a new sibling module `src/piketype/validate/keywords.py`. On the first identifier collision in IR-declaration order, it raises the existing `ValidationError`; no behavior change to existing validations.

The change is strictly additive and respects the four-stage pipeline (Discovery → DSL → IR → Backends): the new pass is a leaf in the IR-consuming validate stage, with no upstream/downstream churn except for the documented in-source comment update under `keywords.py` and a one-line addition to the architecture doc.

```
RepoIR → validate_repo (engine.py)
                ├── existing structural / cycle / collision validations  [unchanged]
                └── _validate_reserved_keywords (NEW)
                            ├── per module:
                            │     • types, fields, flags fields, enum values, constants
                            └── per repo:
                                  • module basename × per-language emitted form
```

## Components

### C-1. `src/piketype/validate/keywords.py` (new)

**Responsibility.** Owns the three frozen keyword sets and the helper that classifies an identifier across them. Pure data + small lookup logic; no IR types referenced.

**Public surface.**

```python
SV_KEYWORDS: frozenset[str]              # IEEE 1800-2017 ∪ 1800-2023 additions
CPP_KEYWORDS: frozenset[str]             # ISO C++20 reserved + alt tokens + import/module
PY_HARD_KEYWORDS: frozenset[str]         # CPython 3.12.x keyword.kwlist snapshot
PY_SOFT_KEYWORDS: frozenset[str]         # CPython 3.12.x keyword.softkwlist snapshot

def keyword_languages(identifier: str) -> tuple[str, ...]:
    """Return alphabetically-sorted list of language labels in which `identifier`
    is a reserved keyword. Soft-only Python matches are reported as 'Python (soft)';
    hard Python matches are 'Python' (hard wins over soft). Empty tuple = no collision."""
```

The module's top-of-file comment records (NFR-5):
- IEEE 1800 standard revisions consumed (1800-2017 + 1800-2023) and an enumerated list of the 2023-only additions.
- ISO C++ standard revision (C++20) and the explicit inclusion (`import`, `module`) and exclusion (`final`, `override`) decisions, citing N4861 §2.13 for the coroutine-keyword classification.
- The CPython 3.12 patch version from which the Python snapshot was taken.

**Private helpers.** None initially. If sort-key logic grows beyond two lines, extract `_format_lang(label: str, soft: bool) -> str`.

### C-2. `_validate_reserved_keywords` in `src/piketype/validate/engine.py` (new helper)

**Responsibility.** Apply `keyword_languages` to every in-scope identifier (FR-1) in deterministic IR-declaration order. Raise `ValidationError` on first match.

**Signature.**

```python
def _validate_reserved_keywords(*, repo: RepoIR) -> None:
    """FR-1..FR-9: reject DSL identifiers that collide with target-language keywords."""
```

Called from `validate_repo` once at the end (after `_validate_repo_struct_cycles` and `_validate_cross_module_name_conflicts`). Per-module identifier checks (FR-1.1..FR-1.5) iterate `repo.modules`; the per-repo module-name check (FR-1.6) is folded into the same pass via per-language emitted-form lookups described below.

**Iteration order (matches FR-7).**

```
for module in repo.modules:                           # repo declaration order
    check module-name (FR-1.6)                        # per-language emitted form
    for const in module.constants:                    # declaration order
        check const.name
    for type_ir in module.types:                      # declaration order
        check type_ir.name (full, FR-1.1)
        if struct: for field in fields: check field.name
        if flags:  for flag in fields: check flag.name
        if enum:   for value in values: check value.name
```

**Module-name check (FR-1.6).** Per-language emitted form, **not** bare-base against all sets:

```python
base = module.ref.basename
sv_form  = f"{base}_pkg"          # SV emitted package name
cpp_form = base                    # C++ emitted namespace name
py_form  = base                    # Python submodule name

# Per-language individual lookups, then assemble combined language list.
hits: list[str] = []
if sv_form  in SV_KEYWORDS:                       hits.append("SystemVerilog")
if cpp_form in CPP_KEYWORDS:                      hits.append("C++")
if py_form  in PY_HARD_KEYWORDS:                  hits.append("Python")
elif py_form in PY_SOFT_KEYWORDS:                 hits.append("Python (soft)")
hits.sort()                                       # alphabetical per FR-3
if hits:
    raise ValidationError(_format_module_msg(...))
```

Note that `module.ref.basename` is the correct attribute (verified against `src/piketype/backends/sv/view.py:699` which uses `f"{module.ref.basename}_pkg"`). The spec's reference to `python_module_name` in FR-1.6 informally describes the same concept; the implementation uses `basename`.

**Error message construction.** A small private helper `_format_keyword_msg` enforces the FR-3 normative shape. Three specializations to keep the call site clean:

```python
def _format_field_msg(*, module_path, kind, type_name, role, identifier, langs)
def _format_top_level_msg(*, module_path, kind, identifier, langs)   # const, type, module
```

Where `kind ∈ {'struct', 'flags', 'enum', 'scalar alias', 'constant', 'module name'}`,
`role ∈ {'field', 'flag', 'value'}`,
`langs` is the alphabetically-sorted list returned by `keyword_languages` (already comma-joined when passed in).

### C-3. Existing placeholder modules

`src/piketype/validate/naming.py` and `src/piketype/validate/cross_language.py` are placeholder stubs (single docstring, no code). The plan does **not** touch them. The new `keywords.py` is a sibling module, named for what it owns (data, not a "naming" or "cross-language" concept).

### C-4. Documentation update

`docs/` will get one paragraph (location TBD during task breakdown — likely the `architecture.md` validation-pipeline section if it exists, otherwise the RFC for this feature) describing the new pass and its three keyword sources. NFR-5.

### C-5. Tests

- One golden-style negative test per identifier kind, plus one multi-language collision test, plus one positive smoke test (NFR-3). Test layout follows the repo convention: `tests/fixtures/<case>/project/...`, with the test asserting `result.returncode != 0` and `assertIn(<substring>, result.stderr)`. **Important:** the existing repo convention uses `assertIn` on a substring of stderr (see `test_gen_const_sv.py:242`), not byte-for-byte expected-error files. The plan adopts that same convention; the spec's mention of "captured as a golden expected-error string" in AC-1 is honored via stable substring assertions (the substring is the FR-3 normative shape, byte-stable across runs per Constitution principle 3).
- One unit test for the Python snapshot (NFR-3): in a new file `tests/test_keyword_set_snapshot.py`, assert that `PY_HARD_KEYWORDS == frozenset(keyword.kwlist)` and `PY_SOFT_KEYWORDS == frozenset(keyword.softkwlist)` when `sys.version_info[:2] == (3, 12)`; skip otherwise.

## Data Model

No IR changes. No new dataclasses. Three module-level frozen sets and two module-level helpers. The Python sets are literal-content snapshots, frozen at import time, captured directly from `keyword.kwlist` and `keyword.softkwlist` at the time of merge.

## API Design

### Public function

```python
# src/piketype/validate/keywords.py
def keyword_languages(identifier: str) -> tuple[str, ...]:
    """Return alphabetically-sorted language labels in which `identifier` is a
    reserved keyword. Empty tuple if no collision.

    Returned labels: 'C++', 'Python', 'Python (soft)', 'SystemVerilog'.
    'Python' (hard) is preferred over 'Python (soft)' if the identifier is in
    both sets (defensive; disjoint in CPython 3.12).
    """
```

This is the single import surface the engine helper uses for all per-identifier checks **except** the module-name check, which needs per-language individual lookups (because the emitted form differs per language). For the module-name case, the engine helper directly references `SV_KEYWORDS`, `CPP_KEYWORDS`, `PY_HARD_KEYWORDS`, `PY_SOFT_KEYWORDS`.

### Private helpers (engine.py)

```python
def _validate_reserved_keywords(*, repo: RepoIR) -> None
def _format_field_msg(*, module_path: str, kind: str, type_name: str, role: str, identifier: str, langs: list[str]) -> str
def _format_top_level_msg(*, module_path: str, kind: str, identifier: str, langs: list[str]) -> str
```

Keyword-only arguments per Constitution coding standard.

### Error message format (normative, from FR-3)

```
{module_repo_relative_path}: {kind} {context_name} {field_or_value} '{identifier}' is a reserved keyword in target language(s): {comma_separated_languages}. Rename it.
```

Worked examples produced by the formatters:

```
foo.py: struct foo_t field 'type' is a reserved keyword in target language(s): Python (soft), SystemVerilog. Rename it.
bar.py: constant 'for' is a reserved keyword in target language(s): C++, Python, SystemVerilog. Rename it.
class.py: module name 'class' is a reserved keyword in target language(s): C++, Python. Rename it.
foo.py: flags my_flags_t flag 'try' is a reserved keyword in target language(s): C++, Python. Rename it.
foo.py: enum my_enum_t value 'WHILE' is a reserved keyword in target language(s): C++, SystemVerilog. Rename it.   # only if WHILE were a keyword; AC-3 says it is not (exact-case)
```

## Dependencies

**No new runtime dependencies** (NFR-4 / Constitution principle 6). Only `frozenset` and the stdlib `keyword` module — and the `keyword` module is **only** used in the snapshot unit test, never at runtime.

**No new dev-tooling dependencies.** `basedpyright` strict mode and `unittest` continue to govern.

## Implementation Strategy

The work decomposes into four atomic, byte-parity-preserving commits per the project's "byte-parity at every commit" preference. Each commit is independently buildable, lint-clean, and test-passing.

### Commit A — Add `keywords.py` and unit test

- Create `src/piketype/validate/keywords.py` with the four frozen sets and `keyword_languages()` helper. Include the NFR-5 top-of-file comment.
- Create `tests/test_keyword_set_snapshot.py` with the Python-snapshot unit test (skip on != 3.12.x).
- No engine-level wiring yet. No fixtures. No goldens.
- **Byte parity:** existing goldens unchanged; existing tests unchanged; no behavior change.

### Commit B — Wire `_validate_reserved_keywords` into `engine.py`, add positive smoke fixture

- Add `_validate_reserved_keywords(*, repo)` and the two `_format_*_msg` helpers in `engine.py`.
- Call from end of `validate_repo`.
- Add **one** positive smoke fixture: a DSL repo with a struct field named `type_id` (near-miss; AC-7) under `tests/fixtures/keyword_near_miss/project/`. Expected golden output committed.
- Add the corresponding integration test in `tests/test_validate_engine.py` (preferred location, since the existing `test_gen_const_sv.py` is already large and this is a validate-layer concern).
- **Byte parity:** all existing goldens unchanged. The positive smoke fixture is a new fixture, so its golden is generated as part of this commit.

### Commit C — Add negative-test fixtures and tests for each identifier kind

Six negative-test fixtures (one per FR-1.1..FR-1.6 plus a multi-language collision case):

| Fixture                              | Target FR  | Identifier collision                   | Expected stderr substring                                                  |
|--------------------------------------|------------|----------------------------------------|----------------------------------------------------------------------------|
| `keyword_struct_field_type_sv`       | FR-1.2     | struct field `type` (SV + Py soft)     | `field 'type' is a reserved keyword in target language(s): Python (soft), SystemVerilog` |
| `keyword_flags_field_try_cpp_py`     | FR-1.3     | flags field `try` (C++ + Py)           | `flag 'try' is a reserved keyword in target language(s): C++, Python`      |
| `keyword_enum_value_for`             | FR-1.4     | enum value `for` (3 langs)             | (note: enum values are validated UPPER_CASE first; this fixture uses a raw enum value `for` to confirm UPPER_CASE rule fires before keyword rule, AC-11.) `value 'for' must be UPPER_CASE` |
| `keyword_constant_for`               | FR-1.5     | constant `for` (3 langs)               | `constant 'for' is a reserved keyword in target language(s): C++, Python, SystemVerilog` |
| `keyword_module_name_class`          | FR-1.6     | module file `class.py` (C++ + Py)      | `module name 'class' is a reserved keyword in target language(s): C++, Python` |
| `keyword_module_name_logic_passes`   | FR-1.6     | module file `logic.py` (positive)      | (no error; positive case for AC-4b)                                        |
| `keyword_type_name_class_t_passes`   | FR-1.1     | type `class_t` (positive, AC-2 nuance) | (no error; type-name `class_t` is not itself a keyword, base form not checked) |

Note that an enum-value-keyword collision **alone** is not directly testable because the UPPER_CASE structural check fires first (FR-9, AC-11). The matrix instead uses the `keyword_enum_value_for` fixture to *prove* that ordering — the test asserts the UPPER_CASE error fires, not the keyword error. This validates AC-11.

Add corresponding integration tests in `tests/test_validate_engine.py`. Each test follows the existing pattern: `result.returncode != 0` and `assertIn(<substring>, result.stderr)`.

- **Byte parity:** existing goldens unchanged. New fixtures produce no `gen/` outputs (they fail validation before emission), so no new goldens are added under `tests/goldens/gen/`.

### Commit D — Documentation

- One paragraph in the appropriate `docs/` file (`architecture.md` or equivalent — exact path determined during task breakdown after a quick `ls docs/`) describing the new pass.
- Update `CHANGELOG.md` (if the repo maintains one — to be confirmed during task breakdown).
- **Byte parity:** preserved; docs only.

### Sequencing rationale

- A is a pure data drop with a self-contained unit test → trivially byte-stable, can be reviewed in isolation.
- B wires the validator with one positive smoke test → exercises the helper without changing any negative output. New positive golden is *additive*.
- C adds the bulk of the negative tests → no goldens change because failed validation never reaches the emitter.
- D is docs only → zero-risk merge tail.

If any existing fixture under `tests/fixtures/` happens to use a now-rejected name (extremely unlikely; spot-check during commit C), that fixture's DSL is renamed and its golden regenerated as a separate sub-commit within commit C, with the change rationale recorded in commit message. AC-8 mandates this.

## Risks and Mitigations

### R-1. Fixture incidentally uses a now-rejected name (LIKELIHOOD: low; IMPACT: medium)

A fixture under `tests/fixtures/` happens to name a struct field, type, constant, or module file in a way that newly trips keyword validation. This would cause an existing golden test to flip from PASS to FAIL.

**Mitigation.** As the first action in commit C, run `piketype gen` over every existing fixture against the new validator to enumerate any breakage. For each break, rename the offending DSL identifier and regenerate the affected golden. Record the renames in the commit message. AC-8 mandates byte-for-byte stability of all unrelated goldens.

### R-2. Python snapshot drift on patch-version upgrade (LIKELIHOOD: low; IMPACT: low)

A future Python 3.12 patch release adds a soft keyword. The snapshot would drift from `keyword.kwlist | keyword.softkwlist`. NFR-3 unit test catches this on next CI run on the upgraded interpreter.

**Mitigation.** The snapshot test is the canary. When it fails, the maintainer updates `keywords.py` to match and bumps the patch-version comment. No silent drift possible.

### R-3. Cross-platform Python keyword variation (LIKELIHOOD: very low; IMPACT: low)

CPython, PyPy, etc. could in theory diverge in `keyword.kwlist`. The constitution mandates CPython 3.12+; PyPy is not a supported runtime. Snapshot is sourced from CPython 3.12.x.

**Mitigation.** Documented in NFR-5 in-source comment.

### R-4. Error-message wording churn (LIKELIHOOD: low; IMPACT: low)

A future maintainer rewords the error message format, breaking every negative-test substring assertion in commit C.

**Mitigation.** The substring assertions target the **structural** parts of the FR-3 format (e.g. `field 'type' is a reserved keyword in target language(s):`), not full lines. Any such rewording is itself a spec-level change requiring a spec/clarification update per the steel workflow. The brittleness here is by design — Constitution principle 3 (Determinism) wants exactly this regression net.

### R-5. Validator performance regression (LIKELIHOOD: very low; IMPACT: low)

Adding a per-identifier dictionary lookup × N identifiers × M languages is O(N) with a tiny constant. NFR-1 budgets < 5 ms; observation budget is 1 ms.

**Mitigation.** NFR-1 caps the budget. Add a microbench to `tests/test_perf_gen.py` if and only if the existing perf-gate machinery already covers this surface; otherwise skip — the algorithm is provably O(N) with frozen-set membership.

### R-6. AC-3 false-positive concern (case sensitivity)

The Gauge in iteration 2 was wary of `WHILE`-style hardware-style enum literals matching keyword sets case-insensitively. FR-4 commits to exact-case; AC-3 confirms `WHILE` *passes*.

**Mitigation.** AC-3 is encoded as an explicit positive smoke test in commit B's near-miss fixture (or a sibling fixture if needed), proving that exact-case is in effect. No code-level mitigation needed.

### R-7. Module-name check on `<base>_pkg` (LIKELIHOOD: nil; IMPACT: trivial)

FR-1.6 prescribes checking `<base>_pkg` against the SV keyword set for symmetry. The 1800-2017 ∪ 1800-2023 set contains no identifier ending in `_pkg`. The check is a free no-op in practice.

**Mitigation.** Implement the lookup anyway for symmetry and forward-compat. Cost is one set membership.

## Testing Strategy

### Test types

1. **Integration tests (golden-style, primary).** The new validator is exercised end-to-end via `piketype gen` over fixtures. Each test asserts non-zero exit and a stable stderr substring. Location: `tests/test_validate_engine.py`. Pattern: identical to `tests/test_gen_const_sv.py:test_rejects_pad_suffix_field`.

2. **Unit test (Python snapshot canary).** `tests/test_keyword_set_snapshot.py` asserts the snapshot equals the live `keyword.kwlist` / `softkwlist` when running on Python 3.12.x; skips otherwise. This catches accidental hand-edits and patch-version drift.

3. **Idempotency.** The new validator is a function of the frozen IR; it has no side effects. The existing idempotency tests cover this implicitly (running `piketype gen` twice produces identical stderr).

4. **Constitutional principle 3 (determinism).** The error-message format is byte-identical across runs by construction (alphabetically-sorted language list, frozen sets, no environmental input). No additional test needed beyond the substring assertions.

### Test matrix (commit C)

| Identifier kind        | Negative fixture                         | AC ref     |
|------------------------|------------------------------------------|------------|
| struct field           | `keyword_struct_field_type_sv`           | AC-1       |
| struct field           | (n/a — type_id positive, see B)          | AC-7       |
| flags field            | `keyword_flags_field_try_cpp_py`         | AC-6       |
| enum value             | `keyword_enum_value_for`                 | AC-11      |
| constant               | `keyword_constant_for`                   | AC-5       |
| module name (negative) | `keyword_module_name_class`              | AC-4       |
| module name (positive) | `keyword_module_name_logic_passes`       | AC-4b      |
| type (positive)        | `keyword_type_name_class_t_passes`       | AC-2       |
| ordering (struct)      | folded into `keyword_struct_field_type_sv` (asserts substring, proves key error wins over no-other-error) | implicit |

AC-2's negative half (struct field named `class` rejected) is folded into a sub-fixture of `keyword_struct_field_type_sv` or added as a sibling fixture; final shape determined during task breakdown.

AC-8 (existing goldens unchanged) is verified by running the existing test suite at every commit. AC-9 (one-file edit to add a language) is verified by code review of `keywords.py` (no integration test possible).

AC-10 (deterministic stderr) is verified by running the negative tests with `--repeat 2` (or a manual spot-check); deterministic-by-construction assertion stands.

### Pyright / lint

`basedpyright --strict` must pass with zero errors after every commit. The new module uses `from __future__ import annotations`, `frozenset[str]` type annotations, and `def fn(*, ...)` keyword-only parameters per Constitution coding standards.

## Out of Scope (Plan Layer)

Items in the spec's "Out of Scope" remain out of scope at the plan layer. In addition, the plan defers:

- A microbench for NFR-1. The algorithm's complexity is provably under-budget; only add a bench if perf regresses on the existing `test_perf_gen.py` suite.
- A CLI escape hatch. Spec FR-8 forbids it for this iteration.
- Refactoring the placeholder `naming.py` / `cross_language.py` modules. They are unused; touching them is out of scope for this feature.

## Phased Schedule

| Commit | Scope                                       | Approx LOC | Goldens churn | Risk |
|--------|---------------------------------------------|------------|---------------|------|
| A      | `keywords.py` + snapshot unit test          | ~120       | none          | nil  |
| B      | Engine wiring + positive smoke fixture      | ~150       | +1 new        | low  |
| C      | Negative fixtures + tests                   | ~200       | none          | low (R-1) |
| D      | Docs                                         | ~20        | none          | nil  |

LOC estimates exclude golden file content.
