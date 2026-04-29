Reading additional input from stdin...
OpenAI Codex v0.125.0 (research preview)
--------
workdir: /Users/ezchi/Projects/pike-type
model: gpt-5.5
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, /Users/ezchi/.codex/memories]
reasoning effort: xhigh
reasoning summaries: none
session id: 019dd8eb-7528-7fb0-9cc1-e5d360247a14
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge-prompt.md
codex
I’ll read the referenced prompt first, then I’ll execute whatever workflow it defines against the current repo state.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Clarification Iteration 2

This is **iteration 2** of the clarification stage. Iteration 1 returned `VERDICT: REVISE` with:

1. BLOCKING — CL-2 permitted backend-local filter registration; FR-16 requires single-file audit from `common/render.py`.
2. WARNING — FR-25's `feature-final` perf row was not scheduled by any FR.

Both issues were stated to be surgical edits.

## Inputs to Review

1. Specification: `specs/010-jinja-template-migration/spec.md`.
2. Iteration-1 review: `specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md`.

## Review Instructions

1. Confirm CL-2 now requires filters be defined and registered only in `backends/common/render.py`. Verify there is no remaining contradiction with FR-16.
2. Confirm FR-25 now explicitly schedules each row's measurement.
3. Look for any new contradiction or regression introduced by the surgical edits. Bias toward APPROVE when the only outstanding work is properly scheduled implementation work.

End with `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after.

codex
This is a Steel-Kit clarification review, so I’m using `steel-clarify` for the workflow conventions and then checking only the files named by the prompt.
exec
/bin/zsh -lc "sed -n '1,220p' .agents/skills/steel-clarify/SKILL.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
---
name: steel-clarify
description: "Steel-Kit workflow skill: Run clarification on the current specification using the Forge-Gauge loop."
---

# steel-clarify

Use this skill when the user invokes `/steel-clarify` or asks to run the corresponding Steel-Kit workflow step.

Run clarification on the current specification using the Forge-Gauge loop.

## Prerequisites
- `.steel/constitution.md` must contain a real project constitution, not the placeholder template
- `.steel/state.json` currentStage must be `clarification`

## Steps

0. Run `/clear` to clear the conversation context before starting this stage.

1. Read `.steel/state.json` and `.steel/config.json`. Verify stage is `clarification`.

2. Read the spec from `specs/<specId>/spec.md` and `.steel/constitution.md`.

3. **FORGE-GAUGE LOOP** (max iterations from config):

   ### Forge Phase (you are the Forge)
   a. Review the specification and:
      - Identify all [NEEDS CLARIFICATION] markers
      - Resolve each ambiguity with a recommended resolution and rationale
      - Identify implicit assumptions that should be explicit
      - Check for contradictions between requirements

      **The Project Constitution is the highest authority.** If prior Gauge feedback contradicts the constitution, IGNORE that feedback. Do not blindly accept all suggestions.

   b. Write clarifications to `specs/<specId>/clarifications.md`. For each clarification, mark whether it requires a spec change:
      - **[SPEC UPDATE]** — the clarification changes, adds, or removes a requirement in spec.md
      - **[NO SPEC CHANGE]** — the clarification only adds context without changing the spec

   c. If any clarifications are marked **[SPEC UPDATE]**, update `specs/<specId>/spec.md`:
      - Apply each spec-affecting clarification directly to the relevant section (FR-*, NFR, acceptance criteria, user stories, etc.)
      - Remove resolved `[NEEDS CLARIFICATION]` markers
      - Add a `## Changelog` section at the bottom of spec.md (or append to it if it exists) with entries:
        ```
        - [Clarification iterN] FR-X: <what changed and why>
        ```
      - Do NOT rewrite unchanged sections — only edit what the clarifications require

   d. Save a copy of clarifications to `specs/<specId>/artifacts/clarification/iterN-forge.md`
   e. If spec.md was modified, save a copy to `specs/<specId>/artifacts/clarification/iterN-spec-diff.md` containing only the diff (before → after for each changed section)
   f. Git commit: `forge(clarification): iteration N output [iteration N]`

   ### Gauge Phase
   g. Call the Gauge LLM (per config) to review. **IMPORTANT: Run the command from the project's working directory, NOT /tmp.**
      - Write the full review prompt to a file at `specs/<specId>/artifacts/clarification/iterN-gauge-prompt.md`
      - If gauge is `gemini`: run `gemini "Read and follow the instructions in <absolute-path-to-prompt-file>"` in the current project directory
      - If gauge is `codex`: run `codex exec "Read and follow the instructions in <absolute-path-to-prompt-file>"` in the current project directory
      - If gauge is `claude`: Review critically yourself as the Gauge role.

      The Gauge must review BOTH the clarifications AND the updated spec.md:
      1. **Clarifications**: Are they complete, logical, and aligned with the constitution? Do they resolve all ambiguities?
      2. **Spec updates**: For each [SPEC UPDATE] clarification, verify the change was correctly applied to spec.md. Check that:
         - The updated requirement is consistent with the rest of the spec
         - No unrelated sections were modified
         - The changelog entry accurately describes the change
         - No requirements were silently dropped or weakened
      3. **Missed updates**: Are there clarifications marked [NO SPEC CHANGE] that should actually update the spec?

      End with `VERDICT: APPROVE` or `VERDICT: REVISE`.

   h. Save review to `specs/<specId>/artifacts/clarification/iterN-gauge.md`
   i. Git commit: `gauge(clarification): iteration N review — <verdict> [iteration N]`

   j. If **APPROVE**: break loop. If **REVISE**: critically evaluate feedback against constitution, incorporate valid points, and loop.

4. **HUMAN APPROVAL GATE** — do not skip this.

   Ask the user: **"Approve clarifications and advance to planning?"**

   - If **approved**: update state to `planning` stage, tag `steel/<specId>/clarification-complete`, and go to step 5.
   - If **rejected**: enter **Delta Clarification Mode** (step 4a).

   ### 4a. Delta Clarification Mode

   This mode processes ONLY the user's new feedback without re-running the full Forge-Gauge loop on already-approved content.

   1. **Collect feedback**: Ask the user what specific changes they want. Record their response verbatim as `userFeedback`.

   2. **DELTA FORGE-GAUGE LOOP** (max iterations from config):

      #### Delta Forge Phase
      a. Read the current `specs/<specId>/clarifications.md` and `specs/<specId>/spec.md`. These are the approved baseline — do NOT regenerate them from scratch.
      b. Address ONLY the items in `userFeedback`. For each feedback item:
         - Identify the specific section(s) of clarifications.md and/or spec.md affected
         - Make targeted edits to those sections only
         - Do NOT rewrite, reorder, or "improve" sections the user did not mention
         - If a feedback item requires a spec change, follow the same [SPEC UPDATE] / changelog rules from the main loop
      c. Save delta to `specs/<specId>/artifacts/clarification/iterN-delta-forge.md` with this structure:
         ```markdown
         # Delta Revision — Iteration N

         ## User Feedback
         (verbatim user feedback)

         ## Changes Made
         (for each change: which file/section, what changed, why)

         ## Sections NOT Modified
         (list sections that were already approved and left untouched)
         ```
      d. Git commit: `forge(clarification): delta iteration N [delta N]`

      #### Delta Gauge Phase
      e. The Gauge reviews ONLY the delta — not the entire clarifications from scratch. Provide the Gauge with:
         - The user's feedback (what was requested)
         - The diff of changes made (before → after for each modified section)
         - The full updated clarifications.md and spec.md (for context, but the review focuses on the delta)

         The Gauge MUST check:
         1. Does each change correctly address the corresponding user feedback item?
         2. Were any unrelated sections modified? (If so: REVISE)
         3. Are the changes consistent with the rest of the spec and the constitution?
         4. If spec.md was modified, was the changelog updated correctly?
         5. Is any user feedback item left unaddressed?

         End with `VERDICT: APPROVE` or `VERDICT: REVISE`.

      f. Save review to `specs/<specId>/artifacts/clarification/iterN-delta-gauge.md`
      g. Git commit: `gauge(clarification): delta iteration N review — <verdict> [delta N]`
      h. If **REVISE**: Forge fixes only the disputed items, loop back to Delta Forge Phase.
      i. If **APPROVE**: exit delta loop.

   3. Return to the approval gate (step 4) — ask the user again: **"Approve clarifications and advance to planning?"**
      The user may approve, or reject again with new feedback (re-entering Delta Clarification Mode).

5. **Track skills used**: Update `.steel/state.json` field `skillsUsed.clarification` with an array of skill names you invoked during this stage. If no skills were used, set it to `[]`.

6. Tell the user: "Run `/steel-plan` to generate the implementation plan."


codex
I’m narrowing the review to CL-2, FR-16, FR-25, and the previous Gauge findings because the iteration-2 prompt asks for a surgical approval check.
exec
/bin/zsh -lc "sed -n '1,220p' specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
Reading additional input from stdin...
OpenAI Codex v0.125.0 (research preview)
--------
workdir: /Users/ezchi/Projects/pike-type
model: gpt-5.5
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, /Users/ezchi/.codex/memories]
reasoning effort: xhigh
reasoning summaries: none
session id: 019dd8e9-b6f7-73a2-8954-0962f431a871
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md
codex
I’ll read the clarification prompt first, then execute exactly what it asks.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Clarification Iteration 1

You are the **Gauge** in a dual-agent Forge-Gauge loop. The specification stage already produced an APPROVED spec. This is the clarification stage: open questions Q-1..Q-4 have been resolved as CL-1..CL-4, and three new requirements (FR-23, FR-24, FR-25) were added to make those resolutions enforceable.

## Inputs to Review

1. **Specification (current):** `specs/010-jinja-template-migration/spec.md` — contains the new "Resolved Clarifications" section, the "Clarification-driven additions" (FR-23..FR-25), and an empty "Open Questions" section.
2. **Clarification forge output:** `specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md`.
3. **Project Constitution:** `.steel/constitution.md`.

## Review Instructions

This is a **delta** review focused on:

1. **Were Q-1..Q-4 fully resolved?** Check that each question is replaced by a concrete decision (CL-1..CL-4) with no remaining ambiguity, weasel words, or hidden alternatives.

2. **Are CL-1..CL-4 internally consistent with the rest of the spec?**
   - CL-1 vs. NFR-6 (revertability) and AC-F8 (commit ordering).
   - CL-2 vs. FR-10/FR-11 (no semantics in templates) and FR-21 (lint patterns).
   - CL-3 vs. FR-2/FR-3 (loader strategy) and AC-F5 (wheel install).
   - CL-4 vs. NFR-1 (perf measurement) and AC-F4 (perf gate).

3. **Are FR-23, FR-24, FR-25 testable and concrete?**
   - FR-23: is the CLI signature unambiguous? Will a developer build it without further questions?
   - FR-24: does the per-filter checklist match what FR-21 / CL-2 require?
   - FR-25: does the table schema let AC-F4 actually be checked numerically?

4. **Are there any new contradictions introduced by FR-23..FR-25?** In particular:
   - Does FR-23's `--output -` to stdout conflict with the requirement that `perf.md` be the authoritative store (CL-4)? (Answer expected: no, because the implementation captures stdout into `perf.md`.) Confirm.
   - Does FR-25's "feature-final" row require an additional measurement run beyond per-backend rows? Is that run defined elsewhere? If not, flag.

5. **Constitution alignment.** Specifically check Principles 3 (determinism) and 5 (template-first); do any of CL-1..CL-4 or FR-23..FR-25 weaken either principle?

