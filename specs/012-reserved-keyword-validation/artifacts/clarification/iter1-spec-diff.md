# Spec Diff — Clarification Iteration 1

This file records exactly which sections of `spec.md` changed in clarification iteration 1, with before/after content for each change.

---

## Change 1 — Status banner

**Section.** Header (top of file).

**Before.**
```
**Status:** draft (iteration 3)
```

**After.**
```
**Status:** draft (clarification iteration 1)
```

**Rationale.** Track stage progression; this is now the post-spec-loop, post-clarification-iter-1 state.

---

## Change 2 — FR-2 SV bullet

**Section.** FR-2 / SystemVerilog bullet.

**Before.**
```
- **SystemVerilog**: IEEE 1800-2017 reserved keywords, plus the additions introduced in IEEE 1800-2023 (notably `nettype`, `interconnect`). Including the 2023 additions defends against forward-compat regressions for users on newer Verilator releases. [NEEDS CLARIFICATION: confirm 1800-2023 inclusion is acceptable; the alternative is 1800-2017 only, which is what current Verilator-targeted goldens assume.]
```

**After.**
```
- **SystemVerilog**: The **union** of IEEE 1800-2017 reserved keywords and the additions introduced in IEEE 1800-2023 (e.g. `nettype`, `interconnect`). The keyword module's comment lists the 2023-only additions explicitly so a reader can audit the source against either standard.
```

**Rationale.** Resolves Q1. Drops the [NEEDS CLARIFICATION] marker. Pins the union. Clarifies the auditing requirement on the keyword-module comment.

---

## Change 3 — FR-2 C++ bullet

**Section.** FR-2 / C++ bullet.

**Before.**
```
- **C++**: ISO C++20 reserved keywords plus alternative tokens (`and`, `or`, `not`, `xor`, `bitand`, `bitor`, `compl`, `and_eq`, `or_eq`, `xor_eq`, `not_eq`). C++20 contextual identifiers `import` and `module` MUST also be included because they tokenize as keywords inside `import`/`module` declarations (high collision risk for hardware DSL authors). Other contextual identifiers (`final`, `override`) MUST NOT be included; they are only meaningful in narrow grammatical positions and using them as field names is legal. [NEEDS CLARIFICATION: confirm `import`/`module` inclusion vs full `final`/`override`/`co_await`/etc. inclusion.]
```

**After.**
```
- **C++**: ISO C++20 reserved keywords (including the coroutine keywords `co_await`, `co_yield`, `co_return`, which are language-level reserved keywords, not contextual identifiers) plus alternative tokens (`and`, `or`, `not`, `xor`, `bitand`, `bitor`, `compl`, `and_eq`, `or_eq`, `xor_eq`, `not_eq`). C++20 contextual identifiers `import` and `module` MUST also be included because they participate in module-declaration parsing and present a forward-compat risk for hardware DSL authors who pick `import.py` or `module.py` as a module filename. Contextual identifiers `final` and `override` MUST NOT be included; they are legal as identifiers in any non-declarator position and rejecting them would over-restrict per Constitution principle 4.
```

**Rationale.** Resolves Q2. Drops the [NEEDS CLARIFICATION] marker. Fixes the iter-2 wording error that grouped `co_await`/`co_yield`/`co_return` with contextual identifiers (they are reserved keywords). Pins the contextual-identifier inclusion list.

---

## Change 4 — NFR-3 (test coverage)

**Section.** NFR-3.

**Before.**
```
- **NFR-3. Test coverage.** Each in-scope identifier kind (FR-1.1 through FR-1.6) MUST have at least one negative-test fixture under `tests/fixtures/` with the matching expected-error golden. Specifically: one fixture per identifier kind × one fixture for a multi-language collision × one positive smoke fixture demonstrating that a near-miss like `type_id` passes.
```

**After.**
```
- **NFR-3. Test coverage.** Each in-scope identifier kind (FR-1.1 through FR-1.6) MUST have at least one negative-test fixture under `tests/fixtures/` with the matching expected-error golden. Specifically: one fixture per identifier kind × one fixture for a multi-language collision × one positive smoke fixture demonstrating that a near-miss like `type_id` passes. In addition, a unit test in `tests/` MUST verify that the Python keyword snapshot in `src/piketype/validate/keywords.py` equals `frozenset(keyword.kwlist) | frozenset(keyword.softkwlist)` when the running interpreter is Python 3.12.x (the test SHOULD skip with an explanatory message under any other Python minor version, since drift is then expected and governed by a separate Python-version-bump PR).
```

