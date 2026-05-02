# Retrospect — 012-reserved-keyword-validation

## Workflow Summary

| Stage           | Iterations | Verdict trail                | Forge | Gauge                          |
|-----------------|------------|------------------------------|-------|--------------------------------|
| Specification   | 3          | REVISE → REVISE → APPROVE    | claude| gemini                         |
| Clarification   | 1          | APPROVE                      | claude| gemini                         |
| Planning        | 1          | APPROVE                      | claude| gemini                         |
| Task breakdown  | 2          | REVISE → APPROVE             | claude| gemini                         |
| Implementation  | 4 commits  | T-001 iter 1 REVISE → iter 2 APPROVE; T-002, T-003, T-004..T-008, T-009..T-018, T-019 all APPROVE on first pass | claude | gemini (T-019 self-reviewed by claude) |
| Validation      | 1          | APPROVE (23 PASS / 0 FAIL / 1 DEFERRED) | claude | gemini |
| Retrospect      | (current)  | —                            | claude| gemini                         |

**Total Forge-Gauge cycles:** 8 across spec/clarification/planning/task-breakdown + 1 per Commit-A/B/C (each Commit batched 3-10 task-level reviews into one Gauge call, with T-001 needing one delta cycle inside Commit A) + 1 self-review for T-019 + 1 for validation = 10 distinct Gauge invocations. All loops converged within the configured `maxIterations: 5`.

**Skills invoked:** `[]` at every stage. The feature is purely Python validation logic against frozen IR; no SystemVerilog code, no RTL, no testbench, no Verilator build files, and no cocotb. None of the registered project skills (`systemverilog-core`, `sv-gen`, `cocotb-verilator-tests`, `verilator-cmake`, etc.) had triggers that matched. The work falls into the project's gap between "DSL/IR/validate Python" and "the SV/C++/Python codegen backends." No skill exists for that gap, and arguably none is needed — the constitution and existing `validate/engine.py` patterns were sufficient guidance.

## Memories to Save

### M-1. Project — Test fixture `.git/HEAD` marker is on-disk-only, not tracked

- **Type:** project
- **Name:** `project_fixture_git_marker_convention`
- **Content:** Each fixture under `tests/fixtures/<case>/project/` requires a `.git/HEAD` file containing `ref: refs/heads/main` so that `piketype.cli` can resolve the repo root via `find_repo_root` (`src/piketype/repo.py:10`). The marker is **not committed to the project's git history** because git ignores nested `.git/` directories. New fixtures must create the marker manually; copy-tree-based tests rely on the on-disk marker existing locally. CI must materialize these markers before running tests (mechanism unknown — possibly absent; flagged for follow-up).
- **Evidence:** `tests/test_gen_const_sv.py:373-374` shows the only programmatic creation pattern (`(repo_dir / ".git").mkdir(); (repo_dir / ".git" / "HEAD").write_text("ref: refs/heads/main\n")`); `git ls-files tests/fixtures/struct_sv_basic/` returns only the `alpha/piketype/types.py`, not any `.git/*`. My iter-1 fixture for `keyword_near_miss` failed with "could not find repo root" until I added the marker — discovered during T-006 implementation.
- **Rationale:** Non-obvious from the constitution and codebase conventions. Future work creating new fixtures will hit the same wall without this knowledge. The fix is mechanical (one `.git/HEAD` write) but undiscoverable without tracing through `find_repo_root`.

### M-2. Project — Use `.venv/bin/python` for tests, not system Python