Apply severity tags `BLOCKING`, `WARNING`, `NOTE`. End with exactly `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after the verdict line.

Approve if every Q is resolved as a concrete decision and no new contradiction has been introduced. Bias toward APPROVE when in doubt — the clarification stage's purpose is exactly to lock answers in, not to perpetuate debate.

codex
The prompt asks for a delta review of the clarified spec against the forge output and constitution. I’m going to read those three inputs now and check the named CL/FR/AC/NFR cross-references directly.
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Clarification — Iteration 1 Forge Output

## Inputs

- Specification: `specs/010-jinja-template-migration/spec.md` (post-specification, 4 open questions Q-1..Q-4).
- User decision (from `/steel-run-all` invocation with no overrides supplied): "accept all recommendations" for the four open questions.

## Resolutions Applied to spec.md

| Was  | Now   | Decision |
|------|-------|----------|
| Q-1  | CL-1  | Multiple contiguous commits per backend; squash-on-merge optional. |
| Q-2  | CL-2  | Custom Jinja filters added on demand; documented per filter; tested per filter; no IR traversal / non-determinism. |
| Q-3  | CL-3  | No `PackageLoader` escape hatch; `pip install -e .` semantics accepted. |
| Q-4  | CL-4  | Baseline captured before first migration commit; stored in `perf.md`; authoritative. |

## New requirements introduced by clarification

- **FR-23.** Concrete CLI signature for `tools/perf_bench.py` (line-based output for table-row append).
- **FR-24.** `docs/templates.md` "Custom Filters" section with per-filter checklist.
- **FR-25.** `perf.md` table schema with named stages (baseline, py-complete, cpp-complete, sv-complete, feature-final) — AC-F4 now references concrete row names rather than abstract `current_ms`.

## Sections preserved unchanged

- Overview, User Stories, Definitions, FR-1..FR-22, NFR-1..NFR-7, all per-backend AC-1..7 sets, AC-F1..F8, OOS-1..OOS-7. Iteration 4 of the specification stage is preserved verbatim except for the Open Questions block (replaced with Resolved Clarifications + Clarification-driven additions) and the addition of FR-23..FR-25.

## Why these decisions hold together

- CL-1 (multi-commit) + NFR-6 (revertability) compose: a contiguous range revert affects only one backend.
- CL-2 (filter discipline) + FR-10 (no template semantics) + FR-21 (lint script) compose: filters are constrained pure helpers; semantic logic still has nowhere to hide in a filter because filters cannot perform IR traversal and the lint catches forbidden patterns inside Jinja blocks regardless of how those patterns are produced.
- CL-3 (no escape hatch) + FR-2/FR-3 (single loader strategy) compose: one loader, one code path, one set of failure modes.
- CL-4 (baseline before first migration) + FR-25 (table schema) + AC-F4 compose: the perf gate is a concrete numeric assertion against named rows, not a recomputation.

 succeeded in 0ms:
# Specification — Jinja Template Migration for Code Emitters

**Spec ID:** 010-jinja-template-migration
**Branch:** feature/010-jinja-template-migration
**Stage:** specification

---

## Overview

The Python, C++, and SystemVerilog backend emitters in `src/piketype/backends/{py,cpp,sv}/emitter.py` are currently single-file inline string-builders. Each file is 700–1100 lines (py: 792, cpp: 1067, sv: 949) and intermixes IR interpretation, formatting decisions, indentation, target-language syntax, helper-method bodies, and special cases. Auditing or extending any backend requires reading long Python functions whose output shape is implicit.

This feature migrates code generation to a Jinja2-based architecture in which:

- **Python prepares typed view models** from frozen IR. View models contain only computed primitive values (names, widths, byte counts, masks, signed/unsigned flags, helper-fragment strings, import lists) and nested frozen view-model dataclasses. Semantic decisions stay in Python.
- **Jinja2 templates render structure and syntax.** Templates contain whitespace/indentation, target-language keywords, and the iteration/conditional skeleton needed to lay out a file. Templates do not compute padding, resolve type references, decide signedness, or duplicate validation.

The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.

The migration is positive-value only when semantics stay out of templates. If templates accumulate Python logic, the migration loses its benefit and the spec's success criteria are not met.

---

## User Stories

- **US-1.** As a maintainer adding a new generated language construct, I want to edit a focused Jinja template alongside a small view-model addition, so that I can change output structure without re-reading 800-line emitter files.
- **US-2.** As a reviewer auditing generated output, I want the file shape (imports, class skeletons, helper bodies, footer) to be visible as a contiguous template, so that I can read the output structure top-to-bottom without reconstructing it from scattered string concatenations.
- **US-3.** As a contributor running the test suite, I want all existing golden-file tests to continue to pass byte-for-byte after the migration, so that I can trust the migration introduced no behavioral regressions.
- **US-4.** As a release engineer, I want determinism guarantees preserved (no timestamps, no ordering changes, idempotent generation), so that generated artifacts remain reproducible and `piketype gen` run twice produces identical output.
- **US-5.** As a future feature author working on a new backend or backend variant, I want a documented view-model + template pattern to follow, so that new backends start out template-first instead of being reverse-engineered later.
- **US-6.** As a maintainer reviewing template-bound code, I want a clear and enforced rule about what may live in templates versus Python, so that templates do not silently accumulate semantic logic over time.

---

## Definitions

- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
- **Template.** A file under `backends/<lang>/templates/` ending in `.j2`, rendered through a Jinja2 `Environment` configured per FR-2.
- **Skeleton.** The structural surround of a generated artifact: file header, imports/includes, top-level type declarations, helper-method declaration boundaries, footer.
- **Fragment.** A short, self-contained string that is not a skeleton: an expression, a single hex literal, a single-line comment string, a comma-separated argument list, a Python initializer expression. Fragments are pre-computed in Python and passed into the view model as `str` fields.
- **Inline string-building (legacy).** The current pre-migration approach: Python lists of strings concatenated to form a generated file. Treated as the migration's regression target, not a permitted alternative once a backend's migration is complete.

---

## Functional Requirements

### Architecture

- **FR-1.** A new module layer SHALL exist for view models. Each backend (`py`, `cpp`, `sv`) SHALL expose typed, frozen view-model dataclasses. Naming convention: `backends/<lang>/view.py` containing `@dataclass(frozen=True, slots=True)` classes.
- **FR-2.** Each backend SHALL expose one Jinja2 `Environment` constructed via `jinja2.PackageLoader("piketype.backends.<lang>", "templates")`. Environment options SHALL be exactly: `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True`, `undefined=jinja2.StrictUndefined`, `autoescape=False`. The environment SHALL be constructed once per `emit_<lang>` call (not module-global) so that emitter state is local and testable. `FileSystemLoader` SHALL NOT be used for production rendering. (Tests MAY construct ad-hoc environments with `DictLoader` or `FileSystemLoader` for unit testing of templates.)
- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
  - `def render(*, env: jinja2.Environment, template_name: str, context: object) -> str` that renders a template and returns a string whose final character is `"\n"` (consistent with current emitter contracts). The `context` SHALL be a view-model dataclass instance; the helper SHALL pass its fields as the template context (via `dataclasses.asdict` or by passing the instance directly with templates accessing `.field` attributes — implementation choice, but uniform across backends).
- **FR-4.** Each backend SHALL keep its existing public emit entry point (`emit_py`, `emit_cpp`, `emit_sv`) with unchanged signatures and unchanged write locations; only the internal rendering pipeline changes. The IR → view-model → template → string flow SHALL be the only public migration surface.

### Migration Order and Scope

- **FR-5.** Migration SHALL proceed in this order: (1) Python backend, (2) C++ backend, (3) SystemVerilog backend. Each backend migration SHALL be a separable, independently reviewable change. A backend's migration is **complete** when its per-backend acceptance criteria (AC-P*, AC-C*, AC-S* below) are all met. Subsequent backends SHALL NOT begin until the prior backend's migration is complete.
- **FR-6.** Within each backend, migration SHALL proceed in the following sub-order:
  1. Module/file-level skeleton (header comment, top-level imports/includes, footer).
  2. Top-level type declaration skeletons (class/struct/enum scaffolding).
  3. Repeated helper-method skeletons (e.g., `to_bytes`, `from_bytes`, `_to_packed_int`, `_from_packed_int`, equality, repr, clone, pack/unpack helpers).
  4. Expression and field-level fragments — only those with meaningful structure.

  **Examples of "meaningful template structure" (MUST move to templates):** the body of a `to_bytes` method, the body of `from_bytes` with conditional sign-handling, the dataclass field block of a Python struct, an enum's member-list block, a SystemVerilog `typedef struct packed { ... }` block, a C++ class scaffold including its packed helpers.

  **Examples of "trivial fragments" (MAY remain inline in Python and be passed as `str` fields):** a single hex literal (`"0xff"`), a numeric expression rendered for a constant (`"(1 << 32) - 1"`), a single-line type alias initializer, a header comment line, an `__all__` tuple body. These fragments SHALL be pre-computed in Python and exposed as `str` fields on the view model; templates SHALL emit them with `{{ fragment }}` and SHALL NOT recompute them.

- **FR-7.** Generated output SHALL be byte-for-byte identical to current output for every committed golden in `tests/goldens/gen/` at the end of each backend's migration. A migration step that changes any golden byte SHALL be rejected and reworked, except per FR-20.

### View-Model Boundaries

- **FR-8.** View-model fields SHALL be exactly one of:
  - A primitive (`int`, `str`, `bool`, `bytes`).
  - A `tuple[T, ...]` where `T` is itself a view-model field type.
  - Another view-model dataclass instance (nesting permitted).

  Nesting is permitted but limited: a view model SHALL NOT contain itself transitively (no recursive view models). View-model construction SHALL produce values whose iteration order is stable: any field whose type is `tuple` SHALL preserve the input's declaration order or sort the input deterministically before construction.

- **FR-9.** View models SHALL NOT contain:
  - References to IR nodes (no `StructIR`, `EnumIR`, etc. fields). View models are a clean break from IR.
  - References to mutable DSL objects.
  - `set`, `frozenset`, or `dict`. For collections whose iteration order affects output, use sorted `tuple`. (Iteration order of `set` and `frozenset` is hash-dependent; iteration order of `dict` is insertion-dependent and risks subtle nondeterminism — both are forbidden.)
  - Callables, lambdas, generators, or user-defined methods that perform IR traversal at render time.
  - Validation logic or assertions about input correctness beyond what `__post_init__` cheaply enforces (e.g., asserting a width is positive).

- **FR-10.** Templates SHALL NOT:
  - Compute padding, alignment, byte counts, masks, sign-extension boundaries, or any width-derived numeric value (these arrive as primitive view-model fields).
  - Resolve type references, look up types by name, or perform any cross-IR-node navigation.
  - Decide signed vs. unsigned behavior. The view model SHALL provide signedness as a `bool` plus pre-computed numeric fragments.
  - Duplicate validation logic from `validate/engine.py`.
  - Contain Python expression blocks (`{% python %}`-style extensions or any registered global that executes arbitrary Python).
- **FR-11.** Templates MAY use:
  - Jinja standard control flow: `if`, `for`, `set`, `include`, `import`, `extends`, `block`, `macro`.
  - Jinja built-in string filters (`upper`, `lower`, `replace`, `join`, `indent`, `trim`).
  - Project-defined custom filters registered on the environment, provided each filter is a pure function over primitives, deterministic, and documented in `docs/templates.md`.

  Template indirection (macro calls, `{% include %}`, `{% extends %}`) SHALL be at most **two levels deep** measured from the top-level template entry point. (One top-level template MAY include or extend one layer of macros/partials; that layer MAY NOT itself include further partials. Inheritance via `{% extends %}` counts as one level; a `{% block %}` override does not.) This bound preserves NFR-5's "find a construct in one place" guarantee while allowing macro reuse.

### Templates

- **FR-12.** Templates SHALL live under `backends/<lang>/templates/`. Subdirectories are permitted. Required convention: each backend SHALL have exactly one **primary template** per generated artifact kind (e.g., `module.j2` for a generated `.py`/`.cpp`/`.sv` source file). Macros and partials live in files prefixed `_` (e.g., `_macros.j2`, `_struct.j2`). Reviewers locate generated output by reading the primary template; partials are an implementation detail.
- **FR-13.** Template file extensions SHALL be `.j2`. Templates SHALL NOT carry the machine-readable header themselves; the header is produced by `backends/common/headers.py` and passed in as a view-model `header: str` field, then emitted by the template with `{{ header }}`.
- **FR-14.** Templates SHALL be packaged with the wheel using `setuptools` `package-data`. `pyproject.toml` SHALL include in `[tool.setuptools.package-data]` (or equivalent) the recursive glob `"piketype.backends.py" = ["templates/**/*.j2"]` and analogous entries for `cpp` and `sv`. `MANIFEST.in` SHALL be updated if needed. Loading at runtime is via `PackageLoader` (FR-2), which discovers templates by package import, independent of the filesystem layout outside the wheel.

### Determinism

- **FR-15.** Generated output SHALL remain deterministic: identical input fixture → identical output bytes across runs, machines, and Python versions ≥ 3.12. View models SHALL NOT use `set` or `frozenset` for fields whose iteration affects output; sorted `tuple` SHALL be used instead. Any iteration that affects output SHALL be over a sorted or declaration-order-stable sequence.
- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.

### Tooling, Lint, and Hygiene

- **FR-17.** `basedpyright` strict mode SHALL pass with zero new errors and SHALL NOT introduce any new `# pyright: ignore` suppressions. View-model dataclasses SHALL be fully typed.
- **FR-18.** Each backend SHALL place its view-model dataclasses **and** the IR-to-view-model construction functions in a single file `backends/<lang>/view.py`. (A separate `builder.py` is not used; if `view.py` exceeds ~250 lines, splitting it into `view.py` + `builder.py` is permitted as a follow-up refactor outside this spec.) Construction functions SHALL be top-level keyword-only functions named `build_<view_model>(...)`.

  Per-backend view-model unit tests SHALL exist:
  - `tests/test_view_py.py` — exercises `backends/py/view.py` builders against fixture IR derived from `tests/fixtures/struct_padded`, `tests/fixtures/scalar_wide`, and `tests/fixtures/enum_basic`. At minimum, asserts that view-model fields are populated with expected primitive values for each fixture (one assertion per non-trivial field per fixture).
  - `tests/test_view_cpp.py` — analogous, against the same three fixtures plus `tests/fixtures/const_cpp_wide`.
  - `tests/test_view_sv.py` — analogous, against the same three fixtures plus `tests/fixtures/scalar_sv_basic` and `tests/fixtures/nested_struct_sv_basic`.

  These view-model tests are in addition to (not a replacement for) existing golden-file integration tests. They use `unittest.TestCase` (constitution-compliant).

- **FR-19.** When a backend's migration is complete, the inline `render_module_<lang>` function and its `_render_*` helpers in `backends/<lang>/emitter.py` SHALL be removed. The `emit_<lang>` entry point remains and now orchestrates: (1) build view model from IR, (2) construct env, (3) render primary template, (4) write file.

 succeeded in 0ms:
# Specification — Jinja Template Migration for Code Emitters

**Spec ID:** 010-jinja-template-migration
**Branch:** feature/010-jinja-template-migration
**Stage:** specification

---

## Overview

The Python, C++, and SystemVerilog backend emitters in `src/piketype/backends/{py,cpp,sv}/emitter.py` are currently single-file inline string-builders. Each file is 700–1100 lines (py: 792, cpp: 1067, sv: 949) and intermixes IR interpretation, formatting decisions, indentation, target-language syntax, helper-method bodies, and special cases. Auditing or extending any backend requires reading long Python functions whose output shape is implicit.

This feature migrates code generation to a Jinja2-based architecture in which:

- **Python prepares typed view models** from frozen IR. View models contain only computed primitive values (names, widths, byte counts, masks, signed/unsigned flags, helper-fragment strings, import lists) and nested frozen view-model dataclasses. Semantic decisions stay in Python.
- **Jinja2 templates render structure and syntax.** Templates contain whitespace/indentation, target-language keywords, and the iteration/conditional skeleton needed to lay out a file. Templates do not compute padding, resolve type references, decide signedness, or duplicate validation.

The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.

The migration is positive-value only when semantics stay out of templates. If templates accumulate Python logic, the migration loses its benefit and the spec's success criteria are not met.

