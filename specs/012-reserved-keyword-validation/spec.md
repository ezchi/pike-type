# Specification — Reserved Keyword Validation

**Spec ID:** 012-reserved-keyword-validation
**Branch:** `feature/012-reserved-keyword-validation`
**Status:** draft (clarification iteration 1)

## Overview

`piketype` generates SystemVerilog, C++20, and Python 3.12 outputs from a single DSL definition. Today, a DSL author can name a type, struct field, enum value, flags field, constant, or module in a way that collides with a reserved keyword in one of the target languages. The collision is silent in the DSL layer and only surfaces as a downstream compile error in the generated artifacts.

Example (illegal under this spec):

```python
foo_t = (
    Struct()
    .add_member("type", Logic(2))   # `type` is a SystemVerilog keyword
)
```

This feature adds an explicit validation pass that rejects DSL inputs whose user-supplied identifiers — **as emitted standalone in any generated file** — collide with the reserved keyword set of any active target language. The check fails fast at `piketype gen` validation time with an actionable error pointing at the offending identifier and the language(s) it conflicts with.

This is a **correctness-over-convenience** validation per Constitution principle 4: if it cannot compile in one of the target languages, it must not be generated.

## User Stories

- **US-1.** As a DSL author, I want `piketype gen` to reject a struct field named `type` before any code is generated, so that I do not waste time chasing a downstream `syntax error` from `verilator` / `g++` / `python -c`.
- **US-2.** As a DSL author who learned C++ but not SystemVerilog, I want the error message to tell me *which* target language reserves the identifier, so that I can pick a non-colliding name without consulting three language standards.
- **US-3.** As a maintainer, I want the keyword sets to be data-driven (one frozen set per language, sourced from the language standard), so that adding a new target language or rev'ing a language standard is a one-file change with zero logic edits.
- **US-4.** As a CI maintainer, I want existing fixtures and goldens to continue passing untouched, so that this feature ships without churn on unrelated golden trees. (If any current fixture happens to use a now-rejected name, that is a defect in the fixture and must be renamed as part of this change.)

## Functional Requirements

### FR-1. Identifiers in scope

The validation pass MUST check the following user-supplied identifiers from the frozen IR. Each entry below names exactly the identifier that appears **standalone** as a token in at least one generated file:

1. Every `type_ir.name` (struct, flags, enum, scalar alias). The full name (e.g. `foo_t`) is checked. The base form with the `_t` suffix stripped (e.g. `foo`) is **NOT** checked: the base only appears as a substring of larger generated identifiers (`pack_foo`, `unpack_foo`, `LP_FOO_WIDTH`, `foo_ct`), each of which is a single token in the target language and therefore cannot collide with a keyword. (The `_ct` suffix on the C++/Python wrapper class similarly insulates the base from C++/Python keyword collisions.)
2. Every struct field `name` (emitted as a SV typedef field, C++ struct member, Python attribute).
3. Every flags field `name` (in addition to the existing `_pad` and reserved-API checks).
4. Every enum value `name` (in addition to the existing UPPER_CASE rule).
5. Every constant `name` (emitted as a SV `localparam`, C++ `constexpr`, Python module attribute).
6. Every module's `python_module_name` (the file basename). The check is **per-language emitted form**, not bare-base against all sets:
   - **SystemVerilog**: the emitted package identifier is `<base>_pkg`. Check `<base>_pkg` against the SV keyword set. (`logic_pkg` is not a keyword even though `logic` is — so a module named `logic.py` is accepted at the SV layer.)
   - **C++**: the emitted namespace identifier is `<base>`. Check `<base>` against the C++ keyword set.
   - **Python**: the emitted submodule identifier is `<base>`. Check `<base>` against the Python keyword set.

   The error message MUST report the offending emitted form per language (e.g. `module name 'class' is a reserved keyword in target language(s): C++, Python`). The bare base name is only at risk for C++/Python; only a `<sv-keyword>_pkg` collision could trip the SV side, which is astronomically rare but checked anyway for symmetry.

### FR-2. Target languages and keyword sources

The validation MUST check identifiers against three frozen keyword sets:

- **SystemVerilog**: The **union** of IEEE 1800-2017 reserved keywords and the additions introduced in IEEE 1800-2023 (e.g. `nettype`, `interconnect`). The keyword module's comment lists the 2023-only additions explicitly so a reader can audit the source against either standard.
- **C++**: ISO C++20 reserved keywords (including the coroutine keywords `co_await`, `co_yield`, `co_return`, which are language-level reserved keywords, not contextual identifiers) plus alternative tokens (`and`, `or`, `not`, `xor`, `bitand`, `bitor`, `compl`, `and_eq`, `or_eq`, `xor_eq`, `not_eq`). C++20 contextual identifiers `import` and `module` MUST also be included because they participate in module-declaration parsing and present a forward-compat risk for hardware DSL authors who pick `import.py` or `module.py` as a module filename. Contextual identifiers `final` and `override` MUST NOT be included; they are legal as identifiers in any non-declarator position and rejecting them would over-restrict per Constitution principle 4.
- **Python**: A static snapshot of `keyword.kwlist` ∪ `keyword.softkwlist` taken from CPython 3.12.x at spec-freeze time, captured as a literal `frozenset` in the keyword module. Snapshotting (rather than late-binding to the running interpreter's `keyword` module) preserves byte-identical error output across patch-level Python upgrades, in service of Constitution principle 3 (Determinism).

Each keyword set MUST be a `frozenset[str]` defined in a single dedicated module (proposed: `src/piketype/validate/keywords.py`) with one constant per language and a documented standard reference. The validation pass MUST NOT compute keyword sets at module load by introspecting target compilers.

### FR-3. Validation rule

For each in-scope identifier, the pass MUST:

1. Look up the identifier in each language's keyword set.
2. If the identifier is a member of any keyword set, raise `ValidationError` with a message that:
   - Names the offending identifier verbatim (preserving case).
   - States the IR location (module path, type name, field/value name as applicable).
   - Lists every target language whose keyword set contains it (a single identifier may collide with multiple languages, e.g. `template` is reserved in C++ but not SV/Python; `for` is reserved in all three).
   - Suggests renaming.

Concrete error message shape, normative:

```
{module_repo_relative_path}: {kind} {context_name} {field_or_value} '{identifier}' is a reserved keyword in target language(s): {comma_separated_languages}. Rename it.
```

Where:
- `{kind}` is one of `struct`, `flags`, `enum`, `scalar alias`, `constant`, `module name`.
- `{context_name}` is the enclosing type name when applicable (e.g. `foo_t`); omitted with the preceding space when the identifier itself is the type or module name.
- `{field_or_value}` is `field`, `flag`, or `value` as appropriate; omitted (with the preceding space) when not applicable.
- `{comma_separated_languages}` is alphabetically sorted: `C++`, `Python`, `SystemVerilog`. Soft-keyword status is annotated inline only when the language *only* matches as a soft keyword: `Python (soft)`.

Worked examples (used as golden expected-error strings; language list always alphabetically sorted):

```
foo.py: struct foo_t field 'type' is a reserved keyword in target language(s): Python (soft), SystemVerilog. Rename it.
bar.py: constant 'for' is a reserved keyword in target language(s): C++, Python, SystemVerilog. Rename it.
class.py: module name 'class' is a reserved keyword in target language(s): C++, Python. Rename it.
```

Note that `type` is a Python 3.12 soft keyword and is therefore reported as `Python (soft)`, while `class` is a Python hard keyword and is reported as `Python` (no annotation).

### FR-4. Comparison semantics

- The comparison MUST be **exact-case** for all three languages. SystemVerilog, C++, and Python are all case-sensitive at the keyword level; `WHILE` is therefore not a collision with `while`. UPPER_CASE enum literals such as `WHILE` or `FOR` MUST pass keyword validation. (This is consistent with Constitution principle 4: the validator rejects only what would actually fail to compile.)
- The check is exact-token, not substring. `type_id` does not collide with `type`. `class_t` does not collide with `class`.
- Identifiers that already pass the existing `_t` suffix rule, UPPER_CASE rule, etc., are still subject to keyword check. Order: structural validations first, then keyword validation.

### FR-5. Validation entry point

The keyword check MUST run inside `validate_repo` in `src/piketype/validate/engine.py`, after existing structural validations and before any backend emission. It MUST be implemented as a private helper (e.g. `_validate_reserved_keywords`) called once per module for the per-module identifiers (FR-1.1 through FR-1.5), and once at repo level for the module-name check (FR-1.6). Per Constitution principle 4, no backend may emit code if any keyword check fails.

The keyword sets themselves live in `src/piketype/validate/keywords.py` as a sibling module (data, not logic). The existing `naming.py` and `cross_language.py` placeholder files MAY be repurposed or left untouched at planner discretion.

### FR-6. Error type

Violations MUST raise the existing `ValidationError` (`piketype.errors`). No new exception class.

### FR-7. Reporting strategy

The validator MUST follow the existing **first-fail** pattern used everywhere else in `engine.py`: on encountering the first reserved-keyword identifier in IR-declaration order, raise `ValidationError` and stop. Subsequent offenders are not collected. Iteration order MUST be deterministic and match existing patterns:

1. Repo iteration: modules in `repo.modules` order.
2. Within a module: constants in declaration order, then types in declaration order.
3. Within a type: fields/values in declaration order.

This satisfies Constitution principle 3 (Deterministic output): identical input → identical error message.

### FR-8. Active target languages

The check MUST run against **all three** target languages unconditionally. There is no DSL or CLI flag to disable a language's keyword set. The constitution mandates that all three backends emit from the same frozen IR; there is no "Python-only" mode in the pipeline today, so a per-language opt-out has no coherent semantics. A future iteration may add an opt-out if and when partial-target generation is added.

### FR-9. Interaction with existing checks

The keyword check MUST NOT replace or duplicate any existing validation. Specifically:

- `_validate_generated_identifier_collision` (FR-14 of the prior spec, in `engine.py`) checks user constants/enum-values against generated derived identifiers like `LP_<BASE>_WIDTH`. It is unrelated to language keywords and remains as-is.
- `_FLAGS_RESERVED_API_NAMES` (`value`, `to_bytes`, `from_bytes`, `clone`, `width`, `byte_count`) checks flag names against the generated runtime API surface. None of those names is a target-language keyword today, so the two checks are orthogonal. They MUST remain separate so that error messages stay precise (a `value` flag name is rejected for runtime-API collision, not for keyword collision).
- The `_pad` suffix check is orthogonal and unchanged.
- The `_t` suffix requirement and UPPER_CASE enum-value rule are orthogonal and unchanged.

If a single identifier could trip multiple checks (e.g. an enum value that is both a non-UPPER_CASE name AND a keyword), the existing structural check fires first per FR-4 ordering.

## Non-Functional Requirements

- **NFR-1. Performance.** The keyword check MUST add < 5 ms to `piketype gen` for the largest fixture currently in `tests/fixtures/`. Rationale: `frozenset` membership is O(1); identifier counts are in the low thousands at most.
- **NFR-2. Determinism.** Repeated runs on the same input produce the same error message byte-for-byte (Constitution principle 3). No environment, OS, locale, or Python patch-version dependence.
- **NFR-3. Test coverage.** Each in-scope identifier kind (FR-1.1 through FR-1.6) MUST have at least one negative-test fixture under `tests/fixtures/` with the matching expected-error golden. Specifically: one fixture per identifier kind × one fixture for a multi-language collision × one positive smoke fixture demonstrating that a near-miss like `type_id` passes. In addition, a unit test in `tests/` MUST verify that the Python keyword snapshot in `src/piketype/validate/keywords.py` equals `frozenset(keyword.kwlist) | frozenset(keyword.softkwlist)` when the running interpreter is Python 3.12.x (the test SHOULD skip with an explanatory message under any other Python minor version, since drift is then expected and governed by a separate Python-version-bump PR).
- **NFR-4. No external dependencies.** The implementation MUST NOT add new runtime dependencies. The Python keyword set is a literal `frozenset` snapshot per FR-2; the stdlib `keyword` module MAY be imported in a doctest or comment that documents the source-of-truth provenance, but MUST NOT be imported at runtime.
- **NFR-5. Documentation.** The `docs/` tree (architecture / RFC sections describing the validation pipeline) MUST be updated to mention the keyword pass. No new top-level docs file is required. The keyword module `src/piketype/validate/keywords.py` MUST contain a top-of-file comment recording: (a) the IEEE 1800 standard revisions consumed (1800-2017 + 1800-2023), (b) the ISO C++ standard revision (C++20) and any contextual-identifier inclusion/exclusion decisions, (c) the exact CPython 3.12 patch version from which the Python snapshot was taken (e.g. `3.12.7`).

## Acceptance Criteria

- **AC-1.** Given a DSL module with `Struct().add_member("type", Logic(2))`, `piketype gen` exits non-zero with an error message naming the field `'type'` and listing `Python (soft), SystemVerilog` as the conflicting languages (alphabetical order; soft annotation inline). No files are written under `gen/`. The exact stderr line matches the FR-3 shape and is captured as a golden expected-error string.
- **AC-2.** Given a DSL module with a struct field named `class`, `piketype gen` exits non-zero. The error names `C++, Python` as the conflicting languages. (`class_t` as a *type name* is **NOT** rejected because the full name `class_t` is not a keyword and the base form is never emitted standalone — see FR-1.1.)
- **AC-3.** Given a DSL module with an enum value named `WHILE`, `piketype gen` succeeds. Exact-case keyword matching means UPPER_CASE enum literals like `WHILE` or `FOR` are valid identifiers in all three target languages and pass keyword validation. (Other validations such as the UPPER_CASE rule and enum-literal collision rule still apply.)
- **AC-4.** Given a DSL module saved as `class.py`, `piketype gen` exits non-zero, naming `C++, Python` as the conflicting languages. The `_pkg` suffix on the SV side keeps the SV emitted form (`class_pkg`) from being a keyword. The C++ namespace `class` and the Python submodule import `class` both collide.
- **AC-4b.** Given a DSL module saved as `logic.py`, `piketype gen` succeeds. The SV emitted form `logic_pkg` is not a keyword. The C++ namespace `logic` and the Python module `logic` are not keywords in C++ or Python. Per-language emission-form checking accepts this case (FR-1.6).
- **AC-5.** Given a constant named `for`, `piketype gen` exits non-zero with `C++, Python, SystemVerilog` as the conflicting languages, alphabetically sorted.
- **AC-6.** Given a flags type with a field named `try`, `piketype gen` exits non-zero, naming `C++, Python` as the conflicting languages. The existing `_pad` and reserved-API checks continue to fire on those respective inputs (existing tests unchanged).
- **AC-7.** Given a struct field named `type_id`, `piketype gen` succeeds. The keyword check is exact-token: substrings and prefixes do not match.
- **AC-8.** All existing golden tests under `tests/goldens/gen/` pass byte-for-byte after this feature is enabled. Any fixture that incidentally uses a now-rejected name MUST be updated as part of this change, with the corresponding golden regenerated and the change-rationale recorded in the planning artifacts.
- **AC-9.** All keyword-set constants live in `src/piketype/validate/keywords.py`. Adding a new target language is a single-file edit (one new constant + one new branch in the keyword-check helper).
- **AC-10.** Running `piketype gen` twice on the same input yields identical stdout/stderr, including error messages from this validator (Constitution principle 3 + NFR-2).
- **AC-11.** The keyword check does not run if a structural validation (e.g. duplicate field name, missing `_t` suffix, non-UPPER_CASE enum value) fires earlier on the same identifier. Order is enforced by FR-5 placement; tested by a fixture that has both a structural defect and a keyword collision on the same identifier — only the structural error is reported.

## Out of Scope

- Renaming auto-generated derived names. The check covers user-supplied identifiers only. Generated derived names (`pack_<base>`, `LP_<BASE>_WIDTH`, `<base>_ct`, etc.) are full-token identifiers in the target language and are not at risk of keyword collision; no validation needed.
- C and SystemC keyword sets. C++ is the only C-family target.
- VHDL, Chisel, or any non-listed target language.
- Compiler-specific reserved identifiers (e.g. GCC `__attribute__`, Verilator pragmas). Only language-standard keywords.
- Macro names or preprocessor identifiers in C++ (`INT_MAX`, `NULL`). Not language keywords.
- Renaming user identifiers automatically (e.g. appending `_`). The validator rejects, it does not rewrite.
- Identifier *length* limits. Out of scope; this feature is keyword identity only.
- Unicode normalization. The DSL is ASCII per the existing convention.
- Per-language opt-out / CLI escape hatch. Deferred until partial-target generation exists.
- Case-insensitive collision detection. Out of scope per FR-4.

## Open Questions

(None. All previously open questions resolved during the clarification stage; see `clarifications.md`.)

## Changelog

- [Clarification iter1] FR-2 (SV): Resolved Q1 — committed to the union of IEEE 1800-2017 + 1800-2023 reserved keywords. Rationale: Constitution principle 4 (correctness over convenience) and asymmetric cost of false-negative vs. false-positive. See `clarifications.md` Q1.
- [Clarification iter1] FR-2 (C++): Resolved Q2 — corrected the classification of `co_await`/`co_yield`/`co_return` (these are reserved C++20 keywords, not contextual identifiers) and pinned the contextual-identifier inclusion list (`import`, `module` IN; `final`, `override` OUT). See `clarifications.md` Q2.
- [Clarification iter1] NFR-3: Added a unit-test requirement that the Python keyword snapshot equals `frozenset(keyword.kwlist) | frozenset(keyword.softkwlist)` when the running interpreter is Python 3.12.x, with skip-on-other-versions semantics. See `clarifications.md` Q7.
- [Clarification iter1] NFR-5: Added a documentation requirement that `keywords.py` records the SV/C++ standard revisions consumed and the exact CPython 3.12 patch version of the Python snapshot. See `clarifications.md` Q7.