- **Type:** project
- **Name:** `project_use_venv_for_tests`
- **Content:** This project uses a uv-managed `.venv/` (Python 3.13.11) at the repo root with Jinja2 installed. System Python (3.14.4 on this host) lacks `jinja2`, so running `python -m unittest` directly fails with `ModuleNotFoundError: No module named 'jinja2'`. Always use `.venv/bin/python -m unittest discover tests` for the test suite. `PYTHONPATH=src` is set automatically by `pyproject.toml:[tool.pytest.ini_options].pythonpath`, but `unittest` doesn't read that config — explicit `PYTHONPATH=src` (or `.venv/bin/python` which has the project pip-installed) is required for the latter.
- **Evidence:** `.venv/pyvenv.cfg` documents `home = ... uv/python/cpython-3.13.11`; `pyproject.toml:[tool.pytest.ini_options]` shows `pythonpath = ["src"]`; my T-002 verification ran `python3 -m unittest tests.test_keyword_set_snapshot` and got `ModuleNotFoundError`, then `.venv/bin/python -m unittest discover tests` returned 294 tests OK.
- **Rationale:** New conversations would otherwise re-discover this every session. The .venv presence is detectable with `ls .venv` but the right invocation pattern (and the gotcha about `pyproject.toml` pytest config not affecting `unittest`) is non-obvious.

### M-3. Feedback — Project pyright baseline is non-zero; target "no new errors"

- **Type:** feedback
- **Name:** `feedback_pyright_baseline_not_zero`
- **Content:** The constitution states "basedpyright strict mode must pass with zero errors" but the actual baseline is **100 errors** project-wide (verified by stashing all feature changes and re-running `basedpyright src/`). The constitution is aspirational on this point. Practice: target "no NEW errors over baseline" for new code, not absolute zero. Inspect baseline before claiming a regression. Do not assume the constitution's literal claim. **Why:** The numeric mismatch will silently mislead someone trying to enforce constitution literally — they'll either (a) waste time fixing pre-existing errors that aren't part of their feature, or (b) be flagged for "violating the constitution" when they only added zero new errors. **How to apply:** When adding Python code to `src/piketype/`, run `basedpyright src/` once before and once after the change; report the delta, not the absolute count.
- **Evidence:** `git stash; basedpyright src/; git stash pop` during T-004 development showed 100 errors with no changes; after my changes (T-004 + T-005), still 100 errors. The constitution at `.steel/constitution.md:33` says "basedpyright strict mode must pass with zero errors."
- **Rationale:** Non-obvious tension between documented standard and reality. Surfaces only on careful inspection.

### M-4. Project — Constants named after Python hard keywords need `__dict__` install

- **Type:** project
- **Name:** `project_dsl_const_python_keyword_workaround`
- **Content:** The DSL captures constant names from module-level Python bindings via `module.__dict__.items()` at `src/piketype/dsl/freeze.py:79`. To create a constant whose name is a **Python hard keyword** (e.g., `for`, `class`, `if`), the normal binding form `for = Const(3)` is a Python syntax error. Workaround: install via `__dict__`:
  ```python
  import sys
  sys.modules[__name__].__dict__["for"] = Const(3)
  ```
  This is needed for any test fixture exercising DSL identifiers that happen to be Python keywords. The freeze step accepts any binding name in `module.__dict__`, including Python keywords. **Why:** validation-test work that ever needs to construct an identifier that's also a Python keyword will hit Python's grammar wall and need this workaround. **How to apply:** When writing a fixture for a DSL identifier matching `keyword.kwlist`, wrap the binding in `sys.modules[__name__].__dict__[name] = ...` and add a comment explaining why.
- **Evidence:** `tests/fixtures/keyword_constant_for/project/alpha/piketype/types.py` (added in T-011); `src/piketype/dsl/freeze.py:79` shows `for name, value in loaded.module.__dict__.items()`.
- **Rationale:** Non-obvious; will recur whenever someone tests another Python-keyword identifier.

### M-5. Reference — IEEE 1800-2017/2023 keyword set source-of-truth pattern