---

## User Stories

- **US-1.** As a maintainer adding a new generated language construct, I want to edit a focused Jinja template alongside a small view-model addition, so that I can change output structure without re-reading 800-line emitter files.
- **US-2.** As a reviewer auditing generated output, I want the file shape (imports, class skeletons, helper bodies, footer) to be visible as a contiguous template, so that I can read the output structure top-to-bottom without reconstructing it from scattered string concatenations.
- **US-3.** As a contributor running the test suite, I want all existing golden-file tests to continue to pass byte-for-byte after the migration, so that I can trust the migration introduced no behavioral regressions.
- **US-4.** As a release engineer, I want determinism guarantees preserved (no timestamps, no ordering changes, idempotent generation), so that generated artifacts remain reproducible and `piketype gen` run twice produces identical output.
- **US-5.** As a future feature author working on a new backend or backend variant, I want a documented view-model + template pattern to follow, so that new backends start out template-first instead of being reverse-engineered later.
- **US-6.** As a maintainer reviewing template-bound code, I want a clear and enforced rule about what may live in templates versus Python, so that templates do not silently accumulate semantic logic over time.

---

## Definitions

- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
- **Template.** A file under `backends/<lang>/templates/` ending in `.j2`, rendered through a Jinja2 `Environment` configured per FR-2.
- **Skeleton.** The structural surround of a generated artifact: file header, imports/includes, top-level type declarations, helper-method declaration boundaries, footer.
- **Fragment.** A short, self-contained string that is not a skeleton: an expression, a single hex literal, a single-line comment string, a comma-separated argument list, a Python initializer expression. Fragments are pre-computed in Python and passed into the view model as `str` fields.
- **Inline string-building (legacy).** The current pre-migration approach: Python lists of strings concatenated to form a generated file. Treated as the migration's regression target, not a permitted alternative once a backend's migration is complete.

---

## Functional Requirements

### Architecture

- **FR-1.** A new module layer SHALL exist for view models. Each backend (`py`, `cpp`, `sv`) SHALL expose typed, frozen view-model dataclasses. Naming convention: `backends/<lang>/view.py` containing `@dataclass(frozen=True, slots=True)` classes.
- **FR-2.** Each backend SHALL expose one Jinja2 `Environment` constructed via `jinja2.PackageLoader("piketype.backends.<lang>", "templates")`. Environment options SHALL be exactly: `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True`, `undefined=jinja2.StrictUndefined`, `autoescape=False`. The environment SHALL be constructed once per `emit_<lang>` call (not module-global) so that emitter state is local and testable. `FileSystemLoader` SHALL NOT be used for production rendering. (Tests MAY construct ad-hoc environments with `DictLoader` or `FileSystemLoader` for unit testing of templates.)
- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
  - `def render(*, env: jinja2.Environment, template_name: str, context: object) -> str` that renders a template and returns a string whose final character is `"\n"` (consistent with current emitter contracts). The `context` SHALL be a view-model dataclass instance; the helper SHALL pass its fields as the template context (via `dataclasses.asdict` or by passing the instance directly with templates accessing `.field` attributes — implementation choice, but uniform across backends).
- **FR-4.** Each backend SHALL keep its existing public emit entry point (`emit_py`, `emit_cpp`, `emit_sv`) with unchanged signatures and unchanged write locations; only the internal rendering pipeline changes. The IR → view-model → template → string flow SHALL be the only public migration surface.

### Migration Order and Scope

- **FR-5.** Migration SHALL proceed in this order: (1) Python backend, (2) C++ backend, (3) SystemVerilog backend. Each backend migration SHALL be a separable, independently reviewable change. A backend's migration is **complete** when its per-backend acceptance criteria (AC-P*, AC-C*, AC-S* below) are all met. Subsequent backends SHALL NOT begin until the prior backend's migration is complete.
- **FR-6.** Within each backend, migration SHALL proceed in the following sub-order:
  1. Module/file-level skeleton (header comment, top-level imports/includes, footer).
  2. Top-level type declaration skeletons (class/struct/enum scaffolding).
  3. Repeated helper-method skeletons (e.g., `to_bytes`, `from_bytes`, `_to_packed_int`, `_from_packed_int`, equality, repr, clone, pack/unpack helpers).
  4. Expression and field-level fragments — only those with meaningful structure.

  **Examples of "meaningful template structure" (MUST move to templates):** the body of a `to_bytes` method, the body of `from_bytes` with conditional sign-handling, the dataclass field block of a Python struct, an enum's member-list block, a SystemVerilog `typedef struct packed { ... }` block, a C++ class scaffold including its packed helpers.

  **Examples of "trivial fragments" (MAY remain inline in Python and be passed as `str` fields):** a single hex literal (`"0xff"`), a numeric expression rendered for a constant (`"(1 << 32) - 1"`), a single-line type alias initializer, a header comment line, an `__all__` tuple body. These fragments SHALL be pre-computed in Python and exposed as `str` fields on the view model; templates SHALL emit them with `{{ fragment }}` and SHALL NOT recompute them.

- **FR-7.** Generated output SHALL be byte-for-byte identical to current output for every committed golden in `tests/goldens/gen/` at the end of each backend's migration. A migration step that changes any golden byte SHALL be rejected and reworked, except per FR-20.

### View-Model Boundaries

- **FR-8.** View-model fields SHALL be exactly one of:
  - A primitive (`int`, `str`, `bool`, `bytes`).
  - A `tuple[T, ...]` where `T` is itself a view-model field type.
  - Another view-model dataclass instance (nesting permitted).

  Nesting is permitted but limited: a view model SHALL NOT contain itself transitively (no recursive view models). View-model construction SHALL produce values whose iteration order is stable: any field whose type is `tuple` SHALL preserve the input's declaration order or sort the input deterministically before construction.

- **FR-9.** View models SHALL NOT contain:
  - References to IR nodes (no `StructIR`, `EnumIR`, etc. fields). View models are a clean break from IR.
  - References to mutable DSL objects.
  - `set`, `frozenset`, or `dict`. For collections whose iteration order affects output, use sorted `tuple`. (Iteration order of `set` and `frozenset` is hash-dependent; iteration order of `dict` is insertion-dependent and risks subtle nondeterminism — both are forbidden.)
  - Callables, lambdas, generators, or user-defined methods that perform IR traversal at render time.
  - Validation logic or assertions about input correctness beyond what `__post_init__` cheaply enforces (e.g., asserting a width is positive).

- **FR-10.** Templates SHALL NOT:
  - Compute padding, alignment, byte counts, masks, sign-extension boundaries, or any width-derived numeric value (these arrive as primitive view-model fields).
  - Resolve type references, look up types by name, or perform any cross-IR-node navigation.
  - Decide signed vs. unsigned behavior. The view model SHALL provide signedness as a `bool` plus pre-computed numeric fragments.
  - Duplicate validation logic from `validate/engine.py`.
  - Contain Python expression blocks (`{% python %}`-style extensions or any registered global that executes arbitrary Python).
- **FR-11.** Templates MAY use:
  - Jinja standard control flow: `if`, `for`, `set`, `include`, `import`, `extends`, `block`, `macro`.
  - Jinja built-in string filters (`upper`, `lower`, `replace`, `join`, `indent`, `trim`).
  - Project-defined custom filters registered on the environment, provided each filter is a pure function over primitives, deterministic, and documented in `docs/templates.md`.

  Template indirection (macro calls, `{% include %}`, `{% extends %}`) SHALL be at most **two levels deep** measured from the top-level template entry point. (One top-level template MAY include or extend one layer of macros/partials; that layer MAY NOT itself include further partials. Inheritance via `{% extends %}` counts as one level; a `{% block %}` override does not.) This bound preserves NFR-5's "find a construct in one place" guarantee while allowing macro reuse.

### Templates

- **FR-12.** Templates SHALL live under `backends/<lang>/templates/`. Subdirectories are permitted. Required convention: each backend SHALL have exactly one **primary template** per generated artifact kind (e.g., `module.j2` for a generated `.py`/`.cpp`/`.sv` source file). Macros and partials live in files prefixed `_` (e.g., `_macros.j2`, `_struct.j2`). Reviewers locate generated output by reading the primary template; partials are an implementation detail.
- **FR-13.** Template file extensions SHALL be `.j2`. Templates SHALL NOT carry the machine-readable header themselves; the header is produced by `backends/common/headers.py` and passed in as a view-model `header: str` field, then emitted by the template with `{{ header }}`.
- **FR-14.** Templates SHALL be packaged with the wheel using `setuptools` `package-data`. `pyproject.toml` SHALL include in `[tool.setuptools.package-data]` (or equivalent) the recursive glob `"piketype.backends.py" = ["templates/**/*.j2"]` and analogous entries for `cpp` and `sv`. `MANIFEST.in` SHALL be updated if needed. Loading at runtime is via `PackageLoader` (FR-2), which discovers templates by package import, independent of the filesystem layout outside the wheel.

### Determinism

- **FR-15.** Generated output SHALL remain deterministic: identical input fixture → identical output bytes across runs, machines, and Python versions ≥ 3.12. View models SHALL NOT use `set` or `frozenset` for fields whose iteration affects output; sorted `tuple` SHALL be used instead. Any iteration that affects output SHALL be over a sorted or declaration-order-stable sequence.
- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.

### Tooling, Lint, and Hygiene

- **FR-17.** `basedpyright` strict mode SHALL pass with zero new errors and SHALL NOT introduce any new `# pyright: ignore` suppressions. View-model dataclasses SHALL be fully typed.
- **FR-18.** Each backend SHALL place its view-model dataclasses **and** the IR-to-view-model construction functions in a single file `backends/<lang>/view.py`. (A separate `builder.py` is not used; if `view.py` exceeds ~250 lines, splitting it into `view.py` + `builder.py` is permitted as a follow-up refactor outside this spec.) Construction functions SHALL be top-level keyword-only functions named `build_<view_model>(...)`.

  Per-backend view-model unit tests SHALL exist:
  - `tests/test_view_py.py` — exercises `backends/py/view.py` builders against fixture IR derived from `tests/fixtures/struct_padded`, `tests/fixtures/scalar_wide`, and `tests/fixtures/enum_basic`. At minimum, asserts that view-model fields are populated with expected primitive values for each fixture (one assertion per non-trivial field per fixture).
  - `tests/test_view_cpp.py` — analogous, against the same three fixtures plus `tests/fixtures/const_cpp_wide`.
  - `tests/test_view_sv.py` — analogous, against the same three fixtures plus `tests/fixtures/scalar_sv_basic` and `tests/fixtures/nested_struct_sv_basic`.

  These view-model tests are in addition to (not a replacement for) existing golden-file integration tests. They use `unittest.TestCase` (constitution-compliant).

- **FR-19.** When a backend's migration is complete, the inline `render_module_<lang>` function and its `_render_*` helpers in `backends/<lang>/emitter.py` SHALL be removed. The `emit_<lang>` entry point remains and now orchestrates: (1) build view model from IR, (2) construct env, (3) render primary template, (4) write file.
- **FR-20.** If a migration step legitimately needs to change output bytes (e.g., to fix a pre-existing whitespace bug discovered during migration), that change SHALL be made in a separate, single-purpose commit before the corresponding template lands. The template-landing commit SHALL produce byte-identical output to its immediate predecessor commit.
- **FR-21.** A template-hygiene check script SHALL be added at `tools/check_templates.py` and SHALL be runnable as `python tools/check_templates.py [<path>...]`. The script SHALL parse each `.j2` file under `src/piketype/backends/{py,cpp,sv}/templates/**/*.j2` and extract the contents of every Jinja expression block (text inside `{{ ... }}`) and every Jinja statement block (text inside `{% ... %}`). It SHALL fail (non-zero exit) if **any extracted Jinja block** matches **any** of these forbidden patterns (Python `re` regex applied to Jinja-block contents only — never to the surrounding target-language template text):

  1. `\(\s*1\s*<<\s*` — bit-shift mask construction.
  2. `\bbyte_count\b\s*[-+*/]|[-+*/]\s*\bbyte_count\b` — arithmetic on `byte_count` (either operand position).
  3. `\bhasattr\b|\bgetattr\b|\bisinstance\b` — runtime type interrogation.
  4. `\.__class__\b|\btype\s*\(` — type lookup.
  5. `[-+*/]\s*8\b|\b8\s*[-+*/]` — explicit-byte arithmetic in Jinja.
  6. `\bopen\s*\(|\bos\.|\bsys\.|\bsubprocess\.` — stdlib/filesystem access.
  7. `\bnow\s*\(|\brandom\b|\buuid\b` — non-determinism sources.
  8. `\{\%\s*python\b` (matched against the **raw template text**, not Jinja-block contents) — Python-embedding extension.

  Patterns 1–7 are scoped to Jinja-block contents to avoid false positives on legitimate target-language output (e.g., SystemVerilog `padded[WIDTH-1:0]`, C++ `BYTE_COUNT * 8`, Python `1 << WIDTH`). Pattern 8 is the only one that scans the whole template body.

  The script SHALL be invoked as part of the validation stage and SHALL be documented in `docs/templates.md`. The script itself SHALL ship with unit tests at `tests/test_check_templates.py` covering at least one positive (forbidden) case per pattern and one negative (allowed) case showing target-language text outside Jinja blocks is not flagged.

### Documentation

- **FR-22.** A short developer-facing document SHALL be added at `docs/templates.md` covering:
  - The view-model + template architecture, with one worked example for the Python backend (IR → view-model → template → output).
  - The "what may live in templates" rule (cross-referenced from FR-10/FR-11) and the indirection-depth bound from FR-11.
  - How to add a new template or extend an existing one, including how to register a custom filter on the environment.
  - The location of templates and view models per backend.
  - The procedure for changing generated output (regen goldens, separate commit per FR-20).
  - How to run the template-hygiene check (`python tools/check_templates.py`) and what it enforces.

---

## Non-Functional Requirements

- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.

  Measurement procedure:
  1. Add a small benchmark helper at `tools/perf_bench.py` that:
     - Copies `tests/fixtures/struct_padded/project/` to a fresh temp directory (so generated `gen/` artifacts do not dirty the working tree).
     - Calls `piketype.commands.gen.run_gen(<tmp>/alpha/piketype/types.py)` in a loop (≥ 5 iterations, discarding the first warm-up).
     - Reports the median wall-clock time in milliseconds.
  2. On `develop` at the spec-creation HEAD, run `python tools/perf_bench.py` and record the median as `baseline_ms` in `specs/010-jinja-template-migration/perf.md`.
  3. On the feature branch after each backend migration completes, run the same script and record `current_ms`.
  4. Assert `current_ms <= 1.25 * baseline_ms`.

  If `tests/fixtures/struct_padded` is not the largest fixture at validation time, the validation stage MAY substitute the largest existing fixture and SHALL document the substitution in `perf.md`.

- **NFR-2. Dependency surface.** No new runtime dependency SHALL be introduced. Jinja2 ≥ 3.1 is already declared in `pyproject.toml` and is the only template engine permitted.
- **NFR-3. Determinism.** Reproducibility guarantees from the constitution (Principle 3) SHALL be preserved verbatim. Any nondeterminism introduced by the migration SHALL block the migration.
- **NFR-4. Type safety.** `basedpyright` strict mode SHALL pass with zero new errors. No new `# pyright: ignore` suppressions SHALL be introduced solely to accommodate Jinja calls.
- **NFR-5. Auditability.** A reviewer SHALL be able to find the full rendering of any generated output construct by reading the backend's primary template (`module.j2`) plus at most one layer of partial templates referenced by it. The two-level indirection bound in FR-11 enforces this.
- **NFR-6. Reversibility per backend.** Each backend's migration SHALL be revertable by reverting a single git commit (or a contiguous sequence of commits scoped to that backend) without affecting the other backends.
- **NFR-7. Stability of public API.** The `emit_py`, `emit_cpp`, `emit_sv` function signatures and import paths SHALL NOT change. CLI behavior SHALL NOT change.

---

## Acceptance Criteria

ACs are split into **per-backend** gates (one set per migrated backend, suffix `-Py`/`-Cpp`/`-Sv`) and **feature-final** gates (`AC-Fx`) verified after all three backends are migrated.

### Per-backend gates

For backend `<lang>` ∈ {`Py`, `Cpp`, `Sv`}, the migration of that backend is complete when **all** of the following hold:

- **AC-1-`<lang>`.** All existing golden-file integration tests that exercise the `<lang>` backend pass with **unchanged** golden bytes. Test files involved: every `tests/test_*.py` that compares against `tests/goldens/gen/<case>/<lang>/**`.
- **AC-2-`<lang>`.** `find src/piketype/backends/<lang>/templates -name '*.j2' | wc -l` is at least 1 and `backends/<lang>/emitter.py` calls `render` from `backends/common/render.py` (verifiable by `grep -n "from piketype.backends.common.render import" src/piketype/backends/<lang>/emitter.py`).
- **AC-3-`<lang>`.** `backends/<lang>/emitter.py` line count has decreased relative to its pre-migration count (commit `develop`@HEAD-at-spec-creation). Helpers `_render_*` whose responsibility moved to a template are removed (no dead code).
- **AC-4-`<lang>`.** `backends/<lang>/view.py` exists and contains only `@dataclass(frozen=True, slots=True)` classes whose fields satisfy FR-8 (primitives, `tuple` of view-model field types, or other view-model dataclass instances). Verifiable by reading the file and by `basedpyright --strict`.
- **AC-5-`<lang>`.** `python tools/check_templates.py` exits 0 against `backends/<lang>/templates/`.
- **AC-6-`<lang>`.** `tests/test_view_<lang_lower>.py` exists, runs, and passes.
- **AC-7-`<lang>`.** Idempotency: running `piketype gen` twice on any in-scope fixture produces identical output bytes for `<lang>` outputs. Verifiable by the existing idempotency test, which SHALL continue to pass unchanged.

### Feature-final gates

After all three per-backend gates are met, **all** of the following SHALL hold:

