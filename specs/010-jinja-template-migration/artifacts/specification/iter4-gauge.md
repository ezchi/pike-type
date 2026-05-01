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
session id: 019dd8ad-0999-78d3-b899-38a823a3daba
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/specification/iter4-gauge-prompt.md
codex
I’ll read the referenced prompt first, then I’ll follow the workflow it specifies rather than guessing at the intended stage.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/specification/iter4-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Specification Iteration 4

You are the **Gauge** in a dual-agent Forge-Gauge loop.

This is **iteration 4**. Iteration 3 returned `VERDICT: REVISE` with these issues:

1. BLOCKING — AC-F5 wheel-filename glob: spec used `piketype-*.whl` but the project name is `pike-type`, which `setuptools` normalizes to `pike_type-*.whl` in the wheel filename.
2. WARNING — FR-21 pattern 2 only matches `byte_count` arithmetic when `byte_count` is on the left side of the operator; it must be symmetric to also catch e.g. `2 * byte_count`.

Both fixes were stated to be surgical edits. No other content was changed in iter4.

## Inputs to Review

1. **Specification under review:** `specs/010-jinja-template-migration/spec.md` (iteration 4).
2. **Iteration-3 review for context:** `specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md`.

## Review Instructions

1. Confirm only the two iter3 issues were touched. If anything else was modified or regressed, flag it. (You may diff iter3-forge against iter4-forge in the artifacts directory.)
2. Confirm AC-F5 now uses the correct wheel filename pattern (`pike_type-*.whl`) and that the surrounding sentence is consistent.
3. Confirm FR-21 pattern 2 is now symmetric (either `byte_count` on the left or on the right of an arithmetic operator).
4. Reconfirm that no new BLOCKING issue exists and that the spec is approvable.

