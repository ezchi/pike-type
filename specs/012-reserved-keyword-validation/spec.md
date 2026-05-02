# Specification — Reserved Keyword Validation

**Spec ID:** 012-reserved-keyword-validation
**Branch:** `feature/012-reserved-keyword-validation`
**Status:** draft (iteration 1)

## Overview

`piketype` generates SystemVerilog, C++20, and Python 3.12 outputs from a single DSL definition. Today, a DSL author can name a type, struct field, enum value, flags field, constant, or module in a way that collides with a reserved keyword in one of the target languages. The collision is silent in the DSL layer and only surfaces as a downstream compile error in the generated artifacts (or worse, miscompiled code if the keyword is context-sensitive).

Example (illegal under this spec):

```python
foo_t = (
    Struct()
    .add_member("type", Logic(2))   # `type` is a SystemVerilog keyword
)
```

This feature adds an explicit validation pass that rejects DSL inputs whose user-supplied identifiers collide with the reserved keyword set of any active target language. The check fails fast at `piketype gen` validation time with an actionable error pointing at the offending identifier and the language(s) it conflicts with.

This is a **correctness-over-convenience** validation per Constitution principle 4: if it cannot compile in one of the target languages, it must not be generated.

## User Stories

- **US-1.** As a DSL author, I want `piketype gen` to reject a struct field named `type` before any code is generated, so that I do not waste time chasing a downstream `syntax error` from `verilator` / `g++` / `python -c`.
- **US-2.** As a DSL author who learned C++ but not SystemVerilog, I want the error message to tell me *which* target language reserves the identifier, so that I can pick a non-colliding name without consulting three language standards.
- **US-3.** As a maintainer, I want the keyword sets to be data-driven (one frozen set per language, sourced from the language standard), so that adding a new target language or rev'ing a language standard is a one-file change with zero logic edits.
- **US-4.** As a CI maintainer, I want existing fixtures and goldens to continue passing untouched, so that this feature ships without churn on unrelated golden trees. (If any current fixture happens to use a now-reserved name, that is a defect in the fixture and must be renamed as part of this change.)

## Functional Requirements

### FR-1. Identifiers in scope

The validation pass MUST check the following user-supplied identifiers from the frozen IR:

1. Every `type_ir.name` (struct, flags, enum, scalar alias). Both the full name (e.g. `foo_t`) and the base form with the `_t` suffix stripped (e.g. `foo`) are checked, because the base form participates in generated identifiers like `pack_<base>`, `unpack_<base>`, `LP_<BASE>_WIDTH`.
2. Every struct field `name`.
3. Every flags field `name` (in addition to the existing `_pad` and reserved-API checks).
4. Every enum value `name` (in addition to the existing UPPER_CASE rule).
5. Every constant `name`.
6. Every module's `python_module_name` (the file basename), because it is emitted as the SV `<base>_pkg` package name, the C++ namespace, and the Python submodule name.

### FR-2. Target languages and keyword sources

The validation MUST check identifiers against three frozen keyword sets:

- **SystemVerilog**: IEEE 1800-2017 reserved keywords. [NEEDS CLARIFICATION: confirm 1800-2017 vs 1800-2023; Verilator currently targets 1800-2017 idioms, but the project may want forward compatibility with -2023 additions like `nettype`, `interconnect`.]
- **C++**: ISO C++20 reserved keywords plus alternative tokens (`and`, `or`, `not`, `xor`, `bitand`, `bitor`, `compl`, `and_eq`, `or_eq`, `xor_eq`, `not_eq`). [NEEDS CLARIFICATION: include C++20 contextual identifiers like `final`, `override`, `import`, `module`? They are not reserved keywords but using them as type/member names is fragile.]
- **Python**: Python 3.12 hard keywords from `keyword.kwlist` plus soft keywords from `keyword.softkwlist` (`match`, `case`, `type`, `_`). [NEEDS CLARIFICATION: should we use the `keyword` stdlib module at runtime, or freeze the literal set at spec-time for determinism?]

Each keyword set MUST be a `frozenset[str]` defined in a single dedicated module (proposed: `src/piketype/validate/keywords.py`) with one constant per language and a documented standard reference. The validation pass MUST NOT compute keyword sets at module load by introspecting target compilers.

### FR-3. Validation rule

