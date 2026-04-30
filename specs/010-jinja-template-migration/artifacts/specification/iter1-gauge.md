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
session id: 019dd78c-acb1-7982-8733-1405de75ada7
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/specification/iter1-gauge-prompt.md
codex
I’ll read the specified prompt first, then inspect only the referenced project context needed to carry it out.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/specification/iter1-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Specification Iteration 1

You are the **Gauge** in a dual-agent Forge-Gauge loop. Your role is to critically review a feature specification produced by the Forge.

## Inputs to Review

1. **Specification under review:** `specs/010-jinja-template-migration/spec.md`
2. **Project Constitution (highest authority):** `.steel/constitution.md`
3. **Repository context:** the current working directory is the `pike-type` project root. You may read any file in the repo if you need to validate a claim made in the spec (e.g., file paths, line counts, existing patterns).

## Review Instructions

Evaluate the specification on these dimensions, with no softening:

1. **Completeness.** Are all sections present (Overview, User Stories, Functional Requirements, Non-Functional Requirements, Acceptance Criteria, Out of Scope, Open Questions)? Does the spec cover the full migration scope claimed by the feature description, including the staged migration order (Python → C++ → SV), view-model boundaries, determinism, and packaging? Are there missing requirements that would make the spec inactionable?

2. **Clarity.** Is each requirement unambiguous and free of weasel words ("appropriate", "reasonable", "as needed")? Could two engineers read it and produce divergent implementations? Are terms like "view model", "template", "skeleton", and "fragment" defined consistently?

3. **Testability.** Can each Acceptance Criterion be verified by a concrete check (running a command, grepping a file, running a test)? Flag ACs that are subjective or only verifiable by human judgment.

4. **Consistency.** Do FR/NFR/AC items contradict each other? Does the Out of Scope list contradict any FR? Do the Open Questions raise issues that should already be answered as FRs?

5. **Feasibility.** Is anything required that cannot be implemented with the project's declared stack (Python ≥ 3.12, Jinja2 ≥ 3.1, basedpyright strict, unittest)? Does the spec assume infrastructure that does not exist (e.g., a benchmarking harness for NFR-1)?

6. **Alignment with the Project Constitution.**
   - Principle 1 (single source of truth) — does the spec preserve it?
   - Principle 2 (immutable boundaries IR → backend) — does the view-model layer respect IR immutability?
   - Principle 3 (deterministic output) — are determinism requirements explicit and enforceable?
   - Principle 4 (correctness over convenience) — does the spec preserve golden-file testing?
   - Principle 5 (template-first generation) — does the spec materially advance this principle?
   - Principle 6 (generated runtime, not handwritten) — does the spec touch the runtime backend? If so, is it consistent with this principle? (Note: spec lists runtime backend as out of scope.)
   - Coding standards (frozen dataclasses, snake_case, no wildcard imports, basedpyright strict) — does the spec require compliance?
   - Project layout — does the proposed `view.py` per backend fit the existing layout convention?
   - Testing standards — is the golden-file primacy preserved?

## Output Format

Produce a review with:

- A short executive summary (2–4 sentences).
- A numbered issue list. Each issue is one item with:
  - A severity tag in ALL CAPS at the start: `BLOCKING`, `WARNING`, or `NOTE`.
    - `BLOCKING` = the spec cannot proceed to clarification without addressing this.
    - `WARNING` = the spec is workable but this issue should be resolved before clarification or carried forward as an open question.
    - `NOTE` = a minor improvement or stylistic suggestion.
  - The specific FR/NFR/AC/OOS/Q identifier (or section name) the issue refers to.
  - A one- or two-sentence description of the problem.
  - A suggested fix (if obvious) or a clarifying question to ask the Forge.
- A final line that reads exactly one of:
  - `VERDICT: APPROVE` — only if there are zero `BLOCKING` issues.
  - `VERDICT: REVISE` — if there is at least one `BLOCKING` issue.

Be strict. The cost of approving a weak spec is paying for it across all downstream stages (clarification, planning, implementation). The cost of revising is one more Forge round. Bias toward `REVISE` when in doubt.

Do not produce any text after the verdict line.

codex
The prompt asks for a strict Gauge review, not code changes. I’m reading the spec and constitution now, then I’ll verify any repo claims that affect the review.
exec
/bin/zsh -lc "sed -n '1,260p' .steel/constitution.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Project Constitution

## Governing Principles

1. **Single source of truth.** Hardware-oriented types are defined once in Python DSL modules. All generated outputs (SystemVerilog, C++, Python) are derived from that single definition.
2. **Immutable boundaries.** The pipeline has four distinct stages (Discovery -> DSL -> IR -> Backends) with frozen, immutable handoff between them. Backends and validators consume only frozen IR, never mutable DSL objects.
3. **Deterministic output.** Generated code must be byte-for-byte reproducible given the same inputs. No timestamps, run-specific metadata, or non-deterministic ordering.
4. **Correctness over convenience.** Strict type checking, explicit validation passes, and golden-file testing guard against silent regressions. If something cannot be validated, it should not be generated.
5. **Template-first generation.** Generated file structure and syntax live in templates wherever practical. Backend code builds typed view models from IR and handles semantic decisions; templates handle presentation only. Inline string building is reserved for trivial fragments or glue.
6. **Generated runtime, not handwritten.** Shared runtime support packages are generated outputs, not manually maintained infrastructure.

## Technology Stack

| Component            | Technology                | Version/Notes                                |
|----------------------|---------------------------|----------------------------------------------|
| Implementation       | Python                    | >= 3.12                                      |
| Package build        | setuptools + wheel        | setuptools >= 69                             |
| Project metadata     | `pyproject.toml`          | PEP 621                                      |
| Template engine      | Jinja2                    | >= 3.1                                      |
| Static type checking | basedpyright              | >= 1.20.0, strict mode                       |
| Test runner          | unittest (stdlib)         | Golden-file / fixture-based integration tests |
| CLI framework        | argparse (stdlib)         | Thin dispatch layer                          |
| License              | GPL-3.0-or-later          |                                              |
| Target outputs       | SystemVerilog, C++20, Python 3.12+ |                                      |

No external runtime dependencies beyond Jinja2. Dev tooling is limited to basedpyright and pytest.

## Coding Standards

### Python

- **`from __future__ import annotations`** in every module.
- **`basedpyright` strict mode** must pass with zero errors. `reportMissingTypeStubs`, `reportAny`, and `reportExplicitAny` are suppressed.
- **Frozen dataclasses** (`@dataclass(frozen=True, slots=True)`) for all IR nodes. Mutable dataclasses with `slots=True` for DSL runtime objects.
- **Naming conventions:**
  - `snake_case` for functions, methods, variables, and module names.
  - `PascalCase` for classes.
  - `UPPER_SNAKE_CASE` for module-level constants.
  - Private helpers prefixed with `_`.
  - DSL type names end with `_t` suffix (e.g., `addr_t`).
  - Generated wrapper class names use `_ct` suffix (e.g., `addr_ct`).
- **No wildcard imports.** All imports are explicit.
- **Pattern matching** (`match`/`case`) preferred for IR node dispatch.
- **Keyword-only arguments** (`*`) for helper functions to enforce clarity at call sites.
- **Type unions** use the `type X = A | B` syntax (Python 3.12+), not `typing.Union`.

### Generated Code

- All generated files carry a machine-readable header comment identifying the source DSL module(s).
- New or changed generated outputs should be backed by Jinja2 templates whenever the output has meaningful structure. This keeps generated formats easy to inspect, tweak, and extend.
- Backend Python must prepare explicit view-model data for templates. It must not hide generated-file layout inside large ad hoc string-building functions.
- SystemVerilog outputs use `_pkg` suffix for synthesizable packages and `_test_pkg` for verification-only packages.
- C++ headers use include guards (`#ifndef`/`#define`/`#endif`), not `#pragma once`.
- Python generated modules include `__init__.py` files for the full package chain.

### Project Layout

```
src/piketype/          -- implementation source
  cli.py             -- thin CLI entry point
  commands/          -- command orchestration (gen, build, test, lint)
  discovery/         -- repo scanning for piketype/ modules
  loader/            -- Python module execution
  dsl/               -- mutable runtime DSL object model
  ir/                -- frozen immutable IR nodes and builders
  validate/          -- explicit validation passes over IR
  backends/          -- code emitters (sv/, py/, cpp/, runtime/, build/, test/, lint/)
  manifest/          -- JSON manifest model and serialization
tests/
  fixtures/          -- input fixture repos
  goldens/gen/       -- expected golden outputs
docs/                -- RFC, product spec, architecture docs
```

## Development Guidelines

### Branching & Commits

- **Branch naming:** `feature/<name>` for feature branches, branching from `develop`.
- **Commit messages:** Conventional Commits format: `<type>(<scope>): <description>`.
  - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `steel`.
  - Scope matches the subsystem: `sv`, `cpp`, `py`, `dsl`, `emitter`, `codegen`, `init`, etc.

### Testing

- **Golden-file integration tests** are the primary correctness mechanism. Each test case:
  1. Copies a fixture repo from `tests/fixtures/<case>/project/` into a temp directory.
  2. Runs `piketype gen` via subprocess.
  3. Compares the full `gen/` output tree byte-for-byte against `tests/goldens/gen/<case>/`.
- **Idempotency tests** verify that running `piketype gen` twice on the same input produces identical output and does not rescan generated files as DSL modules.
- **Negative tests** verify that invalid inputs produce specific error messages and non-zero exit codes.
- Tests use `unittest.TestCase`, not pytest fixtures or parametrize.
- Golden files are committed to the repo and updated explicitly when output format changes.

### Adding a New Type or Feature

1. Define the DSL node in `dsl/`.
2. Add the frozen IR node in `ir/nodes.py`.
3. Add freeze logic in `dsl/freeze.py` and IR builder logic in `ir/builders.py`.
4. Add validation rules in `validate/engine.py`.
5. Add emission in each backend (`sv/emitter.py`, `cpp/emitter.py`, `py/emitter.py`).
6. Create a fixture repo in `tests/fixtures/` and golden output in `tests/goldens/gen/`.
7. Add an integration test case in `tests/test_gen_const_sv.py` (or a new test file for the feature area).

## Constraints

1. **Python >= 3.12 required.** The codebase uses `type` statement aliases, pattern matching, and `X | Y` union syntax that require 3.12+.
2. **No UVM dependency.** Verification helpers in generated SystemVerilog are standalone classes, not UVM components.
3. **Packed types only.** All generated SystemVerilog types must be packed (`typedef struct packed`). Unpacked types are out of scope for v1.
4. **No cross-module type references (current milestone).** Struct fields referencing types from other modules are rejected by validation. This constraint will be relaxed in a future milestone.
5. **Constant widths restricted to 32/64 bits.** Arbitrary-width constants are not supported; the validation layer rejects other widths.
6. **Minimal runtime dependencies.** Only Jinja2 at runtime. No heavy frameworks, no network dependencies.
7. **Stable, reproducible output.** Ordering is by dependency-first then declaration order. No randomness or environment-dependent output.

exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Specification — Jinja Template Migration for Code Emitters

**Spec ID:** 010-jinja-template-migration
**Branch:** feature/010-jinja-template-migration
**Stage:** specification

---

## Overview

The Python, C++, and SystemVerilog backend emitters in `src/piketype/backends/{py,cpp,sv}/emitter.py` are currently single-file inline string-builders. Each file is 700–1100 lines (py: 792, cpp: 1067, sv: 949) and intermixes IR interpretation, formatting decisions, indentation, target-language syntax, helper-method bodies, and special cases. Auditing or extending any backend requires reading long Python functions whose output shape is implicit.