- **AC-F1.** Full test suite passes: `python -m unittest discover tests` exits 0 with no skipped golden assertions.
- **AC-F2.** `basedpyright --strict src/` reports zero errors.
- **AC-F3.** `python tools/check_templates.py` exits 0 against the entire `backends/` tree.
- **AC-F4.** Performance check (NFR-1): `perf.md` exists with `baseline_ms` and `current_ms` recorded by `python tools/perf_bench.py`; `current_ms <= 1.25 * baseline_ms`.
- **AC-F5.** Wheel packaging: `pip wheel . -w /tmp/pike_wheel/ --no-deps` and inspecting the resulting wheel with `unzip -l /tmp/pike_wheel/pike_type-*.whl` shows `*.j2` files present under `piketype/backends/{py,cpp,sv}/templates/` for all three backends. (The project's distribution name in `pyproject.toml` is `pike-type`, which `setuptools` normalizes to `pike_type` in the wheel filename.) Installing into a clean venv (`pip install /tmp/pike_wheel/pike_type-*.whl`) and running `piketype gen <tmp-copy>/alpha/piketype/types.py` against a fresh temp copy of `tests/fixtures/struct_padded/project/` produces identical generated output bytes to running from source on the same fixture copy.
- **AC-F6.** `docs/templates.md` exists and covers every item enumerated in FR-22.
- **AC-F7.** Backend grep audit: `python tools/check_templates.py src/piketype/backends/py/templates src/piketype/backends/cpp/templates src/piketype/backends/sv/templates` exits 0. (Direct `grep -rE` against template files SHALL NOT be used as the audit, because raw target-language text outside Jinja blocks contains legitimate matches for many forbidden patterns; only the script's Jinja-block-scoped scan is authoritative.)
- **AC-F8.** `git log --oneline develop..HEAD` shows one or more commits per backend (Py first, Cpp second, Sv third) and the per-backend migration commits are contiguous (no interleaving). Reverting any single backend's contiguous commit range leaves the other two backends' migrations intact (verifiable by a dry-run revert).

---

## Out of Scope

- **OOS-1.** Adding new generated-output features (new DSL types, new helper methods, new file kinds). The migration is a structural refactor; feature additions land after migration.
- **OOS-2.** Migrating the runtime, build, lint, or test sub-backends under `backends/{runtime,build,lint,test}/`. Those are out of scope for this feature; only the three primary code emitters (py, cpp, sv) are in scope. Follow-up specs may address them.
- **OOS-3.** Changing template engines, adopting type-checked template tools (e.g., `mypy` plugins for Jinja), or introducing IDE/editor template tooling.
- **OOS-4.** Restructuring the IR or DSL layers. The migration consumes the existing IR unchanged.
- **OOS-5.** Performance optimization beyond NFR-1's regression budget.
- **OOS-6.** Localizing or internationalizing generated comments.
- **OOS-7.** Replacing `backends/common/headers.py` with a templated header. Headers stay inline string-built and are passed into templates as a `header: str` view-model field (per FR-13).

---

## Resolved Clarifications

The following clarifications were resolved during the clarification stage and are now binding parts of the spec. They supersede the corresponding `[NEEDS CLARIFICATION]` entries from the specification stage.

- **CL-1 (was Q-1) — Per-backend commit granularity.** Each backend's migration lands as **multiple contiguous commits** on `feature/010-jinja-template-migration`, one per FR-6 sub-step where the change is non-trivial (skeleton, top-level types, helpers, fragments). The first commit of a backend's migration block introduces `view.py` and the primary template; subsequent commits replace inline emitter sections with template-rendered output. Squash-on-merge is permitted by project policy but SHALL NOT be required by this spec. Reverting any backend's migration is a contiguous-range revert per NFR-6.

- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.

- **CL-3 (was Q-3) — Template hot-reload during development.** No special hot-reload escape hatch is added. Production and development both use `PackageLoader`. Developers using `pip install -e .` rely on standard Python import semantics; if template edits are not picked up by a long-running process, the developer restarts the process. The minor ergonomic cost is accepted because adding a `PIKETYPE_TEMPLATE_DEV=1` `FileSystemLoader` escape would create a second loading code path and a second potential source of behavior divergence.

- **CL-4 (was Q-4) — Pre-migration `baseline_ms` capture.** The baseline is captured at the start of the implementation stage, **before** the first backend migration commit, by running `python tools/perf_bench.py` against `tests/fixtures/struct_padded` while `HEAD` still produces the pre-migration output. The result is committed as the file `specs/010-jinja-template-migration/perf.md` in a single dedicated commit with subject `steel(perf): capture pre-migration baseline_ms`. Subsequent commits in the implementation/validation stages append `current_ms` measurements to the same file under the corresponding backend section. The baseline SHALL NOT be reconstructed on demand from a tagged commit; the recorded value in `perf.md` is authoritative.

## Clarification-driven additions

The following requirements were added or tightened during clarification to make the resolutions above enforceable:

- **FR-23.** `tools/perf_bench.py` SHALL exist before the first backend-migration commit. The file SHALL implement a CLI entry point `python tools/perf_bench.py [--fixture <name>] [--iterations <N>] [--output <path>]` with defaults `--fixture struct_padded`, `--iterations 5`, `--output -` (stdout). Output is a single line `<fixture>\t<median_ms>\t<min_ms>\t<max_ms>\n`, suitable for appending to `perf.md` as a markdown table row.
- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
  ```
  | stage          | backend | median_ms | min_ms | max_ms |
  |----------------|---------|-----------|--------|--------|
  | baseline       | -       | <num>     | <num>  | <num>  |
  | py-complete    | py      | <num>     | <num>  | <num>  |
  | cpp-complete   | cpp     | <num>     | <num>  | <num>  |
  | sv-complete    | sv      | <num>     | <num>  | <num>  |
  | feature-final  | all     | <num>     | <num>  | <num>  |
  ```
  Each row records a separate run of `python tools/perf_bench.py` against the same fixture. The runs are scheduled as follows: `baseline` is captured before the first migration commit (per CL-4); `py-complete` is captured immediately after the Python backend's per-backend ACs (AC-1-Py..AC-7-Py) all pass; `cpp-complete` is captured immediately after the C++ backend's per-backend ACs pass; `sv-complete` is captured immediately after the SystemVerilog backend's per-backend ACs pass; `feature-final` is captured during the validation stage immediately before evaluating AC-F4. AC-F4 verifies that the `feature-final` row's `median_ms` is ≤ 1.25× the `baseline` row's `median_ms`.

## Open Questions

(none — all questions resolved as CL-1..CL-4 above)

exec
/bin/zsh -lc 'rg -n "CL-2|FR-16|FR-25|feature-final|Changelog|filter|filters|measurement|performance" specs/010-jinja-template-migration/spec.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
95:  - Jinja built-in string filters (`upper`, `lower`, `replace`, `join`, `indent`, `trim`).
96:  - Project-defined custom filters registered on the environment, provided each filter is a pure function over primitives, deterministic, and documented in `docs/templates.md`.
109:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
145:  - How to add a new template or extend an existing one, including how to register a custom filter on the environment.
178:ACs are split into **per-backend** gates (one set per migrated backend, suffix `-Py`/`-Cpp`/`-Sv`) and **feature-final** gates (`AC-Fx`) verified after all three backends are migrated.
225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
229:- **CL-4 (was Q-4) — Pre-migration `baseline_ms` capture.** The baseline is captured at the start of the implementation stage, **before** the first backend migration commit, by running `python tools/perf_bench.py` against `tests/fixtures/struct_padded` while `HEAD` still produces the pre-migration output. The result is committed as the file `specs/010-jinja-template-migration/perf.md` in a single dedicated commit with subject `steel(perf): capture pre-migration baseline_ms`. Subsequent commits in the implementation/validation stages append `current_ms` measurements to the same file under the corresponding backend section. The baseline SHALL NOT be reconstructed on demand from a tagged commit; the recorded value in `perf.md` is authoritative.
236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
237:- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
245:  | feature-final  | all     | <num>     | <num>  | <num>  |
247:  Each row records a separate run of `python tools/perf_bench.py` against the same fixture. The runs are scheduled as follows: `baseline` is captured before the first migration commit (per CL-4); `py-complete` is captured immediately after the Python backend's per-backend ACs (AC-1-Py..AC-7-Py) all pass; `cpp-complete` is captured immediately after the C++ backend's per-backend ACs pass; `sv-complete` is captured immediately after the SystemVerilog backend's per-backend ACs pass; `feature-final` is captured during the validation stage immediately before evaluating AC-F4. AC-F4 verifies that the `feature-final` row's `median_ms` is ≤ 1.25× the `baseline` row's `median_ms`.

exec
/bin/zsh -lc "sed -n '220,270p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '88,116p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:

The following clarifications were resolved during the clarification stage and are now binding parts of the spec. They supersede the corresponding `[NEEDS CLARIFICATION]` entries from the specification stage.

- **CL-1 (was Q-1) — Per-backend commit granularity.** Each backend's migration lands as **multiple contiguous commits** on `feature/010-jinja-template-migration`, one per FR-6 sub-step where the change is non-trivial (skeleton, top-level types, helpers, fragments). The first commit of a backend's migration block introduces `view.py` and the primary template; subsequent commits replace inline emitter sections with template-rendered output. Squash-on-merge is permitted by project policy but SHALL NOT be required by this spec. Reverting any backend's migration is a contiguous-range revert per NFR-6.

- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.

- **CL-3 (was Q-3) — Template hot-reload during development.** No special hot-reload escape hatch is added. Production and development both use `PackageLoader`. Developers using `pip install -e .` rely on standard Python import semantics; if template edits are not picked up by a long-running process, the developer restarts the process. The minor ergonomic cost is accepted because adding a `PIKETYPE_TEMPLATE_DEV=1` `FileSystemLoader` escape would create a second loading code path and a second potential source of behavior divergence.

- **CL-4 (was Q-4) — Pre-migration `baseline_ms` capture.** The baseline is captured at the start of the implementation stage, **before** the first backend migration commit, by running `python tools/perf_bench.py` against `tests/fixtures/struct_padded` while `HEAD` still produces the pre-migration output. The result is committed as the file `specs/010-jinja-template-migration/perf.md` in a single dedicated commit with subject `steel(perf): capture pre-migration baseline_ms`. Subsequent commits in the implementation/validation stages append `current_ms` measurements to the same file under the corresponding backend section. The baseline SHALL NOT be reconstructed on demand from a tagged commit; the recorded value in `perf.md` is authoritative.

## Clarification-driven additions

The following requirements were added or tightened during clarification to make the resolutions above enforceable:

- **FR-23.** `tools/perf_bench.py` SHALL exist before the first backend-migration commit. The file SHALL implement a CLI entry point `python tools/perf_bench.py [--fixture <name>] [--iterations <N>] [--output <path>]` with defaults `--fixture struct_padded`, `--iterations 5`, `--output -` (stdout). Output is a single line `<fixture>\t<median_ms>\t<min_ms>\t<max_ms>\n`, suitable for appending to `perf.md` as a markdown table row.
- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
  ```
  | stage          | backend | median_ms | min_ms | max_ms |
  |----------------|---------|-----------|--------|--------|
  | baseline       | -       | <num>     | <num>  | <num>  |
  | py-complete    | py      | <num>     | <num>  | <num>  |
  | cpp-complete   | cpp     | <num>     | <num>  | <num>  |
  | sv-complete    | sv      | <num>     | <num>  | <num>  |
  | feature-final  | all     | <num>     | <num>  | <num>  |
  ```
  Each row records a separate run of `python tools/perf_bench.py` against the same fixture. The runs are scheduled as follows: `baseline` is captured before the first migration commit (per CL-4); `py-complete` is captured immediately after the Python backend's per-backend ACs (AC-1-Py..AC-7-Py) all pass; `cpp-complete` is captured immediately after the C++ backend's per-backend ACs pass; `sv-complete` is captured immediately after the SystemVerilog backend's per-backend ACs pass; `feature-final` is captured during the validation stage immediately before evaluating AC-F4. AC-F4 verifies that the `feature-final` row's `median_ms` is ≤ 1.25× the `baseline` row's `median_ms`.

## Open Questions

(none — all questions resolved as CL-1..CL-4 above)

 succeeded in 0ms:
  - Compute padding, alignment, byte counts, masks, sign-extension boundaries, or any width-derived numeric value (these arrive as primitive view-model fields).
  - Resolve type references, look up types by name, or perform any cross-IR-node navigation.
  - Decide signed vs. unsigned behavior. The view model SHALL provide signedness as a `bool` plus pre-computed numeric fragments.
  - Duplicate validation logic from `validate/engine.py`.
  - Contain Python expression blocks (`{% python %}`-style extensions or any registered global that executes arbitrary Python).
- **FR-11.** Templates MAY use:
  - Jinja standard control flow: `if`, `for`, `set`, `include`, `import`, `extends`, `block`, `macro`.
  - Jinja built-in string filters (`upper`, `lower`, `replace`, `join`, `indent`, `trim`).
  - Project-defined custom filters registered on the environment, provided each filter is a pure function over primitives, deterministic, and documented in `docs/templates.md`.

  Template indirection (macro calls, `{% include %}`, `{% extends %}`) SHALL be at most **two levels deep** measured from the top-level template entry point. (One top-level template MAY include or extend one layer of macros/partials; that layer MAY NOT itself include further partials. Inheritance via `{% extends %}` counts as one level; a `{% block %}` override does not.) This bound preserves NFR-5's "find a construct in one place" guarantee while allowing macro reuse.

### Templates

- **FR-12.** Templates SHALL live under `backends/<lang>/templates/`. Subdirectories are permitted. Required convention: each backend SHALL have exactly one **primary template** per generated artifact kind (e.g., `module.j2` for a generated `.py`/`.cpp`/`.sv` source file). Macros and partials live in files prefixed `_` (e.g., `_macros.j2`, `_struct.j2`). Reviewers locate generated output by reading the primary template; partials are an implementation detail.
- **FR-13.** Template file extensions SHALL be `.j2`. Templates SHALL NOT carry the machine-readable header themselves; the header is produced by `backends/common/headers.py` and passed in as a view-model `header: str` field, then emitted by the template with `{{ header }}`.
- **FR-14.** Templates SHALL be packaged with the wheel using `setuptools` `package-data`. `pyproject.toml` SHALL include in `[tool.setuptools.package-data]` (or equivalent) the recursive glob `"piketype.backends.py" = ["templates/**/*.j2"]` and analogous entries for `cpp` and `sv`. `MANIFEST.in` SHALL be updated if needed. Loading at runtime is via `PackageLoader` (FR-2), which discovers templates by package import, independent of the filesystem layout outside the wheel.

### Determinism

- **FR-15.** Generated output SHALL remain deterministic: identical input fixture → identical output bytes across runs, machines, and Python versions ≥ 3.12. View models SHALL NOT use `set` or `frozenset` for fields whose iteration affects output; sorted `tuple` SHALL be used instead. Any iteration that affects output SHALL be over a sorted or declaration-order-stable sequence.
- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.

### Tooling, Lint, and Hygiene

- **FR-17.** `basedpyright` strict mode SHALL pass with zero new errors and SHALL NOT introduce any new `# pyright: ignore` suppressions. View-model dataclasses SHALL be fully typed.
- **FR-18.** Each backend SHALL place its view-model dataclasses **and** the IR-to-view-model construction functions in a single file `backends/<lang>/view.py`. (A separate `builder.py` is not used; if `view.py` exceeds ~250 lines, splitting it into `view.py` + `builder.py` is permitted as a follow-up refactor outside this spec.) Construction functions SHALL be top-level keyword-only functions named `build_<view_model>(...)`.

  Per-backend view-model unit tests SHALL exist:

exec
/bin/zsh -lc "sed -n '132,152p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,140p' specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
  6. `\bopen\s*\(|\bos\.|\bsys\.|\bsubprocess\.` — stdlib/filesystem access.
  7. `\bnow\s*\(|\brandom\b|\buuid\b` — non-determinism sources.
  8. `\{\%\s*python\b` (matched against the **raw template text**, not Jinja-block contents) — Python-embedding extension.

  Patterns 1–7 are scoped to Jinja-block contents to avoid false positives on legitimate target-language output (e.g., SystemVerilog `padded[WIDTH-1:0]`, C++ `BYTE_COUNT * 8`, Python `1 << WIDTH`). Pattern 8 is the only one that scans the whole template body.

  The script SHALL be invoked as part of the validation stage and SHALL be documented in `docs/templates.md`. The script itself SHALL ship with unit tests at `tests/test_check_templates.py` covering at least one positive (forbidden) case per pattern and one negative (allowed) case showing target-language text outside Jinja blocks is not flagged.

### Documentation

- **FR-22.** A short developer-facing document SHALL be added at `docs/templates.md` covering:
  - The view-model + template architecture, with one worked example for the Python backend (IR → view-model → template → output).
  - The "what may live in templates" rule (cross-referenced from FR-10/FR-11) and the indirection-depth bound from FR-11.
  - How to add a new template or extend an existing one, including how to register a custom filter on the environment.
  - The location of templates and view models per backend.
  - The procedure for changing generated output (regen goldens, separate commit per FR-20).
  - How to run the template-hygiene check (`python tools/check_templates.py`) and what it enforces.

---

## Non-Functional Requirements

 succeeded in 0ms:
Reading additional input from stdin...
OpenAI Codex v0.125.0 (research preview)
--------
workdir: /Users/ezchi/Projects/pike-type
model: gpt-5.5
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, /Users/ezchi/.codex/memories]
reasoning effort: xhigh
reasoning summaries: none
session id: 019dd8e9-b6f7-73a2-8954-0962f431a871
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md
codex
I’ll read the clarification prompt first, then execute exactly what it asks.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Clarification Iteration 1

You are the **Gauge** in a dual-agent Forge-Gauge loop. The specification stage already produced an APPROVED spec. This is the clarification stage: open questions Q-1..Q-4 have been resolved as CL-1..CL-4, and three new requirements (FR-23, FR-24, FR-25) were added to make those resolutions enforceable.

## Inputs to Review

1. **Specification (current):** `specs/010-jinja-template-migration/spec.md` — contains the new "Resolved Clarifications" section, the "Clarification-driven additions" (FR-23..FR-25), and an empty "Open Questions" section.
2. **Clarification forge output:** `specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md`.
3. **Project Constitution:** `.steel/constitution.md`.

## Review Instructions

This is a **delta** review focused on:

1. **Were Q-1..Q-4 fully resolved?** Check that each question is replaced by a concrete decision (CL-1..CL-4) with no remaining ambiguity, weasel words, or hidden alternatives.

2. **Are CL-1..CL-4 internally consistent with the rest of the spec?**
   - CL-1 vs. NFR-6 (revertability) and AC-F8 (commit ordering).
   - CL-2 vs. FR-10/FR-11 (no semantics in templates) and FR-21 (lint patterns).
   - CL-3 vs. FR-2/FR-3 (loader strategy) and AC-F5 (wheel install).
   - CL-4 vs. NFR-1 (perf measurement) and AC-F4 (perf gate).

3. **Are FR-23, FR-24, FR-25 testable and concrete?**
   - FR-23: is the CLI signature unambiguous? Will a developer build it without further questions?
   - FR-24: does the per-filter checklist match what FR-21 / CL-2 require?
   - FR-25: does the table schema let AC-F4 actually be checked numerically?

4. **Are there any new contradictions introduced by FR-23..FR-25?** In particular:
   - Does FR-23's `--output -` to stdout conflict with the requirement that `perf.md` be the authoritative store (CL-4)? (Answer expected: no, because the implementation captures stdout into `perf.md`.) Confirm.
   - Does FR-25's "feature-final" row require an additional measurement run beyond per-backend rows? Is that run defined elsewhere? If not, flag.

5. **Constitution alignment.** Specifically check Principles 3 (determinism) and 5 (template-first); do any of CL-1..CL-4 or FR-23..FR-25 weaken either principle?

Apply severity tags `BLOCKING`, `WARNING`, `NOTE`. End with exactly `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after the verdict line.

Approve if every Q is resolved as a concrete decision and no new contradiction has been introduced. Bias toward APPROVE when in doubt — the clarification stage's purpose is exactly to lock answers in, not to perpetuate debate.

codex
The prompt asks for a delta review of the clarified spec against the forge output and constitution. I’m going to read those three inputs now and check the named CL/FR/AC/NFR cross-references directly.
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Clarification — Iteration 1 Forge Output

## Inputs

- Specification: `specs/010-jinja-template-migration/spec.md` (post-specification, 4 open questions Q-1..Q-4).
- User decision (from `/steel-run-all` invocation with no overrides supplied): "accept all recommendations" for the four open questions.

## Resolutions Applied to spec.md

| Was  | Now   | Decision |
|------|-------|----------|
| Q-1  | CL-1  | Multiple contiguous commits per backend; squash-on-merge optional. |
| Q-2  | CL-2  | Custom Jinja filters added on demand; documented per filter; tested per filter; no IR traversal / non-determinism. |
| Q-3  | CL-3  | No `PackageLoader` escape hatch; `pip install -e .` semantics accepted. |
| Q-4  | CL-4  | Baseline captured before first migration commit; stored in `perf.md`; authoritative. |

## New requirements introduced by clarification

- **FR-23.** Concrete CLI signature for `tools/perf_bench.py` (line-based output for table-row append).
- **FR-24.** `docs/templates.md` "Custom Filters" section with per-filter checklist.
- **FR-25.** `perf.md` table schema with named stages (baseline, py-complete, cpp-complete, sv-complete, feature-final) — AC-F4 now references concrete row names rather than abstract `current_ms`.

## Sections preserved unchanged

- Overview, User Stories, Definitions, FR-1..FR-22, NFR-1..NFR-7, all per-backend AC-1..7 sets, AC-F1..F8, OOS-1..OOS-7. Iteration 4 of the specification stage is preserved verbatim except for the Open Questions block (replaced with Resolved Clarifications + Clarification-driven additions) and the addition of FR-23..FR-25.

## Why these decisions hold together

- CL-1 (multi-commit) + NFR-6 (revertability) compose: a contiguous range revert affects only one backend.
- CL-2 (filter discipline) + FR-10 (no template semantics) + FR-21 (lint script) compose: filters are constrained pure helpers; semantic logic still has nowhere to hide in a filter because filters cannot perform IR traversal and the lint catches forbidden patterns inside Jinja blocks regardless of how those patterns are produced.
- CL-3 (no escape hatch) + FR-2/FR-3 (single loader strategy) compose: one loader, one code path, one set of failure modes.
- CL-4 (baseline before first migration) + FR-25 (table schema) + AC-F4 compose: the perf gate is a concrete numeric assertion against named rows, not a recomputation.

 succeeded in 0ms:
# Specification — Jinja Template Migration for Code Emitters

**Spec ID:** 010-jinja-template-migration
**Branch:** feature/010-jinja-template-migration
**Stage:** specification

---

## Overview

The Python, C++, and SystemVerilog backend emitters in `src/piketype/backends/{py,cpp,sv}/emitter.py` are currently single-file inline string-builders. Each file is 700–1100 lines (py: 792, cpp: 1067, sv: 949) and intermixes IR interpretation, formatting decisions, indentation, target-language syntax, helper-method bodies, and special cases. Auditing or extending any backend requires reading long Python functions whose output shape is implicit.

This feature migrates code generation to a Jinja2-based architecture in which:

- **Python prepares typed view models** from frozen IR. View models contain only computed primitive values (names, widths, byte counts, masks, signed/unsigned flags, helper-fragment strings, import lists) and nested frozen view-model dataclasses. Semantic decisions stay in Python.
- **Jinja2 templates render structure and syntax.** Templates contain whitespace/indentation, target-language keywords, and the iteration/conditional skeleton needed to lay out a file. Templates do not compute padding, resolve type references, decide signedness, or duplicate validation.

The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.

The migration is positive-value only when semantics stay out of templates. If templates accumulate Python logic, the migration loses its benefit and the spec's success criteria are not met.

---

## User Stories

- **US-1.** As a maintainer adding a new generated language construct, I want to edit a focused Jinja template alongside a small view-model addition, so that I can change output structure without re-reading 800-line emitter files.
- **US-2.** As a reviewer auditing generated output, I want the file shape (imports, class skeletons, helper bodies, footer) to be visible as a contiguous template, so that I can read the output structure top-to-bottom without reconstructing it from scattered string concatenations.
- **US-3.** As a contributor running the test suite, I want all existing golden-file tests to continue to pass byte-for-byte after the migration, so that I can trust the migration introduced no behavioral regressions.
- **US-4.** As a release engineer, I want determinism guarantees preserved (no timestamps, no ordering changes, idempotent generation), so that generated artifacts remain reproducible and `piketype gen` run twice produces identical output.
- **US-5.** As a future feature author working on a new backend or backend variant, I want a documented view-model + template pattern to follow, so that new backends start out template-first instead of being reverse-engineered later.
- **US-6.** As a maintainer reviewing template-bound code, I want a clear and enforced rule about what may live in templates versus Python, so that templates do not silently accumulate semantic logic over time.

---

## Definitions

- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
- **Template.** A file under `backends/<lang>/templates/` ending in `.j2`, rendered through a Jinja2 `Environment` configured per FR-2.
- **Skeleton.** The structural surround of a generated artifact: file header, imports/includes, top-level type declarations, helper-method declaration boundaries, footer.
- **Fragment.** A short, self-contained string that is not a skeleton: an expression, a single hex literal, a single-line comment string, a comma-separated argument list, a Python initializer expression. Fragments are pre-computed in Python and passed into the view model as `str` fields.
- **Inline string-building (legacy).** The current pre-migration approach: Python lists of strings concatenated to form a generated file. Treated as the migration's regression target, not a permitted alternative once a backend's migration is complete.

---

exec
/bin/zsh -lc 'tail -n 80 specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
3. **Packed types only.** All generated SystemVerilog types must be packed (`typedef struct packed`). Unpacked types are out of scope for v1.
4. **No cross-module type references (current milestone).** Struct fields referencing types from other modules are rejected by validation. This constraint will be relaxed in a future milestone.
5. **Constant widths restricted to 32/64 bits.** Arbitrary-width constants are not supported; the validation layer rejects other widths.
6. **Minimal runtime dependencies.** Only Jinja2 at runtime. No heavy frameworks, no network dependencies.
7. **Stable, reproducible output.** Ordering is by dependency-first then declaration order. No randomness or environment-dependent output.

codex
I found the main sections. One new internal conflict is visible around custom filter registration, so I’m pulling exact line references before I write the review verdict.
exec
/bin/zsh -lc 'rg -n "Principles|Deterministic output|Template-first generation" .steel/constitution.md' in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc 'rg -n "CL-2|FR-16|FR-25|AC-F4|NFR-1|FR-23|FR-24|CL-4|CL-1|CL-3|Open Questions" specs/010-jinja-template-migration/spec.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
3:## Governing Principles
7:3. **Deterministic output.** Generated code must be byte-for-byte reproducible given the same inputs. No timestamps, run-specific metadata, or non-deterministic ordering.
9:5. **Template-first generation.** Generated file structure and syntax live in templates wherever practical. Backend code builds typed view models from IR and handles semantic decisions; templates handle presentation only. Inline string building is reserved for trivial fragments or glue.

 succeeded in 0ms:
109:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
154:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
199:- **AC-F4.** Performance check (NFR-1): `perf.md` exists with `baseline_ms` and `current_ms` recorded by `python tools/perf_bench.py`; `current_ms <= 1.25 * baseline_ms`.
213:- **OOS-5.** Performance optimization beyond NFR-1's regression budget.
223:- **CL-1 (was Q-1) — Per-backend commit granularity.** Each backend's migration lands as **multiple contiguous commits** on `feature/010-jinja-template-migration`, one per FR-6 sub-step where the change is non-trivial (skeleton, top-level types, helpers, fragments). The first commit of a backend's migration block introduces `view.py` and the primary template; subsequent commits replace inline emitter sections with template-rendered output. Squash-on-merge is permitted by project policy but SHALL NOT be required by this spec. Reverting any backend's migration is a contiguous-range revert per NFR-6.
225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be registered on the environment in `backends/common/render.py` or in the per-backend env factory if backend-specific, (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py` (or per-backend `tests/test_view_<lang>.py`). Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
227:- **CL-3 (was Q-3) — Template hot-reload during development.** No special hot-reload escape hatch is added. Production and development both use `PackageLoader`. Developers using `pip install -e .` rely on standard Python import semantics; if template edits are not picked up by a long-running process, the developer restarts the process. The minor ergonomic cost is accepted because adding a `PIKETYPE_TEMPLATE_DEV=1` `FileSystemLoader` escape would create a second loading code path and a second potential source of behavior divergence.
229:- **CL-4 (was Q-4) — Pre-migration `baseline_ms` capture.** The baseline is captured at the start of the implementation stage, **before** the first backend migration commit, by running `python tools/perf_bench.py` against `tests/fixtures/struct_padded` while `HEAD` still produces the pre-migration output. The result is committed as the file `specs/010-jinja-template-migration/perf.md` in a single dedicated commit with subject `steel(perf): capture pre-migration baseline_ms`. Subsequent commits in the implementation/validation stages append `current_ms` measurements to the same file under the corresponding backend section. The baseline SHALL NOT be reconstructed on demand from a tagged commit; the recorded value in `perf.md` is authoritative.
235:- **FR-23.** `tools/perf_bench.py` SHALL exist before the first backend-migration commit. The file SHALL implement a CLI entry point `python tools/perf_bench.py [--fixture <name>] [--iterations <N>] [--output <path>]` with defaults `--fixture struct_padded`, `--iterations 5`, `--output -` (stdout). Output is a single line `<fixture>\t<median_ms>\t<min_ms>\t<max_ms>\n`, suitable for appending to `perf.md` as a markdown table row.
236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
237:- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
247:  AC-F4 verifies that the `feature-final` row's `median_ms` is ≤ 1.25× the `baseline` row's `median_ms`.
249:## Open Questions
251:(none — all questions resolved as CL-1..CL-4 above)

exec
/bin/zsh -lc 'rg -n "Q-1|Q-2|Q-3|Q-4|FR-25|feature-final|compose" specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
5:- Specification: `specs/010-jinja-template-migration/spec.md` (post-specification, 4 open questions Q-1..Q-4).
12:| Q-1  | CL-1  | Multiple contiguous commits per backend; squash-on-merge optional. |
13:| Q-2  | CL-2  | Custom Jinja filters added on demand; documented per filter; tested per filter; no IR traversal / non-determinism. |
14:| Q-3  | CL-3  | No `PackageLoader` escape hatch; `pip install -e .` semantics accepted. |
15:| Q-4  | CL-4  | Baseline captured before first migration commit; stored in `perf.md`; authoritative. |
21:- **FR-25.** `perf.md` table schema with named stages (baseline, py-complete, cpp-complete, sv-complete, feature-final) — AC-F4 now references concrete row names rather than abstract `current_ms`.
25:- Overview, User Stories, Definitions, FR-1..FR-22, NFR-1..NFR-7, all per-backend AC-1..7 sets, AC-F1..F8, OOS-1..OOS-7. Iteration 4 of the specification stage is preserved verbatim except for the Open Questions block (replaced with Resolved Clarifications + Clarification-driven additions) and the addition of FR-23..FR-25.
29:- CL-1 (multi-commit) + NFR-6 (revertability) compose: a contiguous range revert affects only one backend.
30:- CL-2 (filter discipline) + FR-10 (no template semantics) + FR-21 (lint script) compose: filters are constrained pure helpers; semantic logic still has nowhere to hide in a filter because filters cannot perform IR traversal and the lint catches forbidden patterns inside Jinja blocks regardless of how those patterns are produced.
31:- CL-3 (no escape hatch) + FR-2/FR-3 (single loader strategy) compose: one loader, one code path, one set of failure modes.
32:- CL-4 (baseline before first migration) + FR-25 (table schema) + AC-F4 compose: the perf gate is a concrete numeric assertion against named rows, not a recomputation.

exec
/bin/zsh -lc "rg -n \"FR-2\\.|FR-3\\.|FR-10\\.|FR-11\\.|FR-21\\.|FR-24\" specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
38:- **Template.** A file under `backends/<lang>/templates/` ending in `.j2`, rendered through a Jinja2 `Environment` configured per FR-2.
50:- **FR-2.** Each backend SHALL expose one Jinja2 `Environment` constructed via `jinja2.PackageLoader("piketype.backends.<lang>", "templates")`. Environment options SHALL be exactly: `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True`, `undefined=jinja2.StrictUndefined`, `autoescape=False`. The environment SHALL be constructed once per `emit_<lang>` call (not module-global) so that emitter state is local and testable. `FileSystemLoader` SHALL NOT be used for production rendering. (Tests MAY construct ad-hoc environments with `DictLoader` or `FileSystemLoader` for unit testing of templates.)
51:- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
87:- **FR-10.** Templates SHALL NOT:
93:- **FR-11.** Templates MAY use:
125:- **FR-21.** A template-hygiene check script SHALL be added at `tools/check_templates.py` and SHALL be runnable as `python tools/check_templates.py [<path>...]`. The script SHALL parse each `.j2` file under `src/piketype/backends/{py,cpp,sv}/templates/**/*.j2` and extract the contents of every Jinja expression block (text inside `{{ ... }}`) and every Jinja statement block (text inside `{% ... %}`). It SHALL fail (non-zero exit) if **any extracted Jinja block** matches **any** of these forbidden patterns (Python `re` regex applied to Jinja-block contents only — never to the surrounding target-language template text):
144:  - The "what may live in templates" rule (cross-referenced from FR-10/FR-11) and the indirection-depth bound from FR-11.
167:- **NFR-2. Dependency surface.** No new runtime dependency SHALL be introduced. Jinja2 ≥ 3.1 is already declared in `pyproject.toml` and is the only template engine permitted.
168:- **NFR-3. Determinism.** Reproducibility guarantees from the constitution (Principle 3) SHALL be preserved verbatim. Any nondeterminism introduced by the migration SHALL block the migration.
236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.

codex
BLOCKING: CL-2 allows backend-local filter registration, but FR-16 says all registered globals and filters must be auditable from `backends/common/render.py` alone. Those cannot both be true. Fix CL-2/FR-24 to require registration through `common/render.py`, or amend FR-16 deliberately. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:225) and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:109).