For each in-scope identifier, the pass MUST:

1. Look up the identifier in each language's keyword set.
2. If the identifier is a member of any keyword set, raise `ValidationError` with a message that:
   - Names the offending identifier verbatim (preserving case).
   - States the IR location (module path, type name, field/value name as applicable).
   - Lists every target language whose keyword set contains it (a single identifier may collide with multiple languages, e.g. `template` is reserved in C++ but not SV/Python; `type` is reserved in SV and a Python soft keyword).
   - Suggests renaming.

Example error text (target shape, exact wording finalized by Forge):

```
my_pkg/foo.py: struct foo_t field 'type' is a reserved keyword in target languages: SystemVerilog, Python (soft). Rename the field.
```

### FR-4. Comparison semantics

- The comparison MUST be **exact-case** for all three languages. SystemVerilog and C++ are case-sensitive; Python is case-sensitive. `Type` is therefore not a collision with `type`.
- Identifiers that already pass the existing `_t` suffix rule, UPPER_CASE rule, etc., are still subject to keyword check. Order: structural validations first, then keyword validation, so error messages remain layered (one defect at a time per identifier where practical).

### FR-5. Validation entry point

The keyword check MUST run inside `validate_repo` in `src/piketype/validate/engine.py`, after existing structural validations and before any backend emission. It MUST be implemented as a private helper (e.g. `_validate_reserved_keywords`) called once per module, then once at repo level for the module-name check. Per Constitution principle 4, no backend may emit code if any keyword check fails.

### FR-6. Error type

Violations MUST raise the existing `ValidationError` (`piketype.errors`). No new exception class.

### FR-7. Determinism

When multiple identifiers in the same module are reserved, the validator MUST report them in a deterministic order: module declaration order for types and constants, declaration order for fields/values within a type. The first offender MUST be raised; later offenders need not be batched, matching existing validator behavior. [NEEDS CLARIFICATION: do we want batched reporting (collect all errors, raise one combined error) or first-fail (current pattern)? Current validator is first-fail.]

### FR-8. Active target languages

The check MUST run against **all three** target languages unconditionally. There is no DSL or CLI flag to disable a language's keyword set in this iteration. [NEEDS CLARIFICATION: should there be a CLI escape hatch like `--skip-keyword-check=cpp` for users who never emit C++? The constitution says "if something cannot be validated, it should not be generated" — defaulting to all-on is consistent.]

## Non-Functional Requirements

- **NFR-1. Performance.** The keyword check MUST add < 5 ms to `piketype gen` for the largest fixture currently in `tests/fixtures/`. Rationale: `frozenset` membership is O(1); the total number of identifiers in any realistic repo is in the low thousands.
- **NFR-2. Determinism.** Repeated runs on the same input produce the same error message byte-for-byte (Constitution principle 3).
- **NFR-3. Test coverage.** Each in-scope identifier kind (FR-1.1 through FR-1.6) MUST have at least one negative-test fixture under `tests/fixtures/` with the matching expected-error golden. At least one positive smoke test MUST confirm a previously-borderline identifier (e.g. a struct field named `type_id`, which contains the substring `type` but is not itself a keyword) passes.
- **NFR-4. No external dependencies.** The implementation MUST NOT add new runtime dependencies. The Python keyword set MAY use the stdlib `keyword` module *if* its values are captured into a frozen set at module load (snapshot, not late-bound), to preserve byte-for-byte determinism across Python patch releases. [NEEDS CLARIFICATION: confirm snapshot vs live `keyword.kwlist` lookup.]
- **NFR-5. Documentation.** The `docs/` tree (architecture / RFC sections describing the validation pipeline) MUST be updated to mention the keyword pass. No new top-level docs file is required.

## Acceptance Criteria