Apply the same severity scheme: `BLOCKING`, `WARNING`, `NOTE`. End with exactly one of `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after the verdict line.

If the only outstanding items are existing Open Questions Q-1..Q-4 (which are properly framed and will be addressed in clarification), APPROVE.

codex
The prompt is a Gauge review for spec iteration 4. I’m checking the referenced spec, prior review, and iteration artifact diff so the verdict is based on the exact files.
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

## Open Questions

- **[NEEDS CLARIFICATION Q-1]** Backend migration commit/PR granularity: should each backend's migration land as a single commit (squashed) on `feature/010-jinja-template-migration`, or as multiple commits per backend (one per FR-6 sub-step)? Both satisfy NFR-6 (contiguous reverts). **Recommendation:** multiple commits per backend, contiguous; squash on merge if project policy requires. Confirm.
- **[NEEDS CLARIFICATION Q-2]** Custom Jinja filters: should the project define any custom filters up front (e.g., `to_hex`, `comment_block`, `c_string_escape`), or only add them as concrete need arises? **Recommendation:** add on demand during migration; document each in `docs/templates.md`; never add a filter that performs IR traversal or non-deterministic computation. Confirm.
- **[NEEDS CLARIFICATION Q-3]** Template hot-reload during development: `PackageLoader` does not pick up template edits in editable installs (`pip install -e .`) without a re-import in some setups. Is this acceptable, or should developer ergonomics warrant a `PIKETYPE_TEMPLATE_DEV=1` environment-variable escape that switches to `FileSystemLoader` for local iteration? **Recommendation:** accept the small ergonomic cost; rely on `pip install -e .` and Python's standard import semantics. Confirm.
- **[NEEDS CLARIFICATION Q-4]** Pre-migration baseline capture: NFR-1 requires capturing `baseline_ms` on `develop`. Should this baseline be captured and committed to `perf.md` at the start of the implementation stage (before the first backend migration), or computed on demand from a tagged commit (`steel/010/baseline`)? **Recommendation:** capture on the first implementation commit, store in `perf.md`, do not rely on tagged-commit replay. Confirm.

exec
/bin/zsh -lc "sed -n '1,220p' specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md" in /Users/ezchi/Projects/pike-type
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
session id: 019dd8a9-00da-70b2-8281-197f9a8486a4
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/specification/iter3-gauge-prompt.md
codex
I’ll read the prompt first, then inspect the referenced artifacts before acting.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/specification/iter3-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Specification Iteration 3

You are the **Gauge** in a dual-agent Forge-Gauge loop.

This is **iteration 3**. Iteration 2 returned `VERDICT: REVISE` with these issues:

1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
2. BLOCKING — FR-21/AC-F7: lint patterns false-positived on legitimate target-language text inside templates (e.g., SystemVerilog `padded[WIDTH-1:0]`, C++ `BYTE_COUNT * 8`). Patterns must scan only Jinja-block contents.
3. WARNING — FR-8/FR-9/FR-15: `frozenset` was discouraged in one place and recommended in another. Pick one rule.
4. WARNING — FR-18/Q-3: location of view-model construction (in `view.py` vs. a separate `builder.py`) was still an open question. Decide now.

## Inputs to Review

1. **Specification under review:** `specs/010-jinja-template-migration/spec.md` (iteration 3).
2. **Project Constitution:** `.steel/constitution.md`.
3. **Iteration-2 review for context:** `specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md`.

## Review Instructions

This is a delta review. For each iter2 issue (1–4), state whether it is **resolved**, **partially resolved**, or **not resolved**, citing the iter3 FR/NFR/AC identifier.

Then check for new issues introduced by the revision:

- **FR-9 forbids `frozenset`**: does any other section (FR-8, FR-15, FR-18, NFR-3) still permit it?
- **FR-21 Jinja-block scoping**: are the patterns themselves correct? Do they catch what they claim to catch when applied to the contents of `{{ ... }}` and `{% ... %}` only? Could pattern 5 (`[-+*/]\s*8\b|\b8\s*[-+*/]`) over-trigger on benign Jinja expressions like `{{ field.byte_count }}` (no, that has no 8) or `{{ width // 8 }}` (yes, that should be caught)? Is the design correct that `// 8` byte-conversion in a Jinja block IS forbidden? Confirm or flag.
- **NFR-1 / `tools/perf_bench.py`**: does the proposed bench helper actually work given that `run_gen` may write `gen/` artifacts under the input file's repo root? The spec says it copies to a temp dir; verify the spec describes a working flow.
- **FR-18 single-file rule**: does this conflict with the constitution's project-layout convention or coding standards?
- **AC-F5 wheel install**: is the proposed sequence (`pip wheel . -w /tmp/pike_wheel/`, then `pip install`, then `piketype gen <tmp-copy>/alpha/piketype/types.py`) executable as written? Are any pieces still wrong?
- **Open Questions Q-1..Q-4**: are any of them now answerable as FRs (i.e., the spec is implicitly committing to one answer already)?

Apply the same severity scheme: `BLOCKING`, `WARNING`, `NOTE`. End with exactly one of `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after the verdict line.

Bias toward APPROVE only if iter2's blockers are genuinely fixed and no new blocker has been introduced. Open Questions that are properly framed as questions (not hidden contradictions) are acceptable for an APPROVE verdict — they will be resolved in the clarification stage.

codex
This is a Gauge review, so I’m going to treat it as a spec review rather than implementation. I’m reading the spec, constitution, and previous review now, then I’ll check the requested deltas and new contradictions.
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' .steel/constitution.md" in /Users/ezchi/Projects/pike-type
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
session id: 019dd8a4-ca9b-7471-9913-61cc661825ea
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/specification/iter2-gauge-prompt.md
codex
I’ll read the referenced prompt first, then I’ll execute whatever workflow it defines from the repo context.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/specification/iter2-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Specification Iteration 2

You are the **Gauge** in a dual-agent Forge-Gauge loop. Your role is to critically review a feature specification produced by the Forge.

This is **iteration 2**. Your iteration-1 review (`specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md`) returned `VERDICT: REVISE` with the following issues:

1. BLOCKING — loader strategy ambiguity (FR-2/14/AC-7/Q-1).
2. BLOCKING — staged-vs-final acceptance criteria not separated (FR-5/AC-1..8).
3. BLOCKING — view-model shape unresolved (FR-8/9/AC-4/Q-3).
4. WARNING — `templates/*.j2` glob does not include nested templates (FR-12/14).
5. WARNING — NFR-1 perf claim untestable (no fixture, no command, no baseline mechanism).
6. WARNING — grep audit (AC-9, FR-10/11) not concrete enough to enforce mechanically.
7. WARNING — NFR-5 vs. FR-11 (single-file rule contradicts allowed indirection).
8. WARNING — FR-18 view-model tests under-specified (no fixtures, no test paths).
9. NOTE — Q-5 stale (runtime is already OOS-2).
10. NOTE — FR-6 "trivial vs. meaningful" subjective without examples.

## Inputs to Review

1. **Specification under review:** `specs/010-jinja-template-migration/spec.md` (iteration 2).
2. **Project Constitution (highest authority):** `.steel/constitution.md`.
3. **Iteration-1 review for context:** `specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md`.

## Review Instructions

1. **Verify each iteration-1 issue is resolved.** For each of the 10 numbered items above, state whether it is resolved, partially resolved, or not resolved, citing the FR/NFR/AC identifier in iter2 that addresses it.

2. **Look for new issues introduced by the revision.** Revisions sometimes break what was working. Specifically check:
   - Internal consistency: does any new FR contradict an existing FR or AC?
   - Testability: is each new requirement (especially FR-21 the lint script and AC-F5 wheel install) verifiable by a concrete check?
   - Constitution alignment: do FR-8, FR-9, FR-11, FR-21, NFR-5 still satisfy constitution Principles 2, 3, 5 and the coding standards?
   - Feasibility: is the lint regex set in FR-21 actually correct (no false positives on legitimate template content)? Does NFR-1's `python -m timeit` invocation form actually work given how `gen_main` is structured?

3. **Apply the same severity scheme as iter1.** `BLOCKING`, `WARNING`, `NOTE`. Bias toward `REVISE` when in doubt.

4. **Be concise.** This is a delta review. Do not re-evaluate sections that did not change. If the spec is now sound, give a short executive summary plus a `VERDICT: APPROVE` line. If issues remain, list them with the same severity tag and end with `VERDICT: REVISE`.

## Output Format

- Executive summary (2–4 sentences).
- Iteration-1 issue resolution table or numbered list (one line per iter1 item: resolved / partial / not resolved + iter2 FR-id).
- New issues (if any), each with severity + identifier + description + suggested fix.
- Final line: exactly `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after the verdict line.

codex
The prompt is a Gauge delta review. I’m loading the spec, constitution, and prior review now, then I’ll check the ten prior findings plus the new revision risks it calls out.
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' .steel/constitution.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
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

exec
/bin/zsh -lc "sed -n '1,220p' /Users/ezchi/Projects/pike-type/.agents/skills/steel-specify/SKILL.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
---
name: steel-specify
description: "Steel-Kit workflow skill: Create a feature specification using the Forge-Gauge dual-agent loop."
---

# steel-specify

Use this skill when the user invokes `/steel-specify` or asks to run the corresponding Steel-Kit workflow step.

Create a feature specification using the Forge-Gauge dual-agent loop.

Feature description: the user-provided input

## Prerequisites
- `.steel/` must exist (run `/steel-init` first)
- `.steel/constitution.md` must contain a real project constitution, not the placeholder template
- `.steel/state.json` currentStage must be `specification`

## Steps

0. Run `/clear` to clear the conversation context before starting this stage.

1. Read `.steel/state.json` and `.steel/config.json`. Verify stage is `specification`.

2. Generate a spec ID:
   - If `--id <value>` was provided, use `<value>-<slugified-description>` as the spec ID (e.g. `--id PROJ-21` + "add auth" → `PROJ-21-add-auth`).
   - Otherwise, auto-increment: count existing directories in `specs/`, increment, and create `specs/NNN-<semantic-name>/` where the name is derived from the user-provided input.

3. Create a git branch using the configured branch prefix (from `.steel/config.json` git settings, default `spec/`). For example: `spec/NNN-<semantic-name>` or `feature/NNN-<semantic-name>` depending on config.

4. Update `.steel/state.json` with `specId`, `branch`, `description`, and set `specification` status to `in_progress`.

5. Read `.steel/constitution.md` for context.

6. **FORGE-GAUGE LOOP** (max iterations from config, default 5):

   ### Forge Phase (you are the Forge)
   a. Generate a comprehensive specification document including:
      - Overview
      - User Stories (As a [role], I want [action], so that [benefit])
      - Functional Requirements (FR-1, FR-2, etc.)
      - Non-Functional Requirements
      - Acceptance Criteria
      - Out of Scope
      - Open Questions (mark with [NEEDS CLARIFICATION])

      **The Project Constitution is the highest authority.** If prior Gauge feedback contradicts the constitution, IGNORE that feedback and follow the constitution. Do not blindly accept all review suggestions.

   b. Write the spec to `specs/NNN-<name>/spec.md`
   c. Save a copy to `specs/<specId>/artifacts/specification/iterN-forge.md`
   d. Git commit: `forge(specification): iteration N output [iteration N]`

   ### Gauge Phase
   e. Read `.steel/config.json` to get the gauge provider.
   f. Call the Gauge LLM to review the spec. **IMPORTANT: Run the command from the project's working directory, NOT /tmp.**
      - Write the full review prompt to a file at `specs/<specId>/artifacts/specification/iterN-gauge-prompt.md`
      - If gauge is `gemini`: run `gemini "Read and follow the instructions in <absolute-path-to-prompt-file>"` in the current project directory
      - If gauge is `codex`: run `codex exec "Read and follow the instructions in <absolute-path-to-prompt-file>"` in the current project directory
      - If gauge is `claude`: You ARE Claude, so review the spec yourself critically as the Gauge role — evaluate completeness, clarity, testability, consistency. Be strict.

      The Gauge review prompt must include these instructions:
      - Review for completeness, clarity, testability, consistency, feasibility
      - Check alignment with the Project Constitution
      - List issues with severity: BLOCKING / WARNING / NOTE
      - End with exactly: `VERDICT: APPROVE` or `VERDICT: REVISE`

   g. Save the review to `specs/<specId>/artifacts/specification/iterN-gauge.md`
   h. Git commit: `gauge(specification): iteration N review — <verdict> [iteration N]`

   i. Parse the verdict: look for `VERDICT: APPROVE` or `VERDICT: REVISE` in the review.

   j. If **APPROVE**: mark stage complete, break the loop.
   k. If **REVISE**: critically evaluate the feedback against the constitution, incorporate valid feedback, and loop back to Forge Phase.

7. **HUMAN APPROVAL GATE** — do not skip this.

   Ask the user: **"Approve specification and advance to clarification?"**

   - If **approved**: update state to `clarification` stage, tag `steel/<specId>/specification-complete`, and go to step 8.
   - If **rejected**: enter **Delta Clarification Mode** (step 7a).

   ### 7a. Delta Clarification Mode

   This mode processes ONLY the user's new feedback without re-running the full Forge-Gauge loop on already-approved content.

   1. **Collect feedback**: Ask the user what specific changes they want. Record their response verbatim as `userFeedback`.

   2. **DELTA FORGE-GAUGE LOOP** (max iterations from config):

      #### Delta Forge Phase
      a. Read the current `specs/<specId>/spec.md`. This is the approved baseline — do NOT regenerate it from scratch.
      b. Address ONLY the items in `userFeedback`. For each feedback item:
         - Identify the specific section(s) of spec.md affected
         - Make targeted edits to those sections only
         - Do NOT rewrite, reorder, or "improve" sections the user did not mention
      c. Save delta to `specs/<specId>/artifacts/specification/iterN-delta-forge.md` with this structure:
         ```markdown
         # Delta Revision — Iteration N

         ## User Feedback
         (verbatim user feedback)

         ## Changes Made
         (for each change: which section, what changed, why)

         ## Sections NOT Modified
         (list sections that were already approved and left untouched)
         ```
      d. Git commit: `forge(specification): delta iteration N [delta N]`

      #### Delta Gauge Phase
      e. The Gauge reviews ONLY the delta — not the entire spec from scratch. Provide the Gauge with:
         - The user's feedback (what was requested)
         - The diff of changes made (before → after for each modified section)
         - The full updated spec.md (for context, but the review focuses on the delta)

         The Gauge MUST check:
         1. Does each change correctly address the corresponding user feedback item?
         2. Were any unrelated sections modified? (If so: REVISE)
         3. Are the changes consistent with the rest of the spec and the constitution?
         4. Is any user feedback item left unaddressed?

         End with `VERDICT: APPROVE` or `VERDICT: REVISE`.

      f. Save review to `specs/<specId>/artifacts/specification/iterN-delta-gauge.md`
      g. Git commit: `gauge(specification): delta iteration N review — <verdict> [delta N]`
      h. If **REVISE**: Forge fixes only the disputed items, loop back to Delta Forge Phase.
      i. If **APPROVE**: exit delta loop.

   3. Return to the approval gate (step 7) — ask the user again: **"Approve specification and advance to clarification?"**
      The user may approve, or reject again with new feedback (re-entering Delta Clarification Mode).

8. **Track skills used**: Update `.steel/state.json` field `skillsUsed.specification` with an array of skill names you invoked during this stage (e.g., `["systemverilog-core", "sv-gen"]`). If no skills were used, set it to `[]`.

9. Show a summary of the specification.


exec
/bin/zsh -lc 'ls -la specs/010-jinja-template-migration/artifacts/specification' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
total 1320
drwxr-xr-x@ 14 ezchi  staff     448 Apr 29 19:58 .
drwxr-xr-x@  3 ezchi  staff      96 Apr 29 14:36 ..
-rw-r--r--@  1 ezchi  staff   17573 Apr 29 14:38 iter1-forge.md
-rw-r--r--@  1 ezchi  staff    4238 Apr 29 14:43 iter1-gauge-prompt.md
-rw-r--r--@  1 ezchi  staff  104625 Apr 29 14:45 iter1-gauge.md
-rw-r--r--@  1 ezchi  staff   25577 Apr 29 19:49 iter2-forge.md
-rw-r--r--@  1 ezchi  staff    3119 Apr 29 19:49 iter2-gauge-prompt.md
-rw-r--r--@  1 ezchi  staff  209108 Apr 29 19:51 iter2-gauge.md
-rw-r--r--@  1 ezchi  staff   27332 Apr 29 19:53 iter3-forge.md
-rw-r--r--@  1 ezchi  staff    3209 Apr 29 19:54 iter3-gauge-prompt.md
-rw-r--r--@  1 ezchi  staff  119183 Apr 29 19:57 iter3-gauge.md
-rw-r--r--@  1 ezchi  staff   27532 Apr 29 19:58 iter4-forge.md
-rw-r--r--@  1 ezchi  staff    1715 Apr 29 19:58 iter4-gauge-prompt.md
-rw-r--r--@  1 ezchi  staff    2722 Apr 29 19:58 iter4-gauge.md

codex
The skill guidance confirms this is the Gauge half of the Steel specification loop, but the prompt has the concrete review contract. I’m now checking the actual iter3-to-iter4 diff so I can verify the “only two surgical edits” claim.
exec
/bin/zsh -lc "cmp -s specs/010-jinja-template-migration/spec.md specs/010-jinja-template-migration/artifacts/specification/iter4-forge.md; printf '%s\\n' "'$?' in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc 'tail -n 120 specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
0

 succeeded in 0ms:
tests/test_struct_flags_member.py:120:            self.assertEqual(expected, actual, f"idempotency failed for {rel}")
tests/test_struct_multiple_of.py:50:    def test_multiple_of_twice(self) -> None:
tests/test_struct_multiple_of.py:62:    """Run piketype gen on a fixture and return the gen/py root."""
tests/test_runtime_bytes.py:20:    """Run piketype gen on a fixture and return the gen/py root."""
tests/test_struct_enum_member.py:37:    """Run piketype gen on a fixture and return the repo dir."""
tests/test_struct_enum_member.py:224:    def test_idempotent(self) -> None:
tests/test_struct_enum_member.py:225:        """AC-20: piketype gen is idempotent."""
tests/test_struct_enum_member.py:246:            self.assertEqual(expected, actual, f"idempotency failed for {rel}")
src/piketype/cli.py:39:                run_gen(args.path, namespace=args.namespace)
src/piketype/commands/gen.py:21:def run_gen(path: str, *, namespace: str | None = None) -> None:

exec
/bin/zsh -lc "sed -n '1,260p' src/piketype/loader/python_loader.py" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
"""Python module loading helpers."""

from __future__ import annotations

from contextlib import contextmanager
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from piketype.discovery.module_name import module_name_from_path
from piketype.errors import PikeTypeError


@contextmanager
def repo_import_path(repo_root: Path):
    """Temporarily add the repo root to ``sys.path``."""
    repo_root_str = str(repo_root)
    already_present = repo_root_str in sys.path
    if not already_present:
        sys.path.insert(0, repo_root_str)
    try:
        yield
    finally:
        if not already_present:
            sys.path.remove(repo_root_str)


def load_module_from_path(path: Path, *, repo_root: Path) -> ModuleType:
    """Load a Python module from a file path using repo-root import semantics."""
    module_name = module_name_from_path(path=path, repo_root=repo_root)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise PikeTypeError(f"could not create import spec for {path}")

    sys.modules.pop(module_name, None)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        with repo_import_path(repo_root):
            spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - exercised via integration path
        sys.modules.pop(module_name, None)
        raise PikeTypeError(f"failed to load module {path}: {exc}") from exc
    return module

codex
One thing is still suspect in AC-F5: the wheel filename glob. I’m checking the package metadata because the distribution name determines whether the written command can actually match the built wheel.
2026-04-29T09:56:33.113843Z ERROR codex_core::tools::router: error=exec_command failed for `/bin/zsh -lc 'rm -rf /tmp/pike_wheel_codex_check && python -m pip wheel . -w /tmp/pike_wheel_codex_check --no-deps && ls -1 /tmp/pike_wheel_codex_check'`: CreateProcess { message: "Rejected(\"`/bin/zsh -lc 'rm -rf /tmp/pike_wheel_codex_check && python -m pip wheel . -w /tmp/pike_wheel_codex_check --no-deps && ls -1 /tmp/pike_wheel_codex_check'` rejected: blocked by policy\")" }
exec
/bin/zsh -lc "rg -n \"pip wheel|piketype-\\*|pike_type|AC-F5|wheel\" specs/010-jinja-template-migration/spec.md pyproject.toml" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
pyproject.toml:2:requires = ["setuptools>=69", "wheel"]
specs/010-jinja-template-migration/spec.md:104:- **FR-14.** Templates SHALL be packaged with the wheel using `setuptools` `package-data`. `pyproject.toml` SHALL include in `[tool.setuptools.package-data]` (or equivalent) the recursive glob `"piketype.backends.py" = ["templates/**/*.j2"]` and analogous entries for `cpp` and `sv`. `MANIFEST.in` SHALL be updated if needed. Loading at runtime is via `PackageLoader` (FR-2), which discovers templates by package import, independent of the filesystem layout outside the wheel.
specs/010-jinja-template-migration/spec.md:200:- **AC-F5.** Wheel packaging: `pip wheel . -w /tmp/pike_wheel/` and inspecting the resulting wheel with `unzip -l /tmp/pike_wheel/piketype-*.whl` shows `*.j2` files present under `piketype/backends/{py,cpp,sv}/templates/` for all three backends. Installing into a clean venv (`pip install /tmp/pike_wheel/piketype-*.whl`) and running `piketype gen <tmp-copy>/alpha/piketype/types.py` against a fresh temp copy of `tests/fixtures/struct_padded/project/` produces identical generated output bytes to running from source on the same fixture copy.

codex
Executive summary: Iteration 3 fixes the iteration-2 blockers about CLI entry points, lint scoping, `frozenset`, and builder placement. It still cannot be approved because AC-F5 contains a concrete wheel filename glob that is wrong for this project.

Iteration-2 issue resolution:

1. Resolved — NFR-1, AC-F4, AC-F5 now use `piketype gen <dsl-file>` and `piketype.commands.gen.run_gen(path, namespace=None)`.
2. Resolved — FR-21 and AC-F7 now scan forbidden patterns only inside Jinja `{{ ... }}` / `{% ... %}` blocks, with raw scanning only for `{% python %}`.
3. Resolved — FR-8, FR-9, FR-15 now consistently forbid `frozenset`; sorted or declaration-order-stable `tuple` is the rule.
4. Resolved — FR-18 decides builders live in `backends/<lang>/view.py`; old builder-location Q-3 is gone.

New issues:

1. BLOCKING — AC-F5. The wheel glob is wrong. `pyproject.toml` declares project name `pike-type`, so the built wheel filename normalizes to `pike_type-*.whl`, not `piketype-*.whl`. `unzip -l /tmp/pike_wheel/piketype-*.whl` and `pip install /tmp/pike_wheel/piketype-*.whl` will not match the built project wheel. Fix AC-F5 to use `pike_type-*.whl` or to discover the generated wheel path programmatically.

2. WARNING — FR-21 pattern 2. `\bbyte_count\b\s*[-+*/]` catches `byte_count * 2` but misses equivalent arithmetic with `byte_count` on the right side, e.g. `2 * byte_count`. If the claim is “arithmetic on `byte_count`,” make the regex symmetric.

Checks with no issue:

- NFR-1 now describes a working temp-copy benchmark flow: `run_gen` resolves the repo root from the temp DSL file and writes `gen/` under that temp repo, not the source fixture.
- FR-21 pattern 5 correctly catches `{{ width // 8 }}` and should catch it; byte conversion in a Jinja block violates FR-10. It does not catch `{{ field.byte_count }}`.
- FR-18’s single-file `view.py` rule does not conflict with the constitution’s project layout or coding standards.
- Q-1 through Q-4 are still acceptable clarification questions, not hidden contradictions.

VERDICT: REVISE
2026-04-29T09:57:38.964568Z ERROR codex_core::session: failed to record rollout items: thread 019dd8a9-00da-70b2-8281-197f9a8486a4 not found
tokens used
61,455
Executive summary: Iteration 3 fixes the iteration-2 blockers about CLI entry points, lint scoping, `frozenset`, and builder placement. It still cannot be approved because AC-F5 contains a concrete wheel filename glob that is wrong for this project.

Iteration-2 issue resolution:

1. Resolved — NFR-1, AC-F4, AC-F5 now use `piketype gen <dsl-file>` and `piketype.commands.gen.run_gen(path, namespace=None)`.
2. Resolved — FR-21 and AC-F7 now scan forbidden patterns only inside Jinja `{{ ... }}` / `{% ... %}` blocks, with raw scanning only for `{% python %}`.
3. Resolved — FR-8, FR-9, FR-15 now consistently forbid `frozenset`; sorted or declaration-order-stable `tuple` is the rule.
4. Resolved — FR-18 decides builders live in `backends/<lang>/view.py`; old builder-location Q-3 is gone.

New issues:

1. BLOCKING — AC-F5. The wheel glob is wrong. `pyproject.toml` declares project name `pike-type`, so the built wheel filename normalizes to `pike_type-*.whl`, not `piketype-*.whl`. `unzip -l /tmp/pike_wheel/piketype-*.whl` and `pip install /tmp/pike_wheel/piketype-*.whl` will not match the built project wheel. Fix AC-F5 to use `pike_type-*.whl` or to discover the generated wheel path programmatically.

2. WARNING — FR-21 pattern 2. `\bbyte_count\b\s*[-+*/]` catches `byte_count * 2` but misses equivalent arithmetic with `byte_count` on the right side, e.g. `2 * byte_count`. If the claim is “arithmetic on `byte_count`,” make the regex symmetric.

Checks with no issue:

- NFR-1 now describes a working temp-copy benchmark flow: `run_gen` resolves the repo root from the temp DSL file and writes `gen/` under that temp repo, not the source fixture.
- FR-21 pattern 5 correctly catches `{{ width // 8 }}` and should catch it; byte conversion in a Jinja block violates FR-10. It does not catch `{{ field.byte_count }}`.
- FR-18’s single-file `view.py` rule does not conflict with the constitution’s project layout or coding standards.
- Q-1 through Q-4 are still acceptable clarification questions, not hidden contradictions.

VERDICT: REVISE

exec
/bin/zsh -lc 'diff -u specs/010-jinja-template-migration/artifacts/specification/iter3-forge.md specs/010-jinja-template-migration/artifacts/specification/iter4-forge.md' in /Users/ezchi/Projects/pike-type
 exited 1 in 0ms:
--- specs/010-jinja-template-migration/artifacts/specification/iter3-forge.md	2026-04-29 19:53:36
+++ specs/010-jinja-template-migration/artifacts/specification/iter4-forge.md	2026-04-29 19:58:14
@@ -125,7 +125,7 @@
 - **FR-21.** A template-hygiene check script SHALL be added at `tools/check_templates.py` and SHALL be runnable as `python tools/check_templates.py [<path>...]`. The script SHALL parse each `.j2` file under `src/piketype/backends/{py,cpp,sv}/templates/**/*.j2` and extract the contents of every Jinja expression block (text inside `{{ ... }}`) and every Jinja statement block (text inside `{% ... %}`). It SHALL fail (non-zero exit) if **any extracted Jinja block** matches **any** of these forbidden patterns (Python `re` regex applied to Jinja-block contents only — never to the surrounding target-language template text):
 
   1. `\(\s*1\s*<<\s*` — bit-shift mask construction.
-  2. `\bbyte_count\b\s*[-+*/]` — arithmetic on `byte_count`.
+  2. `\bbyte_count\b\s*[-+*/]|[-+*/]\s*\bbyte_count\b` — arithmetic on `byte_count` (either operand position).
   3. `\bhasattr\b|\bgetattr\b|\bisinstance\b` — runtime type interrogation.
   4. `\.__class__\b|\btype\s*\(` — type lookup.
   5. `[-+*/]\s*8\b|\b8\s*[-+*/]` — explicit-byte arithmetic in Jinja.
@@ -197,7 +197,7 @@
 - **AC-F2.** `basedpyright --strict src/` reports zero errors.
 - **AC-F3.** `python tools/check_templates.py` exits 0 against the entire `backends/` tree.
 - **AC-F4.** Performance check (NFR-1): `perf.md` exists with `baseline_ms` and `current_ms` recorded by `python tools/perf_bench.py`; `current_ms <= 1.25 * baseline_ms`.
-- **AC-F5.** Wheel packaging: `pip wheel . -w /tmp/pike_wheel/` and inspecting the resulting wheel with `unzip -l /tmp/pike_wheel/piketype-*.whl` shows `*.j2` files present under `piketype/backends/{py,cpp,sv}/templates/` for all three backends. Installing into a clean venv (`pip install /tmp/pike_wheel/piketype-*.whl`) and running `piketype gen <tmp-copy>/alpha/piketype/types.py` against a fresh temp copy of `tests/fixtures/struct_padded/project/` produces identical generated output bytes to running from source on the same fixture copy.
+- **AC-F5.** Wheel packaging: `pip wheel . -w /tmp/pike_wheel/ --no-deps` and inspecting the resulting wheel with `unzip -l /tmp/pike_wheel/pike_type-*.whl` shows `*.j2` files present under `piketype/backends/{py,cpp,sv}/templates/` for all three backends. (The project's distribution name in `pyproject.toml` is `pike-type`, which `setuptools` normalizes to `pike_type` in the wheel filename.) Installing into a clean venv (`pip install /tmp/pike_wheel/pike_type-*.whl`) and running `piketype gen <tmp-copy>/alpha/piketype/types.py` against a fresh temp copy of `tests/fixtures/struct_padded/project/` produces identical generated output bytes to running from source on the same fixture copy.
 - **AC-F6.** `docs/templates.md` exists and covers every item enumerated in FR-22.
 - **AC-F7.** Backend grep audit: `python tools/check_templates.py src/piketype/backends/py/templates src/piketype/backends/cpp/templates src/piketype/backends/sv/templates` exits 0. (Direct `grep -rE` against template files SHALL NOT be used as the audit, because raw target-language text outside Jinja blocks contains legitimate matches for many forbidden patterns; only the script's Jinja-block-scoped scan is authoritative.)
 - **AC-F8.** `git log --oneline develop..HEAD` shows one or more commits per backend (Py first, Cpp second, Sv third) and the per-backend migration commits are contiguous (no interleaving). Reverting any single backend's contiguous commit range leaves the other two backends' migrations intact (verifiable by a dry-run revert).

exec
/bin/zsh -lc "rg -n \"piketype-\\*\\.whl|pike_type-\\*\\.whl|byte_count\\\\b|FR-21|AC-F5\" specs/010-jinja-template-migration/spec.md specs/010-jinja-template-migration/artifacts/specification/iter3-forge.md specs/010-jinja-template-migration/artifacts/specification/iter4-forge.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
specs/010-jinja-template-migration/artifacts/specification/iter4-forge.md:125:- **FR-21.** A template-hygiene check script SHALL be added at `tools/check_templates.py` and SHALL be runnable as `python tools/check_templates.py [<path>...]`. The script SHALL parse each `.j2` file under `src/piketype/backends/{py,cpp,sv}/templates/**/*.j2` and extract the contents of every Jinja expression block (text inside `{{ ... }}`) and every Jinja statement block (text inside `{% ... %}`). It SHALL fail (non-zero exit) if **any extracted Jinja block** matches **any** of these forbidden patterns (Python `re` regex applied to Jinja-block contents only — never to the surrounding target-language template text):
specs/010-jinja-template-migration/artifacts/specification/iter4-forge.md:128:  2. `\bbyte_count\b\s*[-+*/]|[-+*/]\s*\bbyte_count\b` — arithmetic on `byte_count` (either operand position).
specs/010-jinja-template-migration/artifacts/specification/iter4-forge.md:200:- **AC-F5.** Wheel packaging: `pip wheel . -w /tmp/pike_wheel/ --no-deps` and inspecting the resulting wheel with `unzip -l /tmp/pike_wheel/pike_type-*.whl` shows `*.j2` files present under `piketype/backends/{py,cpp,sv}/templates/` for all three backends. (The project's distribution name in `pyproject.toml` is `pike-type`, which `setuptools` normalizes to `pike_type` in the wheel filename.) Installing into a clean venv (`pip install /tmp/pike_wheel/pike_type-*.whl`) and running `piketype gen <tmp-copy>/alpha/piketype/types.py` against a fresh temp copy of `tests/fixtures/struct_padded/project/` produces identical generated output bytes to running from source on the same fixture copy.
specs/010-jinja-template-migration/artifacts/specification/iter3-forge.md:125:- **FR-21.** A template-hygiene check script SHALL be added at `tools/check_templates.py` and SHALL be runnable as `python tools/check_templates.py [<path>...]`. The script SHALL parse each `.j2` file under `src/piketype/backends/{py,cpp,sv}/templates/**/*.j2` and extract the contents of every Jinja expression block (text inside `{{ ... }}`) and every Jinja statement block (text inside `{% ... %}`). It SHALL fail (non-zero exit) if **any extracted Jinja block** matches **any** of these forbidden patterns (Python `re` regex applied to Jinja-block contents only — never to the surrounding target-language template text):
specs/010-jinja-template-migration/artifacts/specification/iter3-forge.md:128:  2. `\bbyte_count\b\s*[-+*/]` — arithmetic on `byte_count`.
specs/010-jinja-template-migration/artifacts/specification/iter3-forge.md:200:- **AC-F5.** Wheel packaging: `pip wheel . -w /tmp/pike_wheel/` and inspecting the resulting wheel with `unzip -l /tmp/pike_wheel/piketype-*.whl` shows `*.j2` files present under `piketype/backends/{py,cpp,sv}/templates/` for all three backends. Installing into a clean venv (`pip install /tmp/pike_wheel/piketype-*.whl`) and running `piketype gen <tmp-copy>/alpha/piketype/types.py` against a fresh temp copy of `tests/fixtures/struct_padded/project/` produces identical generated output bytes to running from source on the same fixture copy.
specs/010-jinja-template-migration/spec.md:125:- **FR-21.** A template-hygiene check script SHALL be added at `tools/check_templates.py` and SHALL be runnable as `python tools/check_templates.py [<path>...]`. The script SHALL parse each `.j2` file under `src/piketype/backends/{py,cpp,sv}/templates/**/*.j2` and extract the contents of every Jinja expression block (text inside `{{ ... }}`) and every Jinja statement block (text inside `{% ... %}`). It SHALL fail (non-zero exit) if **any extracted Jinja block** matches **any** of these forbidden patterns (Python `re` regex applied to Jinja-block contents only — never to the surrounding target-language template text):
specs/010-jinja-template-migration/spec.md:128:  2. `\bbyte_count\b\s*[-+*/]|[-+*/]\s*\bbyte_count\b` — arithmetic on `byte_count` (either operand position).
specs/010-jinja-template-migration/spec.md:200:- **AC-F5.** Wheel packaging: `pip wheel . -w /tmp/pike_wheel/ --no-deps` and inspecting the resulting wheel with `unzip -l /tmp/pike_wheel/pike_type-*.whl` shows `*.j2` files present under `piketype/backends/{py,cpp,sv}/templates/` for all three backends. (The project's distribution name in `pyproject.toml` is `pike-type`, which `setuptools` normalizes to `pike_type` in the wheel filename.) Installing into a clean venv (`pip install /tmp/pike_wheel/pike_type-*.whl`) and running `piketype gen <tmp-copy>/alpha/piketype/types.py` against a fresh temp copy of `tests/fixtures/struct_padded/project/` produces identical generated output bytes to running from source on the same fixture copy.

codex
The diff is limited to two hunks: FR-21 pattern 2 and AC-F5 wheel packaging. I’m doing one last consistency pass on those two revised requirements before issuing the verdict.
exec
/bin/zsh -lc "sed -n '1,180p' specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md" in /Users/ezchi/Projects/pike-type
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
session id: 019dd8ad-0999-78d3-b899-38a823a3daba
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/specification/iter4-gauge-prompt.md
codex
I’ll read the referenced prompt first, then I’ll follow the workflow it specifies rather than guessing at the intended stage.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/specification/iter4-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Specification Iteration 4

You are the **Gauge** in a dual-agent Forge-Gauge loop.

This is **iteration 4**. Iteration 3 returned `VERDICT: REVISE` with these issues:

1. BLOCKING — AC-F5 wheel-filename glob: spec used `piketype-*.whl` but the project name is `pike-type`, which `setuptools` normalizes to `pike_type-*.whl` in the wheel filename.
2. WARNING — FR-21 pattern 2 only matches `byte_count` arithmetic when `byte_count` is on the left side of the operator; it must be symmetric to also catch e.g. `2 * byte_count`.

Both fixes were stated to be surgical edits. No other content was changed in iter4.

## Inputs to Review

1. **Specification under review:** `specs/010-jinja-template-migration/spec.md` (iteration 4).
2. **Iteration-3 review for context:** `specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md`.

## Review Instructions

1. Confirm only the two iter3 issues were touched. If anything else was modified or regressed, flag it. (You may diff iter3-forge against iter4-forge in the artifacts directory.)
2. Confirm AC-F5 now uses the correct wheel filename pattern (`pike_type-*.whl`) and that the surrounding sentence is consistent.
3. Confirm FR-21 pattern 2 is now symmetric (either `byte_count` on the left or on the right of an arithmetic operator).
4. Reconfirm that no new BLOCKING issue exists and that the spec is approvable.

Apply the same severity scheme: `BLOCKING`, `WARNING`, `NOTE`. End with exactly one of `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after the verdict line.

If the only outstanding items are existing Open Questions Q-1..Q-4 (which are properly framed and will be addressed in clarification), APPROVE.

codex
The prompt is a Gauge review for spec iteration 4. I’m checking the referenced spec, prior review, and iteration artifact diff so the verdict is based on the exact files.
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

codex
No findings.

The iter3-to-iter4 diff is limited to the two expected areas: FR-21 pattern 2 and AC-F5 wheel packaging. AC-F5 now consistently uses `pike_type-*.whl` for both `unzip` and `pip install`, with the correct explanation that `pike-type` normalizes to `pike_type` in wheel filenames.

FR-21 pattern 2 is now symmetric: `\bbyte_count\b\s*[-+*/]|[-+*/]\s*\bbyte_count\b` catches arithmetic with `byte_count` on either side of the operator, including cases like `byte_count * 2` and `2 * byte_count`.

The only remaining open items are Q-1 through Q-4, and they are properly framed for clarification. No new BLOCKING issue exists.

VERDICT: APPROVE
2026-04-29T09:59:33.190635Z ERROR codex_core::session: failed to record rollout items: thread 019dd8ad-0999-78d3-b899-38a823a3daba not found
tokens used
29,306
No findings.

The iter3-to-iter4 diff is limited to the two expected areas: FR-21 pattern 2 and AC-F5 wheel packaging. AC-F5 now consistently uses `pike_type-*.whl` for both `unzip` and `pip install`, with the correct explanation that `pike-type` normalizes to `pike_type` in wheel filenames.

FR-21 pattern 2 is now symmetric: `\bbyte_count\b\s*[-+*/]|[-+*/]\s*\bbyte_count\b` catches arithmetic with `byte_count` on either side of the operator, including cases like `byte_count * 2` and `2 * byte_count`.

The only remaining open items are Q-1 through Q-4, and they are properly framed for clarification. No new BLOCKING issue exists.

VERDICT: APPROVE