- **Type:** reference
- **Name:** `reference_sv_keyword_sources`
- **Content:** When sourcing SystemVerilog reserved keywords (e.g., for the keyword validator at `src/piketype/validate/keywords.py`), do a **two-source cross-check**: (a) the IEEE Std 1800-2017 / 1800-2023 Annex B reserved-keyword table; (b) Verilator's lexer keyword table (`include/verilated_funcs.h` keyword section) as a trusted secondary source. The 1800-2023 standard adds **no** new reserved keywords over 1800-2017 (it is a maintenance revision). Watch out for the common misattribution: `nettype` was added in 1800-2012 (NOT 2023), and `interconnect` was added in 1800-2017 (NOT 2023). The Gemini Gauge in iter-1 of task_breakdown made this attribution error and the Forge subsequently corrected it.
- **Evidence:** `keywords.py:1-49` top comment block; `specs/012-reserved-keyword-validation/artifacts/task_breakdown/iter1-gauge.md` claims `soft` is a 1800-2023 addition (incorrect; `soft` was already in 1800-2009 for distribution constraints); the iter-2 forge correction at `tasks.md` plan-corrections section.
- **Rationale:** Future SV-keyword maintenance (e.g., bumping to 1800-2027) needs this dual-source pattern and the awareness that LLM Gauges may misattribute keyword vintages. Saves rediscovering the right approach.

### M-6. Feedback — Universal `*` on helpers, including single-arg

- **Type:** feedback
- **Name:** `feedback_keyword_only_args_universal`
- **Content:** The project's coding standard ("Keyword-only arguments (*) for helper functions to enforce clarity at call sites") is enforced **universally**, including on single-argument helpers. Existing helpers in `validate/engine.py` (e.g., `_validate_pad_suffix_reservation(*, module: ModuleIR)`) all use `*` even with one positional. The Gauge will flag any helper without it as a constitutional violation. **Why:** The convention is universal across the codebase; a 1-arg helper without `*` reads as a mistake. **How to apply:** All new helpers — even `def fn(*, x: int)` for a single arg — must use `*`. This includes module-public helpers like `keyword_languages`.
- **Evidence:** `specs/012-reserved-keyword-validation/artifacts/implementation/commit-A-gauge.md` — Gemini Gauge flagged `keyword_languages(identifier: str)` as a BLOCKING issue and required `keyword_languages(*, identifier: str)`. The fix at commit `e8e89bf` (`fix(validate): make keyword_languages keyword-only per constitution`) was a one-character insertion. Existing examples in `engine.py:172, 190, 231, 244, 268, 298, 310`.
- **Rationale:** Easy to forget on single-arg helpers; the Gauge catches it but the round-trip is wasted. Memorising this pre-emptively saves an iteration on every new validate-helper.

## Skill Updates

The project's `systemverilog-core`, `sv-gen`, etc. were not invoked because they don't apply to Python validation work. There is no skill specifically for "writing/extending Python validation passes in the `validate/` package." Three improvements would have helped this workflow:

### S-1. Add a `piketype-validate` skill (or extend an existing skill)

- **Skill:** new skill `piketype-validate` or extension of an existing skill family.
- **Issue found:** No skill triggered for "extend `validate/engine.py` with a new validation pass" — the closest registered skill (`systemverilog-core`) does not match Python validator work. The Gauge had to re-derive constitutional patterns (universal `*` on helpers, frozen-set discipline, first-fail order, `ValidationError` reuse) from `.steel/constitution.md` and `validate/engine.py` source on every iteration.
- **Proposed change:** Create a skill that triggers on "edit, extend, or refactor any file under `src/piketype/validate/`" with a checklist:
  - Helper functions use `*` keyword-only args universally (M-6).
  - Reuse `piketype.errors.ValidationError`; do not introduce new exception classes.
  - First-fail in deterministic IR-declaration order; no error collection.
  - Place new passes at the end of `validate_repo` after structural+cross-module passes.
  - Match existing message format conventions (path-prefixed, single-quoted identifiers).
  - For data-driven validation, store data in a sibling module (e.g., `validate/keywords.py`) as frozen sets/tuples; do not compute at import time.