WARNING: FR-25 requires a `feature-final` performance row, but NFR-1/CL-4 only define baseline capture and per-backend completion measurements. The extra feature-final measurement is implied by AC-F4, not explicitly defined as a run step. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:237), [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:154), and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:229).

NOTE: Q-1..Q-4 are replaced by concrete CL-1..CL-4 decisions, and Open Questions is empty. CL-1, CL-3, and CL-4 are consistent with their referenced requirements. FR-23 stdout output does not conflict with `perf.md` being authoritative because the output is explicitly appendable/capturable into `perf.md`.

VERDICT: REVISE
2026-04-29T11:05:45.565480Z ERROR codex_core::session: failed to record rollout items: thread 019dd8e9-b6f7-73a2-8954-0962f431a871 not found
tokens used
35,306
BLOCKING: CL-2 allows backend-local filter registration, but FR-16 says all registered globals and filters must be auditable from `backends/common/render.py` alone. Those cannot both be true. Fix CL-2/FR-24 to require registration through `common/render.py`, or amend FR-16 deliberately. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:225) and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:109).

WARNING: FR-25 requires a `feature-final` performance row, but NFR-1/CL-4 only define baseline capture and per-backend completion measurements. The extra feature-final measurement is implied by AC-F4, not explicitly defined as a run step. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:237), [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:154), and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:229).

NOTE: Q-1..Q-4 are replaced by concrete CL-1..CL-4 decisions, and Open Questions is empty. CL-1, CL-3, and CL-4 are consistent with their referenced requirements. FR-23 stdout output does not conflict with `perf.md` being authoritative because the output is explicitly appendable/capturable into `perf.md`.

VERDICT: REVISE

