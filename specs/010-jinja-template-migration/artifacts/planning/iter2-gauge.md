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
session id: 019dd8f6-d294-7bd1-aef9-7cc3326aacd2
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/planning/iter2-gauge-prompt.md
codex
I’ll read the referenced planning prompt first, then gather only the repository context it asks for before acting.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/planning/iter2-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Planning Iteration 2

This is **iteration 2** of the planning stage. Iteration 1 returned `VERDICT: REVISE` with 5 BLOCKING and 3 WARNING issues:

1. BLOCKING — Phase 1-3 commits ordered by type family, not FR-6 sub-step.
2. BLOCKING — Python view-model sketch incomplete; FlagsFieldView referenced but not defined.
3. BLOCKING — C++ plan precomputed full pack/unpack helper bodies in Python (violates FR-10/NFR-5).
4. BLOCKING — C++/SV view sketches were "same shape as Phase 1", not actionable.
5. BLOCKING — Byte-parity strategy underspecified for intermediate commits.
6. WARNING — Phase 0 wheel-packaging smoke test before any .j2 file exists is meaningless.
7. WARNING — Risk register missed Jinja trim/lstrip and frozen-IR construction.
8. WARNING — `make_environment` env options + keyword-only signature not pinned.
9. NOTE — C++ `--namespace` override.

## Inputs to Review

1. **Implementation plan:** `specs/010-jinja-template-migration/plan.md` (iteration 2).
2. **Specification (binding):** `specs/010-jinja-template-migration/spec.md`.
3. **Iteration-1 review:** `specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md`.

## Review Instructions

1. **Did each iter1 issue get resolved?** For each numbered item above, state whether it is resolved, partially resolved, or not resolved, citing the relevant section of plan.md (Phase X commit Y, view-model dataclass name, risk register row, etc.).

2. **Look for new issues introduced by iter2.** In particular:
   - Does the new `body_lines: tuple[str, ...] | None` passthrough mechanism violate FR-8/FR-9 (it's a primitive `tuple` of `str`, so it should comply, but verify)?
   - Does the FR-6 sub-step commit ordering still preserve byte parity at every commit? Walk through Phase 1 commits 2–6 and confirm each one's parity claim is consistent with how the view + template + legacy fragment interact.
   - Are the Python/C++/SV view-model dataclass sketches now complete enough that an implementer can build them without deriving missing primitives? Spot-check against the actual current emitter helpers:
     - `_render_py_enum` → `EnumView` should carry `mask`, `first_member_name`, `enum_class_name`, `width`, `byte_count`.
     - `_render_py_flags` → `FlagsView` should carry `data_mask`, `total_bits`, plus per-flag `bit_mask`.
     - `_render_py_struct_field_coercer` → `StructFieldView` discriminators must distinguish struct-ref / flags-ref / enum-ref / scalar-ref / narrow-scalar / wide-scalar.
     - `_render_cpp_*` → similar coverage.
     - `_render_sv_*` synth and test split with helper-class fields.

3. **Phase 4 wheel check.** Does the AC-F5 description correctly diff "every .j2 in source" against "every .j2 in the wheel" without hardcoding a count? Verify.

4. **Risk register.** Are the two added risks (Jinja trim/lstrip, frozen-IR construction) concrete enough? Confirm.

5. **Constitution alignment.** Same checks as iter1.

## Output Format

- Executive summary (2-4 sentences).
- Iter1 issue resolution table.
- New issues with severity tags.
- `VERDICT: APPROVE` or `VERDICT: REVISE` on the final line. No text after.

Bias toward APPROVE when no BLOCKING remains and the plan is concretely actionable.

codex
I’m using the Steel-Kit planning workflow because this is a Gauge review of a planning iteration. Next I’m reading the binding spec, the iter2 plan, the prior review, and the current emitter helpers called out by the prompt.
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' /Users/ezchi/Projects/pike-type/.agents/skills/steel-plan/SKILL.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Implementation Plan — Jinja Template Migration

**Spec ID:** 010-jinja-template-migration
**Branch:** feature/010-jinja-template-migration
**Stage:** planning

This plan executes spec.md (post-clarification, FR-1..FR-25, CL-1..CL-4, AC-*-Py/Cpp/Sv, AC-F1..F8). It is organized as five phases: shared infrastructure → Python backend → C++ backend → SystemVerilog backend → final validation. Each phase is a contiguous sequence of commits on `feature/010-jinja-template-migration`.

---

## Architectural overview

```
IR (frozen)                                    Templates (per backend)
   │                                                  ▲
   ▼                                                  │
build_module_view(module: ModuleIR, type_index)  env.get_template(...).render(view)
   │                                                  ▲
   ▼                                                  │
ModuleView (frozen dataclass)  ───────────────────────┘

emit_<lang>(repo) {
    env = make_environment(package="piketype.backends.<lang>")
    for module in repo.modules:
        view  = build_module_view(module=module, ...)
        text  = render(env=env, template_name="module.j2", context=view)
        write(path, text)
}
```

**Key invariants** (all enforced by AC-* gates):
- View models are read-only frozen dataclasses with primitive fields (`int`, `str`, `bool`, `bytes`), `tuple` of view-model field types, or other view-model dataclass instances (FR-8). No `set`/`frozenset`/`dict`/IR-references/callables (FR-9).
- Templates contain no semantics (FR-10), enforced by `tools/check_templates.py` (FR-21).
- `render` returns a string ending in `\n` (FR-3).
- `emit_<lang>` signature unchanged (FR-4, NFR-7).
- Output is byte-for-byte identical at each per-backend completion (FR-7); intermediate commits within a phase target byte parity by use of an **InlineFragmentView passthrough** mechanism described below.
- All custom Jinja filters/globals registered exclusively in `backends/common/render.py` (CL-2, FR-16).

### InlineFragmentView passthrough — byte-parity strategy

Each Phase 1/2/3 sub-step commit replaces one slice of the inline emitter with a template, while remaining slices continue to render via the legacy inline path. The plan keeps byte parity at every commit by passing the not-yet-migrated slices through to the template as **already-rendered strings**.

Concrete mechanism:
- `ModuleView` carries a field `body_lines: tuple[str, ...] | None`. When non-None, the primary template emits `{{ body_lines | join("\n") }}` for the not-yet-templated portion.
- Each sub-step replaces a portion of `body_lines` with a structured field (`types: tuple[TypeView, ...]`, etc.), and the template's body section transitions from `{% if body_lines %}{{ body_lines | join("\n") }}{% endif %}` to a structured loop over `types`.
- After sub-step 4 (fragments), `body_lines` is unused and removed from the view; the field is retired in the cleanup commit.

This is internal scaffolding strictly contained inside view + template; it does not leak to the public emit API and does not survive into the post-cleanup state.

---

## Phase 0 — Shared infrastructure

**Goal:** Land everything that must exist before the first backend migration. After this phase, the repository builds, all existing tests pass, and the new tools are runnable. No emitter changes yet.

**Files:**

| Path                                                            | Action  | Purpose |
|-----------------------------------------------------------------|---------|---------|
| `src/piketype/backends/common/render.py`                        | rewrite | `make_environment(*, package: str) -> jinja2.Environment` and `render(*, env: jinja2.Environment, template_name: str, context: object) -> str`. Custom-filter registration site (CL-2/FR-16). |
| `tools/check_templates.py`                                      | new     | Template-hygiene lint (FR-21). |
| `tests/test_check_templates.py`                                 | new     | Lint script unit tests (FR-21 last paragraph). |
| `tests/test_render.py`                                          | new     | `make_environment` / `render` smoke tests; placeholder for future custom-filter tests (CL-2). |
| `tools/perf_bench.py`                                           | new     | Benchmark CLI (FR-23). |
| `pyproject.toml`                                                | edit    | `[tool.setuptools.package-data]` recursive globs `templates/**/*.j2` for `piketype.backends.{py,cpp,sv}` (FR-14). |
| `MANIFEST.in`                                                   | new/edit| Include rule mirroring FR-14 (defensive, sdist-friendly). |
| `docs/templates.md`                                             | new     | FR-22 + FR-24 sections. |
| `specs/010-jinja-template-migration/perf.md`                    | new     | Pre-migration `baseline_ms` row (CL-4, FR-25). Captured *after* commits 1–5 are merged but *before* any backend migration. |
| (no template directories yet)                                   | n/a     | Empty `templates/` dirs are deferred to Phase 1/2/3 — they are created when their first `.j2` file lands, so the wheel build never tries to package an empty directory. |

**`backends/common/render.py` exact contract:**

```python
"""Template rendering helpers for piketype backends."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING

import jinja2

if TYPE_CHECKING:
    pass


def make_environment(*, package: str) -> jinja2.Environment:
    """Construct the per-call Jinja environment for a backend package."""
    return jinja2.Environment(
        loader=jinja2.PackageLoader(package, "templates"),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=jinja2.StrictUndefined,
        autoescape=False,
    )


def render(*, env: jinja2.Environment, template_name: str, context: object) -> str:
    """Render a template against a view-model dataclass instance."""
    if is_dataclass(context):
        ctx = asdict(context)
    elif isinstance(context, dict):
        ctx = context
    else:
        raise TypeError(f"render context must be a dataclass or dict, got {type(context).__name__}")
    output = env.get_template(template_name).render(**ctx)
    if not output.endswith("\n"):
        output += "\n"
    return output


# Custom filters/globals — single auditable site (CL-2, FR-16).
# Registered by mutating the env returned from make_environment via a hook
# in this module if/when filters are introduced. Empty for now; each
# addition documented in docs/templates.md "Custom Filters".
```

**Commit sequence (Phase 0):**

1. `feat(common): add make_environment and render helpers` — `render.py` + `tests/test_render.py`.
2. `feat(tools): add check_templates lint script` — `tools/check_templates.py` + `tests/test_check_templates.py`. Lint patterns from FR-21 implemented; tests use `unittest.TestCase` with in-memory template strings (one positive case per pattern, one negative case showing target-language text outside Jinja blocks is not flagged).
3. `feat(tools): add perf_bench CLI` — `tools/perf_bench.py` per FR-23 (median over ≥5 runs against `tests/fixtures/struct_padded`).
4. `feat(build): package backend templates with the wheel` — `pyproject.toml` + `MANIFEST.in`. **No template directories created yet.** Wheel package-data globs are configured but match zero files at this point; the build still succeeds.
5. `docs(templates): add developer-facing architecture doc` — `docs/templates.md` covering FR-22 + FR-24.
6. `steel(perf): capture pre-migration baseline_ms` — runs `tools/perf_bench.py` and writes `specs/010-.../perf.md` with the baseline row only (CL-4).

**Phase 0 gates:**
- `python -m unittest discover tests` passes.
- `python tools/check_templates.py` exits 0 (no templates to scan).
- `python tools/perf_bench.py` produces `<fixture>\t<median_ms>\t<min_ms>\t<max_ms>\n`.
- `basedpyright --strict src/ tools/` passes.
- `pip wheel . -w /tmp/pike_wheel_ph0/ --no-deps` succeeds (wheel will not contain any `.j2` yet — packaging proof is deferred to Phase 1's first template-landing commit).

---

## Phase 1 — Python backend migration

**Why first:** Per FR-5/CL-1, Python is the simplest target (no `#include`/preprocessor, no SV `_pkg`/`_test_pkg` split). It validates the migration mechanics on the easiest case before C++/SV.

**Sub-step ordering follows FR-6 verbatim:**

1. Module/file-level skeleton (header, top-level imports, footer).
2. Top-level type declaration skeletons (class scaffolding for `ScalarAlias`, `Struct`, `Enum`, `Flags`).
3. Repeated helper-method skeletons (`__init__`, `to_bytes`, `from_bytes`, `_to_packed_int`, `_from_packed_int`, `clone`, `__eq__`, `__repr__`, struct field coercers, struct `__setattr__`).
4. Expression and field-level fragments (constants, struct field annotations/defaults, enum member values, flag mask literals).

**Files:**

| Path                                              | Action  | Purpose |
|---------------------------------------------------|---------|---------|
| `src/piketype/backends/py/view.py`                | new     | View-model dataclasses + `build_*` functions (FR-1/8/18). |
| `src/piketype/backends/py/templates/module.j2`    | new     | Primary module template (FR-12). |
| `src/piketype/backends/py/templates/_macros.j2`   | new     | Shared macros invoked from `module.j2`. |
| `src/piketype/backends/py/emitter.py`             | rewrite | Shrink to: build view → render → write. Remove `_render_*` helpers (FR-19). |
| `tests/test_view_py.py`                           | new     | View-model tests against `struct_padded`, `scalar_wide`, `enum_basic` (FR-18). |
| `specs/010-.../perf.md`                           | append  | `py-complete` row (FR-25). |

**Concrete view-model dataclasses (Python backend):**

```python
@dataclass(frozen=True, slots=True)
class ConstantView:
    name: str
    value_expr: str               # pre-rendered Python expression, e.g. "(1 << 32)" or "MAX_VALUE"

@dataclass(frozen=True, slots=True)
class ScalarAliasView:
    class_name: str               # e.g. "addr_ct"
    width: int
    signed: bool
    byte_count: int
    is_wide: bool                 # width > 64
    min_value: int
    max_value: int
    mask: int                     # 0 if width > 64
    sign_bit: int                 # 0 if not signed; (1 << (width-1)) otherwise
    pad_bits: int                 # byte_count*8 - width (for signed narrow)
    msb_byte_mask: int            # (1 << (width % 8)) - 1 if width % 8 else 0xFF (for wide)

@dataclass(frozen=True, slots=True)
class EnumMemberView:
    name: str
    resolved_value_expr: str      # pre-rendered, e.g. "0", "16"

@dataclass(frozen=True, slots=True)
class EnumView:
    class_name: str               # wrapper class, e.g. "color_ct"
    enum_class_name: str          # IntEnum subclass, e.g. "color_enum_t"
    width: int
    byte_count: int
    mask: int                     # (1 << width) - 1
    first_member_name: str        # for default arg
    members: tuple[EnumMemberView, ...]  # declaration order

@dataclass(frozen=True, slots=True)
class FlagFieldView:
    name: str
    bit_mask: int                 # 1 << (total_bits - 1 - index)

@dataclass(frozen=True, slots=True)
class FlagsView:
    class_name: str
    num_flags: int                # WIDTH
    byte_count: int               # BYTE_COUNT
    total_bits: int               # byte_count * 8
    data_mask: int                # ((1 << num_flags) - 1) << alignment_bits
    fields: tuple[FlagFieldView, ...]

# Struct field discriminators precompute every branch of the current
# match-case in _render_py_struct_*. The template selects on these
# booleans; it never inspects target_kind by string.

@dataclass(frozen=True, slots=True)
class StructFieldView:
    name: str
    annotation: str               # pre-rendered "int", "bytes", "addr_ct | None"
    default_expr: str             # pre-rendered "0", 'b"\\x00" * 4', "field(default_factory=foo_ct)"
    byte_count: int               # field_byte_count
    pack_bits: int                # byte_count * 8 (precomputed; FR-10 forbids template arithmetic on this)
    # discriminators (exactly one is True)
    is_struct_ref: bool           # TypeRef → StructIR
    is_flags_ref: bool            # TypeRef → FlagsIR
    is_enum_ref: bool             # TypeRef → EnumIR
    is_scalar_ref: bool           # TypeRef → ScalarAliasIR
    is_narrow_scalar: bool        # ScalarTypeSpec, width <= 64
    is_wide_scalar: bool          # ScalarTypeSpec, width > 64
    target_class: str             # _type_class_name of referenced type (empty if scalar spec)
    # numeric primitives for coercion / pack / unpack rendering
    width: int                    # data width in bits (0 for struct/flags/enum refs)
    signed: bool
    min_value: int
    max_value: int
    mask: int                     # (1 << width) - 1 for narrow scalar; 0 otherwise
    sign_bit_value: int           # 1 << (width-1) for signed narrow; 0 otherwise
    pad_bits: int                 # pack_bits - width (signed narrow); 0 otherwise
    msb_byte_mask: int            # for wide scalar tail mask

@dataclass(frozen=True, slots=True)
class StructView:
    class_name: str
    width: int                    # data width
    byte_count: int               # includes alignment
    alignment_bytes: int
    fields: tuple[StructFieldView, ...]
    has_struct_field: bool        # at least one field is_struct_ref → controls "if is None: raise" emission

# Top-level union of type kinds.
type TypeView = ScalarAliasView | StructView | EnumView | FlagsView

@dataclass(frozen=True, slots=True)
class ModuleView:
    header: str                                  # full pre-rendered header line (FR-13)
    has_types: bool
    has_structs: bool
    has_enums: bool
    has_flags: bool
    constants: tuple[ConstantView, ...]
    types: tuple[TypeView, ...]
    # Transitional passthrough: non-None during sub-steps 1–3, retired at sub-step 4.
    body_lines: tuple[str, ...] | None

 succeeded in 0ms:
---
name: steel-plan
description: "Steel-Kit workflow skill: Generate an implementation plan using the Forge-Gauge loop."
---

# steel-plan

Use this skill when the user invokes `/steel-plan` or asks to run the corresponding Steel-Kit workflow step.

Generate an implementation plan using the Forge-Gauge loop.

## Prerequisites
- `.steel/constitution.md` must contain a real project constitution, not the placeholder template
- `.steel/state.json` currentStage must be `planning`

## Steps

0. Run `/clear` to clear the conversation context before starting this stage.

1. Read `.steel/state.json` and `.steel/config.json`. Verify stage is `planning`.

2. Read `specs/<specId>/spec.md`, `specs/<specId>/clarifications.md` (if exists), and `.steel/constitution.md`.

3. **FORGE-GAUGE LOOP** (max iterations from config):

   ### Forge Phase (you are the Forge)
   a. Create a technical implementation plan covering:
      - Architecture Overview
      - Components (responsibilities, interfaces, dependencies)
      - Data Model
      - API Design
      - Dependencies (external libraries/tools)
      - Implementation Strategy (phased approach)
      - Risks and Mitigations
      - Testing Strategy

      **The Project Constitution is the highest authority.** If prior Gauge feedback contradicts the constitution, IGNORE that feedback. Do not blindly accept all suggestions.

   b. Write the plan to `specs/<specId>/plan.md`
   c. Save a copy to `specs/<specId>/artifacts/planning/iterN-forge.md`
   d. Git commit: `forge(planning): iteration N output [iteration N]`

   ### Gauge Phase
   e. Call the Gauge LLM (per config) to review the plan. **IMPORTANT: Run the command from the project's working directory, NOT /tmp.**
      - Write the full review prompt to a file at `specs/<specId>/artifacts/planning/iterN-gauge-prompt.md`
      - If gauge is `gemini`: run `gemini "Read and follow the instructions in <absolute-path-to-prompt-file>"` in the current project directory
      - If gauge is `codex`: run `codex exec "Read and follow the instructions in <absolute-path-to-prompt-file>"` in the current project directory
      - If gauge is `claude`: Review critically yourself as the Gauge role.

      Review criteria: spec coverage, architecture soundness, simplicity, risk assessment, testing strategy, alignment with constitution. End with `VERDICT: APPROVE` or `VERDICT: REVISE`.

   f. Save review to `specs/<specId>/artifacts/planning/iterN-gauge.md`
   g. Git commit: `gauge(planning): iteration N review — <verdict> [iteration N]`

   h. If **APPROVE**: break loop. If **REVISE**: critically evaluate feedback against constitution, incorporate valid points, and loop.

4. Auto-advance to `task_breakdown` stage. **No human approval needed here.**

5. Update `.steel/state.json`, tag `steel/<specId>/planning-complete`.

6. **Track skills used**: Update `.steel/state.json` field `skillsUsed.planning` with an array of skill names you invoked during this stage. If no skills were used, set it to `[]`.

7. Tell the user: "Plan complete. Run `/steel-tasks` to break down tasks."


exec
/bin/zsh -lc "sed -n '1,280p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
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
- **FR-24.** `docs/templates.md` SHALL include a "Custom Filters" section. Each filter added during migration SHALL be appended to that section with: name, signature, deterministic guarantee, and test file location. The registered location is fixed by CL-2 / FR-16 as `backends/common/render.py` and SHALL NOT be a documented variable per filter.
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
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md" in /Users/ezchi/Projects/pike-type
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
session id: 019dd8f0-6ea2-7120-93d7-de8867b3b637
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/planning/iter1-gauge-prompt.md
codex
I’ll read the referenced prompt first, then I’ll execute exactly what it asks in the current repo context.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/planning/iter1-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Planning Iteration 1

You are the **Gauge** in a dual-agent Forge-Gauge loop. The clarification stage produced an APPROVED, fully resolved spec. This is the planning stage: the Forge has produced an implementation plan at `specs/010-jinja-template-migration/plan.md`.

## Inputs to Review

1. **Implementation plan:** `specs/010-jinja-template-migration/plan.md`.
2. **Specification (binding):** `specs/010-jinja-template-migration/spec.md`.
3. **Project Constitution:** `.steel/constitution.md`.
4. **Repository state:** the `pike-type` project root. You may inspect files to validate concrete claims (CLI signatures, current emitter sizes, fixture paths).

## Review Instructions

Evaluate the plan on these dimensions:

1. **Spec coverage.** Does every FR (FR-1..FR-25), every NFR (NFR-1..NFR-7), every per-backend AC (AC-*-Py/Cpp/Sv), every feature-final AC (AC-F1..F8), and every CL (CL-1..CL-4) map to a concrete phase/commit in the plan? Flag any spec requirement with no implementation step.

2. **Phase ordering and dependencies.** Is the dependency chain correct (Phase 0 before any backend migration; Phase 1 → 2 → 3; Phase 4 last)? Is anything in the wrong phase?

3. **Concrete actionability.** For each commit in each phase, is the commit's content described well enough that an implementer can execute it without re-deriving design decisions?

4. **View-model shape correctness.**
   - Does the sketched Python `ScalarAliasView` / `StructFieldView` / `StructView` carry every field that the current `_render_py_*` functions actually use? Spot-check against `src/piketype/backends/py/emitter.py`. Look especially at: signed sign-extension fields, wide-scalar MSB byte mask, struct alignment bytes, struct field byte_count, struct field default expression.
   - Does C++/SV need any additional view fields the plan does not mention? (e.g., C++ namespace nesting strings, include guard symbols, SV `_pkg`/`_test_pkg` distinction.)

5. **Byte-parity strategy.** Is the plan's claim that each Phase 1/2/3 commit produces byte-identical output to the previous commit credible? In particular:
   - Phase 1 commits 2–5 each migrate a slice of rendering. Is the commit-by-commit mechanism (e.g., "add template that renders header + imports + footer; rest of body still inline") feasible without intermediate byte-diff?
   - If not, the plan must say so and propose an alternative (e.g., "commits 2–5 are internal refactor commits whose byte parity is checked only at the end of Phase 1").

6. **Risk register completeness.** Are there obvious risks the register misses? Specifically:
   - Wheel-build environments that strip empty directories (the plan mentions `.gitkeep`).
   - Jinja's auto-trimming interacting with raw-string blocks in templates.
   - View-model construction order vs. IR `frozen=True` semantics.
   - C++ `namespace` rendering depending on `--namespace` CLI override.

7. **Constitution alignment.** The plan should respect:
   - Principle 2 (immutable boundaries IR → backend): view models clean-break IR? Yes per FR-9; verify.
   - Principle 5 (template-first): every backend has templates per FR-12? Yes per plan; verify.
   - Coding standards: frozen dataclasses (FR-1), `from __future__ import annotations`, snake_case, no wildcard imports.
   - "Adding a new type or feature" workflow: not directly relevant since this is structural, but the plan should not break that workflow for future contributors.

## Output Format

- Executive summary (2–4 sentences).
- Numbered issue list with severity (`BLOCKING`/`WARNING`/`NOTE`), the FR/AC/phase/commit identifier, the problem, and a suggested fix.
- Final line: exactly `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after.

A plan can be APPROVED with open `WARNING`/`NOTE` items as long as no `BLOCKING` issue remains.

codex
This is a Gauge review for the Steel planning stage. I’m going to use the local `steel-plan` workflow instructions, then cross-check the plan against the binding spec and current emitters.
exec
/bin/zsh -lc "sed -n '1,260p' /Users/ezchi/Projects/pike-type/.agents/skills/steel-plan/SKILL.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
---
name: steel-plan
description: "Steel-Kit workflow skill: Generate an implementation plan using the Forge-Gauge loop."
---

# steel-plan

Use this skill when the user invokes `/steel-plan` or asks to run the corresponding Steel-Kit workflow step.

Generate an implementation plan using the Forge-Gauge loop.

## Prerequisites
- `.steel/constitution.md` must contain a real project constitution, not the placeholder template
- `.steel/state.json` currentStage must be `planning`

## Steps

0. Run `/clear` to clear the conversation context before starting this stage.

1. Read `.steel/state.json` and `.steel/config.json`. Verify stage is `planning`.

2. Read `specs/<specId>/spec.md`, `specs/<specId>/clarifications.md` (if exists), and `.steel/constitution.md`.

3. **FORGE-GAUGE LOOP** (max iterations from config):

   ### Forge Phase (you are the Forge)
   a. Create a technical implementation plan covering:
      - Architecture Overview
      - Components (responsibilities, interfaces, dependencies)
      - Data Model
      - API Design
      - Dependencies (external libraries/tools)
      - Implementation Strategy (phased approach)
      - Risks and Mitigations
      - Testing Strategy

      **The Project Constitution is the highest authority.** If prior Gauge feedback contradicts the constitution, IGNORE that feedback. Do not blindly accept all suggestions.

   b. Write the plan to `specs/<specId>/plan.md`
   c. Save a copy to `specs/<specId>/artifacts/planning/iterN-forge.md`
   d. Git commit: `forge(planning): iteration N output [iteration N]`

   ### Gauge Phase
   e. Call the Gauge LLM (per config) to review the plan. **IMPORTANT: Run the command from the project's working directory, NOT /tmp.**
      - Write the full review prompt to a file at `specs/<specId>/artifacts/planning/iterN-gauge-prompt.md`
      - If gauge is `gemini`: run `gemini "Read and follow the instructions in <absolute-path-to-prompt-file>"` in the current project directory
      - If gauge is `codex`: run `codex exec "Read and follow the instructions in <absolute-path-to-prompt-file>"` in the current project directory
      - If gauge is `claude`: Review critically yourself as the Gauge role.

      Review criteria: spec coverage, architecture soundness, simplicity, risk assessment, testing strategy, alignment with constitution. End with `VERDICT: APPROVE` or `VERDICT: REVISE`.

   f. Save review to `specs/<specId>/artifacts/planning/iterN-gauge.md`
   g. Git commit: `gauge(planning): iteration N review — <verdict> [iteration N]`

   h. If **APPROVE**: break loop. If **REVISE**: critically evaluate feedback against constitution, incorporate valid points, and loop.

4. Auto-advance to `task_breakdown` stage. **No human approval needed here.**

5. Update `.steel/state.json`, tag `steel/<specId>/planning-complete`.

6. **Track skills used**: Update `.steel/state.json` field `skillsUsed.planning` with an array of skill names you invoked during this stage. If no skills were used, set it to `[]`.

7. Tell the user: "Plan complete. Run `/steel-tasks` to break down tasks."


codex
I’ve confirmed the skill instructions; this turn is the Gauge phase only, not a full planning-stage automation run. Next I’m reading the plan, spec, constitution, and backend emitters to verify the plan’s claims instead of reviewing it abstractly.
exec
/bin/zsh -lc "sed -n '1,320p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' .steel/constitution.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
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
/bin/zsh -lc 'rg -n "def _render_(py|cpp|sv)|class .*View|EnumView|FlagsView|StructFieldView|body_lines|make_environment|namespace" -S .' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
./src/piketype/dsl/freeze.py:67:            namespace_parts=tuple(relative_path.with_suffix("").parts),
./src/piketype/commands/gen.py:18:from piketype.validate.namespace import check_duplicate_basenames, validate_cpp_namespace
./src/piketype/commands/gen.py:21:def run_gen(path: str, *, namespace: str | None = None) -> None:
./src/piketype/commands/gen.py:23:    if namespace is not None:
./src/piketype/commands/gen.py:24:        validate_cpp_namespace(namespace)
./src/piketype/commands/gen.py:31:    if namespace is not None:
./src/piketype/commands/gen.py:66:    emit_cpp(repo, namespace=namespace)
./src/piketype/cli.py:21:    gen_parser.add_argument("--namespace", default=None)
./src/piketype/cli.py:39:                run_gen(args.path, namespace=args.namespace)
./src/piketype/manifest/write_json.py:78:                "namespace_parts": list(module.ref.namespace_parts),
./src/piketype/ir/nodes.py:33:    namespace_parts: tuple[str, ...]
./src/piketype/backends/cpp/emitter.py:32:def emit_cpp(repo: RepoIR, *, namespace: str | None = None) -> list[Path]:
./src/piketype/backends/cpp/emitter.py:42:        output_path.write_text(render_module_hpp(module, namespace=namespace), encoding="utf-8")
./src/piketype/backends/cpp/emitter.py:47:def render_module_hpp(module: ModuleIR, *, namespace: str | None = None) -> str:
./src/piketype/backends/cpp/emitter.py:50:    if namespace is not None:
./src/piketype/backends/cpp/emitter.py:51:        guard = f"{namespace.replace('::', '_')}_{module.ref.basename}_types_hpp".upper()
./src/piketype/backends/cpp/emitter.py:52:        ns = f"{namespace}::{module.ref.basename}"
./src/piketype/backends/cpp/emitter.py:54:        guard = "_".join((*module.ref.namespace_parts, "types_hpp")).upper().replace(".", "_")
./src/piketype/backends/cpp/emitter.py:55:        ns = "::".join(part for part in module.ref.namespace_parts if part != "piketype")
./src/piketype/backends/cpp/emitter.py:58:    body_lines = [f"#ifndef {guard}", f"#define {guard}", "", "#include <cstdint>"]
./src/piketype/backends/cpp/emitter.py:60:        body_lines.extend(["#include <cstddef>", "#include <stdexcept>", "#include <vector>"])
./src/piketype/backends/cpp/emitter.py:61:    body_lines.append("")
./src/piketype/backends/cpp/emitter.py:63:        body_lines.append(f"namespace {ns} {{")
./src/piketype/backends/cpp/emitter.py:64:        body_lines.append("")
./src/piketype/backends/cpp/emitter.py:75:        body_lines.append(f"constexpr {cpp_type} {const.name} = {cpp_expr};")
./src/piketype/backends/cpp/emitter.py:77:        body_lines.append("")
./src/piketype/backends/cpp/emitter.py:80:            body_lines.append("")
./src/piketype/backends/cpp/emitter.py:82:            body_lines.extend(_render_cpp_scalar_alias(type_ir=type_ir))
./src/piketype/backends/cpp/emitter.py:84:            body_lines.extend(_render_cpp_struct(type_ir=type_ir, type_index=type_index))
./src/piketype/backends/cpp/emitter.py:86:            body_lines.extend(_render_cpp_flags(type_ir=type_ir))
./src/piketype/backends/cpp/emitter.py:88:            body_lines.extend(_render_cpp_enum(type_ir=type_ir))
./src/piketype/backends/cpp/emitter.py:90:        body_lines.append("")
./src/piketype/backends/cpp/emitter.py:91:        body_lines.append(f"}}  // namespace {ns}")
./src/piketype/backends/cpp/emitter.py:92:    body_lines.extend(["", f"#endif  // {guard}"])
./src/piketype/backends/cpp/emitter.py:93:    return f"{header}\n" + "\n".join(body_lines) + "\n"
./src/piketype/backends/cpp/emitter.py:96:def _render_cpp_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
./src/piketype/backends/cpp/emitter.py:109:def _render_cpp_expr(*, expr: ExprIR) -> str:
./src/piketype/backends/cpp/emitter.py:129:def _render_cpp_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
./src/piketype/backends/cpp/emitter.py:347:def _render_cpp_enum(*, type_ir: EnumIR) -> list[str]:
./src/piketype/backends/cpp/emitter.py:428:def _render_cpp_flags(*, type_ir: FlagsIR) -> list[str]:
./src/piketype/backends/cpp/emitter.py:547:def _render_cpp_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./src/piketype/backends/cpp/emitter.py:637:def _render_cpp_field_decl(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./src/piketype/backends/cpp/emitter.py:644:def _render_cpp_field_type(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./src/piketype/backends/cpp/emitter.py:657:def _render_cpp_field_default(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./src/piketype/backends/cpp/emitter.py:676:def _render_cpp_struct_pack_step(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./src/piketype/backends/cpp/emitter.py:724:def _render_cpp_struct_unpack_step(
./src/piketype/backends/cpp/emitter.py:770:def _render_cpp_inline_scalar_helpers(*, owner_name: str, field_ir: StructFieldIR) -> list[str]:
./src/piketype/validate/namespace.py:1:"""C++ namespace validation for the --namespace CLI argument."""
./src/piketype/validate/namespace.py:25:    "namespace", "new", "noexcept", "not", "not_eq", "nullptr",
./src/piketype/validate/namespace.py:42:def validate_cpp_namespace(value: str) -> tuple[str, ...]:
./src/piketype/validate/namespace.py:43:    """Validate a ``::``-separated C++ namespace string.
./src/piketype/validate/namespace.py:49:        raise ValidationError("--namespace value must not be empty")
./src/piketype/validate/namespace.py:56:                f"--namespace contains an empty segment in '{value}'"
./src/piketype/validate/namespace.py:60:                f"--namespace segment '{segment}' is not a valid C++ identifier"
./src/piketype/validate/namespace.py:64:                f"--namespace segment '{segment}' is a C++ keyword"
./src/piketype/validate/namespace.py:68:                f"--namespace segment '{segment}' must not begin with an underscore"
./src/piketype/validate/namespace.py:72:                f"--namespace segment '{segment}' must not contain '__'"
./src/piketype/validate/namespace.py:76:                f"--namespace segment '{segment}' must not end with an underscore"
./src/piketype/validate/namespace.py:80:                "--namespace must not use 'std' as the first segment"
./src/piketype/validate/namespace.py:87:            f"--namespace '{value}' would produce a reserved include-guard prefix "
./src/piketype/validate/namespace.py:92:            f"--namespace '{value}' would produce a reserved include-guard prefix "
./src/piketype/validate/namespace.py:100:    """Reject duplicate module basenames when ``--namespace`` is active.
./src/piketype/validate/namespace.py:118:        "--namespace requires unique module basenames, but duplicates were found:\n"
./tests/test_namespace_validation.py:1:"""Unit tests for C++ namespace validation."""
./tests/test_namespace_validation.py:9:from piketype.validate.namespace import (
./tests/test_namespace_validation.py:12:    validate_cpp_namespace,
./tests/test_namespace_validation.py:17:    """Tests for validate_cpp_namespace()."""
./tests/test_namespace_validation.py:22:        self.assertEqual(validate_cpp_namespace("foo"), ("foo",))
./tests/test_namespace_validation.py:25:        self.assertEqual(validate_cpp_namespace("foo::bar"), ("foo", "bar"))
./tests/test_namespace_validation.py:28:        self.assertEqual(validate_cpp_namespace("a::b::c"), ("a", "b", "c"))
./tests/test_namespace_validation.py:31:        self.assertEqual(validate_cpp_namespace("foo2::bar3"), ("foo2", "bar3"))
./tests/test_namespace_validation.py:37:            validate_cpp_namespace("")
./tests/test_namespace_validation.py:41:            validate_cpp_namespace("::foo")
./tests/test_namespace_validation.py:46:            validate_cpp_namespace("foo::")
./tests/test_namespace_validation.py:51:            validate_cpp_namespace("foo::::bar")
./tests/test_namespace_validation.py:58:            validate_cpp_namespace("123bad")
./tests/test_namespace_validation.py:63:            validate_cpp_namespace("foo-bar")
./tests/test_namespace_validation.py:70:            validate_cpp_namespace("class")
./tests/test_namespace_validation.py:73:    def test_rejects_namespace_keyword(self) -> None:
./tests/test_namespace_validation.py:75:            validate_cpp_namespace("namespace")
./tests/test_namespace_validation.py:80:            validate_cpp_namespace("alignas")
./tests/test_namespace_validation.py:85:            validate_cpp_namespace("constexpr")
./tests/test_namespace_validation.py:90:            validate_cpp_namespace("thread_local")
./tests/test_namespace_validation.py:95:            validate_cpp_namespace("noexcept")
./tests/test_namespace_validation.py:100:            validate_cpp_namespace("nullptr")
./tests/test_namespace_validation.py:105:            validate_cpp_namespace("static_assert")
./tests/test_namespace_validation.py:110:            validate_cpp_namespace("foo::int")
./tests/test_namespace_validation.py:120:            validate_cpp_namespace("_foo")
./tests/test_namespace_validation.py:125:            validate_cpp_namespace("foo::_bar")
./tests/test_namespace_validation.py:130:            validate_cpp_namespace("foo::_Bar")
./tests/test_namespace_validation.py:137:            validate_cpp_namespace("foo__bar")
./tests/test_namespace_validation.py:142:            validate_cpp_namespace("foo::a__b")
./tests/test_namespace_validation.py:149:            validate_cpp_namespace("foo_")
./tests/test_namespace_validation.py:154:            validate_cpp_namespace("foo::bar_")
./tests/test_namespace_validation.py:161:            validate_cpp_namespace("std::types")
./tests/test_namespace_validation.py:166:        self.assertEqual(validate_cpp_namespace("foo::std"), ("foo", "std"))
./src/piketype/backends/runtime/emitter.py:65:        "namespace piketype_runtime {\n\n"
./src/piketype/backends/runtime/emitter.py:67:        "}  // namespace piketype_runtime\n\n"
./src/piketype/backends/sv/emitter.py:68:    body_lines = [f"package {module.ref.basename}_pkg;"]
./src/piketype/backends/sv/emitter.py:85:        body_lines.append("")
./src/piketype/backends/sv/emitter.py:87:        body_lines.extend(const_lines)
./src/piketype/backends/sv/emitter.py:89:        body_lines.append("")
./src/piketype/backends/sv/emitter.py:92:            body_lines.append("")
./src/piketype/backends/sv/emitter.py:93:        body_lines.extend(type_block)
./src/piketype/backends/sv/emitter.py:94:    body_lines.append("endpackage")
./src/piketype/backends/sv/emitter.py:95:    return f"{header}\n" + "\n".join(body_lines) + "\n"
./src/piketype/backends/sv/emitter.py:98:def _render_sv_type_block(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./src/piketype/backends/sv/emitter.py:126:def _render_sv_width_value(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> str:
./src/piketype/backends/sv/emitter.py:135:def _render_sv_scalar_alias(*, type_ir: ScalarAliasIR) -> str:
./src/piketype/backends/sv/emitter.py:146:def _render_sv_struct(*, type_ir: StructIR) -> list[str]:
./src/piketype/backends/sv/emitter.py:166:def _render_sv_struct_field_type(*, field_type: FieldTypeIR) -> str:
./src/piketype/backends/sv/emitter.py:177:def _render_sv_flags(*, type_ir: FlagsIR) -> list[str]:
./src/piketype/backends/sv/emitter.py:191:def _render_sv_enum(*, type_ir: EnumIR) -> list[str]:
./src/piketype/backends/sv/emitter.py:201:def _render_sv_pack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./src/piketype/backends/sv/emitter.py:245:def _render_sv_unpack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./src/piketype/backends/sv/emitter.py:315:    body_lines = [
./src/piketype/backends/sv/emitter.py:320:        body_lines.append("")
./src/piketype/backends/sv/emitter.py:322:            body_lines.extend(f"  {line}" for line in _render_sv_scalar_helper_class(type_ir=type_ir))
./src/piketype/backends/sv/emitter.py:324:            body_lines.extend(f"  {line}" for line in _render_sv_struct_helper_class(type_ir=type_ir, type_index=type_index))
./src/piketype/backends/sv/emitter.py:326:            body_lines.extend(f"  {line}" for line in _render_sv_flags_helper_class(type_ir=type_ir))
./src/piketype/backends/sv/emitter.py:328:            body_lines.extend(f"  {line}" for line in _render_sv_enum_helper_class(type_ir=type_ir))
./src/piketype/backends/sv/emitter.py:329:    body_lines.append("endpackage")
./src/piketype/backends/sv/emitter.py:330:    return f"{header}\n" + "\n".join(body_lines) + "\n"
./src/piketype/backends/sv/emitter.py:333:def _render_sv_scalar_helper_class(*, type_ir: ScalarAliasIR) -> list[str]:
./src/piketype/backends/sv/emitter.py:428:def _render_sv_struct_helper_class(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./src/piketype/backends/sv/emitter.py:563:def _render_sv_flags_helper_class(*, type_ir: FlagsIR) -> list[str]:
./src/piketype/backends/sv/emitter.py:674:def _render_sv_enum_helper_class(*, type_ir: EnumIR) -> list[str]:
./src/piketype/backends/sv/emitter.py:756:def _render_sv_helper_field_decl(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./src/piketype/backends/sv/emitter.py:768:def _render_sv_helper_to_bytes_step(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./src/piketype/backends/sv/emitter.py:799:def _render_sv_helper_from_bytes_step(
./src/piketype/backends/sv/emitter.py:846:def _render_sv_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
./src/piketype/backends/sv/emitter.py:866:def _render_sv_expr(*, expr: ExprIR) -> str:
./tests/test_const_ranges.py:77:            namespace_parts=("alpha", "piketype", "constants"),
./docs/v1-product-spec.md:419:One DSL file is one namespace.
./docs/v1-product-spec.md:443:- namespaces derived from path relative to repo root, but skip literal `piketype`
./docs/v1-product-spec.md:444:- example: `foo/piketype/packet_defs.py` -> `namespace foo::packet_defs`
./docs/v1-product-spec.md:451:namespace foo::packet_defs { ... }
./docs/v1-product-spec.md:510:- reject duplicate generated names within a namespace
./docs/v1-product-spec.md:535:- namespaces
./src/piketype/backends/py/emitter.py:55:    body_lines: list[str] = []
./src/piketype/backends/py/emitter.py:57:        body_lines.append("from __future__ import annotations")
./src/piketype/backends/py/emitter.py:59:            body_lines.append("")
./src/piketype/backends/py/emitter.py:60:            body_lines.append("from dataclasses import dataclass, field")
./src/piketype/backends/py/emitter.py:62:            body_lines.append("")
./src/piketype/backends/py/emitter.py:63:            body_lines.append("from enum import IntEnum")
./src/piketype/backends/py/emitter.py:64:        body_lines.append("")
./src/piketype/backends/py/emitter.py:65:    body_lines.extend(f"{const.name} = {_render_py_expr(expr=const.expr)}" for const in module.constants)
./src/piketype/backends/py/emitter.py:67:        body_lines.append("")
./src/piketype/backends/py/emitter.py:70:            body_lines.append("")
./src/piketype/backends/py/emitter.py:72:            body_lines.extend(_render_py_scalar_alias(type_ir=type_ir))
./src/piketype/backends/py/emitter.py:74:            body_lines.extend(_render_py_struct(type_ir=type_ir, type_index=type_index))
./src/piketype/backends/py/emitter.py:76:            body_lines.extend(_render_py_flags(type_ir=type_ir))
./src/piketype/backends/py/emitter.py:78:            body_lines.extend(_render_py_enum(type_ir=type_ir))
./src/piketype/backends/py/emitter.py:79:    return f"{header}\n" + "\n".join(body_lines) + "\n"
./src/piketype/backends/py/emitter.py:99:def _render_py_expr(*, expr: ExprIR) -> str:
./src/piketype/backends/py/emitter.py:114:def _render_py_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
./src/piketype/backends/py/emitter.py:311:def _render_py_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./src/piketype/backends/py/emitter.py:360:def _render_py_struct_to_bytes(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./src/piketype/backends/py/emitter.py:412:def _render_py_struct_from_bytes(*, type_ir: StructIR, class_name: str, type_index: dict[str, TypeDefIR]) -> list[str]:
./src/piketype/backends/py/emitter.py:480:def _render_py_field_annotation(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./src/piketype/backends/py/emitter.py:495:def _render_py_field_default(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./src/piketype/backends/py/emitter.py:508:def _render_py_struct_field_coercer(*, owner_name: str, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./src/piketype/backends/py/emitter.py:634:def _render_py_enum(*, type_ir: EnumIR) -> list[str]:
./src/piketype/backends/py/emitter.py:707:def _render_py_flags(*, type_ir: FlagsIR) -> list[str]:
./tests/test_gen_flags.py:110:            namespace_parts=("alpha", "piketype", "types"),
./tests/test_struct_enum_member.py:108:            namespace_parts=("alpha",),
./tests/test_struct_enum_member.py:338:            namespace_parts=("a",),
./tests/test_struct_enum_member.py:344:            namespace_parts=("b",),
./tests/goldens/gen/namespace_override/piketype_manifest.json:35:      "namespace_parts": [
./tests/goldens/gen/namespace_override/piketype_manifest.json:70:      "namespace_parts": [
./tests/test_gen_const_sv.py:278:    def test_namespace_override_multi_module(self) -> None:
./tests/test_gen_const_sv.py:279:        fixture_root = FIXTURES_DIR / "namespace_override" / "project"
./tests/test_gen_const_sv.py:280:        expected_root = GOLDENS_DIR / "namespace_override"
./tests/test_gen_const_sv.py:285:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::bar")
./tests/test_gen_const_sv.py:289:    def test_namespace_rejects_empty_segment(self) -> None:
./tests/test_gen_const_sv.py:295:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::::bar")
./tests/test_gen_const_sv.py:299:    def test_namespace_rejects_non_identifier(self) -> None:
./tests/test_gen_const_sv.py:305:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "123bad")
./tests/test_gen_const_sv.py:309:    def test_namespace_rejects_cpp_keyword(self) -> None:
./tests/test_gen_const_sv.py:315:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "class")
./tests/test_gen_const_sv.py:319:    def test_namespace_rejects_double_underscore(self) -> None:
./tests/test_gen_const_sv.py:325:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo__bar")
./tests/test_gen_const_sv.py:329:    def test_namespace_rejects_leading_underscore(self) -> None:
./tests/test_gen_const_sv.py:335:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "_foo")
./tests/test_gen_const_sv.py:339:    def test_namespace_rejects_std_first_segment(self) -> None:
./tests/test_gen_const_sv.py:345:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "std::types")
./tests/test_gen_const_sv.py:349:    def test_namespace_rejects_trailing_underscore(self) -> None:
./tests/test_gen_const_sv.py:355:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo_")
./tests/test_gen_const_sv.py:359:    def test_namespace_rejects_leading_underscore_non_first(self) -> None:
./tests/test_gen_const_sv.py:365:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::_bar")
./tests/test_gen_const_sv.py:369:    def test_namespace_rejects_duplicate_basenames(self) -> None:
./tests/test_gen_const_sv.py:384:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::bar")
./tests/test_gen_enum.py:91:        namespace_parts=("foo", "piketype", "defs"),
./tests/test_gen_enum.py:219:            namespace_parts=("foo", "piketype", "defs"),
./tests/test_gen_enum.py:249:            namespace_parts=("foo", "piketype", "defs"),
./docs/rfc-v1.md:357:SystemVerilog namespace rule:
./docs/rfc-v1.md:363:Python namespace rule:
./docs/rfc-v1.md:369:C++ namespace rule:
./docs/rfc-v1.md:371:- namespace is derived from repo-relative path
./docs/rfc-v1.md:372:- the literal `piketype` directory is skipped in the namespace
./docs/rfc-v1.md:417:- reject duplicate generated names within a namespace
./docs/rfc-v1.md:436:- namespaces
./tests/goldens/gen/struct_flags_member/piketype_manifest.json:13:      "namespace_parts": [
./docs/architecture.md:265:- source namespace identities
./specs/004-cpp-constexpr-upper-case/plan.md:60:# Namespace override fixture (requires --namespace):
./specs/004-cpp-constexpr-upper-case/plan.md:62:cp -r "$PROJECT/tests/fixtures/namespace_override/project" "$TMPDIR/project"
./specs/004-cpp-constexpr-upper-case/plan.md:63:PYTHONPATH="$PROJECT/src" python3 -m typist.cli gen --namespace foo::bar "$TMPDIR/project/alpha/typist/constants.py"
./specs/004-cpp-constexpr-upper-case/plan.md:64:rm -rf "$PROJECT/tests/goldens/gen/namespace_override"
./specs/004-cpp-constexpr-upper-case/plan.md:65:cp -r "$TMPDIR/project/gen" "$PROJECT/tests/goldens/gen/namespace_override"
./docs/requirements.org:1:* namespace
./docs/requirements.org:3:Allow user to specify th top level name space with --namespace argument.
./docs/requirements.org:5:for example `piketype gen --namespace foo::bar constants.py`, the generated namespace in the generate c++ file should be `namespace foo:bar::constants{}` 
./docs/ir-schema.md:64:- `namespace_parts: tuple[str, ...]`
./tests/goldens/gen/namespace_override/cpp/alpha/piketype/constants_types.hpp:10:namespace foo::bar::constants {
./tests/goldens/gen/namespace_override/cpp/alpha/piketype/constants_types.hpp:15:}  // namespace foo::bar::constants
./tests/goldens/gen/struct_flags_member/cpp/alpha/piketype/types_types.hpp:13:namespace alpha::types {
./tests/goldens/gen/struct_flags_member/cpp/alpha/piketype/types_types.hpp:218:}  // namespace alpha::types
./specs/002-namespace-cli-argument/spec.md:1:# Spec 002: `--namespace` CLI Argument for C++ Namespace Override
./specs/002-namespace-cli-argument/spec.md:5:Add a `--namespace` CLI argument to `typist gen` that lets users specify a custom
./specs/002-namespace-cli-argument/spec.md:6:top-level C++ namespace prefix. Today, the C++ namespace is derived entirely from
./specs/002-namespace-cli-argument/spec.md:8:out). This feature gives users explicit control over the generated C++ namespace
./specs/002-namespace-cli-argument/spec.md:14:typist gen --namespace foo::bar constants.py
./specs/002-namespace-cli-argument/spec.md:20:namespace foo::bar::constants {
./specs/002-namespace-cli-argument/spec.md:22:}  // namespace foo::bar::constants
./specs/002-namespace-cli-argument/spec.md:25:Instead of the current path-derived namespace (e.g., `alpha::constants`).
./specs/002-namespace-cli-argument/spec.md:29:1. **As a hardware/firmware engineer**, I want to specify the C++ namespace for
./specs/002-namespace-cli-argument/spec.md:31:   namespace hierarchy, without being forced to mirror the DSL file-system layout.
./specs/002-namespace-cli-argument/spec.md:34:   namespace so that CI scripts can target different namespace schemes per build
./specs/002-namespace-cli-argument/spec.md:39:### FR-1: New `--namespace` argument on the `gen` subcommand
./specs/002-namespace-cli-argument/spec.md:41:The `gen` subcommand accepts an optional `--namespace <value>` argument.
./specs/002-namespace-cli-argument/spec.md:43:- `<value>` is a `::` -separated C++ namespace path (e.g., `foo`, `foo::bar`,
./specs/002-namespace-cli-argument/spec.md:46:  (path-derived namespace with `typist` segment filtered).
./specs/002-namespace-cli-argument/spec.md:62:   words (e.g., `class`, `namespace`, `return`, `int`, `void`, etc.) and rejects
./specs/002-namespace-cli-argument/spec.md:76:After segment validation passes, compute the **namespace guard prefix** by
./specs/002-namespace-cli-argument/spec.md:85:this check validates **only the namespace-derived prefix**, not the full include
./specs/002-namespace-cli-argument/spec.md:91:### FR-3: C++ namespace composition
./specs/002-namespace-cli-argument/spec.md:93:When `--namespace` is provided, the generated C++ namespace for a module is:
./specs/002-namespace-cli-argument/spec.md:96:<namespace_value>::<module_basename>
./specs/002-namespace-cli-argument/spec.md:101:parts is bypassed entirely — the user-provided namespace replaces it.
./specs/002-namespace-cli-argument/spec.md:103:When `--namespace` is **not** provided, the existing path-derived behaviour is
./specs/002-namespace-cli-argument/spec.md:108:When `--namespace` is provided, the include guard follows the same composition:
./specs/002-namespace-cli-argument/spec.md:117:When omitted, the existing guard derivation from `namespace_parts` is unchanged.
./specs/002-namespace-cli-argument/spec.md:121:The `--namespace` argument affects **only** generated C++ module headers (the
./specs/002-namespace-cli-argument/spec.md:126:- Manifest `namespace_parts`
./specs/002-namespace-cli-argument/spec.md:129:  keep their existing `typist_runtime` namespace and include guards unchanged.
./specs/002-namespace-cli-argument/spec.md:132:are file-path-derived. Runtime headers have a fixed, well-known namespace.
./specs/002-namespace-cli-argument/spec.md:133:A C++ namespace override should not silently alter any of these.
./specs/002-namespace-cli-argument/spec.md:137:The namespace override value is carried from CLI → `run_gen` → C++ emitter. It
./specs/002-namespace-cli-argument/spec.md:138:does **not** modify `ModuleRefIR.namespace_parts` in the IR. Instead, it is
./specs/002-namespace-cli-argument/spec.md:144:When `--namespace` is specified, it applies to **every** module discovered in the
./specs/002-namespace-cli-argument/spec.md:146:in the run use the same namespace prefix.
./specs/002-namespace-cli-argument/spec.md:149:in the repo. Applying the namespace only to the targeted module would create an
./specs/002-namespace-cli-argument/spec.md:154:When `--namespace` is specified, the tool validates that no two discovered
./specs/002-namespace-cli-argument/spec.md:159:Rationale: With `--namespace`, the C++ namespace is `<prefix>::<basename>`. If
./specs/002-namespace-cli-argument/spec.md:161:`beta/typist/types.py`), they would produce identical namespaces
./specs/002-namespace-cli-argument/spec.md:170:`--namespace` value, consistent with the project constitution.
./specs/002-namespace-cli-argument/spec.md:179:When `--namespace` is omitted, all generated outputs are byte-for-byte identical
./specs/002-namespace-cli-argument/spec.md:184:1. `typist gen --namespace foo::bar <path>` produces C++ headers where every
./specs/002-namespace-cli-argument/spec.md:185:   module's namespace is `foo::bar::<module_basename>`.
./specs/002-namespace-cli-argument/spec.md:186:2. `typist gen --namespace foo::bar <path>` produces C++ headers where the
./specs/002-namespace-cli-argument/spec.md:188:3. `typist gen <path>` (no `--namespace`) produces output identical to the
./specs/002-namespace-cli-argument/spec.md:190:4. `typist gen --namespace "foo::::bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/spec.md:192:5. `typist gen --namespace "123bad" <path>` exits with a validation error and
./specs/002-namespace-cli-argument/spec.md:194:6. `typist gen --namespace "class" <path>` exits with a validation error
./specs/002-namespace-cli-argument/spec.md:196:7. `typist gen --namespace "foo__bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/spec.md:198:8. `typist gen --namespace "_foo" <path>` exits with a validation error (leading
./specs/002-namespace-cli-argument/spec.md:200:9. `typist gen --namespace "std::types" <path>` exits with a validation error
./specs/002-namespace-cli-argument/spec.md:202:10. `typist gen --namespace "foo_" <path>` exits with a validation error
./specs/002-namespace-cli-argument/spec.md:204:11. `typist gen --namespace "foo::_bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/spec.md:206:12. `typist gen --namespace foo::bar <path>` does **not** alter SV, Python,
./specs/002-namespace-cli-argument/spec.md:208:13. When `--namespace` is used on a repo with two modules sharing the same
./specs/002-namespace-cli-argument/spec.md:210:14. Golden-file integration test: at least one positive case using `--namespace`
./specs/002-namespace-cli-argument/spec.md:212:    path-derived namespaces. The test verifies that both C++ headers use the
./specs/002-namespace-cli-argument/spec.md:214:15. Negative CLI tests: at least one test per invalid-namespace category (empty
./specs/002-namespace-cli-argument/spec.md:223:- Per-module namespace overrides (one namespace for module A, another for B).
./specs/002-namespace-cli-argument/spec.md:226:- Modifying the IR `namespace_parts` field — it stays path-derived.
./specs/002-namespace-cli-argument/spec.md:227:- Changing the output file path based on `--namespace` — files stay in the
./specs/002-namespace-cli-argument/spec.md:231:  namespaces by the existing codebase without such checks. The composition-level
./specs/002-namespace-cli-argument/spec.md:232:  check in FR-2 validates only the namespace-derived prefix, not the full
./specs/010-jinja-template-migration/spec.md:37:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/spec.md:52:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/spec.md:154:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./tests/goldens/gen/namespace_override/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/namespace_override/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./specs/010-jinja-template-migration/plan.md:23:    env = make_environment(package="piketype.backends.<lang>")
./specs/010-jinja-template-migration/plan.md:44:- `ModuleView` carries a field `body_lines: tuple[str, ...] | None`. When non-None, the primary template emits `{{ body_lines | join("\n") }}` for the not-yet-templated portion.
./specs/010-jinja-template-migration/plan.md:45:- Each sub-step replaces a portion of `body_lines` with a structured field (`types: tuple[TypeView, ...]`, etc.), and the template's body section transitions from `{% if body_lines %}{{ body_lines | join("\n") }}{% endif %}` to a structured loop over `types`.
./specs/010-jinja-template-migration/plan.md:46:- After sub-step 4 (fragments), `body_lines` is unused and removed from the view; the field is retired in the cleanup commit.
./specs/010-jinja-template-migration/plan.md:60:| `src/piketype/backends/common/render.py`                        | rewrite | `make_environment(*, package: str) -> jinja2.Environment` and `render(*, env: jinja2.Environment, template_name: str, context: object) -> str`. Custom-filter registration site (CL-2/FR-16). |
./specs/010-jinja-template-migration/plan.md:63:| `tests/test_render.py`                                          | new     | `make_environment` / `render` smoke tests; placeholder for future custom-filter tests (CL-2). |
./specs/010-jinja-template-migration/plan.md:86:def make_environment(*, package: str) -> jinja2.Environment:
./specs/010-jinja-template-migration/plan.md:113:# Registered by mutating the env returned from make_environment via a hook
./specs/010-jinja-template-migration/plan.md:120:1. `feat(common): add make_environment and render helpers` — `render.py` + `tests/test_render.py`.
./specs/010-jinja-template-migration/plan.md:162:class ConstantView:
./specs/010-jinja-template-migration/plan.md:167:class ScalarAliasView:
./specs/010-jinja-template-migration/plan.md:181:class EnumMemberView:
./specs/010-jinja-template-migration/plan.md:186:class EnumView:
./specs/010-jinja-template-migration/plan.md:196:class FlagFieldView:
./specs/010-jinja-template-migration/plan.md:201:class FlagsView:
./specs/010-jinja-template-migration/plan.md:214:class StructFieldView:
./specs/010-jinja-template-migration/plan.md:239:class StructView:
./specs/010-jinja-template-migration/plan.md:244:    fields: tuple[StructFieldView, ...]
./specs/010-jinja-template-migration/plan.md:248:type TypeView = ScalarAliasView | StructView | EnumView | FlagsView
./specs/010-jinja-template-migration/plan.md:251:class ModuleView:
./specs/010-jinja-template-migration/plan.md:260:    body_lines: tuple[str, ...] | None
./specs/010-jinja-template-migration/plan.md:267:- `_build_struct_field_view(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> StructFieldView`
./specs/010-jinja-template-migration/plan.md:268:- `_build_enum_view(*, type_ir: EnumIR) -> EnumView`
./specs/010-jinja-template-migration/plan.md:269:- `_build_flags_view(*, type_ir: FlagsIR) -> FlagsView`
./specs/010-jinja-template-migration/plan.md:272:Builders are pure functions, no side effects, no IR mutation. Tests in `tests/test_view_py.py` assert that for a fixture's IR, the builder produces a view whose primitive fields equal expected literal values (e.g., for `enum_basic`, `EnumView.mask == 7`).
./specs/010-jinja-template-migration/plan.md:277:2. `feat(py): module skeleton via templates` (FR-6 sub-step 1) — `module.j2` renders header + imports + footer. `emit_py` constructs `ModuleView` with `body_lines = tuple(legacy_render_body_lines(module))` and the template emits `{{ body_lines | join("\n") }}` for the body. **Byte parity preserved.**
./specs/010-jinja-template-migration/plan.md:278:3. `feat(py): top-level type declaration skeletons via templates` (FR-6 sub-step 2) — `_macros.j2` adds `scalar_class_skeleton`, `struct_class_skeleton`, `enum_classes_skeleton`, `flags_class_skeleton` macros that emit *only the class header lines* (`class X:`, `WIDTH = ...`, `BYTE_COUNT = ...`). Helper-method bodies and expression fragments still arrive as `body_lines_per_type: tuple[str, ...]` strings on each TypeView. The view is augmented with `helper_lines: tuple[str, ...]` per TypeView temporarily. **Byte parity preserved.**
./specs/010-jinja-template-migration/plan.md:280:5. `feat(py): expression and field-level fragments` (FR-6 sub-step 4) — expressions like Python constants, enum member values, and flag mask literals are now rendered from view-model `*_expr: str` fields directly in templates (no Python concatenation). Also handles struct field annotations/defaults/coercer literals. The transitional `body_lines` field on `ModuleView` is now always `None` and removed in this commit. **Byte parity preserved.**
./specs/010-jinja-template-migration/plan.md:298:class CppNamespaceView:
./specs/010-jinja-template-migration/plan.md:299:    open_lines: tuple[str, ...]   # ["namespace alpha {", "namespace piketype {"]
./specs/010-jinja-template-migration/plan.md:300:    close_lines: tuple[str, ...]  # ["}  // namespace piketype", "}  // namespace alpha"]
./specs/010-jinja-template-migration/plan.md:304:class CppGuardView:
./specs/010-jinja-template-migration/plan.md:308:class CppStructFieldView:
./specs/010-jinja-template-migration/plan.md:331:class CppModuleView:
./specs/010-jinja-template-migration/plan.md:334:    namespace: CppNamespaceView
./specs/010-jinja-template-migration/plan.md:341:    types: tuple[TypeView, ...]          # CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView
./specs/010-jinja-template-migration/plan.md:342:    body_lines: tuple[str, ...] | None   # transitional same as Phase 1
./specs/010-jinja-template-migration/plan.md:345:`CppScalarAliasView`, `CppEnumView`, `CppFlagsView` follow the same shape pattern as Python's: precomputed primitives + literal strings, no IR refs, no methods.
./specs/010-jinja-template-migration/plan.md:349:**`--namespace` CLI override:** the namespace builder respects `emit_cpp(repo, *, namespace=None)`. The view's `CppNamespaceView` is constructed from either `module.ref.namespace_parts` (default) or the CLI override (test in `tests/test_view_cpp.py` includes a fixture run with an override).
./specs/010-jinja-template-migration/plan.md:354:2. `feat(cpp): module skeleton via templates` (header, guard open, includes, namespace open, namespace close, guard close).
./specs/010-jinja-template-migration/plan.md:375:class SvConstantView:
./specs/010-jinja-template-migration/plan.md:381:class SvTypedefView:
./specs/010-jinja-template-migration/plan.md:396:class SvSynthModuleView:
./specs/010-jinja-template-migration/plan.md:402:    body_lines: tuple[str, ...] | None     # transitional
./specs/010-jinja-template-migration/plan.md:405:class SvHelperFieldView:
./specs/010-jinja-template-migration/plan.md:419:class SvHelperClassView:
./specs/010-jinja-template-migration/plan.md:433:class SvTestModuleView:
./specs/010-jinja-template-migration/plan.md:438:    body_lines: tuple[str, ...] | None     # transitional
./specs/010-jinja-template-migration/plan.md:484:| Whitespace drift on first template render breaks goldens | High | `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True` in `make_environment`. Migrate one sub-step at a time and diff goldens after each commit. The transitional `body_lines | join("\n")` mechanism preserves line-by-line legacy output verbatim until each sub-step replaces it. |
./specs/010-jinja-template-migration/plan.md:485:| Jinja `trim_blocks`/`lstrip_blocks` interacting unexpectedly with literal-heavy template content (e.g., generated SV helper classes containing `begin`/`end` blocks) | Medium | When a literal-heavy block must be preserved verbatim, wrap it in `{% raw %}...{% endraw %}` or pass it through as a precomputed `str` field on the view (the `body_lines` mechanism). Phase 3 commit 4 explicitly tests this on the largest SV `_helper_class` block. |
./specs/010-jinja-template-migration/plan.md:491:| C++ `--namespace` CLI override regression | Medium | `tests/test_view_cpp.py` runs the namespace-override fixture (`tests/fixtures/namespace_override`) end-to-end, asserting the rendered guard macro and namespace open/close strings. This catches regressions before goldens. |
./specs/010-jinja-template-migration/plan.md:517:- **C++ namespace override tests:** explicit end-to-end run of the namespace-override fixture in `tests/test_view_cpp.py`.
./tests/goldens/gen/struct_flags_member/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/struct_flags_member/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:1:# Validation Report — Spec 002: `--namespace` CLI Argument
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:7:- 33 unit tests (`test_namespace_validation.py`)
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:15:| 1 | Namespace is `foo::bar::<basename>` | `test_namespace_override_multi_module` | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:16:| 2 | Guard is `FOO_BAR_<BASENAME>_TYPES_HPP` | `test_namespace_override_multi_module` | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:17:| 3 | No `--namespace` = identical output | All existing golden tests | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:18:| 4 | `foo::::bar` rejected (empty segment) | `test_namespace_rejects_empty_segment` | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:19:| 5 | `123bad` rejected (non-identifier) | `test_namespace_rejects_non_identifier` | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:20:| 6 | `class` rejected (keyword) | `test_namespace_rejects_cpp_keyword` | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:21:| 7 | `foo__bar` rejected (double underscore) | `test_namespace_rejects_double_underscore` | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:22:| 8 | `_foo` rejected (leading underscore) | `test_namespace_rejects_leading_underscore` | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:23:| 9 | `std::types` rejected (std first) | `test_namespace_rejects_std_first_segment` | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:24:| 10 | `foo_` rejected (trailing underscore) | `test_namespace_rejects_trailing_underscore` | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:25:| 11 | `foo::_bar` rejected (underscore non-first) | `test_namespace_rejects_leading_underscore_non_first` | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:26:| 12 | SV/Python/manifest/runtime unchanged | `test_namespace_override_multi_module` (full tree) | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:27:| 13 | Duplicate basenames rejected | `test_namespace_rejects_duplicate_basenames` | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:28:| 14 | Multi-module golden test | `test_namespace_override_multi_module` (2 modules) | PASS |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:36:| `src/typist/validate/namespace.py` | New: validation logic |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:37:| `src/typist/cli.py` | Modified: `--namespace` arg on `gen` |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:39:| `src/typist/backends/cpp/emitter.py` | Modified: namespace override |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:40:| `tests/test_namespace_validation.py` | New: 33 unit tests |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:42:| `tests/fixtures/namespace_override/` | New: multi-module fixture |
./specs/002-namespace-cli-argument/artifacts/validation/validation.md:43:| `tests/goldens/gen/namespace_override/` | New: golden output |
./specs/007-struct-flags-member/plan.md:206:File: `tests/test_namespace_validation.py` (extend existing)
./tests/goldens/gen/namespace_override/cpp/beta/piketype/more_types.hpp:10:namespace foo::bar::more {
./tests/goldens/gen/namespace_override/cpp/beta/piketype/more_types.hpp:14:}  // namespace foo::bar::more
./specs/007-struct-flags-member/tasks.md:228:**File:** `tests/test_namespace_validation.py` (extend existing)
./specs/010-jinja-template-migration/artifacts/specification/iter3-forge.md:37:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/specification/iter3-forge.md:52:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/specification/iter3-forge.md:154:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./specs/002-namespace-cli-argument/artifacts/retrospect/retrospect.md:1:# Retrospect — Spec 002: `--namespace` CLI Argument
./specs/002-namespace-cli-argument/artifacts/retrospect/retrospect.md:15:2. **Pass-through design was correct.** Threading `namespace: str | None` from
./specs/002-namespace-cli-argument/artifacts/retrospect/retrospect.md:37:- `--namespace` only affects C++ module headers, not SV/Python/manifest/runtime.
./specs/002-namespace-cli-argument/artifacts/retrospect/retrospect.md:38:- IR `namespace_parts` is untouched; the override is a separate parameter.
./specs/002-namespace-cli-argument/artifacts/retrospect/retrospect.md:39:- `std` rejected only as the first segment (it's a namespace, not a keyword).
./specs/002-namespace-cli-argument/artifacts/retrospect/retrospect.md:50:| New files | 3 (namespace.py, test, fixture+goldens) |
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:35:tests/test_gen_const_sv.py::GenConstSvIntegrationTest::test_namespace_override_multi_module PASSED [ 15%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:36:tests/test_gen_const_sv.py::GenConstSvIntegrationTest::test_namespace_rejects_cpp_keyword PASSED [ 15%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:37:tests/test_gen_const_sv.py::GenConstSvIntegrationTest::test_namespace_rejects_double_underscore PASSED [ 16%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:38:tests/test_gen_const_sv.py::GenConstSvIntegrationTest::test_namespace_rejects_duplicate_basenames PASSED [ 16%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:39:tests/test_gen_const_sv.py::GenConstSvIntegrationTest::test_namespace_rejects_empty_segment PASSED [ 17%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:40:tests/test_gen_const_sv.py::GenConstSvIntegrationTest::test_namespace_rejects_leading_underscore PASSED [ 17%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:41:tests/test_gen_const_sv.py::GenConstSvIntegrationTest::test_namespace_rejects_leading_underscore_non_first PASSED [ 18%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:42:tests/test_gen_const_sv.py::GenConstSvIntegrationTest::test_namespace_rejects_non_identifier PASSED [ 18%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:43:tests/test_gen_const_sv.py::GenConstSvIntegrationTest::test_namespace_rejects_std_first_segment PASSED [ 19%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:44:tests/test_gen_const_sv.py::GenConstSvIntegrationTest::test_namespace_rejects_trailing_underscore PASSED [ 19%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:124:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_allows_std_in_non_first_segment PASSED [ 62%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:125:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_keyword_set_is_nonempty PASSED [ 63%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:126:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_alignas PASSED [ 63%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:127:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_class_keyword PASSED [ 64%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:128:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_constexpr PASSED [ 65%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:129:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_double_colon_prefix PASSED [ 65%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:130:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_double_colon_suffix PASSED [ 66%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:131:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_double_underscore PASSED [ 66%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:132:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_double_underscore_middle PASSED [ 67%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:133:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_empty_string PASSED [ 67%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:134:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_hyphen PASSED [ 68%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:135:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_keyword_in_non_first_segment PASSED [ 68%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:136:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_leading_digit PASSED [ 69%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:137:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_leading_underscore_first_segment PASSED [ 69%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:138:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_leading_underscore_non_first_segment PASSED [ 70%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:139:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_leading_underscore_uppercase PASSED [ 70%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:140:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_namespace_keyword PASSED [ 71%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:141:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_noexcept PASSED [ 72%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:142:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_nullptr PASSED [ 72%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:143:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_quadruple_colon PASSED [ 73%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:144:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_static_assert PASSED [ 73%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:145:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_std_first_segment PASSED [ 74%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:146:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_thread_local PASSED [ 74%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:147:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_trailing_underscore PASSED [ 75%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:148:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_rejects_trailing_underscore_non_first PASSED [ 75%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:149:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_segment_with_digits PASSED [ 76%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:150:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_single_segment PASSED [ 76%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:151:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_three_segments PASSED [ 77%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:152:tests/test_namespace_validation.py::ValidateCppNamespaceTest::test_two_segments PASSED [ 77%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:153:tests/test_namespace_validation.py::CheckDuplicateBasenamesTest::test_duplicates_raises PASSED [ 78%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:154:tests/test_namespace_validation.py::CheckDuplicateBasenamesTest::test_empty_list_passes PASSED [ 79%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:155:tests/test_namespace_validation.py::CheckDuplicateBasenamesTest::test_no_duplicates_passes PASSED [ 79%]
./specs/008-enum-dsl-type/artifacts/validation/iter1-test-output.txt:156:tests/test_namespace_validation.py::CheckDuplicateBasenamesTest::test_single_module_passes PASSED [ 80%]
./specs/010-jinja-template-migration/artifacts/specification/iter2-forge.md:37:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/specification/iter2-forge.md:52:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge-prompt.md:1:# Gauge Review: Specification 002 — `--namespace` CLI Argument
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge-prompt.md:9:Read the specification at `specs/002-namespace-cli-argument/spec.md` and the
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge-prompt.md:21:- Namespaces are derived from file paths: `alpha/typist/constants.py` → namespace_parts `("alpha", "typist", "constants")` → C++ namespace `alpha::constants` (filtering out "typist")
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge-prompt.md:22:- CLI: `typist gen <path>` — no namespace arguments exist today
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge-prompt.md:23:- The C++ backend builds namespaces in `src/typist/backends/cpp/emitter.py` line 48
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge-prompt.md:24:- The IR node `ModuleRefIR` stores `namespace_parts: tuple[str, ...]`
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge-prompt.md:27:- Add `--namespace <value>` to `typist gen`
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge-prompt.md:28:- When provided, the C++ namespace becomes `<value>::<module_basename>` instead of path-derived
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:1:# Spec 002: `--namespace` CLI Argument for C++ Namespace Override
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:5:Add a `--namespace` CLI argument to `typist gen` that lets users specify a custom
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:6:top-level C++ namespace prefix. Today, the C++ namespace is derived entirely from
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:8:out). This feature gives users explicit control over the generated C++ namespace
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:14:typist gen --namespace foo::bar constants.py
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:20:namespace foo::bar::constants {
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:22:}  // namespace foo::bar::constants
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:25:Instead of the current path-derived namespace (e.g., `alpha::constants`).
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:29:1. **As a hardware/firmware engineer**, I want to specify the C++ namespace for
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:31:   namespace hierarchy, without being forced to mirror the DSL file-system layout.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:34:   namespace so that CI scripts can target different namespace schemes per build
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:39:### FR-1: New `--namespace` argument on the `gen` subcommand
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:41:The `gen` subcommand accepts an optional `--namespace <value>` argument.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:43:- `<value>` is a `::` -separated C++ namespace path (e.g., `foo`, `foo::bar`,
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:46:  (path-derived namespace with `typist` segment filtered).
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:56:- **C++17 keywords** are rejected as namespace segments. The implementation
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:57:  maintains a set of C++17 reserved words (e.g., `class`, `namespace`, `return`,
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:70:### FR-3: C++ namespace composition
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:72:When `--namespace` is provided, the generated C++ namespace for a module is:
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:75:<namespace_value>::<module_basename>
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:80:parts is bypassed entirely — the user-provided namespace replaces it.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:82:When `--namespace` is **not** provided, the existing path-derived behaviour is
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:87:When `--namespace` is provided, the include guard follows the same composition:
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:96:When omitted, the existing guard derivation from `namespace_parts` is unchanged.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:100:The `--namespace` argument affects **only** generated C++ module headers (the
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:105:- Manifest `namespace_parts`
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:108:  keep their existing `typist_runtime` namespace and include guards unchanged.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:111:are file-path-derived. Runtime headers have a fixed, well-known namespace.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:112:A C++ namespace override should not silently alter any of these.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:116:The namespace override value is carried from CLI → `run_gen` → C++ emitter. It
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:117:does **not** modify `ModuleRefIR.namespace_parts` in the IR. Instead, it is
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:123:When `--namespace` is specified, it applies to **every** module discovered in the
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:125:in the run use the same namespace prefix.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:128:in the repo. Applying the namespace only to the targeted module would create an
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:133:When `--namespace` is specified, the tool validates that no two discovered
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:138:Rationale: With `--namespace`, the C++ namespace is `<prefix>::<basename>`. If
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:140:`beta/typist/types.py`), they would produce identical namespaces
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:149:`--namespace` value, consistent with the project constitution.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:158:When `--namespace` is omitted, all generated outputs are byte-for-byte identical
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:163:1. `typist gen --namespace foo::bar <path>` produces C++ headers where every
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:164:   module's namespace is `foo::bar::<module_basename>`.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:165:2. `typist gen --namespace foo::bar <path>` produces C++ headers where the
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:167:3. `typist gen <path>` (no `--namespace`) produces output identical to the
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:169:4. `typist gen --namespace "foo::::bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:171:5. `typist gen --namespace "123bad" <path>` exits with a validation error and
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:173:6. `typist gen --namespace "class" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:175:7. `typist gen --namespace "foo__bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:177:8. `typist gen --namespace "_foo" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:179:9. `typist gen --namespace "std::types" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:181:10. `typist gen --namespace foo::bar <path>` does **not** alter SV, Python,
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:183:11. When `--namespace` is used on a repo with two modules sharing the same
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:185:12. Golden-file integration test: at least one positive case using `--namespace`
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:187:    path-derived namespaces. The test verifies that both C++ headers use the
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:189:13. Negative CLI tests: at least one test per invalid-namespace category (empty
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:197:- Per-module namespace overrides (one namespace for module A, another for B).
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:200:- Modifying the IR `namespace_parts` field — it stays path-derived.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:201:- Changing the output file path based on `--namespace` — files stay in the
./specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md:204:  user-controlled file names and is already emitted into namespaces by the
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:1:# Spec 002: `--namespace` CLI Argument for C++ Namespace Override
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:5:Add a `--namespace` CLI argument to `typist gen` that lets users specify a custom
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:6:top-level C++ namespace prefix. Today, the C++ namespace is derived entirely from
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:8:out). This feature gives users explicit control over the generated C++ namespace
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:14:typist gen --namespace foo::bar constants.py
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:20:namespace foo::bar::constants {
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:22:}  // namespace foo::bar::constants
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:25:Instead of the current path-derived namespace (e.g., `alpha::constants`).
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:29:1. **As a hardware/firmware engineer**, I want to specify the C++ namespace for
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:31:   namespace hierarchy, without being forced to mirror the DSL file-system layout.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:34:   namespace so that CI scripts can target different namespace schemes per build
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:39:### FR-1: New `--namespace` argument on the `gen` subcommand
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:41:The `gen` subcommand accepts an optional `--namespace <value>` argument.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:43:- `<value>` is a `::` -separated C++ namespace path (e.g., `foo`, `foo::bar`,
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:46:  (path-derived namespace with `typist` segment filtered).
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:56:- **C++17 keywords** are rejected as namespace segments. The implementation
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:57:  maintains a set of C++17 reserved words (e.g., `class`, `namespace`, `return`,
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:64:### FR-3: C++ namespace composition
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:66:When `--namespace` is provided, the generated C++ namespace for a module is:
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:69:<namespace_value>::<module_basename>
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:74:parts is bypassed entirely — the user-provided namespace replaces it.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:76:When `--namespace` is **not** provided, the existing path-derived behaviour is
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:81:When `--namespace` is provided, the include guard follows the same composition:
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:90:When omitted, the existing guard derivation from `namespace_parts` is unchanged.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:94:The `--namespace` argument affects **only** the C++ code generation backend.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:95:SystemVerilog package names, Python module paths, manifest `namespace_parts`, and
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:99:are file-path-derived. A C++ namespace override should not silently alter those.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:103:The namespace override value is carried from CLI → `run_gen` → C++ emitter. It
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:104:does **not** modify `ModuleRefIR.namespace_parts` in the IR. Instead, it is
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:110:When `--namespace` is specified, it applies to **every** module discovered in the
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:112:run use the same namespace prefix.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:115:in the repo. Applying the namespace only to the targeted module would create an
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:120:When `--namespace` is specified, the tool validates that no two discovered
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:125:Rationale: With `--namespace`, the C++ namespace is `<prefix>::<basename>`. If
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:127:`beta/typist/types.py`), they would produce identical namespaces
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:136:`--namespace` value, consistent with the project constitution.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:145:When `--namespace` is omitted, all generated outputs are byte-for-byte identical
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:150:1. `typist gen --namespace foo::bar <path>` produces C++ headers where every
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:151:   module's namespace is `foo::bar::<module_basename>`.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:152:2. `typist gen --namespace foo::bar <path>` produces C++ headers where the
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:154:3. `typist gen <path>` (no `--namespace`) produces output identical to the
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:156:4. `typist gen --namespace "foo::::bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:158:5. `typist gen --namespace "123bad" <path>` exits with a validation error and
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:160:6. `typist gen --namespace "class" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:162:7. `typist gen --namespace "__reserved" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:164:8. `typist gen --namespace foo::bar <path>` does **not** alter SV, Python,
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:166:9. When `--namespace` is used on a repo with two modules sharing the same
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:168:10. Golden-file integration test: at least one positive case using `--namespace`
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:170:11. Negative CLI tests: at least one test per invalid-namespace category (empty
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:177:- Per-module namespace overrides (one namespace for module A, another for B).
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:180:- Modifying the IR `namespace_parts` field — it stays path-derived.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:181:- Changing the output file path based on `--namespace` — files stay in the
./specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md:184:  user-controlled file names and is already emitted into namespaces by the
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:486:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:501:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:855:348:- **[NEEDS CLARIFICATION Q-3]** View-model shape for nested constructs (e.g., struct fields containing references to other types): should the field view model carry a precomputed `type_class_name: str` plus a `width: int` (flat denormalized form), or should it carry a reference to a sibling view-model dataclass (`field_type: ScalarViewModel | EnumViewModel`)? Flat form is simpler for templates; nested form preserves more structure. **Recommendation:** flat denormalized form for first migration (Python backend), revisit if it proves limiting. Confirm.
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:907:specs/010-jinja-template-migration/spec.md:52:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:1022:    gen_parser.add_argument("--namespace", default=None)
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:1040:                run_gen(args.path, namespace=args.namespace)
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:1076:from piketype.validate.namespace import check_duplicate_basenames, validate_cpp_namespace
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:1079:def run_gen(path: str, *, namespace: str | None = None) -> None:
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:1081:    if namespace is not None:
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:1082:        validate_cpp_namespace(namespace)
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:1089:    if namespace is not None:
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:1124:    emit_cpp(repo, namespace=namespace)
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:1146:tests/fixtures/namespace_override
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:1147:tests/fixtures/namespace_override/project
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:2024:tests/test_namespace_validation.py:177:        paths = [Path("alpha/piketype/types.py"), Path("beta/piketype/types.py")]
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:2025:tests/test_namespace_validation.py:181:        self.assertIn("alpha/piketype/types.py", str(ctx.exception))
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:2026:tests/test_namespace_validation.py:182:        self.assertIn("beta/piketype/types.py", str(ctx.exception))
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:2027:tests/goldens/gen/namespace_override/piketype_manifest.json:32:        "py": "gen/py/alpha/piketype/constants_types.py",
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:2028:tests/goldens/gen/namespace_override/piketype_manifest.json:67:        "py": "gen/py/beta/piketype/more_types.py",
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:2029:src/piketype/commands/gen.py:21:def run_gen(path: str, *, namespace: str | None = None) -> None:
./specs/010-jinja-template-migration/artifacts/specification/iter2-gauge.md:2032:src/piketype/cli.py:39:                run_gen(args.path, namespace=args.namespace)
./specs/002-namespace-cli-argument/artifacts/specification/iter2-gauge.md:7:- **Issue:** FR-2 still permits reserved C++ identifiers. C++ reserves identifiers containing `__` anywhere, not only with a `__` prefix. It also reserves names beginning with `_` in the global namespace, so `--namespace _foo` is unsafe. The spec also allows `--namespace std::x`, which generates declarations inside `std`, which is not valid user code.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-gauge.md:12:- **Issue:** FR-7 says "All emitted C++ headers in the run use the same namespace prefix," but the project also emits `cpp/runtime/typist_runtime.hpp`. AC-1 narrows this to module namespaces, so the runtime header behavior is unclear.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-gauge.md:13:- **Suggestion:** State explicitly that `--namespace` affects generated module C++ headers only, and that runtime C++ headers keep their existing namespace and include guard. If runtime should change too, add explicit requirements and acceptance criteria.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-gauge.md:18:- **Suggestion:** Require the positive golden-file case to include at least two discovered modules with different path-derived namespaces, and assert both C++ headers use the same override prefix.
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter3-forge.md:60:# Namespace override fixture (requires --namespace):
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter3-forge.md:62:cp -r "$PROJECT/tests/fixtures/namespace_override/project" "$TMPDIR/project"
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter3-forge.md:63:PYTHONPATH="$PROJECT/src" python -m typist.cli gen --namespace foo::bar "$TMPDIR/project/alpha/typist/constants.py"
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter3-forge.md:64:rm -rf "$PROJECT/tests/goldens/gen/namespace_override"
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter3-forge.md:65:cp -r "$TMPDIR/project/gen" "$PROJECT/tests/goldens/gen/namespace_override"
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:26:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:476:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:491:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:593:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:994:    gen_parser.add_argument("--namespace", default=None)
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1012:                run_gen(args.path, namespace=args.namespace)
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1048:from piketype.validate.namespace import check_duplicate_basenames, validate_cpp_namespace
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1051:def run_gen(path: str, *, namespace: str | None = None) -> None:
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1053:    if namespace is not None:
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1054:        validate_cpp_namespace(namespace)
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1061:    if namespace is not None:
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1096:    emit_cpp(repo, namespace=namespace)
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1196:src/piketype/backends/cpp/emitter.py:32:def emit_cpp(repo: RepoIR, *, namespace: str | None = None) -> list[Path]:
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1201:src/piketype/backends/cpp/emitter.py:42:        output_path.write_text(render_module_hpp(module, namespace=namespace), encoding="utf-8")
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1271:src/piketype/cli.py:39:                run_gen(args.path, namespace=args.namespace)
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1272:src/piketype/commands/gen.py:21:def run_gen(path: str, *, namespace: str | None = None) -> None:
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1338:1. Resolved — NFR-1, AC-F4, AC-F5 now use `piketype gen <dsl-file>` and `piketype.commands.gen.run_gen(path, namespace=None)`.
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:1364:1. Resolved — NFR-1, AC-F4, AC-F5 now use `piketype gen <dsl-file>` and `piketype.commands.gen.run_gen(path, namespace=None)`.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:5:requires multiple modules; and invalid namespace tests are split out from golden
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:10:- **Issue:** FR-2 validates namespace segments individually, but FR-4 creates the
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:12:  namespace values that pass FR-2 can still generate reserved macro identifiers.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:13:  For example, `--namespace foo_` with `constants.py` produces
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:14:  `FOO__CONSTANTS_TYPES_HPP`, and `--namespace foo::_bar` produces
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:17:  user-provided namespace alone.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:19:  constrain namespace segments so guard composition cannot create reserved macro
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:20:  names. At minimum, reject namespace values that would make the final guard
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:30:  `typist gen --namespace "foo::_Bar" <path>` and assert the reserved identifier
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:36:  namespace segment. Iteration 3 explicitly moves basename keyword/identifier
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:38:  current generator already emits file-stem-derived C++ namespace segments, but
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:39:  it means FR-2 must not be read as validating the full generated namespace.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md:41:  track basename/path-derived namespace validation as a separate correctness
./specs/010-jinja-template-migration/artifacts/specification/iter4-forge.md:37:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/specification/iter4-forge.md:52:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/specification/iter4-forge.md:154:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:88:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:103:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:205:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:305:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:678:src/piketype/cli.py:39:                run_gen(args.path, namespace=args.namespace)
./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:679:src/piketype/commands/gen.py:21:def run_gen(path: str, *, namespace: str | None = None) -> None:
./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:745:1. Resolved — NFR-1, AC-F4, AC-F5 now use `piketype gen <dsl-file>` and `piketype.commands.gen.run_gen(path, namespace=None)`.
./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:771:1. Resolved — NFR-1, AC-F4, AC-F5 now use `piketype gen <dsl-file>` and `piketype.commands.gen.run_gen(path, namespace=None)`.
./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:920:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:935:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter2-forge.md:55:# Namespace override fixture (requires --namespace):
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter2-forge.md:57:cp -r tests/fixtures/namespace_override/project regen/project
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter2-forge.md:58:PYTHONPATH=src python -m typist.cli gen --namespace foo::bar regen/project/alpha/typist/constants.py
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter2-forge.md:59:cp -r regen/project/gen/* tests/goldens/gen/namespace_override/
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:1:# Spec 002: `--namespace` CLI Argument for C++ Namespace Override
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:5:Add a `--namespace` CLI argument to `typist gen` that lets users specify a custom
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:6:top-level C++ namespace prefix. Today, the C++ namespace is derived entirely from
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:8:out). This feature gives users explicit control over the generated C++ namespace
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:14:typist gen --namespace foo::bar constants.py
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:20:namespace foo::bar::constants {
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:22:}  // namespace foo::bar::constants
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:25:Instead of the current path-derived namespace (e.g., `alpha::constants`).
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:29:1. **As a hardware/firmware engineer**, I want to specify the C++ namespace for
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:31:   namespace hierarchy, without being forced to mirror the DSL file-system layout.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:34:   namespace so that CI scripts can target different namespace schemes per build
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:39:### FR-1: New `--namespace` argument on the `gen` subcommand
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:41:The `gen` subcommand accepts an optional `--namespace <value>` argument.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:43:- `<value>` is a `::` -separated C++ namespace path (e.g., `foo`, `foo::bar`,
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:46:  (path-derived namespace with `typist` segment filtered).
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:61:   words (e.g., `class`, `namespace`, `return`, `int`, `void`, etc.) and rejects
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:83:### FR-3: C++ namespace composition
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:85:When `--namespace` is provided, the generated C++ namespace for a module is:
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:88:<namespace_value>::<module_basename>
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:93:parts is bypassed entirely — the user-provided namespace replaces it.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:95:When `--namespace` is **not** provided, the existing path-derived behaviour is
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:100:When `--namespace` is provided, the include guard follows the same composition:
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:109:When omitted, the existing guard derivation from `namespace_parts` is unchanged.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:113:The `--namespace` argument affects **only** generated C++ module headers (the
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:118:- Manifest `namespace_parts`
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:121:  keep their existing `typist_runtime` namespace and include guards unchanged.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:124:are file-path-derived. Runtime headers have a fixed, well-known namespace.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:125:A C++ namespace override should not silently alter any of these.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:129:The namespace override value is carried from CLI → `run_gen` → C++ emitter. It
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:130:does **not** modify `ModuleRefIR.namespace_parts` in the IR. Instead, it is
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:136:When `--namespace` is specified, it applies to **every** module discovered in the
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:138:in the run use the same namespace prefix.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:141:in the repo. Applying the namespace only to the targeted module would create an
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:146:When `--namespace` is specified, the tool validates that no two discovered
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:151:Rationale: With `--namespace`, the C++ namespace is `<prefix>::<basename>`. If
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:153:`beta/typist/types.py`), they would produce identical namespaces
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:162:`--namespace` value, consistent with the project constitution.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:171:When `--namespace` is omitted, all generated outputs are byte-for-byte identical
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:176:1. `typist gen --namespace foo::bar <path>` produces C++ headers where every
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:177:   module's namespace is `foo::bar::<module_basename>`.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:178:2. `typist gen --namespace foo::bar <path>` produces C++ headers where the
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:180:3. `typist gen <path>` (no `--namespace`) produces output identical to the
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:182:4. `typist gen --namespace "foo::::bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:184:5. `typist gen --namespace "123bad" <path>` exits with a validation error and
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:186:6. `typist gen --namespace "class" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:188:7. `typist gen --namespace "foo__bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:190:8. `typist gen --namespace "_foo" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:192:9. `typist gen --namespace "std::types" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:194:10. `typist gen --namespace "foo_" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:196:11. `typist gen --namespace "foo::_Bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:198:12. `typist gen --namespace foo::bar <path>` does **not** alter SV, Python,
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:200:13. When `--namespace` is used on a repo with two modules sharing the same
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:202:14. Golden-file integration test: at least one positive case using `--namespace`
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:204:    path-derived namespaces. The test verifies that both C++ headers use the
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:206:15. Negative CLI tests: at least one test per invalid-namespace category (empty
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:215:- Per-module namespace overrides (one namespace for module A, another for B).
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:218:- Modifying the IR `namespace_parts` field — it stays path-derived.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:219:- Changing the output file path based on `--namespace` — files stay in the
./specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md:223:  namespaces by the existing codebase without such checks. Adding that would be
./tests/goldens/gen/const_cpp_wide/piketype_manifest.json:35:      "namespace_parts": [
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:1:# Spec 002: `--namespace` CLI Argument for C++ Namespace Override
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:5:Add a `--namespace` CLI argument to `typist gen` that lets users specify a custom
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:6:top-level C++ namespace prefix. Today, the C++ namespace is derived entirely from
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:8:out). This feature gives users explicit control over the generated C++ namespace
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:14:typist gen --namespace foo::bar constants.py
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:20:namespace foo::bar::constants {
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:22:}  // namespace foo::bar::constants
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:25:Instead of the current path-derived namespace (e.g., `alpha::constants`).
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:29:1. **As a hardware/firmware engineer**, I want to specify the C++ namespace for
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:31:   namespace hierarchy, without being forced to mirror the DSL file-system layout.
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:34:   namespace so that CI scripts can target different namespace schemes per build
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:39:### FR-1: New `--namespace` argument on the `gen` subcommand
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:41:The `gen` subcommand accepts an optional `--namespace <value>` argument.
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:43:- `<value>` is a `::` -separated C++ namespace path (e.g., `foo`, `foo::bar`,
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:46:  (path-derived namespace with `typist` segment filtered).
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:62:   words (e.g., `class`, `namespace`, `return`, `int`, `void`, etc.) and rejects
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:76:After segment validation passes, compute the **namespace guard prefix** by
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:85:this check validates **only the namespace-derived prefix**, not the full include
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:91:### FR-3: C++ namespace composition
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:93:When `--namespace` is provided, the generated C++ namespace for a module is:
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:96:<namespace_value>::<module_basename>
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:101:parts is bypassed entirely — the user-provided namespace replaces it.
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:103:When `--namespace` is **not** provided, the existing path-derived behaviour is
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:108:When `--namespace` is provided, the include guard follows the same composition:
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:117:When omitted, the existing guard derivation from `namespace_parts` is unchanged.
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:121:The `--namespace` argument affects **only** generated C++ module headers (the
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:126:- Manifest `namespace_parts`
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:129:  keep their existing `typist_runtime` namespace and include guards unchanged.
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:132:are file-path-derived. Runtime headers have a fixed, well-known namespace.
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:133:A C++ namespace override should not silently alter any of these.
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:137:The namespace override value is carried from CLI → `run_gen` → C++ emitter. It
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:138:does **not** modify `ModuleRefIR.namespace_parts` in the IR. Instead, it is
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:144:When `--namespace` is specified, it applies to **every** module discovered in the
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:146:in the run use the same namespace prefix.
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:149:in the repo. Applying the namespace only to the targeted module would create an
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:154:When `--namespace` is specified, the tool validates that no two discovered
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:159:Rationale: With `--namespace`, the C++ namespace is `<prefix>::<basename>`. If
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:161:`beta/typist/types.py`), they would produce identical namespaces
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:170:`--namespace` value, consistent with the project constitution.
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:179:When `--namespace` is omitted, all generated outputs are byte-for-byte identical
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:184:1. `typist gen --namespace foo::bar <path>` produces C++ headers where every
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:185:   module's namespace is `foo::bar::<module_basename>`.
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:186:2. `typist gen --namespace foo::bar <path>` produces C++ headers where the
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:188:3. `typist gen <path>` (no `--namespace`) produces output identical to the
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:190:4. `typist gen --namespace "foo::::bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:192:5. `typist gen --namespace "123bad" <path>` exits with a validation error and
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:194:6. `typist gen --namespace "class" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:196:7. `typist gen --namespace "foo__bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:198:8. `typist gen --namespace "_foo" <path>` exits with a validation error (leading
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:200:9. `typist gen --namespace "std::types" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:202:10. `typist gen --namespace "foo_" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:204:11. `typist gen --namespace "foo::_bar" <path>` exits with a validation error
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:206:12. `typist gen --namespace foo::bar <path>` does **not** alter SV, Python,
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:208:13. When `--namespace` is used on a repo with two modules sharing the same
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:210:14. Golden-file integration test: at least one positive case using `--namespace`
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:212:    path-derived namespaces. The test verifies that both C++ headers use the
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:214:15. Negative CLI tests: at least one test per invalid-namespace category (empty
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:223:- Per-module namespace overrides (one namespace for module A, another for B).
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:226:- Modifying the IR `namespace_parts` field — it stays path-derived.
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:227:- Changing the output file path based on `--namespace` — files stay in the
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:231:  namespaces by the existing codebase without such checks. The composition-level
./specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md:232:  check in FR-2 validates only the namespace-derived prefix, not the full
./tests/goldens/gen/const_cpp_wide/cpp/alpha/piketype/constants_types.hpp:10:namespace alpha::constants {
./tests/goldens/gen/const_cpp_wide/cpp/alpha/piketype/constants_types.hpp:15:}  // namespace alpha::constants
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter4-forge.md:60:# Namespace override fixture (requires --namespace):
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter4-forge.md:62:cp -r "$PROJECT/tests/fixtures/namespace_override/project" "$TMPDIR/project"
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter4-forge.md:63:PYTHONPATH="$PROJECT/src" python3 -m typist.cli gen --namespace foo::bar "$TMPDIR/project/alpha/typist/constants.py"
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter4-forge.md:64:rm -rf "$PROJECT/tests/goldens/gen/namespace_override"
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter4-forge.md:65:cp -r "$TMPDIR/project/gen" "$PROJECT/tests/goldens/gen/namespace_override"
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:348:- **[NEEDS CLARIFICATION Q-3]** View-model shape for nested constructs (e.g., struct fields containing references to other types): should the field view model carry a precomputed `type_class_name: str` plus a `width: int` (flat denormalized form), or should it carry a reference to a sibling view-model dataclass (`field_type: ScalarViewModel | EnumViewModel`)? Flat form is simpler for templates; nested form preserves more structure. **Recommendation:** flat denormalized form for first migration (Python backend), revisit if it proves limiting. Confirm.
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:367:tests/test_namespace_validation.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:368:specs/002-namespace-cli-argument/spec.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:393:tests/goldens/gen/namespace_override/piketype_manifest.json
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:399:specs/002-namespace-cli-argument/artifacts/validation/validation.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:408:specs/002-namespace-cli-argument/artifacts/retrospect/retrospect.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:419:specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge-prompt.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:420:specs/002-namespace-cli-argument/artifacts/specification/iter3-forge.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:421:specs/002-namespace-cli-argument/artifacts/specification/iter2-forge.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:422:specs/002-namespace-cli-argument/artifacts/specification/iter2-gauge.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:423:specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:424:specs/002-namespace-cli-argument/artifacts/specification/iter4-forge.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:425:specs/002-namespace-cli-argument/artifacts/specification/iter5-forge.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:426:specs/002-namespace-cli-argument/artifacts/specification/iter5-gauge.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:427:specs/002-namespace-cli-argument/artifacts/specification/iter4-gauge.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:428:specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:429:specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:430:specs/002-namespace-cli-argument/artifacts/specification/iter2-gauge-prompt.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:431:specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge-prompt.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:432:specs/002-namespace-cli-argument/artifacts/specification/iter4-gauge-prompt.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:434:tests/goldens/gen/namespace_override/cpp/alpha/piketype/constants_types.hpp
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:445:specs/002-namespace-cli-argument/artifacts/planning/iter1-gauge-prompt.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:451:specs/002-namespace-cli-argument/artifacts/planning/plan.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:452:tests/goldens/gen/namespace_override/cpp/runtime/piketype_runtime.cpp
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:454:tests/goldens/gen/namespace_override/cpp/runtime/piketype_runtime.hpp
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:501:specs/002-namespace-cli-argument/artifacts/clarification/clarification.md
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:518:tests/goldens/gen/namespace_override/cpp/beta/piketype/more_types.hpp
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:589:tests/goldens/gen/namespace_override/py/alpha/piketype/constants_types.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:590:tests/goldens/gen/namespace_override/py/alpha/piketype/__init__.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:594:tests/goldens/gen/namespace_override/py/alpha/__init__.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:595:tests/goldens/gen/namespace_override/py/__init__.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:598:tests/goldens/gen/namespace_override/py/runtime/piketype_runtime.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:599:tests/goldens/gen/namespace_override/py/runtime/__init__.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:651:tests/goldens/gen/namespace_override/py/beta/piketype/more_types.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:652:tests/goldens/gen/namespace_override/py/beta/piketype/__init__.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:653:tests/goldens/gen/namespace_override/py/beta/__init__.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:674:src/piketype/validate/namespace.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:717:tests/goldens/gen/namespace_override/sv/alpha/piketype/constants_pkg.sv
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:732:tests/goldens/gen/namespace_override/sv/runtime/piketype_runtime_pkg.sv
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:777:tests/goldens/gen/namespace_override/sv/beta/piketype/more_pkg.sv
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:781:tests/fixtures/namespace_override/project/alpha/piketype/__pycache__/constants.cpython-314.pyc
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:782:tests/fixtures/namespace_override/project/alpha/piketype/constants.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:802:tests/fixtures/namespace_override/project/beta/piketype/more.py
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:809:tests/fixtures/namespace_override/project/beta/piketype/__pycache__/more.cpython-314.pyc
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:1107:src/piketype/backends/cpp/emitter.py:32:def emit_cpp(repo: RepoIR, *, namespace: str | None = None) -> list[Path]:
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:1108:src/piketype/backends/cpp/emitter.py:42:        output_path.write_text(render_module_hpp(module, namespace=namespace), encoding="utf-8")
./specs/010-jinja-template-migration/artifacts/specification/iter1-gauge.md:1109:src/piketype/backends/cpp/emitter.py:47:def render_module_hpp(module: ModuleIR, *, namespace: str | None = None) -> str:
./specs/002-namespace-cli-argument/artifacts/specification/iter4-gauge.md:8:- **Suggestion:** Either validate only the namespace-derived guard prefix before discovery, or make full per-module include-guard validation in scope.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-gauge.md:13:- **Suggestion:** Add a negative test for `typist gen --namespace "foo::_bar" <path>`.
./tests/goldens/gen/scalar_sv_basic/piketype_manifest.json:25:      "namespace_parts": [
./specs/010-jinja-template-migration/artifacts/specification/iter1-forge.md:151:- **[NEEDS CLARIFICATION Q-3]** View-model shape for nested constructs (e.g., struct fields containing references to other types): should the field view model carry a precomputed `type_class_name: str` plus a `width: int` (flat denormalized form), or should it carry a reference to a sibling view-model dataclass (`field_type: ScalarViewModel | EnumViewModel`)? Flat form is simpler for templates; nested form preserves more structure. **Recommendation:** flat denormalized form for first migration (Python backend), revisit if it proves limiting. Confirm.
./tests/goldens/gen/const_cpp_wide/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/const_cpp_wide/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./specs/004-cpp-constexpr-upper-case/artifacts/planning/iter1-gauge.md:7:- **WARNING**: Golden regeneration is underspecified. The plan says to run `typist gen` against each fixture, but fixtures include negative cases without goldens and `namespace_override` requires `--namespace foo::bar`. The plan needs exact regeneration commands or a script.
./tests/goldens/gen/flags_basic/piketype_manifest.json:13:      "namespace_parts": [
./tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:13:namespace alpha::types {
./tests/goldens/gen/scalar_sv_basic/cpp/alpha/piketype/types_types.hpp:176:}  // namespace alpha::types
./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge-prompt.md:7:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge.md:7:- **Issue:** The regex accepts C++ keywords and reserved identifiers such as `class`, `namespace`, `__foo`, or `_Bar`. Those can produce invalid or reserved C++ namespaces/include guards despite passing validation. The final namespace also includes `<module_basename>`, but the spec does not require validating that segment.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge.md:8:- **Suggestion:** Define validation for every generated namespace segment: user-provided segments plus module basename. Reject C++17 keywords and reserved identifier forms, not just regex failures.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge.md:12:- **Issue:** Applying one prefix to every discovered module and appending only `<module_basename>` means `alpha/typist/types.py` and `beta/typist/types.py` both generate `foo::bar::types`. That silently destroys the path-derived namespace uniqueness the current design relies on.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge.md:13:- **Suggestion:** Specify collision handling. Either reject duplicate module basenames when `--namespace` is used, or include enough path-derived identity in the composed namespace to keep modules distinct. Add a test for two modules with the same basename.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-gauge.md:17:- **Issue:** An invalid namespace should exit before generation, so there is no generated output tree to compare against a golden. Calling this a golden-file integration test is wrong.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:1:# Spec 002: `--namespace` CLI Argument for C++ Namespace Override
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:5:Add a `--namespace` CLI argument to `typist gen` that lets users specify a custom
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:6:top-level C++ namespace prefix. Today, the C++ namespace is derived entirely from
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:8:out). This feature gives users explicit control over the generated C++ namespace
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:14:typist gen --namespace foo::bar constants.py
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:20:namespace foo::bar::constants {
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:22:}  // namespace foo::bar::constants
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:25:Instead of the current path-derived namespace (e.g., `alpha::constants`).
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:29:1. **As a hardware/firmware engineer**, I want to specify the C++ namespace for
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:31:   namespace hierarchy, without being forced to mirror the DSL file-system layout.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:34:   namespace so that CI scripts can target different namespace schemes per build
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:39:### FR-1: New `--namespace` argument on the `gen` subcommand
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:41:The `gen` subcommand accepts an optional `--namespace <value>` argument.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:43:- `<value>` is a `::` -separated C++ namespace path (e.g., `foo`, `foo::bar`,
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:46:  (path-derived namespace with `typist` segment filtered).
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:58:### FR-3: C++ namespace composition
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:60:When `--namespace` is provided, the generated C++ namespace for a module is:
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:63:<namespace_value>::<module_basename>
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:68:parts is bypassed entirely — the user-provided namespace replaces it.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:70:When `--namespace` is **not** provided, the existing path-derived behaviour is
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:75:When `--namespace` is provided, the include guard follows the same composition:
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:84:When omitted, the existing guard derivation from `namespace_parts` is unchanged.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:88:The `--namespace` argument affects **only** the C++ code generation backend.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:89:SystemVerilog package names, Python module paths, manifest `namespace_parts`, and
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:93:are file-path-derived. A C++ namespace override should not silently alter those.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:97:The namespace override value is carried from CLI → `run_gen` → C++ emitter. It
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:98:does **not** modify `ModuleRefIR.namespace_parts` in the IR. Instead, it is
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:104:When `--namespace` is specified, it applies to **every** module discovered in the
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:106:run use the same namespace prefix.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:109:in the repo. Applying the namespace only to the targeted module would create an
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:117:`--namespace` value, consistent with the project constitution.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:126:When `--namespace` is omitted, all generated outputs are byte-for-byte identical
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:131:1. `typist gen --namespace foo::bar <path>` produces C++ headers where every
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:132:   module's namespace is `foo::bar::<module_basename>`.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:133:2. `typist gen --namespace foo::bar <path>` produces C++ headers where the
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:135:3. `typist gen <path>` (no `--namespace`) produces output identical to the
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:137:4. `typist gen --namespace "foo::::bar" <path>` exits with a validation error.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:138:5. `typist gen --namespace "123bad" <path>` exits with a validation error.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:139:6. `typist gen --namespace foo::bar <path>` does **not** alter SV, Python,
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:142:   (`--namespace` with constants and types) and one negative case (invalid
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:143:   namespace value).
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:148:- Per-module namespace overrides (one namespace for module A, another for B).
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:151:- Modifying the IR `namespace_parts` field — it stays path-derived.
./specs/002-namespace-cli-argument/artifacts/specification/iter1-forge.md:152:- Changing the output file path based on `--namespace` — files stay in the
./tests/goldens/gen/flags_basic/cpp/alpha/piketype/types_types.hpp:13:namespace alpha::types {
./tests/goldens/gen/flags_basic/cpp/alpha/piketype/types_types.hpp:431:}  // namespace alpha::types
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge-prompt.md:23:   - Does the sketched Python `ScalarAliasView` / `StructFieldView` / `StructView` carry every field that the current `_render_py_*` functions actually use? Spot-check against `src/piketype/backends/py/emitter.py`. Look especially at: signed sign-extension fields, wide-scalar MSB byte mask, struct alignment bytes, struct field byte_count, struct field default expression.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge-prompt.md:24:   - Does C++/SV need any additional view fields the plan does not mention? (e.g., C++ namespace nesting strings, include guard symbols, SV `_pkg`/`_test_pkg` distinction.)
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge-prompt.md:34:   - C++ `namespace` rendering depending on `--namespace` CLI override.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-gauge-prompt.md:1:# Gauge Review: Specification 002 — `--namespace` CLI Argument (Iteration 2)
./specs/002-namespace-cli-argument/artifacts/specification/iter2-gauge-prompt.md:16:   duplicate basenames when `--namespace` is used. AC-9 tests this.
./specs/002-namespace-cli-argument/artifacts/specification/iter2-gauge-prompt.md:27:Read the updated specification at `specs/002-namespace-cli-argument/spec.md` and the
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:23:    env = make_environment(package="piketype.backends.<lang>")
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:44:- `ModuleView` carries a field `body_lines: tuple[str, ...] | None`. When non-None, the primary template emits `{{ body_lines | join("\n") }}` for the not-yet-templated portion.
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:45:- Each sub-step replaces a portion of `body_lines` with a structured field (`types: tuple[TypeView, ...]`, etc.), and the template's body section transitions from `{% if body_lines %}{{ body_lines | join("\n") }}{% endif %}` to a structured loop over `types`.
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:46:- After sub-step 4 (fragments), `body_lines` is unused and removed from the view; the field is retired in the cleanup commit.
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:60:| `src/piketype/backends/common/render.py`                        | rewrite | `make_environment(*, package: str) -> jinja2.Environment` and `render(*, env: jinja2.Environment, template_name: str, context: object) -> str`. Custom-filter registration site (CL-2/FR-16). |
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:63:| `tests/test_render.py`                                          | new     | `make_environment` / `render` smoke tests; placeholder for future custom-filter tests (CL-2). |
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:86:def make_environment(*, package: str) -> jinja2.Environment:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:113:# Registered by mutating the env returned from make_environment via a hook
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:120:1. `feat(common): add make_environment and render helpers` — `render.py` + `tests/test_render.py`.
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:162:class ConstantView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:167:class ScalarAliasView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:181:class EnumMemberView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:186:class EnumView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:196:class FlagFieldView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:201:class FlagsView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:214:class StructFieldView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:239:class StructView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:244:    fields: tuple[StructFieldView, ...]
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:248:type TypeView = ScalarAliasView | StructView | EnumView | FlagsView
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:251:class ModuleView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:260:    body_lines: tuple[str, ...] | None
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:267:- `_build_struct_field_view(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> StructFieldView`
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:268:- `_build_enum_view(*, type_ir: EnumIR) -> EnumView`
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:269:- `_build_flags_view(*, type_ir: FlagsIR) -> FlagsView`
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:272:Builders are pure functions, no side effects, no IR mutation. Tests in `tests/test_view_py.py` assert that for a fixture's IR, the builder produces a view whose primitive fields equal expected literal values (e.g., for `enum_basic`, `EnumView.mask == 7`).
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:277:2. `feat(py): module skeleton via templates` (FR-6 sub-step 1) — `module.j2` renders header + imports + footer. `emit_py` constructs `ModuleView` with `body_lines = tuple(legacy_render_body_lines(module))` and the template emits `{{ body_lines | join("\n") }}` for the body. **Byte parity preserved.**
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:278:3. `feat(py): top-level type declaration skeletons via templates` (FR-6 sub-step 2) — `_macros.j2` adds `scalar_class_skeleton`, `struct_class_skeleton`, `enum_classes_skeleton`, `flags_class_skeleton` macros that emit *only the class header lines* (`class X:`, `WIDTH = ...`, `BYTE_COUNT = ...`). Helper-method bodies and expression fragments still arrive as `body_lines_per_type: tuple[str, ...]` strings on each TypeView. The view is augmented with `helper_lines: tuple[str, ...]` per TypeView temporarily. **Byte parity preserved.**
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:280:5. `feat(py): expression and field-level fragments` (FR-6 sub-step 4) — expressions like Python constants, enum member values, and flag mask literals are now rendered from view-model `*_expr: str` fields directly in templates (no Python concatenation). Also handles struct field annotations/defaults/coercer literals. The transitional `body_lines` field on `ModuleView` is now always `None` and removed in this commit. **Byte parity preserved.**
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:298:class CppNamespaceView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:299:    open_lines: tuple[str, ...]   # ["namespace alpha {", "namespace piketype {"]
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:300:    close_lines: tuple[str, ...]  # ["}  // namespace piketype", "}  // namespace alpha"]
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:304:class CppGuardView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:308:class CppStructFieldView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:331:class CppModuleView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:334:    namespace: CppNamespaceView
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:341:    types: tuple[TypeView, ...]          # CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:342:    body_lines: tuple[str, ...] | None   # transitional same as Phase 1
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:345:`CppScalarAliasView`, `CppEnumView`, `CppFlagsView` follow the same shape pattern as Python's: precomputed primitives + literal strings, no IR refs, no methods.
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:349:**`--namespace` CLI override:** the namespace builder respects `emit_cpp(repo, *, namespace=None)`. The view's `CppNamespaceView` is constructed from either `module.ref.namespace_parts` (default) or the CLI override (test in `tests/test_view_cpp.py` includes a fixture run with an override).
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:354:2. `feat(cpp): module skeleton via templates` (header, guard open, includes, namespace open, namespace close, guard close).
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:375:class SvConstantView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:381:class SvTypedefView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:396:class SvSynthModuleView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:402:    body_lines: tuple[str, ...] | None     # transitional
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:405:class SvHelperFieldView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:419:class SvHelperClassView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:433:class SvTestModuleView:
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:438:    body_lines: tuple[str, ...] | None     # transitional
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:484:| Whitespace drift on first template render breaks goldens | High | `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True` in `make_environment`. Migrate one sub-step at a time and diff goldens after each commit. The transitional `body_lines | join("\n")` mechanism preserves line-by-line legacy output verbatim until each sub-step replaces it. |
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:485:| Jinja `trim_blocks`/`lstrip_blocks` interacting unexpectedly with literal-heavy template content (e.g., generated SV helper classes containing `begin`/`end` blocks) | Medium | When a literal-heavy block must be preserved verbatim, wrap it in `{% raw %}...{% endraw %}` or pass it through as a precomputed `str` field on the view (the `body_lines` mechanism). Phase 3 commit 4 explicitly tests this on the largest SV `_helper_class` block. |
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:491:| C++ `--namespace` CLI override regression | Medium | `tests/test_view_cpp.py` runs the namespace-override fixture (`tests/fixtures/namespace_override`) end-to-end, asserting the rendered guard macro and namespace open/close strings. This catches regressions before goldens. |
./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:517:- **C++ namespace override tests:** explicit end-to-end run of the namespace-override fixture in `tests/test_view_cpp.py`.
./tests/goldens/gen/scalar_sv_basic/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/scalar_sv_basic/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge-prompt.md:1:# Gauge Review: Specification 002 — `--namespace` CLI Argument (Iteration 3)
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge-prompt.md:16:   fixture to contain at least two modules with different path-derived namespaces.
./specs/002-namespace-cli-argument/artifacts/specification/iter3-gauge-prompt.md:20:Read the updated specification at `specs/002-namespace-cli-argument/spec.md` and the
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:31:8. WARNING — `make_environment` env options + keyword-only signature not pinned.
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:32:9. NOTE — C++ `--namespace` override.
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:45:   - Does the new `body_lines: tuple[str, ...] | None` passthrough mechanism violate FR-8/FR-9 (it's a primitive `tuple` of `str`, so it should comply, but verify)?
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:48:     - `_render_py_enum` → `EnumView` should carry `mask`, `first_member_name`, `enum_class_name`, `width`, `byte_count`.
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:49:     - `_render_py_flags` → `FlagsView` should carry `data_mask`, `total_bits`, plus per-flag `bit_mask`.
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:50:     - `_render_py_struct_field_coercer` → `StructFieldView` discriminators must distinguish struct-ref / flags-ref / enum-ref / scalar-ref / narrow-scalar / wide-scalar.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-gauge-prompt.md:1:# Gauge Review: Specification 002 — `--namespace` CLI Argument (Iteration 4)
./specs/002-namespace-cli-argument/artifacts/specification/iter4-gauge-prompt.md:14:   `typist gen --namespace "foo::_Bar" <path>`.
./specs/002-namespace-cli-argument/artifacts/specification/iter4-gauge-prompt.md:21:Read the updated specification at `specs/002-namespace-cli-argument/spec.md` and the
./tests/goldens/gen/struct_multiple_of/piketype_manifest.json:13:      "namespace_parts": [
./specs/004-cpp-constexpr-upper-case/artifacts/clarification/iter1-gauge.md:5:**WARNING — Catalogue wording is not literally complete.** The Forge says "No other `constexpr` identifiers exist," but `src/typist/backends/cpp/emitter.py` also emits namespace-scope user-defined constants via `constexpr {cpp_type} {const.name}` at line 72. Q2 covers these as user-defined/out of scope, so the implementation scope is still clear, but the catalogue statement is imprecise.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:42:   - Does the sketched Python `ScalarAliasView` / `StructFieldView` / `StructView` carry every field that the current `_render_py_*` functions actually use? Spot-check against `src/piketype/backends/py/emitter.py`. Look especially at: signed sign-extension fields, wide-scalar MSB byte mask, struct alignment bytes, struct field byte_count, struct field default expression.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:43:   - Does C++/SV need any additional view fields the plan does not mention? (e.g., C++ namespace nesting strings, include guard symbols, SV `_pkg`/`_test_pkg` distinction.)
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:53:   - C++ `namespace` rendering depending on `--namespace` CLI override.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:299:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:314:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:416:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:538:    env = make_environment("piketype.backends.<lang>")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:563:| `src/piketype/backends/common/render.py`      | rewrite | Stub → `make_environment(*, package: str) -> jinja2.Environment` and `render(*, env, template_name, context) -> str`. Custom-filter registration site (FR-2/3, CL-2). |
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:566:| `tests/test_render.py`                        | new     | `make_environment` / `render` smoke tests; placeholder for future custom-filter tests (CL-2). |
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:576:1. `feat(common): add make_environment and render helpers` — `render.py` + `tests/test_render.py`.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:611:class ScalarAliasView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:625:class StructFieldView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:641:class StructView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:645:    fields: tuple[StructFieldView, ...]
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:650:class EnumMemberView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:655:class EnumView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:661:class FlagsView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:668:class ConstantView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:673:class ModuleView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:680:    types: tuple[ScalarAliasView | StructView | EnumView | FlagsView, ...]
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:708:- View must precompute namespace nesting strings, include-guard symbol, and full pack/unpack helper bodies.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:716:2. `feat(cpp): module/file skeleton via template (header, includes, namespace open/close, guard)`.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:817:The plan has the expected high-level phase order, but the review hinges on whether the sketched view models actually cover current renderer state. I’m spot-checking the Python, C++, and SV emitters now, especially signed/wide scalar paths, struct defaults, package naming, and namespace handling.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:819:/bin/zsh -lc 'rg -n "def _render_sv|def render_module_sv|_pkg|_test_pkg|typedef struct|class|to_bytes|from_bytes|packed|byte|signed|mask|package|_render" src/piketype/backends/sv/emitter.py' in /Users/ezchi/Projects/pike-type
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:821:/bin/zsh -lc 'rg -n "def _render_py|def render_module_py|sign|msb|mask|alignment|default|byte_count|to_bytes|from_bytes|Flags|Enum|Constant|_render" src/piketype/backends/py/emitter.py' in /Users/ezchi/Projects/pike-type
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:823:/bin/zsh -lc 'rg -n "def _render_cpp|def render_module_cpp|namespace|guard|include|to_bytes|from_bytes|pack|unpack|byte_count|signed|mask|default|_render" src/piketype/backends/cpp/emitter.py' in /Users/ezchi/Projects/pike-type
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:830:68:    body_lines = [f"package {module.ref.basename}_pkg;"]
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:835:94:    body_lines.append("endpackage")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:836:98:def _render_sv_type_block(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:845:126:def _render_sv_width_value(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:847:135:def _render_sv_scalar_alias(*, type_ir: ScalarAliasIR) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:851:146:def _render_sv_struct(*, type_ir: StructIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:855:166:def _render_sv_struct_field_type(*, field_type: FieldTypeIR) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:860:177:def _render_sv_flags(*, type_ir: FlagsIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:863:191:def _render_sv_enum(*, type_ir: EnumIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:864:201:def _render_sv_pack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:865:245:def _render_sv_unpack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:872:322:            body_lines.extend(f"  {line}" for line in _render_sv_scalar_helper_class(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:873:324:            body_lines.extend(f"  {line}" for line in _render_sv_struct_helper_class(type_ir=type_ir, type_index=type_index))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:874:326:            body_lines.extend(f"  {line}" for line in _render_sv_flags_helper_class(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:875:328:            body_lines.extend(f"  {line}" for line in _render_sv_enum_helper_class(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:876:329:    body_lines.append("endpackage")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:877:333:def _render_sv_scalar_helper_class(*, type_ir: ScalarAliasIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:900:428:def _render_sv_struct_helper_class(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:937:563:def _render_sv_flags_helper_class(*, type_ir: FlagsIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:961:674:def _render_sv_enum_helper_class(*, type_ir: EnumIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:981:756:def _render_sv_helper_field_decl(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:984:768:def _render_sv_helper_to_bytes_step(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:996:799:def _render_sv_helper_from_bytes_step(
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1010:846:def _render_sv_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1022:866:def _render_sv_expr(*, expr: ExprIR) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1049:63:            body_lines.append("from enum import IntEnum")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1050:65:    body_lines.extend(f"{const.name} = {_render_py_expr(expr=const.expr)}" for const in module.constants)
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1051:72:            body_lines.extend(_render_py_scalar_alias(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1052:74:            body_lines.extend(_render_py_struct(type_ir=type_ir, type_index=type_index))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1054:76:            body_lines.extend(_render_py_flags(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1056:78:            body_lines.extend(_render_py_enum(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1057:99:def _render_py_expr(*, expr: ExprIR) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1060:114:def _render_py_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1098:311:def _render_py_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1110:360:def _render_py_struct_to_bytes(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1127:412:def _render_py_struct_from_bytes(*, type_ir: StructIR, class_name: str, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1148:480:def _render_py_field_annotation(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1149:495:def _render_py_field_default(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1153:508:def _render_py_struct_field_coercer(*, owner_name: str, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1176:634:def _render_py_enum(*, type_ir: EnumIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1190:707:def _render_py_flags(*, type_ir: FlagsIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1211:32:def emit_cpp(repo: RepoIR, *, namespace: str | None = None) -> list[Path]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1212:42:        output_path.write_text(render_module_hpp(module, namespace=namespace), encoding="utf-8")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1213:47:def render_module_hpp(module: ModuleIR, *, namespace: str | None = None) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1214:50:    if namespace is not None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1215:51:        guard = f"{namespace.replace('::', '_')}_{module.ref.basename}_types_hpp".upper()
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1216:52:        ns = f"{namespace}::{module.ref.basename}"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1217:54:        guard = "_".join((*module.ref.namespace_parts, "types_hpp")).upper().replace(".", "_")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1218:55:        ns = "::".join(part for part in module.ref.namespace_parts if part != "piketype")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1219:58:    body_lines = [f"#ifndef {guard}", f"#define {guard}", "", "#include <cstdint>"]
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1220:60:        body_lines.extend(["#include <cstddef>", "#include <stdexcept>", "#include <vector>"])
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1221:63:        body_lines.append(f"namespace {ns} {{")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1225:82:            body_lines.extend(_render_cpp_scalar_alias(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1226:84:            body_lines.extend(_render_cpp_struct(type_ir=type_ir, type_index=type_index))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1227:86:            body_lines.extend(_render_cpp_flags(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1228:88:            body_lines.extend(_render_cpp_enum(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1229:91:        body_lines.append(f"}}  // namespace {ns}")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1230:92:    body_lines.extend(["", f"#endif  // {guard}"])
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1231:96:def _render_cpp_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1237:109:def _render_cpp_expr(*, expr: ExprIR) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1240:129:def _render_cpp_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1271:347:def _render_cpp_enum(*, type_ir: EnumIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1281:428:def _render_cpp_flags(*, type_ir: FlagsIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1308:547:def _render_cpp_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1318:637:def _render_cpp_field_decl(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1322:644:def _render_cpp_field_type(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1325:657:def _render_cpp_field_default(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1329:676:def _render_cpp_struct_pack_step(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1334:724:def _render_cpp_struct_unpack_step(
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1338:770:def _render_cpp_inline_scalar_helpers(*, owner_name: str, field_ir: StructFieldIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1403:    55	    body_lines: list[str] = []
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1405:    57	        body_lines.append("from __future__ import annotations")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1407:    59	            body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1408:    60	            body_lines.append("from dataclasses import dataclass, field")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1410:    62	            body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1411:    63	            body_lines.append("from enum import IntEnum")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1412:    64	        body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1413:    65	    body_lines.extend(f"{const.name} = {_render_py_expr(expr=const.expr)}" for const in module.constants)
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1415:    67	        body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1418:    70	            body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1420:    72	            body_lines.extend(_render_py_scalar_alias(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1422:    74	            body_lines.extend(_render_py_struct(type_ir=type_ir, type_index=type_index))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1424:    76	            body_lines.extend(_render_py_flags(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1426:    78	            body_lines.extend(_render_py_enum(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1427:    79	    return f"{header}\n" + "\n".join(body_lines) + "\n"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1441:   114	def _render_py_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1637:   311	def _render_py_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1686:   360	def _render_py_struct_to_bytes(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1738:   412	def _render_py_struct_from_bytes(*, type_ir: StructIR, class_name: str, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1806:   480	def _render_py_field_annotation(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1821:   495	def _render_py_field_default(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1834:   508	def _render_py_struct_field_coercer(*, owner_name: str, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:1957:   634	def _render_py_enum(*, type_ir: EnumIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2030:   707	def _render_py_flags(*, type_ir: FlagsIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2116:    32	def emit_cpp(repo: RepoIR, *, namespace: str | None = None) -> list[Path]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2126:    42	        output_path.write_text(render_module_hpp(module, namespace=namespace), encoding="utf-8")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2131:    47	def render_module_hpp(module: ModuleIR, *, namespace: str | None = None) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2134:    50	    if namespace is not None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2135:    51	        guard = f"{namespace.replace('::', '_')}_{module.ref.basename}_types_hpp".upper()
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2136:    52	        ns = f"{namespace}::{module.ref.basename}"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2138:    54	        guard = "_".join((*module.ref.namespace_parts, "types_hpp")).upper().replace(".", "_")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2139:    55	        ns = "::".join(part for part in module.ref.namespace_parts if part != "piketype")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2142:    58	    body_lines = [f"#ifndef {guard}", f"#define {guard}", "", "#include <cstdint>"]
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2144:    60	        body_lines.extend(["#include <cstddef>", "#include <stdexcept>", "#include <vector>"])
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2145:    61	    body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2147:    63	        body_lines.append(f"namespace {ns} {{")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2148:    64	        body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2159:    75	        body_lines.append(f"constexpr {cpp_type} {const.name} = {cpp_expr};")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2161:    77	        body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2164:    80	            body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2166:    82	            body_lines.extend(_render_cpp_scalar_alias(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2168:    84	            body_lines.extend(_render_cpp_struct(type_ir=type_ir, type_index=type_index))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2170:    86	            body_lines.extend(_render_cpp_flags(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2172:    88	            body_lines.extend(_render_cpp_enum(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2174:    90	        body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2175:    91	        body_lines.append(f"}}  // namespace {ns}")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2176:    92	    body_lines.extend(["", f"#endif  // {guard}"])
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2177:    93	    return f"{header}\n" + "\n".join(body_lines) + "\n"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2180:    96	def _render_cpp_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2181:   129	def _render_cpp_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2398:   347	def _render_cpp_enum(*, type_ir: EnumIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2479:   428	def _render_cpp_flags(*, type_ir: FlagsIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2597:   547	def _render_cpp_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2687:   637	def _render_cpp_field_decl(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2694:   644	def _render_cpp_field_type(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2707:   657	def _render_cpp_field_default(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2726:   676	def _render_cpp_struct_pack_step(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2774:   724	def _render_cpp_struct_unpack_step(
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:2820:   770	def _render_cpp_inline_scalar_helpers(*, owner_name: str, field_ir: StructFieldIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3115:    68	    body_lines = [f"package {module.ref.basename}_pkg;"]
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3132:    85	        body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3134:    87	        body_lines.extend(const_lines)
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3136:    89	        body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3139:    92	            body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3140:    93	        body_lines.extend(type_block)
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3141:    94	    body_lines.append("endpackage")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3142:    95	    return f"{header}\n" + "\n".join(body_lines) + "\n"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3145:    98	def _render_sv_type_block(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3171:   126	def _render_sv_width_value(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3180:   135	def _render_sv_scalar_alias(*, type_ir: ScalarAliasIR) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3191:   146	def _render_sv_struct(*, type_ir: StructIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3211:   166	def _render_sv_struct_field_type(*, field_type: FieldTypeIR) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3222:   177	def _render_sv_flags(*, type_ir: FlagsIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3236:   191	def _render_sv_enum(*, type_ir: EnumIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3246:   201	def _render_sv_pack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3290:   245	def _render_sv_unpack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3360:   315	    body_lines = [
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3365:   320	        body_lines.append("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3367:   322	            body_lines.extend(f"  {line}" for line in _render_sv_scalar_helper_class(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3369:   324	            body_lines.extend(f"  {line}" for line in _render_sv_struct_helper_class(type_ir=type_ir, type_index=type_index))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3371:   326	            body_lines.extend(f"  {line}" for line in _render_sv_flags_helper_class(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3373:   328	            body_lines.extend(f"  {line}" for line in _render_sv_enum_helper_class(type_ir=type_ir))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3374:   329	    body_lines.append("endpackage")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3375:   330	    return f"{header}\n" + "\n".join(body_lines) + "\n"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3378:   333	def _render_sv_scalar_helper_class(*, type_ir: ScalarAliasIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3471:   428	def _render_sv_struct_helper_class(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3602:   563	def _render_sv_flags_helper_class(*, type_ir: FlagsIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3713:   674	def _render_sv_enum_helper_class(*, type_ir: EnumIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3795:   756	def _render_sv_helper_field_decl(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3807:   768	def _render_sv_helper_to_bytes_step(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3838:   799	def _render_sv_helper_from_bytes_step(
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3880:   846	def _render_sv_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:3900:   866	def _render_sv_expr(*, expr: ExprIR) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4009:    23	    env = make_environment("piketype.backends.<lang>")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4034:    48	| `src/piketype/backends/common/render.py`      | rewrite | Stub → `make_environment(*, package: str) -> jinja2.Environment` and `render(*, env, template_name, context) -> str`. Custom-filter registration site (FR-2/3, CL-2). |
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4037:    51	| `tests/test_render.py`                        | new     | `make_environment` / `render` smoke tests; placeholder for future custom-filter tests (CL-2). |
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4047:    61	1. `feat(common): add make_environment and render helpers` — `render.py` + `tests/test_render.py`.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4082:    96	class ScalarAliasView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4096:   110	class StructFieldView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4112:   126	class StructView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4116:   130	    fields: tuple[StructFieldView, ...]
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4121:   135	class EnumMemberView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4126:   140	class EnumView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4132:   146	class FlagsView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4139:   153	class ConstantView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4144:   158	class ModuleView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4151:   165	    types: tuple[ScalarAliasView | StructView | EnumView | FlagsView, ...]
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4179:   193	- View must precompute namespace nesting strings, include-guard symbol, and full pack/unpack helper bodies.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4187:   201	2. `feat(cpp): module/file skeleton via template (header, includes, namespace open/close, guard)`.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4333:   154	- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4530:/bin/zsh -lc "rg -n \"piketype gen|run_gen|--namespace|namespace\" src/piketype tests -g '*.py'" in /Users/ezchi/Projects/pike-type
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4532:tests/test_namespace_validation.py:1:"""Unit tests for C++ namespace validation."""
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4533:tests/test_namespace_validation.py:9:from piketype.validate.namespace import (
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4534:tests/test_namespace_validation.py:12:    validate_cpp_namespace,
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4535:tests/test_namespace_validation.py:17:    """Tests for validate_cpp_namespace()."""
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4536:tests/test_namespace_validation.py:22:        self.assertEqual(validate_cpp_namespace("foo"), ("foo",))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4537:tests/test_namespace_validation.py:25:        self.assertEqual(validate_cpp_namespace("foo::bar"), ("foo", "bar"))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4538:tests/test_namespace_validation.py:28:        self.assertEqual(validate_cpp_namespace("a::b::c"), ("a", "b", "c"))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4539:tests/test_namespace_validation.py:31:        self.assertEqual(validate_cpp_namespace("foo2::bar3"), ("foo2", "bar3"))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4540:tests/test_namespace_validation.py:37:            validate_cpp_namespace("")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4541:tests/test_namespace_validation.py:41:            validate_cpp_namespace("::foo")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4542:tests/test_namespace_validation.py:46:            validate_cpp_namespace("foo::")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4543:tests/test_namespace_validation.py:51:            validate_cpp_namespace("foo::::bar")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4544:tests/test_namespace_validation.py:58:            validate_cpp_namespace("123bad")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4545:tests/test_namespace_validation.py:63:            validate_cpp_namespace("foo-bar")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4546:tests/test_namespace_validation.py:70:            validate_cpp_namespace("class")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4547:tests/test_namespace_validation.py:73:    def test_rejects_namespace_keyword(self) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4548:tests/test_namespace_validation.py:75:            validate_cpp_namespace("namespace")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4549:tests/test_namespace_validation.py:80:            validate_cpp_namespace("alignas")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4550:tests/test_namespace_validation.py:85:            validate_cpp_namespace("constexpr")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4551:tests/test_namespace_validation.py:90:            validate_cpp_namespace("thread_local")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4552:tests/test_namespace_validation.py:95:            validate_cpp_namespace("noexcept")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4553:tests/test_namespace_validation.py:100:            validate_cpp_namespace("nullptr")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4554:tests/test_namespace_validation.py:105:            validate_cpp_namespace("static_assert")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4555:tests/test_namespace_validation.py:110:            validate_cpp_namespace("foo::int")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4556:tests/test_namespace_validation.py:120:            validate_cpp_namespace("_foo")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4557:tests/test_namespace_validation.py:125:            validate_cpp_namespace("foo::_bar")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4558:tests/test_namespace_validation.py:130:            validate_cpp_namespace("foo::_Bar")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4559:tests/test_namespace_validation.py:137:            validate_cpp_namespace("foo__bar")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4560:tests/test_namespace_validation.py:142:            validate_cpp_namespace("foo::a__b")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4561:tests/test_namespace_validation.py:149:            validate_cpp_namespace("foo_")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4562:tests/test_namespace_validation.py:154:            validate_cpp_namespace("foo::bar_")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4563:tests/test_namespace_validation.py:161:            validate_cpp_namespace("std::types")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4564:tests/test_namespace_validation.py:166:        self.assertEqual(validate_cpp_namespace("foo::std"), ("foo", "std"))
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4565:src/piketype/commands/gen.py:18:from piketype.validate.namespace import check_duplicate_basenames, validate_cpp_namespace
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4566:src/piketype/commands/gen.py:21:def run_gen(path: str, *, namespace: str | None = None) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4567:src/piketype/commands/gen.py:23:    if namespace is not None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4568:src/piketype/commands/gen.py:24:        validate_cpp_namespace(namespace)
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4569:src/piketype/commands/gen.py:31:    if namespace is not None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4570:src/piketype/commands/gen.py:66:    emit_cpp(repo, namespace=namespace)
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4571:src/piketype/dsl/freeze.py:67:            namespace_parts=tuple(relative_path.with_suffix("").parts),
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4573:tests/test_gen_const_sv.py:278:    def test_namespace_override_multi_module(self) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4574:tests/test_gen_const_sv.py:279:        fixture_root = FIXTURES_DIR / "namespace_override" / "project"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4575:tests/test_gen_const_sv.py:280:        expected_root = GOLDENS_DIR / "namespace_override"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4576:tests/test_gen_const_sv.py:285:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::bar")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4577:tests/test_gen_const_sv.py:289:    def test_namespace_rejects_empty_segment(self) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4578:tests/test_gen_const_sv.py:295:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::::bar")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4579:tests/test_gen_const_sv.py:299:    def test_namespace_rejects_non_identifier(self) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4580:tests/test_gen_const_sv.py:305:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "123bad")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4581:tests/test_gen_const_sv.py:309:    def test_namespace_rejects_cpp_keyword(self) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4582:tests/test_gen_const_sv.py:315:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "class")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4583:tests/test_gen_const_sv.py:319:    def test_namespace_rejects_double_underscore(self) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4584:tests/test_gen_const_sv.py:325:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo__bar")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4585:tests/test_gen_const_sv.py:329:    def test_namespace_rejects_leading_underscore(self) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4586:tests/test_gen_const_sv.py:335:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "_foo")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4587:tests/test_gen_const_sv.py:339:    def test_namespace_rejects_std_first_segment(self) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4588:tests/test_gen_const_sv.py:345:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "std::types")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4589:tests/test_gen_const_sv.py:349:    def test_namespace_rejects_trailing_underscore(self) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4590:tests/test_gen_const_sv.py:355:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo_")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4591:tests/test_gen_const_sv.py:359:    def test_namespace_rejects_leading_underscore_non_first(self) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4592:tests/test_gen_const_sv.py:365:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::_bar")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4593:tests/test_gen_const_sv.py:369:    def test_namespace_rejects_duplicate_basenames(self) -> None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4594:tests/test_gen_const_sv.py:384:            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::bar")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4596:tests/test_struct_enum_member.py:108:            namespace_parts=("alpha",),
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4598:tests/test_struct_enum_member.py:338:            namespace_parts=("a",),
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4599:tests/test_struct_enum_member.py:344:            namespace_parts=("b",),
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4601:tests/test_gen_flags.py:110:            namespace_parts=("alpha", "piketype", "types"),
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4603:src/piketype/cli.py:21:    gen_parser.add_argument("--namespace", default=None)
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4604:src/piketype/cli.py:39:                run_gen(args.path, namespace=args.namespace)
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4605:src/piketype/manifest/write_json.py:78:                "namespace_parts": list(module.ref.namespace_parts),
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4606:src/piketype/backends/cpp/emitter.py:32:def emit_cpp(repo: RepoIR, *, namespace: str | None = None) -> list[Path]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4607:src/piketype/backends/cpp/emitter.py:42:        output_path.write_text(render_module_hpp(module, namespace=namespace), encoding="utf-8")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4608:src/piketype/backends/cpp/emitter.py:47:def render_module_hpp(module: ModuleIR, *, namespace: str | None = None) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4609:src/piketype/backends/cpp/emitter.py:50:    if namespace is not None:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4610:src/piketype/backends/cpp/emitter.py:51:        guard = f"{namespace.replace('::', '_')}_{module.ref.basename}_types_hpp".upper()
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4611:src/piketype/backends/cpp/emitter.py:52:        ns = f"{namespace}::{module.ref.basename}"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4612:src/piketype/backends/cpp/emitter.py:54:        guard = "_".join((*module.ref.namespace_parts, "types_hpp")).upper().replace(".", "_")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4613:src/piketype/backends/cpp/emitter.py:55:        ns = "::".join(part for part in module.ref.namespace_parts if part != "piketype")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4614:src/piketype/backends/cpp/emitter.py:63:        body_lines.append(f"namespace {ns} {{")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4615:src/piketype/backends/cpp/emitter.py:91:        body_lines.append(f"}}  // namespace {ns}")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4617:tests/test_gen_enum.py:91:        namespace_parts=("foo", "piketype", "defs"),
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4618:tests/test_gen_enum.py:219:            namespace_parts=("foo", "piketype", "defs"),
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4619:tests/test_gen_enum.py:249:            namespace_parts=("foo", "piketype", "defs"),
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4621:tests/test_const_ranges.py:77:            namespace_parts=("alpha", "piketype", "constants"),
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4624:src/piketype/validate/namespace.py:1:"""C++ namespace validation for the --namespace CLI argument."""
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4625:src/piketype/validate/namespace.py:25:    "namespace", "new", "noexcept", "not", "not_eq", "nullptr",
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4626:src/piketype/validate/namespace.py:42:def validate_cpp_namespace(value: str) -> tuple[str, ...]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4627:src/piketype/validate/namespace.py:43:    """Validate a ``::``-separated C++ namespace string.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4628:src/piketype/validate/namespace.py:49:        raise ValidationError("--namespace value must not be empty")
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4629:src/piketype/validate/namespace.py:56:                f"--namespace contains an empty segment in '{value}'"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4630:src/piketype/validate/namespace.py:60:                f"--namespace segment '{segment}' is not a valid C++ identifier"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4631:src/piketype/validate/namespace.py:64:                f"--namespace segment '{segment}' is a C++ keyword"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4632:src/piketype/validate/namespace.py:68:                f"--namespace segment '{segment}' must not begin with an underscore"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4633:src/piketype/validate/namespace.py:72:                f"--namespace segment '{segment}' must not contain '__'"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4634:src/piketype/validate/namespace.py:76:                f"--namespace segment '{segment}' must not end with an underscore"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4635:src/piketype/validate/namespace.py:80:                "--namespace must not use 'std' as the first segment"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4636:src/piketype/validate/namespace.py:87:            f"--namespace '{value}' would produce a reserved include-guard prefix "
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4637:src/piketype/validate/namespace.py:92:            f"--namespace '{value}' would produce a reserved include-guard prefix "
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4638:src/piketype/validate/namespace.py:100:    """Reject duplicate module basenames when ``--namespace`` is active.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4639:src/piketype/validate/namespace.py:118:        "--namespace requires unique module basenames, but duplicates were found:\n"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4640:src/piketype/ir/nodes.py:33:    namespace_parts: tuple[str, ...]
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4641:src/piketype/backends/runtime/emitter.py:65:        "namespace piketype_runtime {\n\n"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4642:src/piketype/backends/runtime/emitter.py:67:        "}  // namespace piketype_runtime\n\n"
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4683:    37	- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4698:    52	  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4721:   547	def _render_cpp_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4811:   637	def _render_cpp_field_decl(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4818:   644	def _render_cpp_field_type(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4831:   657	def _render_cpp_field_default(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4849:   428	def _render_cpp_flags(*, type_ir: FlagsIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4971:   146	def _render_sv_struct(*, type_ir: StructIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:4991:   166	def _render_sv_struct_field_type(*, field_type: FieldTypeIR) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5002:   177	def _render_sv_flags(*, type_ir: FlagsIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5016:   191	def _render_sv_enum(*, type_ir: EnumIR) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5026:   201	def _render_sv_pack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5070:   245	def _render_sv_unpack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5132:   428	def _render_sv_struct_helper_class(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5263:   756	def _render_sv_helper_field_decl(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5275:   768	def _render_sv_helper_to_bytes_step(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5306:   799	def _render_sv_helper_from_bytes_step(
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5354:2. **BLOCKING — FR-8 / FR-10 / FR-18 / Phase 1 view model.** The Python view sketch is incomplete. Current Python rendering needs enum class name, enum wrapper width/byte_count/first member/mask, flags field masks/data mask, struct field min/max, padding bits, sign-bit index, and target kind for type refs. `FlagsFieldView` is referenced but not defined. Fix by expanding the sketch into concrete dataclasses that cover every value used by current `_render_py_*` helpers.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5356:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5358:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5366:8. **WARNING — FR-2 / CL-2 / Phase 0.** The render helper commit does not spell out the exact required Jinja environment options and the architecture snippet calls `make_environment` positionally despite the planned keyword-only signature. Fix the plan to name the exact `Environment` options and require all custom filters/globals to be auditable in `backends/common/render.py`.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5368:9. **NOTE — C++ namespace override.** The plan mentions namespace/guard precomputation, which is correct, but it should explicitly include the existing `--namespace` override fixture in C++ view/golden validation. This is a known regression point.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5378:2. **BLOCKING — FR-8 / FR-10 / FR-18 / Phase 1 view model.** The Python view sketch is incomplete. Current Python rendering needs enum class name, enum wrapper width/byte_count/first member/mask, flags field masks/data mask, struct field min/max, padding bits, sign-bit index, and target kind for type refs. `FlagsFieldView` is referenced but not defined. Fix by expanding the sketch into concrete dataclasses that cover every value used by current `_render_py_*` helpers.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5380:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5382:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5390:8. **WARNING — FR-2 / CL-2 / Phase 0.** The render helper commit does not spell out the exact required Jinja environment options and the architecture snippet calls `make_environment` positionally despite the planned keyword-only signature. Fix the plan to name the exact `Environment` options and require all custom filters/globals to be auditable in `backends/common/render.py`.
./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5392:9. **NOTE — C++ namespace override.** The plan mentions namespace/guard precomputation, which is correct, but it should explicitly include the existing `--namespace` override fixture in C++ view/golden validation. This is a known regression point.
./tests/goldens/gen/flags_basic/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/flags_basic/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./specs/004-cpp-constexpr-upper-case/artifacts/clarification/iter1-forge.md:28:**NO RISK.** User-defined constants are emitted at namespace scope (not inside classes), and their names come directly from DSL definitions which are already `UPPER_SNAKE_CASE`. The renamed class-static and function-local constants live in different scopes and cannot collide.
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:23:    env = make_environment("piketype.backends.<lang>")
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:48:| `src/piketype/backends/common/render.py`      | rewrite | Stub → `make_environment(*, package: str) -> jinja2.Environment` and `render(*, env, template_name, context) -> str`. Custom-filter registration site (FR-2/3, CL-2). |
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:51:| `tests/test_render.py`                        | new     | `make_environment` / `render` smoke tests; placeholder for future custom-filter tests (CL-2). |
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:61:1. `feat(common): add make_environment and render helpers` — `render.py` + `tests/test_render.py`.
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:96:class ScalarAliasView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:110:class StructFieldView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:126:class StructView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:130:    fields: tuple[StructFieldView, ...]
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:135:class EnumMemberView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:140:class EnumView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:146:class FlagsView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:153:class ConstantView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:158:class ModuleView:
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:165:    types: tuple[ScalarAliasView | StructView | EnumView | FlagsView, ...]
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:193:- View must precompute namespace nesting strings, include-guard symbol, and full pack/unpack helper bodies.
./specs/010-jinja-template-migration/artifacts/planning/iter1-forge.md:201:2. `feat(cpp): module/file skeleton via template (header, includes, namespace open/close, guard)`.
./specs/002-namespace-cli-argument/artifacts/planning/iter1-gauge-prompt.md:3:You are reviewing an implementation plan for the `--namespace` CLI argument feature
./specs/002-namespace-cli-argument/artifacts/planning/iter1-gauge-prompt.md:8:Read the plan at `specs/002-namespace-cli-argument/artifacts/planning/plan.md`,
./specs/002-namespace-cli-argument/artifacts/planning/iter1-gauge-prompt.md:9:the spec at `specs/002-namespace-cli-argument/spec.md`, and the constitution at
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge-prompt.md:12:8. WARNING — `make_environment` env options + keyword-only signature not pinned.
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge-prompt.md:13:9. NOTE — C++ `--namespace` override.
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge-prompt.md:26:   - Does the new `body_lines: tuple[str, ...] | None` passthrough mechanism violate FR-8/FR-9 (it's a primitive `tuple` of `str`, so it should comply, but verify)?
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge-prompt.md:29:     - `_render_py_enum` → `EnumView` should carry `mask`, `first_member_name`, `enum_class_name`, `width`, `byte_count`.
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge-prompt.md:30:     - `_render_py_flags` → `FlagsView` should carry `data_mask`, `total_bits`, plus per-flag `bit_mask`.
./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge-prompt.md:31:     - `_render_py_struct_field_coercer` → `StructFieldView` discriminators must distinguish struct-ref / flags-ref / enum-ref / scalar-ref / narrow-scalar / wide-scalar.
./tests/goldens/gen/struct_multiple_of/cpp/alpha/piketype/types_types.hpp:13:namespace alpha::types {
./tests/goldens/gen/struct_multiple_of/cpp/alpha/piketype/types_types.hpp:353:}  // namespace alpha::types
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:1:# Implementation Plan — Spec 002: `--namespace` CLI Argument
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:5:**Approach:** Pass-through parameter. The `--namespace` value flows from CLI →
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:18:1. **`src/typist/validate/namespace.py`** — Namespace validation logic
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:19:   - `validate_cpp_namespace(value: str) -> tuple[str, ...]` — Validates and
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:28:     `if`, `inline`, `int`, `long`, `mutable`, `namespace`, `new`, `noexcept`,
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:41:2. **`tests/test_namespace_validation.py`** — Unit tests for validation logic
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:50:3. **`tests/fixtures/namespace_override/project/`** — Multi-module fixture
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:52:   - `beta/typist/more.py` — More constants (different path-derived namespace).
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:55:4. **`tests/goldens/gen/namespace_override/`** — Golden output for the fixture
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:64:     baseline (SV/Python/manifest unaffected by `--namespace`).
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:70:5. **`src/typist/cli.py`** — Add `--namespace` to `gen` subparser
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:71:   - Break out `gen` from the shared loop to add `--namespace` as an optional arg.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:72:   - Pass `args.namespace` (which is `None` when omitted) to `run_gen`.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:74:6. **`src/typist/commands/gen.py`** — Accept and thread `namespace` parameter
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:75:   - `run_gen(path: str, *, namespace: str | None = None)` — New kwarg.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:76:   - Call `validate_cpp_namespace()` before discovery if `namespace` is not None.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:77:   - After discovery, if `namespace` is set, call `check_duplicate_basenames()`.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:78:   - Pass `namespace` to `emit_cpp()`.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:80:7. **`src/typist/backends/cpp/emitter.py`** — Use namespace override
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:81:   - `emit_cpp(repo, *, namespace: str | None = None)` — New kwarg.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:82:   - `render_module_hpp(module, *, namespace: str | None = None)` — New kwarg.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:83:   - When `namespace` is not None:
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:84:     - `guard = f"{namespace.replace('::', '_')}_{module.ref.basename}_TYPES_HPP".upper()`
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:85:     - `ns = f"{namespace}::{module.ref.basename}"`
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:86:   - When `namespace` is None: existing logic unchanged.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:90:     `--namespace foo::bar` before the path argument. Signature:
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:93:   - Positive golden test: `--namespace foo::bar` with `namespace_override` fixture.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:95:     - Empty segment: `--namespace "foo::::bar"`
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:96:     - Non-identifier: `--namespace "123bad"`
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:97:     - C++ keyword: `--namespace "class"`
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:98:     - Double underscore: `--namespace "foo__bar"`
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:99:     - Leading underscore: `--namespace "_foo"`
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:100:     - `std` first segment: `--namespace "std::types"`
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:101:     - Trailing underscore: `--namespace "foo_"`
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:102:     - Leading underscore non-first: `--namespace "foo::_bar"`
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:110:1. validate/namespace.py  (new, no deps)
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:111:2. test_namespace_validation.py  (unit tests for ^, run to verify)
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:114:5. backends/cpp/emitter.py  (namespace override logic)
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:123:  exercise `namespace=None` path.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:124:- **Low risk:** C++ emitter change is guarded by `if namespace is not None`.
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:132:- **Deterministic output:** Preserved — namespace is an explicit input, not
./specs/002-namespace-cli-argument/artifacts/planning/plan.md:134:- **Immutable IR:** Respected — IR `namespace_parts` untouched.
./specs/007-struct-flags-member/artifacts/planning/iter2-forge.md:206:File: `tests/test_namespace_validation.py` (extend existing)
./specs/010-jinja-template-migration/artifacts/clarification/iter3-forge.md:37:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/clarification/iter3-forge.md:52:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/clarification/iter3-forge.md:154:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./tests/goldens/gen/struct_padded/piketype_manifest.json:13:      "namespace_parts": [
./specs/002-namespace-cli-argument/artifacts/clarification/clarification.md:1:# Clarification — Spec 002: `--namespace` CLI Argument
./specs/002-namespace-cli-argument/artifacts/clarification/clarification.md:10:| FR-1 | `src/typist/cli.py:20-22` | Add `--namespace` to `gen` subparser only |
./specs/002-namespace-cli-argument/artifacts/clarification/clarification.md:11:| FR-2 | New module: `src/typist/validate/namespace.py` | Validation function |
./specs/002-namespace-cli-argument/artifacts/clarification/clarification.md:12:| FR-3 | `src/typist/backends/cpp/emitter.py:48` | Conditional namespace derivation |
./specs/002-namespace-cli-argument/artifacts/clarification/clarification.md:15:| FR-6 | `src/typist/commands/gen.py:59` | Pass namespace to `emit_cpp` |
./specs/002-namespace-cli-argument/artifacts/clarification/clarification.md:16:| FR-7 | `src/typist/backends/cpp/emitter.py:29-41` | Pass namespace through per-module loop |
./specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:37:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:52:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/clarification/iter2-forge.md:154:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./tests/goldens/gen/struct_multiple_of/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/struct_multiple_of/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:326:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:341:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:451:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:466:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:568:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:912:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/clarification/iter2-gauge.md:942:154:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./tests/goldens/gen/struct_padded/cpp/alpha/piketype/types_types.hpp:13:namespace alpha::types {
./tests/goldens/gen/struct_padded/cpp/alpha/piketype/types_types.hpp:211:}  // namespace alpha::types
./specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:134:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
./specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:149:  - `def make_environment(*, package: str) -> jinja2.Environment` constructing an Environment per FR-2 with `PackageLoader(package, "templates")`.
./specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:251:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./specs/010-jinja-template-migration/artifacts/clarification/iter1-gauge.md:480:154:- **NFR-1. Performance.** The wall-clock time of `piketype gen` against fixture `tests/fixtures/struct_padded` SHALL NOT regress by more than 25% relative to the pre-migration baseline. The actual CLI signature is `piketype gen [--namespace NS] <dsl-file-path>`, where `<dsl-file-path>` is a single Python DSL file (e.g., `tests/fixtures/struct_padded/project/alpha/piketype/types.py`) — not a project root.
./specs/005-flags-dsl-type/artifacts/retrospect/retrospect.md:33:2. **Reserved API names need validation.** Unlike Struct (where fields are just public attributes), Flags generates Python properties that share namespace with methods. The minimal reserved-name set (`value`, `to_bytes`, `from_bytes`, `clone`, `width`, `byte_count`) is sufficient for now but a broader language-keyword check remains a cross-cutting gap.
./tests/goldens/gen/const_cpp_explicit_uint32/piketype_manifest.json:35:      "namespace_parts": [
./tests/goldens/gen/struct_padded/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/struct_padded/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./tests/goldens/gen/const_cpp_explicit_uint32/cpp/alpha/piketype/constants_types.hpp:10:namespace alpha::constants {
./tests/goldens/gen/const_cpp_explicit_uint32/cpp/alpha/piketype/constants_types.hpp:15:}  // namespace alpha::constants
./specs/007-struct-flags-member/artifacts/task_breakdown/iter1-forge.md:228:**File:** `tests/test_namespace_validation.py` (extend existing)
./tests/goldens/gen/const_cpp_explicit_uint32/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/const_cpp_explicit_uint32/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./tests/goldens/gen/struct_wide/piketype_manifest.json:13:      "namespace_parts": [
./tests/goldens/gen/const_expr_basic/piketype_manifest.json:68:      "namespace_parts": [
./tests/goldens/gen/const_sv_basic/piketype_manifest.json:35:      "namespace_parts": [
./tests/goldens/gen/const_sv_basic/piketype_manifest.json:70:      "namespace_parts": [
./tests/goldens/gen/struct_wide/cpp/alpha/piketype/types_types.hpp:13:namespace alpha::types {
./tests/goldens/gen/struct_wide/cpp/alpha/piketype/types_types.hpp:124:}  // namespace alpha::types
./tests/goldens/gen/const_expr_basic/cpp/alpha/piketype/constants_types.hpp:10:namespace alpha::constants {
./tests/goldens/gen/const_expr_basic/cpp/alpha/piketype/constants_types.hpp:18:}  // namespace alpha::constants
./tests/goldens/gen/const_sv_basic/cpp/alpha/piketype/constants_types.hpp:10:namespace alpha::constants {
./tests/goldens/gen/const_sv_basic/cpp/alpha/piketype/constants_types.hpp:15:}  // namespace alpha::constants
./tests/goldens/gen/struct_sv_basic/piketype_manifest.json:25:      "namespace_parts": [
./tests/goldens/gen/struct_wide/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/struct_wide/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./tests/goldens/gen/const_expr_basic/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/const_expr_basic/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./tests/goldens/gen/const_sv_basic/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/const_sv_basic/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./tests/goldens/gen/const_sv_basic/cpp/beta/piketype/more_types.hpp:10:namespace beta::more {
./tests/goldens/gen/const_sv_basic/cpp/beta/piketype/more_types.hpp:14:}  // namespace beta::more
./tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:13:namespace alpha::types {
./tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:205:}  // namespace alpha::types
./specs/006-rename-to-pike-type/spec.md:22:| C++ namespace filter     | removes `"typist"`    | removes `"piketype"`   |
./specs/006-rename-to-pike-type/spec.md:69:  - C++: namespace `typist_runtime` → `piketype_runtime`, header guard `TYPIST_RUNTIME_HPP` → `PIKETYPE_RUNTIME_HPP`, file names `typist_runtime.*` → `piketype_runtime.*`
./specs/006-rename-to-pike-type/spec.md:71:- **C++ emitter namespace filter:** Change `part != "typist"` to `part != "piketype"` in `cpp/emitter.py`.
./specs/006-rename-to-pike-type/spec.md:116:- String literals referencing `typist` in test data (module names, namespace parts, paths)
./specs/006-rename-to-pike-type/spec.md:174:- **AC-10:** Generated C++ code uses namespace `piketype_runtime` and header guard `PIKETYPE_RUNTIME_HPP`.
./specs/006-rename-to-pike-type/plan.md:104:6. `namespace_override`
./specs/006-rename-to-pike-type/plan.md:114:For each, copy the fixture to a temp dir, run `piketype gen` (with `--namespace` for `namespace_override`), and copy the `gen/` output to `tests/goldens/gen/<case>/`.
./specs/006-rename-to-pike-type/plan.md:125:- String literals in test data: module names, namespace parts, paths
./tests/goldens/gen/enum_basic/piketype_manifest.json:13:      "namespace_parts": [
./tests/goldens/gen/struct_sv_basic/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/struct_sv_basic/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./specs/006-rename-to-pike-type/tasks.md:36:- `src/piketype/validate/namespace.py` — imports
./specs/006-rename-to-pike-type/tasks.md:42:- `src/piketype/backends/cpp/emitter.py` — namespace filter, imports
./specs/006-rename-to-pike-type/tasks.md:64:- `tests/fixtures/*/project/beta/typist/` → `*/beta/piketype/` (const_sv_basic, namespace_override)
./specs/006-rename-to-pike-type/tasks.md:86:**Description:** Install the package with `pip install -e .` and regenerate golden output for all 14 positive fixtures by running `piketype gen` on each. Copy `gen/` output to `tests/goldens/gen/<case>/`. The `namespace_override` fixture requires `--namespace foo::bar`.
./specs/006-rename-to-pike-type/tasks.md:88:**Fixtures:** const_cpp_explicit_uint32, const_cpp_wide, const_expr_basic, const_sv_basic, flags_basic, namespace_override, nested_struct_sv_basic, scalar_sv_basic, scalar_wide, struct_multiple_of, struct_padded, struct_signed, struct_sv_basic, struct_wide
./specs/006-rename-to-pike-type/tasks.md:105:- `tests/test_namespace_validation.py`
./specs/006-rename-to-pike-type/tasks.md:192:# AC-10: C++ namespace and header guard
./specs/006-rename-to-pike-type/tasks.md:193:grep -q "namespace piketype_runtime" tests/goldens/gen/const_sv_basic/cpp/runtime/piketype_runtime.hpp && echo "AC-10 namespace: PASS"
./specs/006-rename-to-pike-type/artifacts/validation/results.md:16:| AC-10 | C++ namespace `piketype_runtime`, guard `PIKETYPE_RUNTIME_HPP` | PASS | Verified in golden files |
./specs/006-rename-to-pike-type/artifacts/planning/iter2-forge.md:104:6. `namespace_override`
./specs/006-rename-to-pike-type/artifacts/planning/iter2-forge.md:114:For each, copy the fixture to a temp dir, run `piketype gen` (with `--namespace` for `namespace_override`), and copy the `gen/` output to `tests/goldens/gen/<case>/`.
./specs/006-rename-to-pike-type/artifacts/planning/iter2-forge.md:125:- String literals in test data: module names, namespace parts, paths
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter3-forge.md:36:- `src/piketype/validate/namespace.py` — imports
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter3-forge.md:42:- `src/piketype/backends/cpp/emitter.py` — namespace filter, imports
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter3-forge.md:64:- `tests/fixtures/*/project/beta/typist/` → `*/beta/piketype/` (const_sv_basic, namespace_override)
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter3-forge.md:86:**Description:** Install the package with `pip install -e .` and regenerate golden output for all 14 positive fixtures by running `piketype gen` on each. Copy `gen/` output to `tests/goldens/gen/<case>/`. The `namespace_override` fixture requires `--namespace foo::bar`.
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter3-forge.md:88:**Fixtures:** const_cpp_explicit_uint32, const_cpp_wide, const_expr_basic, const_sv_basic, flags_basic, namespace_override, nested_struct_sv_basic, scalar_sv_basic, scalar_wide, struct_multiple_of, struct_padded, struct_signed, struct_sv_basic, struct_wide
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter3-forge.md:105:- `tests/test_namespace_validation.py`
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter3-forge.md:192:# AC-10: C++ namespace and header guard
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter3-forge.md:193:grep -q "namespace piketype_runtime" tests/goldens/gen/const_sv_basic/cpp/runtime/piketype_runtime.hpp && echo "AC-10 namespace: PASS"
./tests/goldens/gen/enum_basic/cpp/foo/piketype/defs_types.hpp:13:namespace foo::defs {
./tests/goldens/gen/enum_basic/cpp/foo/piketype/defs_types.hpp:229:}  // namespace foo::defs
./specs/006-rename-to-pike-type/artifacts/retrospect/retrospect.md:9:3. **Golden regeneration by running the tool** was much more reliable than trying to hand-edit hundreds of golden files. One namespace_override regeneration bug was caught immediately by the test suite.
./specs/006-rename-to-pike-type/artifacts/retrospect/retrospect.md:11:4. **139 tests passed on first full run** (after the namespace_override golden fix). The test suite was the primary correctness mechanism, exactly as designed by the constitution.
./specs/006-rename-to-pike-type/artifacts/retrospect/retrospect.md:19:3. **Golden regeneration for namespace_override was wrong initially.** I ran a second `piketype gen` without `--namespace` which overwrote the correct output. Should have checked the test to understand the exact invocation pattern before regenerating.
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-forge.md:36:- `src/piketype/validate/namespace.py` — imports
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-forge.md:42:- `src/piketype/backends/cpp/emitter.py` — namespace filter, imports
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-forge.md:64:- `tests/fixtures/*/project/beta/typist/` → `*/beta/piketype/` (const_sv_basic, namespace_override)
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-forge.md:86:**Description:** Install the package with `pip install -e .` and regenerate golden output for all 14 positive fixtures by running `piketype gen` on each. Copy `gen/` output to `tests/goldens/gen/<case>/`. The `namespace_override` fixture requires `--namespace foo::bar`.
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-forge.md:88:**Fixtures:** const_cpp_explicit_uint32, const_cpp_wide, const_expr_basic, const_sv_basic, flags_basic, namespace_override, nested_struct_sv_basic, scalar_sv_basic, scalar_wide, struct_multiple_of, struct_padded, struct_signed, struct_sv_basic, struct_wide
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-forge.md:105:- `tests/test_namespace_validation.py`
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-forge.md:192:# AC-10: C++ namespace and header guard
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-forge.md:193:grep -q "namespace piketype_runtime" tests/goldens/gen/const_sv_basic/cpp/runtime/piketype_runtime.hpp && echo "AC-10 namespace: PASS"
./specs/006-rename-to-pike-type/artifacts/planning/iter1-forge.md:121:- String literals in test data: module names, namespace parts, paths
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-gauge.md:3:**BLOCKING:** Task 10 claims AC-1 through AC-14 are verified, but the listed commands do not directly verify AC-2 (golden diff), AC-5 (discovery accept/reject), AC-6 (Generated by piketype header), AC-7 (piketype_runtime* names), AC-8 (piketype_manifest.json), or AC-10 (C++ namespace/guard). Add explicit checks.
./tests/goldens/gen/nested_struct_sv_basic/piketype_manifest.json:25:      "namespace_parts": [
./tests/goldens/gen/struct_enum_member/piketype_manifest.json:13:      "namespace_parts": [
./specs/006-rename-to-pike-type/artifacts/specification/iter3-forge.md:22:| C++ namespace filter     | removes `"typist"`    | removes `"piketype"`   |
./specs/006-rename-to-pike-type/artifacts/specification/iter3-forge.md:69:  - C++: namespace `typist_runtime` → `piketype_runtime`, header guard `TYPIST_RUNTIME_HPP` → `PIKETYPE_RUNTIME_HPP`, file names `typist_runtime.*` → `piketype_runtime.*`
./specs/006-rename-to-pike-type/artifacts/specification/iter3-forge.md:71:- **C++ emitter namespace filter:** Change `part != "typist"` to `part != "piketype"` in `cpp/emitter.py`.
./specs/006-rename-to-pike-type/artifacts/specification/iter3-forge.md:116:- String literals referencing `typist` in test data (module names, namespace parts, paths)
./specs/006-rename-to-pike-type/artifacts/specification/iter3-forge.md:172:- **AC-10:** Generated C++ code uses namespace `piketype_runtime` and header guard `PIKETYPE_RUNTIME_HPP`.
./tests/goldens/gen/enum_basic/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/enum_basic/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter2-gauge-prompt.md:5:1. Task 10 now has explicit commands for AC-2 (covered by test suite), AC-5 (is_under_piketype_dir check), AC-6 (grep for header), AC-7 (find piketype_runtime*), AC-8 (find piketype_manifest.json), AC-10 (grep for namespace and guard)
./specs/006-rename-to-pike-type/artifacts/specification/iter3-forge-final.md:22:| C++ namespace filter     | removes `"typist"`    | removes `"piketype"`   |
./specs/006-rename-to-pike-type/artifacts/specification/iter3-forge-final.md:69:  - C++: namespace `typist_runtime` → `piketype_runtime`, header guard `TYPIST_RUNTIME_HPP` → `PIKETYPE_RUNTIME_HPP`, file names `typist_runtime.*` → `piketype_runtime.*`
./specs/006-rename-to-pike-type/artifacts/specification/iter3-forge-final.md:71:- **C++ emitter namespace filter:** Change `part != "typist"` to `part != "piketype"` in `cpp/emitter.py`.
./specs/006-rename-to-pike-type/artifacts/specification/iter3-forge-final.md:116:- String literals referencing `typist` in test data (module names, namespace parts, paths)
./specs/006-rename-to-pike-type/artifacts/specification/iter3-forge-final.md:172:- **AC-10:** Generated C++ code uses namespace `piketype_runtime` and header guard `PIKETYPE_RUNTIME_HPP`.
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-forge.md:36:- `src/piketype/validate/namespace.py` — imports
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-forge.md:42:- `src/piketype/backends/cpp/emitter.py` — namespace filter, imports
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-forge.md:60:- `tests/fixtures/*/project/beta/typist/` → `*/beta/piketype/` (const_sv_basic, namespace_override)
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-forge.md:82:**Description:** Install the package with `pip install -e .` and regenerate golden output for all 14 positive fixtures by running `piketype gen` on each. Copy `gen/` output to `tests/goldens/gen/<case>/`. The `namespace_override` fixture requires `--namespace foo::bar`.
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-forge.md:84:**Fixtures:** const_cpp_explicit_uint32, const_cpp_wide, const_expr_basic, const_sv_basic, flags_basic, namespace_override, nested_struct_sv_basic, scalar_sv_basic, scalar_wide, struct_multiple_of, struct_padded, struct_signed, struct_sv_basic, struct_wide
./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-forge.md:101:- `tests/test_namespace_validation.py`
./tests/goldens/gen/struct_signed/piketype_manifest.json:13:      "namespace_parts": [
./specs/006-rename-to-pike-type/artifacts/specification/iter2-forge.md:20:| C++ namespace filter     | removes `"typist"`    | removes `"piketype"`   |
./specs/006-rename-to-pike-type/artifacts/specification/iter2-forge.md:67:  - C++: namespace `typist_runtime` → `piketype_runtime`, header guard `TYPIST_RUNTIME_HPP` → `PIKETYPE_RUNTIME_HPP`, file names `typist_runtime.*` → `piketype_runtime.*`
./specs/006-rename-to-pike-type/artifacts/specification/iter2-forge.md:69:- **C++ emitter namespace filter:** Change `part != "typist"` to `part != "piketype"` in `cpp/emitter.py`.
./specs/006-rename-to-pike-type/artifacts/specification/iter2-forge.md:114:- String literals referencing `typist` in test data (module names, namespace parts, paths)
./specs/006-rename-to-pike-type/artifacts/specification/iter2-forge.md:163:- **AC-10:** Generated C++ code uses namespace `piketype_runtime` and header guard `PIKETYPE_RUNTIME_HPP`.
./tests/goldens/gen/struct_enum_member/cpp/alpha/piketype/types_types.hpp:13:namespace alpha::types {
./tests/goldens/gen/struct_enum_member/cpp/alpha/piketype/types_types.hpp:218:}  // namespace alpha::types
./specs/006-rename-to-pike-type/artifacts/specification/iter1-forge.md:20:| C++ namespace filter     | removes `"typist"`    | removes `"piketype"`   |
./specs/006-rename-to-pike-type/artifacts/specification/iter1-forge.md:65:  - C++: namespace `typist_runtime` → `piketype_runtime`, header guard `TYPIST_RUNTIME_HPP` → `PIKETYPE_RUNTIME_HPP`, file names `typist_runtime.*` → `piketype_runtime.*`
./specs/006-rename-to-pike-type/artifacts/specification/iter1-forge.md:67:- **C++ emitter namespace filter:** Change `part != "typist"` to `part != "piketype"` in `cpp/emitter.py`.
./specs/006-rename-to-pike-type/artifacts/specification/iter1-forge.md:98:- String literals referencing `typist` in test data (module names, namespace parts, paths)
./specs/006-rename-to-pike-type/artifacts/specification/iter1-forge.md:135:- **AC-10:** Generated C++ code uses namespace `piketype_runtime` and header guard `PIKETYPE_RUNTIME_HPP`.
./tests/goldens/gen/scalar_wide/piketype_manifest.json:13:      "namespace_parts": [
./tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp:13:namespace alpha::types {
./tests/goldens/gen/nested_struct_sv_basic/cpp/alpha/piketype/types_types.hpp:279:}  // namespace alpha::types
./tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:13:namespace alpha::types {
./tests/goldens/gen/struct_signed/cpp/alpha/piketype/types_types.hpp:242:}  // namespace alpha::types
./tests/goldens/gen/struct_signed/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/struct_signed/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./tests/goldens/gen/struct_enum_member/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/struct_enum_member/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./tests/goldens/gen/nested_struct_sv_basic/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/nested_struct_sv_basic/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime
./tests/goldens/gen/scalar_wide/cpp/alpha/piketype/types_types.hpp:13:namespace alpha::types {
./tests/goldens/gen/scalar_wide/cpp/alpha/piketype/types_types.hpp:136:}  // namespace alpha::types
./tests/goldens/gen/scalar_wide/cpp/runtime/piketype_runtime.hpp:8:namespace piketype_runtime {
./tests/goldens/gen/scalar_wide/cpp/runtime/piketype_runtime.hpp:12:}  // namespace piketype_runtime

codex
The first pass shows iter2 added the missing scaffolding and a transitional `body_lines` strategy. I need line-level checks now, especially around Phase 1 commit sequencing, C++/SV view sketches, wheel validation, and the risk register.
exec
/bin/zsh -lc "nl -ba specs/010-jinja-template-migration/plan.md | sed -n '221,520p'" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "nl -ba specs/010-jinja-template-migration/plan.md | sed -n '1,220p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
   221	    is_struct_ref: bool           # TypeRef → StructIR
   222	    is_flags_ref: bool            # TypeRef → FlagsIR
   223	    is_enum_ref: bool             # TypeRef → EnumIR
   224	    is_scalar_ref: bool           # TypeRef → ScalarAliasIR
   225	    is_narrow_scalar: bool        # ScalarTypeSpec, width <= 64
   226	    is_wide_scalar: bool          # ScalarTypeSpec, width > 64
   227	    target_class: str             # _type_class_name of referenced type (empty if scalar spec)
   228	    # numeric primitives for coercion / pack / unpack rendering
   229	    width: int                    # data width in bits (0 for struct/flags/enum refs)
   230	    signed: bool
   231	    min_value: int
   232	    max_value: int
   233	    mask: int                     # (1 << width) - 1 for narrow scalar; 0 otherwise
   234	    sign_bit_value: int           # 1 << (width-1) for signed narrow; 0 otherwise
   235	    pad_bits: int                 # pack_bits - width (signed narrow); 0 otherwise
   236	    msb_byte_mask: int            # for wide scalar tail mask
   237	
   238	@dataclass(frozen=True, slots=True)
   239	class StructView:
   240	    class_name: str
   241	    width: int                    # data width
   242	    byte_count: int               # includes alignment
   243	    alignment_bytes: int
   244	    fields: tuple[StructFieldView, ...]
   245	    has_struct_field: bool        # at least one field is_struct_ref → controls "if is None: raise" emission
   246	
   247	# Top-level union of type kinds.
   248	type TypeView = ScalarAliasView | StructView | EnumView | FlagsView
   249	
   250	@dataclass(frozen=True, slots=True)
   251	class ModuleView:
   252	    header: str                                  # full pre-rendered header line (FR-13)
   253	    has_types: bool
   254	    has_structs: bool
   255	    has_enums: bool
   256	    has_flags: bool
   257	    constants: tuple[ConstantView, ...]
   258	    types: tuple[TypeView, ...]
   259	    # Transitional passthrough: non-None during sub-steps 1–3, retired at sub-step 4.
   260	    body_lines: tuple[str, ...] | None
   261	```
   262	
   263	**Builder functions (top-level in `view.py`, keyword-only per FR-18):**
   264	- `build_module_view_py(*, module: ModuleIR) -> ModuleView`
   265	- `_build_scalar_alias_view(*, type_ir: ScalarAliasIR) -> ScalarAliasView` (private helper)
   266	- `_build_struct_view(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> StructView`
   267	- `_build_struct_field_view(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> StructFieldView`
   268	- `_build_enum_view(*, type_ir: EnumIR) -> EnumView`
   269	- `_build_flags_view(*, type_ir: FlagsIR) -> FlagsView`
   270	- `_build_constant_view(*, const_ir: ConstantIR) -> ConstantView`
   271	
   272	Builders are pure functions, no side effects, no IR mutation. Tests in `tests/test_view_py.py` assert that for a fixture's IR, the builder produces a view whose primitive fields equal expected literal values (e.g., for `enum_basic`, `EnumView.mask == 7`).
   273	
   274	**Commit sequence (Phase 1) — strictly FR-6 sub-step ordered:**
   275	
   276	1. `feat(py): introduce ModuleView dataclasses and builders` — `view.py` complete, `tests/test_view_py.py` complete. `emitter.py` unchanged. View module is dormant; tests pass against it directly.
   277	2. `feat(py): module skeleton via templates` (FR-6 sub-step 1) — `module.j2` renders header + imports + footer. `emit_py` constructs `ModuleView` with `body_lines = tuple(legacy_render_body_lines(module))` and the template emits `{{ body_lines | join("\n") }}` for the body. **Byte parity preserved.**
   278	3. `feat(py): top-level type declaration skeletons via templates` (FR-6 sub-step 2) — `_macros.j2` adds `scalar_class_skeleton`, `struct_class_skeleton`, `enum_classes_skeleton`, `flags_class_skeleton` macros that emit *only the class header lines* (`class X:`, `WIDTH = ...`, `BYTE_COUNT = ...`). Helper-method bodies and expression fragments still arrive as `body_lines_per_type: tuple[str, ...]` strings on each TypeView. The view is augmented with `helper_lines: tuple[str, ...]` per TypeView temporarily. **Byte parity preserved.**
   279	4. `feat(py): helper-method skeletons via templates` (FR-6 sub-step 3) — macros gain `to_bytes_block`, `from_bytes_block`, `coerce_block`, `setattr_block`, `clone_block`, `eq_repr_block`. Each block consumes precomputed numeric primitives from the view and emits the helper body skeleton. The transitional `helper_lines` field is removed. **Byte parity preserved.**
   280	5. `feat(py): expression and field-level fragments` (FR-6 sub-step 4) — expressions like Python constants, enum member values, and flag mask literals are now rendered from view-model `*_expr: str` fields directly in templates (no Python concatenation). Also handles struct field annotations/defaults/coercer literals. The transitional `body_lines` field on `ModuleView` is now always `None` and removed in this commit. **Byte parity preserved.**
   281	6. `refactor(py): remove inline emitter helpers` (FR-19) — delete every `_render_py_*` function and the legacy `render_module_py`. `emit_py` becomes ≤ ~40 lines. **Byte parity preserved.**
   282	7. `steel(perf): record py-complete perf row` — appends `py-complete` row to `perf.md` (FR-25).
   283	
   284	**Phase 1 gates (per-backend):** AC-1-Py..AC-7-Py, all tested at the end of commit 7.
   285	
   286	---
   287	
   288	## Phase 2 — C++ backend migration
   289	
   290	Same FR-6 sub-step structure. Backend-specific shape differences:
   291	
   292	**Files:** `src/piketype/backends/cpp/view.py`, `templates/{module.j2,_macros.j2,_pack.j2}`, `tests/test_view_cpp.py`.
   293	
   294	**View-model additions / variations from Python:**
   295	
   296	```python
   297	@dataclass(frozen=True, slots=True)
   298	class CppNamespaceView:
   299	    open_lines: tuple[str, ...]   # ["namespace alpha {", "namespace piketype {"]
   300	    close_lines: tuple[str, ...]  # ["}  // namespace piketype", "}  // namespace alpha"]
   301	    qualified: str                # "alpha::piketype" (used in fully-qualified names)
   302	
   303	@dataclass(frozen=True, slots=True)
   304	class CppGuardView:
   305	    macro: str                    # "ALPHA_PIKETYPE_TYPES_TYPES_HPP" (uppercased, _ joined)
   306	
   307	@dataclass(frozen=True, slots=True)
   308	class CppStructFieldView:
   309	    name: str
   310	    decl: str                     # pre-rendered field declaration "uint32_t foo{};", "alpha_ct foo{};"
   311	    field_type_str: str           # "uint32_t", "std::vector<std::byte>", "alpha_ct"
   312	    storage_type: str             # "uint32_t" / "uint64_t" / "std::vector<std::byte>"
   313	    byte_count: int
   314	    pack_bits: int                # precomputed
   315	    is_struct_ref: bool
   316	    is_flags_ref: bool
   317	    is_enum_ref: bool
   318	    is_scalar_ref: bool
   319	    is_narrow_scalar: bool
   320	    is_wide_scalar: bool
   321	    target_class: str
   322	    width: int
   323	    signed: bool
   324	    min_value_literal: str        # pre-rendered "INT32_MIN" / "0"
   325	    max_value_literal: str        # pre-rendered "INT32_MAX" / "0xFFFFFFFFULL"
   326	    mask_literal: str             # pre-rendered "0xFFFFFFFFULL"
   327	    sign_bit_literal: str         # pre-rendered "0x80000000ULL" or ""
   328	    msb_byte_mask_literal: str    # pre-rendered "0xFF" or "0x07"
   329	
   330	@dataclass(frozen=True, slots=True)
   331	class CppModuleView:
   332	    header: str
   333	    guard: CppGuardView
   334	    namespace: CppNamespaceView
   335	    has_types: bool
   336	    has_structs: bool
   337	    has_enums: bool
   338	    has_flags: bool
   339	    standard_includes: tuple[str, ...]   # sorted "<cstdint>", "<cstddef>", "<stdexcept>", "<vector>"
   340	    constants: tuple[ConstantView, ...]  # value_expr already C++-formatted
   341	    types: tuple[TypeView, ...]          # CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView
   342	    body_lines: tuple[str, ...] | None   # transitional same as Phase 1
   343	```
   344	
   345	`CppScalarAliasView`, `CppEnumView`, `CppFlagsView` follow the same shape pattern as Python's: precomputed primitives + literal strings, no IR refs, no methods.
   346	
   347	**Critical:** templates render the `to_bytes`/`from_bytes` *helper skeletons* (the `for` loops, the `if signed { ... }` blocks, the `switch` on flag bit). The view supplies operand values, masks, and storage-type names. Helper bodies are NOT precomputed in Python.
   348	
   349	**`--namespace` CLI override:** the namespace builder respects `emit_cpp(repo, *, namespace=None)`. The view's `CppNamespaceView` is constructed from either `module.ref.namespace_parts` (default) or the CLI override (test in `tests/test_view_cpp.py` includes a fixture run with an override).
   350	
   351	**Commit sequence (Phase 2):** same FR-6 sub-step structure as Phase 1 — 7 commits.
   352	
   353	1. `feat(cpp): introduce CppModuleView dataclasses and builders`.
   354	2. `feat(cpp): module skeleton via templates` (header, guard open, includes, namespace open, namespace close, guard close).
   355	3. `feat(cpp): top-level class scaffolding via templates`.
   356	4. `feat(cpp): helper-method skeletons via templates` (pack/unpack loops, scalar inline helpers).
   357	5. `feat(cpp): expression and field-level fragments via templates`.
   358	6. `refactor(cpp): remove inline emitter helpers`.
   359	7. `steel(perf): record cpp-complete perf row`.
   360	
   361	**Phase 2 gates:** AC-1-Cpp..AC-7-Cpp.
   362	
   363	---
   364	
   365	## Phase 3 — SystemVerilog backend migration
   366	
   367	Same FR-6 sub-step structure. Two output files per module: `<basename>_pkg.sv` (synth) and `<basename>_test_pkg.sv` (verification). Two primary templates.
   368	
   369	**Files:** `src/piketype/backends/sv/view.py`, `templates/{module_synth.j2,module_test.j2,_macros.j2}`, `tests/test_view_sv.py`.
   370	
   371	**View-model:**
   372	
   373	```python
   374	@dataclass(frozen=True, slots=True)
   375	class SvConstantView:
   376	    sv_type: str                  # "int signed", "logic [31:0]", etc.
   377	    name: str
   378	    sv_expr: str                  # pre-rendered SV literal or expression
   379	
   380	@dataclass(frozen=True, slots=True)
   381	class SvTypedefView:
   382	    name: str
   383	    width: int
   384	    is_scalar_alias: bool
   385	    is_struct: bool
   386	    is_flags: bool
   387	    is_enum: bool
   388	    # populated based on kind (others empty/zero)
   389	    scalar_signed: bool
   390	    struct_field_lines: tuple[str, ...]    # pre-rendered "logic [N-1:0] field_name;" lines
   391	    flags_field_names: tuple[str, ...]
   392	    enum_member_lines: tuple[str, ...]     # pre-rendered "MEMBER_NAME = value"
   393	    enum_underlying_width: int
   394	
   395	@dataclass(frozen=True, slots=True)
   396	class SvSynthModuleView:
   397	    header: str
   398	    package_name: str             # <basename>_pkg
   399	    constants: tuple[SvConstantView, ...]
   400	    typedefs: tuple[SvTypedefView, ...]
   401	    pack_unpack_blocks: tuple[str, ...]    # transitional fragment for sub-steps 1-3
   402	    body_lines: tuple[str, ...] | None     # transitional
   403	
   404	@dataclass(frozen=True, slots=True)
   405	class SvHelperFieldView:
   406	    name: str
   407	    type_str: str
   408	    byte_count: int
   409	    width: int
   410	    signed: bool
   411	    is_composite_ref: bool        # struct/flags/enum target
   412	    target_helper_class: str      # e.g. "foo_helper"
   413	    # numeric literals for to_bytes / from_bytes step rendering
   414	    mask_literal: str
   415	    sign_bit_literal: str
   416	    pack_bits: int
   417	
   418	@dataclass(frozen=True, slots=True)
   419	class SvHelperClassView:
   420	    name: str                     # "alpha_helper"
   421	    width: int
   422	    byte_count: int
   423	    is_scalar: bool
   424	    is_struct: bool
   425	    is_flags: bool
   426	    is_enum: bool
   427	    fields: tuple[SvHelperFieldView, ...]   # for struct
   428	    flag_field_names: tuple[str, ...]       # for flags
   429	    enum_member_names: tuple[str, ...]      # for enum
   430	    underlying_typedef: str       # name of the synth-package typedef this helper wraps
   431	
   432	@dataclass(frozen=True, slots=True)
   433	class SvTestModuleView:
   434	    header: str
   435	    package_name: str             # <basename>_test_pkg
   436	    synth_package_import: str     # "import <basename>_pkg::*;"
   437	    helper_classes: tuple[SvHelperClassView, ...]
   438	    body_lines: tuple[str, ...] | None     # transitional
   439	```
   440	
   441	Builder produces both views from one `ModuleIR`:
   442	- `build_synth_module_view_sv(*, module: ModuleIR) -> SvSynthModuleView`
   443	- `build_test_module_view_sv(*, module: ModuleIR) -> SvTestModuleView`
   444	
   445	The test-package builder shares helpers with the synth builder where possible.
   446	
   447	**Commit sequence (Phase 3):**
   448	
   449	1. `feat(sv): introduce SvSynthModuleView and SvTestModuleView dataclasses and builders`.
   450	2. `feat(sv): synth and test package skeletons via templates` (FR-6 sub-step 1, both packages handled in one commit since they share most skeleton rules).
   451	3. `feat(sv): synth typedef scaffolding and test helper-class scaffolding via templates` (FR-6 sub-step 2).
   452	4. `feat(sv): pack/unpack functions and verification helper-method skeletons via templates` (FR-6 sub-step 3 — the largest chunk for SV).
   453	5. `feat(sv): expression and field-level fragments via templates` (FR-6 sub-step 4).
   454	6. `refactor(sv): remove inline emitter helpers`.
   455	7. `steel(perf): record sv-complete perf row`.
   456	
   457	**Phase 3 gates:** AC-1-Sv..AC-7-Sv.
   458	
   459	---
   460	
   461	## Phase 4 — Feature-final validation
   462	
   463	Runs during the spec's `validation` Steel-Kit stage.
   464	
   465	**Steps:**
   466	
   467	1. `python -m unittest discover tests` → must pass cleanly. **AC-F1.**
   468	2. `basedpyright --strict src/ tools/` → zero errors. **AC-F2.**
   469	3. `python tools/check_templates.py src/piketype/backends/{py,cpp,sv}/templates/` → exit 0. **AC-F3.**
   470	4. `python tools/perf_bench.py` → append result as `feature-final` row to `perf.md`. Verify `feature-final.median_ms ≤ 1.25 * baseline.median_ms`. **AC-F4 / FR-25.**
   471	5. Wheel packaging: `pip wheel . -w /tmp/pike_wheel/ --no-deps`; `unzip -l /tmp/pike_wheel/pike_type-*.whl` shows the expected primary templates per backend (`piketype/backends/py/templates/module.j2`, `piketype/backends/cpp/templates/module.j2`, `piketype/backends/sv/templates/module_synth.j2`, `piketype/backends/sv/templates/module_test.j2`, plus each backend's `_macros.j2`). The exact set of `.j2` files is checked against the actual files committed in `src/piketype/backends/{py,cpp,sv}/templates/` (i.e., the wheel must contain every `.j2` that exists in source, no more no less). Install into clean venv → `piketype gen <tmp-copy>/alpha/piketype/types.py` → diff against from-source generation. **AC-F5.**
   472	6. `docs/templates.md` covers FR-22 + FR-24 items (manual checklist). **AC-F6.**
   473	7. `python tools/check_templates.py src/piketype/backends/{py,cpp,sv}/templates/` exits 0 (same script as AC-F3, repeated for AC-F7's audit form).
   474	8. `git log --oneline develop..HEAD` shows commits grouped by Phase 0..3 in order; `git revert <sha-range>` dry-runs cleanly per backend. **AC-F8.**
   475	
   476	**Validation commit:** `steel(validation): record feature-final results` — appends row to `perf.md`, no source changes.
   477	
   478	---
   479	
   480	## Risks and mitigations
   481	
   482	| Risk | Likelihood | Mitigation |
   483	|------|------------|------------|
   484	| Whitespace drift on first template render breaks goldens | High | `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True` in `make_environment`. Migrate one sub-step at a time and diff goldens after each commit. The transitional `body_lines | join("\n")` mechanism preserves line-by-line legacy output verbatim until each sub-step replaces it. |
   485	| Jinja `trim_blocks`/`lstrip_blocks` interacting unexpectedly with literal-heavy template content (e.g., generated SV helper classes containing `begin`/`end` blocks) | Medium | When a literal-heavy block must be preserved verbatim, wrap it in `{% raw %}...{% endraw %}` or pass it through as a precomputed `str` field on the view (the `body_lines` mechanism). Phase 3 commit 4 explicitly tests this on the largest SV `_helper_class` block. |
   486	| `PackageLoader` does not find templates from a wheel install | Medium | Phase 1 commit 2 verifies wheel packaging immediately by building the wheel and running smoke test once the first `.j2` file lands (Phase 0 commit 4 only configures package-data; Phase 1 commit 2 lands the first template and exercises the wheel path). |
   487	| View-model construction order vs. frozen-IR semantics | Low | Builders use only IR read-access; they construct view models with explicit tuples in IR's declaration order (no `set` or `dict` traversal). `tests/test_view_py.py`/`test_view_cpp.py`/`test_view_sv.py` each include a test asserting that field/member tuples preserve declaration order from the source fixture. IR is never mutated — verified by the existing immutable-IR contract. |
   488	| View-model tests over-couple to internal numeric values | Low | Tests assert public-contract values (class names, widths, byte counts, mask literals) — the same values that already appear in goldens. |
   489	| Performance regression > 25% from Jinja template loading overhead | Low–Medium | Measured at every per-backend completion (FR-25). `jinja2.Environment` caches compiled templates by default within a process. `emit_<lang>` constructs the env once per call, so all modules in a single `gen` invocation share compiled-template caches. Mitigation if exceeded: switch to `jinja2.PackageLoader` with bytecode caching enabled. |
   490	| `frozen=True, slots=True` prevents `__post_init__` validation cleanly | Low | Validation lives in builder functions (before construction), so `__post_init__` is rarely needed. If it is needed, `object.__setattr__` is the documented escape. |
   491	| C++ `--namespace` CLI override regression | Medium | `tests/test_view_cpp.py` runs the namespace-override fixture (`tests/fixtures/namespace_override`) end-to-end, asserting the rendered guard macro and namespace open/close strings. This catches regressions before goldens. |
   492	| SV verification helpers contain large mostly-static blocks where parity is brittle | Medium | Phase 3 splits synth and test rendering into separate templates so a parity break is localized to one file. Goldens fail-fast on byte diff. The largest helper-class blocks (`*_helper` classes) are migrated in Phase 3 commit 4 with extra golden checks. |
   493	
   494	---
   495	
   496	## Dependencies and ordering
   497	
   498	- Phase 0 must complete before any of Phase 1/2/3 starts.
   499	- Phase 1 → Phase 2 → Phase 3 (FR-5/CL-1).
   500	- Phase 4 must be the last phase.
   501	- Within each Phase 1/2/3 sub-step commit sequence, commit N+1 depends on commit N's byte parity verification.
   502	- Filter additions (CL-2) and lint-pattern adjustments (FR-21) happen on the sub-step commit that introduces the need; both land via `backends/common/render.py` (CL-2/FR-16) and `tools/check_templates.py` respectively.
   503	
   504	## Out of plan (deliberately deferred)
   505	
   506	- New view-model fields beyond what's needed to render current goldens.
   507	- Refactoring `headers.py` (OOS-7).
   508	- Migrating `runtime`/`build`/`lint`/`test` sub-backends (OOS-2).
   509	- Splitting `view.py` into `view.py + builder.py` if line count grows past ~250 (FR-18 permits as a future refactor; not in this plan).
   510	
   511	## Testing strategy
   512	
   513	- **Existing golden integration tests:** unchanged. Run after every commit. Each commit's correctness criterion is golden bytes parity.
   514	- **New view-model tests** (`tests/test_view_<lang>.py`): introduced in Phase N commit 1. They assert primitive-field values per fixture (one assertion per non-trivial field).
   515	- **New helper tests** (`tests/test_render.py`, `tests/test_check_templates.py`): land in Phase 0 commits 1–2.
   516	- **Idempotency tests** (existing): unchanged; pass throughout because the migration changes how output is produced, not what is produced.
   517	- **C++ namespace override tests:** explicit end-to-end run of the namespace-override fixture in `tests/test_view_cpp.py`.
   518	- **SV synth/test split tests:** explicit assertion in `tests/test_view_sv.py` that synth and test packages produce independent views (no shared mutable state).
   519	
   520	## Estimated commit count

exec
/bin/zsh -lc "nl -ba specs/010-jinja-template-migration/plan.md | sed -n '521,900p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
     1	# Implementation Plan — Jinja Template Migration
     2	
     3	**Spec ID:** 010-jinja-template-migration
     4	**Branch:** feature/010-jinja-template-migration
     5	**Stage:** planning
     6	
     7	This plan executes spec.md (post-clarification, FR-1..FR-25, CL-1..CL-4, AC-*-Py/Cpp/Sv, AC-F1..F8). It is organized as five phases: shared infrastructure → Python backend → C++ backend → SystemVerilog backend → final validation. Each phase is a contiguous sequence of commits on `feature/010-jinja-template-migration`.
     8	
     9	---
    10	
    11	## Architectural overview
    12	
    13	```
    14	IR (frozen)                                    Templates (per backend)
    15	   │                                                  ▲
    16	   ▼                                                  │
    17	build_module_view(module: ModuleIR, type_index)  env.get_template(...).render(view)
    18	   │                                                  ▲
    19	   ▼                                                  │
    20	ModuleView (frozen dataclass)  ───────────────────────┘
    21	
    22	emit_<lang>(repo) {
    23	    env = make_environment(package="piketype.backends.<lang>")
    24	    for module in repo.modules:
    25	        view  = build_module_view(module=module, ...)
    26	        text  = render(env=env, template_name="module.j2", context=view)
    27	        write(path, text)
    28	}
    29	```
    30	
    31	**Key invariants** (all enforced by AC-* gates):
    32	- View models are read-only frozen dataclasses with primitive fields (`int`, `str`, `bool`, `bytes`), `tuple` of view-model field types, or other view-model dataclass instances (FR-8). No `set`/`frozenset`/`dict`/IR-references/callables (FR-9).
    33	- Templates contain no semantics (FR-10), enforced by `tools/check_templates.py` (FR-21).
    34	- `render` returns a string ending in `\n` (FR-3).
    35	- `emit_<lang>` signature unchanged (FR-4, NFR-7).
    36	- Output is byte-for-byte identical at each per-backend completion (FR-7); intermediate commits within a phase target byte parity by use of an **InlineFragmentView passthrough** mechanism described below.
    37	- All custom Jinja filters/globals registered exclusively in `backends/common/render.py` (CL-2, FR-16).
    38	
    39	### InlineFragmentView passthrough — byte-parity strategy
    40	
    41	Each Phase 1/2/3 sub-step commit replaces one slice of the inline emitter with a template, while remaining slices continue to render via the legacy inline path. The plan keeps byte parity at every commit by passing the not-yet-migrated slices through to the template as **already-rendered strings**.
    42	
    43	Concrete mechanism:
    44	- `ModuleView` carries a field `body_lines: tuple[str, ...] | None`. When non-None, the primary template emits `{{ body_lines | join("\n") }}` for the not-yet-templated portion.
    45	- Each sub-step replaces a portion of `body_lines` with a structured field (`types: tuple[TypeView, ...]`, etc.), and the template's body section transitions from `{% if body_lines %}{{ body_lines | join("\n") }}{% endif %}` to a structured loop over `types`.
    46	- After sub-step 4 (fragments), `body_lines` is unused and removed from the view; the field is retired in the cleanup commit.
    47	
    48	This is internal scaffolding strictly contained inside view + template; it does not leak to the public emit API and does not survive into the post-cleanup state.
    49	
    50	---
    51	
    52	## Phase 0 — Shared infrastructure
    53	
    54	**Goal:** Land everything that must exist before the first backend migration. After this phase, the repository builds, all existing tests pass, and the new tools are runnable. No emitter changes yet.
    55	
    56	**Files:**
    57	
    58	| Path                                                            | Action  | Purpose |
    59	|-----------------------------------------------------------------|---------|---------|
    60	| `src/piketype/backends/common/render.py`                        | rewrite | `make_environment(*, package: str) -> jinja2.Environment` and `render(*, env: jinja2.Environment, template_name: str, context: object) -> str`. Custom-filter registration site (CL-2/FR-16). |
    61	| `tools/check_templates.py`                                      | new     | Template-hygiene lint (FR-21). |
    62	| `tests/test_check_templates.py`                                 | new     | Lint script unit tests (FR-21 last paragraph). |
    63	| `tests/test_render.py`                                          | new     | `make_environment` / `render` smoke tests; placeholder for future custom-filter tests (CL-2). |
    64	| `tools/perf_bench.py`                                           | new     | Benchmark CLI (FR-23). |
    65	| `pyproject.toml`                                                | edit    | `[tool.setuptools.package-data]` recursive globs `templates/**/*.j2` for `piketype.backends.{py,cpp,sv}` (FR-14). |
    66	| `MANIFEST.in`                                                   | new/edit| Include rule mirroring FR-14 (defensive, sdist-friendly). |
    67	| `docs/templates.md`                                             | new     | FR-22 + FR-24 sections. |
    68	| `specs/010-jinja-template-migration/perf.md`                    | new     | Pre-migration `baseline_ms` row (CL-4, FR-25). Captured *after* commits 1–5 are merged but *before* any backend migration. |
    69	| (no template directories yet)                                   | n/a     | Empty `templates/` dirs are deferred to Phase 1/2/3 — they are created when their first `.j2` file lands, so the wheel build never tries to package an empty directory. |
    70	
    71	**`backends/common/render.py` exact contract:**
    72	
    73	```python
    74	"""Template rendering helpers for piketype backends."""
    75	from __future__ import annotations
    76	
    77	from dataclasses import asdict, is_dataclass
    78	from typing import TYPE_CHECKING
    79	
    80	import jinja2
    81	
    82	if TYPE_CHECKING:
    83	    pass
    84	
    85	
    86	def make_environment(*, package: str) -> jinja2.Environment:
    87	    """Construct the per-call Jinja environment for a backend package."""
    88	    return jinja2.Environment(
    89	        loader=jinja2.PackageLoader(package, "templates"),
    90	        keep_trailing_newline=True,
    91	        trim_blocks=True,
    92	        lstrip_blocks=True,
    93	        undefined=jinja2.StrictUndefined,
    94	        autoescape=False,
    95	    )
    96	
    97	
    98	def render(*, env: jinja2.Environment, template_name: str, context: object) -> str:
    99	    """Render a template against a view-model dataclass instance."""
   100	    if is_dataclass(context):
   101	        ctx = asdict(context)
   102	    elif isinstance(context, dict):
   103	        ctx = context
   104	    else:
   105	        raise TypeError(f"render context must be a dataclass or dict, got {type(context).__name__}")
   106	    output = env.get_template(template_name).render(**ctx)
   107	    if not output.endswith("\n"):
   108	        output += "\n"
   109	    return output
   110	
   111	
   112	# Custom filters/globals — single auditable site (CL-2, FR-16).
   113	# Registered by mutating the env returned from make_environment via a hook
   114	# in this module if/when filters are introduced. Empty for now; each
   115	# addition documented in docs/templates.md "Custom Filters".
   116	```
   117	
   118	**Commit sequence (Phase 0):**
   119	
   120	1. `feat(common): add make_environment and render helpers` — `render.py` + `tests/test_render.py`.
   121	2. `feat(tools): add check_templates lint script` — `tools/check_templates.py` + `tests/test_check_templates.py`. Lint patterns from FR-21 implemented; tests use `unittest.TestCase` with in-memory template strings (one positive case per pattern, one negative case showing target-language text outside Jinja blocks is not flagged).
   122	3. `feat(tools): add perf_bench CLI` — `tools/perf_bench.py` per FR-23 (median over ≥5 runs against `tests/fixtures/struct_padded`).
   123	4. `feat(build): package backend templates with the wheel` — `pyproject.toml` + `MANIFEST.in`. **No template directories created yet.** Wheel package-data globs are configured but match zero files at this point; the build still succeeds.
   124	5. `docs(templates): add developer-facing architecture doc` — `docs/templates.md` covering FR-22 + FR-24.
   125	6. `steel(perf): capture pre-migration baseline_ms` — runs `tools/perf_bench.py` and writes `specs/010-.../perf.md` with the baseline row only (CL-4).
   126	
   127	**Phase 0 gates:**
   128	- `python -m unittest discover tests` passes.
   129	- `python tools/check_templates.py` exits 0 (no templates to scan).
   130	- `python tools/perf_bench.py` produces `<fixture>\t<median_ms>\t<min_ms>\t<max_ms>\n`.
   131	- `basedpyright --strict src/ tools/` passes.
   132	- `pip wheel . -w /tmp/pike_wheel_ph0/ --no-deps` succeeds (wheel will not contain any `.j2` yet — packaging proof is deferred to Phase 1's first template-landing commit).
   133	
   134	---
   135	
   136	## Phase 1 — Python backend migration
   137	
   138	**Why first:** Per FR-5/CL-1, Python is the simplest target (no `#include`/preprocessor, no SV `_pkg`/`_test_pkg` split). It validates the migration mechanics on the easiest case before C++/SV.
   139	
   140	**Sub-step ordering follows FR-6 verbatim:**
   141	
   142	1. Module/file-level skeleton (header, top-level imports, footer).
   143	2. Top-level type declaration skeletons (class scaffolding for `ScalarAlias`, `Struct`, `Enum`, `Flags`).
   144	3. Repeated helper-method skeletons (`__init__`, `to_bytes`, `from_bytes`, `_to_packed_int`, `_from_packed_int`, `clone`, `__eq__`, `__repr__`, struct field coercers, struct `__setattr__`).
   145	4. Expression and field-level fragments (constants, struct field annotations/defaults, enum member values, flag mask literals).
   146	
   147	**Files:**
   148	
   149	| Path                                              | Action  | Purpose |
   150	|---------------------------------------------------|---------|---------|
   151	| `src/piketype/backends/py/view.py`                | new     | View-model dataclasses + `build_*` functions (FR-1/8/18). |
   152	| `src/piketype/backends/py/templates/module.j2`    | new     | Primary module template (FR-12). |
   153	| `src/piketype/backends/py/templates/_macros.j2`   | new     | Shared macros invoked from `module.j2`. |
   154	| `src/piketype/backends/py/emitter.py`             | rewrite | Shrink to: build view → render → write. Remove `_render_*` helpers (FR-19). |
   155	| `tests/test_view_py.py`                           | new     | View-model tests against `struct_padded`, `scalar_wide`, `enum_basic` (FR-18). |
   156	| `specs/010-.../perf.md`                           | append  | `py-complete` row (FR-25). |
   157	
   158	**Concrete view-model dataclasses (Python backend):**
   159	
   160	```python
   161	@dataclass(frozen=True, slots=True)
   162	class ConstantView:
   163	    name: str
   164	    value_expr: str               # pre-rendered Python expression, e.g. "(1 << 32)" or "MAX_VALUE"
   165	
   166	@dataclass(frozen=True, slots=True)
   167	class ScalarAliasView:
   168	    class_name: str               # e.g. "addr_ct"
   169	    width: int
   170	    signed: bool
   171	    byte_count: int
   172	    is_wide: bool                 # width > 64
   173	    min_value: int
   174	    max_value: int
   175	    mask: int                     # 0 if width > 64
   176	    sign_bit: int                 # 0 if not signed; (1 << (width-1)) otherwise
   177	    pad_bits: int                 # byte_count*8 - width (for signed narrow)
   178	    msb_byte_mask: int            # (1 << (width % 8)) - 1 if width % 8 else 0xFF (for wide)
   179	
   180	@dataclass(frozen=True, slots=True)
   181	class EnumMemberView:
   182	    name: str
   183	    resolved_value_expr: str      # pre-rendered, e.g. "0", "16"
   184	
   185	@dataclass(frozen=True, slots=True)
   186	class EnumView:
   187	    class_name: str               # wrapper class, e.g. "color_ct"
   188	    enum_class_name: str          # IntEnum subclass, e.g. "color_enum_t"
   189	    width: int
   190	    byte_count: int
   191	    mask: int                     # (1 << width) - 1
   192	    first_member_name: str        # for default arg
   193	    members: tuple[EnumMemberView, ...]  # declaration order
   194	
   195	@dataclass(frozen=True, slots=True)
   196	class FlagFieldView:
   197	    name: str
   198	    bit_mask: int                 # 1 << (total_bits - 1 - index)
   199	
   200	@dataclass(frozen=True, slots=True)
   201	class FlagsView:
   202	    class_name: str
   203	    num_flags: int                # WIDTH
   204	    byte_count: int               # BYTE_COUNT
   205	    total_bits: int               # byte_count * 8
   206	    data_mask: int                # ((1 << num_flags) - 1) << alignment_bits
   207	    fields: tuple[FlagFieldView, ...]
   208	
   209	# Struct field discriminators precompute every branch of the current
   210	# match-case in _render_py_struct_*. The template selects on these
   211	# booleans; it never inspects target_kind by string.
   212	
   213	@dataclass(frozen=True, slots=True)
   214	class StructFieldView:
   215	    name: str
   216	    annotation: str               # pre-rendered "int", "bytes", "addr_ct | None"
   217	    default_expr: str             # pre-rendered "0", 'b"\\x00" * 4', "field(default_factory=foo_ct)"
   218	    byte_count: int               # field_byte_count
   219	    pack_bits: int                # byte_count * 8 (precomputed; FR-10 forbids template arithmetic on this)
   220	    # discriminators (exactly one is True)

 succeeded in 0ms:
   521	
   522	- Phase 0: 6 commits
   523	- Phase 1: 7 commits (6 migration + 1 perf row)
   524	- Phase 2: 7 commits
   525	- Phase 3: 7 commits
   526	- Phase 4: 1 commit
   527	- Total: ~28 commits on `feature/010-jinja-template-migration`.

exec
/bin/zsh -lc "nl -ba .steel/constitution.md | sed -n '1,220p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
     1	# Project Constitution
     2	
     3	## Governing Principles
     4	
     5	1. **Single source of truth.** Hardware-oriented types are defined once in Python DSL modules. All generated outputs (SystemVerilog, C++, Python) are derived from that single definition.
     6	2. **Immutable boundaries.** The pipeline has four distinct stages (Discovery -> DSL -> IR -> Backends) with frozen, immutable handoff between them. Backends and validators consume only frozen IR, never mutable DSL objects.
     7	3. **Deterministic output.** Generated code must be byte-for-byte reproducible given the same inputs. No timestamps, run-specific metadata, or non-deterministic ordering.
     8	4. **Correctness over convenience.** Strict type checking, explicit validation passes, and golden-file testing guard against silent regressions. If something cannot be validated, it should not be generated.
     9	5. **Template-first generation.** Generated file structure and syntax live in templates wherever practical. Backend code builds typed view models from IR and handles semantic decisions; templates handle presentation only. Inline string building is reserved for trivial fragments or glue.
    10	6. **Generated runtime, not handwritten.** Shared runtime support packages are generated outputs, not manually maintained infrastructure.
    11	
    12	## Technology Stack
    13	
    14	| Component            | Technology                | Version/Notes                                |
    15	|----------------------|---------------------------|----------------------------------------------|
    16	| Implementation       | Python                    | >= 3.12                                      |
    17	| Package build        | setuptools + wheel        | setuptools >= 69                             |
    18	| Project metadata     | `pyproject.toml`          | PEP 621                                      |
    19	| Template engine      | Jinja2                    | >= 3.1                                      |
    20	| Static type checking | basedpyright              | >= 1.20.0, strict mode                       |
    21	| Test runner          | unittest (stdlib)         | Golden-file / fixture-based integration tests |
    22	| CLI framework        | argparse (stdlib)         | Thin dispatch layer                          |
    23	| License              | GPL-3.0-or-later          |                                              |
    24	| Target outputs       | SystemVerilog, C++20, Python 3.12+ |                                      |
    25	
    26	No external runtime dependencies beyond Jinja2. Dev tooling is limited to basedpyright and pytest.
    27	
    28	## Coding Standards
    29	
    30	### Python
    31	
    32	- **`from __future__ import annotations`** in every module.
    33	- **`basedpyright` strict mode** must pass with zero errors. `reportMissingTypeStubs`, `reportAny`, and `reportExplicitAny` are suppressed.
    34	- **Frozen dataclasses** (`@dataclass(frozen=True, slots=True)`) for all IR nodes. Mutable dataclasses with `slots=True` for DSL runtime objects.
    35	- **Naming conventions:**
    36	  - `snake_case` for functions, methods, variables, and module names.
    37	  - `PascalCase` for classes.
    38	  - `UPPER_SNAKE_CASE` for module-level constants.
    39	  - Private helpers prefixed with `_`.
    40	  - DSL type names end with `_t` suffix (e.g., `addr_t`).
    41	  - Generated wrapper class names use `_ct` suffix (e.g., `addr_ct`).
    42	- **No wildcard imports.** All imports are explicit.
    43	- **Pattern matching** (`match`/`case`) preferred for IR node dispatch.
    44	- **Keyword-only arguments** (`*`) for helper functions to enforce clarity at call sites.
    45	- **Type unions** use the `type X = A | B` syntax (Python 3.12+), not `typing.Union`.
    46	
    47	### Generated Code
    48	
    49	- All generated files carry a machine-readable header comment identifying the source DSL module(s).
    50	- New or changed generated outputs should be backed by Jinja2 templates whenever the output has meaningful structure. This keeps generated formats easy to inspect, tweak, and extend.
    51	- Backend Python must prepare explicit view-model data for templates. It must not hide generated-file layout inside large ad hoc string-building functions.
    52	- SystemVerilog outputs use `_pkg` suffix for synthesizable packages and `_test_pkg` for verification-only packages.
    53	- C++ headers use include guards (`#ifndef`/`#define`/`#endif`), not `#pragma once`.
    54	- Python generated modules include `__init__.py` files for the full package chain.
    55	
    56	### Project Layout
    57	
    58	```
    59	src/piketype/          -- implementation source
    60	  cli.py             -- thin CLI entry point
    61	  commands/          -- command orchestration (gen, build, test, lint)
    62	  discovery/         -- repo scanning for piketype/ modules
    63	  loader/            -- Python module execution
    64	  dsl/               -- mutable runtime DSL object model
    65	  ir/                -- frozen immutable IR nodes and builders
    66	  validate/          -- explicit validation passes over IR
    67	  backends/          -- code emitters (sv/, py/, cpp/, runtime/, build/, test/, lint/)
    68	  manifest/          -- JSON manifest model and serialization
    69	tests/
    70	  fixtures/          -- input fixture repos
    71	  goldens/gen/       -- expected golden outputs
    72	docs/                -- RFC, product spec, architecture docs
    73	```
    74	
    75	## Development Guidelines
    76	
    77	### Branching & Commits
    78	
    79	- **Branch naming:** `feature/<name>` for feature branches, branching from `develop`.
    80	- **Commit messages:** Conventional Commits format: `<type>(<scope>): <description>`.
    81	  - Types: `feat`, `fix`, `refactor`, `docs`, `test`, `steel`.
    82	  - Scope matches the subsystem: `sv`, `cpp`, `py`, `dsl`, `emitter`, `codegen`, `init`, etc.
    83	
    84	### Testing
    85	
    86	- **Golden-file integration tests** are the primary correctness mechanism. Each test case:
    87	  1. Copies a fixture repo from `tests/fixtures/<case>/project/` into a temp directory.
    88	  2. Runs `piketype gen` via subprocess.
    89	  3. Compares the full `gen/` output tree byte-for-byte against `tests/goldens/gen/<case>/`.
    90	- **Idempotency tests** verify that running `piketype gen` twice on the same input produces identical output and does not rescan generated files as DSL modules.
    91	- **Negative tests** verify that invalid inputs produce specific error messages and non-zero exit codes.
    92	- Tests use `unittest.TestCase`, not pytest fixtures or parametrize.
    93	- Golden files are committed to the repo and updated explicitly when output format changes.
    94	
    95	### Adding a New Type or Feature
    96	
    97	1. Define the DSL node in `dsl/`.
    98	2. Add the frozen IR node in `ir/nodes.py`.
    99	3. Add freeze logic in `dsl/freeze.py` and IR builder logic in `ir/builders.py`.
   100	4. Add validation rules in `validate/engine.py`.
   101	5. Add emission in each backend (`sv/emitter.py`, `cpp/emitter.py`, `py/emitter.py`).
   102	6. Create a fixture repo in `tests/fixtures/` and golden output in `tests/goldens/gen/`.
   103	7. Add an integration test case in `tests/test_gen_const_sv.py` (or a new test file for the feature area).
   104	
   105	## Constraints
   106	
   107	1. **Python >= 3.12 required.** The codebase uses `type` statement aliases, pattern matching, and `X | Y` union syntax that require 3.12+.
   108	2. **No UVM dependency.** Verification helpers in generated SystemVerilog are standalone classes, not UVM components.
   109	3. **Packed types only.** All generated SystemVerilog types must be packed (`typedef struct packed`). Unpacked types are out of scope for v1.
   110	4. **No cross-module type references (current milestone).** Struct fields referencing types from other modules are rejected by validation. This constraint will be relaxed in a future milestone.
   111	5. **Constant widths restricted to 32/64 bits.** Arbitrary-width constants are not supported; the validation layer rejects other widths.
   112	6. **Minimal runtime dependencies.** Only Jinja2 at runtime. No heavy frameworks, no network dependencies.
   113	7. **Stable, reproducible output.** Ordering is by dependency-first then declaration order. No randomness or environment-dependent output.

exec
/bin/zsh -lc "nl -ba specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md | sed -n '1,220p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
     1	Reading additional input from stdin...
     2	OpenAI Codex v0.125.0 (research preview)
     3	--------
     4	workdir: /Users/ezchi/Projects/pike-type
     5	model: gpt-5.5
     6	provider: openai
     7	approval: never
     8	sandbox: workspace-write [workdir, /tmp, $TMPDIR, /Users/ezchi/.codex/memories]
     9	reasoning effort: xhigh
    10	reasoning summaries: none
    11	session id: 019dd8f0-6ea2-7120-93d7-de8867b3b637
    12	--------
    13	user
    14	Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/planning/iter1-gauge-prompt.md
    15	codex
    16	I’ll read the referenced prompt first, then I’ll execute exactly what it asks in the current repo context.
    17	exec
    18	/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/planning/iter1-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
    19	 succeeded in 0ms:
    20	# Gauge Review Prompt — Planning Iteration 1
    21	
    22	You are the **Gauge** in a dual-agent Forge-Gauge loop. The clarification stage produced an APPROVED, fully resolved spec. This is the planning stage: the Forge has produced an implementation plan at `specs/010-jinja-template-migration/plan.md`.
    23	
    24	## Inputs to Review
    25	
    26	1. **Implementation plan:** `specs/010-jinja-template-migration/plan.md`.
    27	2. **Specification (binding):** `specs/010-jinja-template-migration/spec.md`.
    28	3. **Project Constitution:** `.steel/constitution.md`.
    29	4. **Repository state:** the `pike-type` project root. You may inspect files to validate concrete claims (CLI signatures, current emitter sizes, fixture paths).
    30	
    31	## Review Instructions
    32	
    33	Evaluate the plan on these dimensions:
    34	
    35	1. **Spec coverage.** Does every FR (FR-1..FR-25), every NFR (NFR-1..NFR-7), every per-backend AC (AC-*-Py/Cpp/Sv), every feature-final AC (AC-F1..F8), and every CL (CL-1..CL-4) map to a concrete phase/commit in the plan? Flag any spec requirement with no implementation step.
    36	
    37	2. **Phase ordering and dependencies.** Is the dependency chain correct (Phase 0 before any backend migration; Phase 1 → 2 → 3; Phase 4 last)? Is anything in the wrong phase?
    38	
    39	3. **Concrete actionability.** For each commit in each phase, is the commit's content described well enough that an implementer can execute it without re-deriving design decisions?
    40	
    41	4. **View-model shape correctness.**
    42	   - Does the sketched Python `ScalarAliasView` / `StructFieldView` / `StructView` carry every field that the current `_render_py_*` functions actually use? Spot-check against `src/piketype/backends/py/emitter.py`. Look especially at: signed sign-extension fields, wide-scalar MSB byte mask, struct alignment bytes, struct field byte_count, struct field default expression.
    43	   - Does C++/SV need any additional view fields the plan does not mention? (e.g., C++ namespace nesting strings, include guard symbols, SV `_pkg`/`_test_pkg` distinction.)
    44	
    45	5. **Byte-parity strategy.** Is the plan's claim that each Phase 1/2/3 commit produces byte-identical output to the previous commit credible? In particular:
    46	   - Phase 1 commits 2–5 each migrate a slice of rendering. Is the commit-by-commit mechanism (e.g., "add template that renders header + imports + footer; rest of body still inline") feasible without intermediate byte-diff?
    47	   - If not, the plan must say so and propose an alternative (e.g., "commits 2–5 are internal refactor commits whose byte parity is checked only at the end of Phase 1").
    48	
    49	6. **Risk register completeness.** Are there obvious risks the register misses? Specifically:
    50	   - Wheel-build environments that strip empty directories (the plan mentions `.gitkeep`).
    51	   - Jinja's auto-trimming interacting with raw-string blocks in templates.
    52	   - View-model construction order vs. IR `frozen=True` semantics.
    53	   - C++ `namespace` rendering depending on `--namespace` CLI override.
    54	
    55	7. **Constitution alignment.** The plan should respect:
    56	   - Principle 2 (immutable boundaries IR → backend): view models clean-break IR? Yes per FR-9; verify.
    57	   - Principle 5 (template-first): every backend has templates per FR-12? Yes per plan; verify.
    58	   - Coding standards: frozen dataclasses (FR-1), `from __future__ import annotations`, snake_case, no wildcard imports.
    59	   - "Adding a new type or feature" workflow: not directly relevant since this is structural, but the plan should not break that workflow for future contributors.
    60	
    61	## Output Format
    62	
    63	- Executive summary (2–4 sentences).
    64	- Numbered issue list with severity (`BLOCKING`/`WARNING`/`NOTE`), the FR/AC/phase/commit identifier, the problem, and a suggested fix.
    65	- Final line: exactly `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after.
    66	
    67	A plan can be APPROVED with open `WARNING`/`NOTE` items as long as no `BLOCKING` issue remains.
    68	
    69	codex
    70	This is a Gauge review for the Steel planning stage. I’m going to use the local `steel-plan` workflow instructions, then cross-check the plan against the binding spec and current emitters.
    71	exec
    72	/bin/zsh -lc "sed -n '1,260p' /Users/ezchi/Projects/pike-type/.agents/skills/steel-plan/SKILL.md" in /Users/ezchi/Projects/pike-type
    73	 succeeded in 0ms:
    74	---
    75	name: steel-plan
    76	description: "Steel-Kit workflow skill: Generate an implementation plan using the Forge-Gauge loop."
    77	---
    78	
    79	# steel-plan
    80	
    81	Use this skill when the user invokes `/steel-plan` or asks to run the corresponding Steel-Kit workflow step.
    82	
    83	Generate an implementation plan using the Forge-Gauge loop.
    84	
    85	## Prerequisites
    86	- `.steel/constitution.md` must contain a real project constitution, not the placeholder template
    87	- `.steel/state.json` currentStage must be `planning`
    88	
    89	## Steps
    90	
    91	0. Run `/clear` to clear the conversation context before starting this stage.
    92	
    93	1. Read `.steel/state.json` and `.steel/config.json`. Verify stage is `planning`.
    94	
    95	2. Read `specs/<specId>/spec.md`, `specs/<specId>/clarifications.md` (if exists), and `.steel/constitution.md`.
    96	
    97	3. **FORGE-GAUGE LOOP** (max iterations from config):
    98	
    99	   ### Forge Phase (you are the Forge)
   100	   a. Create a technical implementation plan covering:
   101	      - Architecture Overview
   102	      - Components (responsibilities, interfaces, dependencies)
   103	      - Data Model
   104	      - API Design
   105	      - Dependencies (external libraries/tools)
   106	      - Implementation Strategy (phased approach)
   107	      - Risks and Mitigations
   108	      - Testing Strategy
   109	
   110	      **The Project Constitution is the highest authority.** If prior Gauge feedback contradicts the constitution, IGNORE that feedback. Do not blindly accept all suggestions.
   111	
   112	   b. Write the plan to `specs/<specId>/plan.md`
   113	   c. Save a copy to `specs/<specId>/artifacts/planning/iterN-forge.md`
   114	   d. Git commit: `forge(planning): iteration N output [iteration N]`
   115	
   116	   ### Gauge Phase
   117	   e. Call the Gauge LLM (per config) to review the plan. **IMPORTANT: Run the command from the project's working directory, NOT /tmp.**
   118	      - Write the full review prompt to a file at `specs/<specId>/artifacts/planning/iterN-gauge-prompt.md`
   119	      - If gauge is `gemini`: run `gemini "Read and follow the instructions in <absolute-path-to-prompt-file>"` in the current project directory
   120	      - If gauge is `codex`: run `codex exec "Read and follow the instructions in <absolute-path-to-prompt-file>"` in the current project directory
   121	      - If gauge is `claude`: Review critically yourself as the Gauge role.
   122	
   123	      Review criteria: spec coverage, architecture soundness, simplicity, risk assessment, testing strategy, alignment with constitution. End with `VERDICT: APPROVE` or `VERDICT: REVISE`.
   124	
   125	   f. Save review to `specs/<specId>/artifacts/planning/iterN-gauge.md`
   126	   g. Git commit: `gauge(planning): iteration N review — <verdict> [iteration N]`
   127	
   128	   h. If **APPROVE**: break loop. If **REVISE**: critically evaluate feedback against constitution, incorporate valid points, and loop.
   129	
   130	4. Auto-advance to `task_breakdown` stage. **No human approval needed here.**
   131	
   132	5. Update `.steel/state.json`, tag `steel/<specId>/planning-complete`.
   133	
   134	6. **Track skills used**: Update `.steel/state.json` field `skillsUsed.planning` with an array of skill names you invoked during this stage. If no skills were used, set it to `[]`.
   135	
   136	7. Tell the user: "Plan complete. Run `/steel-tasks` to break down tasks."
   137	
   138	
   139	codex
   140	I’ve confirmed the skill instructions; this turn is the Gauge phase only, not a full planning-stage automation run. Next I’m reading the plan, spec, constitution, and backend emitters to verify the plan’s claims instead of reviewing it abstractly.
   141	exec
   142	/bin/zsh -lc "sed -n '1,320p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
   143	exec
   144	/bin/zsh -lc "sed -n '1,260p' .steel/constitution.md" in /Users/ezchi/Projects/pike-type
   145	exec
   146	/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
   147	 succeeded in 0ms:
   148	# Project Constitution
   149	
   150	## Governing Principles
   151	
   152	1. **Single source of truth.** Hardware-oriented types are defined once in Python DSL modules. All generated outputs (SystemVerilog, C++, Python) are derived from that single definition.
   153	2. **Immutable boundaries.** The pipeline has four distinct stages (Discovery -> DSL -> IR -> Backends) with frozen, immutable handoff between them. Backends and validators consume only frozen IR, never mutable DSL objects.
   154	3. **Deterministic output.** Generated code must be byte-for-byte reproducible given the same inputs. No timestamps, run-specific metadata, or non-deterministic ordering.
   155	4. **Correctness over convenience.** Strict type checking, explicit validation passes, and golden-file testing guard against silent regressions. If something cannot be validated, it should not be generated.
   156	5. **Template-first generation.** Generated file structure and syntax live in templates wherever practical. Backend code builds typed view models from IR and handles semantic decisions; templates handle presentation only. Inline string building is reserved for trivial fragments or glue.
   157	6. **Generated runtime, not handwritten.** Shared runtime support packages are generated outputs, not manually maintained infrastructure.
   158	
   159	## Technology Stack
   160	
   161	| Component            | Technology                | Version/Notes                                |
   162	|----------------------|---------------------------|----------------------------------------------|
   163	| Implementation       | Python                    | >= 3.12                                      |
   164	| Package build        | setuptools + wheel        | setuptools >= 69                             |
   165	| Project metadata     | `pyproject.toml`          | PEP 621                                      |
   166	| Template engine      | Jinja2                    | >= 3.1                                      |
   167	| Static type checking | basedpyright              | >= 1.20.0, strict mode                       |
   168	| Test runner          | unittest (stdlib)         | Golden-file / fixture-based integration tests |
   169	| CLI framework        | argparse (stdlib)         | Thin dispatch layer                          |
   170	| License              | GPL-3.0-or-later          |                                              |
   171	| Target outputs       | SystemVerilog, C++20, Python 3.12+ |                                      |
   172	
   173	No external runtime dependencies beyond Jinja2. Dev tooling is limited to basedpyright and pytest.
   174	
   175	## Coding Standards
   176	
   177	### Python
   178	
   179	- **`from __future__ import annotations`** in every module.
   180	- **`basedpyright` strict mode** must pass with zero errors. `reportMissingTypeStubs`, `reportAny`, and `reportExplicitAny` are suppressed.
   181	- **Frozen dataclasses** (`@dataclass(frozen=True, slots=True)`) for all IR nodes. Mutable dataclasses with `slots=True` for DSL runtime objects.
   182	- **Naming conventions:**
   183	  - `snake_case` for functions, methods, variables, and module names.
   184	  - `PascalCase` for classes.
   185	  - `UPPER_SNAKE_CASE` for module-level constants.
   186	  - Private helpers prefixed with `_`.
   187	  - DSL type names end with `_t` suffix (e.g., `addr_t`).
   188	  - Generated wrapper class names use `_ct` suffix (e.g., `addr_ct`).
   189	- **No wildcard imports.** All imports are explicit.
   190	- **Pattern matching** (`match`/`case`) preferred for IR node dispatch.
   191	- **Keyword-only arguments** (`*`) for helper functions to enforce clarity at call sites.
   192	- **Type unions** use the `type X = A | B` syntax (Python 3.12+), not `typing.Union`.
   193	
   194	### Generated Code
   195	
   196	- All generated files carry a machine-readable header comment identifying the source DSL module(s).
   197	- New or changed generated outputs should be backed by Jinja2 templates whenever the output has meaningful structure. This keeps generated formats easy to inspect, tweak, and extend.
   198	- Backend Python must prepare explicit view-model data for templates. It must not hide generated-file layout inside large ad hoc string-building functions.
   199	- SystemVerilog outputs use `_pkg` suffix for synthesizable packages and `_test_pkg` for verification-only packages.
   200	- C++ headers use include guards (`#ifndef`/`#define`/`#endif`), not `#pragma once`.
   201	- Python generated modules include `__init__.py` files for the full package chain.
   202	
   203	### Project Layout
   204	
   205	```
   206	src/piketype/          -- implementation source
   207	  cli.py             -- thin CLI entry point
   208	  commands/          -- command orchestration (gen, build, test, lint)
   209	  discovery/         -- repo scanning for piketype/ modules
   210	  loader/            -- Python module execution
   211	  dsl/               -- mutable runtime DSL object model
   212	  ir/                -- frozen immutable IR nodes and builders
   213	  validate/          -- explicit validation passes over IR
   214	  backends/          -- code emitters (sv/, py/, cpp/, runtime/, build/, test/, lint/)
   215	  manifest/          -- JSON manifest model and serialization
   216	tests/
   217	  fixtures/          -- input fixture repos
   218	  goldens/gen/       -- expected golden outputs
   219	docs/                -- RFC, product spec, architecture docs
   220	```

exec
/bin/zsh -lc 'tail -n 80 specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
   808	        fbc = _field_byte_count(field=field, type_index=type_index)
   809	        lines.extend([
   810	            "    begin",
   811	            f"      byte unsigned field_bytes[] = new[{fbc}];",
   812	            f"      for (int i = 0; i < {fbc}; i++) field_bytes[i] = bytes[byte_idx + i];",
   813	            f"      {field.name}.from_bytes(field_bytes);",
   814	            f"      byte_idx += {fbc};",
   815	            "    end",
   816	        ])
   817	    else:
   818	        fbc = _field_byte_count(field=field, type_index=type_index)
   819	        w = _field_data_width(field=field, type_index=type_index)
   820	        total_bits = fbc * 8
   821	        signed = _is_field_signed(field=field, type_index=type_index)
   822	        pad = field.padding_bits
   823	        lines.append("    begin")
   824	        lines.append(f"      logic [{total_bits - 1}:0] fb;")
   825	        lines.append("      fb = '0;")
   826	        lines.append(f"      for (int i = 0; i < {fbc}; i++) fb[({fbc} - 1 - i)*8 +: 8] = bytes[byte_idx + i];")
   827	        if pad > 0 and signed:
   828	            lines.extend([
   829	                f"      for (int i = {w}; i < {total_bits}; i++) begin",
   830	                f"        if (fb[i] !== fb[{w - 1}]) begin",
   831	                f'          $fatal(1, "{class_name}.from_bytes signed padding mismatch for field {field.name}");',
   832	                "        end",
   833	                "      end",
   834	            ])
   835	        lines.append(f"      {field.name} = fb[{w - 1}:0];")
   836	        lines.append(f"      byte_idx += {fbc};")
   837	        lines.append("    end")
   838	    return lines
   839	
   840	

codex
Executive summary: The plan has the right top-level phase order, but it is not implementable against the binding spec as written. The main failures are commit ordering versus FR-6, incomplete view-model shapes, and an unsupported byte-parity claim for mixed inline/template commits. It needs revision.

1. **BLOCKING — FR-6 / CL-1 / Phase 1-3 commit sequences.** The backend commits migrate by type family (`scalar`, then `struct`, then `enum/flags`) instead of the required sub-order: module skeleton → top-level type declaration skeletons → helper-method skeletons → expression/field fragments. That violates the spec’s required migration order. Fix by restructuring each backend block around FR-6 sub-steps, not type families.

2. **BLOCKING — FR-8 / FR-10 / FR-18 / Phase 1 view model.** The Python view sketch is incomplete. Current Python rendering needs enum class name, enum wrapper width/byte_count/first member/mask, flags field masks/data mask, struct field min/max, padding bits, sign-bit index, and target kind for type refs. `FlagsFieldView` is referenced but not defined. Fix by expanding the sketch into concrete dataclasses that cover every value used by current `_render_py_*` helpers.

3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.

4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.

5. **BLOCKING — FR-7 / FR-20 / Phase 1 commits 2-5.** The byte-parity strategy is underspecified. “Template renders header/imports/footer; rest inline” and partial type migration can work only if the plan defines temporary legacy body/type fragments and how ordering is preserved. Fix by either documenting a temporary `InlineFragmentView` strategy with per-commit golden checks, or state that intermediate commits are internal refactors and parity is checked only at backend completion.

6. **WARNING — FR-14 / AC-F5 / Phase 0 and Phase 4.** The Phase 0 wheel-packaging smoke test is not meaningful before `.j2` files exist; empty template dirs or `.gitkeep` do not prove package-data works, and wheels may strip empty dirs. Also, Phase 4’s “nine .j2 files” requirement is stricter and inconsistent with the spec. Fix by checking actual expected primary templates per backend after templates land, not a hardcoded count.

7. **WARNING — Risk register.** It misses two required risks: Jinja trim/lstrip behavior around raw blocks or literal-heavy helper templates, and view-model construction order versus frozen IR semantics. Add explicit mitigations: golden checks around raw/literal-heavy templates, and builder tests asserting declaration-order tuples without mutating IR.

8. **WARNING — FR-2 / CL-2 / Phase 0.** The render helper commit does not spell out the exact required Jinja environment options and the architecture snippet calls `make_environment` positionally despite the planned keyword-only signature. Fix the plan to name the exact `Environment` options and require all custom filters/globals to be auditable in `backends/common/render.py`.

9. **NOTE — C++ namespace override.** The plan mentions namespace/guard precomputation, which is correct, but it should explicitly include the existing `--namespace` override fixture in C++ view/golden validation. This is a known regression point.

VERDICT: REVISE
2026-04-29T11:14:40.450521Z ERROR codex_core::session: failed to record rollout items: thread 019dd8f0-6ea2-7120-93d7-de8867b3b637 not found
tokens used
115,367
Executive summary: The plan has the right top-level phase order, but it is not implementable against the binding spec as written. The main failures are commit ordering versus FR-6, incomplete view-model shapes, and an unsupported byte-parity claim for mixed inline/template commits. It needs revision.

1. **BLOCKING — FR-6 / CL-1 / Phase 1-3 commit sequences.** The backend commits migrate by type family (`scalar`, then `struct`, then `enum/flags`) instead of the required sub-order: module skeleton → top-level type declaration skeletons → helper-method skeletons → expression/field fragments. That violates the spec’s required migration order. Fix by restructuring each backend block around FR-6 sub-steps, not type families.

2. **BLOCKING — FR-8 / FR-10 / FR-18 / Phase 1 view model.** The Python view sketch is incomplete. Current Python rendering needs enum class name, enum wrapper width/byte_count/first member/mask, flags field masks/data mask, struct field min/max, padding bits, sign-bit index, and target kind for type refs. `FlagsFieldView` is referenced but not defined. Fix by expanding the sketch into concrete dataclasses that cover every value used by current `_render_py_*` helpers.

3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.

4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.

5. **BLOCKING — FR-7 / FR-20 / Phase 1 commits 2-5.** The byte-parity strategy is underspecified. “Template renders header/imports/footer; rest inline” and partial type migration can work only if the plan defines temporary legacy body/type fragments and how ordering is preserved. Fix by either documenting a temporary `InlineFragmentView` strategy with per-commit golden checks, or state that intermediate commits are internal refactors and parity is checked only at backend completion.

6. **WARNING — FR-14 / AC-F5 / Phase 0 and Phase 4.** The Phase 0 wheel-packaging smoke test is not meaningful before `.j2` files exist; empty template dirs or `.gitkeep` do not prove package-data works, and wheels may strip empty dirs. Also, Phase 4’s “nine .j2 files” requirement is stricter and inconsistent with the spec. Fix by checking actual expected primary templates per backend after templates land, not a hardcoded count.

7. **WARNING — Risk register.** It misses two required risks: Jinja trim/lstrip behavior around raw blocks or literal-heavy helper templates, and view-model construction order versus frozen IR semantics. Add explicit mitigations: golden checks around raw/literal-heavy templates, and builder tests asserting declaration-order tuples without mutating IR.

8. **WARNING — FR-2 / CL-2 / Phase 0.** The render helper commit does not spell out the exact required Jinja environment options and the architecture snippet calls `make_environment` positionally despite the planned keyword-only signature. Fix the plan to name the exact `Environment` options and require all custom filters/globals to be auditable in `backends/common/render.py`.

9. **NOTE — C++ namespace override.** The plan mentions namespace/guard precomputation, which is correct, but it should explicitly include the existing `--namespace` override fixture in C++ view/golden validation. This is a known regression point.

VERDICT: REVISE

exec
/bin/zsh -lc "nl -ba src/piketype/backends/py/emitter.py | sed -n '1,220p'" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "nl -ba src/piketype/backends/py/emitter.py | sed -n '220,560p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
     1	"""Python backend."""
     2	
     3	from __future__ import annotations
     4	
     5	from pathlib import Path
     6	
     7	from piketype.backends.common.headers import render_header
     8	from piketype.ir.nodes import (
     9	    BinaryExprIR,
    10	    ConstRefExprIR,
    11	    EnumIR,
    12	    ExprIR,
    13	    FieldTypeIR,
    14	    FlagsIR,
    15	    IntLiteralExprIR,
    16	    ModuleIR,
    17	    RepoIR,
    18	    ScalarAliasIR,
    19	    ScalarTypeSpecIR,
    20	    StructIR,
    21	    StructFieldIR,
    22	    TypeDefIR,
    23	    TypeRefIR,
    24	    UnaryExprIR,
    25	    byte_count,
    26	)
    27	from piketype.paths import py_module_output_path
    28	
    29	
    30	def emit_py(repo: RepoIR) -> list[Path]:
    31	    """Emit Python outputs."""
    32	    written_paths: list[Path] = []
    33	    repo_root = Path(repo.repo_root)
    34	    py_root = repo_root / "gen" / "py"
    35	    _ensure_package_init(py_root, written_paths)
    36	    for module in repo.modules:
    37	        output_path = py_module_output_path(
    38	            repo_root=repo_root,
    39	            module_path=repo_root / module.ref.repo_relative_path,
    40	        )
    41	        output_path.parent.mkdir(parents=True, exist_ok=True)
    42	        _ensure_package_chain(output_path.parent, py_root, written_paths)
    43	        output_path.write_text(render_module_py(module), encoding="utf-8")
    44	        written_paths.append(output_path)
    45	    return written_paths
    46	
    47	
    48	def render_module_py(module: ModuleIR) -> str:
    49	    """Render a Python module."""
    50	    header = render_header(source_paths=(module.ref.repo_relative_path,)).replace("//", "#")
    51	    type_index = {type_ir.name: type_ir for type_ir in module.types}
    52	    has_types = bool(module.types)
    53	    has_structs = any(isinstance(type_ir, StructIR) for type_ir in module.types)
    54	    has_enums = any(isinstance(type_ir, EnumIR) for type_ir in module.types)
    55	    body_lines: list[str] = []
    56	    if has_types:
    57	        body_lines.append("from __future__ import annotations")
    58	        if has_structs:
    59	            body_lines.append("")
    60	            body_lines.append("from dataclasses import dataclass, field")
    61	        if has_enums:
    62	            body_lines.append("")
    63	            body_lines.append("from enum import IntEnum")
    64	        body_lines.append("")
    65	    body_lines.extend(f"{const.name} = {_render_py_expr(expr=const.expr)}" for const in module.constants)
    66	    if module.constants and module.types:
    67	        body_lines.append("")
    68	    for index, type_ir in enumerate(module.types):
    69	        if index > 0:
    70	            body_lines.append("")
    71	        if isinstance(type_ir, ScalarAliasIR):
    72	            body_lines.extend(_render_py_scalar_alias(type_ir=type_ir))
    73	        elif isinstance(type_ir, StructIR):
    74	            body_lines.extend(_render_py_struct(type_ir=type_ir, type_index=type_index))
    75	        elif isinstance(type_ir, FlagsIR):
    76	            body_lines.extend(_render_py_flags(type_ir=type_ir))
    77	        elif isinstance(type_ir, EnumIR):
    78	            body_lines.extend(_render_py_enum(type_ir=type_ir))
    79	    return f"{header}\n" + "\n".join(body_lines) + "\n"
    80	
    81	
    82	def _ensure_package_init(package_dir: Path, written_paths: list[Path]) -> None:
    83	    """Create a package ``__init__.py`` if missing."""
    84	    package_dir.mkdir(parents=True, exist_ok=True)
    85	    init_path = package_dir / "__init__.py"
    86	    if not init_path.exists():
    87	        init_path.write_text("# Generated by piketype\n# Do not edit by hand.\n", encoding="utf-8")
    88	        written_paths.append(init_path)
    89	
    90	
    91	def _ensure_package_chain(target_dir: Path, py_root: Path, written_paths: list[Path]) -> None:
    92	    """Ensure all parent Python packages from the root to target exist."""
    93	    current = py_root
    94	    for part in target_dir.relative_to(py_root).parts:
    95	        current = current / part
    96	        _ensure_package_init(current, written_paths)
    97	
    98	
    99	def _render_py_expr(*, expr: ExprIR) -> str:
   100	    """Render an expression into Python syntax."""
   101	    match expr:
   102	        case IntLiteralExprIR(value=value):
   103	            return str(value)
   104	        case ConstRefExprIR(name=name):
   105	            return name
   106	        case UnaryExprIR(op=op, operand=operand):
   107	            return f"({op}{_render_py_expr(expr=operand)})"
   108	        case BinaryExprIR(op=op, lhs=lhs, rhs=rhs):
   109	            return f"({_render_py_expr(expr=lhs)} {op} {_render_py_expr(expr=rhs)})"
   110	        case _:
   111	            raise ValueError(f"unsupported Python expression node {type(expr).__name__}")
   112	
   113	
   114	def _render_py_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
   115	    """Render a Python scalar wrapper class."""
   116	    class_name = _type_class_name(type_ir.name)
   117	    bc = byte_count(type_ir.resolved_width)
   118	    lines = [
   119	        f"class {class_name}:",
   120	        f"    WIDTH = {type_ir.resolved_width}",
   121	        f"    SIGNED = {type_ir.signed}",
   122	        f"    BYTE_COUNT = {bc}",
   123	    ]
   124	    if type_ir.resolved_width <= 64:
   125	        if type_ir.signed:
   126	            minimum = -(2 ** (type_ir.resolved_width - 1))
   127	            maximum = 2 ** (type_ir.resolved_width - 1) - 1
   128	            mask = (1 << type_ir.resolved_width) - 1
   129	            sign_bit = 1 << (type_ir.resolved_width - 1)
   130	            pad_bits = bc * 8 - type_ir.resolved_width
   131	            lines.extend(
   132	                [
   133	                    f"    MIN_VALUE = {minimum}",
   134	                    f"    MAX_VALUE = {maximum}",
   135	                    f"    MASK = {mask}",
   136	                    f"    SIGN_BIT = {sign_bit}",
   137	                    "",
   138	                    "    def __init__(self, value: int = 0) -> None:",
   139	                    '        if not isinstance(value, int):',
   140	                    f'            raise TypeError("{class_name} value must be int")',
   141	                    "        if value < self.MIN_VALUE or value > self.MAX_VALUE:",
   142	                    f'            raise ValueError("{class_name} value out of range")',
   143	                    "        self.value = value",
   144	                    "",
   145	                    "    def _to_packed_int(self) -> int:",
   146	                    "        return self.value & self.MASK",
   147	                    "",
   148	                    "    @classmethod",
   149	                    f'    def _from_packed_int(cls, packed: int) -> "{class_name}":',
   150	                    "        value = packed & cls.MASK",
   151	                    "        signed_value = value - (1 << cls.WIDTH) if (value & cls.SIGN_BIT) else value",
   152	                    "        return cls(signed_value)",
   153	                    "",
   154	                    "    def to_bytes(self) -> bytes:",
   155	                    "        mask = self.MASK",
   156	                    "        packed = self.value & mask",
   157	                    "        if self.value < 0:",
   158	                    f"            packed |= ((1 << (self.BYTE_COUNT * 8)) - 1) ^ mask",
   159	                    '        return packed.to_bytes(self.BYTE_COUNT, "big", signed=False)',
   160	                    "",
   161	                    "    @classmethod",
   162	                    f'    def from_bytes(cls, data: bytes | bytearray) -> "{class_name}":',
   163	                    '        if not isinstance(data, (bytes, bytearray)):',
   164	                    f'            raise TypeError("{class_name}.from_bytes expects bytes or bytearray")',
   165	                    "        raw = bytes(data)",
   166	                    "        if len(raw) != cls.BYTE_COUNT:",
   167	                    f'            raise ValueError("{class_name}.from_bytes size mismatch")',
   168	                    '        raw_int = int.from_bytes(raw, "big", signed=False)',
   169	                    "        data_bits = raw_int & cls.MASK",
   170	                    f"        padding = raw_int >> cls.WIDTH",
   171	                    "        sign_bit = (data_bits >> (cls.WIDTH - 1)) & 1",
   172	                    f"        expected_padding = ((1 << {pad_bits}) - 1) if sign_bit else 0",
   173	                    "        if padding != expected_padding:",
   174	                    f'            raise ValueError("{class_name}.from_bytes signed padding mismatch")',
   175	                    "        return cls._from_packed_int(data_bits)",
   176	                    "",
   177	                    f'    def clone(self) -> "{class_name}":',
   178	                    "        return type(self)(self.value)",
   179	                    "",
   180	                    "    def __int__(self) -> int:",
   181	                    "        return self.value",
   182	                    "",
   183	                    "    def __index__(self) -> int:",
   184	                    "        return self.value",
   185	                    "",
   186	                    "    def __eq__(self, other: object) -> bool:",
   187	                    "        if isinstance(other, type(self)):",
   188	                    "            return self.value == other.value",
   189	                    "        if isinstance(other, int):",
   190	                    "            return self.value == other",
   191	                    "        return NotImplemented",
   192	                    "",
   193	                    "    def __repr__(self) -> str:",
   194	                    f'        return f"{class_name}(value={{self.value!r}})"',
   195	                ]
   196	            )
   197	        else:
   198	            maximum = 2 ** type_ir.resolved_width - 1
   199	            lines.extend(
   200	                [
   201	                    "    MIN_VALUE = 0",
   202	                    f"    MAX_VALUE = {maximum}",
   203	                    "",
   204	                    "    def __init__(self, value: int = 0) -> None:",
   205	                    '        if not isinstance(value, int):',
   206	                    f'            raise TypeError("{class_name} value must be int")',
   207	                    "        if value < self.MIN_VALUE or value > self.MAX_VALUE:",
   208	                    f'            raise ValueError("{class_name} value out of range")',
   209	                    "        self.value = value",
   210	                    "",
   211	                    "    def _to_packed_int(self) -> int:",
   212	                    "        return self.value",
   213	                    "",
   214	                    "    @classmethod",
   215	                    f'    def _from_packed_int(cls, packed: int) -> "{class_name}":',
   216	                    "        return cls(packed)",
   217	                    "",
   218	                    "    def to_bytes(self) -> bytes:",
   219	                    '        return self.value.to_bytes(self.BYTE_COUNT, "big", signed=False)',
   220	                    "",

 succeeded in 0ms:
   220	                    "",
   221	                    "    @classmethod",
   222	                    f'    def from_bytes(cls, data: bytes | bytearray) -> "{class_name}":',
   223	                    '        if not isinstance(data, (bytes, bytearray)):',
   224	                    f'            raise TypeError("{class_name}.from_bytes expects bytes or bytearray")',
   225	                    "        raw = bytes(data)",
   226	                    "        if len(raw) != cls.BYTE_COUNT:",
   227	                    f'            raise ValueError("{class_name}.from_bytes size mismatch")',
   228	                    "        value = int.from_bytes(raw, \"big\", signed=False) & cls.MAX_VALUE",
   229	                    "        return cls(value)",
   230	                    "",
   231	                    f'    def clone(self) -> "{class_name}":',
   232	                    "        return type(self)(self.value)",
   233	                    "",
   234	                    "    def __int__(self) -> int:",
   235	                    "        return self.value",
   236	                    "",
   237	                    "    def __index__(self) -> int:",
   238	                    "        return self.value",
   239	                    "",
   240	                    "    def __eq__(self, other: object) -> bool:",
   241	                    "        if isinstance(other, type(self)):",
   242	                    "            return self.value == other.value",
   243	                    "        if isinstance(other, int):",
   244	                    "            return self.value == other",
   245	                    "        return NotImplemented",
   246	                    "",
   247	                    "    def __repr__(self) -> str:",
   248	                    f'        return f"{class_name}(value={{self.value!r}})"',
   249	                ]
   250	            )
   251	    else:
   252	        maximum = 2 ** type_ir.resolved_width - 1
   253	        mask_msb_byte = (1 << (type_ir.resolved_width % 8)) - 1 if type_ir.resolved_width % 8 else 0xFF
   254	        lines.extend(
   255	            [
   256	                f"    MAX_VALUE = {maximum}",
   257	                "",
   258	                "    def __init__(self, value: bytes | bytearray | int = b'') -> None:",
   259	                "        if isinstance(value, int):",
   260	                "            if value < 0 or value > self.MAX_VALUE:",
   261	                f'                raise ValueError("{class_name} value out of range")',
   262	                '            self.value = value.to_bytes(self.BYTE_COUNT, "big", signed=False)',
   263	                "            return",
   264	                '        if not isinstance(value, (bytes, bytearray)):',
   265	                f'            raise TypeError("{class_name} value must be bytes, bytearray, or int")',
   266	                "        raw = bytes(value)",
   267	                "        if len(raw) == 0:",
   268	                '            raw = b"\\x00" * self.BYTE_COUNT',
   269	                "        if len(raw) != self.BYTE_COUNT:",
   270	                f'            raise ValueError("{class_name} value size mismatch")',
   271	                "        self.value = raw",
   272	                "",
   273	                "    def _to_packed_int(self) -> int:",
   274	                '        return int.from_bytes(self.value, "big", signed=False)',
   275	                "",
   276	                "    @classmethod",
   277	                f'    def _from_packed_int(cls, packed: int) -> "{class_name}":',
   278	                '        return cls(packed.to_bytes(cls.BYTE_COUNT, "big", signed=False))',
   279	                "",
   280	                "    def to_bytes(self) -> bytes:",
   281	                "        return self.value",
   282	                "",
   283	                "    @classmethod",
   284	                f'    def from_bytes(cls, data: bytes | bytearray) -> "{class_name}":',
   285	                '        if not isinstance(data, (bytes, bytearray)):',
   286	                f'            raise TypeError("{class_name}.from_bytes expects bytes or bytearray")',
   287	                "        raw = bytes(data)",
   288	                "        if len(raw) != cls.BYTE_COUNT:",
   289	                f'            raise ValueError("{class_name}.from_bytes size mismatch")',
   290	                "        # Mask padding bits in MSB byte",
   291	                f"        masked = bytes([raw[0] & {mask_msb_byte}]) + raw[1:]",
   292	                "        return cls(masked)",
   293	                "",
   294	                f'    def clone(self) -> "{class_name}":',
   295	                "        return type(self)(self.value)",
   296	                "",
   297	                "    def __eq__(self, other: object) -> bool:",
   298	                "        if isinstance(other, type(self)):",
   299	                "            return self.value == other.value",
   300	                "        if isinstance(other, (bytes, bytearray)):",
   301	                "            return self.value == bytes(other)",
   302	                "        return NotImplemented",
   303	                "",
   304	                "    def __repr__(self) -> str:",
   305	                f'        return f"{class_name}(value={{self.value!r}})"',
   306	            ]
   307	        )
   308	    return lines
   309	
   310	
   311	def _render_py_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
   312	    """Render a Python struct wrapper class."""
   313	    class_name = _type_class_name(type_ir.name)
   314	    width = _resolved_type_width(type_ir=type_ir, type_index=type_index)
   315	    struct_byte_count = sum(
   316	        _field_byte_count(field_ir=f, type_index=type_index) for f in type_ir.fields
   317	    ) + type_ir.alignment_bits // 8
   318	    lines = [
   319	        "@dataclass",
   320	        f"class {class_name}:",
   321	        f"    WIDTH = {width}",
   322	        f"    BYTE_COUNT = {struct_byte_count}",
   323	    ]
   324	    for field_ir in type_ir.fields:
   325	        lines.append(f"    {field_ir.name}: {_render_py_field_annotation(field_ir=field_ir, type_index=type_index)} = {_render_py_field_default(field_ir=field_ir, type_index=type_index)}")
   326	    lines.append("")
   327	    lines.extend(
   328	        [
   329	            "    def __setattr__(self, name: str, value: object) -> None:",
   330	        ]
   331	    )
   332	    for index, field_ir in enumerate(type_ir.fields):
   333	        prefix = "if" if index == 0 else "elif"
   334	        lines.append(f'        {prefix} name == "{field_ir.name}":')
   335	        lines.append(f"            value = self._coerce_{field_ir.name}(value)")
   336	    lines.extend(
   337	        [
   338	            "        super().__setattr__(name, value)",
   339	            "",
   340	        ]
   341	    )
   342	    for field_ir in type_ir.fields:
   343	        lines.extend(_render_py_struct_field_coercer(owner_name=class_name, field_ir=field_ir, type_index=type_index))
   344	        lines.append("")
   345	    # to_bytes: per-field big-endian serialization
   346	    lines.extend(_render_py_struct_to_bytes(type_ir=type_ir, type_index=type_index))
   347	    lines.append("")
   348	    # from_bytes: per-field big-endian deserialization
   349	    lines.extend(_render_py_struct_from_bytes(type_ir=type_ir, class_name=class_name, type_index=type_index))
   350	    lines.append("")
   351	    lines.extend(
   352	        [
   353	            f'    def clone(self) -> "{class_name}":',
   354	            '        return type(self).from_bytes(self.to_bytes())',
   355	        ]
   356	    )
   357	    return lines
   358	
   359	
   360	def _render_py_struct_to_bytes(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
   361	    """Render the struct to_bytes method with per-field big-endian serialization."""
   362	    lines = [
   363	        "    def to_bytes(self) -> bytes:",
   364	        "        result = bytearray()",
   365	    ]
   366	    for field_ir in type_ir.fields:
   367	        fbc = _field_byte_count(field_ir=field_ir, type_index=type_index)
   368	        match field_ir.type_ir:
   369	            case TypeRefIR(name=name):
   370	                target = type_index[name]
   371	                if isinstance(target, StructIR):
   372	                    lines.extend(
   373	                        [
   374	                            f"        if self.{field_ir.name} is None:",
   375	                            f'            raise ValueError("{field_ir.name} cannot be None during packing")',
   376	                        ]
   377	                    )
   378	                lines.append(f"        result.extend(self.{field_ir.name}.to_bytes())")
   379	            case ScalarTypeSpecIR(signed=signed, resolved_width=resolved_width):
   380	                if resolved_width <= 64:
   381	                    fw = resolved_width
   382	                    mask = (1 << fw) - 1
   383	                    if signed:
   384	                        lines.extend(
   385	                            [
   386	                                f"        _mask_{field_ir.name} = {mask}",
   387	                                f"        _packed_{field_ir.name} = self.{field_ir.name} & _mask_{field_ir.name}",
   388	                                f"        if self.{field_ir.name} < 0:",
   389	                                f"            _packed_{field_ir.name} |= ((1 << {fbc * 8}) - 1) ^ _mask_{field_ir.name}",
   390	                                f'        result.extend(_packed_{field_ir.name}.to_bytes({fbc}, "big", signed=False))',
   391	                            ]
   392	                        )
   393	                    else:
   394	                        lines.extend(
   395	                            [
   396	                                f"        _packed_{field_ir.name} = self.{field_ir.name} & {mask}",
   397	                                f'        result.extend(_packed_{field_ir.name}.to_bytes({fbc}, "big", signed=False))',
   398	                            ]
   399	                        )
   400	                else:
   401	                    # Wide unsigned scalar stored as bytes, already big-endian
   402	                    lines.append(f"        result.extend(self.{field_ir.name})")
   403	            case _:
   404	                raise ValueError(f"unsupported Python struct field type {type(field_ir.type_ir).__name__}")
   405	    if type_ir.alignment_bits > 0:
   406	        align_bytes = type_ir.alignment_bits // 8
   407	        lines.append(f"        result.extend(b'\\x00' * {align_bytes})")
   408	    lines.append("        return bytes(result)")
   409	    return lines
   410	
   411	
   412	def _render_py_struct_from_bytes(*, type_ir: StructIR, class_name: str, type_index: dict[str, TypeDefIR]) -> list[str]:
   413	    """Render the struct from_bytes method with per-field big-endian deserialization."""
   414	    lines = [
   415	        "    @classmethod",
   416	        f'    def from_bytes(cls, data: bytes | bytearray) -> "{class_name}":',
   417	        '        if not isinstance(data, (bytes, bytearray)):',
   418	        f'            raise TypeError("{class_name}.from_bytes expects bytes or bytearray")',
   419	        "        raw = bytes(data)",
   420	        "        if len(raw) != cls.BYTE_COUNT:",
   421	        f'            raise ValueError("{class_name}.from_bytes size mismatch")',
   422	        "        obj = cls()",
   423	        "        offset = 0",
   424	    ]
   425	    for field_ir in type_ir.fields:
   426	        fbc = _field_byte_count(field_ir=field_ir, type_index=type_index)
   427	        match field_ir.type_ir:
   428	            case TypeRefIR(name=name):
   429	                target = type_index[name]
   430	                target_class = _type_class_name(target.name)
   431	                lines.extend(
   432	                    [
   433	                        f"        obj.{field_ir.name} = {target_class}.from_bytes(raw[offset:offset + {fbc}])",
   434	                        f"        offset += {fbc}",
   435	                    ]
   436	                )
   437	            case ScalarTypeSpecIR(signed=signed, resolved_width=resolved_width):
   438	                if resolved_width <= 64:
   439	                    fw = resolved_width
   440	                    mask = (1 << fw) - 1
   441	                    if signed:
   442	                        pad_bits = fbc * 8 - fw
   443	                        sign_bit_val = 1 << (fw - 1)
   444	                        lines.extend(
   445	                            [
   446	                                f"        _raw_int_{field_ir.name} = int.from_bytes(raw[offset:offset + {fbc}], \"big\", signed=False)",
   447	                                f"        _data_{field_ir.name} = _raw_int_{field_ir.name} & {mask}",
   448	                                f"        _padding_{field_ir.name} = _raw_int_{field_ir.name} >> {fw}",
   449	                                f"        _sign_bit_{field_ir.name} = (_data_{field_ir.name} >> {fw - 1}) & 1",
   450	                                f"        _expected_padding_{field_ir.name} = ((1 << {pad_bits}) - 1) if _sign_bit_{field_ir.name} else 0",
   451	                                f"        if _padding_{field_ir.name} != _expected_padding_{field_ir.name}:",
   452	                                f'            raise ValueError("{class_name}.from_bytes signed padding mismatch for {field_ir.name}")',
   453	                                f"        obj.{field_ir.name} = _data_{field_ir.name} - {1 << fw} if (_data_{field_ir.name} & {sign_bit_val}) else _data_{field_ir.name}",
   454	                                f"        offset += {fbc}",
   455	                            ]
   456	                        )
   457	                    else:
   458	                        lines.extend(
   459	                            [
   460	                                f"        obj.{field_ir.name} = int.from_bytes(raw[offset:offset + {fbc}], \"big\", signed=False) & {mask}",
   461	                                f"        offset += {fbc}",
   462	                            ]
   463	                        )
   464	                else:
   465	                    # Wide unsigned scalar stored as bytes
   466	                    mask_msb_byte = (1 << (resolved_width % 8)) - 1 if resolved_width % 8 else 0xFF
   467	                    lines.extend(
   468	                        [
   469	                            f"        _wide_raw_{field_ir.name} = raw[offset:offset + {fbc}]",
   470	                            f"        obj.{field_ir.name} = bytes([_wide_raw_{field_ir.name}[0] & {mask_msb_byte}]) + _wide_raw_{field_ir.name}[1:]",
   471	                            f"        offset += {fbc}",
   472	                        ]
   473	                    )
   474	            case _:
   475	                raise ValueError(f"unsupported Python struct field type {type(field_ir.type_ir).__name__}")
   476	    lines.append("        return obj")
   477	    return lines
   478	
   479	
   480	def _render_py_field_annotation(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
   481	    """Render one Python field annotation."""
   482	    match field_ir.type_ir:
   483	        case TypeRefIR(name=name):
   484	            target = type_index[name]
   485	            class_name = _type_class_name(target.name)
   486	            if isinstance(target, StructIR):
   487	                return f"{class_name} | None"
   488	            return class_name
   489	        case ScalarTypeSpecIR(resolved_width=resolved_width):
   490	            return "int" if resolved_width <= 64 else "bytes"
   491	        case _:
   492	            raise ValueError(f"unsupported Python struct field type {type(field_ir.type_ir).__name__}")
   493	
   494	
   495	def _render_py_field_default(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
   496	    """Render one Python field default."""
   497	    match field_ir.type_ir:
   498	        case TypeRefIR(name=name):
   499	            return f"field(default_factory={_type_class_name(type_index[name].name)})"
   500	        case ScalarTypeSpecIR(resolved_width=resolved_width):
   501	            if resolved_width <= 64:
   502	                return "0"
   503	            return f'b"\\x00" * {byte_count(resolved_width)}'
   504	        case _:
   505	            raise ValueError(f"unsupported Python struct field type {type(field_ir.type_ir).__name__}")
   506	
   507	
   508	def _render_py_struct_field_coercer(*, owner_name: str, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
   509	    """Render one Python field coercion helper."""
   510	    lines = ["    @staticmethod", f"    def _coerce_{field_ir.name}(value: object) -> {_render_py_field_annotation(field_ir=field_ir, type_index=type_index)}:"]
   511	    match field_ir.type_ir:
   512	        case TypeRefIR(name=name):
   513	            target = type_index[name]
   514	            class_name = _type_class_name(target.name)
   515	            if isinstance(target, StructIR):
   516	                lines.extend(
   517	                    [
   518	                        "        if value is None:",
   519	                        "            return None",
   520	                        f"        if isinstance(value, {class_name}):",
   521	                        "            return value",
   522	                        f'        raise TypeError("{owner_name}.{field_ir.name} must be {class_name} or None")',
   523	                    ]
   524	                )
   525	            elif isinstance(target, FlagsIR):
   526	                lines.extend(
   527	                    [
   528	                        f"        if isinstance(value, {class_name}):",
   529	                        "            return value",
   530	                        f'        raise TypeError("{owner_name}.{field_ir.name} must be {class_name}")',
   531	                    ]
   532	                )
   533	            elif isinstance(target, EnumIR):
   534	                lines.extend(
   535	                    [
   536	                        f"        if isinstance(value, {class_name}):",
   537	                        "            return value",
   538	                        f'        raise TypeError("{owner_name}.{field_ir.name} must be {class_name}")',
   539	                    ]
   540	                )
   541	            else:
   542	                lines.extend(
   543	                    [
   544	                        f"        if isinstance(value, {class_name}):",
   545	                        "            return value",
   546	                        f"        return {class_name}(value)",
   547	                    ]
   548	                )
   549	        case ScalarTypeSpecIR(signed=signed, resolved_width=resolved_width):
   550	            if resolved_width <= 64:
   551	                minimum = -(2 ** (resolved_width - 1)) if signed else 0
   552	                maximum = 2 ** (resolved_width - 1) - 1 if signed else 2 ** resolved_width - 1
   553	                lines.extend(
   554	                    [
   555	                        "        if not isinstance(value, int):",
   556	                        f'            raise TypeError("{owner_name}.{field_ir.name} must be int")',
   557	                        f"        if value < {minimum} or value > {maximum}:",
   558	                        f'            raise ValueError("{owner_name}.{field_ir.name} value out of range")',
   559	                        "        return value",
   560	                    ]

exec
/bin/zsh -lc "nl -ba src/piketype/backends/cpp/emitter.py | sed -n '1,240p'" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "nl -ba src/piketype/backends/sv/emitter.py | sed -n '1,240p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
     1	"""C++ backend — big-endian, byte-aligned padding."""
     2	
     3	from __future__ import annotations
     4	
     5	from pathlib import Path
     6	
     7	from piketype.backends.common.headers import render_header
     8	from piketype.errors import ValidationError
     9	from piketype.ir.nodes import (
    10	    BinaryExprIR,
    11	    ConstRefExprIR,
    12	    EnumIR,
    13	    ExprIR,
    14	    FieldTypeIR,
    15	    FlagFieldIR,
    16	    FlagsIR,
    17	    IntLiteralExprIR,
    18	    ModuleIR,
    19	    RepoIR,
    20	    ScalarAliasIR,
    21	    ScalarTypeSpecIR,
    22	    StructIR,
    23	    StructFieldIR,
    24	    TypeDefIR,
    25	    TypeRefIR,
    26	    UnaryExprIR,
    27	    byte_count,
    28	)
    29	from piketype.paths import cpp_header_output_path
    30	
    31	
    32	def emit_cpp(repo: RepoIR, *, namespace: str | None = None) -> list[Path]:
    33	    """Emit C++ outputs."""
    34	    written_paths: list[Path] = []
    35	    repo_root = Path(repo.repo_root)
    36	    for module in repo.modules:
    37	        output_path = cpp_header_output_path(
    38	            repo_root=repo_root,
    39	            module_path=repo_root / module.ref.repo_relative_path,
    40	        )
    41	        output_path.parent.mkdir(parents=True, exist_ok=True)
    42	        output_path.write_text(render_module_hpp(module, namespace=namespace), encoding="utf-8")
    43	        written_paths.append(output_path)
    44	    return written_paths
    45	
    46	
    47	def render_module_hpp(module: ModuleIR, *, namespace: str | None = None) -> str:
    48	    """Render a C++ header."""
    49	    header = render_header(source_paths=(module.ref.repo_relative_path,))
    50	    if namespace is not None:
    51	        guard = f"{namespace.replace('::', '_')}_{module.ref.basename}_types_hpp".upper()
    52	        ns = f"{namespace}::{module.ref.basename}"
    53	    else:
    54	        guard = "_".join((*module.ref.namespace_parts, "types_hpp")).upper().replace(".", "_")
    55	        ns = "::".join(part for part in module.ref.namespace_parts if part != "piketype")
    56	    type_index = {type_ir.name: type_ir for type_ir in module.types}
    57	    has_types = bool(module.types)
    58	    body_lines = [f"#ifndef {guard}", f"#define {guard}", "", "#include <cstdint>"]
    59	    if has_types:
    60	        body_lines.extend(["#include <cstddef>", "#include <stdexcept>", "#include <vector>"])
    61	    body_lines.append("")
    62	    if ns:
    63	        body_lines.append(f"namespace {ns} {{")
    64	        body_lines.append("")
    65	    for const in module.constants:
    66	        cpp_type, cpp_literal = _render_cpp_const(
    67	            value=const.resolved_value,
    68	            signed=const.resolved_signed,
    69	            width=const.resolved_width,
    70	        )
    71	        if isinstance(const.expr, IntLiteralExprIR):
    72	            cpp_expr = cpp_literal
    73	        else:
    74	            cpp_expr = _render_cpp_expr(expr=const.expr)
    75	        body_lines.append(f"constexpr {cpp_type} {const.name} = {cpp_expr};")
    76	    if module.constants and module.types:
    77	        body_lines.append("")
    78	    for index, type_ir in enumerate(module.types):
    79	        if index > 0:
    80	            body_lines.append("")
    81	        if isinstance(type_ir, ScalarAliasIR):
    82	            body_lines.extend(_render_cpp_scalar_alias(type_ir=type_ir))
    83	        elif isinstance(type_ir, StructIR):
    84	            body_lines.extend(_render_cpp_struct(type_ir=type_ir, type_index=type_index))
    85	        elif isinstance(type_ir, FlagsIR):
    86	            body_lines.extend(_render_cpp_flags(type_ir=type_ir))
    87	        elif isinstance(type_ir, EnumIR):
    88	            body_lines.extend(_render_cpp_enum(type_ir=type_ir))
    89	    if ns:
    90	        body_lines.append("")
    91	        body_lines.append(f"}}  // namespace {ns}")
    92	    body_lines.extend(["", f"#endif  // {guard}"])
    93	    return f"{header}\n" + "\n".join(body_lines) + "\n"
    94	
    95	
    96	def _render_cpp_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
    97	    """Choose a safe C++ constant type and literal spelling."""
    98	    if width == 32 and signed:
    99	        return ("std::int32_t", str(value))
   100	    if width == 32 and not signed:
   101	        return ("std::uint32_t", f"{value}U")
   102	    if width == 64 and signed:
   103	        return ("std::int64_t", f"{value}LL")
   104	    if width == 64 and not signed:
   105	        return ("std::uint64_t", f"{value}ULL")
   106	    raise ValidationError(f"unsupported C++ constant storage: signed={signed}, width={width}")
   107	
   108	
   109	def _render_cpp_expr(*, expr: ExprIR) -> str:
   110	    """Render an expression into C++ syntax."""
   111	    match expr:
   112	        case IntLiteralExprIR(value=value):
   113	            return str(value)
   114	        case ConstRefExprIR(name=name):
   115	            return name
   116	        case UnaryExprIR(op=op, operand=operand):
   117	            return f"({op}{_render_cpp_expr(expr=operand)})"
   118	        case BinaryExprIR(op=op, lhs=lhs, rhs=rhs):
   119	            return f"({_render_cpp_expr(expr=lhs)} {op} {_render_cpp_expr(expr=rhs)})"
   120	        case _:
   121	            raise ValidationError(f"unsupported C++ expression node {type(expr).__name__}")
   122	
   123	
   124	# ---------------------------------------------------------------------------
   125	# Scalar alias wrapper class
   126	# ---------------------------------------------------------------------------
   127	
   128	
   129	def _render_cpp_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
   130	    """Render a C++ scalar wrapper class (big-endian serialization)."""
   131	    class_name = _type_class_name(type_ir.name)
   132	    bc = byte_count(type_ir.resolved_width)
   133	    width = type_ir.resolved_width
   134	    lines = [
   135	        f"class {class_name} {{",
   136	        " public:",
   137	        f"  static constexpr std::size_t WIDTH = {width};",
   138	        f"  static constexpr bool SIGNED = {'true' if type_ir.signed else 'false'};",
   139	        f"  static constexpr std::size_t BYTE_COUNT = {bc};",
   140	    ]
   141	    if width <= 64:
   142	        value_type = _cpp_scalar_value_type(width=width, signed=type_ir.signed)
   143	        mask_literal = _cpp_unsigned_literal(
   144	            (1 << width) - 1 if width < 64 else 2**64 - 1
   145	        )
   146	        lines.extend(
   147	            [
   148	                f"  using value_type = {value_type};",
   149	                "  value_type value;",
   150	            ]
   151	        )
   152	        if type_ir.signed:
   153	            minimum = -(2 ** (width - 1))
   154	            maximum = 2 ** (width - 1) - 1
   155	            pad_bits = bc * 8 - width
   156	            lines.extend(
   157	                [
   158	                    f"  static constexpr value_type MIN_VALUE = static_cast<value_type>({minimum});",
   159	                    f"  static constexpr value_type MAX_VALUE = static_cast<value_type>({maximum});",
   160	                    f"  static constexpr std::uint64_t MASK = {mask_literal};",
   161	                    f"  {class_name}() : value(0) {{}}",
   162	                    f"  {class_name}(value_type value_in) : value(validate_value(value_in)) {{}}",
   163	                    "",
   164	                    "  std::vector<std::uint8_t> to_bytes() const {",
   165	                    "    std::vector<std::uint8_t> bytes(BYTE_COUNT, 0);",
   166	                    "    std::uint64_t bits = static_cast<std::uint64_t>(value) & MASK;",
   167	                ]
   168	            )
   169	            # Sign-extend into padding bits
   170	            if pad_bits > 0:
   171	                lines.extend(
   172	                    [
   173	                        f"    if (value < 0 && WIDTH < BYTE_COUNT * 8U) {{",
   174	                        f"      for (std::size_t i = WIDTH; i < BYTE_COUNT * 8U; ++i) {{",
   175	                        "        bits |= (1ULL << i);",
   176	                        "      }",
   177	                        "    }",
   178	                    ]
   179	                )
   180	            lines.extend(
   181	                [
   182	                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
   183	                    "      bytes[BYTE_COUNT - 1 - idx] = static_cast<std::uint8_t>((bits >> (8U * idx)) & 0xFFU);",
   184	                    "    }",
   185	                    "    return bytes;",
   186	                    "  }",
   187	                    "",
   188	                    "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
   189	                    "    if (bytes.size() != BYTE_COUNT) {",
   190	                    '      throw std::invalid_argument("byte width mismatch");',
   191	                    "    }",
   192	                    "    std::uint64_t bits = 0;",
   193	                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
   194	                    "      bits = (bits << 8U) | bytes[idx];",
   195	                    "    }",
   196	                ]
   197	            )
   198	            # Validate sign extension in padding bits
   199	            if pad_bits > 0:
   200	                byte_mask = _cpp_unsigned_literal((1 << (bc * 8)) - 1 if bc * 8 < 64 else 2**64 - 1)
   201	                lines.extend(
   202	                    [
   203	                        "    std::uint64_t data_bits = bits & MASK;",
   204	                        f"    bool sign_bit = ((data_bits >> ({width - 1}U)) & 1U) != 0U;",
   205	                        f"    std::uint64_t expected_pad = sign_bit ? (~MASK & {byte_mask}) : 0ULL;",
   206	                        f"    if ((bits & ~MASK & {byte_mask}) != expected_pad) {{",
   207	                        '      throw std::invalid_argument("signed padding mismatch");',
   208	                        "    }",
   209	                    ]
   210	                )
   211	            lines.extend(
   212	                [
   213	                    "    bits &= MASK;",
   214	                    "    std::int64_t signed_value = static_cast<std::int64_t>(bits);",
   215	                ]
   216	            )
   217	            if width < 64:
   218	                sign_bit_lit = _cpp_unsigned_literal(1 << (width - 1))
   219	                full_range_lit = _cpp_unsigned_literal(1 << width)
   220	                lines.extend(
   221	                    [
   222	                        f"    if ((bits & {sign_bit_lit}) != 0U && WIDTH < 64) {{",
   223	                        f"      signed_value -= static_cast<std::int64_t>({full_range_lit});",
   224	                        "    }",
   225	                    ]
   226	                )
   227	            lines.extend(
   228	                [
   229	                    "    value = validate_value(static_cast<value_type>(signed_value));",
   230	                    "  }",
   231	                    "",
   232	                    f"  {class_name} clone() const {{",
   233	                    f"    return {class_name}(value);",
   234	                    "  }",
   235	                    "",
   236	                    "  operator value_type() const {",
   237	                    "    return value;",
   238	                    "  }",
   239	                    "",
   240	                    f"  bool operator==(const {class_name}& other) const = default;",

 succeeded in 0ms:
     1	"""SystemVerilog backend."""
     2	
     3	from __future__ import annotations
     4	
     5	from pathlib import Path
     6	
     7	from piketype.backends.common.headers import render_header
     8	from piketype.ir.nodes import (
     9	    BinaryExprIR,
    10	    ConstRefExprIR,
    11	    EnumIR,
    12	    ExprIR,
    13	    FieldTypeIR,
    14	    FlagFieldIR,
    15	    FlagsIR,
    16	    IntLiteralExprIR,
    17	    ModuleIR,
    18	    RepoIR,
    19	    ScalarAliasIR,
    20	    ScalarTypeSpecIR,
    21	    StructFieldIR,
    22	    StructIR,
    23	    TypeDefIR,
    24	    TypeRefIR,
    25	    UnaryExprIR,
    26	    byte_count,
    27	)
    28	from piketype.paths import sv_module_output_path, sv_test_module_output_path
    29	
    30	
    31	# ---------------------------------------------------------------------------
    32	# Entry point
    33	# ---------------------------------------------------------------------------
    34	
    35	
    36	def emit_sv(repo: RepoIR) -> list[Path]:
    37	    """Emit SystemVerilog package files for all modules."""
    38	    written_paths: list[Path] = []
    39	    repo_root = Path(repo.repo_root)
    40	    for module in repo.modules:
    41	        synth_output_path = sv_module_output_path(
    42	            repo_root=repo_root,
    43	            module_path=repo_root / module.ref.repo_relative_path,
    44	        )
    45	        synth_output_path.parent.mkdir(parents=True, exist_ok=True)
    46	        synth_output_path.write_text(render_module_sv(module), encoding="utf-8")
    47	        written_paths.append(synth_output_path)
    48	        if module.types:
    49	            test_output_path = sv_test_module_output_path(
    50	                repo_root=repo_root,
    51	                module_path=repo_root / module.ref.repo_relative_path,
    52	            )
    53	            test_output_path.parent.mkdir(parents=True, exist_ok=True)
    54	            test_output_path.write_text(render_module_test_sv(module), encoding="utf-8")
    55	            written_paths.append(test_output_path)
    56	    return written_paths
    57	
    58	
    59	# ---------------------------------------------------------------------------
    60	# Synthesizable package
    61	# ---------------------------------------------------------------------------
    62	
    63	
    64	def render_module_sv(module: ModuleIR) -> str:
    65	    """Render a synthesizable SystemVerilog package."""
    66	    header = render_header(source_paths=(module.ref.repo_relative_path,))
    67	    type_index: dict[str, TypeDefIR] = {t.name: t for t in module.types}
    68	    body_lines = [f"package {module.ref.basename}_pkg;"]
    69	
    70	    const_lines: list[str] = []
    71	    for const in module.constants:
    72	        sv_type, sv_literal = _render_sv_const(
    73	            value=const.resolved_value,
    74	            signed=const.resolved_signed,
    75	            width=const.resolved_width,
    76	        )
    77	        sv_expr = sv_literal if isinstance(const.expr, IntLiteralExprIR) else _render_sv_expr(expr=const.expr)
    78	        const_lines.append(f"  localparam {sv_type} {const.name} = {sv_expr};")
    79	
    80	    type_blocks: list[list[str]] = []
    81	    for type_ir in module.types:
    82	        type_blocks.append(_render_sv_type_block(type_ir=type_ir, type_index=type_index))
    83	
    84	    if const_lines or type_blocks:
    85	        body_lines.append("")
    86	    if const_lines:
    87	        body_lines.extend(const_lines)
    88	    if const_lines and type_blocks:
    89	        body_lines.append("")
    90	    for index, type_block in enumerate(type_blocks):
    91	        if index > 0:
    92	            body_lines.append("")
    93	        body_lines.extend(type_block)
    94	    body_lines.append("endpackage")
    95	    return f"{header}\n" + "\n".join(body_lines) + "\n"
    96	
    97	
    98	def _render_sv_type_block(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
    99	    """Render localparams, typedef, and pack/unpack for one type."""
   100	    base = _type_base_name(type_ir.name)
   101	    upper_base = base.upper()
   102	
   103	    lines = [
   104	        f"  localparam int LP_{upper_base}_WIDTH = {_render_sv_width_value(type_ir=type_ir, type_index=type_index)};",
   105	        f"  localparam int LP_{upper_base}_BYTE_COUNT = {_type_byte_count(type_ir=type_ir, type_index=type_index)};",
   106	        "",
   107	    ]
   108	
   109	    if isinstance(type_ir, ScalarAliasIR):
   110	        lines.append(f"  {_render_sv_scalar_alias(type_ir=type_ir)}")
   111	    elif isinstance(type_ir, StructIR):
   112	        lines.extend(f"  {line}" for line in _render_sv_struct(type_ir=type_ir))
   113	    elif isinstance(type_ir, FlagsIR):
   114	        lines.extend(f"  {line}" for line in _render_sv_flags(type_ir=type_ir))
   115	    elif isinstance(type_ir, EnumIR):
   116	        lines.extend(f"  {line}" for line in _render_sv_enum(type_ir=type_ir))
   117	
   118	    lines.append("")
   119	    lines.extend(f"  {line}" for line in _render_sv_pack_fn(type_ir=type_ir, type_index=type_index))
   120	    lines.append("")
   121	    lines.extend(f"  {line}" for line in _render_sv_unpack_fn(type_ir=type_ir, type_index=type_index))
   122	
   123	    return lines
   124	
   125	
   126	def _render_sv_width_value(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> str:
   127	    """Render the width value for a localparam."""
   128	    if isinstance(type_ir, ScalarAliasIR):
   129	        return _render_sv_expr(expr=type_ir.width_expr)
   130	    if isinstance(type_ir, EnumIR):
   131	        return str(type_ir.resolved_width)
   132	    return str(_data_width(type_ir=type_ir, type_index=type_index))
   133	
   134	
   135	def _render_sv_scalar_alias(*, type_ir: ScalarAliasIR) -> str:
   136	    """Render a named scalar typedef using the LP_WIDTH localparam."""
   137	    base = _type_base_name(type_ir.name)
   138	    upper_base = base.upper()
   139	    base_type = type_ir.state_kind
   140	    signed_kw = " signed" if type_ir.signed else ""
   141	    if type_ir.resolved_width == 1:
   142	        return f"typedef {base_type}{signed_kw} {type_ir.name};"
   143	    return f"typedef {base_type}{signed_kw} [LP_{upper_base}_WIDTH-1:0] {type_ir.name};"
   144	
   145	
   146	def _render_sv_struct(*, type_ir: StructIR) -> list[str]:
   147	    """Render one packed struct typedef with per-member padding."""
   148	    lines = ["typedef struct packed {"]
   149	    for field in type_ir.fields:
   150	        pad = field.padding_bits
   151	        if pad > 0:
   152	            if pad == 1:
   153	                lines.append(f"  logic {field.name}_pad;")
   154	            else:
   155	                lines.append(f"  logic [{pad - 1}:0] {field.name}_pad;")
   156	        lines.append(f"  {_render_sv_struct_field_type(field_type=field.type_ir)} {field.name};")
   157	    if type_ir.alignment_bits > 0:
   158	        if type_ir.alignment_bits == 1:
   159	            lines.append("  logic _align_pad;")
   160	        else:
   161	            lines.append(f"  logic [{type_ir.alignment_bits - 1}:0] _align_pad;")
   162	    lines.append(f"}} {type_ir.name};")
   163	    return lines
   164	
   165	
   166	def _render_sv_struct_field_type(*, field_type: FieldTypeIR) -> str:
   167	    """Render one packed struct field type (without padding)."""
   168	    if isinstance(field_type, TypeRefIR):
   169	        return field_type.name
   170	    base_type = field_type.state_kind
   171	    signed_kw = " signed" if field_type.signed else ""
   172	    if field_type.resolved_width == 1:
   173	        return f"{base_type}{signed_kw}"
   174	    return f"{base_type}{signed_kw} [{field_type.resolved_width - 1}:0]"
   175	
   176	
   177	def _render_sv_flags(*, type_ir: FlagsIR) -> list[str]:
   178	    """Render one packed flags typedef."""
   179	    lines = ["typedef struct packed {"]
   180	    for flag in type_ir.fields:
   181	        lines.append(f"  logic {flag.name};")
   182	    if type_ir.alignment_bits > 0:
   183	        if type_ir.alignment_bits == 1:
   184	            lines.append("  logic _align_pad;")
   185	        else:
   186	            lines.append(f"  logic [{type_ir.alignment_bits - 1}:0] _align_pad;")
   187	    lines.append(f"}} {type_ir.name};")
   188	    return lines
   189	
   190	
   191	def _render_sv_enum(*, type_ir: EnumIR) -> list[str]:
   192	    """Render one enum typedef."""
   193	    base = _type_base_name(type_ir.name)
   194	    upper_base = base.upper()
   195	    members = ", ".join(f"{v.name} = {v.resolved_value}" for v in type_ir.values)
   196	    if type_ir.resolved_width == 1:
   197	        return [f"typedef enum logic {{{members}}} {type_ir.name};"]
   198	    return [f"typedef enum logic [LP_{upper_base}_WIDTH-1:0] {{{members}}} {type_ir.name};"]
   199	
   200	
   201	def _render_sv_pack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
   202	    """Render a pack_<base> function."""
   203	    base = _type_base_name(type_ir.name)
   204	    upper_base = base.upper()
   205	
   206	    if isinstance(type_ir, ScalarAliasIR):
   207	        return [
   208	            f"function automatic logic [LP_{upper_base}_WIDTH-1:0] pack_{base}({type_ir.name} a);",
   209	            "  return a;",
   210	            "endfunction",
   211	        ]
   212	
   213	    if isinstance(type_ir, FlagsIR):
   214	        parts = [f"a.{flag.name}" for flag in type_ir.fields]
   215	        concat = ", ".join(parts)
   216	        return [
   217	            f"function automatic logic [LP_{upper_base}_WIDTH-1:0] pack_{base}({type_ir.name} a);",
   218	            f"  return {{{concat}}};",
   219	            "endfunction",
   220	        ]
   221	
   222	    if isinstance(type_ir, EnumIR):
   223	        return [
   224	            f"function automatic logic [LP_{upper_base}_WIDTH-1:0] pack_{base}({type_ir.name} a);",
   225	            f"  return logic'(a);",
   226	            "endfunction",
   227	        ]
   228	
   229	    parts: list[str] = []
   230	    for field in type_ir.fields:
   231	        if isinstance(field.type_ir, TypeRefIR):
   232	            target = type_index[field.type_ir.name]
   233	            inner_base = _type_base_name(target.name)
   234	            parts.append(f"pack_{inner_base}(a.{field.name})")
   235	        else:
   236	            parts.append(f"a.{field.name}")
   237	    concat = ", ".join(parts)
   238	    return [
   239	        f"function automatic logic [LP_{upper_base}_WIDTH-1:0] pack_{base}({type_ir.name} a);",
   240	        f"  return {{{concat}}};",

exec
/bin/zsh -lc "nl -ba src/piketype/backends/py/emitter.py | sed -n '560,820p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
   560	                    ]
   561	                )
   562	            else:
   563	                fbc = byte_count(resolved_width)
   564	                lines.extend(
   565	                    [
   566	                        "        if isinstance(value, bytearray):",
   567	                        "            value = bytes(value)",
   568	                        "        if not isinstance(value, bytes):",
   569	                        f'            raise TypeError("{owner_name}.{field_ir.name} must be bytes")',
   570	                        f"        if len(value) != {fbc}:",
   571	                        f'            raise ValueError("{owner_name}.{field_ir.name} size mismatch")',
   572	                        "        return value",
   573	                    ]
   574	                )
   575	        case _:
   576	            raise ValueError(f"unsupported Python struct field type {type(field_ir.type_ir).__name__}")
   577	    return lines
   578	
   579	
   580	def _resolved_type_width(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
   581	    """Resolve the data width (in bits) of one type."""
   582	    if isinstance(type_ir, ScalarAliasIR):
   583	        return type_ir.resolved_width
   584	    if isinstance(type_ir, FlagsIR):
   585	        return len(type_ir.fields)
   586	    if isinstance(type_ir, EnumIR):
   587	        return type_ir.resolved_width
   588	    return sum(_resolved_field_width(field_type=field.type_ir, type_index=type_index) for field in type_ir.fields)
   589	
   590	
   591	def _resolved_field_width(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> int:
   592	    """Resolve the data width (in bits) of one field type."""
   593	    if isinstance(field_type, ScalarTypeSpecIR):
   594	        return field_type.resolved_width
   595	    return _resolved_type_width(type_ir=type_index[field_type.name], type_index=type_index)
   596	
   597	
   598	def _type_byte_count(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
   599	    """Resolve the byte-aligned byte count of one type (including alignment)."""
   600	    if isinstance(type_ir, ScalarAliasIR):
   601	        return byte_count(type_ir.resolved_width)
   602	    if isinstance(type_ir, FlagsIR):
   603	        return (len(type_ir.fields) + type_ir.alignment_bits) // 8
   604	    if isinstance(type_ir, EnumIR):
   605	        return byte_count(type_ir.resolved_width)
   606	    field_bytes = sum(_field_byte_count(field_ir=f, type_index=type_index) for f in type_ir.fields)
   607	    return field_bytes + type_ir.alignment_bits // 8
   608	
   609	
   610	def _field_byte_count(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> int:
   611	    """Resolve the byte-aligned byte count of one struct field."""
   612	    match field_ir.type_ir:
   613	        case ScalarTypeSpecIR(resolved_width=resolved_width):
   614	            return byte_count(resolved_width)
   615	        case TypeRefIR(name=name):
   616	            return _type_byte_count(type_ir=type_index[name], type_index=type_index)
   617	        case _:
   618	            raise ValueError(f"unsupported field type {type(field_ir.type_ir).__name__}")
   619	
   620	
   621	
   622	def _type_class_name(type_name: str) -> str:
   623	    """Convert a generated type name to its software wrapper class name."""
   624	    if type_name.endswith("_t"):
   625	        return f"{type_name[:-2]}_ct"
   626	    return f"{type_name}_ct"
   627	
   628	
   629	# ---------------------------------------------------------------------------
   630	# Enum IntEnum + wrapper class
   631	# ---------------------------------------------------------------------------
   632	
   633	
   634	def _render_py_enum(*, type_ir: EnumIR) -> list[str]:
   635	    """Render a Python IntEnum subclass and wrapper class for an enum type."""
   636	    base = type_ir.name[:-2] if type_ir.name.endswith("_t") else type_ir.name
   637	    enum_class_name = f"{base}_enum_t"
   638	    class_name = _type_class_name(type_ir.name)
   639	    bc = byte_count(type_ir.resolved_width)
   640	    width = type_ir.resolved_width
   641	    first_member = type_ir.values[0].name if type_ir.values else "0"
   642	    mask = (1 << width) - 1
   643	
   644	    lines: list[str] = []
   645	
   646	    # IntEnum subclass
   647	    lines.append(f"class {enum_class_name}(IntEnum):")
   648	    for v in type_ir.values:
   649	        lines.append(f"    {v.name} = {v.resolved_value}")
   650	    lines.append("")
   651	
   652	    # Wrapper class
   653	    lines.extend([
   654	        f"class {class_name}:",
   655	        f"    WIDTH = {width}",
   656	        f"    BYTE_COUNT = {bc}",
   657	        "",
   658	        f"    def __init__(self, value: {enum_class_name} = {enum_class_name}.{first_member}) -> None:",
   659	        f"        if not isinstance(value, {enum_class_name}):",
   660	        f'            raise TypeError("{class_name} value must be {enum_class_name}")',
   661	        "        self.value = value",
   662	        "",
   663	        "    def to_bytes(self) -> bytes:",
   664	        f'        return int(self.value).to_bytes({bc}, "big", signed=False)',
   665	        "",
   666	        "    @classmethod",
   667	        f'    def from_bytes(cls, data: bytes | bytearray) -> "{class_name}":',
   668	        "        if not isinstance(data, (bytes, bytearray)):",
   669	        f'            raise TypeError("{class_name}.from_bytes expects bytes or bytearray")',
   670	        "        raw = bytes(data)",
   671	        f"        if len(raw) != {bc}:",
   672	        f'            raise ValueError("{class_name}.from_bytes size mismatch")',
   673	        f'        raw_int = int.from_bytes(raw, "big", signed=False) & {mask}',
   674	        "        try:",
   675	        f"            enum_val = {enum_class_name}(raw_int)",
   676	        "        except ValueError:",
   677	        f'            raise ValueError("{class_name}.from_bytes unknown enum value")',
   678	        "        return cls(enum_val)",
   679	        "",
   680	        f'    def clone(self) -> "{class_name}":',
   681	        "        return type(self)(self.value)",
   682	        "",
   683	        "    def __int__(self) -> int:",
   684	        "        return int(self.value)",
   685	        "",
   686	        "    def __index__(self) -> int:",
   687	        "        return int(self.value)",
   688	        "",
   689	        "    def __eq__(self, other: object) -> bool:",
   690	        "        if isinstance(other, type(self)):",
   691	        "            return self.value == other.value",
   692	        "        if isinstance(other, int):",
   693	        "            return int(self.value) == other",
   694	        "        return NotImplemented",
   695	        "",
   696	        "    def __repr__(self) -> str:",
   697	        f'        return f"{class_name}(value={{self.value!r}})"',
   698	    ])
   699	    return lines
   700	
   701	
   702	# ---------------------------------------------------------------------------
   703	# Flags wrapper class
   704	# ---------------------------------------------------------------------------
   705	
   706	
   707	def _render_py_flags(*, type_ir: FlagsIR) -> list[str]:
   708	    """Render a Python flags wrapper class."""
   709	    class_name = _type_class_name(type_ir.name)
   710	    num_flags = len(type_ir.fields)
   711	    bc = byte_count(num_flags)
   712	    total_bits = bc * 8
   713	    # Data mask: top num_flags bits set, bottom alignment_bits clear
   714	    data_mask = ((1 << num_flags) - 1) << type_ir.alignment_bits
   715	
   716	    lines = [
   717	        f"class {class_name}:",
   718	        f"    WIDTH: int = {num_flags}",
   719	        f"    BYTE_COUNT: int = {bc}",
   720	        "",
   721	        "    def __init__(self) -> None:",
   722	        "        self._value: int = 0",
   723	        "",
   724	    ]
   725	
   726	    # Per-flag properties
   727	    for i, flag in enumerate(type_ir.fields):
   728	        mask = 1 << (total_bits - 1 - i)
   729	        lines.extend(
   730	            [
   731	                "    @property",
   732	                f"    def {flag.name}(self) -> bool:",
   733	                f"        return (self._value & {mask}) != 0",
   734	                "",
   735	                f"    @{flag.name}.setter",
   736	                f"    def {flag.name}(self, v: bool) -> None:",
   737	                f"        if v:",
   738	                f"            self._value |= {mask}",
   739	                f"        else:",
   740	                f"            self._value &= ~{mask}",
   741	                "",
   742	            ]
   743	        )
   744	
   745	    # to_bytes
   746	    lines.extend(
   747	        [
   748	            "    def to_bytes(self) -> bytes:",
   749	            f'        return (self._value & {data_mask}).to_bytes({bc}, "big")',
   750	            "",
   751	        ]
   752	    )
   753	
   754	    # from_bytes
   755	    lines.extend(
   756	        [
   757	            "    @classmethod",
   758	            f'    def from_bytes(cls, data: bytes | bytearray) -> "{class_name}":',
   759	            "        if not isinstance(data, (bytes, bytearray)):",
   760	            f'            raise TypeError("{class_name}.from_bytes expects bytes or bytearray")',
   761	            "        raw = bytes(data)",
   762	            f"        if len(raw) != {bc}:",
   763	            f'            raise ValueError("{class_name}.from_bytes size mismatch")',
   764	            "        obj = cls()",
   765	            f'        obj._value = int.from_bytes(raw, "big") & {data_mask}',
   766	            "        return obj",
   767	            "",
   768	        ]
   769	    )
   770	
   771	    # clone
   772	    lines.extend(
   773	        [
   774	            f'    def clone(self) -> "{class_name}":',
   775	            "        obj = self.__class__()",
   776	            f"        obj._value = self._value & {data_mask}",
   777	            "        return obj",
   778	            "",
   779	        ]
   780	    )
   781	
   782	    # __eq__
   783	    lines.extend(
   784	        [
   785	            "    def __eq__(self, other: object) -> bool:",
   786	            f"        if not isinstance(other, {class_name}):",
   787	            "            return NotImplemented",
   788	            f"        return (self._value & {data_mask}) == (other._value & {data_mask})",
   789	        ]
   790	    )
   791	
   792	    return lines

exec
/bin/zsh -lc "nl -ba src/piketype/backends/cpp/emitter.py | sed -n '900,1160p'" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "nl -ba src/piketype/backends/sv/emitter.py | sed -n '560,900p'" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "nl -ba src/piketype/backends/cpp/emitter.py | sed -n '560,900p'" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "nl -ba src/piketype/backends/cpp/emitter.py | sed -n '240,560p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
   900	                "",
   901	            ]
   902	        )
   903	
   904	    # --- validate ---
   905	    minimum = -(2 ** (width - 1)) if signed else 0
   906	    maximum = 2 ** (width - 1) - 1 if signed else (2**width - 1 if width < 64 else 2**64 - 1)
   907	    lines.append(f"  static {value_type} validate_{field_ir.name}({value_type} value_in) {{")
   908	    if signed:
   909	        lines.extend(
   910	            [
   911	                f"    constexpr {value_type} MIN_VALUE = static_cast<{value_type}>({minimum});",
   912	                f"    constexpr {value_type} MAX_VALUE = static_cast<{value_type}>({maximum});",
   913	                "    if (value_in < MIN_VALUE || value_in > MAX_VALUE) {",
   914	                '      throw std::out_of_range("value out of range");',
   915	                "    }",
   916	            ]
   917	        )
   918	    else:
   919	        lines.extend(
   920	            [
   921	                f"    constexpr {value_type} MAX_VALUE = static_cast<{value_type}>({_cpp_unsigned_literal(maximum)});",
   922	                "    if (value_in > MAX_VALUE) {",
   923	                '      throw std::out_of_range("value out of range");',
   924	                "    }",
   925	            ]
   926	        )
   927	    lines.extend(
   928	        [
   929	            "    return value_in;",
   930	            "  }",
   931	        ]
   932	    )
   933	    return lines
   934	
   935	
   936	def _render_wide_inline_helpers(
   937	    *, field_ir: StructFieldIR, width: int, bc: int, pad: int
   938	) -> list[str]:
   939	    """Encode/decode helpers for inline scalar > 64 bits (unsigned, vector<uint8_t>, big-endian)."""
   940	    msb_mask = _cpp_unsigned_literal((1 << (8 - pad)) - 1) if pad > 0 else "0xFFU"
   941	    lines = [
   942	        f"  static std::vector<std::uint8_t> encode_{field_ir.name}(const std::vector<std::uint8_t>& value_in) {{",
   943	        f"    if (value_in.size() != {bc}U) {{",
   944	        '      throw std::invalid_argument("byte width mismatch");',
   945	        "    }",
   946	        "    std::vector<std::uint8_t> normalized = value_in;",
   947	        f"    normalized[0] &= {msb_mask};",
   948	        "    return normalized;",
   949	        "  }",
   950	        "",
   951	        f"  static std::vector<std::uint8_t> decode_{field_ir.name}(const std::vector<std::uint8_t>& bytes, std::size_t offset) {{",
   952	        f"    std::vector<std::uint8_t> result(bytes.begin() + static_cast<std::ptrdiff_t>(offset),"
   953	        f" bytes.begin() + static_cast<std::ptrdiff_t>(offset + {bc}));",
   954	    ]
   955	    if pad > 0:
   956	        lines.append(f"    result[0] &= {msb_mask};")
   957	    lines.extend(
   958	        [
   959	            "    return result;",
   960	            "  }",
   961	        ]
   962	    )
   963	    return lines
   964	
   965	
   966	# ---------------------------------------------------------------------------
   967	# Width / byte-count resolution helpers
   968	# ---------------------------------------------------------------------------
   969	
   970	
   971	def _resolved_type_width(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
   972	    """Resolve the data width (sum of field data widths) of one type."""
   973	    if isinstance(type_ir, ScalarAliasIR):
   974	        return type_ir.resolved_width
   975	    if isinstance(type_ir, FlagsIR):
   976	        return len(type_ir.fields)
   977	    if isinstance(type_ir, EnumIR):
   978	        return type_ir.resolved_width
   979	    return sum(_resolved_field_width(field_type=field.type_ir, type_index=type_index) for field in type_ir.fields)
   980	
   981	
   982	def _resolved_field_width(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> int:
   983	    """Resolve the data width of one field type."""
   984	    if isinstance(field_type, ScalarTypeSpecIR):
   985	        return field_type.resolved_width
   986	    return _resolved_type_width(type_ir=type_index[field_type.name], type_index=type_index)
   987	
   988	
   989	def _type_byte_count(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
   990	    """Compute the byte-aligned byte count for a type (sum of per-field byte counts + alignment)."""
   991	    if isinstance(type_ir, ScalarAliasIR):
   992	        return byte_count(type_ir.resolved_width)
   993	    if isinstance(type_ir, FlagsIR):
   994	        return (len(type_ir.fields) + type_ir.alignment_bits) // 8
   995	    if isinstance(type_ir, EnumIR):
   996	        return byte_count(type_ir.resolved_width)
   997	    field_bytes = sum(_field_byte_count(field=field, type_index=type_index) for field in type_ir.fields)
   998	    return field_bytes + type_ir.alignment_bits // 8
   999	
  1000	
  1001	def _field_byte_count(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> int:
  1002	    """Compute the byte-aligned byte count for one field."""
  1003	    match field.type_ir:
  1004	        case ScalarTypeSpecIR(resolved_width=resolved_width):
  1005	            return byte_count(resolved_width)
  1006	        case TypeRefIR(name=name):
  1007	            target = type_index[name]
  1008	            if isinstance(target, ScalarAliasIR):
  1009	                return byte_count(target.resolved_width)
  1010	            return _type_byte_count(type_ir=target, type_index=type_index)
  1011	        case _:
  1012	            raise ValidationError(f"unsupported field type {type(field.type_ir).__name__}")
  1013	
  1014	
  1015	# ---------------------------------------------------------------------------
  1016	# Shared utilities
  1017	# ---------------------------------------------------------------------------
  1018	
  1019	
  1020	def _cpp_scalar_value_type(*, width: int, signed: bool) -> str:
  1021	    """Choose the public C++ storage type for a scalar width."""
  1022	    if width <= 8:
  1023	        return "std::int8_t" if signed else "std::uint8_t"
  1024	    if width <= 16:
  1025	        return "std::int16_t" if signed else "std::uint16_t"
  1026	    if width <= 32:
  1027	        return "std::int32_t" if signed else "std::uint32_t"
  1028	    return "std::int64_t" if signed else "std::uint64_t"
  1029	
  1030	
  1031	def _cpp_unsigned_literal(value: int) -> str:
  1032	    """Render an unsigned integer literal for C++."""
  1033	    if value <= 0xFFFFFFFF:
  1034	        return f"{value}U"
  1035	    return f"{value}ULL"
  1036	
  1037	
  1038	def _is_struct_ref(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> bool:
  1039	    """Return whether one field references a named struct."""
  1040	    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], StructIR)
  1041	
  1042	
  1043	def _is_scalar_ref(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> bool:
  1044	    """Return whether one field references a named scalar alias."""
  1045	    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], ScalarAliasIR)
  1046	
  1047	
  1048	def _is_flags_ref(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> bool:
  1049	    """Return whether one field references a named flags type."""
  1050	    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], FlagsIR)
  1051	
  1052	
  1053	def _is_enum_ref(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> bool:
  1054	    """Return whether one field references a named enum type."""
  1055	    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], EnumIR)
  1056	
  1057	
  1058	def _is_wide_inline_scalar(*, field_type: FieldTypeIR) -> bool:
  1059	    """Return whether one field is an inline scalar wider than 64 bits."""
  1060	    return isinstance(field_type, ScalarTypeSpecIR) and field_type.resolved_width > 64
  1061	
  1062	
  1063	def _type_class_name(type_name: str) -> str:
  1064	    """Convert a generated type name to its software wrapper class name."""
  1065	    if type_name.endswith("_t"):
  1066	        return f"{type_name[:-2]}_ct"
  1067	    return f"{type_name}_ct"

 succeeded in 0ms:
   560	    return lines
   561	
   562	
   563	def _render_sv_flags_helper_class(*, type_ir: FlagsIR) -> list[str]:
   564	    """Render a verification helper class for a flags type."""
   565	    class_name = _helper_class_name(type_ir.name)
   566	    base = _type_base_name(type_ir.name)
   567	    upper_base = base.upper()
   568	    num_flags = len(type_ir.fields)
   569	    bc = byte_count(num_flags)
   570	    total_bits = bc * 8
   571	
   572	    lines = [
   573	        f"class {class_name};",
   574	        f"  localparam int WIDTH = {num_flags};",
   575	        f"  localparam int BYTE_COUNT = {bc};",
   576	    ]
   577	    for flag in type_ir.fields:
   578	        lines.append(f"  rand logic {flag.name};")
   579	
   580	    # Constructor
   581	    lines.extend(["", "  function new();"])
   582	    for flag in type_ir.fields:
   583	        lines.append(f"    {flag.name} = '0;")
   584	    lines.append("  endfunction")
   585	
   586	    # to_slv
   587	    lines.extend(["", f"  function automatic {type_ir.name} to_slv();", f"    {type_ir.name} packed_value;"])
   588	    for flag in type_ir.fields:
   589	        lines.append(f"    packed_value.{flag.name} = {flag.name};")
   590	    if type_ir.alignment_bits > 0:
   591	        lines.append("    packed_value._align_pad = '0;")
   592	    lines.extend(["    return packed_value;", "  endfunction"])
   593	
   594	    # from_slv
   595	    lines.extend(["", f"  function void from_slv({type_ir.name} value_in);"])
   596	    for flag in type_ir.fields:
   597	        lines.append(f"    {flag.name} = value_in.{flag.name};")
   598	    lines.append("  endfunction")
   599	
   600	    # to_bytes
   601	    lines.extend([
   602	        "",
   603	        "  task automatic to_bytes(output byte unsigned bytes[]);",
   604	        f"    logic [{total_bits - 1}:0] bv;",
   605	        "    bytes = new[BYTE_COUNT];",
   606	        "    bv = '0;",
   607	    ])
   608	    # Pack flag bits into a bit vector (MSB = first flag, matching typedef layout)
   609	    for idx, flag in enumerate(type_ir.fields):
   610	        bit_pos = total_bits - 1 - idx
   611	        lines.append(f"    bv[{bit_pos}] = {flag.name};")
   612	    lines.extend([
   613	        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
   614	        "      bytes[idx] = bv[(BYTE_COUNT - 1 - idx)*8 +: 8];",
   615	        "    end",
   616	        "  endtask",
   617	    ])
   618	
   619	    # from_bytes
   620	    lines.extend([
   621	        "",
   622	        "  function void from_bytes(input byte unsigned bytes[]);",
   623	        f"    logic [{total_bits - 1}:0] bv;",
   624	        "    if (bytes.size() != BYTE_COUNT) begin",
   625	        f'      $fatal(1, "{class_name}.from_bytes size mismatch: expected %0d got %0d", BYTE_COUNT, bytes.size());',
   626	        "    end",
   627	        "    bv = '0;",
   628	        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
   629	        "      bv[(BYTE_COUNT - 1 - idx)*8 +: 8] = bytes[idx];",
   630	        "    end",
   631	    ])
   632	    for idx, flag in enumerate(type_ir.fields):
   633	        bit_pos = total_bits - 1 - idx
   634	        lines.append(f"    {flag.name} = bv[{bit_pos}];")
   635	    lines.append("  endfunction")
   636	
   637	    # copy
   638	    lines.extend(["", f"  function void copy(input {class_name} rhs);"])
   639	    for flag in type_ir.fields:
   640	        lines.append(f"    {flag.name} = rhs.{flag.name};")
   641	    lines.append("  endfunction")
   642	
   643	    # clone
   644	    lines.extend([
   645	        "",
   646	        f"  function automatic {class_name} clone();",
   647	        f"    {class_name} cloned = new();",
   648	        "    cloned.copy(this);",
   649	        "    return cloned;",
   650	        "  endfunction",
   651	    ])
   652	
   653	    # compare
   654	    lines.extend(["", f"  function automatic bit compare(input {class_name} rhs);", "    bit match;", "    match = 1'b1;"])
   655	    for flag in type_ir.fields:
   656	        lines.append(f"    match &= ({flag.name} === rhs.{flag.name});")
   657	    lines.extend(["    return match;", "  endfunction"])
   658	
   659	    # sprint
   660	    fmt_parts = [f"{flag.name}=%0b" for flag in type_ir.fields]
   661	    arg_parts = [flag.name for flag in type_ir.fields]
   662	    fmt = ", ".join(fmt_parts)
   663	    args = ", ".join(arg_parts)
   664	    lines.extend([
   665	        "",
   666	        "  function automatic string sprint();",
   667	        f'    return $sformatf("{class_name}({fmt})", {args});',
   668	        "  endfunction",
   669	        f"endclass : {class_name}",
   670	    ])
   671	    return lines
   672	
   673	
   674	def _render_sv_enum_helper_class(*, type_ir: EnumIR) -> list[str]:
   675	    """Render a verification helper class for an enum type."""
   676	    class_name = _helper_class_name(type_ir.name)
   677	    base = _type_base_name(type_ir.name)
   678	    upper_base = base.upper()
   679	    bc = byte_count(type_ir.resolved_width)
   680	    pad_bits = bc * 8 - type_ir.resolved_width
   681	    first_value = type_ir.values[0].name if type_ir.values else "0"
   682	
   683	    lines = [
   684	        f"class {class_name};",
   685	        f"  localparam int WIDTH = LP_{upper_base}_WIDTH;",
   686	        f"  localparam int BYTE_COUNT = LP_{upper_base}_BYTE_COUNT;",
   687	        f"  rand {type_ir.name} value;",
   688	        "",
   689	        f"  function new({type_ir.name} value_in = {first_value});",
   690	        "    value = value_in;",
   691	        "  endfunction",
   692	        "",
   693	        f"  function automatic {type_ir.name} to_slv();",
   694	        "    return value;",
   695	        "  endfunction",
   696	        "",
   697	        f"  function void from_slv({type_ir.name} value_in);",
   698	        "    value = value_in;",
   699	        "  endfunction",
   700	        "",
   701	    ]
   702	
   703	    # to_bytes: big-endian serialization
   704	    lines.extend([
   705	        "  task automatic to_bytes(output byte unsigned bytes[]);",
   706	        f"    logic [{bc * 8 - 1}:0] padded;",
   707	        "    bytes = new[BYTE_COUNT];",
   708	        "    padded = '0;",
   709	        f"    padded[WIDTH-1:0] = value;",
   710	        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
   711	        "      bytes[idx] = padded[(BYTE_COUNT - 1 - idx)*8 +: 8];",
   712	        "    end",
   713	        "  endtask",
   714	        "",
   715	    ])
   716	
   717	    # from_bytes: big-endian deserialization with padding mask
   718	    lines.extend([
   719	        "  function void from_bytes(input byte unsigned bytes[]);",
   720	        f"    logic [{bc * 8 - 1}:0] padded;",
   721	        "    if (bytes.size() != BYTE_COUNT) begin",
   722	        f'      $fatal(1, "{class_name}.from_bytes size mismatch: expected %0d got %0d", BYTE_COUNT, bytes.size());',
   723	        "    end",
   724	        "    padded = '0;",
   725	        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
   726	        "      padded[(BYTE_COUNT - 1 - idx)*8 +: 8] = bytes[idx];",
   727	        "    end",
   728	        f"    value = {type_ir.name}'(padded[WIDTH-1:0]);",
   729	        "  endfunction",
   730	        "",
   731	    ])
   732	
   733	    lines.extend([
   734	        f"  function void copy(input {class_name} rhs);",
   735	        "    value = rhs.value;",
   736	        "  endfunction",
   737	        "",
   738	        f"  function automatic {class_name} clone();",
   739	        f"    {class_name} cloned = new();",
   740	        "    cloned.value = value;",
   741	        "    return cloned;",
   742	        "  endfunction",
   743	        "",
   744	        f"  function automatic bit compare(input {class_name} rhs);",
   745	        "    return value === rhs.value;",
   746	        "  endfunction",
   747	        "",
   748	        "  function automatic string sprint();",
   749	        f'    return $sformatf("{class_name}(value=0x%0h)", value);',
   750	        "  endfunction",
   751	        f"endclass : {class_name}",
   752	    ])
   753	    return lines
   754	
   755	
   756	def _render_sv_helper_field_decl(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
   757	    """Render one struct helper field declaration."""
   758	    if isinstance(field.type_ir, TypeRefIR):
   759	        target = type_index[field.type_ir.name]
   760	        if isinstance(target, (StructIR, FlagsIR, EnumIR)):
   761	            return f"{_helper_class_name(target.name)} {field.name};"
   762	        rand_kw = "rand " if field.rand else ""
   763	        return f"{rand_kw}{target.name} {field.name};"
   764	    rand_kw = "rand " if field.rand else ""
   765	    return f"{rand_kw}{_render_sv_struct_field_type(field_type=field.type_ir)} {field.name};"
   766	
   767	
   768	def _render_sv_helper_to_bytes_step(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
   769	    """Render one to_bytes serialization step for a struct field."""
   770	    lines: list[str] = []
   771	    if _is_sv_composite_ref(field_type=field.type_ir, type_index=type_index):
   772	        fbc = _field_byte_count(field=field, type_index=type_index)
   773	        lines.extend([
   774	            "    begin",
   775	            "      byte unsigned field_bytes[];",
   776	            f"      {field.name}.to_bytes(field_bytes);",
   777	            f"      for (int i = 0; i < {fbc}; i++) bytes[byte_idx + i] = field_bytes[i];",
   778	            f"      byte_idx += {fbc};",
   779	            "    end",
   780	        ])
   781	    else:
   782	        fbc = _field_byte_count(field=field, type_index=type_index)
   783	        w = _field_data_width(field=field, type_index=type_index)
   784	        total_bits = fbc * 8
   785	        signed = _is_field_signed(field=field, type_index=type_index)
   786	        pad = field.padding_bits
   787	        lines.append("    begin")
   788	        lines.append(f"      logic [{total_bits - 1}:0] fb;")
   789	        lines.append("      fb = '0;")
   790	        lines.append(f"      fb[{w - 1}:0] = {field.name};")
   791	        if pad > 0 and signed:
   792	            lines.append(f"      for (int i = {w}; i < {total_bits}; i++) fb[i] = {field.name}[{w - 1}];")
   793	        lines.append(f"      for (int i = 0; i < {fbc}; i++) bytes[byte_idx + i] = fb[({fbc} - 1 - i)*8 +: 8];")
   794	        lines.append(f"      byte_idx += {fbc};")
   795	        lines.append("    end")
   796	    return lines
   797	
   798	
   799	def _render_sv_helper_from_bytes_step(
   800	    *,
   801	    field: StructFieldIR,
   802	    type_index: dict[str, TypeDefIR],
   803	    class_name: str,
   804	) -> list[str]:
   805	    """Render one from_bytes deserialization step for a struct field."""
   806	    lines: list[str] = []
   807	    if _is_sv_composite_ref(field_type=field.type_ir, type_index=type_index):
   808	        fbc = _field_byte_count(field=field, type_index=type_index)
   809	        lines.extend([
   810	            "    begin",
   811	            f"      byte unsigned field_bytes[] = new[{fbc}];",
   812	            f"      for (int i = 0; i < {fbc}; i++) field_bytes[i] = bytes[byte_idx + i];",
   813	            f"      {field.name}.from_bytes(field_bytes);",
   814	            f"      byte_idx += {fbc};",
   815	            "    end",
   816	        ])
   817	    else:
   818	        fbc = _field_byte_count(field=field, type_index=type_index)
   819	        w = _field_data_width(field=field, type_index=type_index)
   820	        total_bits = fbc * 8
   821	        signed = _is_field_signed(field=field, type_index=type_index)
   822	        pad = field.padding_bits
   823	        lines.append("    begin")
   824	        lines.append(f"      logic [{total_bits - 1}:0] fb;")
   825	        lines.append("      fb = '0;")
   826	        lines.append(f"      for (int i = 0; i < {fbc}; i++) fb[({fbc} - 1 - i)*8 +: 8] = bytes[byte_idx + i];")
   827	        if pad > 0 and signed:
   828	            lines.extend([
   829	                f"      for (int i = {w}; i < {total_bits}; i++) begin",
   830	                f"        if (fb[i] !== fb[{w - 1}]) begin",
   831	                f'          $fatal(1, "{class_name}.from_bytes signed padding mismatch for field {field.name}");',
   832	                "        end",
   833	                "      end",
   834	            ])
   835	        lines.append(f"      {field.name} = fb[{w - 1}:0];")
   836	        lines.append(f"      byte_idx += {fbc};")
   837	        lines.append("    end")
   838	    return lines
   839	
   840	
   841	# ---------------------------------------------------------------------------
   842	# Constant rendering (unchanged)
   843	# ---------------------------------------------------------------------------
   844	
   845	
   846	def _render_sv_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
   847	    """Choose a safe SystemVerilog constant type and literal spelling."""
   848	    if width == 32 and signed:
   849	        return ("int", _sv_signed_literal(width=32, value=value))
   850	    if width == 32 and not signed:
   851	        return ("int unsigned", f"32'd{value}")
   852	    if width == 64 and signed:
   853	        return ("longint", _sv_signed_literal(width=64, value=value))
   854	    if width == 64 and not signed:
   855	        return ("longint unsigned", f"64'd{value}")
   856	    raise ValueError(f"unsupported SystemVerilog constant storage: signed={signed}, width={width}")
   857	
   858	
   859	def _sv_signed_literal(*, width: int, value: int) -> str:
   860	    """Render a signed decimal SystemVerilog literal."""
   861	    if value < 0:
   862	        return f"-{width}'sd{abs(value)}"
   863	    return f"{width}'sd{value}"
   864	
   865	
   866	def _render_sv_expr(*, expr: ExprIR) -> str:
   867	    """Render an expression into SystemVerilog syntax."""
   868	    match expr:
   869	        case IntLiteralExprIR(value=value):
   870	            return str(value)
   871	        case ConstRefExprIR(name=name):
   872	            return name
   873	        case UnaryExprIR(op=op, operand=operand):
   874	            return f"({op}{_render_sv_expr(expr=operand)})"
   875	        case BinaryExprIR(op=op, lhs=lhs, rhs=rhs):
   876	            return f"({_render_sv_expr(expr=lhs)} {op} {_render_sv_expr(expr=rhs)})"
   877	        case _:
   878	            raise ValueError(f"unsupported SV expression node {type(expr).__name__}")
   879	
   880	
   881	# ---------------------------------------------------------------------------
   882	# Width / byte-count resolution helpers
   883	# ---------------------------------------------------------------------------
   884	
   885	
   886	def _type_base_name(name: str) -> str:
   887	    """Strip trailing _t from a type name."""
   888	    return name[:-2] if name.endswith("_t") else name
   889	
   890	
   891	def _data_width(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
   892	    """Total data width (excluding padding) of a type."""
   893	    if isinstance(type_ir, ScalarAliasIR):
   894	        return type_ir.resolved_width
   895	    if isinstance(type_ir, FlagsIR):
   896	        return len(type_ir.fields)
   897	    if isinstance(type_ir, EnumIR):
   898	        return type_ir.resolved_width
   899	    return sum(_field_data_width(field=f, type_index=type_index) for f in type_ir.fields)
   900	

 succeeded in 0ms:
   560	    lines.extend(
   561	        [
   562	            "",
   563	            f"  {class_name}() = default;",
   564	            "",
   565	            "  std::vector<std::uint8_t> to_bytes() const {",
   566	            "    std::vector<std::uint8_t> bytes;",
   567	            "    bytes.reserve(BYTE_COUNT);",
   568	        ]
   569	    )
   570	    for field_ir in type_ir.fields:
   571	        lines.extend(_render_cpp_struct_pack_step(field_ir=field_ir, type_index=type_index))
   572	    if type_ir.alignment_bits > 0:
   573	        align_bytes = type_ir.alignment_bits // 8
   574	        lines.append(f"    for (std::size_t i = 0; i < {align_bytes}; ++i) bytes.push_back(0);")
   575	    lines.extend(
   576	        [
   577	            "    return bytes;",
   578	            "  }",
   579	            "",
   580	            "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
   581	            "    if (bytes.size() != BYTE_COUNT) {",
   582	            '      throw std::invalid_argument("byte width mismatch");',
   583	            "    }",
   584	            "    std::size_t offset = 0;",
   585	        ]
   586	    )
   587	    for field_ir in type_ir.fields:
   588	        lines.extend(_render_cpp_struct_unpack_step(field_ir=field_ir, type_index=type_index))
   589	    lines.extend(
   590	        [
   591	            "  }",
   592	            "",
   593	            f"  {class_name} clone() const {{",
   594	            f"    {class_name} cloned;",
   595	        ]
   596	    )
   597	    for field_ir in type_ir.fields:
   598	        if _is_struct_ref(field_type=field_ir.type_ir, type_index=type_index) or _is_scalar_ref(
   599	            field_type=field_ir.type_ir, type_index=type_index
   600	        ) or _is_flags_ref(field_type=field_ir.type_ir, type_index=type_index) or _is_enum_ref(
   601	            field_type=field_ir.type_ir, type_index=type_index
   602	        ):
   603	            lines.append(f"    cloned.{field_ir.name} = {field_ir.name}.clone();")
   604	        elif _is_wide_inline_scalar(field_type=field_ir.type_ir):
   605	            lines.append(f"    cloned.{field_ir.name} = {field_ir.name};")
   606	        else:
   607	            lines.append(f"    cloned.{field_ir.name} = {field_ir.name};")
   608	    lines.extend(
   609	        [
   610	            "    return cloned;",
   611	            "  }",
   612	            "",
   613	            f"  bool operator==(const {class_name}& other) const = default;",
   614	        ]
   615	    )
   616	    # Per-field encode/decode helpers
   617	    all_helpers: list[str] = []
   618	    for field_ir in type_ir.fields:
   619	        helper_lines = _render_cpp_inline_scalar_helpers(owner_name=class_name, field_ir=field_ir)
   620	        if helper_lines:
   621	            if all_helpers:
   622	                all_helpers.append("")
   623	            all_helpers.extend(helper_lines)
   624	    if all_helpers:
   625	        lines.append("")
   626	        lines.append(" private:")
   627	        lines.extend(all_helpers)
   628	    lines.append("};")
   629	    return lines
   630	
   631	
   632	# ---------------------------------------------------------------------------
   633	# Field declarations
   634	# ---------------------------------------------------------------------------
   635	
   636	
   637	def _render_cpp_field_decl(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
   638	    """Render one public C++ field declaration."""
   639	    type_name = _render_cpp_field_type(field_ir=field_ir, type_index=type_index)
   640	    default = _render_cpp_field_default(field_ir=field_ir, type_index=type_index)
   641	    return f"{type_name} {field_ir.name}{default};"
   642	
   643	
   644	def _render_cpp_field_type(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
   645	    """Render one C++ field type."""
   646	    match field_ir.type_ir:
   647	        case TypeRefIR(name=name):
   648	            return _type_class_name(type_index[name].name)
   649	        case ScalarTypeSpecIR(signed=signed, resolved_width=resolved_width):
   650	            if resolved_width <= 64:
   651	                return _cpp_scalar_value_type(width=resolved_width, signed=signed)
   652	            return "std::vector<std::uint8_t>"
   653	        case _:
   654	            raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
   655	
   656	
   657	def _render_cpp_field_default(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
   658	    """Render one C++ field default initializer."""
   659	    match field_ir.type_ir:
   660	        case TypeRefIR():
   661	            return "{}"
   662	        case ScalarTypeSpecIR(resolved_width=resolved_width):
   663	            if resolved_width <= 64:
   664	                return " = 0"
   665	            bc = byte_count(resolved_width)
   666	            return f"{{std::vector<std::uint8_t>({bc}, 0U)}}"
   667	        case _:
   668	            raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
   669	
   670	
   671	# ---------------------------------------------------------------------------
   672	# Struct to_bytes — per-field big-endian serialization
   673	# ---------------------------------------------------------------------------
   674	
   675	
   676	def _render_cpp_struct_pack_step(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
   677	    """Render one C++ struct packing step (big-endian, per-field byte-aligned)."""
   678	    lines: list[str] = []
   679	    if isinstance(field_ir.type_ir, ScalarTypeSpecIR) and field_ir.type_ir.resolved_width <= 64:
   680	        # Inline scalar ≤64 — use encode helper
   681	        lines.extend(
   682	            [
   683	                "    {",
   684	                f"      auto field_bytes = encode_{field_ir.name}({field_ir.name});",
   685	                "      bytes.insert(bytes.end(), field_bytes.begin(), field_bytes.end());",
   686	                "    }",
   687	            ]
   688	        )
   689	    elif isinstance(field_ir.type_ir, ScalarTypeSpecIR):
   690	        # Wide inline scalar >64 — vector IS big-endian bytes, but need to normalize MSB padding
   691	        bc = byte_count(field_ir.type_ir.resolved_width)
   692	        pad = bc * 8 - field_ir.type_ir.resolved_width
   693	        lines.extend(
   694	            [
   695	                "    {",
   696	                f"      auto field_bytes = encode_{field_ir.name}({field_ir.name});",
   697	                "      bytes.insert(bytes.end(), field_bytes.begin(), field_bytes.end());",
   698	                "    }",
   699	            ]
   700	        )
   701	    elif isinstance(field_ir.type_ir, TypeRefIR):
   702	        target = type_index[field_ir.type_ir.name]
   703	        if isinstance(target, (StructIR, ScalarAliasIR, FlagsIR, EnumIR)):
   704	            lines.extend(
   705	                [
   706	                    "    {",
   707	                    f"      auto field_bytes = {field_ir.name}.to_bytes();",
   708	                    "      bytes.insert(bytes.end(), field_bytes.begin(), field_bytes.end());",
   709	                    "    }",
   710	                ]
   711	            )
   712	        else:
   713	            raise ValidationError(f"unsupported type ref target {type(target).__name__}")
   714	    else:
   715	        raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
   716	    return lines
   717	
   718	
   719	# ---------------------------------------------------------------------------
   720	# Struct from_bytes — per-field big-endian deserialization
   721	# ---------------------------------------------------------------------------
   722	
   723	
   724	def _render_cpp_struct_unpack_step(
   725	    *, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]
   726	) -> list[str]:
   727	    """Render one C++ struct unpacking step (big-endian, per-field byte-aligned)."""
   728	    fbc = _field_byte_count(field=field_ir, type_index=type_index)
   729	    lines: list[str] = []
   730	    if isinstance(field_ir.type_ir, ScalarTypeSpecIR) and field_ir.type_ir.resolved_width <= 64:
   731	        lines.extend(
   732	            [
   733	                f"    {field_ir.name} = decode_{field_ir.name}(bytes, offset);",
   734	                f"    offset += {fbc};",
   735	            ]
   736	        )
   737	    elif isinstance(field_ir.type_ir, ScalarTypeSpecIR):
   738	        # Wide inline scalar
   739	        lines.extend(
   740	            [
   741	                f"    {field_ir.name} = decode_{field_ir.name}(bytes, offset);",
   742	                f"    offset += {fbc};",
   743	            ]
   744	        )
   745	    elif isinstance(field_ir.type_ir, TypeRefIR):
   746	        target = type_index[field_ir.type_ir.name]
   747	        if isinstance(target, (StructIR, ScalarAliasIR, FlagsIR, EnumIR)):
   748	            lines.extend(
   749	                [
   750	                    "    {",
   751	                    f"      std::vector<std::uint8_t> field_bytes(bytes.begin() + static_cast<std::ptrdiff_t>(offset),"
   752	                    f" bytes.begin() + static_cast<std::ptrdiff_t>(offset + {fbc}));",
   753	                    f"      {field_ir.name}.from_bytes(field_bytes);",
   754	                    f"      offset += {fbc};",
   755	                    "    }",
   756	                ]
   757	            )
   758	        else:
   759	            raise ValidationError(f"unsupported type ref target {type(target).__name__}")
   760	    else:
   761	        raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
   762	    return lines
   763	
   764	
   765	# ---------------------------------------------------------------------------
   766	# Inline scalar encode/decode helpers (private section of struct class)
   767	# ---------------------------------------------------------------------------
   768	
   769	
   770	def _render_cpp_inline_scalar_helpers(*, owner_name: str, field_ir: StructFieldIR) -> list[str]:
   771	    """Render private helper functions for one inline scalar field (big-endian)."""
   772	    if not isinstance(field_ir.type_ir, ScalarTypeSpecIR):
   773	        return []
   774	    width = field_ir.type_ir.resolved_width
   775	    bc = byte_count(width)
   776	    pad = bc * 8 - width
   777	    if width <= 64:
   778	        return _render_narrow_inline_helpers(field_ir=field_ir, width=width, bc=bc, pad=pad)
   779	    return _render_wide_inline_helpers(field_ir=field_ir, width=width, bc=bc, pad=pad)
   780	
   781	
   782	def _render_narrow_inline_helpers(
   783	    *, field_ir: StructFieldIR, width: int, bc: int, pad: int
   784	) -> list[str]:
   785	    """Encode/decode helpers for inline scalar ≤64 bits."""
   786	    assert isinstance(field_ir.type_ir, ScalarTypeSpecIR)
   787	    signed = field_ir.type_ir.signed
   788	    value_type = _cpp_scalar_value_type(width=width, signed=signed)
   789	    mask = (1 << width) - 1 if width < 64 else 2**64 - 1
   790	    mask_lit = _cpp_unsigned_literal(mask)
   791	    lines: list[str] = []
   792	
   793	    if signed:
   794	        # --- encode (signed) ---
   795	        lines.extend(
   796	            [
   797	                f"  static std::vector<std::uint8_t> encode_{field_ir.name}({value_type} v) {{",
   798	                f"    validate_{field_ir.name}(v);",
   799	                f"    constexpr std::uint64_t MASK = {mask_lit};",
   800	                "    std::uint64_t bits = static_cast<std::uint64_t>(v) & MASK;",
   801	            ]
   802	        )
   803	        if pad > 0:
   804	            lines.extend(
   805	                [
   806	                    "    if (v < 0) {",
   807	                    "      bits |= ~MASK;",
   808	                    "    }",
   809	                ]
   810	            )
   811	        lines.extend(
   812	            [
   813	                f"    std::vector<std::uint8_t> b({bc}, 0U);",
   814	                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
   815	                f"      b[{bc} - 1 - i] = static_cast<std::uint8_t>((bits >> (8U * i)) & 0xFFU);",
   816	                "    }",
   817	                "    return b;",
   818	                "  }",
   819	                "",
   820	            ]
   821	        )
   822	        # --- decode (signed) ---
   823	        lines.extend(
   824	            [
   825	                f"  static {value_type} decode_{field_ir.name}(const std::vector<std::uint8_t>& bytes, std::size_t offset) {{",
   826	                "    std::uint64_t bits = 0;",
   827	                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
   828	                "      bits = (bits << 8U) | bytes[offset + i];",
   829	                "    }",
   830	            ]
   831	        )
   832	        if pad > 0:
   833	            byte_total_mask = (1 << (bc * 8)) - 1 if bc * 8 < 64 else 2**64 - 1
   834	            byte_total_mask_lit = _cpp_unsigned_literal(byte_total_mask)
   835	            lines.extend(
   836	                [
   837	                    f"    constexpr std::uint64_t MASK = {mask_lit};",
   838	                    "    std::uint64_t data_bits = bits & MASK;",
   839	                    f"    bool sign_bit = ((data_bits >> ({width - 1}U)) & 1U) != 0U;",
   840	                    f"    std::uint64_t expected_pad = sign_bit ? (~MASK & {byte_total_mask_lit}) : 0ULL;",
   841	                    f"    if ((bits & ~MASK & {byte_total_mask_lit}) != expected_pad) {{",
   842	                    '      throw std::invalid_argument("signed padding mismatch");',
   843	                    "    }",
   844	                    "    bits = data_bits;",
   845	                ]
   846	            )
   847	        else:
   848	            lines.append(f"    constexpr std::uint64_t MASK = {mask_lit};")
   849	            lines.append("    bits &= MASK;")
   850	        lines.append("    std::int64_t signed_value = static_cast<std::int64_t>(bits);")
   851	        if width < 64:
   852	            sign_bit_lit = _cpp_unsigned_literal(1 << (width - 1))
   853	            full_range_lit = _cpp_unsigned_literal(1 << width)
   854	            lines.extend(
   855	                [
   856	                    f"    if ((bits & {sign_bit_lit}) != 0U) {{",
   857	                    f"      signed_value -= static_cast<std::int64_t>({full_range_lit});",
   858	                    "    }",
   859	                ]
   860	            )
   861	        lines.extend(
   862	            [
   863	                f"    return validate_{field_ir.name}(static_cast<{value_type}>(signed_value));",
   864	                "  }",
   865	                "",
   866	            ]
   867	        )
   868	    else:
   869	        # --- encode (unsigned) ---
   870	        lines.extend(
   871	            [
   872	                f"  static std::vector<std::uint8_t> encode_{field_ir.name}({value_type} v) {{",
   873	                f"    validate_{field_ir.name}(v);",
   874	                f"    std::vector<std::uint8_t> b({bc}, 0U);",
   875	                "    std::uint64_t bits = static_cast<std::uint64_t>(v);",
   876	                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
   877	                f"      b[{bc} - 1 - i] = static_cast<std::uint8_t>((bits >> (8U * i)) & 0xFFU);",
   878	                "    }",
   879	                "    return b;",
   880	                "  }",
   881	                "",
   882	            ]
   883	        )
   884	        # --- decode (unsigned) ---
   885	        lines.extend(
   886	            [
   887	                f"  static {value_type} decode_{field_ir.name}(const std::vector<std::uint8_t>& bytes, std::size_t offset) {{",
   888	                "    std::uint64_t bits = 0;",
   889	                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
   890	                "      bits = (bits << 8U) | bytes[offset + i];",
   891	                "    }",
   892	            ]
   893	        )
   894	        if pad > 0:
   895	            lines.append(f"    bits &= {mask_lit};")
   896	        lines.extend(
   897	            [
   898	                f"    return validate_{field_ir.name}(static_cast<{value_type}>(bits));",
   899	                "  }",
   900	                "",

 succeeded in 0ms:
   240	                    f"  bool operator==(const {class_name}& other) const = default;",
   241	                    "",
   242	                    " private:",
   243	                    "  static value_type validate_value(value_type value_in) {",
   244	                    "    if (value_in < MIN_VALUE || value_in > MAX_VALUE) {",
   245	                    '      throw std::out_of_range("value out of range");',
   246	                    "    }",
   247	                    "    return value_in;",
   248	                    "  }",
   249	                    "};",
   250	                ]
   251	            )
   252	        else:
   253	            # Unsigned <= 64
   254	            maximum = 2**width - 1 if width < 64 else 2**64 - 1
   255	            lines.extend(
   256	                [
   257	                    f"  static constexpr std::uint64_t MASK = {mask_literal};",
   258	                    f"  static constexpr value_type MAX_VALUE = static_cast<value_type>({_cpp_unsigned_literal(maximum)});",
   259	                    f"  {class_name}() : value(0) {{}}",
   260	                    f"  {class_name}(value_type value_in) : value(validate_value(value_in)) {{}}",
   261	                    "",
   262	                    "  std::vector<std::uint8_t> to_bytes() const {",
   263	                    "    std::vector<std::uint8_t> bytes(BYTE_COUNT, 0);",
   264	                    "    std::uint64_t bits = static_cast<std::uint64_t>(value);",
   265	                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
   266	                    "      bytes[BYTE_COUNT - 1 - idx] = static_cast<std::uint8_t>((bits >> (8U * idx)) & 0xFFU);",
   267	                    "    }",
   268	                    "    return bytes;",
   269	                    "  }",
   270	                    "",
   271	                    "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
   272	                    "    if (bytes.size() != BYTE_COUNT) {",
   273	                    '      throw std::invalid_argument("byte width mismatch");',
   274	                    "    }",
   275	                    "    std::uint64_t bits = 0;",
   276	                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
   277	                    "      bits = (bits << 8U) | bytes[idx];",
   278	                    "    }",
   279	                    "    value = validate_value(static_cast<value_type>(bits & MASK));",
   280	                    "  }",
   281	                    "",
   282	                    f"  {class_name} clone() const {{",
   283	                    f"    return {class_name}(value);",
   284	                    "  }",
   285	                    "",
   286	                    "  operator value_type() const {",
   287	                    "    return value;",
   288	                    "  }",
   289	                    "",
   290	                    f"  bool operator==(const {class_name}& other) const = default;",
   291	                    "",
   292	                    " private:",
   293	                    "  static value_type validate_value(value_type value_in) {",
   294	                    "    if (value_in > MAX_VALUE) {",
   295	                    '      throw std::out_of_range("value out of range");',
   296	                    "    }",
   297	                    "    return value_in;",
   298	                    "  }",
   299	                    "};",
   300	                ]
   301	            )
   302	    else:
   303	        # Wide unsigned > 64 — vector<uint8_t> in big-endian order
   304	        pad = bc * 8 - width
   305	        msb_mask = _cpp_unsigned_literal((1 << (8 - pad)) - 1) if pad > 0 else "0xFFU"
   306	        lines.extend(
   307	            [
   308	                "  using value_type = std::vector<std::uint8_t>;",
   309	                "  value_type value;",
   310	                f"  {class_name}() : value(BYTE_COUNT, 0U) {{}}",
   311	                f"  {class_name}(const value_type& value_in) : value(validate_value(value_in)) {{}}",
   312	                "",
   313	                "  std::vector<std::uint8_t> to_bytes() const {",
   314	                "    return value;",
   315	                "  }",
   316	                "",
   317	                "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
   318	                "    value = validate_value(bytes);",
   319	                "  }",
   320	                "",
   321	                f"  {class_name} clone() const {{",
   322	                f"    return {class_name}(value);",
   323	                "  }",
   324	                "",
   325	                f"  bool operator==(const {class_name}& other) const = default;",
   326	                "",
   327	                " private:",
   328	                "  static value_type validate_value(const value_type& value_in) {",
   329	                "    if (value_in.size() != BYTE_COUNT) {",
   330	                '      throw std::invalid_argument("byte width mismatch");',
   331	                "    }",
   332	                "    value_type normalized = value_in;",
   333	                f"    normalized[0] &= {msb_mask};",
   334	                "    return normalized;",
   335	                "  }",
   336	                "};",
   337	            ]
   338	        )
   339	    return lines
   340	
   341	
   342	# ---------------------------------------------------------------------------
   343	# Enum class + wrapper
   344	# ---------------------------------------------------------------------------
   345	
   346	
   347	def _render_cpp_enum(*, type_ir: EnumIR) -> list[str]:
   348	    """Render a C++ enum class and wrapper class."""
   349	    base = type_ir.name[:-2] if type_ir.name.endswith("_t") else type_ir.name
   350	    enum_class_name = f"{base}_enum_t"
   351	    class_name = _type_class_name(type_ir.name)
   352	    width = type_ir.resolved_width
   353	    bc = byte_count(width)
   354	    uint_type = _cpp_scalar_value_type(width=width, signed=False)
   355	    first_member = type_ir.values[0].name if type_ir.values else "0"
   356	    mask_lit = _cpp_unsigned_literal((1 << width) - 1 if width < 64 else 2**64 - 1)
   357	
   358	    lines: list[str] = []
   359	
   360	    # enum class
   361	    members = ", ".join(f"{v.name} = {_cpp_unsigned_literal(v.resolved_value)}" for v in type_ir.values)
   362	    lines.append(f"enum class {enum_class_name} : {uint_type} {{{members}}};")
   363	    lines.append("")
   364	
   365	    # wrapper class
   366	    lines.extend([
   367	        f"class {class_name} {{",
   368	        " public:",
   369	        f"  static constexpr std::size_t WIDTH = {width};",
   370	        f"  static constexpr std::size_t BYTE_COUNT = {bc};",
   371	        f"  using enum_type = {enum_class_name};",
   372	        f"  enum_type value;",
   373	        "",
   374	        f"  {class_name}() : value({enum_class_name}::{first_member}) {{}}",
   375	        f"  explicit {class_name}(enum_type value_in) : value(validate_value(value_in)) {{}}",
   376	        "",
   377	        "  std::vector<std::uint8_t> to_bytes() const {",
   378	        f"    std::vector<std::uint8_t> bytes({bc}, 0);",
   379	        f"    std::uint64_t bits = static_cast<std::uint64_t>(value);",
   380	        f"    for (std::size_t idx = 0; idx < {bc}; ++idx) {{",
   381	        f"      bytes[{bc} - 1 - idx] = static_cast<std::uint8_t>((bits >> (8U * idx)) & 0xFFU);",
   382	        "    }",
   383	        "    return bytes;",
   384	        "  }",
   385	        "",
   386	        "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
   387	        f"    if (bytes.size() != {bc}) {{",
   388	        '      throw std::invalid_argument("byte width mismatch");',
   389	        "    }",
   390	        "    std::uint64_t bits = 0;",
   391	        f"    for (std::size_t idx = 0; idx < {bc}; ++idx) {{",
   392	        "      bits = (bits << 8U) | bytes[idx];",
   393	        "    }",
   394	        f"    value = validate_value(static_cast<enum_type>(bits & {mask_lit}));",
   395	        "  }",
   396	        "",
   397	        f"  {class_name} clone() const {{",
   398	        f"    return {class_name}(value);",
   399	        "  }",
   400	        "",
   401	        "  operator enum_type() const {",
   402	        "    return value;",
   403	        "  }",
   404	        "",
   405	        f"  bool operator==(const {class_name}& other) const = default;",
   406	        "",
   407	        " private:",
   408	        "  static enum_type validate_value(enum_type v) {",
   409	        "    switch (v) {",
   410	    ])
   411	    for v in type_ir.values:
   412	        lines.append(f"      case {enum_class_name}::{v.name}: return v;")
   413	    lines.extend([
   414	        "      default:",
   415	        '        throw std::invalid_argument("unknown enum value");',
   416	        "    }",
   417	        "  }",
   418	        "};",
   419	    ])
   420	    return lines
   421	
   422	
   423	# ---------------------------------------------------------------------------
   424	# Flags wrapper class
   425	# ---------------------------------------------------------------------------
   426	
   427	
   428	def _render_cpp_flags(*, type_ir: FlagsIR) -> list[str]:
   429	    """Render a C++ flags wrapper class (big-endian, MSB-first bit packing)."""
   430	    class_name = _type_class_name(type_ir.name)
   431	    num_flags = len(type_ir.fields)
   432	    total_width = num_flags + type_ir.alignment_bits
   433	    bc = byte_count(total_width)
   434	    storage_bits = bc * 8
   435	
   436	    # Choose smallest unsigned storage type
   437	    value_type = _cpp_scalar_value_type(width=storage_bits, signed=False)
   438	    is_64 = storage_bits > 32
   439	
   440	    # Data mask: top num_flags bits set, bottom alignment_bits clear
   441	    data_mask_val = ((1 << num_flags) - 1) << (storage_bits - num_flags)
   442	    if is_64:
   443	        data_mask_lit = f"0x{data_mask_val:02X}ULL"
   444	    else:
   445	        data_mask_lit = f"0x{data_mask_val:02X}U"
   446	
   447	    lines = [
   448	        f"class {class_name} {{",
   449	        " public:",
   450	        f"  static constexpr std::size_t WIDTH = {num_flags};",
   451	        f"  static constexpr std::size_t BYTE_COUNT = {bc};",
   452	        f"  using value_type = {value_type};",
   453	    ]
   454	
   455	    # Per-flag mask constants
   456	    for i, field in enumerate(type_ir.fields):
   457	        mask_val = 1 << (storage_bits - 1 - i)
   458	        if is_64:
   459	            mask_lit = f"0x{mask_val:02X}ULL"
   460	        else:
   461	            mask_lit = f"0x{mask_val:02X}U"
   462	        lines.append(f"  static constexpr value_type {field.name.upper()}_MASK = {mask_lit};")
   463	
   464	    lines.extend(
   465	        [
   466	            "  value_type value = 0;",
   467	            "",
   468	            f"  {class_name}() = default;",
   469	        ]
   470	    )
   471	
   472	    # Per-flag get/set accessors
   473	    for field in type_ir.fields:
   474	        mask_name = f"{field.name.upper()}_MASK"
   475	        lines.extend(
   476	            [
   477	                "",
   478	                f"  bool get_{field.name}() const {{ return (value & {mask_name}) != 0; }}",
   479	                f"  void set_{field.name}(bool v) {{ if (v) value |= {mask_name};"
   480	                f" else value &= static_cast<value_type>(~{mask_name}); }}",
   481	            ]
   482	        )
   483	
   484	    # to_bytes
   485	    lines.extend(
   486	        [
   487	            "",
   488	            "  std::vector<std::uint8_t> to_bytes() const {",
   489	            "    std::vector<std::uint8_t> bytes(BYTE_COUNT, 0);",
   490	            f"    value_type masked = value & {data_mask_lit};",
   491	            "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
   492	            f"      bytes[BYTE_COUNT - 1 - idx] = static_cast<std::uint8_t>((static_cast<std::uint64_t>(masked) >> (8U * idx)) & 0xFFU);",
   493	            "    }",
   494	            "    return bytes;",
   495	            "  }",
   496	        ]
   497	    )
   498	
   499	    # from_bytes
   500	    lines.extend(
   501	        [
   502	            "",
   503	            "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
   504	            "    if (bytes.size() != BYTE_COUNT) {",
   505	            '      throw std::invalid_argument("byte width mismatch");',
   506	            "    }",
   507	            "    std::uint64_t bits = 0;",
   508	            "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
   509	            "      bits = (bits << 8U) | bytes[idx];",
   510	            "    }",
   511	            f"    value = static_cast<value_type>(bits) & {data_mask_lit};",
   512	            "  }",
   513	        ]
   514	    )
   515	
   516	    # clone
   517	    lines.extend(
   518	        [
   519	            "",
   520	            f"  {class_name} clone() const {{",
   521	            f"    {class_name} cloned;",
   522	            "    cloned.value = value;",
   523	            "    return cloned;",
   524	            "  }",
   525	        ]
   526	    )
   527	
   528	    # operator==
   529	    lines.extend(
   530	        [
   531	            "",
   532	            f"  bool operator==(const {class_name}& other) const {{",
   533	            f"    return (value & {data_mask_lit}) == (other.value & {data_mask_lit});",
   534	            "  }",
   535	            "};",
   536	        ]
   537	    )
   538	
   539	    return lines
   540	
   541	
   542	# ---------------------------------------------------------------------------
   543	# Struct wrapper class
   544	# ---------------------------------------------------------------------------
   545	
   546	
   547	def _render_cpp_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
   548	    """Render a C++ struct wrapper class (per-field byte-aligned, big-endian)."""
   549	    class_name = _type_class_name(type_ir.name)
   550	    data_width = _resolved_type_width(type_ir=type_ir, type_index=type_index)
   551	    total_bc = _type_byte_count(type_ir=type_ir, type_index=type_index)
   552	    lines = [
   553	        f"class {class_name} {{",
   554	        " public:",
   555	        f"  static constexpr std::size_t WIDTH = {data_width};",
   556	        f"  static constexpr std::size_t BYTE_COUNT = {total_bc};",
   557	    ]
   558	    for field_ir in type_ir.fields:
   559	        lines.append(f"  {_render_cpp_field_decl(field_ir=field_ir, type_index=type_index)}")
   560	    lines.extend(

exec
/bin/zsh -lc "nl -ba src/piketype/backends/sv/emitter.py | sed -n '240,560p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
   240	        f"  return {{{concat}}};",
   241	        "endfunction",
   242	    ]
   243	
   244	
   245	def _render_sv_unpack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
   246	    """Render an unpack_<base> function."""
   247	    base = _type_base_name(type_ir.name)
   248	    upper_base = base.upper()
   249	
   250	    if isinstance(type_ir, ScalarAliasIR):
   251	        return [
   252	            f"function automatic {type_ir.name} unpack_{base}(logic [LP_{upper_base}_WIDTH-1:0] a);",
   253	            "  return a;",
   254	            "endfunction",
   255	        ]
   256	
   257	    if isinstance(type_ir, FlagsIR):
   258	        lines = [
   259	            f"function automatic {type_ir.name} unpack_{base}(logic [LP_{upper_base}_WIDTH-1:0] a);",
   260	            f"  {type_ir.name} result;",
   261	            "  result = '0;",
   262	        ]
   263	        for bit_idx, flag in enumerate(reversed(type_ir.fields)):
   264	            lines.append(f"  result.{flag.name} = a[{bit_idx}];")
   265	        lines.append("  return result;")
   266	        lines.append("endfunction")
   267	        return lines
   268	
   269	    if isinstance(type_ir, EnumIR):
   270	        return [
   271	            f"function automatic {type_ir.name} unpack_{base}(logic [LP_{upper_base}_WIDTH-1:0] a);",
   272	            f"  return {type_ir.name}'(a);",
   273	            "endfunction",
   274	        ]
   275	
   276	    lines = [
   277	        f"function automatic {type_ir.name} unpack_{base}(logic [LP_{upper_base}_WIDTH-1:0] a);",
   278	        f"  {type_ir.name} result;",
   279	        "  int unsigned offset;",
   280	        "  result = '0;",
   281	        "  offset = 0;",
   282	    ]
   283	
   284	    for field in reversed(type_ir.fields):
   285	        fw = _field_data_width(field=field, type_index=type_index)
   286	        if isinstance(field.type_ir, TypeRefIR):
   287	            target = type_index[field.type_ir.name]
   288	            inner_base = _type_base_name(target.name)
   289	            inner_upper = inner_base.upper()
   290	            lines.append(f"  result.{field.name} = unpack_{inner_base}(a[offset +: LP_{inner_upper}_WIDTH]);")
   291	            lines.append(f"  offset += LP_{inner_upper}_WIDTH;")
   292	        else:
   293	            lines.append(f"  result.{field.name} = a[offset +: {fw}];")
   294	            lines.append(f"  offset += {fw};")
   295	
   296	        if field.padding_bits > 0 and _is_field_signed(field=field, type_index=type_index):
   297	            w = _field_data_width(field=field, type_index=type_index)
   298	            p = field.padding_bits
   299	            lines.append(f"  result.{field.name}_pad = {{{p}{{result.{field.name}[{w - 1}]}}}};")
   300	
   301	    lines.append("  return result;")
   302	    lines.append("endfunction")
   303	    return lines
   304	
   305	
   306	# ---------------------------------------------------------------------------
   307	# Verification (test) package
   308	# ---------------------------------------------------------------------------
   309	
   310	
   311	def render_module_test_sv(module: ModuleIR) -> str:
   312	    """Render a verification-only SystemVerilog package."""
   313	    header = render_header(source_paths=(module.ref.repo_relative_path,))
   314	    type_index: dict[str, TypeDefIR] = {t.name: t for t in module.types}
   315	    body_lines = [
   316	        f"package {module.ref.basename}_test_pkg;",
   317	        f"  import {module.ref.basename}_pkg::*;",
   318	    ]
   319	    for type_ir in module.types:
   320	        body_lines.append("")
   321	        if isinstance(type_ir, ScalarAliasIR):
   322	            body_lines.extend(f"  {line}" for line in _render_sv_scalar_helper_class(type_ir=type_ir))
   323	        elif isinstance(type_ir, StructIR):
   324	            body_lines.extend(f"  {line}" for line in _render_sv_struct_helper_class(type_ir=type_ir, type_index=type_index))
   325	        elif isinstance(type_ir, FlagsIR):
   326	            body_lines.extend(f"  {line}" for line in _render_sv_flags_helper_class(type_ir=type_ir))
   327	        elif isinstance(type_ir, EnumIR):
   328	            body_lines.extend(f"  {line}" for line in _render_sv_enum_helper_class(type_ir=type_ir))
   329	    body_lines.append("endpackage")
   330	    return f"{header}\n" + "\n".join(body_lines) + "\n"
   331	
   332	
   333	def _render_sv_scalar_helper_class(*, type_ir: ScalarAliasIR) -> list[str]:
   334	    """Render a verification helper class for a scalar alias."""
   335	    class_name = _helper_class_name(type_ir.name)
   336	    base = _type_base_name(type_ir.name)
   337	    upper_base = base.upper()
   338	    bc = byte_count(type_ir.resolved_width)
   339	    pad_bits = (-type_ir.resolved_width) % 8
   340	
   341	    lines = [
   342	        f"class {class_name};",
   343	        f"  localparam int WIDTH = LP_{upper_base}_WIDTH;",
   344	        f"  localparam int BYTE_COUNT = LP_{upper_base}_BYTE_COUNT;",
   345	        f"  rand {type_ir.name} value;",
   346	        "",
   347	        f"  function new({type_ir.name} value_in = '0);",
   348	        "    value = value_in;",
   349	        "  endfunction",
   350	        "",
   351	        f"  function automatic {type_ir.name} to_slv();",
   352	        "    return value;",
   353	        "  endfunction",
   354	        "",
   355	        f"  function void from_slv({type_ir.name} value_in);",
   356	        "    value = value_in;",
   357	        "  endfunction",
   358	        "",
   359	    ]
   360	
   361	    # to_bytes: big-endian, per-field serialization
   362	    lines.extend([
   363	        "  task automatic to_bytes(output byte unsigned bytes[]);",
   364	        f"    logic [{bc * 8 - 1}:0] padded;",
   365	        "    bytes = new[BYTE_COUNT];",
   366	        "    padded = '0;",
   367	        f"    padded[WIDTH-1:0] = value;",
   368	    ])
   369	    if pad_bits > 0 and type_ir.signed:
   370	        lines.append(f"    for (int i = WIDTH; i < BYTE_COUNT*8; i++) padded[i] = value[WIDTH-1];")
   371	    lines.extend([
   372	        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
   373	        "      bytes[idx] = padded[(BYTE_COUNT - 1 - idx)*8 +: 8];",
   374	        "    end",
   375	        "  endtask",
   376	        "",
   377	    ])
   378	
   379	    # from_bytes: big-endian, mask/validate padding
   380	    lines.extend([
   381	        "  function void from_bytes(input byte unsigned bytes[]);",
   382	        f"    logic [{bc * 8 - 1}:0] padded;",
   383	        "    if (bytes.size() != BYTE_COUNT) begin",
   384	        f'      $fatal(1, "{class_name}.from_bytes size mismatch: expected %0d got %0d", BYTE_COUNT, bytes.size());',
   385	        "    end",
   386	        "    padded = '0;",
   387	        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
   388	        "      padded[(BYTE_COUNT - 1 - idx)*8 +: 8] = bytes[idx];",
   389	        "    end",
   390	    ])
   391	    if pad_bits > 0 and type_ir.signed:
   392	        lines.extend([
   393	            f"    for (int i = WIDTH; i < BYTE_COUNT*8; i++) begin",
   394	            "      if (padded[i] !== padded[WIDTH-1]) begin",
   395	            f'        $fatal(1, "{class_name}.from_bytes signed padding mismatch");',
   396	            "      end",
   397	            "    end",
   398	        ])
   399	    lines.extend([
   400	        f"    value = {type_ir.name}'(padded[WIDTH-1:0]);",
   401	        "  endfunction",
   402	        "",
   403	    ])
   404	
   405	    lines.extend([
   406	        f"  function void copy(input {class_name} rhs);",
   407	        "    value = rhs.value;",
   408	        "  endfunction",
   409	        "",
   410	        f"  function automatic {class_name} clone();",
   411	        f"    {class_name} cloned = new();",
   412	        "    cloned.value = value;",
   413	        "    return cloned;",
   414	        "  endfunction",
   415	        "",
   416	        f"  function automatic bit compare(input {class_name} rhs);",
   417	        "    return value === rhs.value;",
   418	        "  endfunction",
   419	        "",
   420	        "  function automatic string sprint();",
   421	        f'    return $sformatf("{class_name}(value=0x%0h)", value);',
   422	        "  endfunction",
   423	        f"endclass : {class_name}",
   424	    ])
   425	    return lines
   426	
   427	
   428	def _render_sv_struct_helper_class(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
   429	    """Render a field-oriented verification helper class for a struct."""
   430	    class_name = _helper_class_name(type_ir.name)
   431	    base = _type_base_name(type_ir.name)
   432	    upper_base = base.upper()
   433	
   434	    lines = [
   435	        f"class {class_name};",
   436	        f"  localparam int WIDTH = LP_{upper_base}_WIDTH;",
   437	        f"  localparam int BYTE_COUNT = LP_{upper_base}_BYTE_COUNT;",
   438	    ]
   439	    for field in type_ir.fields:
   440	        lines.append(f"  {_render_sv_helper_field_decl(field=field, type_index=type_index)}")
   441	
   442	    # Constructor
   443	    lines.extend(["", "  function new();"])
   444	    for field in type_ir.fields:
   445	        if _is_sv_composite_ref(field_type=field.type_ir, type_index=type_index):
   446	            lines.append(f"    {field.name} = new();")
   447	        else:
   448	            lines.append(f"    {field.name} = '0;")
   449	    lines.append("  endfunction")
   450	
   451	    # to_slv: assemble padded typedef with proper padding fill
   452	    lines.extend(["", f"  function automatic {type_ir.name} to_slv();", f"    {type_ir.name} packed_value;"])
   453	    for field in type_ir.fields:
   454	        if _is_sv_composite_ref(field_type=field.type_ir, type_index=type_index):
   455	            lines.append(f"    packed_value.{field.name} = {field.name}.to_slv();")
   456	        else:
   457	            lines.append(f"    packed_value.{field.name} = {field.name};")
   458	        if field.padding_bits > 0:
   459	            if _is_field_signed(field=field, type_index=type_index):
   460	                w = _field_data_width(field=field, type_index=type_index)
   461	                p = field.padding_bits
   462	                lines.append(f"    packed_value.{field.name}_pad = {{{p}{{packed_value.{field.name}[{w - 1}]}}}};")
   463	            else:
   464	                lines.append(f"    packed_value.{field.name}_pad = '0;")
   465	    if type_ir.alignment_bits > 0:
   466	        lines.append("    packed_value._align_pad = '0;")
   467	    lines.extend(["    return packed_value;", "  endfunction"])
   468	
   469	    # from_slv: extract field values, ignore padding
   470	    lines.extend(["", f"  function void from_slv({type_ir.name} value_in);"])
   471	    for field in type_ir.fields:
   472	        if _is_sv_composite_ref(field_type=field.type_ir, type_index=type_index):
   473	            lines.append(f"    {field.name}.from_slv(value_in.{field.name});")
   474	        else:
   475	            lines.append(f"    {field.name} = value_in.{field.name};")
   476	    lines.append("  endfunction")
   477	
   478	    # to_bytes: per-field big-endian serialization
   479	    lines.extend([
   480	        "",
   481	        "  task automatic to_bytes(output byte unsigned bytes[]);",
   482	        "    int byte_idx;",
   483	        "    bytes = new[BYTE_COUNT];",
   484	        "    byte_idx = 0;",
   485	    ])
   486	    for field in type_ir.fields:
   487	        lines.extend(_render_sv_helper_to_bytes_step(field=field, type_index=type_index))
   488	    if type_ir.alignment_bits > 0:
   489	        align_bytes = type_ir.alignment_bits // 8
   490	        lines.append("    begin")
   491	        lines.append(f"      for (int i = 0; i < {align_bytes}; i++) bytes[byte_idx + i] = 8'h00;")
   492	        lines.append(f"      byte_idx += {align_bytes};")
   493	        lines.append("    end")
   494	    lines.append("  endtask")
   495	
   496	    # from_bytes: per-field deserialization with signed validation
   497	    lines.extend([
   498	        "",
   499	        "  function void from_bytes(input byte unsigned bytes[]);",
   500	        "    int byte_idx;",
   501	        "    if (bytes.size() != BYTE_COUNT) begin",
   502	        f'      $fatal(1, "{class_name}.from_bytes size mismatch: expected %0d got %0d", BYTE_COUNT, bytes.size());',
   503	        "    end",
   504	        "    byte_idx = 0;",
   505	    ])
   506	    for field in type_ir.fields:
   507	        lines.extend(_render_sv_helper_from_bytes_step(field=field, type_index=type_index, class_name=class_name))
   508	    if type_ir.alignment_bits > 0:
   509	        align_bytes = type_ir.alignment_bits // 8
   510	        lines.append(f"    byte_idx += {align_bytes};")
   511	    lines.append("  endfunction")
   512	
   513	    # copy
   514	    lines.extend(["", f"  function void copy(input {class_name} rhs);"])
   515	    for field in type_ir.fields:
   516	        if _is_sv_composite_ref(field_type=field.type_ir, type_index=type_index):
   517	            lines.append(f"    {field.name}.copy(rhs.{field.name});")
   518	        else:
   519	            lines.append(f"    {field.name} = rhs.{field.name};")
   520	    lines.append("  endfunction")
   521	
   522	    # clone
   523	    lines.extend([
   524	        "",
   525	        f"  function automatic {class_name} clone();",
   526	        f"    {class_name} cloned = new();",
   527	        "    cloned.copy(this);",
   528	        "    return cloned;",
   529	        "  endfunction",
   530	    ])
   531	
   532	    # compare
   533	    lines.extend(["", f"  function automatic bit compare(input {class_name} rhs);", "    bit match;", "    match = 1'b1;"])
   534	    for field in type_ir.fields:
   535	        if _is_sv_composite_ref(field_type=field.type_ir, type_index=type_index):
   536	            lines.append(f"    match &= {field.name}.compare(rhs.{field.name});")
   537	        else:
   538	            lines.append(f"    match &= ({field.name} === rhs.{field.name});")
   539	    lines.extend(["    return match;", "  endfunction"])
   540	
   541	    # sprint
   542	    fmt_parts: list[str] = []
   543	    arg_parts: list[str] = []
   544	    for field in type_ir.fields:
   545	        if _is_sv_composite_ref(field_type=field.type_ir, type_index=type_index):
   546	            fmt_parts.append(f"{field.name}=%s")
   547	            arg_parts.append(f"{field.name}.sprint()")
   548	        else:
   549	            fmt_parts.append(f"{field.name}=0x%0h")
   550	            arg_parts.append(field.name)
   551	    fmt = ", ".join(fmt_parts)
   552	    args = ", ".join(arg_parts)
   553	    lines.extend([
   554	        "",
   555	        "  function automatic string sprint();",
   556	        f'    return $sformatf("{class_name}({fmt})", {args});',
   557	        "  endfunction",
   558	        f"endclass : {class_name}",
   559	    ])
   560	    return lines

exec
/bin/zsh -lc "nl -ba src/piketype/backends/sv/emitter.py | sed -n '900,980p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
   900	
   901	
   902	def _field_data_width(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> int:
   903	    """Data width of one struct field."""
   904	    if isinstance(field.type_ir, ScalarTypeSpecIR):
   905	        return field.type_ir.resolved_width
   906	    target = type_index[field.type_ir.name]
   907	    return _data_width(type_ir=target, type_index=type_index)
   908	
   909	
   910	def _type_byte_count(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
   911	    """Total byte count (including padding and alignment) of a type."""
   912	    if isinstance(type_ir, ScalarAliasIR):
   913	        return byte_count(type_ir.resolved_width)
   914	    if isinstance(type_ir, FlagsIR):
   915	        return byte_count(len(type_ir.fields))
   916	    if isinstance(type_ir, EnumIR):
   917	        return byte_count(type_ir.resolved_width)
   918	    field_bytes = sum(_field_byte_count(field=f, type_index=type_index) for f in type_ir.fields)
   919	    return field_bytes + type_ir.alignment_bits // 8
   920	
   921	
   922	def _field_byte_count(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> int:
   923	    """Byte count of one struct field."""
   924	    if isinstance(field.type_ir, ScalarTypeSpecIR):
   925	        return byte_count(field.type_ir.resolved_width)
   926	    target = type_index[field.type_ir.name]
   927	    return _type_byte_count(type_ir=target, type_index=type_index)
   928	
   929	
   930	def _is_field_signed(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> bool:
   931	    """Whether a scalar-typed field is signed."""
   932	    if isinstance(field.type_ir, ScalarTypeSpecIR):
   933	        return field.type_ir.signed
   934	    target = type_index.get(field.type_ir.name)
   935	    if isinstance(target, ScalarAliasIR):
   936	        return target.signed
   937	    return False
   938	
   939	
   940	def _is_sv_composite_ref(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> bool:
   941	    """Return whether one SV field references a named struct or flags type."""
   942	    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], (StructIR, FlagsIR, EnumIR))
   943	
   944	
   945	def _helper_class_name(type_name: str) -> str:
   946	    """Convert a type name to its SV helper class name."""
   947	    if type_name.endswith("_t"):
   948	        return f"{type_name[:-2]}_ct"
   949	    return f"{type_name}_ct"

codex
Executive summary: Iter2 fixes most of the iter1 review: ordering, Python view coverage, render environment contract, wheel check, and risk register are materially improved. The plan still cannot be approved because the transitional view fields violate FR-8, and the C++/SV view sketches remain byte-risky or incomplete.

| # | Iter1 issue | Status | Evidence |
|---|---|---|---|
| 1 | FR-6 commit ordering | Resolved | Phase 1 commits 2-5 follow FR-6 at `plan.md:274-281`; Phase 2 at `351-359`; Phase 3 at `447-455`. |
| 2 | Python view model incomplete | Resolved | `EnumView`, `FlagsView`, `FlagFieldView`, and `StructFieldView` are now explicit at `185-245`. |
| 3 | C++ helper bodies precomputed in Python | Resolved | `plan.md:347` says templates render helper skeletons and helper bodies are not precomputed. |
| 4 | C++/SV sketches not actionable | Partially resolved | C++/SV sketches exist at `294-349` and `371-445`, but C++ scalar/enum/flags are still hand-waved and SV lacks enough structured pack/unpack/helper-step fields. |
| 5 | Byte-parity strategy underspecified | Mostly resolved | `body_lines` passthrough is specified at `39-48`; Phase 1 commits 2-6 are credible if the FR-8 issue below is fixed. |
| 6 | Phase 0 wheel smoke meaningless | Resolved | Empty dirs are deferred at `69`; Phase 0 only proves build at `132`; Phase 4 diffs source `.j2` files against wheel contents at `471`. |
| 7 | Missing trim/lstrip and frozen-IR risks | Resolved | Added risk rows at `485` and `487`. |
| 8 | Env options and keyword-only signature not pinned | Resolved | Exact `make_environment(*, package: str)` contract and options are at `86-95`. |
| 9 | C++ `--namespace` override | Partially resolved | Override is covered at `349` and `491`, but the concrete namespace sketch is byte-inaccurate as written. |

Phase 1 parity check: Commit 2 preserves the full legacy body through `body_lines`; commit 3 keeps helper bodies as per-type passthrough strings; commit 4 moves helper skeletons while consuming precomputed primitives; commit 5 moves fragments and retires `body_lines`; commit 6 deletes dead helpers after template output owns the backend. That sequence is coherent.

New issues with severity tags:

1. **BLOCKING — FR-8 / Phase 1-3 transitional views.** `body_lines: tuple[str, ...] | None` appears in the Python, C++, and SV view sketches (`plan.md:44`, `250-260`, `331-343`, `396-438`). FR-8 does not allow `None` as a view-model field type. Fix by using `body_lines: tuple[str, ...]` with an empty tuple sentinel, optionally plus a primitive `has_body_lines: bool`.

2. **BLOCKING — FR-7 / C++ byte parity.** `CppNamespaceView` examples use nested namespace lines and include `piketype` in `qualified` (`plan.md:298-302`), but the current emitter emits one C++17 namespace line and filters out `piketype`. Also `standard_includes` says sorted at `339`, which can reorder the current `<cstdint>`-first output. Pin the view to the exact current namespace string/open/close and include order.

3. **BLOCKING — FR-18 / FR-10 / Phase 2-3 view-model completeness.** `CppScalarAliasView`, `CppEnumView`, `CppFlagsView`, and `CppStructView` are not explicitly defined (`plan.md:345`). SV also lacks final structured views for synth pack/unpack and test helper to/from-bytes steps; `pack_unpack_blocks` is only transitional. Add concrete dataclasses for every primitive, literal, discriminator, padding value, and loop bound the templates need.

4. **WARNING — FR-3 / Phase 0 render helper.** The planned `render` accepts `dict` context (`plan.md:100-104`), while FR-3 says context shall be a view-model dataclass instance. Either reject dicts or explicitly limit dict support to tests outside production rendering.

VERDICT: REVISE
2026-04-29T11:23:37.774885Z ERROR codex_core::session: failed to record rollout items: thread 019dd8f6-d294-7bd1-aef9-7cc3326aacd2 not found
tokens used
98,349
Executive summary: Iter2 fixes most of the iter1 review: ordering, Python view coverage, render environment contract, wheel check, and risk register are materially improved. The plan still cannot be approved because the transitional view fields violate FR-8, and the C++/SV view sketches remain byte-risky or incomplete.

| # | Iter1 issue | Status | Evidence |
|---|---|---|---|
| 1 | FR-6 commit ordering | Resolved | Phase 1 commits 2-5 follow FR-6 at `plan.md:274-281`; Phase 2 at `351-359`; Phase 3 at `447-455`. |
| 2 | Python view model incomplete | Resolved | `EnumView`, `FlagsView`, `FlagFieldView`, and `StructFieldView` are now explicit at `185-245`. |
| 3 | C++ helper bodies precomputed in Python | Resolved | `plan.md:347` says templates render helper skeletons and helper bodies are not precomputed. |
| 4 | C++/SV sketches not actionable | Partially resolved | C++/SV sketches exist at `294-349` and `371-445`, but C++ scalar/enum/flags are still hand-waved and SV lacks enough structured pack/unpack/helper-step fields. |
| 5 | Byte-parity strategy underspecified | Mostly resolved | `body_lines` passthrough is specified at `39-48`; Phase 1 commits 2-6 are credible if the FR-8 issue below is fixed. |
| 6 | Phase 0 wheel smoke meaningless | Resolved | Empty dirs are deferred at `69`; Phase 0 only proves build at `132`; Phase 4 diffs source `.j2` files against wheel contents at `471`. |
| 7 | Missing trim/lstrip and frozen-IR risks | Resolved | Added risk rows at `485` and `487`. |
| 8 | Env options and keyword-only signature not pinned | Resolved | Exact `make_environment(*, package: str)` contract and options are at `86-95`. |
| 9 | C++ `--namespace` override | Partially resolved | Override is covered at `349` and `491`, but the concrete namespace sketch is byte-inaccurate as written. |

Phase 1 parity check: Commit 2 preserves the full legacy body through `body_lines`; commit 3 keeps helper bodies as per-type passthrough strings; commit 4 moves helper skeletons while consuming precomputed primitives; commit 5 moves fragments and retires `body_lines`; commit 6 deletes dead helpers after template output owns the backend. That sequence is coherent.

New issues with severity tags:

1. **BLOCKING — FR-8 / Phase 1-3 transitional views.** `body_lines: tuple[str, ...] | None` appears in the Python, C++, and SV view sketches (`plan.md:44`, `250-260`, `331-343`, `396-438`). FR-8 does not allow `None` as a view-model field type. Fix by using `body_lines: tuple[str, ...]` with an empty tuple sentinel, optionally plus a primitive `has_body_lines: bool`.

2. **BLOCKING — FR-7 / C++ byte parity.** `CppNamespaceView` examples use nested namespace lines and include `piketype` in `qualified` (`plan.md:298-302`), but the current emitter emits one C++17 namespace line and filters out `piketype`. Also `standard_includes` says sorted at `339`, which can reorder the current `<cstdint>`-first output. Pin the view to the exact current namespace string/open/close and include order.

3. **BLOCKING — FR-18 / FR-10 / Phase 2-3 view-model completeness.** `CppScalarAliasView`, `CppEnumView`, `CppFlagsView`, and `CppStructView` are not explicitly defined (`plan.md:345`). SV also lacks final structured views for synth pack/unpack and test helper to/from-bytes steps; `pack_unpack_blocks` is only transitional. Add concrete dataclasses for every primitive, literal, discriminator, padding value, and loop bound the templates need.

4. **WARNING — FR-3 / Phase 0 render helper.** The planned `render` accepts `dict` context (`plan.md:100-104`), while FR-3 says context shall be a view-model dataclass instance. Either reject dicts or explicitly limit dict support to tests outside production rendering.

VERDICT: REVISE