- **Expected impact:** Would have eliminated the iter-1 REVISE in T-001 (missing `*`) and would have set the stage for the iteration-2 task-breakdown fix (commit-boundary discipline for the wire+repair atomic step). Reduces total Gauge cycles by 1-2.

### S-2. Document the `.git/HEAD` fixture-marker requirement somewhere reachable

- **Skill:** could be the new `piketype-validate` skill above, or a shared "test fixtures" doc in `docs/`.
- **Issue found:** `tests/test_gen_const_sv.py:373-374` is the only place the project documents the `.git/HEAD` marker convention — and only inline in one test method. New fixtures fail mysteriously with "could not find repo root" without it. I rediscovered this during T-006.
- **Proposed change:** Add a one-paragraph note to `docs/architecture.md` (under the test-fixture conventions section, or in a new "Adding test fixtures" subsection) that says: "Each fixture under `tests/fixtures/<case>/project/` must contain a `.git/HEAD` file with content `ref: refs/heads/main`. The file is on-disk-only (not git-tracked, since git ignores nested `.git/`); CI must materialize it before running tests, or fixtures must create it programmatically per `tests/test_gen_const_sv.py:373-374`."
- **Expected impact:** Saves ~10 minutes of debugging "could not find repo root" for every new fixture author.

### S-3. Steel-implement skill: clarify gauge batching strategy