- **AC-1.** Given a DSL module with `Struct().add_member("type", Logic(2))`, `piketype gen` exits non-zero with an error message naming the field `'type'` and listing SystemVerilog (and Python soft) as the conflicting language(s). No files are written under `gen/`.
- **AC-2.** Given a DSL module with a type named `class_t`, `piketype gen` exits non-zero. Both the full name `class_t` *and* the base form `class` are reported; the error names C++ as a conflicting language. (Rationale: the base `class` participates in `pack_class`, `LP_CLASS_WIDTH`.)
- **AC-3.** Given a DSL module with an enum value named `WHILE` (UPPER_CASE, otherwise valid), `piketype gen` exits non-zero with an error naming SV (`while`) and C++ (`while`) — but only if FR-4's case rule is relaxed for case-insensitive collision in SV/C++. [NEEDS CLARIFICATION: SV is case-sensitive at the language level; `WHILE` is *not* the keyword `while`. AC-3 is included to flush out whether the team wants case-insensitive collision detection for hardware-domain-style UPPER_CASE enum literals. Default per FR-4: exact-case, so this AC currently expects PASS, not FAIL. Author should confirm.]
- **AC-4.** Given a DSL module saved as `class.py` (so the SV package would be `class_pkg`, the C++ namespace `class`), `piketype gen` exits non-zero, naming C++ as the conflicting language for the module name `class`. The `_pkg` suffix does not save the SV side from collision because the C++ side has no suffix.
- **AC-5.** Given a constant named `for`, `piketype gen` exits non-zero, naming SV, C++, and Python.
- **AC-6.** Given a flags type with a field named `try`, `piketype gen` exits non-zero, naming C++ and Python. The existing `_pad` and reserved-API checks continue to fire on those respective inputs (existing tests unchanged).
- **AC-7.** Given a struct field named `type_id` (substring of a keyword, but not itself a keyword), `piketype gen` succeeds. The keyword check does not match prefixes or substrings.
- **AC-8.** All existing golden tests under `tests/goldens/gen/` pass byte-for-byte after this feature is enabled. Any fixture that incidentally uses a now-rejected name MUST be updated as part of this change, with the corresponding golden regenerated.
- **AC-9.** All keyword-set constants live in a single source file. Adding a new target language is a single-file edit (one new constant + one new branch in the keyword-check helper).
- **AC-10.** Running `piketype gen` twice on the same input yields identical stdout/stderr, including error messages from this validator (Constitution principle 3 + NFR-2).

## Out of Scope

- Renaming auto-generated names. The check covers user-supplied identifiers only. Generated derived names (`pack_<base>`, `LP_<BASE>_WIDTH`, etc.) are validated indirectly via the base-name check.
- C and SystemC keyword sets. C++ is the only C-family target.
- VHDL, Chisel, or any non-listed target language.
- Compiler-specific reserved identifiers (e.g. GCC `__attribute__`, Verilator pragmas). Only language-standard keywords.
- Macro names or preprocessor identifiers in C++ (`INT_MAX`, `NULL`). Not language keywords.
- Renaming user identifiers automatically (e.g. appending `_`). The validator rejects, it does not rewrite.
- Identifier *length* limits. Out of scope; this feature is keyword identity only.
- Unicode normalization. The DSL is ASCII per the existing convention.

## Open Questions

1. **[NEEDS CLARIFICATION]** SystemVerilog standard revision: 1800-2017 vs 1800-2023? (FR-2)
2. **[NEEDS CLARIFICATION]** C++ contextual identifiers (`final`, `override`, `import`, `module`): include in the C++ set or not? (FR-2)
3. **[NEEDS CLARIFICATION]** Python keyword source: snapshot of `keyword.kwlist` at spec-freeze time, or live `keyword.kwlist` lookup at validation time? Snapshot favors determinism across Python patch releases; live lookup auto-updates with the toolchain. (FR-2, NFR-4)
4. **[NEEDS CLARIFICATION]** Case sensitivity for SV/C++: exact-case (current FR-4) or case-insensitive? UPPER_CASE enum literals like `WHILE` would pass under exact-case but fail under case-insensitive. (FR-4, AC-3)
5. **[NEEDS CLARIFICATION]** Error reporting strategy: first-fail (current validator pattern) or batched (collect all keyword violations and raise one combined error)? (FR-7)
6. **[NEEDS CLARIFICATION]** CLI escape hatch (`--skip-keyword-check=<lang>`): include in this iteration or defer? (FR-8)
7. **[NEEDS CLARIFICATION]** Should the base form (without `_t`) of every type name be checked, or only the full name? FR-1.1 currently says both; confirm. (FR-1)
8. **[NEEDS CLARIFICATION]** Should we also check **constant base names** for the `LP_<BASE>_*` macro side, analogous to type base names? Constants are emitted directly without a base form, so probably not — confirm.