codex
The two requested fixes are mostly present. One stale requirement still points at backend-local filter registration, so I’m checking whether that creates a real remaining contradiction rather than treating it as harmless wording.
exec
/bin/zsh -lc "rg -n \"backend-local|global env|registered location|common/render.py|tests/test_render.py|test_view\" specs/010-jinja-template-migration/spec.md specs/010-jinja-template-migration/artifacts/clarification -g '*.md'" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc 'rg -n "iter2|Clarification iter2|FR-24|CL-2|FR-25" specs/010-jinja-template-migration/artifacts/clarification specs/010-jinja-template-migration/spec.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
specs/010-jinja-template-migration/spec.md:18:The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.
specs/010-jinja-template-migration/spec.md:51:- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
specs/010-jinja-template-migration/spec.md:109:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
specs/010-jinja-template-migration/spec.md:117:  - `tests/test_view_py.py` — exercises `backends/py/view.py` builders against fixture IR derived from `tests/fixtures/struct_padded`, `tests/fixtures/scalar_wide`, and `tests/fixtures/enum_basic`. At minimum, asserts that view-model fields are populated with expected primitive values for each fixture (one assertion per non-trivial field per fixture).
specs/010-jinja-template-migration/spec.md:118:  - `tests/test_view_cpp.py` — analogous, against the same three fixtures plus `tests/fixtures/const_cpp_wide`.
specs/010-jinja-template-migration/spec.md:119:  - `tests/test_view_sv.py` — analogous, against the same three fixtures plus `tests/fixtures/scalar_sv_basic` and `tests/fixtures/nested_struct_sv_basic`.
specs/010-jinja-template-migration/spec.md:185:- **AC-2-`<lang>`.** `find src/piketype/backends/<lang>/templates -name '*.j2' | wc -l` is at least 1 and `backends/<lang>/emitter.py` calls `render` from `backends/common/render.py` (verifiable by `grep -n "from piketype.backends.common.render import" src/piketype/backends/<lang>/emitter.py`).
specs/010-jinja-template-migration/spec.md:189:- **AC-6-`<lang>`.** `tests/test_view_<lang_lower>.py` exists, runs, and passes.
specs/010-jinja-template-migration/spec.md:225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/spec.md:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:18:The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:51:- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:109:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:117:  - `tests/test_view_py.py` — exercises `backends/py/view.py` builders against fixture IR derived from `tests/fixtures/struct_padded`, `tests/fixtures/scalar_wide`, and `tests/fixtures/enum_basic`. At minimum, asserts that view-model fields are populated with expected primitive values for each fixture (one assertion per non-trivial field per fixture).
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:118:  - `tests/test_view_cpp.py` — analogous, against the same three fixtures plus `tests/fixtures/const_cpp_wide`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:119:  - `tests/test_view_sv.py` — analogous, against the same three fixtures plus `tests/fixtures/scalar_sv_basic` and `tests/fixtures/nested_struct_sv_basic`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:185:- **AC-2-`<lang>`.** `find src/piketype/backends/<lang>/templates -name '*.j2' | wc -l` is at least 1 and `backends/<lang>/emitter.py` calls `render` from `backends/common/render.py` (verifiable by `grep -n "from piketype.backends.common.render import" src/piketype/backends/<lang>/emitter.py`).
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:189:- **AC-6-`<lang>`.** `tests/test_view_<lang_lower>.py` exists, runs, and passes.
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:24:1. BLOCKING — CL-2 permitted backend-local filter registration; FR-16 requires single-file audit from `common/render.py`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:36:1. Confirm CL-2 now requires filters be defined and registered only in `backends/common/render.py`. Verify there is no remaining contradiction with FR-16.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:307:The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:340:- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:398:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:406:  - `tests/test_view_py.py` — exercises `backends/py/view.py` builders against fixture IR derived from `tests/fixtures/struct_padded`, `tests/fixtures/scalar_wide`, and `tests/fixtures/enum_basic`. At minimum, asserts that view-model fields are populated with expected primitive values for each fixture (one assertion per non-trivial field per fixture).
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:407:  - `tests/test_view_cpp.py` — analogous, against the same three fixtures plus `tests/fixtures/const_cpp_wide`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:408:  - `tests/test_view_sv.py` — analogous, against the same three fixtures plus `tests/fixtures/scalar_sv_basic` and `tests/fixtures/nested_struct_sv_basic`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:432:The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:465:- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:523:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:531:  - `tests/test_view_py.py` — exercises `backends/py/view.py` builders against fixture IR derived from `tests/fixtures/struct_padded`, `tests/fixtures/scalar_wide`, and `tests/fixtures/enum_basic`. At minimum, asserts that view-model fields are populated with expected primitive values for each fixture (one assertion per non-trivial field per fixture).
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:532:  - `tests/test_view_cpp.py` — analogous, against the same three fixtures plus `tests/fixtures/const_cpp_wide`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:533:  - `tests/test_view_sv.py` — analogous, against the same three fixtures plus `tests/fixtures/scalar_sv_basic` and `tests/fixtures/nested_struct_sv_basic`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:599:- **AC-2-`<lang>`.** `find src/piketype/backends/<lang>/templates -name '*.j2' | wc -l` is at least 1 and `backends/<lang>/emitter.py` calls `render` from `backends/common/render.py` (verifiable by `grep -n "from piketype.backends.common.render import" src/piketype/backends/<lang>/emitter.py`).
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:603:- **AC-6-`<lang>`.** `tests/test_view_<lang_lower>.py` exists, runs, and passes.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:639:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:650:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:672:109:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:675:225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:677:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:692:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:703:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:742:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:893:The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:941:109:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:946:225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be registered on the environment in `backends/common/render.py` or in the per-backend env factory if backend-specific, (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py` (or per-backend `tests/test_view_<lang>.py`). Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:950:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:976:51:- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:983:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:986:BLOCKING: CL-2 allows backend-local filter registration, but FR-16 says all registered globals and filters must be auditable from `backends/common/render.py` alone. Those cannot both be true. Fix CL-2/FR-24 to require registration through `common/render.py`, or amend FR-16 deliberately. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:225) and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:109).
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:996:BLOCKING: CL-2 allows backend-local filter registration, but FR-16 says all registered globals and filters must be auditable from `backends/common/render.py` alone. Those cannot both be true. Fix CL-2/FR-24 to require registration through `common/render.py`, or amend FR-16 deliberately. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:225) and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:109).
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:1005:The two requested fixes are mostly present. One stale requirement still points at backend-local filter registration, so I’m checking whether that creates a real remaining contradiction rather than treating it as harmless wording.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:115:The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:148:- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:206:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:214:  - `tests/test_view_py.py` — exercises `backends/py/view.py` builders against fixture IR derived from `tests/fixtures/struct_padded`, `tests/fixtures/scalar_wide`, and `tests/fixtures/enum_basic`. At minimum, asserts that view-model fields are populated with expected primitive values for each fixture (one assertion per non-trivial field per fixture).
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:215:  - `tests/test_view_cpp.py` — analogous, against the same three fixtures plus `tests/fixtures/const_cpp_wide`.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:216:  - `tests/test_view_sv.py` — analogous, against the same three fixtures plus `tests/fixtures/scalar_sv_basic` and `tests/fixtures/nested_struct_sv_basic`.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:282:- **AC-2-`<lang>`.** `find src/piketype/backends/<lang>/templates -name '*.j2' | wc -l` is at least 1 and `backends/<lang>/emitter.py` calls `render` from `backends/common/render.py` (verifiable by `grep -n "from piketype.backends.common.render import" src/piketype/backends/<lang>/emitter.py`).
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:286:- **AC-6-`<lang>`.** `tests/test_view_<lang_lower>.py` exists, runs, and passes.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:322:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be registered on the environment in `backends/common/render.py` or in the per-backend env factory if backend-specific, (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py` (or per-backend `tests/test_view_<lang>.py`). Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:333:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:479:109:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:484:225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be registered on the environment in `backends/common/render.py` or in the per-backend env factory if backend-specific, (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py` (or per-backend `tests/test_view_<lang>.py`). Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:488:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:514:51:- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:521:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:524:BLOCKING: CL-2 allows backend-local filter registration, but FR-16 says all registered globals and filters must be auditable from `backends/common/render.py` alone. Those cannot both be true. Fix CL-2/FR-24 to require registration through `common/render.py`, or amend FR-16 deliberately. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:225) and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:109).
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:534:BLOCKING: CL-2 allows backend-local filter registration, but FR-16 says all registered globals and filters must be auditable from `backends/common/render.py` alone. Those cannot both be true. Fix CL-2/FR-24 to require registration through `common/render.py`, or amend FR-16 deliberately. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:225) and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:109).
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge-prompt.md:5:1. BLOCKING — CL-2 permitted backend-local filter registration; FR-16 requires single-file audit from `common/render.py`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge-prompt.md:17:1. Confirm CL-2 now requires filters be defined and registered only in `backends/common/render.py`. Verify there is no remaining contradiction with FR-16.

 succeeded in 0ms:
specs/010-jinja-template-migration/spec.md:225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/spec.md:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/spec.md:237:- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md:3:You are the **Gauge** in a dual-agent Forge-Gauge loop. The specification stage already produced an APPROVED spec. This is the clarification stage: open questions Q-1..Q-4 have been resolved as CL-1..CL-4, and three new requirements (FR-23, FR-24, FR-25) were added to make those resolutions enforceable.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md:7:1. **Specification (current):** `specs/010-jinja-template-migration/spec.md` — contains the new "Resolved Clarifications" section, the "Clarification-driven additions" (FR-23..FR-25), and an empty "Open Questions" section.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md:19:   - CL-2 vs. FR-10/FR-11 (no semantics in templates) and FR-21 (lint patterns).
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md:23:3. **Are FR-23, FR-24, FR-25 testable and concrete?**
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md:25:   - FR-24: does the per-filter checklist match what FR-21 / CL-2 require?
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md:26:   - FR-25: does the table schema let AC-F4 actually be checked numerically?
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md:28:4. **Are there any new contradictions introduced by FR-23..FR-25?** In particular:
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md:30:   - Does FR-25's "feature-final" row require an additional measurement run beyond per-backend rows? Is that run defined elsewhere? If not, flag.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge-prompt.md:32:5. **Constitution alignment.** Specifically check Principles 3 (determinism) and 5 (template-first); do any of CL-1..CL-4 or FR-23..FR-25 weaken either principle?
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:237:- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:14:Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge-prompt.md
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:18:/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:24:1. BLOCKING — CL-2 permitted backend-local filter registration; FR-16 requires single-file audit from `common/render.py`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:25:2. WARNING — FR-25's `feature-final` perf row was not scheduled by any FR.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:36:1. Confirm CL-2 now requires filters be defined and registered only in `backends/common/render.py`. Verify there is no remaining contradiction with FR-16.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:37:2. Confirm FR-25 now explicitly schedules each row's measurement.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:187:I’m narrowing the review to CL-2, FR-16, FR-25, and the previous Gauge findings because the iteration-2 prompt asks for a surgical approval check.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:214:You are the **Gauge** in a dual-agent Forge-Gauge loop. The specification stage already produced an APPROVED spec. This is the clarification stage: open questions Q-1..Q-4 have been resolved as CL-1..CL-4, and three new requirements (FR-23, FR-24, FR-25) were added to make those resolutions enforceable.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:218:1. **Specification (current):** `specs/010-jinja-template-migration/spec.md` — contains the new "Resolved Clarifications" section, the "Clarification-driven additions" (FR-23..FR-25), and an empty "Open Questions" section.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:230:   - CL-2 vs. FR-10/FR-11 (no semantics in templates) and FR-21 (lint patterns).
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:234:3. **Are FR-23, FR-24, FR-25 testable and concrete?**
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:236:   - FR-24: does the per-filter checklist match what FR-21 / CL-2 require?
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:237:   - FR-25: does the table schema let AC-F4 actually be checked numerically?
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:239:4. **Are there any new contradictions introduced by FR-23..FR-25?** In particular:
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:241:   - Does FR-25's "feature-final" row require an additional measurement run beyond per-backend rows? Is that run defined elsewhere? If not, flag.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:243:5. **Constitution alignment.** Specifically check Principles 3 (determinism) and 5 (template-first); do any of CL-1..CL-4 or FR-23..FR-25 weaken either principle?
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:268:| Q-2  | CL-2  | Custom Jinja filters added on demand; documented per filter; tested per filter; no IR traversal / non-determinism. |
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:275:- **FR-24.** `docs/templates.md` "Custom Filters" section with per-filter checklist.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:276:- **FR-25.** `perf.md` table schema with named stages (baseline, py-complete, cpp-complete, sv-complete, feature-final) — AC-F4 now references concrete row names rather than abstract `current_ms`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:280:- Overview, User Stories, Definitions, FR-1..FR-22, NFR-1..NFR-7, all per-backend AC-1..7 sets, AC-F1..F8, OOS-1..OOS-7. Iteration 4 of the specification stage is preserved verbatim except for the Open Questions block (replaced with Resolved Clarifications + Clarification-driven additions) and the addition of FR-23..FR-25.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:285:- CL-2 (filter discipline) + FR-10 (no template semantics) + FR-21 (lint script) compose: filters are constrained pure helpers; semantic logic still has nowhere to hide in a filter because filters cannot perform IR traversal and the lint catches forbidden patterns inside Jinja blocks regardless of how those patterns are produced.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:287:- CL-4 (baseline before first migration) + FR-25 (table schema) + AC-F4 compose: the perf gate is a concrete numeric assertion against named rows, not a recomputation.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:639:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:650:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:651:- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:668:/bin/zsh -lc 'rg -n "CL-2|FR-16|FR-25|feature-final|Changelog|filter|filters|measurement|performance" specs/010-jinja-template-migration/spec.md' in /Users/ezchi/Projects/pike-type
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:675:225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:677:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:678:237:- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:692:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be defined and registered **only** in `backends/common/render.py` (no per-backend env-factory filter registration; this preserves FR-16's single-file audit guarantee), (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py`. Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:703:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:704:- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:800:You are the **Gauge** in a dual-agent Forge-Gauge loop. The specification stage already produced an APPROVED spec. This is the clarification stage: open questions Q-1..Q-4 have been resolved as CL-1..CL-4, and three new requirements (FR-23, FR-24, FR-25) were added to make those resolutions enforceable.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:804:1. **Specification (current):** `specs/010-jinja-template-migration/spec.md` — contains the new "Resolved Clarifications" section, the "Clarification-driven additions" (FR-23..FR-25), and an empty "Open Questions" section.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:816:   - CL-2 vs. FR-10/FR-11 (no semantics in templates) and FR-21 (lint patterns).
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:820:3. **Are FR-23, FR-24, FR-25 testable and concrete?**
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:822:   - FR-24: does the per-filter checklist match what FR-21 / CL-2 require?
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:823:   - FR-25: does the table schema let AC-F4 actually be checked numerically?
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:825:4. **Are there any new contradictions introduced by FR-23..FR-25?** In particular:
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:827:   - Does FR-25's "feature-final" row require an additional measurement run beyond per-backend rows? Is that run defined elsewhere? If not, flag.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:829:5. **Constitution alignment.** Specifically check Principles 3 (determinism) and 5 (template-first); do any of CL-1..CL-4 or FR-23..FR-25 weaken either principle?
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:854:| Q-2  | CL-2  | Custom Jinja filters added on demand; documented per filter; tested per filter; no IR traversal / non-determinism. |
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:861:- **FR-24.** `docs/templates.md` "Custom Filters" section with per-filter checklist.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:862:- **FR-25.** `perf.md` table schema with named stages (baseline, py-complete, cpp-complete, sv-complete, feature-final) — AC-F4 now references concrete row names rather than abstract `current_ms`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:866:- Overview, User Stories, Definitions, FR-1..FR-22, NFR-1..NFR-7, all per-backend AC-1..7 sets, AC-F1..F8, OOS-1..OOS-7. Iteration 4 of the specification stage is preserved verbatim except for the Open Questions block (replaced with Resolved Clarifications + Clarification-driven additions) and the addition of FR-23..FR-25.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:871:- CL-2 (filter discipline) + FR-10 (no template semantics) + FR-21 (lint script) compose: filters are constrained pure helpers; semantic logic still has nowhere to hide in a filter because filters cannot perform IR traversal and the lint catches forbidden patterns inside Jinja blocks regardless of how those patterns are produced.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:873:- CL-4 (baseline before first migration) + FR-25 (table schema) + AC-F4 compose: the perf gate is a concrete numeric assertion against named rows, not a recomputation.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:934:/bin/zsh -lc 'rg -n "CL-2|FR-16|FR-25|AC-F4|NFR-1|FR-23|FR-24|CL-4|CL-1|CL-3|Open Questions" specs/010-jinja-template-migration/spec.md' in /Users/ezchi/Projects/pike-type
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:946:225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be registered on the environment in `backends/common/render.py` or in the per-backend env factory if backend-specific, (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py` (or per-backend `tests/test_view_<lang>.py`). Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:950:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:951:237:- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:957:/bin/zsh -lc 'rg -n "Q-1|Q-2|Q-3|Q-4|FR-25|feature-final|compose" specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md' in /Users/ezchi/Projects/pike-type
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:961:13:| Q-2  | CL-2  | Custom Jinja filters added on demand; documented per filter; tested per filter; no IR traversal / non-determinism. |
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:964:21:- **FR-25.** `perf.md` table schema with named stages (baseline, py-complete, cpp-complete, sv-complete, feature-final) — AC-F4 now references concrete row names rather than abstract `current_ms`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:965:25:- Overview, User Stories, Definitions, FR-1..FR-22, NFR-1..NFR-7, all per-backend AC-1..7 sets, AC-F1..F8, OOS-1..OOS-7. Iteration 4 of the specification stage is preserved verbatim except for the Open Questions block (replaced with Resolved Clarifications + Clarification-driven additions) and the addition of FR-23..FR-25.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:967:30:- CL-2 (filter discipline) + FR-10 (no template semantics) + FR-21 (lint script) compose: filters are constrained pure helpers; semantic logic still has nowhere to hide in a filter because filters cannot perform IR traversal and the lint catches forbidden patterns inside Jinja blocks regardless of how those patterns are produced.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:969:32:- CL-4 (baseline before first migration) + FR-25 (table schema) + AC-F4 compose: the perf gate is a concrete numeric assertion against named rows, not a recomputation.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:972:/bin/zsh -lc "rg -n \"FR-2\\.|FR-3\\.|FR-10\\.|FR-11\\.|FR-21\\.|FR-24\" specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:983:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:986:BLOCKING: CL-2 allows backend-local filter registration, but FR-16 says all registered globals and filters must be auditable from `backends/common/render.py` alone. Those cannot both be true. Fix CL-2/FR-24 to require registration through `common/render.py`, or amend FR-16 deliberately. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:225) and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:109).
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:988:WARNING: FR-25 requires a `feature-final` performance row, but NFR-1/CL-4 only define baseline capture and per-backend completion measurements. The extra feature-final measurement is implied by AC-F4, not explicitly defined as a run step. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:237), [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:154), and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:229).
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:996:BLOCKING: CL-2 allows backend-local filter registration, but FR-16 says all registered globals and filters must be auditable from `backends/common/render.py` alone. Those cannot both be true. Fix CL-2/FR-24 to require registration through `common/render.py`, or amend FR-16 deliberately. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:225) and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:109).
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:998:WARNING: FR-25 requires a `feature-final` performance row, but NFR-1/CL-4 only define baseline capture and per-backend completion measurements. The extra feature-final measurement is implied by AC-F4, not explicitly defined as a run step. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:237), [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:154), and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:229).
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:22:You are the **Gauge** in a dual-agent Forge-Gauge loop. The specification stage already produced an APPROVED spec. This is the clarification stage: open questions Q-1..Q-4 have been resolved as CL-1..CL-4, and three new requirements (FR-23, FR-24, FR-25) were added to make those resolutions enforceable.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:26:1. **Specification (current):** `specs/010-jinja-template-migration/spec.md` — contains the new "Resolved Clarifications" section, the "Clarification-driven additions" (FR-23..FR-25), and an empty "Open Questions" section.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:38:   - CL-2 vs. FR-10/FR-11 (no semantics in templates) and FR-21 (lint patterns).
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:42:3. **Are FR-23, FR-24, FR-25 testable and concrete?**
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:44:   - FR-24: does the per-filter checklist match what FR-21 / CL-2 require?
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:45:   - FR-25: does the table schema let AC-F4 actually be checked numerically?
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:47:4. **Are there any new contradictions introduced by FR-23..FR-25?** In particular:
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:49:   - Does FR-25's "feature-final" row require an additional measurement run beyond per-backend rows? Is that run defined elsewhere? If not, flag.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:51:5. **Constitution alignment.** Specifically check Principles 3 (determinism) and 5 (template-first); do any of CL-1..CL-4 or FR-23..FR-25 weaken either principle?
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:76:| Q-2  | CL-2  | Custom Jinja filters added on demand; documented per filter; tested per filter; no IR traversal / non-determinism. |
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:83:- **FR-24.** `docs/templates.md` "Custom Filters" section with per-filter checklist.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:84:- **FR-25.** `perf.md` table schema with named stages (baseline, py-complete, cpp-complete, sv-complete, feature-final) — AC-F4 now references concrete row names rather than abstract `current_ms`.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:88:- Overview, User Stories, Definitions, FR-1..FR-22, NFR-1..NFR-7, all per-backend AC-1..7 sets, AC-F1..F8, OOS-1..OOS-7. Iteration 4 of the specification stage is preserved verbatim except for the Open Questions block (replaced with Resolved Clarifications + Clarification-driven additions) and the addition of FR-23..FR-25.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:93:- CL-2 (filter discipline) + FR-10 (no template semantics) + FR-21 (lint script) compose: filters are constrained pure helpers; semantic logic still has nowhere to hide in a filter because filters cannot perform IR traversal and the lint catches forbidden patterns inside Jinja blocks regardless of how those patterns are produced.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:95:- CL-4 (baseline before first migration) + FR-25 (table schema) + AC-F4 compose: the perf gate is a concrete numeric assertion against named rows, not a recomputation.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:322:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be registered on the environment in `backends/common/render.py` or in the per-backend env factory if backend-specific, (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py` (or per-backend `tests/test_view_<lang>.py`). Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:333:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:334:- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:472:/bin/zsh -lc 'rg -n "CL-2|FR-16|FR-25|AC-F4|NFR-1|FR-23|FR-24|CL-4|CL-1|CL-3|Open Questions" specs/010-jinja-template-migration/spec.md' in /Users/ezchi/Projects/pike-type
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:484:225:- **CL-2 (was Q-2) — Custom Jinja filters.** Custom filters SHALL be added **on demand** as concrete migration needs arise. No pre-defined filter set is mandated. Each filter added SHALL: (a) be a pure function over primitives, (b) be deterministic, (c) be registered on the environment in `backends/common/render.py` or in the per-backend env factory if backend-specific, (d) be documented in `docs/templates.md` with a one-line description, name, signature, and example use site, and (e) carry a unit test in `tests/test_render.py` (or per-backend `tests/test_view_<lang>.py`). Filters that perform IR traversal, file I/O, or non-deterministic computation are forbidden.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:488:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:489:237:- **FR-25.** `specs/010-jinja-template-migration/perf.md` SHALL contain at minimum:
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:495:/bin/zsh -lc 'rg -n "Q-1|Q-2|Q-3|Q-4|FR-25|feature-final|compose" specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md' in /Users/ezchi/Projects/pike-type
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:499:13:| Q-2  | CL-2  | Custom Jinja filters added on demand; documented per filter; tested per filter; no IR traversal / non-determinism. |
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:502:21:- **FR-25.** `perf.md` table schema with named stages (baseline, py-complete, cpp-complete, sv-complete, feature-final) — AC-F4 now references concrete row names rather than abstract `current_ms`.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:503:25:- Overview, User Stories, Definitions, FR-1..FR-22, NFR-1..NFR-7, all per-backend AC-1..7 sets, AC-F1..F8, OOS-1..OOS-7. Iteration 4 of the specification stage is preserved verbatim except for the Open Questions block (replaced with Resolved Clarifications + Clarification-driven additions) and the addition of FR-23..FR-25.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:505:30:- CL-2 (filter discipline) + FR-10 (no template semantics) + FR-21 (lint script) compose: filters are constrained pure helpers; semantic logic still has nowhere to hide in a filter because filters cannot perform IR traversal and the lint catches forbidden patterns inside Jinja blocks regardless of how those patterns are produced.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:507:32:- CL-4 (baseline before first migration) + FR-25 (table schema) + AC-F4 compose: the perf gate is a concrete numeric assertion against named rows, not a recomputation.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:510:/bin/zsh -lc "rg -n \"FR-2\\.|FR-3\\.|FR-10\\.|FR-11\\.|FR-21\\.|FR-24\" specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:521:236:- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, registered location (global env or backend-local), test file location.
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:524:BLOCKING: CL-2 allows backend-local filter registration, but FR-16 says all registered globals and filters must be auditable from `backends/common/render.py` alone. Those cannot both be true. Fix CL-2/FR-24 to require registration through `common/render.py`, or amend FR-16 deliberately. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:225) and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:109).
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:526:WARNING: FR-25 requires a `feature-final` performance row, but NFR-1/CL-4 only define baseline capture and per-backend completion measurements. The extra feature-final measurement is implied by AC-F4, not explicitly defined as a run step. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:237), [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:154), and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:229).
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:534:BLOCKING: CL-2 allows backend-local filter registration, but FR-16 says all registered globals and filters must be auditable from `backends/common/render.py` alone. Those cannot both be true. Fix CL-2/FR-24 to require registration through `common/render.py`, or amend FR-16 deliberately. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:225) and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:109).
specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:536:WARNING: FR-25 requires a `feature-final` performance row, but NFR-1/CL-4 only define baseline capture and per-backend completion measurements. The extra feature-final measurement is implied by AC-F4, not explicitly defined as a run step. See [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:237), [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:154), and [spec.md](/Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/spec.md:229).
specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md:13:| Q-2  | CL-2  | Custom Jinja filters added on demand; documented per filter; tested per filter; no IR traversal / non-determinism. |
specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md:20:- **FR-24.** `docs/templates.md` "Custom Filters" section with per-filter checklist.
specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md:21:- **FR-25.** `perf.md` table schema with named stages (baseline, py-complete, cpp-complete, sv-complete, feature-final) — AC-F4 now references concrete row names rather than abstract `current_ms`.
specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md:25:- Overview, User Stories, Definitions, FR-1..FR-22, NFR-1..NFR-7, all per-backend AC-1..7 sets, AC-F1..F8, OOS-1..OOS-7. Iteration 4 of the specification stage is preserved verbatim except for the Open Questions block (replaced with Resolved Clarifications + Clarification-driven additions) and the addition of FR-23..FR-25.
specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md:30:- CL-2 (filter discipline) + FR-10 (no template semantics) + FR-21 (lint script) compose: filters are constrained pure helpers; semantic logic still has nowhere to hide in a filter because filters cannot perform IR traversal and the lint catches forbidden patterns inside Jinja blocks regardless of how those patterns are produced.
specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md:32:- CL-4 (baseline before first migration) + FR-25 (table schema) + AC-F4 compose: the perf gate is a concrete numeric assertion against named rows, not a recomputation.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge-prompt.md:5:1. BLOCKING — CL-2 permitted backend-local filter registration; FR-16 requires single-file audit from `common/render.py`.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge-prompt.md:6:2. WARNING — FR-25's `feature-final` perf row was not scheduled by any FR.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge-prompt.md:17:1. Confirm CL-2 now requires filters be defined and registered only in `backends/common/render.py`. Verify there is no remaining contradiction with FR-16.
specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge-prompt.md:18:2. Confirm FR-25 now explicitly schedules each row's measurement.

codex
NOTE: CL-2 now requires custom filters to be defined and registered only in `backends/common/render.py`, which aligns with FR-16.

NOTE: FR-25 now explicitly schedules every measurement row, including `feature-final`.

BLOCKING: FR-24 still says custom filter docs record registered location as “global env or backend-local.” That keeps backend-local registration alive in a functional requirement and contradicts CL-2/FR-16’s single-file audit rule. Fix FR-24 to require `backends/common/render.py` as the registered location.

VERDICT: REVISE
2026-04-29T11:07:51.550458Z ERROR codex_core::session: failed to record rollout items: thread 019dd8eb-7528-7fb0-9cc1-e5d360247a14 not found
tokens used
64,613
NOTE: CL-2 now requires custom filters to be defined and registered only in `backends/common/render.py`, which aligns with FR-16.

NOTE: FR-25 now explicitly schedules every measurement row, including `feature-final`.

BLOCKING: FR-24 still says custom filter docs record registered location as “global env or backend-local.” That keeps backend-local registration alive in a functional requirement and contradicts CL-2/FR-16’s single-file audit rule. Fix FR-24 to require `backends/common/render.py` as the registered location.

VERDICT: REVISE
