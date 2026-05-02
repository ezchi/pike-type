# Clarifications — 012-reserved-keyword-validation

This document resolves the open questions left in `spec.md` after the specification stage and surfaces implicit assumptions that need to be explicit before planning.

Each clarification is tagged:

- **[SPEC UPDATE]** — the resolution changes a requirement in `spec.md`
- **[NO SPEC CHANGE]** — the resolution adds context only

---

## Q1. SystemVerilog standard revision (FR-2)

**Question.** Use IEEE 1800-2017 reserved keywords only, or include the additions introduced in IEEE 1800-2023 (e.g. `nettype`, `interconnect`)?

**Resolution.** Include the union: 1800-2017 base + 1800-2023 additions.

**Rationale.**

1. **Constitution principle 4 (Correctness over convenience).** The validator's job is to prevent generated code from failing downstream compilation. Verilator 5.x already accepts a substantial portion of 1800-2023 syntax, and project consumers may upgrade Verilator independently of `piketype`. Rejecting an identifier that is a 1800-2023 keyword today defends against silent breakage tomorrow when a downstream consumer upgrades their simulator.
2. **Asymmetric cost.** A false positive (rejecting `nettype` as a field name) is a one-line rename in the DSL. A false negative (accepting `nettype`, then `verilator --2023` fails to parse generated SV) is a downstream compile failure that the user must trace back across the codegen boundary — exactly what this feature is designed to prevent.
3. **Forward-compat is a project value.** The constitution does not pin a specific SV standard; the tech-stack table just says "SystemVerilog". Defaulting to the strictest reasonable union honors that openness.
4. **Cost of the decision is bounded.** The 1800-2023 additions over 1800-2017 are a small set (single-digit count of additions like `nettype`, `interconnect`). The probability that a hardware DSL author chose any of them as a field name is low; the validation cost is trivial.

**Action.**
- The SV keyword set in `src/piketype/validate/keywords.py` is the **union** of 1800-2017 reserved keywords and 1800-2023 additions.
- The module's docstring or comment cites the standard reference and lists the 2023-only additions explicitly so a reader can audit the source.
- No CLI knob to switch between revisions — Constitution principle 3 (Determinism) prefers a single, frozen authoritative set.

**[SPEC UPDATE]** — FR-2 SV bullet: drop the `[NEEDS CLARIFICATION]` and commit to the union.

---

## Q2. C++ contextual identifiers (FR-2)

**Question.** Beyond ISO C++20 reserved keywords and alternative tokens, which contextual / context-sensitive identifiers should be in the C++ set? Specifically, include `import` and `module` only, or also `final`/`override`/coroutines?

**Resolution.** Three separate decisions, not one:

1. **C++20 reserved keywords** (`co_await`, `co_yield`, `co_return` — these are actual reserved keywords in C++20, **not** contextual identifiers): **MUST be included.** The iteration-2 spec text grouped these with contextual identifiers, which was a wording error. Per [N4861] §2.13, `co_await`, `co_yield`, `co_return` are reserved.
2. **C++20 alternative tokens** (`and`, `or`, `not`, `xor`, `bitand`, `bitor`, `compl`, `and_eq`, `or_eq`, `xor_eq`, `not_eq`): **MUST be included** (already in iter-2 FR-2, unchanged).
3. **C++20 contextual identifiers** `final`, `override`: **MUST NOT be included.** These are only treated specially in narrow grammatical positions (after a class name in a base-clause, after a virtual function declarator). Used as a member name (e.g. `int final;`) they are legal identifiers in all C++ standards. Rejecting them would over-restrict per Constitution principle 4.
4. **C++20 module-related identifiers** `import`, `module`: **MUST be included.** Although these are technically contextual identifiers (only treated as keywords at the start of a translation unit or module-declaration), the practical risk profile differs from `final`/`override`:
   - The grammar interaction with `module foo;` and `import bar;` declarations means a member named `module` or `import` produces parse failures in implementations that pre-scan for module-declarations, even when used in contexts that should be plain identifiers.
   - Both `<base>::module` and `<base>::import` are realistic collision points if a DSL author picks `import.py` or `module.py` as a module filename.
   - Excluding them is a forward-compat risk as toolchains tighten the C++20 modules story.