**Rationale.** Resolves Q7. Adds an explicit unit-test requirement to catch accidental drift in the Python snapshot.

---

## Change 5 — NFR-5 (documentation)

**Section.** NFR-5.

**Before.**
```
- **NFR-5. Documentation.** The `docs/` tree (architecture / RFC sections describing the validation pipeline) MUST be updated to mention the keyword pass. No new top-level docs file is required.
```

**After.**
```
- **NFR-5. Documentation.** The `docs/` tree (architecture / RFC sections describing the validation pipeline) MUST be updated to mention the keyword pass. No new top-level docs file is required. The keyword module `src/piketype/validate/keywords.py` MUST contain a top-of-file comment recording: (a) the IEEE 1800 standard revisions consumed (1800-2017 + 1800-2023), (b) the ISO C++ standard revision (C++20) and any contextual-identifier inclusion/exclusion decisions, (c) the exact CPython 3.12 patch version from which the Python snapshot was taken (e.g. `3.12.7`).
```

**Rationale.** Resolves Q7. Pins the in-source documentation requirements so the planner and implementer have a clear bar.

---

## Change 6 — Open Questions section

**Section.** Open Questions.

**Before.**
```
## Open Questions

1. **[NEEDS CLARIFICATION]** SystemVerilog standard revision: include IEEE 1800-2023 additions (`nettype`, `interconnect`, etc.) on top of the 1800-2017 base? Including them defends against forward-compat regressions but rejects identifiers that compile fine on current Verilator. (FR-2)
2. **[NEEDS CLARIFICATION]** C++ contextual identifiers: include `import` and `module` only (current FR-2 default), or also include `final`, `override`, `co_await`, `co_yield`, `co_return`? `final`/`override` are legal as field names but may surprise reviewers who treat them as keywords. (FR-2)
```

**After.**
```
## Open Questions

(None. All previously open questions resolved during the clarification stage; see `clarifications.md`.)
```

**Rationale.** Both questions resolved. Cross-references the source-of-truth document for the resolution.

---

## Change 7 — Changelog (new section)

**Section.** Changelog (added at end of file).

**Before.** (section did not exist)

**After.**
```
## Changelog

- [Clarification iter1] FR-2 (SV): Resolved Q1 — committed to the union of IEEE 1800-2017 + 1800-2023 reserved keywords. Rationale: Constitution principle 4 (correctness over convenience) and asymmetric cost of false-negative vs. false-positive. See `clarifications.md` Q1.
- [Clarification iter1] FR-2 (C++): Resolved Q2 — corrected the classification of `co_await`/`co_yield`/`co_return` (these are reserved C++20 keywords, not contextual identifiers) and pinned the contextual-identifier inclusion list (`import`, `module` IN; `final`, `override` OUT). See `clarifications.md` Q2.
- [Clarification iter1] NFR-3: Added a unit-test requirement that the Python keyword snapshot equals `frozenset(keyword.kwlist) | frozenset(keyword.softkwlist)` when the running interpreter is Python 3.12.x, with skip-on-other-versions semantics. See `clarifications.md` Q7.
- [Clarification iter1] NFR-5: Added a documentation requirement that `keywords.py` records the SV/C++ standard revisions consumed and the exact CPython 3.12 patch version of the Python snapshot. See `clarifications.md` Q7.
```

**Rationale.** Standard changelog convention for the steel workflow.

---

## Sections NOT modified

The following sections were left untouched:

- Overview
- User Stories (US-1 through US-4)
- FR-1 (identifier scope), FR-3 (validation rule), FR-4 (comparison semantics), FR-5 (entry point), FR-6 (error type), FR-7 (reporting strategy), FR-8 (active languages), FR-9 (interaction with existing checks)
- NFR-1 (performance), NFR-2 (determinism), NFR-4 (no external deps)
- Acceptance Criteria (AC-1 through AC-11, including AC-4b)
- Out of Scope
