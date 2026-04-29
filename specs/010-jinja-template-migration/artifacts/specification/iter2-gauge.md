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
  - `set`, `dict` (use `frozenset`/`tuple` and ordered-pair tuples instead — though `frozenset` is discouraged because its iteration order is hash-dependent; prefer sorted tuples).
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
- **FR-18.** Per-backend view-model unit tests SHALL exist:
  - `tests/test_view_py.py` — exercises `backends/py/view.py` builders against fixture IR derived from `tests/fixtures/struct_padded`, `tests/fixtures/scalar_wide`, and `tests/fixtures/enum_basic`. At minimum, asserts that view-model fields are populated with expected primitive values for each fixture (one assertion per non-trivial field per fixture).
  - `tests/test_view_cpp.py` — analogous, against the same three fixtures plus `tests/fixtures/const_cpp_wide`.
  - `tests/test_view_sv.py` — analogous, against the same three fixtures plus `tests/fixtures/scalar_sv_basic` and `tests/fixtures/nested_struct_sv_basic`.

  These view-model tests are in addition to (not a replacement for) existing golden-file integration tests. They use `unittest.TestCase` (constitution-compliant).

- **FR-19.** When a backend's migration is complete, the inline `render_module_<lang>` function and its `_render_*` helpers in `backends/<lang>/emitter.py` SHALL be removed. The `emit_<lang>` entry point remains and now orchestrates: (1) build view model from IR, (2) construct env, (3) render primary template, (4) write file.
- **FR-20.** If a migration step legitimately needs to change output bytes (e.g., to fix a pre-existing whitespace bug discovered during migration), that change SHALL be made in a separate, single-purpose commit before the corresponding template lands. The template-landing commit SHALL produce byte-identical output to its immediate predecessor commit.
- **FR-21.** A template-hygiene check script SHALL be added at `tools/check_templates.py` and SHALL be runnable as `python tools/check_templates.py`. It SHALL fail (non-zero exit) if any file under `src/piketype/backends/{py,cpp,sv}/templates/**/*.j2` matches **any** of these forbidden patterns (Python `re` regex):
  - `\(\s*1\s*<<\s*` — bit-shift mask construction.
  - `\bbyte_count\b` followed by an arithmetic operator within the same Jinja expression.
  - `\bhasattr\b|\bgetattr\b|\bisinstance\b` — runtime type interrogation.
  - `\.__class__\b|\btype\s*\(` — type lookup.
  - `\bWIDTH\s*[-+*/]` or `\bMASK\s*[-+*/]` — arithmetic on width/mask names.
  - `{%\s*python` or `{{\s*[^}]*\bopen\s*\(` — Python embedding or filesystem access.

  The check script SHALL be invoked as part of the validation stage (this spec's downstream `validation` Steel-Kit stage) and SHALL be documented in `docs/templates.md`.

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

- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. Measurement procedure:
  1. On `develop` (pre-migration), run `python -m timeit -n 5 -r 3 -s "from piketype.commands.gen import gen_main" "gen_main(['--repo', 'tests/fixtures/struct_padded/project'])"` (or equivalent CLI subprocess invocation) and record the median wall-clock time as `baseline_ms`.
  2. On the feature branch after each backend migration completes, repeat the same invocation and record `current_ms`.
  3. Assert `current_ms <= 1.25 * baseline_ms`.

  Both numbers SHALL be recorded in `specs/010-jinja-template-migration/perf.md` (created during validation). If the project's `tests/fixtures/struct_padded` is not the largest fixture at validation time, the validation stage MAY substitute the largest existing fixture and SHALL document the substitution in `perf.md`.

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
- **AC-F4.** Performance check (NFR-1): `perf.md` exists with `baseline_ms` and `current_ms` recorded; `current_ms <= 1.25 * baseline_ms`.
- **AC-F5.** Wheel packaging: `pip wheel . -w /tmp/wheel/` and inspecting the resulting wheel with `unzip -l` shows `templates/*.j2` files present under `piketype/backends/{py,cpp,sv}/templates/` for all three backends. Installing into a clean venv (`pip install /tmp/wheel/piketype-*.whl`) and running `piketype gen` against `tests/fixtures/struct_padded/project` produces identical output to running from source.
- **AC-F6.** `docs/templates.md` exists and covers every item enumerated in FR-22.
- **AC-F7.** Backend grep audit: `grep -rE "(1 << |WIDTH\\s*[-+*/]|MASK\\s*[-+*/]|hasattr|getattr|isinstance|__class__|\\btype\\s*\\()" src/piketype/backends/{py,cpp,sv}/templates/` returns no matches. (This is the human-friendly view of the same patterns enforced by `tools/check_templates.py`.)
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
- **[NEEDS CLARIFICATION Q-3]** View-model construction location: should view-model construction live in `backends/<lang>/view.py` alongside the dataclasses (single file) or in a separate `backends/<lang>/builder.py`? **Recommendation:** single `view.py` for first cut to limit file count; split if a builder grows beyond ~250 lines. Confirm.
- **[NEEDS CLARIFICATION Q-4]** Template hot-reload during development: `PackageLoader` does not pick up template edits in editable installs (`pip install -e .`) without a re-import in some setups. Is this acceptable, or should developer ergonomics warrant a `PIKETYPE_TEMPLATE_DEV=1` environment-variable escape that switches to `FileSystemLoader` for local iteration? **Recommendation:** accept the small ergonomic cost; rely on `pip install -e .` and Python's standard import semantics. Confirm.
- **[NEEDS CLARIFICATION Q-5]** Pre-migration baseline capture: NFR-1 requires capturing `baseline_ms` on `develop`. Should this baseline be captured and committed to `perf.md` at the start of the implementation stage (before the first backend migration), or computed on demand from a tagged commit (`steel/010/baseline`)? **Recommendation:** capture on the first implementation commit, store in `perf.md`, do not rely on tagged-commit replay. Confirm.

codex
The iter2 spec has materially changed from the iteration-1 version. I’m checking the prior review’s actual verdict section now, because that artifact includes more than the final issue list.
exec
/bin/zsh -lc 'tail -n 160 specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
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

exec
/bin/zsh -lc 'rg -n "''^(BLOCKING|WARNING|NOTE|VERDICT)|loader|staged|view-model|templates/'"\\*|NFR-1|grep|NFR-5|FR-18|Q-5|trivial\" specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
34:1. **Completeness.** Are all sections present (Overview, User Stories, Functional Requirements, Non-Functional Requirements, Acceptance Criteria, Out of Scope, Open Questions)? Does the spec cover the full migration scope claimed by the feature description, including the staged migration order (Python → C++ → SV), view-model boundaries, determinism, and packaging? Are there missing requirements that would make the spec inactionable?
38:3. **Testability.** Can each Acceptance Criterion be verified by a concrete check (running a command, grepping a file, running a test)? Flag ACs that are subjective or only verifiable by human judgment.
42:5. **Feasibility.** Is anything required that cannot be implemented with the project's declared stack (Python ≥ 3.12, Jinja2 ≥ 3.1, basedpyright strict, unittest)? Does the spec assume infrastructure that does not exist (e.g., a benchmarking harness for NFR-1)?
46:   - Principle 2 (immutable boundaries IR → backend) — does the view-model layer respect IR immutability?
89:5. **Template-first generation.** Generated file structure and syntax live in templates wherever practical. Backend code builds typed view models from IR and handles semantic decisions; templates handle presentation only. Inline string building is reserved for trivial fragments or glue.
131:- Backend Python must prepare explicit view-model data for templates. It must not hide generated-file layout inside large ad hoc string-building functions.
143:  loader/            -- Python module execution
215:The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.
223:- **US-1.** As a maintainer adding a new generated language construct, I want to edit a focused Jinja template alongside a small view-model addition, so that I can change output structure without re-reading 800-line emitter files.
227:- **US-5.** As a future feature author working on a new backend or backend variant, I want a documented view-model + template pattern to follow, so that new backends start out template-first instead of being reverse-engineered later.
236:- **FR-1.** A new module layer SHALL exist for view models. Each backend (`py`, `cpp`, `sv`) SHALL expose typed, frozen dataclasses representing the data needed to render its output files. Naming convention: `backends/<lang>/view.py` with `@dataclass(frozen=True, slots=True)` view-model classes.
241:- **FR-4.** Each backend SHALL keep its existing public emit entry point (`emit_py`, `emit_cpp`, `emit_sv`) with unchanged signatures and unchanged write locations; only the internal rendering pipeline changes. The IR → view-model → template → string flow SHALL be the only public migration surface.
250:  4. Expression and field-level fragments (only if they have meaningful template structure; trivial one-liners MAY remain inline string concatenations).
257:  - Tuples or `frozenset`s of primitives or other view-model dataclasses.
281:- **FR-14.** Templates SHALL be packaged with the wheel. `pyproject.toml` SHALL include the `templates/*.j2` glob in the `setuptools` package data configuration so that `pip install piketype` ships the templates.
291:- **FR-18.** Unit tests SHALL exist at the view-model layer for each backend, validating the view model produced from a representative fixture IR. View-model tests SHALL be in addition to (not a replacement for) the existing golden-file integration tests.
298:  - The view-model + template architecture.
308:- **NFR-1. Performance.** Wall-clock time for `piketype gen` against the largest existing fixture SHALL NOT regress by more than 25% relative to the pre-migration baseline measured on the same machine. Jinja's caching of compiled templates within a single environment instance SHALL be relied upon to keep render overhead bounded.
312:- **NFR-5. Auditability.** A reviewer SHALL be able to find the rendering of any generated output construct in a single template file, not by tracing across multiple Python helper functions.
323:- **AC-4.** A view-model module `backends/<lang>/view.py` exists for each migrated backend, containing only frozen dataclasses with primitive fields (per FR-8/FR-9).
328:- **AC-9.** Grep audit: no template under `backends/<lang>/templates/` contains arithmetic on byte counts, mask construction (`(1 << ...)`), sign-extension expressions, or IR-node attribute access via Jinja getattr beyond simple `.field` reads on the view-model dataclasses.
338:- **OOS-5.** Performance optimization beyond NFR-1's regression budget.
340:- **OOS-7.** Replacing `backends/common/headers.py` with a templated header. Headers may stay inline string-built; they are trivial fragments and FR-6's last clause permits this.
348:- **[NEEDS CLARIFICATION Q-3]** View-model shape for nested constructs (e.g., struct fields containing references to other types): should the field view model carry a precomputed `type_class_name: str` plus a `width: int` (flat denormalized form), or should it carry a reference to a sibling view-model dataclass (`field_type: ScalarViewModel | EnumViewModel`)? Flat form is simpler for templates; nested form preserves more structure. **Recommendation:** flat denormalized form for first migration (Python backend), revisit if it proves limiting. Confirm.
350:- **[NEEDS CLARIFICATION Q-5]** How should the migration treat `backends/runtime/emitter.py` (the runtime support package generator)? It is currently the only emitter that already has imports of "Template" related symbols (per the earlier grep). Is it in scope as a fourth migration, deferred to a follow-up spec, or considered out of scope per OOS-2? **Recommendation:** explicitly out of scope here (per OOS-2); follow-up spec after the three primary backends land. Confirm.
351:- **[NEEDS CLARIFICATION Q-6]** Should view-model construction live in `backends/<lang>/view.py` (data classes only) with a separate `backends/<lang>/builder.py` (IR → view-model construction), or should `view.py` contain both? **Recommendation:** combine in `view.py` for first cut to limit file count; split if construction logic grows beyond ~200 lines. Confirm.
409:src/piketype/loader/python_loader.py
410:src/piketype/loader/__init__.py
411:src/piketype/loader/module_context.py
1204:1. **Completeness.** Are all sections present (Overview, User Stories, Functional Requirements, Non-Functional Requirements, Acceptance Criteria, Out of Scope, Open Questions)? Does the spec cover the full migration scope claimed by the feature description, including the staged migration order (Python → C++ → SV), view-model boundaries, determinism, and packaging? Are there missing requirements that would make the spec inactionable?
1208:3. **Testability.** Can each Acceptance Criterion be verified by a concrete check (running a command, grepping a file, running a test)? Flag ACs that are subjective or only verifiable by human judgment.
1212:5. **Feasibility.** Is anything required that cannot be implemented with the project's declared stack (Python ≥ 3.12, Jinja2 ≥ 3.1, basedpyright strict, unittest)? Does the spec assume infrastructure that does not exist (e.g., a benchmarking harness for NFR-1)?
1216:   - Principle 2 (immutable boundaries IR → backend) — does the view-model layer respect IR immutability?
1259:5. **Template-first generation.** Generated file structure and syntax live in templates wherever practical. Backend code builds typed view models from IR and handles semantic decisions; templates handle presentation only. Inline string building is reserved for trivial fragments or glue.
1301:- Backend Python must prepare explicit view-model data for templates. It must not hide generated-file layout inside large ad hoc string-building functions.
1313:  loader/            -- Python module execution
1385:The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.
1393:- **US-1.** As a maintainer adding a new generated language construct, I want to edit a focused Jinja template alongside a small view-model addition, so that I can change output structure without re-reading 800-line emitter files.
1397:- **US-5.** As a future feature author working on a new backend or backend variant, I want a documented view-model + template pattern to follow, so that new backends start out template-first instead of being reverse-engineered later.
1406:- **FR-1.** A new module layer SHALL exist for view models. Each backend (`py`, `cpp`, `sv`) SHALL expose typed, frozen dataclasses representing the data needed to render its output files. Naming convention: `backends/<lang>/view.py` with `@dataclass(frozen=True, slots=True)` view-model classes.
1413:Executive summary: The spec has the right major sections and aligns with the constitution’s template-first direction, but it is not internally consistent enough to approve. The main failures are packaging/loader ambiguity, staged acceptance ambiguity, and unresolved view-model shape rules that directly affect implementation.
1415:1. BLOCKING — FR-2, FR-14, AC-7, Q-1. The loader strategy is contradictory: FR-2 mandates `FileSystemLoader`, Q-1 recommends `PackageLoader`, and AC-7 requires installed-wheel behavior from outside the repo. Pick one production loading strategy and update FR-2/FR-3/FR-14/AC-7; do not leave this as an open question.
1417:2. BLOCKING — FR-5, AC-1 through AC-8. The migration is explicitly staged per backend, but the acceptance criteria mix per-backend gates with final all-backend gates. Split ACs into “per backend migration complete” and “full feature complete” checks so a Python-only migration can be reviewed without pretending C++/SV are already done.
1419:3. BLOCKING — FR-8, FR-9, AC-4, Q-3. The view-model boundary is still unresolved: FR-8 allows nested view-model dataclasses and `frozenset`, AC-4 says primitive fields only, and Q-3 asks whether nested models are allowed at all. Decide flat versus nested now, and make AC-4 match the chosen rule.
1421:4. WARNING — FR-12, FR-14. `templates/*.j2` does not package nested templates, but FR-12 leaves directory layout at the author’s discretion. Either require flat template directories or use a recursive package-data rule such as `templates/**/*.j2`.
1423:5. WARNING — NFR-1. The performance requirement is not testable: “largest existing fixture” is unnamed, no command is specified, and no baseline recording mechanism exists. Name the fixture, command, measurement method, and required artifact.
1425:6. WARNING — FR-10, FR-11, AC-9. The “grep audit” cannot reliably enforce “no semantics in templates”; terms like “arithmetic on byte counts” and “IR-node attribute access beyond simple `.field` reads” are not concrete grep checks. Add exact prohibited patterns plus a small lint/check script, or admit this requires human review.
1427:7. WARNING — NFR-5, FR-11. NFR-5 says a construct must be found in a single template file, while FR-11 permits macros, includes, inheritance, and blocks. Define acceptable indirection, or NFR-5 contradicts the allowed template architecture.
1429:8. WARNING — FR-18. View-model tests require a “representative fixture IR” but do not name fixtures, expected coverage, or test locations. Specify at least one required fixture per backend and the concrete test file pattern.
1431:9. NOTE — Q-5, OOS-2. Runtime migration is already out of scope by OOS-2, so Q-5 is stale. Remove it or rewrite it as a future follow-up note.
1433:10. NOTE — FR-6. “Meaningful template structure” and “trivial one-liners” are subjective. Add examples of fragments that may remain inline versus constructs that must move to templates.
1435:VERDICT: REVISE
1439:Executive summary: The spec has the right major sections and aligns with the constitution’s template-first direction, but it is not internally consistent enough to approve. The main failures are packaging/loader ambiguity, staged acceptance ambiguity, and unresolved view-model shape rules that directly affect implementation.
1441:1. BLOCKING — FR-2, FR-14, AC-7, Q-1. The loader strategy is contradictory: FR-2 mandates `FileSystemLoader`, Q-1 recommends `PackageLoader`, and AC-7 requires installed-wheel behavior from outside the repo. Pick one production loading strategy and update FR-2/FR-3/FR-14/AC-7; do not leave this as an open question.
1443:2. BLOCKING — FR-5, AC-1 through AC-8. The migration is explicitly staged per backend, but the acceptance criteria mix per-backend gates with final all-backend gates. Split ACs into “per backend migration complete” and “full feature complete” checks so a Python-only migration can be reviewed without pretending C++/SV are already done.
1445:3. BLOCKING — FR-8, FR-9, AC-4, Q-3. The view-model boundary is still unresolved: FR-8 allows nested view-model dataclasses and `frozenset`, AC-4 says primitive fields only, and Q-3 asks whether nested models are allowed at all. Decide flat versus nested now, and make AC-4 match the chosen rule.
1447:4. WARNING — FR-12, FR-14. `templates/*.j2` does not package nested templates, but FR-12 leaves directory layout at the author’s discretion. Either require flat template directories or use a recursive package-data rule such as `templates/**/*.j2`.
1449:5. WARNING — NFR-1. The performance requirement is not testable: “largest existing fixture” is unnamed, no command is specified, and no baseline recording mechanism exists. Name the fixture, command, measurement method, and required artifact.
1451:6. WARNING — FR-10, FR-11, AC-9. The “grep audit” cannot reliably enforce “no semantics in templates”; terms like “arithmetic on byte counts” and “IR-node attribute access beyond simple `.field` reads” are not concrete grep checks. Add exact prohibited patterns plus a small lint/check script, or admit this requires human review.
1453:7. WARNING — NFR-5, FR-11. NFR-5 says a construct must be found in a single template file, while FR-11 permits macros, includes, inheritance, and blocks. Define acceptable indirection, or NFR-5 contradicts the allowed template architecture.
1455:8. WARNING — FR-18. View-model tests require a “representative fixture IR” but do not name fixtures, expected coverage, or test locations. Specify at least one required fixture per backend and the concrete test file pattern.
1457:9. NOTE — Q-5, OOS-2. Runtime migration is already out of scope by OOS-2, so Q-5 is stale. Remove it or rewrite it as a future follow-up note.
1459:10. NOTE — FR-6. “Meaningful template structure” and “trivial one-liners” are subjective. Add examples of fragments that may remain inline versus constructs that must move to templates.
1461:VERDICT: REVISE

exec
/bin/zsh -lc 'rg -n "def gen_main|def main|struct_padded|PackageLoader|package-data|templates|Jinja2|jinja2" -S src pyproject.toml tests specs/010-jinja-template-migration/spec.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
specs/010-jinja-template-migration/spec.md:13:This feature migrates code generation to a Jinja2-based architecture in which:
specs/010-jinja-template-migration/spec.md:16:- **Jinja2 templates render structure and syntax.** Templates contain whitespace/indentation, target-language keywords, and the iteration/conditional skeleton needed to lay out a file. Templates do not compute padding, resolve type references, decide signedness, or duplicate validation.
specs/010-jinja-template-migration/spec.md:18:The migration is staged: Python backend first, then C++, then SystemVerilog. Each backend's golden tests must continue to pass byte-for-byte after the migration; the migration itself adds no new generated-output features. Jinja2 is already declared as a runtime dependency in `pyproject.toml` and listed as the Template engine in the project constitution; an empty stub `backends/common/render.py` already exists. This feature builds on those foundations.
specs/010-jinja-template-migration/spec.md:20:The migration is positive-value only when semantics stay out of templates. If templates accumulate Python logic, the migration loses its benefit and the spec's success criteria are not met.
specs/010-jinja-template-migration/spec.md:31:- **US-6.** As a maintainer reviewing template-bound code, I want a clear and enforced rule about what may live in templates versus Python, so that templates do not silently accumulate semantic logic over time.
specs/010-jinja-template-migration/spec.md:38:- **Template.** A file under `backends/<lang>/templates/` ending in `.j2`, rendered through a Jinja2 `Environment` configured per FR-2.
specs/010-jinja-template-migration/spec.md:50:- **FR-2.** Each backend SHALL expose one Jinja2 `Environment` constructed via `jinja2.PackageLoader("piketype.backends.<lang>", "templates")`. Environment options SHALL be exactly: `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True`, `undefined=jinja2.StrictUndefined`, `autoescape=False`. The environment SHALL be constructed once per `emit_<lang>` call (not module-global) so that emitter state is local and testable. `FileSystemLoader` SHALL NOT be used for production rendering. (Tests MAY construct ad-hoc environments with `DictLoader` or `FileSystemLoader` for unit testing of templates.)
specs/010-jinja-template-migration/spec.md:52:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
specs/010-jinja-template-migration/spec.md:53:  - `def render(*, env: jinja2.Environment, template_name: str, context: object) -> str` that renders a template and returns a string whose final character is `"\n"` (consistent with current emitter contracts). The `context` SHALL be a view-model dataclass instance; the helper SHALL pass its fields as the template context (via `dataclasses.asdict` or by passing the instance directly with templates accessing `.field` attributes — implementation choice, but uniform across backends).
specs/010-jinja-template-migration/spec.md:65:  **Examples of "meaningful template structure" (MUST move to templates):** the body of a `to_bytes` method, the body of `from_bytes` with conditional sign-handling, the dataclass field block of a Python struct, an enum's member-list block, a SystemVerilog `typedef struct packed { ... }` block, a C++ class scaffold including its packed helpers.
specs/010-jinja-template-migration/spec.md:67:  **Examples of "trivial fragments" (MAY remain inline in Python and be passed as `str` fields):** a single hex literal (`"0xff"`), a numeric expression rendered for a constant (`"(1 << 32) - 1"`), a single-line type alias initializer, a header comment line, an `__all__` tuple body. These fragments SHALL be pre-computed in Python and exposed as `str` fields on the view model; templates SHALL emit them with `{{ fragment }}` and SHALL NOT recompute them.
specs/010-jinja-template-migration/spec.md:96:  - Project-defined custom filters registered on the environment, provided each filter is a pure function over primitives, deterministic, and documented in `docs/templates.md`.
specs/010-jinja-template-migration/spec.md:102:- **FR-12.** Templates SHALL live under `backends/<lang>/templates/`. Subdirectories are permitted. Required convention: each backend SHALL have exactly one **primary template** per generated artifact kind (e.g., `module.j2` for a generated `.py`/`.cpp`/`.sv` source file). Macros and partials live in files prefixed `_` (e.g., `_macros.j2`, `_struct.j2`). Reviewers locate generated output by reading the primary template; partials are an implementation detail.
specs/010-jinja-template-migration/spec.md:104:- **FR-14.** Templates SHALL be packaged with the wheel using `setuptools` `package-data`. `pyproject.toml` SHALL include in `[tool.setuptools.package-data]` (or equivalent) the recursive glob `"piketype.backends.py" = ["templates/**/*.j2"]` and analogous entries for `cpp` and `sv`. `MANIFEST.in` SHALL be updated if needed. Loading at runtime is via `PackageLoader` (FR-2), which discovers templates by package import, independent of the filesystem layout outside the wheel.
specs/010-jinja-template-migration/spec.md:109:- **FR-16.** No template SHALL reference `now()`, environment variables, the filesystem (other than via Jinja includes resolved by `PackageLoader`), random sources, or hash-based ordering. The Jinja environment SHALL NOT register any non-deterministic global. The set of registered globals and filters SHALL be auditable from `backends/common/render.py` alone.
specs/010-jinja-template-migration/spec.md:115:  - `tests/test_view_py.py` — exercises `backends/py/view.py` builders against fixture IR derived from `tests/fixtures/struct_padded`, `tests/fixtures/scalar_wide`, and `tests/fixtures/enum_basic`. At minimum, asserts that view-model fields are populated with expected primitive values for each fixture (one assertion per non-trivial field per fixture).
specs/010-jinja-template-migration/spec.md:123:- **FR-21.** A template-hygiene check script SHALL be added at `tools/check_templates.py` and SHALL be runnable as `python tools/check_templates.py`. It SHALL fail (non-zero exit) if any file under `src/piketype/backends/{py,cpp,sv}/templates/**/*.j2` matches **any** of these forbidden patterns (Python `re` regex):
specs/010-jinja-template-migration/spec.md:131:  The check script SHALL be invoked as part of the validation stage (this spec's downstream `validation` Steel-Kit stage) and SHALL be documented in `docs/templates.md`.
specs/010-jinja-template-migration/spec.md:135:- **FR-22.** A short developer-facing document SHALL be added at `docs/templates.md` covering:
specs/010-jinja-template-migration/spec.md:137:  - The "what may live in templates" rule (cross-referenced from FR-10/FR-11) and the indirection-depth bound from FR-11.
specs/010-jinja-template-migration/spec.md:139:  - The location of templates and view models per backend.
specs/010-jinja-template-migration/spec.md:141:  - How to run the template-hygiene check (`python tools/check_templates.py`) and what it enforces.
specs/010-jinja-template-migration/spec.md:147:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. Measurement procedure:
specs/010-jinja-template-migration/spec.md:148:  1. On `develop` (pre-migration), run `python -m timeit -n 5 -r 3 -s "from piketype.commands.gen import gen_main" "gen_main(['--repo', 'tests/fixtures/struct_padded/project'])"` (or equivalent CLI subprocess invocation) and record the median wall-clock time as `baseline_ms`.
specs/010-jinja-template-migration/spec.md:152:  Both numbers SHALL be recorded in `specs/010-jinja-template-migration/perf.md` (created during validation). If the project's `tests/fixtures/struct_padded` is not the largest fixture at validation time, the validation stage MAY substitute the largest existing fixture and SHALL document the substitution in `perf.md`.
specs/010-jinja-template-migration/spec.md:154:- **NFR-2. Dependency surface.** No new runtime dependency SHALL be introduced. Jinja2 ≥ 3.1 is already declared in `pyproject.toml` and is the only template engine permitted.
specs/010-jinja-template-migration/spec.md:157:- **NFR-5. Auditability.** A reviewer SHALL be able to find the full rendering of any generated output construct by reading the backend's primary template (`module.j2`) plus at most one layer of partial templates referenced by it. The two-level indirection bound in FR-11 enforces this.
specs/010-jinja-template-migration/spec.md:172:- **AC-2-`<lang>`.** `find src/piketype/backends/<lang>/templates -name '*.j2' | wc -l` is at least 1 and `backends/<lang>/emitter.py` calls `render` from `backends/common/render.py` (verifiable by `grep -n "from piketype.backends.common.render import" src/piketype/backends/<lang>/emitter.py`).
specs/010-jinja-template-migration/spec.md:175:- **AC-5-`<lang>`.** `python tools/check_templates.py` exits 0 against `backends/<lang>/templates/`.
specs/010-jinja-template-migration/spec.md:185:- **AC-F3.** `python tools/check_templates.py` exits 0 against the entire `backends/` tree.
specs/010-jinja-template-migration/spec.md:187:- **AC-F5.** Wheel packaging: `pip wheel . -w /tmp/wheel/` and inspecting the resulting wheel with `unzip -l` shows `templates/*.j2` files present under `piketype/backends/{py,cpp,sv}/templates/` for all three backends. Installing into a clean venv (`pip install /tmp/wheel/piketype-*.whl`) and running `piketype gen` against `tests/fixtures/struct_padded/project` produces identical output to running from source.
specs/010-jinja-template-migration/spec.md:188:- **AC-F6.** `docs/templates.md` exists and covers every item enumerated in FR-22.
specs/010-jinja-template-migration/spec.md:189:- **AC-F7.** Backend grep audit: `grep -rE "(1 << |WIDTH\\s*[-+*/]|MASK\\s*[-+*/]|hasattr|getattr|isinstance|__class__|\\btype\\s*\\()" src/piketype/backends/{py,cpp,sv}/templates/` returns no matches. (This is the human-friendly view of the same patterns enforced by `tools/check_templates.py`.)
specs/010-jinja-template-migration/spec.md:202:- **OOS-7.** Replacing `backends/common/headers.py` with a templated header. Headers stay inline string-built and are passed into templates as a `header: str` view-model field (per FR-13).
specs/010-jinja-template-migration/spec.md:209:- **[NEEDS CLARIFICATION Q-2]** Custom Jinja filters: should the project define any custom filters up front (e.g., `to_hex`, `comment_block`, `c_string_escape`), or only add them as concrete need arises? **Recommendation:** add on demand during migration; document each in `docs/templates.md`; never add a filter that performs IR traversal or non-deterministic computation. Confirm.
specs/010-jinja-template-migration/spec.md:211:- **[NEEDS CLARIFICATION Q-4]** Template hot-reload during development: `PackageLoader` does not pick up template edits in editable installs (`pip install -e .`) without a re-import in some setups. Is this acceptable, or should developer ergonomics warrant a `PIKETYPE_TEMPLATE_DEV=1` environment-variable escape that switches to `FileSystemLoader` for local iteration? **Recommendation:** accept the small ergonomic cost; rely on `pip install -e .` and Python's standard import semantics. Confirm.
pyproject.toml:16:  "Jinja2>=3.1",
tests/test_runtime_bytes.py:49:        for fixture_name in ("struct_padded", "struct_signed", "scalar_wide",
tests/test_runtime_bytes.py:72:    def test_struct_padded_to_bytes(self) -> None:
tests/test_runtime_bytes.py:73:        mod = self._import_module("struct_padded")
tests/test_runtime_bytes.py:79:    def test_struct_padded_from_bytes_nonzero_padding(self) -> None:
tests/test_runtime_bytes.py:80:        mod = self._import_module("struct_padded")
tests/test_runtime_bytes.py:91:        mod = self._import_module("struct_padded")
tests/test_gen_const_sv.py:177:    def test_generates_struct_padded(self) -> None:
tests/test_gen_const_sv.py:178:        fixture_root = FIXTURES_DIR / "struct_padded" / "project"
tests/test_gen_const_sv.py:179:        expected_root = GOLDENS_DIR / "struct_padded"
src/piketype/cli.py:31:def main(argv: Sequence[str] | None = None) -> int:

codex
One concrete feasibility problem is already visible: the revised NFR-1 command imports `gen_main`, but the repo search did not find that symbol. I’m reading the CLI/gen modules to confirm whether that is an actual blocker or just a naming mismatch.
exec
/bin/zsh -lc "sed -n '1,220p' pyproject.toml" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,220p' src/piketype/cli.py" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' src/piketype/commands/gen.py" in /Users/ezchi/Projects/pike-type
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

 succeeded in 0ms:
"""Command-line entry point for piketype."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from piketype.commands.build import run_build
from piketype.commands.gen import run_gen
from piketype.commands.lint import run_lint
from piketype.commands.test import run_test
from piketype.errors import PikeTypeError


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level CLI parser."""
    parser = argparse.ArgumentParser(prog="piketype")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("gen")
    gen_parser.add_argument("--namespace", default=None)
    gen_parser.add_argument("path")

    for name in ("build", "test", "lint"):
        command_parser = subparsers.add_parser(name)
        command_parser.add_argument("path")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        match args.command:
            case "gen":
                run_gen(args.path, namespace=args.namespace)
            case "build":
                run_build(args.path)
            case "test":
                run_test(args.path)
            case "lint":
                run_lint(args.path)
            case _:
                parser.error(f"unsupported command: {args.command}")
    except PikeTypeError as exc:
        parser.exit(status=1, message=f"error: {exc}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

 succeeded in 0ms:
"""Generate command."""

from __future__ import annotations

from pathlib import Path

from piketype import __version__
from piketype.backends.cpp.emitter import emit_cpp
from piketype.backends.py.emitter import emit_py
from piketype.backends.runtime.emitter import emit_runtime
from piketype.backends.sv.emitter import emit_sv
from piketype.discovery.scanner import ensure_cli_path_is_valid, find_piketype_modules
from piketype.dsl.freeze import build_const_definition_map, build_loaded_module, build_type_definition_map, freeze_module, freeze_repo
from piketype.loader.python_loader import load_module_from_path
from piketype.manifest.write_json import write_manifest
from piketype.repo import find_repo_root
from piketype.validate.engine import validate_repo
from piketype.validate.namespace import check_duplicate_basenames, validate_cpp_namespace


def run_gen(path: str, *, namespace: str | None = None) -> None:
    """Run generation orchestration."""
    if namespace is not None:
        validate_cpp_namespace(namespace)

    cli_path = Path(path).resolve()
    ensure_cli_path_is_valid(cli_path)
    repo_root = find_repo_root(cli_path)
    module_paths = find_piketype_modules(repo_root)

    if namespace is not None:
        check_duplicate_basenames(module_paths=module_paths)

    loaded_modules = [
        build_loaded_module(
            module=load_module_from_path(module_path, repo_root=repo_root),
            module_path=module_path,
            repo_root=repo_root,
        )
        for module_path in module_paths
    ]
    definition_map = build_const_definition_map(loaded_modules=loaded_modules)
    type_definition_map = build_type_definition_map(loaded_modules=loaded_modules)

    frozen_modules = []
    cli_module_had_local_definitions = False
    for loaded_module in loaded_modules:
        frozen_module = freeze_module(
            loaded_module=loaded_module,
            definition_map=definition_map,
            type_definition_map=type_definition_map,
        )
        if loaded_module.module_path == cli_path and frozen_module.has_local_definitions:
            cli_module_had_local_definitions = True
        frozen_modules.append(frozen_module)

    repo = freeze_repo(repo_root=repo_root, frozen_modules=frozen_modules, tool_version=__version__)
    validate_repo(repo)
    if not cli_module_had_local_definitions:
        from piketype.errors import ValidationError

        raise ValidationError(f"{cli_path}: piketype file defines no DSL objects")

    emit_sv(repo)
    emit_py(repo)
    emit_cpp(repo, namespace=namespace)
    emit_runtime(repo)
    write_manifest(repo)

exec
/bin/zsh -lc "find tests/fixtures -maxdepth 2 -type d | sort | sed -n '1,120p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
tests/fixtures
tests/fixtures/const_collision
tests/fixtures/const_collision/project
tests/fixtures/const_cpp_explicit_uint32
tests/fixtures/const_cpp_explicit_uint32/project
tests/fixtures/const_cpp_wide
tests/fixtures/const_cpp_wide/project
tests/fixtures/const_expr_basic
tests/fixtures/const_expr_basic/project
tests/fixtures/const_sv_basic
tests/fixtures/const_sv_basic/project
tests/fixtures/enum_basic
tests/fixtures/enum_basic/project
tests/fixtures/flags_basic
tests/fixtures/flags_basic/project
tests/fixtures/namespace_override
tests/fixtures/namespace_override/project
tests/fixtures/nested_struct_sv_basic
tests/fixtures/nested_struct_sv_basic/project
tests/fixtures/no_dsl
tests/fixtures/no_dsl/project
tests/fixtures/outside_piketype
tests/fixtures/outside_piketype/project
tests/fixtures/scalar_signed_wide
tests/fixtures/scalar_signed_wide/project
tests/fixtures/scalar_sv_basic
tests/fixtures/scalar_sv_basic/project
tests/fixtures/scalar_wide
tests/fixtures/scalar_wide/project
tests/fixtures/struct_enum_member
tests/fixtures/struct_enum_member/project
tests/fixtures/struct_flags_member
tests/fixtures/struct_flags_member/project
tests/fixtures/struct_multiple_of
tests/fixtures/struct_multiple_of/project
tests/fixtures/struct_pad_collision
tests/fixtures/struct_pad_collision/project
tests/fixtures/struct_padded
tests/fixtures/struct_padded/project
tests/fixtures/struct_signed
tests/fixtures/struct_signed/project
tests/fixtures/struct_sv_basic
tests/fixtures/struct_sv_basic/project
tests/fixtures/struct_wide
tests/fixtures/struct_wide/project

codex
The NFR-1 command is not aligned with the current CLI: the project has `run_gen(path, ...)` and `piketype gen <path>`, not `gen_main(['--repo', ...])`. I’m doing one more targeted search against existing generated output to judge whether the proposed template lint patterns would reject legitimate template text.
exec
/bin/zsh -lc 'wc -l src/piketype/backends/py/emitter.py src/piketype/backends/cpp/emitter.py src/piketype/backends/sv/emitter.py' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
     792 src/piketype/backends/py/emitter.py
    1067 src/piketype/backends/cpp/emitter.py
     949 src/piketype/backends/sv/emitter.py
    2808 total

exec
/bin/zsh -lc "find src/piketype/backends -maxdepth 3 -type f | sort | sed -n '1,160p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
src/piketype/backends/__init__.py
src/piketype/backends/__pycache__/__init__.cpython-313.pyc
src/piketype/backends/__pycache__/__init__.cpython-314.pyc
src/piketype/backends/__pycache__/registry.cpython-314.pyc
src/piketype/backends/build/__init__.py
src/piketype/backends/build/__pycache__/__init__.cpython-314.pyc
src/piketype/backends/build/__pycache__/emitter.cpython-314.pyc
src/piketype/backends/build/emitter.py
src/piketype/backends/build/templates/.gitkeep
src/piketype/backends/common/__init__.py
src/piketype/backends/common/__pycache__/__init__.cpython-313.pyc
src/piketype/backends/common/__pycache__/__init__.cpython-314.pyc
src/piketype/backends/common/__pycache__/headers.cpython-313.pyc
src/piketype/backends/common/__pycache__/headers.cpython-314.pyc
src/piketype/backends/common/__pycache__/ordering.cpython-314.pyc
src/piketype/backends/common/__pycache__/render.cpython-314.pyc
src/piketype/backends/common/headers.py
src/piketype/backends/common/ordering.py
src/piketype/backends/common/render.py
src/piketype/backends/cpp/__init__.py
src/piketype/backends/cpp/__pycache__/__init__.cpython-313.pyc
src/piketype/backends/cpp/__pycache__/__init__.cpython-314.pyc
src/piketype/backends/cpp/__pycache__/emitter.cpython-313.pyc
src/piketype/backends/cpp/__pycache__/emitter.cpython-314.pyc
src/piketype/backends/cpp/emitter.py
src/piketype/backends/cpp/templates/.gitkeep
src/piketype/backends/lint/__init__.py
src/piketype/backends/lint/__pycache__/__init__.cpython-314.pyc
src/piketype/backends/lint/__pycache__/emitter.cpython-314.pyc
src/piketype/backends/lint/emitter.py
src/piketype/backends/lint/templates/.gitkeep
src/piketype/backends/py/__init__.py
src/piketype/backends/py/__pycache__/__init__.cpython-313.pyc
src/piketype/backends/py/__pycache__/__init__.cpython-314.pyc
src/piketype/backends/py/__pycache__/emitter.cpython-313.pyc
src/piketype/backends/py/__pycache__/emitter.cpython-314.pyc
src/piketype/backends/py/emitter.py
src/piketype/backends/py/templates/.gitkeep
src/piketype/backends/registry.py
src/piketype/backends/runtime/__init__.py
src/piketype/backends/runtime/__pycache__/__init__.cpython-313.pyc
src/piketype/backends/runtime/__pycache__/__init__.cpython-314.pyc
src/piketype/backends/runtime/__pycache__/emitter.cpython-313.pyc
src/piketype/backends/runtime/__pycache__/emitter.cpython-314.pyc
src/piketype/backends/runtime/emitter.py
src/piketype/backends/runtime/templates/.gitkeep
src/piketype/backends/sv/__init__.py
src/piketype/backends/sv/__pycache__/__init__.cpython-313.pyc
src/piketype/backends/sv/__pycache__/__init__.cpython-314.pyc
src/piketype/backends/sv/__pycache__/emitter.cpython-313.pyc
src/piketype/backends/sv/__pycache__/emitter.cpython-314.pyc
src/piketype/backends/sv/emitter.py
src/piketype/backends/sv/templates/.gitkeep
src/piketype/backends/test/__init__.py
src/piketype/backends/test/__pycache__/__init__.cpython-314.pyc
src/piketype/backends/test/__pycache__/emitter.cpython-314.pyc
src/piketype/backends/test/emitter.py
src/piketype/backends/test/templates/.gitkeep

exec
/bin/zsh -lc "rg -n \"\\bWIDTH\\b|\\bMASK\\b|byte_count|1 <<|hasattr|getattr|isinstance|__class__|\\btype\\s*\\(\" tests/goldens src/piketype/backends/{py,cpp,sv}" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
src/piketype/backends/py/emitter.py:25:    byte_count,
src/piketype/backends/py/emitter.py:53:    has_structs = any(isinstance(type_ir, StructIR) for type_ir in module.types)
src/piketype/backends/py/emitter.py:54:    has_enums = any(isinstance(type_ir, EnumIR) for type_ir in module.types)
src/piketype/backends/py/emitter.py:71:        if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/py/emitter.py:73:        elif isinstance(type_ir, StructIR):
src/piketype/backends/py/emitter.py:75:        elif isinstance(type_ir, FlagsIR):
src/piketype/backends/py/emitter.py:77:        elif isinstance(type_ir, EnumIR):
src/piketype/backends/py/emitter.py:111:            raise ValueError(f"unsupported Python expression node {type(expr).__name__}")
src/piketype/backends/py/emitter.py:117:    bc = byte_count(type_ir.resolved_width)
src/piketype/backends/py/emitter.py:120:        f"    WIDTH = {type_ir.resolved_width}",
src/piketype/backends/py/emitter.py:128:            mask = (1 << type_ir.resolved_width) - 1
src/piketype/backends/py/emitter.py:129:            sign_bit = 1 << (type_ir.resolved_width - 1)
src/piketype/backends/py/emitter.py:135:                    f"    MASK = {mask}",
src/piketype/backends/py/emitter.py:139:                    '        if not isinstance(value, int):',
src/piketype/backends/py/emitter.py:146:                    "        return self.value & self.MASK",
src/piketype/backends/py/emitter.py:150:                    "        value = packed & cls.MASK",
src/piketype/backends/py/emitter.py:151:                    "        signed_value = value - (1 << cls.WIDTH) if (value & cls.SIGN_BIT) else value",
src/piketype/backends/py/emitter.py:155:                    "        mask = self.MASK",
src/piketype/backends/py/emitter.py:158:                    f"            packed |= ((1 << (self.BYTE_COUNT * 8)) - 1) ^ mask",
src/piketype/backends/py/emitter.py:163:                    '        if not isinstance(data, (bytes, bytearray)):',
src/piketype/backends/py/emitter.py:169:                    "        data_bits = raw_int & cls.MASK",
src/piketype/backends/py/emitter.py:170:                    f"        padding = raw_int >> cls.WIDTH",
src/piketype/backends/py/emitter.py:171:                    "        sign_bit = (data_bits >> (cls.WIDTH - 1)) & 1",
src/piketype/backends/py/emitter.py:172:                    f"        expected_padding = ((1 << {pad_bits}) - 1) if sign_bit else 0",
src/piketype/backends/py/emitter.py:178:                    "        return type(self)(self.value)",
src/piketype/backends/py/emitter.py:187:                    "        if isinstance(other, type(self)):",
src/piketype/backends/py/emitter.py:189:                    "        if isinstance(other, int):",
src/piketype/backends/py/emitter.py:205:                    '        if not isinstance(value, int):',
src/piketype/backends/py/emitter.py:223:                    '        if not isinstance(data, (bytes, bytearray)):',
src/piketype/backends/py/emitter.py:232:                    "        return type(self)(self.value)",
src/piketype/backends/py/emitter.py:241:                    "        if isinstance(other, type(self)):",
src/piketype/backends/py/emitter.py:243:                    "        if isinstance(other, int):",
src/piketype/backends/py/emitter.py:253:        mask_msb_byte = (1 << (type_ir.resolved_width % 8)) - 1 if type_ir.resolved_width % 8 else 0xFF
src/piketype/backends/py/emitter.py:259:                "        if isinstance(value, int):",
src/piketype/backends/py/emitter.py:264:                '        if not isinstance(value, (bytes, bytearray)):',
src/piketype/backends/py/emitter.py:285:                '        if not isinstance(data, (bytes, bytearray)):',
src/piketype/backends/py/emitter.py:295:                "        return type(self)(self.value)",
src/piketype/backends/py/emitter.py:298:                "        if isinstance(other, type(self)):",
src/piketype/backends/py/emitter.py:300:                "        if isinstance(other, (bytes, bytearray)):",
src/piketype/backends/py/emitter.py:315:    struct_byte_count = sum(
src/piketype/backends/py/emitter.py:316:        _field_byte_count(field_ir=f, type_index=type_index) for f in type_ir.fields
src/piketype/backends/py/emitter.py:321:        f"    WIDTH = {width}",
src/piketype/backends/py/emitter.py:322:        f"    BYTE_COUNT = {struct_byte_count}",
src/piketype/backends/py/emitter.py:354:            '        return type(self).from_bytes(self.to_bytes())',
src/piketype/backends/py/emitter.py:367:        fbc = _field_byte_count(field_ir=field_ir, type_index=type_index)
src/piketype/backends/py/emitter.py:371:                if isinstance(target, StructIR):
src/piketype/backends/py/emitter.py:382:                    mask = (1 << fw) - 1
src/piketype/backends/py/emitter.py:389:                                f"            _packed_{field_ir.name} |= ((1 << {fbc * 8}) - 1) ^ _mask_{field_ir.name}",
src/piketype/backends/py/emitter.py:404:                raise ValueError(f"unsupported Python struct field type {type(field_ir.type_ir).__name__}")
src/piketype/backends/py/emitter.py:417:        '        if not isinstance(data, (bytes, bytearray)):',
src/piketype/backends/py/emitter.py:426:        fbc = _field_byte_count(field_ir=field_ir, type_index=type_index)
src/piketype/backends/py/emitter.py:440:                    mask = (1 << fw) - 1
src/piketype/backends/py/emitter.py:443:                        sign_bit_val = 1 << (fw - 1)
src/piketype/backends/py/emitter.py:450:                                f"        _expected_padding_{field_ir.name} = ((1 << {pad_bits}) - 1) if _sign_bit_{field_ir.name} else 0",
src/piketype/backends/py/emitter.py:453:                                f"        obj.{field_ir.name} = _data_{field_ir.name} - {1 << fw} if (_data_{field_ir.name} & {sign_bit_val}) else _data_{field_ir.name}",
src/piketype/backends/py/emitter.py:466:                    mask_msb_byte = (1 << (resolved_width % 8)) - 1 if resolved_width % 8 else 0xFF
src/piketype/backends/py/emitter.py:475:                raise ValueError(f"unsupported Python struct field type {type(field_ir.type_ir).__name__}")
src/piketype/backends/py/emitter.py:486:            if isinstance(target, StructIR):
src/piketype/backends/py/emitter.py:492:            raise ValueError(f"unsupported Python struct field type {type(field_ir.type_ir).__name__}")
src/piketype/backends/py/emitter.py:503:            return f'b"\\x00" * {byte_count(resolved_width)}'
src/piketype/backends/py/emitter.py:505:            raise ValueError(f"unsupported Python struct field type {type(field_ir.type_ir).__name__}")
src/piketype/backends/py/emitter.py:515:            if isinstance(target, StructIR):
src/piketype/backends/py/emitter.py:520:                        f"        if isinstance(value, {class_name}):",
src/piketype/backends/py/emitter.py:525:            elif isinstance(target, FlagsIR):
src/piketype/backends/py/emitter.py:528:                        f"        if isinstance(value, {class_name}):",
src/piketype/backends/py/emitter.py:533:            elif isinstance(target, EnumIR):
src/piketype/backends/py/emitter.py:536:                        f"        if isinstance(value, {class_name}):",
src/piketype/backends/py/emitter.py:544:                        f"        if isinstance(value, {class_name}):",
src/piketype/backends/py/emitter.py:555:                        "        if not isinstance(value, int):",
src/piketype/backends/py/emitter.py:563:                fbc = byte_count(resolved_width)
src/piketype/backends/py/emitter.py:566:                        "        if isinstance(value, bytearray):",
src/piketype/backends/py/emitter.py:568:                        "        if not isinstance(value, bytes):",
src/piketype/backends/py/emitter.py:576:            raise ValueError(f"unsupported Python struct field type {type(field_ir.type_ir).__name__}")
src/piketype/backends/py/emitter.py:582:    if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/py/emitter.py:584:    if isinstance(type_ir, FlagsIR):
src/piketype/backends/py/emitter.py:586:    if isinstance(type_ir, EnumIR):
src/piketype/backends/py/emitter.py:593:    if isinstance(field_type, ScalarTypeSpecIR):
src/piketype/backends/py/emitter.py:598:def _type_byte_count(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
src/piketype/backends/py/emitter.py:599:    """Resolve the byte-aligned byte count of one type (including alignment)."""
src/piketype/backends/py/emitter.py:600:    if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/py/emitter.py:601:        return byte_count(type_ir.resolved_width)
src/piketype/backends/py/emitter.py:602:    if isinstance(type_ir, FlagsIR):
src/piketype/backends/py/emitter.py:604:    if isinstance(type_ir, EnumIR):
src/piketype/backends/py/emitter.py:605:        return byte_count(type_ir.resolved_width)
src/piketype/backends/py/emitter.py:606:    field_bytes = sum(_field_byte_count(field_ir=f, type_index=type_index) for f in type_ir.fields)
src/piketype/backends/py/emitter.py:610:def _field_byte_count(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> int:
src/piketype/backends/py/emitter.py:614:            return byte_count(resolved_width)
src/piketype/backends/py/emitter.py:616:            return _type_byte_count(type_ir=type_index[name], type_index=type_index)
src/piketype/backends/py/emitter.py:618:            raise ValueError(f"unsupported field type {type(field_ir.type_ir).__name__}")
src/piketype/backends/py/emitter.py:639:    bc = byte_count(type_ir.resolved_width)
src/piketype/backends/py/emitter.py:642:    mask = (1 << width) - 1
src/piketype/backends/py/emitter.py:655:        f"    WIDTH = {width}",
src/piketype/backends/py/emitter.py:659:        f"        if not isinstance(value, {enum_class_name}):",
src/piketype/backends/py/emitter.py:668:        "        if not isinstance(data, (bytes, bytearray)):",
src/piketype/backends/py/emitter.py:681:        "        return type(self)(self.value)",
src/piketype/backends/py/emitter.py:690:        "        if isinstance(other, type(self)):",
src/piketype/backends/py/emitter.py:692:        "        if isinstance(other, int):",
src/piketype/backends/py/emitter.py:711:    bc = byte_count(num_flags)
src/piketype/backends/py/emitter.py:714:    data_mask = ((1 << num_flags) - 1) << type_ir.alignment_bits
src/piketype/backends/py/emitter.py:718:        f"    WIDTH: int = {num_flags}",
src/piketype/backends/py/emitter.py:728:        mask = 1 << (total_bits - 1 - i)
src/piketype/backends/py/emitter.py:759:            "        if not isinstance(data, (bytes, bytearray)):",
src/piketype/backends/py/emitter.py:775:            "        obj = self.__class__()",
src/piketype/backends/py/emitter.py:786:            f"        if not isinstance(other, {class_name}):",
src/piketype/backends/cpp/emitter.py:27:    byte_count,
src/piketype/backends/cpp/emitter.py:71:        if isinstance(const.expr, IntLiteralExprIR):
src/piketype/backends/cpp/emitter.py:81:        if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/cpp/emitter.py:83:        elif isinstance(type_ir, StructIR):
src/piketype/backends/cpp/emitter.py:85:        elif isinstance(type_ir, FlagsIR):
src/piketype/backends/cpp/emitter.py:87:        elif isinstance(type_ir, EnumIR):
src/piketype/backends/cpp/emitter.py:121:            raise ValidationError(f"unsupported C++ expression node {type(expr).__name__}")
src/piketype/backends/cpp/emitter.py:132:    bc = byte_count(type_ir.resolved_width)
src/piketype/backends/cpp/emitter.py:137:        f"  static constexpr std::size_t WIDTH = {width};",
src/piketype/backends/cpp/emitter.py:144:            (1 << width) - 1 if width < 64 else 2**64 - 1
src/piketype/backends/cpp/emitter.py:160:                    f"  static constexpr std::uint64_t MASK = {mask_literal};",
src/piketype/backends/cpp/emitter.py:166:                    "    std::uint64_t bits = static_cast<std::uint64_t>(value) & MASK;",
src/piketype/backends/cpp/emitter.py:173:                        f"    if (value < 0 && WIDTH < BYTE_COUNT * 8U) {{",
src/piketype/backends/cpp/emitter.py:174:                        f"      for (std::size_t i = WIDTH; i < BYTE_COUNT * 8U; ++i) {{",
src/piketype/backends/cpp/emitter.py:200:                byte_mask = _cpp_unsigned_literal((1 << (bc * 8)) - 1 if bc * 8 < 64 else 2**64 - 1)
src/piketype/backends/cpp/emitter.py:203:                        "    std::uint64_t data_bits = bits & MASK;",
src/piketype/backends/cpp/emitter.py:205:                        f"    std::uint64_t expected_pad = sign_bit ? (~MASK & {byte_mask}) : 0ULL;",
src/piketype/backends/cpp/emitter.py:206:                        f"    if ((bits & ~MASK & {byte_mask}) != expected_pad) {{",
src/piketype/backends/cpp/emitter.py:213:                    "    bits &= MASK;",
src/piketype/backends/cpp/emitter.py:218:                sign_bit_lit = _cpp_unsigned_literal(1 << (width - 1))
src/piketype/backends/cpp/emitter.py:219:                full_range_lit = _cpp_unsigned_literal(1 << width)
src/piketype/backends/cpp/emitter.py:222:                        f"    if ((bits & {sign_bit_lit}) != 0U && WIDTH < 64) {{",
src/piketype/backends/cpp/emitter.py:257:                    f"  static constexpr std::uint64_t MASK = {mask_literal};",
src/piketype/backends/cpp/emitter.py:279:                    "    value = validate_value(static_cast<value_type>(bits & MASK));",
src/piketype/backends/cpp/emitter.py:305:        msb_mask = _cpp_unsigned_literal((1 << (8 - pad)) - 1) if pad > 0 else "0xFFU"
src/piketype/backends/cpp/emitter.py:353:    bc = byte_count(width)
src/piketype/backends/cpp/emitter.py:356:    mask_lit = _cpp_unsigned_literal((1 << width) - 1 if width < 64 else 2**64 - 1)
src/piketype/backends/cpp/emitter.py:369:        f"  static constexpr std::size_t WIDTH = {width};",
src/piketype/backends/cpp/emitter.py:433:    bc = byte_count(total_width)
src/piketype/backends/cpp/emitter.py:441:    data_mask_val = ((1 << num_flags) - 1) << (storage_bits - num_flags)
src/piketype/backends/cpp/emitter.py:450:        f"  static constexpr std::size_t WIDTH = {num_flags};",
src/piketype/backends/cpp/emitter.py:457:        mask_val = 1 << (storage_bits - 1 - i)
src/piketype/backends/cpp/emitter.py:551:    total_bc = _type_byte_count(type_ir=type_ir, type_index=type_index)
src/piketype/backends/cpp/emitter.py:555:        f"  static constexpr std::size_t WIDTH = {data_width};",
src/piketype/backends/cpp/emitter.py:654:            raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
src/piketype/backends/cpp/emitter.py:665:            bc = byte_count(resolved_width)
src/piketype/backends/cpp/emitter.py:668:            raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
src/piketype/backends/cpp/emitter.py:679:    if isinstance(field_ir.type_ir, ScalarTypeSpecIR) and field_ir.type_ir.resolved_width <= 64:
src/piketype/backends/cpp/emitter.py:689:    elif isinstance(field_ir.type_ir, ScalarTypeSpecIR):
src/piketype/backends/cpp/emitter.py:691:        bc = byte_count(field_ir.type_ir.resolved_width)
src/piketype/backends/cpp/emitter.py:701:    elif isinstance(field_ir.type_ir, TypeRefIR):
src/piketype/backends/cpp/emitter.py:703:        if isinstance(target, (StructIR, ScalarAliasIR, FlagsIR, EnumIR)):
src/piketype/backends/cpp/emitter.py:713:            raise ValidationError(f"unsupported type ref target {type(target).__name__}")
src/piketype/backends/cpp/emitter.py:715:        raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
src/piketype/backends/cpp/emitter.py:728:    fbc = _field_byte_count(field=field_ir, type_index=type_index)
src/piketype/backends/cpp/emitter.py:730:    if isinstance(field_ir.type_ir, ScalarTypeSpecIR) and field_ir.type_ir.resolved_width <= 64:
src/piketype/backends/cpp/emitter.py:737:    elif isinstance(field_ir.type_ir, ScalarTypeSpecIR):
src/piketype/backends/cpp/emitter.py:745:    elif isinstance(field_ir.type_ir, TypeRefIR):
src/piketype/backends/cpp/emitter.py:747:        if isinstance(target, (StructIR, ScalarAliasIR, FlagsIR, EnumIR)):
src/piketype/backends/cpp/emitter.py:759:            raise ValidationError(f"unsupported type ref target {type(target).__name__}")
src/piketype/backends/cpp/emitter.py:761:        raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
src/piketype/backends/cpp/emitter.py:772:    if not isinstance(field_ir.type_ir, ScalarTypeSpecIR):
src/piketype/backends/cpp/emitter.py:775:    bc = byte_count(width)
src/piketype/backends/cpp/emitter.py:786:    assert isinstance(field_ir.type_ir, ScalarTypeSpecIR)
src/piketype/backends/cpp/emitter.py:789:    mask = (1 << width) - 1 if width < 64 else 2**64 - 1
src/piketype/backends/cpp/emitter.py:799:                f"    constexpr std::uint64_t MASK = {mask_lit};",
src/piketype/backends/cpp/emitter.py:800:                "    std::uint64_t bits = static_cast<std::uint64_t>(v) & MASK;",
src/piketype/backends/cpp/emitter.py:807:                    "      bits |= ~MASK;",
src/piketype/backends/cpp/emitter.py:833:            byte_total_mask = (1 << (bc * 8)) - 1 if bc * 8 < 64 else 2**64 - 1
src/piketype/backends/cpp/emitter.py:837:                    f"    constexpr std::uint64_t MASK = {mask_lit};",
src/piketype/backends/cpp/emitter.py:838:                    "    std::uint64_t data_bits = bits & MASK;",
src/piketype/backends/cpp/emitter.py:840:                    f"    std::uint64_t expected_pad = sign_bit ? (~MASK & {byte_total_mask_lit}) : 0ULL;",
src/piketype/backends/cpp/emitter.py:841:                    f"    if ((bits & ~MASK & {byte_total_mask_lit}) != expected_pad) {{",
src/piketype/backends/cpp/emitter.py:848:            lines.append(f"    constexpr std::uint64_t MASK = {mask_lit};")
src/piketype/backends/cpp/emitter.py:849:            lines.append("    bits &= MASK;")
src/piketype/backends/cpp/emitter.py:852:            sign_bit_lit = _cpp_unsigned_literal(1 << (width - 1))
src/piketype/backends/cpp/emitter.py:853:            full_range_lit = _cpp_unsigned_literal(1 << width)
src/piketype/backends/cpp/emitter.py:940:    msb_mask = _cpp_unsigned_literal((1 << (8 - pad)) - 1) if pad > 0 else "0xFFU"
src/piketype/backends/cpp/emitter.py:973:    if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/cpp/emitter.py:975:    if isinstance(type_ir, FlagsIR):
src/piketype/backends/cpp/emitter.py:977:    if isinstance(type_ir, EnumIR):
src/piketype/backends/cpp/emitter.py:984:    if isinstance(field_type, ScalarTypeSpecIR):
src/piketype/backends/cpp/emitter.py:989:def _type_byte_count(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
src/piketype/backends/cpp/emitter.py:990:    """Compute the byte-aligned byte count for a type (sum of per-field byte counts + alignment)."""
src/piketype/backends/cpp/emitter.py:991:    if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/cpp/emitter.py:992:        return byte_count(type_ir.resolved_width)
src/piketype/backends/cpp/emitter.py:993:    if isinstance(type_ir, FlagsIR):
src/piketype/backends/cpp/emitter.py:995:    if isinstance(type_ir, EnumIR):
src/piketype/backends/cpp/emitter.py:996:        return byte_count(type_ir.resolved_width)
src/piketype/backends/cpp/emitter.py:997:    field_bytes = sum(_field_byte_count(field=field, type_index=type_index) for field in type_ir.fields)
src/piketype/backends/cpp/emitter.py:1001:def _field_byte_count(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> int:
src/piketype/backends/cpp/emitter.py:1005:            return byte_count(resolved_width)
src/piketype/backends/cpp/emitter.py:1008:            if isinstance(target, ScalarAliasIR):
src/piketype/backends/cpp/emitter.py:1009:                return byte_count(target.resolved_width)
src/piketype/backends/cpp/emitter.py:1010:            return _type_byte_count(type_ir=target, type_index=type_index)
src/piketype/backends/cpp/emitter.py:1012:            raise ValidationError(f"unsupported field type {type(field.type_ir).__name__}")
src/piketype/backends/cpp/emitter.py:1040:    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], StructIR)
src/piketype/backends/cpp/emitter.py:1045:    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], ScalarAliasIR)
src/piketype/backends/cpp/emitter.py:1050:    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], FlagsIR)
src/piketype/backends/cpp/emitter.py:1055:    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], EnumIR)
src/piketype/backends/cpp/emitter.py:1060:    return isinstance(field_type, ScalarTypeSpecIR) and field_type.resolved_width > 64
src/piketype/backends/sv/emitter.py:26:    byte_count,
src/piketype/backends/sv/emitter.py:77:        sv_expr = sv_literal if isinstance(const.expr, IntLiteralExprIR) else _render_sv_expr(expr=const.expr)
src/piketype/backends/sv/emitter.py:105:        f"  localparam int LP_{upper_base}_BYTE_COUNT = {_type_byte_count(type_ir=type_ir, type_index=type_index)};",
src/piketype/backends/sv/emitter.py:109:    if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/sv/emitter.py:111:    elif isinstance(type_ir, StructIR):
src/piketype/backends/sv/emitter.py:113:    elif isinstance(type_ir, FlagsIR):
src/piketype/backends/sv/emitter.py:115:    elif isinstance(type_ir, EnumIR):
src/piketype/backends/sv/emitter.py:128:    if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/sv/emitter.py:130:    if isinstance(type_ir, EnumIR):
src/piketype/backends/sv/emitter.py:167:    """Render one packed struct field type (without padding)."""
src/piketype/backends/sv/emitter.py:168:    if isinstance(field_type, TypeRefIR):
src/piketype/backends/sv/emitter.py:206:    if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/sv/emitter.py:213:    if isinstance(type_ir, FlagsIR):
src/piketype/backends/sv/emitter.py:222:    if isinstance(type_ir, EnumIR):
src/piketype/backends/sv/emitter.py:231:        if isinstance(field.type_ir, TypeRefIR):
src/piketype/backends/sv/emitter.py:250:    if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/sv/emitter.py:257:    if isinstance(type_ir, FlagsIR):
src/piketype/backends/sv/emitter.py:269:    if isinstance(type_ir, EnumIR):
src/piketype/backends/sv/emitter.py:286:        if isinstance(field.type_ir, TypeRefIR):
src/piketype/backends/sv/emitter.py:321:        if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/sv/emitter.py:323:        elif isinstance(type_ir, StructIR):
src/piketype/backends/sv/emitter.py:325:        elif isinstance(type_ir, FlagsIR):
src/piketype/backends/sv/emitter.py:327:        elif isinstance(type_ir, EnumIR):
src/piketype/backends/sv/emitter.py:338:    bc = byte_count(type_ir.resolved_width)
src/piketype/backends/sv/emitter.py:343:        f"  localparam int WIDTH = LP_{upper_base}_WIDTH;",
src/piketype/backends/sv/emitter.py:367:        f"    padded[WIDTH-1:0] = value;",
src/piketype/backends/sv/emitter.py:370:        lines.append(f"    for (int i = WIDTH; i < BYTE_COUNT*8; i++) padded[i] = value[WIDTH-1];")
src/piketype/backends/sv/emitter.py:393:            f"    for (int i = WIDTH; i < BYTE_COUNT*8; i++) begin",
src/piketype/backends/sv/emitter.py:394:            "      if (padded[i] !== padded[WIDTH-1]) begin",
src/piketype/backends/sv/emitter.py:400:        f"    value = {type_ir.name}'(padded[WIDTH-1:0]);",
src/piketype/backends/sv/emitter.py:436:        f"  localparam int WIDTH = LP_{upper_base}_WIDTH;",
src/piketype/backends/sv/emitter.py:569:    bc = byte_count(num_flags)
src/piketype/backends/sv/emitter.py:574:        f"  localparam int WIDTH = {num_flags};",
src/piketype/backends/sv/emitter.py:679:    bc = byte_count(type_ir.resolved_width)
src/piketype/backends/sv/emitter.py:685:        f"  localparam int WIDTH = LP_{upper_base}_WIDTH;",
src/piketype/backends/sv/emitter.py:709:        f"    padded[WIDTH-1:0] = value;",
src/piketype/backends/sv/emitter.py:728:        f"    value = {type_ir.name}'(padded[WIDTH-1:0]);",
src/piketype/backends/sv/emitter.py:758:    if isinstance(field.type_ir, TypeRefIR):
src/piketype/backends/sv/emitter.py:760:        if isinstance(target, (StructIR, FlagsIR, EnumIR)):
src/piketype/backends/sv/emitter.py:772:        fbc = _field_byte_count(field=field, type_index=type_index)
src/piketype/backends/sv/emitter.py:782:        fbc = _field_byte_count(field=field, type_index=type_index)
src/piketype/backends/sv/emitter.py:808:        fbc = _field_byte_count(field=field, type_index=type_index)
src/piketype/backends/sv/emitter.py:818:        fbc = _field_byte_count(field=field, type_index=type_index)
src/piketype/backends/sv/emitter.py:878:            raise ValueError(f"unsupported SV expression node {type(expr).__name__}")
src/piketype/backends/sv/emitter.py:893:    if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/sv/emitter.py:895:    if isinstance(type_ir, FlagsIR):
src/piketype/backends/sv/emitter.py:897:    if isinstance(type_ir, EnumIR):
src/piketype/backends/sv/emitter.py:904:    if isinstance(field.type_ir, ScalarTypeSpecIR):
src/piketype/backends/sv/emitter.py:910:def _type_byte_count(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
src/piketype/backends/sv/emitter.py:912:    if isinstance(type_ir, ScalarAliasIR):
src/piketype/backends/sv/emitter.py:913:        return byte_count(type_ir.resolved_width)
src/piketype/backends/sv/emitter.py:914:    if isinstance(type_ir, FlagsIR):
src/piketype/backends/sv/emitter.py:915:        return byte_count(len(type_ir.fields))
src/piketype/backends/sv/emitter.py:916:    if isinstance(type_ir, EnumIR):
src/piketype/backends/sv/emitter.py:917:        return byte_count(type_ir.resolved_width)
src/piketype/backends/sv/emitter.py:918:    field_bytes = sum(_field_byte_count(field=f, type_index=type_index) for f in type_ir.fields)
src/piketype/backends/sv/emitter.py:922:def _field_byte_count(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> int:
src/piketype/backends/sv/emitter.py:924:    if isinstance(field.type_ir, ScalarTypeSpecIR):
src/piketype/backends/sv/emitter.py:925:        return byte_count(field.type_ir.resolved_width)
src/piketype/backends/sv/emitter.py:927:    return _type_byte_count(type_ir=target, type_index=type_index)
src/piketype/backends/sv/emitter.py:932:    if isinstance(field.type_ir, ScalarTypeSpecIR):
src/piketype/backends/sv/emitter.py:935:    if isinstance(target, ScalarAliasIR):
src/piketype/backends/sv/emitter.py:942:    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], (StructIR, FlagsIR, EnumIR))
tests/goldens/gen/struct_enum_member/cpp/alpha/piketype/types_types.hpp:19:  static constexpr std::size_t WIDTH = 2;
tests/goldens/gen/struct_enum_member/cpp/alpha/piketype/types_types.hpp:71:  static constexpr std::size_t WIDTH = 10;
tests/goldens/gen/struct_enum_member/cpp/alpha/piketype/types_types.hpp:145:  static constexpr std::size_t WIDTH = 10;
tests/goldens/gen/struct_multiple_of/cpp/alpha/piketype/types_types.hpp:17:  static constexpr std::size_t WIDTH = 17;
tests/goldens/gen/struct_multiple_of/cpp/alpha/piketype/types_types.hpp:117:  static constexpr std::size_t WIDTH = 17;
tests/goldens/gen/struct_multiple_of/cpp/alpha/piketype/types_types.hpp:216:  static constexpr std::size_t WIDTH = 3;
tests/goldens/gen/struct_multiple_of/cpp/alpha/piketype/types_types.hpp:281:  static constexpr std::size_t WIDTH = 11;
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:17:    WIDTH = 2
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:21:        if not isinstance(value, cmd_enum_t):
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:30:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:43:        return type(self)(self.value)
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:52:        if isinstance(other, type(self)):
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:54:        if isinstance(other, int):
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:63:    WIDTH = 10
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:77:        if isinstance(value, cmd_ct):
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:83:        if not isinstance(value, int):
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:98:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:112:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:116:    WIDTH = 10
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:130:        if isinstance(value, cmd_ct):
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:136:        if not isinstance(value, int):
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:152:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:166:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:11:    WIDTH = 17
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:25:        if not isinstance(value, int):
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:33:        if not isinstance(value, int):
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:50:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:64:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:68:    WIDTH = 17
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:82:        if not isinstance(value, int):
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:90:        if not isinstance(value, int):
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:106:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:120:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:124:    WIDTH = 3
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:135:        if not isinstance(value, int):
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:150:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:162:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:166:    WIDTH = 11
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:182:        if isinstance(value, inner_ct):
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:188:        if not isinstance(value, int):
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:205:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:219:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_multiple_of/sv/alpha/piketype/types_test_pkg.sv:9:    localparam int WIDTH = LP_ALIGNED_WIDTH;
tests/goldens/gen/struct_multiple_of/sv/alpha/piketype/types_test_pkg.sv:106:    localparam int WIDTH = LP_NO_EXTRA_PAD_WIDTH;
tests/goldens/gen/struct_multiple_of/sv/alpha/piketype/types_test_pkg.sv:197:    localparam int WIDTH = LP_INNER_WIDTH;
tests/goldens/gen/struct_multiple_of/sv/alpha/piketype/types_test_pkg.sv:273:    localparam int WIDTH = LP_OUTER_WIDTH;
tests/goldens/gen/struct_flags_member/cpp/alpha/piketype/types_types.hpp:17:  static constexpr std::size_t WIDTH = 3;
tests/goldens/gen/struct_flags_member/cpp/alpha/piketype/types_types.hpp:69:  static constexpr std::size_t WIDTH = 8;
tests/goldens/gen/struct_flags_member/cpp/alpha/piketype/types_types.hpp:144:  static constexpr std::size_t WIDTH = 6;
tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_test_pkg.sv:9:    localparam int WIDTH = LP_CMD_WIDTH;
tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_test_pkg.sv:29:      padded[WIDTH-1:0] = value;
tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_test_pkg.sv:44:      value = cmd_t'(padded[WIDTH-1:0]);
tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_test_pkg.sv:67:    localparam int WIDTH = LP_PKT_WIDTH;
tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_test_pkg.sv:155:    localparam int WIDTH = LP_ALIGNED_PKT_WIDTH;
tests/goldens/gen/struct_flags_member/sv/alpha/piketype/types_test_pkg.sv:9:    localparam int WIDTH = 3;
tests/goldens/gen/struct_flags_member/sv/alpha/piketype/types_test_pkg.sv:89:    localparam int WIDTH = LP_REPORT_WIDTH;
tests/goldens/gen/struct_flags_member/sv/alpha/piketype/types_test_pkg.sv:177:    localparam int WIDTH = LP_ALIGNED_REPORT_WIDTH;
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:10:    WIDTH: int = 3
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:54:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:64:        obj = self.__class__()
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:69:        if not isinstance(other, status_ct):
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:75:    WIDTH = 8
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:89:        if isinstance(value, status_ct):
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:95:        if not isinstance(value, int):
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:110:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:124:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:128:    WIDTH = 6
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:142:        if isinstance(value, status_ct):
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:148:        if not isinstance(value, int):
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:164:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:178:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_wide/cpp/alpha/piketype/types_types.hpp:17:  static constexpr std::size_t WIDTH = 194;
tests/goldens/gen/struct_padded/cpp/alpha/piketype/types_types.hpp:17:  static constexpr std::size_t WIDTH = 13;
tests/goldens/gen/struct_padded/cpp/alpha/piketype/types_types.hpp:22:  static constexpr std::uint64_t MASK = 8191U;
tests/goldens/gen/struct_padded/cpp/alpha/piketype/types_types.hpp:44:    value = validate_value(static_cast<value_type>(bits & MASK));
tests/goldens/gen/struct_padded/cpp/alpha/piketype/types_types.hpp:68:  static constexpr std::size_t WIDTH = 19;
tests/goldens/gen/struct_wide/py/alpha/piketype/types_types.py:11:    WIDTH = 194
tests/goldens/gen/struct_wide/py/alpha/piketype/types_types.py:28:        if isinstance(value, bytearray):
tests/goldens/gen/struct_wide/py/alpha/piketype/types_types.py:30:        if not isinstance(value, bytes):
tests/goldens/gen/struct_wide/py/alpha/piketype/types_types.py:38:        if not isinstance(value, int):
tests/goldens/gen/struct_wide/py/alpha/piketype/types_types.py:46:        if isinstance(value, bytearray):
tests/goldens/gen/struct_wide/py/alpha/piketype/types_types.py:48:        if not isinstance(value, bytes):
tests/goldens/gen/struct_wide/py/alpha/piketype/types_types.py:64:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_wide/py/alpha/piketype/types_types.py:82:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_wide/sv/alpha/piketype/types_test_pkg.sv:9:    localparam int WIDTH = LP_BIG_WIDTH;
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:19:  static constexpr std::size_t WIDTH = 13;
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:24:  static constexpr std::uint64_t MASK = 8191U;
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:46:    value = validate_value(static_cast<value_type>(bits & MASK));
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:70:  static constexpr std::size_t WIDTH = 8;
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:77:  static constexpr std::uint64_t MASK = 255U;
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:83:    std::uint64_t bits = static_cast<std::uint64_t>(value) & MASK;
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:98:    bits &= MASK;
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:100:    if ((bits & 128U) != 0U && WIDTH < 64) {
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:127:  static constexpr std::size_t WIDTH = 1;
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:132:  static constexpr std::uint64_t MASK = 1U;
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:154:    value = validate_value(static_cast<value_type>(bits & MASK));
tests/goldens/gen/scalar_wide/cpp/alpha/piketype/types_types.hpp:17:  static constexpr std::size_t WIDTH = 37;
tests/goldens/gen/scalar_wide/cpp/alpha/piketype/types_types.hpp:22:  static constexpr std::uint64_t MASK = 137438953471ULL;
tests/goldens/gen/scalar_wide/cpp/alpha/piketype/types_types.hpp:44:    value = validate_value(static_cast<value_type>(bits & MASK));
tests/goldens/gen/scalar_wide/cpp/alpha/piketype/types_types.hpp:68:  static constexpr std::size_t WIDTH = 65;
tests/goldens/gen/scalar_wide/cpp/alpha/piketype/types_types.hpp:103:  static constexpr std::size_t WIDTH = 128;
tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp:19:  static constexpr std::size_t WIDTH = 13;
tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp:24:  static constexpr std::uint64_t MASK = 8191U;
tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp:46:    value = validate_value(static_cast<value_type>(bits & MASK));
tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp:70:  static constexpr std::size_t WIDTH = 1;
tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp:75:  static constexpr std::uint64_t MASK = 1U;
tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp:97:    value = validate_value(static_cast<value_type>(bits & MASK));
tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp:121:  static constexpr std::size_t WIDTH = 14;
tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp:171:  static constexpr std::size_t WIDTH = 19;
tests/goldens/gen/enum_basic/cpp/foo/piketype/defs_types.hpp:19:  static constexpr std::size_t WIDTH = 4;
tests/goldens/gen/enum_basic/cpp/foo/piketype/defs_types.hpp:73:  static constexpr std::size_t WIDTH = 8;
tests/goldens/gen/enum_basic/cpp/foo/piketype/defs_types.hpp:128:  static constexpr std::size_t WIDTH = 1;
tests/goldens/gen/enum_basic/cpp/foo/piketype/defs_types.hpp:180:  static constexpr std::size_t WIDTH = 64;
tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:19:  static constexpr std::size_t WIDTH = 13;
tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:24:  static constexpr std::uint64_t MASK = 8191U;
tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:46:    value = validate_value(static_cast<value_type>(bits & MASK));
tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:70:  static constexpr std::size_t WIDTH = 1;
tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:75:  static constexpr std::uint64_t MASK = 1U;
tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:97:    value = validate_value(static_cast<value_type>(bits & MASK));
tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:121:  static constexpr std::size_t WIDTH = 16;
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:9:    localparam int WIDTH = LP_ADDR_WIDTH;
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:29:      padded[WIDTH-1:0] = value;
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:44:      value = addr_t'(padded[WIDTH-1:0]);
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:67:    localparam int WIDTH = LP_FLAG_WIDTH;
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:87:      padded[WIDTH-1:0] = value;
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:102:      value = flag_t'(padded[WIDTH-1:0]);
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:125:    localparam int WIDTH = LP_HEADER_WIDTH;
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:216:    localparam int WIDTH = LP_PACKET_WIDTH;
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:12:    WIDTH = 13
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:19:        if not isinstance(value, int):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:37:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:46:        return type(self)(self.value)
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:55:        if isinstance(other, type(self)):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:57:        if isinstance(other, int):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:65:    WIDTH = 1
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:72:        if not isinstance(value, int):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:90:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:99:        return type(self)(self.value)
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:108:        if isinstance(other, type(self)):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:110:        if isinstance(other, int):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:119:    WIDTH = 14
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:133:        if isinstance(value, addr_ct):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:139:        if isinstance(value, flag_ct):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:151:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:165:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:169:    WIDTH = 19
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:188:        if isinstance(value, header_ct):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:194:        if not isinstance(value, int):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:202:        if not isinstance(value, int):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:221:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:237:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:17:  static constexpr std::size_t WIDTH = 4;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:24:  static constexpr std::uint64_t MASK = 15U;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:30:    std::uint64_t bits = static_cast<std::uint64_t>(value) & MASK;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:31:    if (value < 0 && WIDTH < BYTE_COUNT * 8U) {
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:32:      for (std::size_t i = WIDTH; i < BYTE_COUNT * 8U; ++i) {
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:50:    std::uint64_t data_bits = bits & MASK;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:52:    std::uint64_t expected_pad = sign_bit ? (~MASK & 255U) : 0ULL;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:53:    if ((bits & ~MASK & 255U) != expected_pad) {
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:56:    bits &= MASK;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:58:    if ((bits & 8U) != 0U && WIDTH < 64) {
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:85:  static constexpr std::size_t WIDTH = 5;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:92:  static constexpr std::uint64_t MASK = 31U;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:98:    std::uint64_t bits = static_cast<std::uint64_t>(value) & MASK;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:99:    if (value < 0 && WIDTH < BYTE_COUNT * 8U) {
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:100:      for (std::size_t i = WIDTH; i < BYTE_COUNT * 8U; ++i) {
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:118:    std::uint64_t data_bits = bits & MASK;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:120:    std::uint64_t expected_pad = sign_bit ? (~MASK & 255U) : 0ULL;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:121:    if ((bits & ~MASK & 255U) != expected_pad) {
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:124:    bits &= MASK;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:126:    if ((bits & 16U) != 0U && WIDTH < 64) {
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:153:  static constexpr std::size_t WIDTH = 9;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:200:    constexpr std::uint64_t MASK = 31U;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:201:    std::uint64_t bits = static_cast<std::uint64_t>(v) & MASK;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:203:      bits |= ~MASK;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:217:    constexpr std::uint64_t MASK = 31U;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:218:    std::uint64_t data_bits = bits & MASK;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:220:    std::uint64_t expected_pad = sign_bit ? (~MASK & 255U) : 0ULL;
tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:221:    if ((bits & ~MASK & 255U) != expected_pad) {
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:10:    WIDTH = 4
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:15:    MASK = 15
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:19:        if not isinstance(value, int):
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:26:        return self.value & self.MASK
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:30:        value = packed & cls.MASK
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:31:        signed_value = value - (1 << cls.WIDTH) if (value & cls.SIGN_BIT) else value
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:35:        mask = self.MASK
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:38:            packed |= ((1 << (self.BYTE_COUNT * 8)) - 1) ^ mask
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:43:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:49:        data_bits = raw_int & cls.MASK
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:50:        padding = raw_int >> cls.WIDTH
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:51:        sign_bit = (data_bits >> (cls.WIDTH - 1)) & 1
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:52:        expected_padding = ((1 << 4) - 1) if sign_bit else 0
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:58:        return type(self)(self.value)
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:67:        if isinstance(other, type(self)):
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:69:        if isinstance(other, int):
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:77:    WIDTH = 5
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:82:    MASK = 31
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:86:        if not isinstance(value, int):
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:93:        return self.value & self.MASK
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:97:        value = packed & cls.MASK
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:98:        signed_value = value - (1 << cls.WIDTH) if (value & cls.SIGN_BIT) else value
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:102:        mask = self.MASK
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:105:            packed |= ((1 << (self.BYTE_COUNT * 8)) - 1) ^ mask
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:110:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:116:        data_bits = raw_int & cls.MASK
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:117:        padding = raw_int >> cls.WIDTH
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:118:        sign_bit = (data_bits >> (cls.WIDTH - 1)) & 1
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:119:        expected_padding = ((1 << 3) - 1) if sign_bit else 0
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:125:        return type(self)(self.value)
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:134:        if isinstance(other, type(self)):
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:136:        if isinstance(other, int):
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:145:    WIDTH = 9
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:159:        if isinstance(value, signed_4_ct):
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:165:        if not isinstance(value, int):
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:177:            _packed_field_u |= ((1 << 8) - 1) ^ _mask_field_u
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:183:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:196:        _expected_padding_field_u = ((1 << 3) - 1) if _sign_bit_field_u else 0
tests/goldens/gen/struct_signed/py/alpha/piketype/types_types.py:204:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:10:    WIDTH = 13
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:17:        if not isinstance(value, int):
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:35:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:44:        return type(self)(self.value)
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:53:        if isinstance(other, type(self)):
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:55:        if isinstance(other, int):
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:64:    WIDTH = 19
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:84:        if not isinstance(value, int):
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:92:        if isinstance(value, foo_ct):
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:98:        if not isinstance(value, int):
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:106:        if not isinstance(value, int):
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:125:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_padded/py/alpha/piketype/types_types.py:143:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:9:    localparam int WIDTH = LP_SIGNED_4_WIDTH;
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:29:      padded[WIDTH-1:0] = value;
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:30:      for (int i = WIDTH; i < BYTE_COUNT*8; i++) padded[i] = value[WIDTH-1];
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:45:      for (int i = WIDTH; i < BYTE_COUNT*8; i++) begin
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:46:        if (padded[i] !== padded[WIDTH-1]) begin
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:50:      value = signed_4_t'(padded[WIDTH-1:0]);
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:73:    localparam int WIDTH = LP_SIGNED_5_WIDTH;
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:93:      padded[WIDTH-1:0] = value;
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:94:      for (int i = WIDTH; i < BYTE_COUNT*8; i++) padded[i] = value[WIDTH-1];
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:109:      for (int i = WIDTH; i < BYTE_COUNT*8; i++) begin
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:110:        if (padded[i] !== padded[WIDTH-1]) begin
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:114:      value = signed_5_t'(padded[WIDTH-1:0]);
tests/goldens/gen/struct_signed/sv/alpha/piketype/types_test_pkg.sv:137:    localparam int WIDTH = LP_MIXED_WIDTH;
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:8:    WIDTH = 37
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:15:        if not isinstance(value, int):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:33:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:42:        return type(self)(self.value)
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:51:        if isinstance(other, type(self)):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:53:        if isinstance(other, int):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:61:    WIDTH = 65
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:67:        if isinstance(value, int):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:72:        if not isinstance(value, (bytes, bytearray)):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:93:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:103:        return type(self)(self.value)
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:106:        if isinstance(other, type(self)):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:108:        if isinstance(other, (bytes, bytearray)):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:116:    WIDTH = 128
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:122:        if isinstance(value, int):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:127:        if not isinstance(value, (bytes, bytearray)):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:148:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:158:        return type(self)(self.value)
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:161:        if isinstance(other, type(self)):
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:163:        if isinstance(other, (bytes, bytearray)):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:10:    WIDTH = 13
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:17:        if not isinstance(value, int):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:35:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:44:        return type(self)(self.value)
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:53:        if isinstance(other, type(self)):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:55:        if isinstance(other, int):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:63:    WIDTH = 8
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:68:    MASK = 255
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:72:        if not isinstance(value, int):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:79:        return self.value & self.MASK
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:83:        value = packed & cls.MASK
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:84:        signed_value = value - (1 << cls.WIDTH) if (value & cls.SIGN_BIT) else value
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:88:        mask = self.MASK
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:91:            packed |= ((1 << (self.BYTE_COUNT * 8)) - 1) ^ mask
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:96:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:102:        data_bits = raw_int & cls.MASK
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:103:        padding = raw_int >> cls.WIDTH
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:104:        sign_bit = (data_bits >> (cls.WIDTH - 1)) & 1
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:105:        expected_padding = ((1 << 0) - 1) if sign_bit else 0
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:111:        return type(self)(self.value)
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:120:        if isinstance(other, type(self)):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:122:        if isinstance(other, int):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:130:    WIDTH = 1
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:137:        if not isinstance(value, int):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:155:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:164:        return type(self)(self.value)
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:173:        if isinstance(other, type(self)):
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:175:        if isinstance(other, int):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:15:    WIDTH = 4
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:19:        if not isinstance(value, color_enum_t):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:28:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:41:        return type(self)(self.value)
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:50:        if isinstance(other, type(self)):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:52:        if isinstance(other, int):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:66:    WIDTH = 8
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:70:        if not isinstance(value, cmd_enum_t):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:79:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:92:        return type(self)(self.value)
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:101:        if isinstance(other, type(self)):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:103:        if isinstance(other, int):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:114:    WIDTH = 1
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:118:        if not isinstance(value, flag_enum_t):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:127:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:140:        return type(self)(self.value)
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:149:        if isinstance(other, type(self)):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:151:        if isinstance(other, int):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:163:    WIDTH = 64
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:167:        if not isinstance(value, big_enum_t):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:176:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:189:        return type(self)(self.value)
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:198:        if isinstance(other, type(self)):
tests/goldens/gen/enum_basic/py/foo/piketype/defs_types.py:200:        if isinstance(other, int):
tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_test_pkg.sv:9:    localparam int WIDTH = LP_ADDR_WIDTH;
tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_test_pkg.sv:29:      padded[WIDTH-1:0] = value;
tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_test_pkg.sv:44:      value = addr_t'(padded[WIDTH-1:0]);
tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_test_pkg.sv:67:    localparam int WIDTH = LP_MASK_WIDTH;
tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_test_pkg.sv:87:      padded[WIDTH-1:0] = value;
tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_test_pkg.sv:102:      value = mask_t'(padded[WIDTH-1:0]);
tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_test_pkg.sv:125:    localparam int WIDTH = LP_FLAG_WIDTH;
tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_test_pkg.sv:145:      padded[WIDTH-1:0] = value;
tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_test_pkg.sv:160:      value = flag_t'(padded[WIDTH-1:0]);
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:12:    WIDTH = 13
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:19:        if not isinstance(value, int):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:37:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:46:        return type(self)(self.value)
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:55:        if isinstance(other, type(self)):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:57:        if isinstance(other, int):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:65:    WIDTH = 1
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:72:        if not isinstance(value, int):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:90:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:99:        return type(self)(self.value)
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:108:        if isinstance(other, type(self)):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:110:        if isinstance(other, int):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:119:    WIDTH = 16
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:136:        if isinstance(value, addr_ct):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:142:        if isinstance(value, flag_ct):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:148:        if not isinstance(value, int):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:164:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/struct_sv_basic/py/alpha/piketype/types_types.py:180:        return type(self).from_bytes(self.to_bytes())
tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:9:    localparam int WIDTH = LP_ADDR_WIDTH;
tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:29:      padded[WIDTH-1:0] = value;
tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:44:      value = addr_t'(padded[WIDTH-1:0]);
tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:67:    localparam int WIDTH = LP_FLAG_WIDTH;
tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:87:      padded[WIDTH-1:0] = value;
tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:102:      value = flag_t'(padded[WIDTH-1:0]);
tests/goldens/gen/struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:125:    localparam int WIDTH = LP_HEADER_WIDTH;
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_test_pkg.sv:9:    localparam int WIDTH = LP_NARROW_WIDTH;
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_test_pkg.sv:29:      padded[WIDTH-1:0] = value;
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_test_pkg.sv:44:      value = narrow_t'(padded[WIDTH-1:0]);
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_test_pkg.sv:67:    localparam int WIDTH = LP_WIDE_WIDTH;
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_test_pkg.sv:87:      padded[WIDTH-1:0] = value;
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_test_pkg.sv:102:      value = wide_t'(padded[WIDTH-1:0]);
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_test_pkg.sv:125:    localparam int WIDTH = LP_VERY_WIDE_WIDTH;
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_test_pkg.sv:145:      padded[WIDTH-1:0] = value;
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_test_pkg.sv:160:      value = very_wide_t'(padded[WIDTH-1:0]);
tests/goldens/gen/struct_padded/sv/alpha/piketype/types_test_pkg.sv:9:    localparam int WIDTH = LP_FOO_WIDTH;
tests/goldens/gen/struct_padded/sv/alpha/piketype/types_test_pkg.sv:29:      padded[WIDTH-1:0] = value;
tests/goldens/gen/struct_padded/sv/alpha/piketype/types_test_pkg.sv:44:      value = foo_t'(padded[WIDTH-1:0]);
tests/goldens/gen/struct_padded/sv/alpha/piketype/types_test_pkg.sv:67:    localparam int WIDTH = LP_BAR_WIDTH;
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:8:    WIDTH: int = 1
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:30:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:40:        obj = self.__class__()
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:45:        if not isinstance(other, single_ct):
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:50:    WIDTH: int = 3
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:94:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:104:        obj = self.__class__()
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:109:        if not isinstance(other, triple_ct):
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:114:    WIDTH: int = 8
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:213:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:223:        obj = self.__class__()
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:228:        if not isinstance(other, byte_ct):
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:233:    WIDTH: int = 9
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:343:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:353:        obj = self.__class__()
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:358:        if not isinstance(other, wide_ct):
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:363:    WIDTH: int = 33
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:737:        if not isinstance(data, (bytes, bytearray)):
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:747:        obj = self.__class__()
tests/goldens/gen/flags_basic/py/alpha/piketype/types_types.py:752:        if not isinstance(other, very_wide_ct):
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:9:    localparam int WIDTH = LP_COLOR_WIDTH;
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:29:      padded[WIDTH-1:0] = value;
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:44:      value = color_t'(padded[WIDTH-1:0]);
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:67:    localparam int WIDTH = LP_CMD_WIDTH;
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:87:      padded[WIDTH-1:0] = value;
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:102:      value = cmd_t'(padded[WIDTH-1:0]);
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:125:    localparam int WIDTH = LP_FLAG_WIDTH;
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:145:      padded[WIDTH-1:0] = value;
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:160:      value = flag_t'(padded[WIDTH-1:0]);
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:183:    localparam int WIDTH = LP_BIG_WIDTH;
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:203:      padded[WIDTH-1:0] = value;
tests/goldens/gen/enum_basic/sv/foo/piketype/defs_test_pkg.sv:218:      value = big_t'(padded[WIDTH-1:0]);
tests/goldens/gen/flags_basic/cpp/alpha/piketype/types_types.hpp:17:  static constexpr std::size_t WIDTH = 1;
tests/goldens/gen/flags_basic/cpp/alpha/piketype/types_types.hpp:61:  static constexpr std::size_t WIDTH = 3;
tests/goldens/gen/flags_basic/cpp/alpha/piketype/types_types.hpp:113:  static constexpr std::size_t WIDTH = 8;
tests/goldens/gen/flags_basic/cpp/alpha/piketype/types_types.hpp:185:  static constexpr std::size_t WIDTH = 9;
tests/goldens/gen/flags_basic/cpp/alpha/piketype/types_types.hpp:261:  static constexpr std::size_t WIDTH = 33;
tests/goldens/gen/flags_basic/sv/alpha/piketype/types_test_pkg.sv:9:    localparam int WIDTH = 1;
tests/goldens/gen/flags_basic/sv/alpha/piketype/types_test_pkg.sv:73:    localparam int WIDTH = 3;
tests/goldens/gen/flags_basic/sv/alpha/piketype/types_test_pkg.sv:153:    localparam int WIDTH = 8;
tests/goldens/gen/flags_basic/sv/alpha/piketype/types_test_pkg.sv:272:    localparam int WIDTH = 9;
tests/goldens/gen/flags_basic/sv/alpha/piketype/types_test_pkg.sv:400:    localparam int WIDTH = 33;

codex
I have enough to write the delta review. The revised spec resolves the prior blockers, but it introduces a real feasibility failure in the performance command and a lint-rule problem against existing generated SystemVerilog patterns.
exec
/bin/zsh -lc "sed -n '150,210p' tests/test_gen_const_sv.py" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,180p' src/piketype/discovery/scanner.py" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
"""Filesystem scanning for piketype modules."""

from __future__ import annotations

from pathlib import Path

from piketype.errors import PikeTypeError
from piketype.paths import GEN_DIRNAME


def is_under_piketype_dir(path: Path) -> bool:
    """Return whether the path lives under a directory named ``piketype``."""
    return "piketype" in path.parts


def ensure_cli_path_is_valid(path: Path) -> None:
    """Validate that the CLI path is a concrete DSL module path."""
    if path.suffix != ".py":
        raise PikeTypeError(f"expected a Python file path, got {path}")
    if path.name == "__init__.py":
        raise PikeTypeError(f"{path} is not a valid piketype module")
    if not is_under_piketype_dir(path):
        raise PikeTypeError(f"{path} is not under a piketype/ directory")


def find_piketype_modules(repo_root: Path) -> list[Path]:
    """Return all DSL module files under piketype/ directories."""
    return sorted(
        path
        for path in repo_root.rglob("*.py")
        if path.name != "__init__.py"
        and GEN_DIRNAME not in path.relative_to(repo_root).parts
        and is_under_piketype_dir(path.relative_to(repo_root))
    )

 succeeded in 0ms:
    def test_generates_nested_structs_in_sv(self) -> None:
        fixture_root = FIXTURES_DIR / "nested_struct_sv_basic" / "project"
        expected_root = GOLDENS_DIR / "nested_struct_sv_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"

            result = self.run_piketype(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_rejects_piketype_file_with_no_dsl_objects(self) -> None:
        fixture_root = FIXTURES_DIR / "no_dsl" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "empty.py"

            result = self.run_piketype(repo_dir, str(cli_file))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("defines no DSL objects", result.stderr)

    # -- New positive golden tests for byte-aligned padding --

    def test_generates_struct_padded(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_padded" / "project"
        expected_root = GOLDENS_DIR / "struct_padded"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_struct_signed(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_signed" / "project"
        expected_root = GOLDENS_DIR / "struct_signed"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_scalar_wide(self) -> None:
        fixture_root = FIXTURES_DIR / "scalar_wide" / "project"
        expected_root = GOLDENS_DIR / "scalar_wide"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_struct_wide(self) -> None:

exec
/bin/zsh -lc "rg -n \"piketype gen|run_gen\\(|main\\(\\[.*gen|subprocess.*gen|types\\.py\" tests src specs | head -n 120" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
tests/test_namespace_validation.py:177:        paths = [Path("alpha/piketype/types.py"), Path("beta/piketype/types.py")]
tests/test_namespace_validation.py:181:        self.assertIn("alpha/piketype/types.py", str(ctx.exception))
tests/test_namespace_validation.py:182:        self.assertIn("beta/piketype/types.py", str(ctx.exception))
tests/goldens/gen/namespace_override/piketype_manifest.json:32:        "py": "gen/py/alpha/piketype/constants_types.py",
tests/goldens/gen/namespace_override/piketype_manifest.json:67:        "py": "gen/py/beta/piketype/more_types.py",
src/piketype/commands/gen.py:21:def run_gen(path: str, *, namespace: str | None = None) -> None:
specs/008-enum-dsl-type/spec.md:180:**FR-30**: A test case class in `tests/` runs `piketype gen` on the fixture and compares output byte-for-byte against goldens.
specs/008-enum-dsl-type/spec.md:182:**FR-31**: Negative test cases verify that `piketype gen` fails with appropriate error messages for:
src/piketype/cli.py:39:                run_gen(args.path, namespace=args.namespace)
specs/008-enum-dsl-type/plan.md:207:**Checkpoint**: `basedpyright` passes, existing tests pass, can manually run `piketype gen` on a test fixture.
specs/008-enum-dsl-type/tasks.md:174:**Description**: Create `tests/fixtures/enum_basic/project/` with `.git/` marker and `foo/piketype/defs.py` containing four enums: `color_t` (explicit: RED=0, GREEN=5, BLUE=10), `cmd_t` (explicit width 8, NOP=0, READ=5, WRITE=6 auto, RESET=7 auto), `flag_t` (single value SET=0, width 1), `big_t` (SMALL=0, LARGE=2**63). Run `piketype gen` to generate outputs. Copy generated `gen/` tree to `tests/goldens/gen/enum_basic/`.
specs/008-enum-dsl-type/tasks.md:180:**Verification**: `piketype gen` succeeds on the fixture. Golden files exist and are byte-for-byte reproducible.
specs/008-enum-dsl-type/tasks.md:190:- **13 negative tests** (one per FR-31 case): empty enum, non-UPPER_CASE name, duplicate name, negative value, duplicate resolved values, name not `_t`, enumerator collides with constant, collides with other enum's enumerator, collides with generated SV identifier, width > 64, explicit width too small, explicit width < 1, explicit width > 64. Each creates a minimal fixture, runs `piketype gen`, asserts non-zero exit + expected error substring.
tests/goldens/gen/nested_struct_sv_basic/piketype_manifest.json:14:            "path": "alpha/piketype/types.py"
tests/goldens/gen/nested_struct_sv_basic/piketype_manifest.json:21:        "py": "gen/py/alpha/piketype/types_types.py",
tests/goldens/gen/nested_struct_sv_basic/piketype_manifest.json:31:      "repo_relative_path": "alpha/piketype/types.py",
tests/goldens/gen/nested_struct_sv_basic/piketype_manifest.json:35:        "path": "alpha/piketype/types.py"
tests/goldens/gen/nested_struct_sv_basic/piketype_manifest.json:46:            "path": "alpha/piketype/types.py"
tests/goldens/gen/nested_struct_sv_basic/piketype_manifest.json:58:            "path": "alpha/piketype/types.py"
tests/goldens/gen/nested_struct_sv_basic/piketype_manifest.json:69:            "path": "alpha/piketype/types.py"
tests/goldens/gen/nested_struct_sv_basic/piketype_manifest.json:79:            "path": "alpha/piketype/types.py"
src/piketype/paths.py:41:    return gen_root(repo_root=repo_root) / "py" / relative.parent / f"{relative.stem}_types.py"
tests/goldens/gen/struct_multiple_of/piketype_manifest.json:9:        "py": "gen/py/alpha/piketype/types_types.py",
tests/goldens/gen/struct_multiple_of/piketype_manifest.json:19:      "repo_relative_path": "alpha/piketype/types.py",
tests/goldens/gen/struct_multiple_of/piketype_manifest.json:23:        "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_multiple_of/piketype_manifest.json:33:            "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_multiple_of/piketype_manifest.json:43:            "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_multiple_of/piketype_manifest.json:53:            "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_multiple_of/piketype_manifest.json:63:            "path": "alpha/piketype/types.py"
tests/goldens/gen/scalar_wide/piketype_manifest.json:9:        "py": "gen/py/alpha/piketype/types_types.py",
tests/goldens/gen/scalar_wide/piketype_manifest.json:19:      "repo_relative_path": "alpha/piketype/types.py",
tests/goldens/gen/scalar_wide/piketype_manifest.json:23:        "path": "alpha/piketype/types.py"
tests/goldens/gen/scalar_wide/piketype_manifest.json:34:            "path": "alpha/piketype/types.py"
tests/goldens/gen/scalar_wide/piketype_manifest.json:46:            "path": "alpha/piketype/types.py"
tests/goldens/gen/scalar_wide/piketype_manifest.json:58:            "path": "alpha/piketype/types.py"
tests/test_struct_multiple_of.py:62:    """Run piketype gen on a fixture and return the gen/py root."""
tests/test_struct_multiple_of.py:66:    cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_struct_enum_member.py:37:    """Run piketype gen on a fixture and return the repo dir."""
tests/test_struct_enum_member.py:41:    cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_struct_enum_member.py:225:        """AC-20: piketype gen is idempotent."""
tests/test_struct_enum_member.py:233:        cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_struct_enum_member.py:336:            repo_relative_path="a/piketype/types.py",
tests/test_struct_enum_member.py:342:            repo_relative_path="b/piketype/types.py",
tests/test_struct_flags_member.py:24:    """Run piketype gen on a fixture and return the repo dir."""
tests/test_struct_flags_member.py:28:    cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_struct_flags_member.py:99:        """AC-21: piketype gen is idempotent."""
tests/test_struct_flags_member.py:107:        cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_flags.py:27:    """Run piketype gen on a fixture and return the repo dir."""
tests/test_gen_flags.py:31:    cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_flags.py:108:            repo_relative_path="alpha/piketype/types.py",
tests/test_gen_flags.py:213:        cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp:2:// Source: alpha/piketype/types.py
specs/005-flags-dsl-type/plan.md:137:**Files:** `tests/fixtures/flags_basic/project/alpha/typist/types.py` (NEW)
tests/goldens/gen/struct_multiple_of/cpp/alpha/piketype/types_types.hpp:2:// Source: alpha/piketype/types.py
tests/test_runtime_bytes.py:20:    """Run piketype gen on a fixture and return the gen/py root."""
tests/test_runtime_bytes.py:24:    cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:130:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:143:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:156:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:183:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:194:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:205:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:216:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:227:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:239:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:249:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:259:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/test_gen_const_sv.py:377:            (repo_dir / "alpha" / "piketype" / "types.py").write_text(
tests/test_gen_const_sv.py:380:            (repo_dir / "beta" / "piketype" / "types.py").write_text(
tests/test_gen_const_sv.py:383:            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
tests/goldens/gen/scalar_wide/cpp/alpha/piketype/types_types.hpp:2:// Source: alpha/piketype/types.py
tests/goldens/gen/struct_flags_member/piketype_manifest.json:9:        "py": "gen/py/alpha/piketype/types_types.py",
tests/goldens/gen/struct_flags_member/piketype_manifest.json:19:      "repo_relative_path": "alpha/piketype/types.py",
tests/goldens/gen/struct_flags_member/piketype_manifest.json:23:        "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_flags_member/piketype_manifest.json:38:            "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_flags_member/piketype_manifest.json:48:            "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_flags_member/piketype_manifest.json:58:            "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_multiple_of/sv/alpha/piketype/types_pkg.sv:2:// Source: alpha/piketype/types.py
tests/goldens/gen/const_expr_basic/piketype_manifest.json:65:        "py": "gen/py/alpha/piketype/constants_types.py",
tests/goldens/gen/struct_multiple_of/py/alpha/piketype/types_types.py:2:# Source: alpha/piketype/types.py
tests/goldens/gen/struct_multiple_of/sv/alpha/piketype/types_test_pkg.sv:2:// Source: alpha/piketype/types.py
tests/goldens/gen/nested_struct_sv_basic/py/alpha/piketype/types_types.py:2:# Source: alpha/piketype/types.py
tests/goldens/gen/scalar_sv_basic/piketype_manifest.json:14:            "path": "alpha/piketype/types.py"
tests/goldens/gen/scalar_sv_basic/piketype_manifest.json:21:        "py": "gen/py/alpha/piketype/types_types.py",
tests/goldens/gen/scalar_sv_basic/piketype_manifest.json:31:      "repo_relative_path": "alpha/piketype/types.py",
tests/goldens/gen/scalar_sv_basic/piketype_manifest.json:35:        "path": "alpha/piketype/types.py"
tests/goldens/gen/scalar_sv_basic/piketype_manifest.json:46:            "path": "alpha/piketype/types.py"
tests/goldens/gen/scalar_sv_basic/piketype_manifest.json:58:            "path": "alpha/piketype/types.py"
tests/goldens/gen/scalar_sv_basic/piketype_manifest.json:70:            "path": "alpha/piketype/types.py"
tests/goldens/gen/scalar_wide/py/alpha/piketype/types_types.py:2:# Source: alpha/piketype/types.py
tests/goldens/gen/struct_flags_member/cpp/alpha/piketype/types_types.hpp:2:// Source: alpha/piketype/types.py
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_pkg.sv:2:// Source: alpha/piketype/types.py
tests/goldens/gen/const_cpp_wide/piketype_manifest.json:32:        "py": "gen/py/alpha/piketype/constants_types.py",
tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_test_pkg.sv:2:// Source: alpha/piketype/types.py
tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:2:// Source: alpha/piketype/types.py
tests/goldens/gen/const_cpp_explicit_uint32/piketype_manifest.json:32:        "py": "gen/py/alpha/piketype/constants_types.py",
tests/goldens/gen/enum_basic/piketype_manifest.json:9:        "py": "gen/py/foo/piketype/defs_types.py",
tests/goldens/gen/struct_enum_member/piketype_manifest.json:9:        "py": "gen/py/alpha/piketype/types_types.py",
tests/goldens/gen/struct_enum_member/piketype_manifest.json:19:      "repo_relative_path": "alpha/piketype/types.py",
tests/goldens/gen/struct_enum_member/piketype_manifest.json:23:        "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_enum_member/piketype_manifest.json:33:            "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_enum_member/piketype_manifest.json:58:            "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_enum_member/piketype_manifest.json:68:            "path": "alpha/piketype/types.py"
tests/goldens/gen/struct_flags_member/py/alpha/piketype/types_types.py:2:# Source: alpha/piketype/types.py
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_pkg.sv:2:// Source: alpha/piketype/types.py
tests/goldens/gen/scalar_wide/sv/alpha/piketype/types_test_pkg.sv:2:// Source: alpha/piketype/types.py
tests/goldens/gen/struct_enum_member/cpp/alpha/piketype/types_types.hpp:2:// Source: alpha/piketype/types.py
tests/goldens/gen/scalar_sv_basic/py/alpha/piketype/types_types.py:2:# Source: alpha/piketype/types.py
specs/008-enum-dsl-type/artifacts/specification/iter3-forge.md:181:**FR-30**: A test case class in `tests/` runs `piketype gen` on the fixture and compares output byte-for-byte against goldens.
specs/008-enum-dsl-type/artifacts/specification/iter3-forge.md:183:**FR-31**: Negative test cases verify that `piketype gen` fails with appropriate error messages for:
tests/goldens/gen/struct_enum_member/py/alpha/piketype/types_types.py:2:# Source: alpha/piketype/types.py
tests/goldens/gen/struct_flags_member/sv/alpha/piketype/types_pkg.sv:2:// Source: alpha/piketype/types.py
specs/008-enum-dsl-type/artifacts/specification/iter2-forge.md:179:**FR-29**: A test case class in `tests/` runs `piketype gen` on the fixture and compares output byte-for-byte against goldens.
specs/008-enum-dsl-type/artifacts/specification/iter2-forge.md:181:**FR-30**: Negative test cases verify that `piketype gen` fails with appropriate error messages for:
tests/goldens/gen/struct_flags_member/sv/alpha/piketype/types_test_pkg.sv:2:// Source: alpha/piketype/types.py
tests/goldens/gen/const_sv_basic/piketype_manifest.json:32:        "py": "gen/py/alpha/piketype/constants_types.py",
tests/goldens/gen/const_sv_basic/piketype_manifest.json:67:        "py": "gen/py/beta/piketype/more_types.py",
tests/goldens/gen/struct_signed/piketype_manifest.json:9:        "py": "gen/py/alpha/piketype/types_types.py",
tests/goldens/gen/struct_signed/piketype_manifest.json:19:      "repo_relative_path": "alpha/piketype/types.py",
tests/goldens/gen/struct_signed/piketype_manifest.json:23:        "path": "alpha/piketype/types.py"

codex
Executive summary: Iteration 2 fixes the three prior blockers and most warnings. It still cannot be approved because the revised performance and wheel-install checks specify commands/paths that do not work in this repo, and the template lint rules would reject legitimate byte-preserving SystemVerilog template text.

Iteration-1 issue resolution:

1. Resolved — loader strategy ambiguity: FR-2, FR-3, FR-14, AC-F5 now select `PackageLoader` and wheel packaging.
2. Resolved — staged-vs-final AC split: FR-5 plus AC-1-`<lang>` through AC-7-`<lang>` and AC-F1 through AC-F8.
3. Resolved — view-model shape: FR-8, FR-9, AC-4-`<lang>` define nested frozen dataclasses and field types.
4. Resolved — nested templates packaging: FR-12 permits subdirectories; FR-14 uses `templates/**/*.j2`.
5. Partially resolved — performance testability: NFR-1 and AC-F4 add a fixture, command, and `perf.md`, but the specified command is invalid.
6. Partially resolved — grep audit concreteness: FR-21, AC-F3, AC-F7 add a script and patterns, but the patterns have false positives on legitimate output templates.
7. Resolved — NFR-5 vs FR-11: FR-11 and NFR-5 now define the two-level indirection bound.
8. Resolved — view-model tests: FR-18 and AC-6-`<lang>` name test files, fixtures, and minimum assertions.
9. Resolved — stale runtime Q-5: runtime remains OOS-2 and the old question is gone.
10. Resolved — subjective trivial/meaningful split: FR-6 now gives concrete examples.

New issues:

1. BLOCKING — NFR-1, AC-F4, AC-F5. The specified command imports nonexistent `piketype.commands.gen.gen_main`, passes unsupported `--repo`, and points at `tests/fixtures/struct_padded/project`, but current generation requires a concrete DSL file path such as `.../alpha/piketype/types.py`. Fix the spec to use a real command, preferably a temp-copy wrapper invoking `run_gen(<tmp>/project/alpha/piketype/types.py)` or `piketype gen <tmp>/project/alpha/piketype/types.py`, so validation does not dirty fixtures.

2. BLOCKING — FR-21, AC-F7, FR-7. The `WIDTH\s*[-+*/]` lint pattern conflicts with existing generated SystemVerilog that must remain byte-identical, e.g. `padded[WIDTH-1:0]` and loops from `WIDTH` to `BYTE_COUNT*8`. Raw-template regex lint must scan only Jinja expression/statement bodies, or these target-language expressions must be explicitly allowed.

3. WARNING — FR-8, FR-9, FR-15. FR-8 excludes `frozenset`, but FR-9 says to use `frozenset`/`tuple` instead of `set`/`dict`, and FR-15 warns against hash-dependent ordering. Remove `frozenset` from FR-9 and require sorted tuples for any collection whose order can affect output.

4. WARNING — FR-18, Q-3. FR-18 assumes `backends/<lang>/view.py` contains builders, while Q-3 still asks whether builders should live in `view.py` or `builder.py`. Decide this now or make FR-18 reference the chosen builder module generically.

VERDICT: REVISE
2026-04-29T09:51:16.596629Z ERROR codex_core::session: failed to record rollout items: thread 019dd8a4-ca9b-7471-9913-61cc661825ea not found
tokens used
69,969
Executive summary: Iteration 2 fixes the three prior blockers and most warnings. It still cannot be approved because the revised performance and wheel-install checks specify commands/paths that do not work in this repo, and the template lint rules would reject legitimate byte-preserving SystemVerilog template text.

Iteration-1 issue resolution:

1. Resolved — loader strategy ambiguity: FR-2, FR-3, FR-14, AC-F5 now select `PackageLoader` and wheel packaging.
2. Resolved — staged-vs-final AC split: FR-5 plus AC-1-`<lang>` through AC-7-`<lang>` and AC-F1 through AC-F8.
3. Resolved — view-model shape: FR-8, FR-9, AC-4-`<lang>` define nested frozen dataclasses and field types.
4. Resolved — nested templates packaging: FR-12 permits subdirectories; FR-14 uses `templates/**/*.j2`.
5. Partially resolved — performance testability: NFR-1 and AC-F4 add a fixture, command, and `perf.md`, but the specified command is invalid.
6. Partially resolved — grep audit concreteness: FR-21, AC-F3, AC-F7 add a script and patterns, but the patterns have false positives on legitimate output templates.
7. Resolved — NFR-5 vs FR-11: FR-11 and NFR-5 now define the two-level indirection bound.
8. Resolved — view-model tests: FR-18 and AC-6-`<lang>` name test files, fixtures, and minimum assertions.
9. Resolved — stale runtime Q-5: runtime remains OOS-2 and the old question is gone.
10. Resolved — subjective trivial/meaningful split: FR-6 now gives concrete examples.

New issues:

1. BLOCKING — NFR-1, AC-F4, AC-F5. The specified command imports nonexistent `piketype.commands.gen.gen_main`, passes unsupported `--repo`, and points at `tests/fixtures/struct_padded/project`, but current generation requires a concrete DSL file path such as `.../alpha/piketype/types.py`. Fix the spec to use a real command, preferably a temp-copy wrapper invoking `run_gen(<tmp>/project/alpha/piketype/types.py)` or `piketype gen <tmp>/project/alpha/piketype/types.py`, so validation does not dirty fixtures.

2. BLOCKING — FR-21, AC-F7, FR-7. The `WIDTH\s*[-+*/]` lint pattern conflicts with existing generated SystemVerilog that must remain byte-identical, e.g. `padded[WIDTH-1:0]` and loops from `WIDTH` to `BYTE_COUNT*8`. Raw-template regex lint must scan only Jinja expression/statement bodies, or these target-language expressions must be explicitly allowed.

3. WARNING — FR-8, FR-9, FR-15. FR-8 excludes `frozenset`, but FR-9 says to use `frozenset`/`tuple` instead of `set`/`dict`, and FR-15 warns against hash-dependent ordering. Remove `frozenset` from FR-9 and require sorted tuples for any collection whose order can affect output.

4. WARNING — FR-18, Q-3. FR-18 assumes `backends/<lang>/view.py` contains builders, while Q-3 still asks whether builders should live in `view.py` or `builder.py`. Decide this now or make FR-18 reference the chosen builder module generically.

VERDICT: REVISE