**Rationale recap.**
- Reserved keywords (`co_await` etc.): Required, non-negotiable, language-mandated.
- Alternative tokens: Required, language-mandated.
- `import`/`module`: Asymmetric-cost argument identical to Q1 — false-positive cost is one rename; false-negative cost is a downstream parse failure post-modules-rollout.
- `final`/`override`: Plainly legal C++ identifiers in any non-declarator position. Rejecting would punish valid code; matches Constitution principle 4.

**Action.**
- The C++ keyword set in `src/piketype/validate/keywords.py` is the union of: C++20 reserved keywords (including coroutine keywords) + alternative tokens + `import` + `module`.
- `final` and `override` are explicitly excluded; the module's comment documents this exclusion with a line citing N4861 grammar context.

**[SPEC UPDATE]** — FR-2 C++ bullet: drop the `[NEEDS CLARIFICATION]`, fix the wording so coroutine keywords are correctly classified as reserved (not contextual), and pin the inclusion list.

---

## Q3 (implicit). Soft-keyword annotation in error messages (FR-3)

**Question.** FR-3 specifies that the language list is alphabetically sorted and Python-soft is annotated inline as `Python (soft)`. Two implicit edge cases:

1. What if an identifier is BOTH a Python hard keyword AND a Python soft keyword? (Empty in Python 3.12 — `keyword.kwlist` and `keyword.softkwlist` are disjoint — but the implementation should not assume this forever.)
2. How does `Python (soft)` sort relative to `Python` and `SystemVerilog` in the alphabetical list?

**Resolution.**

1. **Hard wins.** If an identifier is in both `kwlist` and `softkwlist` (impossible in 3.12, defensive for future-proofing), report it as `Python` (no `(soft)` annotation). Hard-keyword status is strictly stronger.
2. **Sort by base language name, then annotation.** The sort key is the language name without the annotation: `C++` < `Python` < `Python (soft)` < `SystemVerilog`. So `class` (C++ hard, Python hard) sorts as `C++, Python`. So `type` (Python soft, SV hard) sorts as `Python (soft), SystemVerilog`. This matches the worked examples in iter-3 FR-3.

**[NO SPEC CHANGE]** — the existing FR-3 examples already match this rule; the rule is implicit but not contradicted. Recording it here so the planner does not invent a different sort order.

---

## Q4 (implicit). Verilator default-net check vs. SV keyword set (NFR-3)

**Question.** Verilator's default `--default-net wire` and the existing project goldens generate `package` declarations. If FR-1.6 checks the per-language emitted form of the module name (`<base>_pkg`), is the empty case (`base = ""`) reachable? What about a base that becomes `_pkg` after stripping?

**Resolution.** The repo invariant (stated in the constitution under "Cross-module type references") is that module basenames are unique across the repo and follow the standard Python module-name convention (non-empty, valid Python identifier). The DSL loader rejects empty/invalid module basenames before this validator ever runs. Therefore:

- The keyword check operates on a guaranteed-non-empty `<base>` string.
- `<base>_pkg` is guaranteed to be a valid SV identifier candidate.
- The validator does not need to defensively handle `base == ""`.

**[NO SPEC CHANGE]** — this is an invariant inherited from the loader, not a new requirement.

---

## Q5 (implicit). Test fixture organization (NFR-3)

**Question.** NFR-3 mandates "at least one negative-test fixture per identifier kind." The existing test convention is `tests/fixtures/<case>/project/` + `tests/goldens/gen/<case>/`. For negative tests, what does the "golden" look like?

**Resolution.** Existing negative-test convention in this repo:

- For each negative-test case, create a fixture under `tests/fixtures/<case>/project/`.
- Capture the expected error message in a per-case golden file (the convention used elsewhere in the codebase — confirm exact path during planning, but the pattern is `tests/goldens/gen/<case>/expected_error.txt` or similar).
- The integration test runs `piketype gen`, asserts non-zero exit, and matches stderr (or the captured error text) against the golden byte-for-byte.