- **Skill:** `steel-implement` (project skill at `~/.claude/skills/steel-implement/SKILL.md` or wherever Steel-Kit skills live).
- **Issue found:** The skill says "every task MUST receive a Gauge code review with a VERDICT" but doesn't clearly authorize batching. I batched commit A (T-001..T-003) and commit B (T-004..T-008) and commit C (T-009..T-018) into single Gauge calls that produced multiple `VERDICT-T<N>:` lines. The skill's example output format implied per-task gauge artifacts, but didn't say "you may batch the call as long as each task gets a per-task verdict." This left ambiguity.
- **Proposed change:** Add to the skill's "Gauge Phase" section: "Batched gauge reviews are permitted: a single Gauge LLM call may produce verdicts for multiple tasks if the prompt explicitly enumerates one VERDICT line per task (e.g., `VERDICT-T001: APPROVE`, `VERDICT-T002: APPROVE`). The single artifact file (e.g., `commit-A-gauge.md`) is the per-batch artifact; each task's verdict is parsed from within that file. Save per-task Gauge artifacts only when an iteration loop occurs on a single task (e.g., `task1-iter2-gauge.md` for T-001's REVISE→APPROVE delta cycle)."
- **Expected impact:** Clarifies workflow expectations; would have saved ~20 minutes of internal deliberation on whether to make 19 separate Gauge calls vs. 4 batched ones.

## Process Improvements

### P-1. Bottlenecks

- **Specification — 3 iterations.** Healthy convergence. Each REVISE was substantive and added information:
  - iter 1 → REVISE: Gauge correctly flagged that base-form type-name check (e.g., `class` for `class_t`) is over-restrictive (the base never appears as a standalone token). See `artifacts/specification/iter1-gauge.md`.
  - iter 2 → REVISE: Gauge correctly flagged FR-1.6 module-name check was over-restrictive in the same way (using bare `<base>` against all keyword sets vs. per-language emitted form). See `artifacts/specification/iter2-gauge.md`.
  - iter 3 → APPROVE.
  - Root cause: the spec author (claude) wrote a first-cut that over-applied the keyword check to identifiers that don't actually appear standalone in generated code. The Gauge caught both. Both REVISE cycles added real spec content.
- **Task breakdown — 2 iterations.** iter 1 → REVISE for two real BLOCKING issues:
  - T-005/T-008 sequencing leaving a broken intermediate commit (the user's "byte-parity-per-commit" preference, captured in their auto-memory, would have caught this earlier if the skill primed the planner). See `artifacts/task_breakdown/iter1-gauge.md`.
  - T-001 keyword-source accuracy (the Forge made hand-wavey claims about 1800-2023 additions that were unverifiable). See same file.
  - Both real defects; iter 2 fixed both. Healthy.
- **Implementation T-001 — 1 delta iteration.** Gauge caught the missing `*` in `keyword_languages(identifier: str)`. One-line fix. Real defect catch (M-6).
- **No bottleneck stages.** All loops converged in ≤3 iterations, well under the configured `maxIterations: 5`.

### P-2. Forge-Gauge dynamics — REVISE classification

| Stage / Task        | REVISE iter | Classification | Source                                    |
|---------------------|-------------|----------------|-------------------------------------------|
| Specification iter 1| (a) real defect — base-form check over-restriction | `artifacts/specification/iter1-gauge.md` |
| Specification iter 2| (a) real defect — module-name over-restriction | `artifacts/specification/iter2-gauge.md` |
| Task_breakdown iter 1| (a) real defect ×2 — atomic-commit and keyword accuracy | `artifacts/task_breakdown/iter1-gauge.md` |
| Implementation T-001 iter 1| (b) enforcing valid standard — universal `*` on helpers | `artifacts/implementation/commit-A-gauge.md` |

**No (c) "unnecessary churn" REVISE cycles.** Every REVISE caught either a real defect (a) or enforced a valid standard (b). The Gemini Gauge was high-signal across the workflow.

One Gauge **error** was caught and corrected by the Forge: in `artifacts/task_breakdown/iter1-gauge.md` the Gauge claimed `nettype`/`interconnect` are 1800-2012 and `soft` is a 1800-2023 addition. The Forge correctly evaluated this against constitutional principle 4 ("correctness over convenience" — only commit to claims you can verify) and reframed T-001's instructions to require standard-text verification rather than copy-pasting the Gauge's vintages. This is the prescribed Forge behavior per the workflow ("If prior Gauge feedback contradicts the constitution, IGNORE that feedback").

### P-3. Constitution gaps

- **The "basedpyright strict mode must pass with zero errors" claim is not currently enforced.** Baseline is 100 errors. Either:
  - Remediate the baseline (out of scope for this feature; needs a dedicated cleanup pass).
  - Refine the constitution to read "basedpyright strict mode must pass with zero NEW errors over baseline" or similar.
  - This was not surfaced as a Gauge issue during the workflow because every commit kept the count at baseline; but a future Gauge that reads the constitution literally would flag any non-zero count as a violation, leading to false REVISEs.
  - Evidence: `git stash; basedpyright src/; git stash pop` produced 100 errors at every measurement during commits A, B, C, D.
- **No guidance on test fixture conventions.** The constitution describes the test-runner choice and golden-file pattern but says nothing about the `.git/HEAD` marker requirement (M-1) or the `.venv` invocation requirement (M-2). Both are recurring traps for new contributors.

### P-4. Workflow gaps

- **No gap detected** in the steel-kit workflow itself. All 7 stages contributed value.
- The implementation stage's batching of Gauge calls (one per commit) was an emergent practice that worked well but is under-documented (S-3 above).

## Observations on the spec quality

- The spec converged on a thoughtful, internally-consistent set of 9 FRs, 5 NFRs, and 12 ACs. The clarification stage resolved 8 implicit/explicit questions cleanly.
- The plan's "byte-parity at every commit" decomposition into 4 commits (A/B/C/D) was well-aligned with the user's auto-memory preference and shipped cleanly.
- AC-2's spec wording ("error names `C++, Python` as the conflicting languages" for a struct field named `class`) was technically incomplete — `class` is a SystemVerilog keyword too, so the actual error names all three languages. This was a spec-level cosmetic error, caught only by the Forge during T-009 fixture work, but it did not affect the implementation since no test asserts the AC-2 negative half. Recommend updating spec.md AC-2 wording in a follow-up commit (out of scope here).