This feature migrates code generation to a Jinja2-based architecture in which:

- **Python prepares typed view models** from frozen IR. View models contain only computed primitive values (names, widths, byte counts, masks, signed/unsigned flags, helper-fragment strings, import lists). Semantic decisions stay in Python.
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

## Functional Requirements

### Architecture

- **FR-1.** A new module layer SHALL exist for view models. Each backend (`py`, `cpp`, `sv`) SHALL expose typed, frozen dataclasses representing the data needed to render its output files. Naming convention: `backends/<lang>/view.py` with `@dataclass(frozen=True, slots=True)` view-model classes.
- **FR-2.** Each backend SHALL expose one Jinja2 environment scoped to its `templates/` directory using a `FileSystemLoader` rooted at `backends/<lang>/templates/`. Environment options SHALL include `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True`, `undefined=jinja2.StrictUndefined`, and `autoescape=False`. Environments SHALL be constructed once per `emit_<lang>` call (not module-global) to keep emitter state local and testable.
- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
  - A helper to construct a Jinja2 `Environment` for a given backend's template directory using the options in FR-2.
  - A helper to render a template and return a `str` whose final character is `"\n"` (consistent with current emitter contracts).
- **FR-4.** Each backend SHALL keep its existing public emit entry point (`emit_py`, `emit_cpp`, `emit_sv`) with unchanged signatures and unchanged write locations; only the internal rendering pipeline changes. The IR → view-model → template → string flow SHALL be the only public migration surface.

### Migration Order and Scope

- **FR-5.** Migration SHALL proceed in this order: (1) Python backend, (2) C++ backend, (3) SystemVerilog backend. Each backend migration SHALL be a separable, independently reviewable change. Subsequent backends SHALL NOT begin until the prior backend's golden tests pass byte-for-byte and its inline emitter has been removed.
- **FR-6.** Within each backend, migration SHALL proceed in the following sub-order:
  1. Module/file-level skeleton (header comment, top-level imports/includes, footer).
  2. Top-level type declaration skeletons (class/struct/enum scaffolding).
  3. Repeated helper-method skeletons (e.g., `to_bytes`, `from_bytes`, `_to_packed_int`, `_from_packed_int`, equality, repr, clone, pack/unpack helpers).
  4. Expression and field-level fragments (only if they have meaningful template structure; trivial one-liners MAY remain inline string concatenations).
- **FR-7.** Generated output SHALL be byte-for-byte identical to current output for every committed golden in `tests/goldens/gen/` at the end of each backend's migration. A migration step that changes any golden byte SHALL be rejected and reworked, or the change SHALL be documented and the golden updated in a separate, clearly-scoped commit (see FR-19).

### View-Model Boundaries

- **FR-8.** View models SHALL contain only the following kinds of data:
  - Primitive values (`int`, `str`, `bool`).
  - Tuples or `frozenset`s of primitives or other view-model dataclasses.
  - Pre-computed strings for fragments that the template would otherwise have to build (e.g., a fully-formatted Python expression, a comma-separated initializer list, a hex literal).
  - Pre-computed import/include/dependency lists, already deduplicated and sorted.
- **FR-9.** View models SHALL NOT contain:
  - References to IR nodes (no `StructIR`, `EnumIR`, etc. fields). View models are a clean break from IR.
  - References to mutable DSL objects.
  - Callables, lambdas, or methods that perform IR traversal at template render time.
  - Validation logic or assertions about input correctness.
- **FR-10.** Templates SHALL NOT:
  - Compute padding, alignment, byte counts, masks, sign-extension boundaries, or any width-derived numeric value.
  - Resolve type references, look up types by name, or perform any cross-IR-node navigation.
  - Decide signed vs. unsigned behavior. The view model SHALL provide this as a flag plus pre-computed numeric fragments.
  - Duplicate validation logic from `validate/engine.py`.
  - Contain Python code blocks beyond Jinja's standard control-flow constructs (`if`/`for`/`set`/`include`/`block`/`extends`/`macro`).
- **FR-11.** Templates MAY use:
  - Jinja standard control flow.
  - Jinja string filters (`upper`, `lower`, `replace`, `join`, `indent`).
  - Project-defined custom filters registered on the environment, provided each filter is a pure function over primitives and is documented in `backends/common/render.py` or alongside the environment factory.
  - Macros and template inheritance for shared scaffolding within a backend.

### Templates