This honors Constitution testing rule 3 ("Negative tests verify that invalid inputs produce specific error messages and non-zero exit codes") and rule 4 ("Tests use unittest.TestCase").

**[NO SPEC CHANGE]** — captured for the planner to follow existing patterns. Specific file layout decisions belong in the plan, not the spec.

---

## Q6 (implicit). Validation order between FR-1.5 (constants) and FR-9

**Question.** FR-9 says the keyword check does not duplicate `_validate_generated_identifier_collision`, which checks user constants/enum-values against derived `LP_<BASE>_*` identifiers. Both checks operate on constant names. What is the order between them?

**Resolution.** Run them in the existing `validate_repo` declaration order in `engine.py`:

1. Per-module structural validations (current order).
2. `_validate_generated_identifier_collision` (existing, FR-14 of prior spec).
3. New `_validate_reserved_keywords` (this spec).

A constant name that is both a derived-identifier collision AND a reserved keyword will fire on the derived-identifier check first, matching FR-7 (first-fail). This is acceptable because the user must rename either way; the first error message is sufficient.

**[NO SPEC CHANGE]** — refines FR-7's first-fail order without altering the spec.

---

## Q7 (implicit). Snapshot freshness for Python keyword set (FR-2, NFR-4)

**Question.** FR-2 says the Python keyword set is "a static snapshot of `keyword.kwlist ∪ keyword.softkwlist` taken from CPython 3.12.x at spec-freeze time." Which exact 3.12 patch version? How is the snapshot maintained when CPython adds a soft keyword in 3.13/3.14?

**Resolution.**

- The snapshot is taken from the **latest CPython 3.12.x** patch version at the time of implementation merge. The implementation PR records the exact version (e.g. `3.12.7`) in a module-level comment.
- Future CPython releases (3.13+) that add new soft keywords are out of scope for this iteration. The constitution's tech-stack table requires Python 3.12; updates to a newer minimum Python version are governed separately and would naturally include refreshing this snapshot.
- An explicit unit test in `tests/` verifies that the snapshot frozen-set equals `frozenset(keyword.kwlist) | frozenset(keyword.softkwlist)` *under the running interpreter when the running interpreter is 3.12.x*. This catches drift if a maintainer accidentally edits the snapshot. Under 3.13+, the test should skip with an explanatory message rather than fail, since drift is then expected and a separate PR.

**[SPEC UPDATE]** — NFR-3 (test coverage): add a unit test for the Python snapshot vs. `keyword` module under Python 3.12. Add a documentation requirement under NFR-5 to record the exact Python patch version in the keyword module.

---

## Q8 (implicit). Error wording stability across iterations

**Question.** FR-3 pins a normative error message shape. ACs reference exact strings as goldens. If the wording changes (e.g. "Rename it." → "Rename this identifier."), every negative-test golden must be regenerated. Do we want this brittleness, or should the error message format be referenced by tag rather than literal string?

**Resolution.** Keep the exact-string approach. Rationale:

- Constitution principle 3 (Determinism) is enforced byte-for-byte. Error messages are part of the deterministic output surface.
- Tag-based assertions hide formatting bugs; literal-string goldens catch them.
- The cost of a wording change is a one-time golden-regeneration commit; the benefit is a strong regression net.

This is consistent with the existing negative-test approach in the repo.

**[NO SPEC CHANGE]** — captures the maintenance posture for future PRs.

---

## Summary of [SPEC UPDATE] items

The following spec.md sections require edits:

1. **FR-2 SV bullet** — remove `[NEEDS CLARIFICATION]`, commit to 1800-2017 + 1800-2023 union.
2. **FR-2 C++ bullet** — remove `[NEEDS CLARIFICATION]`, fix coroutine-keyword classification (they are reserved, not contextual), pin the inclusion list, document `final`/`override` exclusion.
3. **NFR-3** — add a unit test for the Python keyword snapshot vs. `keyword` module under Python 3.12.
4. **NFR-5** — add a documentation requirement to record the exact Python 3.12 patch version inside `keywords.py`.
5. **Open Questions section** — empty out (both Q1 and Q2 resolved).
6. **Changelog** — append entries for each FR/NFR change with iteration tag.
