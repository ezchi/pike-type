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