- **FR-12.** Templates SHALL live under `backends/<lang>/templates/`. The directory layout within each `templates/` directory is at the migration author's discretion but SHALL be consistent across backends (recommended: `module.j2` for top-level files, `_macros.j2` for shared macros, one file per generated artifact kind).
- **FR-13.** Template file extensions SHALL be `.j2`. Templates SHALL carry no machine-generated markers themselves (the generated output's machine-readable header is produced by `backends/common/headers.py`, not by the templates).
- **FR-14.** Templates SHALL be packaged with the wheel. `pyproject.toml` SHALL include the `templates/*.j2` glob in the `setuptools` package data configuration so that `pip install piketype` ships the templates.

### Determinism

- **FR-15.** Generated output SHALL remain deterministic: identical input fixture → identical output bytes across runs, machines, and Python versions ≥ 3.12. View models SHALL contain no `set` types (only `frozenset` or sorted `tuple`); any iteration that affects output SHALL be over a sorted or declaration-order-stable sequence.
- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem, random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global.

### Tooling and Hygiene

- **FR-17.** `basedpyright` strict mode SHALL pass with zero new errors or new suppressions after the migration. View-model dataclasses SHALL be fully typed.
- **FR-18.** Unit tests SHALL exist at the view-model layer for each backend, validating the view model produced from a representative fixture IR. View-model tests SHALL be in addition to (not a replacement for) the existing golden-file integration tests.
- **FR-19.** When a backend's migration is complete, the inline `render_module_<lang>` function and its helpers in `backends/<lang>/emitter.py` SHALL be removed (no dead code retained "just in case"). The `emit_<lang>` entry point remains.
- **FR-20.** If a migration step legitimately needs to change output bytes (e.g., to fix a pre-existing whitespace bug discovered during migration), that change SHALL be made in a separate commit before the corresponding template lands. The template-landing commit SHALL produce byte-identical output to the immediate predecessor commit.

### Documentation

- **FR-21.** A short developer-facing document SHALL be added at `docs/templates.md` covering:
  - The view-model + template architecture.
  - The "what may live in templates" rule (cross-referenced from FR-10/FR-11).
  - How to add a new template or extend an existing one.
  - The location of templates and view models per backend.
  - The procedure for changing generated output (regen goldens, separate commit).

---

## Non-Functional Requirements

- **NFR-1. Performance.** Wall-clock time for `piketype gen` against the largest existing fixture SHALL NOT regress by more than 25% relative to the pre-migration baseline measured on the same machine. Jinja's caching of compiled templates within a single environment instance SHALL be relied upon to keep render overhead bounded.
- **NFR-2. Dependency surface.** No new runtime dependency SHALL be introduced. Jinja2 ≥ 3.1 is already declared in `pyproject.toml` and is the only template engine permitted.
- **NFR-3. Determinism.** Reproducibility guarantees from the constitution (Principle 3) SHALL be preserved verbatim. Any nondeterminism introduced by the migration SHALL block the migration.
- **NFR-4. Type safety.** `basedpyright` strict mode SHALL pass with zero new errors. No new `# pyright: ignore` suppressions SHALL be introduced solely to accommodate Jinja calls.
- **NFR-5. Auditability.** A reviewer SHALL be able to find the rendering of any generated output construct in a single template file, not by tracing across multiple Python helper functions.
- **NFR-6. Reversibility per backend.** Each backend's migration SHALL be revertable by reverting a single git commit (or a contiguous sequence of commits scoped to that backend) without affecting the other backends.
- **NFR-7. Stability of public API.** The `emit_py`, `emit_cpp`, `emit_sv` function signatures and import paths SHALL NOT change. CLI behavior SHALL NOT change.

---

## Acceptance Criteria

- **AC-1.** Every existing test in `tests/test_*.py` passes without modification of test files (only fixture/golden bytes may change if FR-20 conditions apply, in a separate commit). In particular, all golden-file integration tests pass byte-for-byte against unchanged goldens at the end of each backend's migration.
- **AC-2.** `find src/piketype/backends/{py,cpp,sv}/templates -name '*.j2'` lists at least one template per backend, and each backend's `emit_<lang>` calls into a Jinja2 `Environment` to produce its output.
- **AC-3.** Each backend's `emitter.py` has shrunk relative to its pre-migration line count. Helper functions whose responsibility is now in templates have been removed (no dead code).
- **AC-4.** A view-model module `backends/<lang>/view.py` exists for each migrated backend, containing only frozen dataclasses with primitive fields (per FR-8/FR-9).
- **AC-5.** `basedpyright` strict mode reports zero errors. CI passes on the feature branch.
- **AC-6.** Running `piketype gen` twice on any fixture produces identical bytes (idempotency test continues to pass).
- **AC-7.** `pip install .` from a clean checkout installs templates such that `piketype gen` run from outside the repo can locate template files (templates are packaged, not file-system-relative-to-source).
- **AC-8.** `docs/templates.md` exists and documents the architecture, the template-vs-Python boundary rule, and how to extend templates.
- **AC-9.** Grep audit: no template under `backends/<lang>/templates/` contains arithmetic on byte counts, mask construction (`(1 << ...)`), sign-extension expressions, or IR-node attribute access via Jinja getattr beyond simple `.field` reads on the view-model dataclasses.

---

## Out of Scope

- **OOS-1.** Adding new generated-output features (new DSL types, new helper methods, new file kinds). The migration is a structural refactor; feature additions land after migration.
- **OOS-2.** Migrating the runtime, build, lint, or test sub-backends under `backends/{runtime,build,lint,test}/`. Those are out of scope for v1 of this feature; only the three primary code emitters (py, cpp, sv) are in scope.
- **OOS-3.** Changing template engines, adopting type-checked template tools (e.g., `mypy` plugins for Jinja), or introducing IDE/editor template tooling.
- **OOS-4.** Restructuring the IR or DSL layers. The migration consumes the existing IR unchanged.
- **OOS-5.** Performance optimization beyond NFR-1's regression budget.
- **OOS-6.** Localizing or internationalizing generated comments.
- **OOS-7.** Replacing `backends/common/headers.py` with a templated header. Headers may stay inline string-built; they are trivial fragments and FR-6's last clause permits this.

---

## Open Questions

- **[NEEDS CLARIFICATION Q-1]** Template file packaging: should templates ship as raw `.j2` files via `setuptools` `package_data` (FR-14 default), or should the project use `importlib.resources` with `PackageLoader` rather than `FileSystemLoader`? `PackageLoader` is more robust for installed wheels and zip-safe environments but slightly more indirect. **Recommendation:** `PackageLoader` for production loading, `FileSystemLoader` only in tests if needed for hot-reload during development. Confirm direction.
- **[NEEDS CLARIFICATION Q-2]** Should the C++ and SystemVerilog migrations land in this same feature spec/branch, or should each backend's migration be a separate spec under separate `specs/NNN-...` directories? The migration order is fixed (Python → C++ → SV) but the spec scope is a process question. **Recommendation:** one spec, three commits/PRs scoped per backend, all on `feature/010-jinja-template-migration`. Confirm.
- **[NEEDS CLARIFICATION Q-3]** View-model shape for nested constructs (e.g., struct fields containing references to other types): should the field view model carry a precomputed `type_class_name: str` plus a `width: int` (flat denormalized form), or should it carry a reference to a sibling view-model dataclass (`field_type: ScalarViewModel | EnumViewModel`)? Flat form is simpler for templates; nested form preserves more structure. **Recommendation:** flat denormalized form for first migration (Python backend), revisit if it proves limiting. Confirm.
- **[NEEDS CLARIFICATION Q-4]** Custom filters: should the project define any custom Jinja filters up front (e.g., `to_hex`, `comment_block`, `c_string_escape`), or only add them as concrete need arises? **Recommendation:** add on demand, document each in `docs/templates.md`, never add a filter that performs IR traversal. Confirm.
- **[NEEDS CLARIFICATION Q-5]** How should the migration treat `backends/runtime/emitter.py` (the runtime support package generator)? It is currently the only emitter that already has imports of "Template" related symbols (per the earlier grep). Is it in scope as a fourth migration, deferred to a follow-up spec, or considered out of scope per OOS-2? **Recommendation:** explicitly out of scope here (per OOS-2); follow-up spec after the three primary backends land. Confirm.
- **[NEEDS CLARIFICATION Q-6]** Should view-model construction live in `backends/<lang>/view.py` (data classes only) with a separate `backends/<lang>/builder.py` (IR → view-model construction), or should `view.py` contain both? **Recommendation:** combine in `view.py` for first cut to limit file count; split if construction logic grows beyond ~200 lines. Confirm.

exec
/bin/zsh -lc 'rg --files' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
pyproject.toml
README.md
LICENSE
uv.lock
docs/ir-schema.md
docs/architecture.md
docs/planning.org
docs/v1-product-spec.md
docs/rfc-v1.md
docs/requirements.org
docs/milestone-01-const-sv.md
tests/test_namespace_validation.py
specs/002-namespace-cli-argument/spec.md
specs/004-cpp-constexpr-upper-case/spec.md
specs/004-cpp-constexpr-upper-case/plan.md
specs/004-cpp-constexpr-upper-case/tasks.md
specs/008-enum-dsl-type/clarifications.md
specs/008-enum-dsl-type/spec.md
specs/008-enum-dsl-type/plan.md
specs/008-enum-dsl-type/retrospect.md
specs/008-enum-dsl-type/tasks.md
specs/008-enum-dsl-type/validation.md
src/piketype/dsl/union.py
src/piketype/dsl/struct.py
src/piketype/dsl/const.py
src/piketype/dsl/base.py
src/piketype/dsl/array.py
src/piketype/dsl/enum.py
src/piketype/dsl/source_info.py
src/piketype/dsl/freeze.py
src/piketype/dsl/__init__.py
src/piketype/dsl/software_view.py
src/piketype/dsl/scalar.py
src/piketype/dsl/flags.py
src/piketype/dsl/registry.py
src/piketype/dsl/field_options.py
src/piketype/errors.py
tests/goldens/gen/namespace_override/piketype_manifest.json
specs/001-byte-aligned-struct-codegen/clarifications.md
specs/001-byte-aligned-struct-codegen/spec.md
specs/001-byte-aligned-struct-codegen/plan.md
specs/001-byte-aligned-struct-codegen/tasks.md
specs/004-cpp-constexpr-upper-case/artifacts/validation/results.md
specs/002-namespace-cli-argument/artifacts/validation/validation.md
src/piketype/commands/lint.py
src/piketype/commands/test.py
src/piketype/commands/__init__.py
src/piketype/commands/gen.py
src/piketype/commands/build.py
src/piketype/repo.py
specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt
specs/008-enum-dsl-type/artifacts/validation/iter1-forge.md
specs/002-namespace-cli-argument/artifacts/retrospect/retrospect.md
src/piketype/loader/python_loader.py
src/piketype/loader/__init__.py
src/piketype/loader/module_context.py
src/piketype/cli.py
src/piketype/__init__.py
specs/008-enum-dsl-type/artifacts/retrospect/iter1-forge.md
specs/004-cpp-constexpr-upper-case/artifacts/retrospect/retrospect.md
src/piketype/discovery/__init__.py
src/piketype/discovery/scanner.py
src/piketype/discovery/module_name.py
specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge-prompt.md
specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md
specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md
specs/002-namespace-cli-argument/artifacts/specification/iter2-gauge.md
specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md
specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md
specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md
specs/002-namespace-cli-argument/artifacts/specification/iter5-gauge.md
specs/002-namespace-cli-argument/artifacts/specification/iter4-gauge.md
specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge.md
specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md
specs/002-namespace-cli-argument/artifacts/specification/iter2-gauge-prompt.md
specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge-prompt.md
specs/002-namespace-cli-argument/artifacts/specification/iter4-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/implementation/task4-iter1-forge.md
tests/goldens/gen/namespace_override/cpp/alpha/piketype/constants_types.hpp
specs/008-enum-dsl-type/artifacts/implementation/task1-iter1-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/implementation/task3-iter1-forge.md
specs/008-enum-dsl-type/artifacts/implementation/task2-iter1-forge.md
specs/008-enum-dsl-type/artifacts/implementation/task5-iter1-forge.md
specs/008-enum-dsl-type/artifacts/implementation/task1-iter1-forge.md
specs/008-enum-dsl-type/artifacts/implementation/task1-iter1-gauge.md
src/piketype/manifest/write_json.py
src/piketype/manifest/model.py
src/piketype/manifest/__init__.py
specs/004-cpp-constexpr-upper-case/artifacts/specification/iter1-gauge-prompt.md
specs/002-namespace-cli-argument/artifacts/planning/iter1-gauge-prompt.md
specs/004-cpp-constexpr-upper-case/artifacts/specification/iter2-forge.md
specs/004-cpp-constexpr-upper-case/artifacts/specification/iter2-gauge.md
specs/004-cpp-constexpr-upper-case/artifacts/specification/iter1-gauge.md
specs/004-cpp-constexpr-upper-case/artifacts/specification/iter1-forge.md
specs/004-cpp-constexpr-upper-case/artifacts/specification/iter2-gauge-prompt.md
specs/002-namespace-cli-argument/artifacts/planning/plan.md
tests/goldens/gen/namespace_override/cpp/runtime/piketype_runtime.cpp
specs/008-enum-dsl-type/artifacts/specification/iter1-gauge-prompt.md
tests/goldens/gen/namespace_override/cpp/runtime/piketype_runtime.hpp
specs/008-enum-dsl-type/artifacts/specification/iter3-forge.md
specs/008-enum-dsl-type/artifacts/specification/iter2-forge.md
specs/008-enum-dsl-type/artifacts/specification/iter2-gauge.md
specs/008-enum-dsl-type/artifacts/specification/iter3-gauge.md
specs/008-enum-dsl-type/artifacts/specification/iter4-forge.md
specs/008-enum-dsl-type/artifacts/specification/iter4-gauge.md
specs/008-enum-dsl-type/artifacts/specification/iter1-gauge.md
specs/008-enum-dsl-type/artifacts/specification/iter1-forge.md
specs/008-enum-dsl-type/artifacts/specification/iter2-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/specification/iter3-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/specification/iter4-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter1-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter3-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter2-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter2-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter3-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter4-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter5-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter5-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter4-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter1-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter5-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter1-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter2-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter3-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/specification/iter4-gauge-prompt.md
specs/004-cpp-constexpr-upper-case/artifacts/planning/iter1-gauge-prompt.md
specs/004-cpp-constexpr-upper-case/artifacts/planning/iter3-forge.md
specs/004-cpp-constexpr-upper-case/artifacts/planning/iter2-forge.md
specs/004-cpp-constexpr-upper-case/artifacts/planning/iter2-gauge.md
specs/004-cpp-constexpr-upper-case/artifacts/planning/iter3-gauge.md
specs/004-cpp-constexpr-upper-case/artifacts/planning/iter4-forge.md
specs/004-cpp-constexpr-upper-case/artifacts/planning/iter4-gauge.md
specs/004-cpp-constexpr-upper-case/artifacts/planning/iter1-gauge.md
specs/004-cpp-constexpr-upper-case/artifacts/planning/iter1-forge.md
specs/004-cpp-constexpr-upper-case/artifacts/planning/iter2-gauge-prompt.md
specs/004-cpp-constexpr-upper-case/artifacts/planning/iter3-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/planning/iter1-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/planning/iter3-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/planning/iter2-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/planning/iter2-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/planning/iter3-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/planning/iter1-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/planning/iter1-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/planning/iter2-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/planning/iter3-gauge-prompt.md
specs/002-namespace-cli-argument/artifacts/clarification/clarification.md
src/piketype/backends/cpp/emitter.py
specs/004-cpp-constexpr-upper-case/artifacts/clarification/iter1-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/planning/iter1-gauge-prompt.md
specs/004-cpp-constexpr-upper-case/artifacts/clarification/iter1-gauge.md
specs/004-cpp-constexpr-upper-case/artifacts/clarification/iter1-forge.md
specs/008-enum-dsl-type/artifacts/planning/iter3-forge.md
specs/008-enum-dsl-type/artifacts/planning/iter2-forge.md
specs/008-enum-dsl-type/artifacts/planning/iter2-gauge.md
specs/008-enum-dsl-type/artifacts/planning/iter3-gauge.md
specs/008-enum-dsl-type/artifacts/planning/iter4-forge.md
specs/008-enum-dsl-type/artifacts/planning/iter4-gauge.md
specs/008-enum-dsl-type/artifacts/planning/iter1-gauge.md
specs/008-enum-dsl-type/artifacts/planning/iter1-forge.md
specs/008-enum-dsl-type/artifacts/planning/iter2-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/planning/iter3-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/planning/iter4-gauge-prompt.md
tests/goldens/gen/namespace_override/cpp/beta/piketype/more_types.hpp
src/piketype/backends/cpp/__init__.py
src/piketype/backends/test/emitter.py
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter1-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter2-spec-diff.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter6-delta-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter2-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter4-delta-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter2-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter1-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter6-delta-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter1-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter6-delta-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter5-delta-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter2-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter5-delta-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter5-delta-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter3-delta-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter1-spec-diff.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter3-delta-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter4-delta-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter4-delta-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/clarification/iter3-delta-forge.md
specs/004-cpp-constexpr-upper-case/artifacts/task_breakdown/iter1-gauge.md
specs/004-cpp-constexpr-upper-case/artifacts/task_breakdown/iter1-forge.md
specs/008-enum-dsl-type/artifacts/clarification/iter1-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/clarification/iter2-forge.md
specs/008-enum-dsl-type/artifacts/clarification/iter2-gauge.md
specs/008-enum-dsl-type/artifacts/clarification/iter1-gauge.md
specs/008-enum-dsl-type/artifacts/clarification/iter1-forge.md
specs/008-enum-dsl-type/artifacts/clarification/iter2-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/clarification/iter3-delta-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/clarification/iter1-spec-diff.md
specs/008-enum-dsl-type/artifacts/clarification/iter3-delta-gauge.md
specs/008-enum-dsl-type/artifacts/clarification/iter3-delta-forge.md
src/piketype/backends/common/headers.py
src/piketype/backends/common/ordering.py
src/piketype/backends/common/__init__.py
src/piketype/backends/common/render.py
src/piketype/backends/__init__.py
src/piketype/backends/test/__init__.py
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter1-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter3-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter2-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter2-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter3-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter4-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter4-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter1-gauge.md
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter1-forge.md
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter2-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter3-gauge-prompt.md
specs/001-byte-aligned-struct-codegen/artifacts/task_breakdown/iter4-gauge-prompt.md
specs/005-flags-dsl-type/spec.md
specs/005-flags-dsl-type/plan.md
specs/005-flags-dsl-type/tasks.md
specs/008-enum-dsl-type/artifacts/task_breakdown/iter1-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/task_breakdown/iter3-forge.md
specs/008-enum-dsl-type/artifacts/task_breakdown/iter2-forge.md
specs/008-enum-dsl-type/artifacts/task_breakdown/iter2-gauge.md
specs/008-enum-dsl-type/artifacts/task_breakdown/iter3-gauge.md
specs/008-enum-dsl-type/artifacts/task_breakdown/iter1-gauge.md
specs/008-enum-dsl-type/artifacts/task_breakdown/iter1-forge.md
specs/008-enum-dsl-type/artifacts/task_breakdown/iter2-gauge-prompt.md
specs/008-enum-dsl-type/artifacts/task_breakdown/iter3-gauge-prompt.md
src/piketype/backends/py/emitter.py
src/piketype/backends/runtime/emitter.py
specs/010-jinja-template-migration/spec.md
src/piketype/backends/py/__init__.py
src/piketype/backends/runtime/__init__.py
src/piketype/backends/registry.py
tests/goldens/gen/namespace_override/py/alpha/piketype/constants_types.py
tests/goldens/gen/namespace_override/py/alpha/piketype/__init__.py
specs/006-rename-to-pike-type/spec.md
specs/006-rename-to-pike-type/plan.md
specs/006-rename-to-pike-type/tasks.md
tests/goldens/gen/namespace_override/py/alpha/__init__.py
tests/goldens/gen/namespace_override/py/__init__.py
specs/005-flags-dsl-type/artifacts/validation/results.md
src/piketype/backends/sv/emitter.py
tests/goldens/gen/namespace_override/py/runtime/piketype_runtime.py
tests/goldens/gen/namespace_override/py/runtime/__init__.py
specs/005-flags-dsl-type/artifacts/retrospect/retrospect.md
specs/005-flags-dsl-type/artifacts/planning/iter1-gauge-prompt.md
specs/010-jinja-template-migration/artifacts/specification/iter1-gauge-prompt.md
specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md
specs/010-jinja-template-migration/artifacts/specification/iter1-forge.md
specs/005-flags-dsl-type/artifacts/planning/iter3-forge.md
specs/005-flags-dsl-type/artifacts/planning/iter2-forge.md
src/piketype/backends/sv/__init__.py
specs/005-flags-dsl-type/artifacts/planning/iter2-gauge.md
specs/005-flags-dsl-type/artifacts/planning/iter3-gauge.md
specs/005-flags-dsl-type/artifacts/planning/iter1-gauge.md
specs/005-flags-dsl-type/artifacts/planning/iter1-forge.md
specs/005-flags-dsl-type/artifacts/planning/iter2-gauge-prompt.md
specs/005-flags-dsl-type/artifacts/planning/iter3-gauge-prompt.md
specs/006-rename-to-pike-type/artifacts/validation/results.md
src/piketype/paths.py
specs/005-flags-dsl-type/artifacts/specification/iter1-gauge-prompt.md
specs/007-struct-flags-member/spec.md
specs/005-flags-dsl-type/artifacts/specification/iter3-forge.md
specs/005-flags-dsl-type/artifacts/specification/iter2-forge.md
specs/005-flags-dsl-type/artifacts/specification/iter2-gauge.md
specs/005-flags-dsl-type/artifacts/specification/iter3-gauge.md
specs/005-flags-dsl-type/artifacts/specification/iter4-forge.md
specs/005-flags-dsl-type/artifacts/specification/iter5-forge.md
specs/005-flags-dsl-type/artifacts/specification/iter5-gauge.md
specs/005-flags-dsl-type/artifacts/specification/iter4-gauge.md
specs/005-flags-dsl-type/artifacts/specification/iter1-gauge.md
specs/005-flags-dsl-type/artifacts/specification/iter5-gauge-prompt.md
specs/007-struct-flags-member/plan.md
specs/005-flags-dsl-type/artifacts/specification/iter1-forge.md
specs/007-struct-flags-member/tasks.md
specs/005-flags-dsl-type/artifacts/specification/iter2-gauge-prompt.md
specs/005-flags-dsl-type/artifacts/specification/iter3-gauge-prompt.md
specs/005-flags-dsl-type/artifacts/specification/iter4-gauge-prompt.md
specs/006-rename-to-pike-type/artifacts/planning/iter1-gauge-prompt.md
specs/006-rename-to-pike-type/artifacts/planning/iter2-forge.md
specs/006-rename-to-pike-type/artifacts/planning/iter2-gauge.md
specs/006-rename-to-pike-type/artifacts/planning/iter1-gauge.md
specs/006-rename-to-pike-type/artifacts/planning/iter1-forge.md
specs/006-rename-to-pike-type/artifacts/planning/iter2-gauge-prompt.md
src/piketype/backends/lint/emitter.py
specs/005-flags-dsl-type/artifacts/clarification/iter1-forge.md
tests/test_const_ranges.py
tests/test_struct_flags_member.py
tests/__init__.py
tests/test_runtime_bytes.py
tests/test_struct_enum_member.py
tests/test_gen_flags.py
tests/test_gen_const_sv.py
tests/test_dsl_const.py
tests/test_cli_smoke.py
tests/goldens/gen/namespace_override/py/beta/piketype/more_types.py
tests/goldens/gen/namespace_override/py/beta/piketype/__init__.py
tests/goldens/gen/namespace_override/py/beta/__init__.py
specs/009-struct-enum-member/spec.md
specs/009-struct-enum-member/plan.md
specs/009-struct-enum-member/tasks.md
tests/goldens/gen/const_expr_basic/piketype_manifest.json
specs/003-struct-multiple-of/spec.md
specs/006-rename-to-pike-type/artifacts/clarification/iter1-gauge-prompt.md
specs/005-flags-dsl-type/artifacts/task_breakdown/iter1-gauge-prompt.md
specs/006-rename-to-pike-type/artifacts/clarification/iter2-forge.md
specs/006-rename-to-pike-type/artifacts/clarification/iter2-gauge.md
specs/006-rename-to-pike-type/artifacts/clarification/iter1-gauge.md
specs/006-rename-to-pike-type/artifacts/clarification/iter1-forge.md
specs/006-rename-to-pike-type/artifacts/clarification/iter2-gauge-prompt.md
specs/005-flags-dsl-type/artifacts/task_breakdown/iter2-forge.md
specs/005-flags-dsl-type/artifacts/task_breakdown/iter2-gauge.md
specs/005-flags-dsl-type/artifacts/task_breakdown/iter1-gauge.md
specs/005-flags-dsl-type/artifacts/task_breakdown/iter1-forge.md
specs/006-rename-to-pike-type/artifacts/retrospect/retrospect.md
tests/test_struct_multiple_of.py
tests/test_gen_enum.py
src/piketype/backends/lint/__init__.py
src/piketype/validate/namespace.py
src/piketype/validate/topology.py
src/piketype/validate/engine.py
src/piketype/validate/cross_language.py
src/piketype/validate/widths.py
src/piketype/validate/collisions.py
src/piketype/validate/__init__.py
src/piketype/validate/naming.py
specs/006-rename-to-pike-type/artifacts/specification/iter1-gauge-prompt.md
specs/006-rename-to-pike-type/artifacts/specification/iter3-forge.md
specs/006-rename-to-pike-type/artifacts/specification/iter2-forge.md
specs/006-rename-to-pike-type/artifacts/specification/iter2-gauge.md
specs/006-rename-to-pike-type/artifacts/specification/iter3-gauge.md
specs/006-rename-to-pike-type/artifacts/specification/iter1-gauge.md
specs/006-rename-to-pike-type/artifacts/specification/iter3-forge-final.md
specs/006-rename-to-pike-type/artifacts/specification/iter1-forge.md
specs/006-rename-to-pike-type/artifacts/specification/iter2-gauge-prompt.md
specs/006-rename-to-pike-type/artifacts/specification/iter3-gauge-prompt.md
tests/goldens/gen/const_sv_basic/piketype_manifest.json
specs/007-struct-flags-member/artifacts/validation/results.md
specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-gauge-prompt.md
specs/006-rename-to-pike-type/artifacts/task_breakdown/iter3-forge.md
specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-forge.md
specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-gauge.md
specs/006-rename-to-pike-type/artifacts/task_breakdown/iter3-gauge.md
specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-gauge.md
specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-forge.md
specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-gauge-prompt.md
specs/006-rename-to-pike-type/artifacts/task_breakdown/iter3-gauge-prompt.md
tests/goldens/gen/const_expr_basic/cpp/alpha/piketype/constants_types.hpp
specs/009-struct-enum-member/artifacts/retrospect/retrospect.md
specs/007-struct-flags-member/artifacts/planning/iter1-gauge-prompt.md
specs/007-struct-flags-member/artifacts/planning/iter2-forge.md
specs/007-struct-flags-member/artifacts/planning/iter2-gauge.md
specs/007-struct-flags-member/artifacts/planning/iter1-gauge.md
specs/007-struct-flags-member/artifacts/planning/iter1-forge.md
tests/goldens/gen/struct_padded/piketype_manifest.json
tests/goldens/gen/struct_enum_member/piketype_manifest.json
src/piketype/ir/nodes.py
src/piketype/ir/manifest_view.py
src/piketype/ir/__init__.py
src/piketype/ir/builders.py
specs/003-struct-multiple-of/artifacts/validation/validation.md
tests/goldens/gen/namespace_override/sv/alpha/piketype/constants_pkg.sv
specs/009-struct-enum-member/artifacts/specification/iter1-gauge-prompt.md
specs/009-struct-enum-member/artifacts/specification/iter2-forge.md
specs/009-struct-enum-member/artifacts/specification/iter1-gauge.md
specs/009-struct-enum-member/artifacts/specification/iter1-forge.md
tests/goldens/gen/const_expr_basic/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/const_expr_basic/cpp/runtime/piketype_runtime.hpp
specs/007-struct-flags-member/artifacts/clarification/iter1-gauge-prompt.md
specs/007-struct-flags-member/artifacts/clarification/iter2-spec-diff.md
specs/007-struct-flags-member/artifacts/clarification/iter2-forge.md
specs/007-struct-flags-member/artifacts/clarification/iter2-gauge.md
specs/007-struct-flags-member/artifacts/clarification/iter1-gauge.md
specs/007-struct-flags-member/artifacts/clarification/iter1-forge.md
specs/007-struct-flags-member/artifacts/clarification/iter2-gauge-prompt.md
specs/003-struct-multiple-of/artifacts/retrospect/retrospect.md
tests/goldens/gen/namespace_override/sv/runtime/piketype_runtime_pkg.sv
specs/007-struct-flags-member/artifacts/retrospect/retrospect.md
specs/007-struct-flags-member/artifacts/task_breakdown/iter1-gauge.md
specs/007-struct-flags-member/artifacts/task_breakdown/iter1-forge.md
specs/009-struct-enum-member/artifacts/planning/iter1-gauge-prompt.md
specs/009-struct-enum-member/artifacts/planning/iter2-forge.md
specs/009-struct-enum-member/artifacts/planning/iter2-gauge.md
specs/009-struct-enum-member/artifacts/planning/iter1-gauge.md
specs/009-struct-enum-member/artifacts/planning/iter1-forge.md
specs/009-struct-enum-member/artifacts/planning/iter2-gauge-prompt.md
specs/003-struct-multiple-of/artifacts/specification/iter1-gauge-prompt.md
specs/003-struct-multiple-of/artifacts/specification/iter3-forge.md
specs/003-struct-multiple-of/artifacts/specification/iter2-forge.md
specs/003-struct-multiple-of/artifacts/specification/iter2-gauge.md
specs/003-struct-multiple-of/artifacts/specification/iter3-gauge.md
specs/003-struct-multiple-of/artifacts/specification/iter1-gauge.md
specs/003-struct-multiple-of/artifacts/specification/iter3-forge-final.md
specs/003-struct-multiple-of/artifacts/specification/iter1-forge.md
specs/003-struct-multiple-of/artifacts/specification/iter2-gauge-prompt.md
specs/003-struct-multiple-of/artifacts/specification/iter3-gauge-prompt.md
tests/goldens/gen/const_sv_basic/cpp/beta/piketype/more_types.hpp
tests/goldens/gen/struct_enum_member/cpp/alpha/piketype/types_types.hpp
specs/007-struct-flags-member/artifacts/specification/iter1-gauge-prompt.md
specs/007-struct-flags-member/artifacts/specification/iter3-forge.md
specs/007-struct-flags-member/artifacts/specification/iter2-forge.md
specs/007-struct-flags-member/artifacts/specification/iter2-gauge.md
specs/007-struct-flags-member/artifacts/specification/iter3-gauge.md
specs/007-struct-flags-member/artifacts/specification/iter4-forge.md
specs/007-struct-flags-member/artifacts/specification/iter5-forge.md
specs/007-struct-flags-member/artifacts/specification/iter5-gauge.md
specs/007-struct-flags-member/artifacts/specification/iter4-gauge.md
specs/007-struct-flags-member/artifacts/specification/iter1-gauge.md
specs/007-struct-flags-member/artifacts/specification/iter5-gauge-prompt.md
specs/007-struct-flags-member/artifacts/specification/iter1-forge.md
specs/007-struct-flags-member/artifacts/specification/iter2-gauge-prompt.md
specs/007-struct-flags-member/artifacts/specification/iter3-gauge-prompt.md
specs/007-struct-flags-member/artifacts/specification/iter4-gauge-prompt.md
tests/goldens/gen/struct_padded/cpp/alpha/piketype/types_types.hpp
specs/009-struct-enum-member/artifacts/task_breakdown/iter1-gauge.md
specs/009-struct-enum-member/artifacts/task_breakdown/iter1-forge.md
specs/003-struct-multiple-of/artifacts/planning/iter1-gauge-prompt.md
specs/003-struct-multiple-of/artifacts/planning/iter2-gauge.md
specs/003-struct-multiple-of/artifacts/planning/plan.md
specs/003-struct-multiple-of/artifacts/planning/iter1-gauge.md
specs/003-struct-multiple-of/artifacts/planning/iter2-gauge-prompt.md
tests/goldens/gen/namespace_override/sv/beta/piketype/more_pkg.sv
tests/goldens/gen/const_sv_basic/sv/alpha/piketype/constants_pkg.sv
tests/goldens/gen/const_sv_basic/cpp/alpha/piketype/constants_types.hpp
tests/goldens/gen/const_sv_basic/sv/beta/piketype/more_pkg.sv
tests/fixtures/namespace_override/project/alpha/piketype/__pycache__/constants.cpython-314.pyc
tests/fixtures/namespace_override/project/alpha/piketype/constants.py
tests/goldens/gen/const_sv_basic/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/const_expr_basic/py/alpha/piketype/constants_types.py
tests/goldens/gen/const_expr_basic/py/alpha/piketype/__init__.py
tests/goldens/gen/const_expr_basic/py/alpha/__init__.py
tests/goldens/gen/const_expr_basic/py/__init__.py
tests/goldens/gen/struct_enum_member/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/struct_enum_member/cpp/runtime/piketype_runtime.hpp
tests/goldens/gen/const_sv_basic/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/const_sv_basic/cpp/runtime/piketype_runtime.hpp
tests/goldens/gen/struct_padded/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/struct_padded/cpp/runtime/piketype_runtime.hpp
specs/003-struct-multiple-of/artifacts/clarification/clarification.md
tests/goldens/gen/scalar_sv_basic/piketype_manifest.json
tests/goldens/gen/const_expr_basic/py/runtime/piketype_runtime.py
tests/goldens/gen/const_expr_basic/py/runtime/__init__.py
tests/goldens/gen/const_sv_basic/py/alpha/piketype/constants_types.py
tests/goldens/gen/const_sv_basic/py/alpha/piketype/__init__.py
tests/goldens/gen/const_sv_basic/py/alpha/__init__.py
tests/goldens/gen/const_sv_basic/py/__init__.py
tests/fixtures/namespace_override/project/beta/piketype/more.py
tests/goldens/gen/const_sv_basic/py/runtime/piketype_runtime.py
tests/goldens/gen/const_sv_basic/py/runtime/__init__.py
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py
tests/goldens/gen/struct_enum_member/py/alpha/piketype/__init__.py
tests/goldens/gen/struct_enum_member/py/alpha/__init__.py
tests/goldens/gen/struct_enum_member/py/__init__.py
tests/fixtures/namespace_override/project/beta/piketype/__pycache__/more.cpython-314.pyc
tests/fixtures/flags_basic/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/flags_basic/project/alpha/piketype/types.py
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py
tests/goldens/gen/struct_padded/py/alpha/piketype/__init__.py
tests/goldens/gen/struct_padded/py/alpha/__init__.py
tests/goldens/gen/struct_padded/py/__init__.py
tests/fixtures/no_dsl/project/alpha/piketype/__pycache__/empty.cpython-314.pyc
tests/fixtures/no_dsl/project/alpha/piketype/empty.py
tests/goldens/gen/const_sv_basic/py/beta/piketype/more_types.py
tests/goldens/gen/const_sv_basic/py/beta/piketype/__init__.py
tests/goldens/gen/struct_enum_member/py/runtime/piketype_runtime.py
tests/goldens/gen/struct_enum_member/py/runtime/__init__.py
tests/goldens/gen/const_sv_basic/py/beta/__init__.py
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp
tests/fixtures/struct_enum_member/project/alpha/piketype/__pycache__/types.cpython-313.pyc
tests/fixtures/struct_enum_member/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/struct_enum_member/project/alpha/piketype/types.py
tests/goldens/gen/struct_padded/py/runtime/piketype_runtime.py
tests/goldens/gen/struct_padded/py/runtime/__init__.py
tests/goldens/gen/const_expr_basic/sv/alpha/piketype/constants_pkg.sv
tests/goldens/gen/scalar_sv_basic/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/scalar_sv_basic/cpp/runtime/piketype_runtime.hpp
tests/fixtures/const_collision/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/const_collision/project/alpha/piketype/types.py
tests/fixtures/const_expr_basic/project/alpha/piketype/__pycache__/constants.cpython-314.pyc
tests/goldens/gen/const_expr_basic/sv/runtime/piketype_runtime_pkg.sv
tests/fixtures/const_expr_basic/project/alpha/piketype/constants.py
tests/fixtures/const_sv_basic/project/alpha/piketype/__pycache__/constants.cpython-314.pyc
tests/fixtures/const_sv_basic/project/alpha/piketype/constants.py
tests/goldens/gen/flags_basic/piketype_manifest.json
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/__init__.py
tests/goldens/gen/scalar_sv_basic/py/alpha/__init__.py
tests/goldens/gen/scalar_sv_basic/py/__init__.py
tests/goldens/gen/struct_padded/sv/alpha/piketype/types_pkg.sv
tests/goldens/gen/struct_padded/sv/alpha/piketype/types_test_pkg.sv
tests/goldens/gen/scalar_sv_basic/py/runtime/piketype_runtime.py
tests/goldens/gen/scalar_sv_basic/py/runtime/__init__.py
tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_pkg.sv
tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_test_pkg.sv
tests/fixtures/const_sv_basic/project/beta/piketype/more.py
tests/fixtures/struct_multiple_of/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/struct_multiple_of/project/alpha/piketype/types.py
tests/fixtures/scalar_sv_basic/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/scalar_sv_basic/project/alpha/piketype/types.py
tests/goldens/gen/struct_padded/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/struct_enum_member/sv/runtime/piketype_runtime_pkg.sv
tests/fixtures/const_sv_basic/project/beta/piketype/__pycache__/more.cpython-314.pyc
tests/fixtures/const_cpp_wide/project/alpha/piketype/__pycache__/constants.cpython-314.pyc
tests/fixtures/const_cpp_wide/project/alpha/piketype/constants.py
tests/goldens/gen/flags_basic/cpp/alpha/piketype/types_types.hpp
tests/goldens/gen/struct_flags_member/piketype_manifest.json
tests/fixtures/struct_signed/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/struct_pad_collision/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/struct_signed/project/alpha/piketype/types.py
tests/fixtures/struct_pad_collision/project/alpha/piketype/types.py
tests/goldens/gen/scalar_wide/piketype_manifest.json
tests/fixtures/scalar_wide/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/scalar_wide/project/alpha/piketype/types.py
tests/fixtures/scalar_signed_wide/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/scalar_signed_wide/project/alpha/piketype/types.py
tests/goldens/gen/flags_basic/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_pkg.sv
tests/goldens/gen/flags_basic/cpp/runtime/piketype_runtime.hpp
tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_test_pkg.sv
tests/goldens/gen/scalar_sv_basic/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/const_cpp_explicit_uint32/piketype_manifest.json
tests/fixtures/outside_piketype/project/alpha/not_piketype/plain.py
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py
tests/goldens/gen/flags_basic/py/alpha/piketype/__init__.py
tests/goldens/gen/flags_basic/py/alpha/__init__.py
tests/goldens/gen/flags_basic/py/__init__.py
tests/goldens/gen/flags_basic/py/runtime/piketype_runtime.py
tests/goldens/gen/flags_basic/py/runtime/__init__.py
tests/goldens/gen/struct_flags_member/cpp/alpha/piketype/types_types.hpp
tests/goldens/gen/scalar_wide/cpp/alpha/piketype/types_types.hpp
tests/fixtures/outside_piketype/project/alpha/not_piketype/__pycache__/plain.cpython-314.pyc
tests/fixtures/struct_wide/project/alpha/piketype/types.py
tests/fixtures/const_cpp_explicit_uint32/project/alpha/piketype/constants.py
tests/goldens/gen/const_cpp_explicit_uint32/cpp/alpha/piketype/constants_types.hpp
tests/fixtures/const_cpp_explicit_uint32/project/alpha/piketype/__pycache__/constants.cpython-314.pyc
tests/goldens/gen/struct_flags_member/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/struct_flags_member/cpp/runtime/piketype_runtime.hpp
tests/fixtures/struct_padded/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/struct_padded/project/alpha/piketype/types.py
tests/fixtures/struct_sv_basic/project/alpha/piketype/types.py
tests/fixtures/struct_flags_member/project/alpha/piketype/types.py
tests/fixtures/nested_struct_sv_basic/project/alpha/piketype/types.py
tests/fixtures/struct_wide/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/goldens/gen/scalar_wide/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/scalar_wide/cpp/runtime/piketype_runtime.hpp
tests/goldens/gen/struct_multiple_of/piketype_manifest.json
tests/fixtures/struct_flags_member/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/goldens/gen/const_cpp_explicit_uint32/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/const_cpp_explicit_uint32/cpp/runtime/piketype_runtime.hpp
tests/fixtures/struct_sv_basic/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/enum_basic/project/foo/piketype/defs.py
tests/goldens/gen/flags_basic/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/flags_basic/sv/alpha/piketype/types_test_pkg.sv
tests/goldens/gen/flags_basic/sv/alpha/piketype/types_pkg.sv
tests/fixtures/nested_struct_sv_basic/project/alpha/piketype/__pycache__/types.cpython-314.pyc
tests/fixtures/enum_basic/project/foo/piketype/__pycache__/defs.cpython-314.pyc
tests/goldens/gen/const_cpp_wide/piketype_manifest.json
tests/goldens/gen/struct_signed/piketype_manifest.json
tests/goldens/gen/enum_basic/piketype_manifest.json
tests/goldens/gen/nested_struct_sv_basic/piketype_manifest.json
tests/goldens/gen/const_cpp_explicit_uint32/py/alpha/piketype/constants_types.py
tests/goldens/gen/const_cpp_explicit_uint32/py/alpha/piketype/__init__.py
tests/goldens/gen/const_cpp_explicit_uint32/py/alpha/__init__.py
tests/goldens/gen/const_cpp_explicit_uint32/py/__init__.py
tests/goldens/gen/const_cpp_explicit_uint32/py/runtime/piketype_runtime.py
tests/goldens/gen/const_cpp_explicit_uint32/py/runtime/__init__.py
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py
tests/goldens/gen/struct_flags_member/py/alpha/piketype/__init__.py
tests/goldens/gen/struct_flags_member/py/alpha/__init__.py
tests/goldens/gen/struct_flags_member/py/__init__.py
tests/goldens/gen/struct_multiple_of/sv/alpha/piketype/types_pkg.sv
tests/goldens/gen/struct_multiple_of/sv/alpha/piketype/types_test_pkg.sv
tests/goldens/gen/struct_multiple_of/cpp/alpha/piketype/types_types.hpp
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py
tests/goldens/gen/scalar_wide/py/alpha/piketype/__init__.py
tests/goldens/gen/scalar_wide/py/alpha/__init__.py
tests/goldens/gen/scalar_wide/py/__init__.py
tests/goldens/gen/const_cpp_explicit_uint32/sv/alpha/piketype/constants_pkg.sv
tests/goldens/gen/struct_flags_member/sv/alpha/piketype/types_pkg.sv
tests/goldens/gen/struct_flags_member/sv/alpha/piketype/types_test_pkg.sv
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/__init__.py
tests/goldens/gen/struct_multiple_of/py/alpha/__init__.py
tests/goldens/gen/struct_multiple_of/py/__init__.py
tests/goldens/gen/const_cpp_wide/cpp/alpha/piketype/constants_types.hpp
tests/goldens/gen/struct_flags_member/py/runtime/piketype_runtime.py
tests/goldens/gen/struct_flags_member/py/runtime/__init__.py
tests/goldens/gen/const_cpp_explicit_uint32/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/struct_multiple_of/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_pkg.sv
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_test_pkg.sv
tests/goldens/gen/struct_multiple_of/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/struct_multiple_of/cpp/runtime/piketype_runtime.hpp
tests/goldens/gen/scalar_wide/py/runtime/piketype_runtime.py
tests/goldens/gen/scalar_wide/py/runtime/__init__.py
tests/goldens/gen/enum_basic/cpp/foo/piketype/defs_types.hpp
tests/goldens/gen/const_cpp_wide/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/struct_multiple_of/py/runtime/piketype_runtime.py
tests/goldens/gen/const_cpp_wide/cpp/runtime/piketype_runtime.hpp
tests/goldens/gen/struct_multiple_of/py/runtime/__init__.py
tests/goldens/gen/struct_sv_basic/piketype_manifest.json
tests/goldens/gen/struct_flags_member/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/struct_signed/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp
tests/goldens/gen/struct_signed/cpp/runtime/piketype_runtime.hpp
tests/goldens/gen/nested_struct_sv_basic/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/nested_struct_sv_basic/cpp/runtime/piketype_runtime.hpp
tests/goldens/gen/scalar_wide/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/struct_wide/piketype_manifest.json
tests/goldens/gen/enum_basic/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/enum_basic/cpp/runtime/piketype_runtime.hpp
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/__init__.py
tests/goldens/gen/nested_struct_sv_basic/py/alpha/__init__.py
tests/goldens/gen/nested_struct_sv_basic/py/__init__.py
tests/goldens/gen/nested_struct_sv_basic/py/runtime/piketype_runtime.py
tests/goldens/gen/nested_struct_sv_basic/py/runtime/__init__.py
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py
tests/goldens/gen/enum_basic/py/foo/piketype/__init__.py
tests/goldens/gen/enum_basic/py/foo/__init__.py
tests/goldens/gen/enum_basic/py/__init__.py
tests/goldens/gen/const_cpp_wide/py/alpha/piketype/constants_types.py
tests/goldens/gen/const_cpp_wide/py/alpha/piketype/__init__.py
tests/goldens/gen/const_cpp_wide/py/alpha/__init__.py
tests/goldens/gen/const_cpp_wide/py/__init__.py
tests/goldens/gen/struct_sv_basic/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/enum_basic/py/runtime/piketype_runtime.py
tests/goldens/gen/enum_basic/py/runtime/__init__.py
tests/goldens/gen/const_cpp_wide/sv/alpha/piketype/constants_pkg.sv
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py
tests/goldens/gen/const_cpp_wide/py/runtime/piketype_runtime.py
tests/goldens/gen/struct_signed/py/alpha/piketype/__init__.py
tests/goldens/gen/const_cpp_wide/py/runtime/__init__.py
tests/goldens/gen/struct_signed/py/alpha/__init__.py
tests/goldens/gen/struct_signed/py/__init__.py
tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_pkg.sv
tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_pkg.sv
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv
tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/__init__.py
tests/goldens/gen/struct_sv_basic/py/alpha/__init__.py
tests/goldens/gen/struct_sv_basic/py/__init__.py
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_pkg.sv
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv
tests/goldens/gen/nested_struct_sv_basic/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/struct_wide/py/__init__.py
tests/goldens/gen/const_cpp_wide/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/struct_wide/py/runtime/piketype_runtime.py
tests/goldens/gen/struct_wide/py/runtime/__init__.py
tests/goldens/gen/enum_basic/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/struct_sv_basic/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/struct_sv_basic/cpp/runtime/piketype_runtime.hpp
tests/goldens/gen/struct_signed/py/runtime/piketype_runtime.py
tests/goldens/gen/struct_signed/py/runtime/__init__.py
tests/goldens/gen/struct_signed/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/struct_wide/cpp/runtime/piketype_runtime.cpp
tests/goldens/gen/struct_wide/cpp/runtime/piketype_runtime.hpp
tests/goldens/gen/struct_wide/py/alpha/__init__.py
tests/goldens/gen/struct_sv_basic/py/runtime/piketype_runtime.py
tests/goldens/gen/struct_sv_basic/py/runtime/__init__.py
tests/goldens/gen/struct_wide/cpp/alpha/piketype/types_types.hpp
tests/goldens/gen/struct_wide/sv/runtime/piketype_runtime_pkg.sv
tests/goldens/gen/struct_wide/py/alpha/piketype/types_types.py
tests/goldens/gen/struct_wide/py/alpha/piketype/__init__.py
tests/goldens/gen/struct_wide/sv/alpha/piketype/types_pkg.sv
tests/goldens/gen/struct_wide/sv/alpha/piketype/types_test_pkg.sv

codex
The spec is broad and mostly structured, but several claims need checking against packaging and existing tests before I can give a defensible verdict. I’m verifying the current backend/package/test setup now.
exec
/bin/zsh -lc "sed -n '1,260p' pyproject.toml" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pike-type"
version = "0.5.0"
description = "Python-based code generator for FPGA-oriented type definitions"
readme = "docs/rfc-v1.md"
requires-python = ">=3.12"
license = { text = "GPL-3.0-or-later" }
authors = [
  { name = "ezchi" },
]
dependencies = [
  "Jinja2>=3.1",
]

[project.optional-dependencies]
dev = [
  "basedpyright>=1.20.0",
  "pytest>=8.0",
]

[project.scripts]
piketype = "piketype.cli:main"

[tool.setuptools]
package-dir = { "" = "src" }

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.basedpyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
reportMissingTypeStubs = false
reportAny = false
reportExplicitAny = false

exec
/bin/zsh -lc "sed -n '1,220p' src/piketype/backends/common/render.py" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
"""Template rendering helpers."""

exec
/bin/zsh -lc 'wc -l src/piketype/backends/py/emitter.py src/piketype/backends/cpp/emitter.py src/piketype/backends/sv/emitter.py src/piketype/backends/runtime/emitter.py' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
     792 src/piketype/backends/py/emitter.py
    1067 src/piketype/backends/cpp/emitter.py
     949 src/piketype/backends/sv/emitter.py
      75 src/piketype/backends/runtime/emitter.py
    2883 total

exec
/bin/zsh -lc "rg -n \"emit_py|emit_cpp|emit_sv|render_module|Template|Jinja|jinja|idempot|golden|subprocess|piketype gen\" tests src/piketype/backends -g '*.py'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
tests/test_struct_flags_member.py:8:import subprocess
tests/test_struct_flags_member.py:24:    """Run piketype gen on a fixture and return the repo dir."""
tests/test_struct_flags_member.py:31:    subprocess.run(
tests/test_struct_flags_member.py:83:    def test_golden_match(self) -> None:
tests/test_struct_flags_member.py:87:        golden_root = TESTS_DIR / "goldens" / "gen" / "struct_flags_member"
tests/test_struct_flags_member.py:88:        for golden_file in golden_root.rglob("*"):
tests/test_struct_flags_member.py:89:            if golden_file.is_dir():
tests/test_struct_flags_member.py:91:            relative = golden_file.relative_to(golden_root)
tests/test_struct_flags_member.py:94:            expected = golden_file.read_text(encoding="utf-8")
tests/test_struct_flags_member.py:98:    def test_idempotent(self) -> None:
tests/test_struct_flags_member.py:99:        """AC-21: piketype gen is idempotent."""
tests/test_struct_flags_member.py:110:        subprocess.run(
tests/test_struct_flags_member.py:120:            self.assertEqual(expected, actual, f"idempotency failed for {rel}")
src/piketype/backends/cpp/emitter.py:32:def emit_cpp(repo: RepoIR, *, namespace: str | None = None) -> list[Path]:
src/piketype/backends/cpp/emitter.py:42:        output_path.write_text(render_module_hpp(module, namespace=namespace), encoding="utf-8")
src/piketype/backends/cpp/emitter.py:47:def render_module_hpp(module: ModuleIR, *, namespace: str | None = None) -> str:
src/piketype/backends/common/render.py:1:"""Template rendering helpers."""
src/piketype/backends/py/emitter.py:30:def emit_py(repo: RepoIR) -> list[Path]:
src/piketype/backends/py/emitter.py:43:        output_path.write_text(render_module_py(module), encoding="utf-8")
src/piketype/backends/py/emitter.py:48:def render_module_py(module: ModuleIR) -> str:
src/piketype/backends/sv/emitter.py:36:def emit_sv(repo: RepoIR) -> list[Path]:
src/piketype/backends/sv/emitter.py:46:        synth_output_path.write_text(render_module_sv(module), encoding="utf-8")
src/piketype/backends/sv/emitter.py:54:            test_output_path.write_text(render_module_test_sv(module), encoding="utf-8")
src/piketype/backends/sv/emitter.py:64:def render_module_sv(module: ModuleIR) -> str:
src/piketype/backends/sv/emitter.py:311:def render_module_test_sv(module: ModuleIR) -> str:
tests/test_runtime_bytes.py:7:import subprocess
tests/test_runtime_bytes.py:20:    """Run piketype gen on a fixture and return the gen/py root."""
tests/test_runtime_bytes.py:27:    result = subprocess.run(
tests/test_gen_const_sv.py:9:import subprocess
tests/test_gen_const_sv.py:18:GOLDENS_DIR = TESTS_DIR / "goldens" / "gen"
tests/test_gen_const_sv.py:45:    def run_piketype(self, repo_dir: Path, cli_arg: str, *extra_args: str) -> subprocess.CompletedProcess[str]:
tests/test_gen_const_sv.py:48:        return subprocess.run(
tests/test_gen_const_sv.py:175:    # -- New positive golden tests for byte-aligned padding --
tests/test_struct_enum_member.py:8:import subprocess
tests/test_struct_enum_member.py:37:    """Run piketype gen on a fixture and return the repo dir."""
tests/test_struct_enum_member.py:44:    subprocess.run(
tests/test_struct_enum_member.py:209:    def test_golden_match(self) -> None:
tests/test_struct_enum_member.py:213:        golden_root = TESTS_DIR / "goldens" / "gen" / "struct_enum_member"
tests/test_struct_enum_member.py:214:        for golden_file in golden_root.rglob("*"):
tests/test_struct_enum_member.py:215:            if golden_file.is_dir():
tests/test_struct_enum_member.py:217:            relative = golden_file.relative_to(golden_root)
tests/test_struct_enum_member.py:220:            expected = golden_file.read_text(encoding="utf-8")
tests/test_struct_enum_member.py:224:    def test_idempotent(self) -> None:
tests/test_struct_enum_member.py:225:        """AC-20: piketype gen is idempotent."""
tests/test_struct_enum_member.py:236:        subprocess.run(
tests/test_struct_enum_member.py:246:            self.assertEqual(expected, actual, f"idempotency failed for {rel}")
tests/test_gen_flags.py:7:import subprocess
tests/test_gen_flags.py:27:    """Run piketype gen on a fixture and return the repo dir."""
tests/test_gen_flags.py:34:    subprocess.run(
tests/test_gen_flags.py:190:    def test_generates_flags_golden(self) -> None:
tests/test_gen_flags.py:193:        golden_root = TESTS_DIR / "goldens" / "gen" / "flags_basic"
tests/test_gen_flags.py:194:        for golden_file in golden_root.rglob("*"):
tests/test_gen_flags.py:195:            if golden_file.is_dir():
tests/test_gen_flags.py:197:            relative = golden_file.relative_to(golden_root)
tests/test_gen_flags.py:200:            expected = golden_file.read_text(encoding="utf-8")
tests/test_gen_flags.py:204:    def test_idempotent(self) -> None:
tests/test_gen_flags.py:216:        subprocess.run(
tests/test_gen_flags.py:226:            self.assertEqual(expected, actual, f"idempotency failed for {rel}")
tests/test_struct_multiple_of.py:7:import subprocess
tests/test_struct_multiple_of.py:62:    """Run piketype gen on a fixture and return the gen/py root."""
tests/test_struct_multiple_of.py:69:    subprocess.run(
tests/test_gen_enum.py:1:"""Integration, golden-file, and runtime tests for Enum() DSL type."""
tests/test_gen_enum.py:8:import subprocess
tests/test_gen_enum.py:35:    """Run piketype gen on a fixture and return the repo dir."""
tests/test_gen_enum.py:42:    subprocess.run(
tests/test_gen_enum.py:284:        golden_root = TESTS_DIR / "goldens" / "gen" / "enum_basic"
tests/test_gen_enum.py:285:        for golden_file in golden_root.rglob("*"):
tests/test_gen_enum.py:286:            if golden_file.is_dir():
tests/test_gen_enum.py:288:            relative = golden_file.relative_to(golden_root)
tests/test_gen_enum.py:291:            expected = golden_file.read_text(encoding="utf-8")
tests/test_gen_enum.py:295:    def test_enum_basic_idempotent(self) -> None:
tests/test_gen_enum.py:306:        subprocess.run(
tests/test_gen_enum.py:316:            self.assertEqual(expected, actual, f"idempotency failed for {rel}")

exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md" in /Users/ezchi/Projects/pike-type
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
session id: 019dd78c-acb1-7982-8733-1405de75ada7
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/specification/iter1-gauge-prompt.md
codex
I’ll read the specified prompt first, then inspect only the referenced project context needed to carry it out.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/specification/iter1-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Specification Iteration 1

You are the **Gauge** in a dual-agent Forge-Gauge loop. Your role is to critically review a feature specification produced by the Forge.

## Inputs to Review

1. **Specification under review:** `specs/010-jinja-template-migration/spec.md`
2. **Project Constitution (highest authority):** `.steel/constitution.md`
3. **Repository context:** the current working directory is the `pike-type` project root. You may read any file in the repo if you need to validate a claim made in the spec (e.g., file paths, line counts, existing patterns).

## Review Instructions

Evaluate the specification on these dimensions, with no softening:

1. **Completeness.** Are all sections present (Overview, User Stories, Functional Requirements, Non-Functional Requirements, Acceptance Criteria, Out of Scope, Open Questions)? Does the spec cover the full migration scope claimed by the feature description, including the staged migration order (Python → C++ → SV), view-model boundaries, determinism, and packaging? Are there missing requirements that would make the spec inactionable?

2. **Clarity.** Is each requirement unambiguous and free of weasel words ("appropriate", "reasonable", "as needed")? Could two engineers read it and produce divergent implementations? Are terms like "view model", "template", "skeleton", and "fragment" defined consistently?

3. **Testability.** Can each Acceptance Criterion be verified by a concrete check (running a command, grepping a file, running a test)? Flag ACs that are subjective or only verifiable by human judgment.

4. **Consistency.** Do FR/NFR/AC items contradict each other? Does the Out of Scope list contradict any FR? Do the Open Questions raise issues that should already be answered as FRs?

5. **Feasibility.** Is anything required that cannot be implemented with the project's declared stack (Python ≥ 3.12, Jinja2 ≥ 3.1, basedpyright strict, unittest)? Does the spec assume infrastructure that does not exist (e.g., a benchmarking harness for NFR-1)?

6. **Alignment with the Project Constitution.**
   - Principle 1 (single source of truth) — does the spec preserve it?
   - Principle 2 (immutable boundaries IR → backend) — does the view-model layer respect IR immutability?
   - Principle 3 (deterministic output) — are determinism requirements explicit and enforceable?
   - Principle 4 (correctness over convenience) — does the spec preserve golden-file testing?
   - Principle 5 (template-first generation) — does the spec materially advance this principle?
   - Principle 6 (generated runtime, not handwritten) — does the spec touch the runtime backend? If so, is it consistent with this principle? (Note: spec lists runtime backend as out of scope.)
   - Coding standards (frozen dataclasses, snake_case, no wildcard imports, basedpyright strict) — does the spec require compliance?
   - Project layout — does the proposed `view.py` per backend fit the existing layout convention?
   - Testing standards — is the golden-file primacy preserved?

## Output Format

Produce a review with:

- A short executive summary (2–4 sentences).
- A numbered issue list. Each issue is one item with:
  - A severity tag in ALL CAPS at the start: `BLOCKING`, `WARNING`, or `NOTE`.
    - `BLOCKING` = the spec cannot proceed to clarification without addressing this.
    - `WARNING` = the spec is workable but this issue should be resolved before clarification or carried forward as an open question.
    - `NOTE` = a minor improvement or stylistic suggestion.
  - The specific FR/NFR/AC/OOS/Q identifier (or section name) the issue refers to.
  - A one- or two-sentence description of the problem.
  - A suggested fix (if obvious) or a clarifying question to ask the Forge.
- A final line that reads exactly one of:
  - `VERDICT: APPROVE` — only if there are zero `BLOCKING` issues.
  - `VERDICT: REVISE` — if there is at least one `BLOCKING` issue.

Be strict. The cost of approving a weak spec is paying for it across all downstream stages (clarification, planning, implementation). The cost of revising is one more Forge round. Bias toward `REVISE` when in doubt.

Do not produce any text after the verdict line.

codex
The prompt asks for a strict Gauge review, not code changes. I’m reading the spec and constitution now, then I’ll verify any repo claims that affect the review.
exec
/bin/zsh -lc "sed -n '1,260p' .steel/constitution.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Project Constitution

## Governing Principles

1. **Single source of truth.** Hardware-oriented types are defined once in Python DSL modules. All generated outputs (SystemVerilog, C++, Python) are derived from that single definition.
2. **Immutable boundaries.** The pipeline has four distinct stages (Discovery -> DSL -> IR -> Backends) with frozen, immutable handoff between them. Backends and validators consume only frozen IR, never mutable DSL objects.
3. **Deterministic output.** Generated code must be byte-for-byte reproducible given the same inputs. No timestamps, run-specific metadata, or non-deterministic ordering.
4. **Correctness over convenience.** Strict type checking, explicit validation passes, and golden-file testing guard against silent regressions. If something cannot be validated, it should not be generated.
5. **Template-first generation.** Generated file structure and syntax live in templates wherever practical. Backend code builds typed view models from IR and handles semantic decisions; templates handle presentation only. Inline string building is reserved for trivial fragments or glue.
6. **Generated runtime, not handwritten.** Shared runtime support packages are generated outputs, not manually maintained infrastructure.

## Technology Stack

| Component            | Technology                | Version/Notes                                |
|----------------------|---------------------------|----------------------------------------------|
| Implementation       | Python                    | >= 3.12                                      |
| Package build        | setuptools + wheel        | setuptools >= 69                             |
| Project metadata     | `pyproject.toml`          | PEP 621                                      |
| Template engine      | Jinja2                    | >= 3.1                                      |
| Static type checking | basedpyright              | >= 1.20.0, strict mode                       |
| Test runner          | unittest (stdlib)         | Golden-file / fixture-based integration tests |
| CLI framework        | argparse (stdlib)         | Thin dispatch layer                          |
| License              | GPL-3.0-or-later          |                                              |
| Target outputs       | SystemVerilog, C++20, Python 3.12+ |                                      |

No external runtime dependencies beyond Jinja2. Dev tooling is limited to basedpyright and pytest.

## Coding Standards

### Python

- **`from __future__ import annotations`** in every module.
- **`basedpyright` strict mode** must pass with zero errors. `reportMissingTypeStubs`, `reportAny`, and `reportExplicitAny` are suppressed.
- **Frozen dataclasses** (`@dataclass(frozen=True, slots=True)`) for all IR nodes. Mutable dataclasses with `slots=True` for DSL runtime objects.
- **Naming conventions:**
  - `snake_case` for functions, methods, variables, and module names.
  - `PascalCase` for classes.
  - `UPPER_SNAKE_CASE` for module-level constants.
  - Private helpers prefixed with `_`.
  - DSL type names end with `_t` suffix (e.g., `addr_t`).
  - Generated wrapper class names use `_ct` suffix (e.g., `addr_ct`).
- **No wildcard imports.** All imports are explicit.
- **Pattern matching** (`match`/`case`) preferred for IR node dispatch.
- **Keyword-only arguments** (`*`) for helper functions to enforce clarity at call sites.
- **Type unions** use the `type X = A | B` syntax (Python 3.12+), not `typing.Union`.

### Generated Code

- All generated files carry a machine-readable header comment identifying the source DSL module(s).
- New or changed generated outputs should be backed by Jinja2 templates whenever the output has meaningful structure. This keeps generated formats easy to inspect, tweak, and extend.
- Backend Python must prepare explicit view-model data for templates. It must not hide generated-file layout inside large ad hoc string-building functions.
- SystemVerilog outputs use `_pkg` suffix for synthesizable packages and `_test_pkg` for verification-only packages.
- C++ headers use include guards (`#ifndef`/`#define`/`#endif`), not `#pragma once`.
- Python generated modules include `__init__.py` files for the full package chain.

### Project Layout

```
src/piketype/          -- implementation source
  cli.py             -- thin CLI entry point
  commands/          -- command orchestration (gen, build, test, lint)
  discovery/         -- repo scanning for piketype/ modules
  loader/            -- Python module execution
  dsl/               -- mutable runtime DSL object model
  ir/                -- frozen immutable IR nodes and builders
  validate/          -- explicit validation passes over IR
  backends/          -- code emitters (sv/, py/, cpp/, runtime/, build/, test/, lint/)
  manifest/          -- JSON manifest model and serialization
tests/
  fixtures/          -- input fixture repos
  goldens/gen/       -- expected golden outputs
docs/                -- RFC, product spec, architecture docs
```

## Development Guidelines

### Branching & Commits

- **Branch naming:** `feature/<name>` for feature branches, branching from `develop`.
- **Commit messages:** Conventional Commits format: `<type>(<scope>): <description>`.
  - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `steel`.
  - Scope matches the subsystem: `sv`, `cpp`, `py`, `dsl`, `emitter`, `codegen`, `init`, etc.

### Testing

- **Golden-file integration tests** are the primary correctness mechanism. Each test case:
  1. Copies a fixture repo from `tests/fixtures/<case>/project/` into a temp directory.
  2. Runs `piketype gen` via subprocess.
  3. Compares the full `gen/` output tree byte-for-byte against `tests/goldens/gen/<case>/`.
- **Idempotency tests** verify that running `piketype gen` twice on the same input produces identical output and does not rescan generated files as DSL modules.
- **Negative tests** verify that invalid inputs produce specific error messages and non-zero exit codes.
- Tests use `unittest.TestCase`, not pytest fixtures or parametrize.
- Golden files are committed to the repo and updated explicitly when output format changes.

### Adding a New Type or Feature

1. Define the DSL node in `dsl/`.
2. Add the frozen IR node in `ir/nodes.py`.
3. Add freeze logic in `dsl/freeze.py` and IR builder logic in `ir/builders.py`.
4. Add validation rules in `validate/engine.py`.
5. Add emission in each backend (`sv/emitter.py`, `cpp/emitter.py`, `py/emitter.py`).
6. Create a fixture repo in `tests/fixtures/` and golden output in `tests/goldens/gen/`.
7. Add an integration test case in `tests/test_gen_const_sv.py` (or a new test file for the feature area).

## Constraints

1. **Python >= 3.12 required.** The codebase uses `type` statement aliases, pattern matching, and `X | Y` union syntax that require 3.12+.
2. **No UVM dependency.** Verification helpers in generated SystemVerilog are standalone classes, not UVM components.
3. **Packed types only.** All generated SystemVerilog types must be packed (`typedef struct packed`). Unpacked types are out of scope for v1.
4. **No cross-module type references (current milestone).** Struct fields referencing types from other modules are rejected by validation. This constraint will be relaxed in a future milestone.
5. **Constant widths restricted to 32/64 bits.** Arbitrary-width constants are not supported; the validation layer rejects other widths.
6. **Minimal runtime dependencies.** Only Jinja2 at runtime. No heavy frameworks, no network dependencies.
7. **Stable, reproducible output.** Ordering is by dependency-first then declaration order. No randomness or environment-dependent output.

exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Specification — Jinja Template Migration for Code Emitters

**Spec ID:** 010-jinja-template-migration
**Branch:** feature/010-jinja-template-migration
**Stage:** specification

---

## Overview

The Python, C++, and SystemVerilog backend emitters in `src/piketype/backends/{py,cpp,sv}/emitter.py` are currently single-file inline string-builders. Each file is 700–1100 lines (py: 792, cpp: 1067, sv: 949) and intermixes IR interpretation, formatting decisions, indentation, target-language syntax, helper-method bodies, and special cases. Auditing or extending any backend requires reading long Python functions whose output shape is implicit.

This feature migrates code generation to a Jinja2-based architecture in which:

- **Python prepares typed view models** from frozen IR. View models contain only computed primitive values (names, widths, byte counts, masks, signed/unsigned flags, helper-fragment strings, import lists). Semantic decisions stay in Python.
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

## Functional Requirements

### Architecture

- **FR-1.** A new module layer SHALL exist for view models. Each backend (`py`, `cpp`, `sv`) SHALL expose typed, frozen dataclasses representing the data needed to render its output files. Naming convention: `backends/<lang>/view.py` with `@dataclass(frozen=True, slots=True)` view-model classes.
- **FR-2.** Each backend SHALL expose one Jinja2 environment scoped to its `templates/` directory using a `FileSystemLoader` rooted at `backends/<lang>/templates/`. Environment options SHALL include `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True`, `undefined=jinja2.StrictUndefined`, and `autoescape=False`. Environments SHALL be constructed once per `emit_<lang>` call (not module-global) to keep emitter state local and testable.
- **FR-3.** A shared module `backends/common/render.py` SHALL provide:
  - A helper to construct a Jinja2 `Environment` for a given backend's template directory using the options in FR-2.
  - A helper to render a template and return a `str` whose final character is `"\n"` (consistent with current emitter contracts).

codex
Executive summary: The spec has the right major sections and aligns with the constitution’s template-first direction, but it is not internally consistent enough to approve. The main failures are packaging/loader ambiguity, staged acceptance ambiguity, and unresolved view-model shape rules that directly affect implementation.

1. BLOCKING — FR-2, FR-14, AC-7, Q-1. The loader strategy is contradictory: FR-2 mandates `FileSystemLoader`, Q-1 recommends `PackageLoader`, and AC-7 requires installed-wheel behavior from outside the repo. Pick one production loading strategy and update FR-2/FR-3/FR-14/AC-7; do not leave this as an open question.

2. BLOCKING — FR-5, AC-1 through AC-8. The migration is explicitly staged per backend, but the acceptance criteria mix per-backend gates with final all-backend gates. Split ACs into “per backend migration complete” and “full feature complete” checks so a Python-only migration can be reviewed without pretending C++/SV are already done.

3. BLOCKING — FR-8, FR-9, AC-4, Q-3. The view-model boundary is still unresolved: FR-8 allows nested view-model dataclasses and `frozenset`, AC-4 says primitive fields only, and Q-3 asks whether nested models are allowed at all. Decide flat versus nested now, and make AC-4 match the chosen rule.

4. WARNING — FR-12, FR-14. `templates/*.j2` does not package nested templates, but FR-12 leaves directory layout at the author’s discretion. Either require flat template directories or use a recursive package-data rule such as `templates/**/*.j2`.

5. WARNING — NFR-1. The performance requirement is not testable: “largest existing fixture” is unnamed, no command is specified, and no baseline recording mechanism exists. Name the fixture, command, measurement method, and required artifact.

6. WARNING — FR-10, FR-11, AC-9. The “grep audit” cannot reliably enforce “no semantics in templates”; terms like “arithmetic on byte counts” and “IR-node attribute access beyond simple `.field` reads” are not concrete grep checks. Add exact prohibited patterns plus a small lint/check script, or admit this requires human review.

7. WARNING — NFR-5, FR-11. NFR-5 says a construct must be found in a single template file, while FR-11 permits macros, includes, inheritance, and blocks. Define acceptable indirection, or NFR-5 contradicts the allowed template architecture.

8. WARNING — FR-18. View-model tests require a “representative fixture IR” but do not name fixtures, expected coverage, or test locations. Specify at least one required fixture per backend and the concrete test file pattern.

9. NOTE — Q-5, OOS-2. Runtime migration is already out of scope by OOS-2, so Q-5 is stale. Remove it or rewrite it as a future follow-up note.

10. NOTE — FR-6. “Meaningful template structure” and “trivial one-liners” are subjective. Add examples of fragments that may remain inline versus constructs that must move to templates.

VERDICT: REVISE
2026-04-29T04:45:21.290639Z ERROR codex_core::session: failed to record rollout items: thread 019dd78c-acb1-7982-8733-1405de75ada7 not found
tokens used
51,115
Executive summary: The spec has the right major sections and aligns with the constitution’s template-first direction, but it is not internally consistent enough to approve. The main failures are packaging/loader ambiguity, staged acceptance ambiguity, and unresolved view-model shape rules that directly affect implementation.

1. BLOCKING — FR-2, FR-14, AC-7, Q-1. The loader strategy is contradictory: FR-2 mandates `FileSystemLoader`, Q-1 recommends `PackageLoader`, and AC-7 requires installed-wheel behavior from outside the repo. Pick one production loading strategy and update FR-2/FR-3/FR-14/AC-7; do not leave this as an open question.

2. BLOCKING — FR-5, AC-1 through AC-8. The migration is explicitly staged per backend, but the acceptance criteria mix per-backend gates with final all-backend gates. Split ACs into “per backend migration complete” and “full feature complete” checks so a Python-only migration can be reviewed without pretending C++/SV are already done.

3. BLOCKING — FR-8, FR-9, AC-4, Q-3. The view-model boundary is still unresolved: FR-8 allows nested view-model dataclasses and `frozenset`, AC-4 says primitive fields only, and Q-3 asks whether nested models are allowed at all. Decide flat versus nested now, and make AC-4 match the chosen rule.

4. WARNING — FR-12, FR-14. `templates/*.j2` does not package nested templates, but FR-12 leaves directory layout at the author’s discretion. Either require flat template directories or use a recursive package-data rule such as `templates/**/*.j2`.

5. WARNING — NFR-1. The performance requirement is not testable: “largest existing fixture” is unnamed, no command is specified, and no baseline recording mechanism exists. Name the fixture, command, measurement method, and required artifact.

6. WARNING — FR-10, FR-11, AC-9. The “grep audit” cannot reliably enforce “no semantics in templates”; terms like “arithmetic on byte counts” and “IR-node attribute access beyond simple `.field` reads” are not concrete grep checks. Add exact prohibited patterns plus a small lint/check script, or admit this requires human review.

7. WARNING — NFR-5, FR-11. NFR-5 says a construct must be found in a single template file, while FR-11 permits macros, includes, inheritance, and blocks. Define acceptable indirection, or NFR-5 contradicts the allowed template architecture.

8. WARNING — FR-18. View-model tests require a “representative fixture IR” but do not name fixtures, expected coverage, or test locations. Specify at least one required fixture per backend and the concrete test file pattern.

9. NOTE — Q-5, OOS-2. Runtime migration is already out of scope by OOS-2, so Q-5 is stale. Remove it or rewrite it as a future follow-up note.

10. NOTE — FR-6. “Meaningful template structure” and “trivial one-liners” are subjective. Add examples of fragments that may remain inline versus constructs that must move to templates.

VERDICT: REVISE
