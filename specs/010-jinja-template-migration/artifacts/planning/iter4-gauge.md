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
session id: 019dd900-6655-7e21-bfda-f173695076f0
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/planning/iter4-gauge-prompt.md
codex
I’ll read the planning prompt first, then execute exactly what it asks within the repo context.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/planning/iter4-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Planning Iteration 4

This is iteration 4. Iteration 3 returned `VERDICT: REVISE` with three BLOCKINGs:

1. Leftover prose at Phase 1 commit 5 still said `body_lines` was "always None" — contradicting the new tuple-plus-bool mechanism.
2. `SvPackUnpackFnView` precomputed `pack_lines` / `unpack_lines` as Python-built body strings — meaningful structure had to move into templates.
3. C++ scalar dataclasses missed primitives needed for current helper branches (signed-padding branch booleans, full-range literal, byte-total mask literal).

All three were addressed in iter4.

## Inputs

- `specs/010-jinja-template-migration/plan.md` (iter4).
- `specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md`.

## Review

1. Confirm the Phase 1 commit 5 description now uses the empty-tuple + `has_body_lines=False` language.
2. Confirm `SvPackUnpackFnView` is now a union of four structured variants (scalar/flags/enum/struct) with no pre-rendered body strings.
3. Confirm `CppScalarAliasView` now exposes:
   - `is_narrow_signed` / `is_narrow_unsigned` / `is_wide` discriminators.
   - `has_signed_padding` and `has_signed_short_width` branch booleans.
   - `full_range_literal`, `byte_total_mask_literal`, in addition to the previously existing literals.
4. Look for any new contradictions introduced by these surgical edits.

This is the **maxIterations=5 budget**. After this round there is one more REVISE allowed before the loop exits without an APPROVE; bias APPROVE if the three BLOCKINGs are mechanically resolved and no new BLOCKING is introduced.

End with `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after.

codex
The prompt is a planning gauge review: I need verify three prior blockers against the current plan and return a strict APPROVE/REVISE verdict. I’m checking the plan and prior gauge notes now.
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md" in /Users/ezchi/Projects/pike-type
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

Concrete mechanism (FR-8/FR-9 compliant — no `None`, no `set`, no `dict`):
- `ModuleView` carries two fields: `body_lines: tuple[str, ...]` (default empty tuple) and `has_body_lines: bool` (a primitive bool, FR-8 compliant). When `has_body_lines` is `True`, the primary template emits `{{ body_lines | join("\n") }}` for the not-yet-templated portion.
- Each sub-step replaces a portion of `body_lines` with a structured field (`types: tuple[TypeView, ...]`, etc.). The template's body section transitions from `{% if has_body_lines %}{{ body_lines | join("\n") }}{% endif %}` to a structured loop over `types`.
- After sub-step 4 (fragments), `body_lines` is empty and `has_body_lines` is False everywhere. Both fields are retired in the cleanup commit.

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
    """Render a template against a view-model dataclass instance.

    Per FR-3, the production context is always a frozen view-model dataclass.
    Dict contexts are rejected. Tests that need a dict-shaped context build
    their own ad-hoc env via `jinja2.Environment(loader=DictLoader(...))`.
    """
    if not is_dataclass(context) or isinstance(context, type):
        raise TypeError(
            f"render context must be a dataclass instance, got {type(context).__name__}"
        )
    output = env.get_template(template_name).render(**asdict(context))
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
session id: 019dd8fd-5bfd-7490-aab6-2fbfe12085af
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/planning/iter3-gauge-prompt.md
codex
I’ll read the referenced prompt first, then inspect only the files it points at before making any changes.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/planning/iter3-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Planning Iteration 3

This is iteration 3 of the planning stage. Iteration 2 returned `VERDICT: REVISE` with:

1. BLOCKING — `tuple[str, ...] | None` violates FR-8.
2. BLOCKING — C++ byte-parity issues in `CppNamespaceView` (nested `piketype`) and `standard_includes` (alphabetization claim).
3. BLOCKING — C++/SV view-model dataclasses still under-specified.
4. WARNING — `render` accepted `dict` context, contradicting FR-3.

All four were addressed in iter3.

## Inputs

- `specs/010-jinja-template-migration/plan.md` (iter3).
- `specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md`.

## Review

1. Confirm every transitional view uses `tuple[str, ...]` + `has_body_lines: bool`, no `| None`.
2. Confirm `CppNamespaceView` matches current emitter byte output (single C++17 nested namespace line, `piketype` filtered, `has_namespace` bool guards open/close lines).
3. Confirm `standard_includes` is declaration-order (cstdint always; cstddef/stdexcept/vector if has_types) — NOT alphabetized.
4. Confirm Cpp{Guard,Constant,ScalarAlias,EnumMember,Enum,FlagField,Flags,StructField,Struct}View are explicitly defined.
5. Confirm SV typedef and helper-class variants are explicitly defined (synth and test).
6. Confirm `render` rejects dict context.
7. Look for any new contradictions, missing FR coverage, or commit-level inconsistency.

End with `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after.

Bias APPROVE: only one round of REVISE remains in the maxIterations budget.

codex
The prompt is a planning-stage gauge review. I’m reading the iter3 plan and the prior gauge output, then I’ll verify the specific regression points against the current code where byte-parity claims depend on emitters.
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
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

Concrete mechanism (FR-8/FR-9 compliant — no `None`, no `set`, no `dict`):
- `ModuleView` carries two fields: `body_lines: tuple[str, ...]` (default empty tuple) and `has_body_lines: bool` (a primitive bool, FR-8 compliant). When `has_body_lines` is `True`, the primary template emits `{{ body_lines | join("\n") }}` for the not-yet-templated portion.
- Each sub-step replaces a portion of `body_lines` with a structured field (`types: tuple[TypeView, ...]`, etc.). The template's body section transitions from `{% if has_body_lines %}{{ body_lines | join("\n") }}{% endif %}` to a structured loop over `types`.
- After sub-step 4 (fragments), `body_lines` is empty and `has_body_lines` is False everywhere. Both fields are retired in the cleanup commit.

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
    """Render a template against a view-model dataclass instance.

    Per FR-3, the production context is always a frozen view-model dataclass.
    Dict contexts are rejected. Tests that need a dict-shaped context build
    their own ad-hoc env via `jinja2.Environment(loader=DictLoader(...))`.
    """
    if not is_dataclass(context) or isinstance(context, type):
        raise TypeError(
            f"render context must be a dataclass instance, got {type(context).__name__}"
        )
    output = env.get_template(template_name).render(**asdict(context))
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

exec
/bin/zsh -lc 'rg -n "Phase 1|commit 5|body_lines|empty-tuple|has_body_lines|SvPackUnpackFnView|pack_lines|unpack_lines|CppScalarAliasView|is_narrow_signed|is_narrow_unsigned|is_wide|has_signed_padding|has_signed_short_width|full_range_literal|byte_total_mask_literal" specs/010-jinja-template-migration/plan.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
41:Each Phase 1/2/3 sub-step commit replaces one slice of the inline emitter with a template, while remaining slices continue to render via the legacy inline path. The plan keeps byte parity at every commit by passing the not-yet-migrated slices through to the template as **already-rendered strings**.
44:- `ModuleView` carries two fields: `body_lines: tuple[str, ...]` (default empty tuple) and `has_body_lines: bool` (a primitive bool, FR-8 compliant). When `has_body_lines` is `True`, the primary template emits `{{ body_lines | join("\n") }}` for the not-yet-templated portion.
45:- Each sub-step replaces a portion of `body_lines` with a structured field (`types: tuple[TypeView, ...]`, etc.). The template's body section transitions from `{% if has_body_lines %}{{ body_lines | join("\n") }}{% endif %}` to a structured loop over `types`.
46:- After sub-step 4 (fragments), `body_lines` is empty and `has_body_lines` is False everywhere. Both fields are retired in the cleanup commit.
69:| (no template directories yet)                                   | n/a     | Empty `templates/` dirs are deferred to Phase 1/2/3 — they are created when their first `.j2` file lands, so the wheel build never tries to package an empty directory. |
135:- `pip wheel . -w /tmp/pike_wheel_ph0/ --no-deps` succeeds (wheel will not contain any `.j2` yet — packaging proof is deferred to Phase 1's first template-landing commit).
139:## Phase 1 — Python backend migration
175:    is_wide: bool                 # width > 64
229:    is_wide_scalar: bool          # ScalarTypeSpec, width > 64
263:    body_lines: tuple[str, ...]
264:    has_body_lines: bool
278:**Commit sequence (Phase 1) — strictly FR-6 sub-step ordered:**
281:2. `feat(py): module skeleton via templates` (FR-6 sub-step 1) — `module.j2` renders header + imports + footer. `emit_py` constructs `ModuleView` with `body_lines = tuple(legacy_render_body_lines(module))` and the template emits `{{ body_lines | join("\n") }}` for the body. **Byte parity preserved.**
282:3. `feat(py): top-level type declaration skeletons via templates` (FR-6 sub-step 2) — `_macros.j2` adds `scalar_class_skeleton`, `struct_class_skeleton`, `enum_classes_skeleton`, `flags_class_skeleton` macros that emit *only the class header lines* (`class X:`, `WIDTH = ...`, `BYTE_COUNT = ...`). Helper-method bodies and expression fragments still arrive as `body_lines_per_type: tuple[str, ...]` strings on each TypeView. The view is augmented with `helper_lines: tuple[str, ...]` per TypeView temporarily. **Byte parity preserved.**
284:5. `feat(py): expression and field-level fragments` (FR-6 sub-step 4) — expressions like Python constants, enum member values, and flag mask literals are now rendered from view-model `*_expr: str` fields directly in templates (no Python concatenation). Also handles struct field annotations/defaults/coercer literals. The transitional `body_lines: tuple[str, ...]` field on `ModuleView` is now always the empty tuple and `has_body_lines: bool` is always `False` after this commit. (Both fields remain on the dataclass with default values until the cleanup commit; the template no longer reads them after this commit.) **Byte parity preserved.**
288:**Phase 1 gates (per-backend):** AC-1-Py..AC-7-Py, all tested at the end of commit 7.
324:class CppScalarAliasView:
331:    is_narrow_signed: bool        # width <= 64 and signed
332:    is_narrow_unsigned: bool      # width <= 64 and not signed
333:    is_wide: bool                 # width > 64 (always unsigned in current emitter)
335:    has_signed_padding: bool      # is_narrow_signed and (byte_count*8 - width) > 0
336:    has_signed_short_width: bool  # is_narrow_signed and width < 64
344:    sign_bit_literal: str         # _cpp_unsigned_literal(1 << (width-1)) when has_signed_short_width; else ""
345:    full_range_literal: str       # _cpp_unsigned_literal(1 << width) when has_signed_short_width; else ""
346:    byte_total_mask_literal: str  # _cpp_unsigned_literal((1 << (byte_count*8)) - 1 if byte_count*8 < 64 else 2**64 - 1) when has_signed_padding; else ""
379:    is_wide: bool                 # storage_bits > 64
395:    is_wide_scalar: bool
414:type CppTypeView = CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView
432:    body_lines: tuple[str, ...]   # transitional, FR-8 compliant
433:    has_body_lines: bool
446:**Commit sequence (Phase 2):** same FR-6 sub-step structure as Phase 1 — 7 commits.
546:    has_signed_padding: bool      # field.padding_bits > 0 and field is signed
547:    padding_bits: int             # field.padding_bits when has_signed_padding else 0
548:    sign_bit_index: int           # data_width - 1 when has_signed_padding else 0
562:type SvPackUnpackFnView = (
575:    pack_unpack_fns: tuple[SvPackUnpackFnView, ...]
576:    body_lines: tuple[str, ...]   # transitional, FR-8 compliant
577:    has_body_lines: bool
645:    body_lines: tuple[str, ...]   # transitional, FR-8 compliant
646:    has_body_lines: bool
692:| Whitespace drift on first template render breaks goldens | High | `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True` in `make_environment`. Migrate one sub-step at a time and diff goldens after each commit. The transitional `body_lines | join("\n")` mechanism preserves line-by-line legacy output verbatim until each sub-step replaces it. |
693:| Jinja `trim_blocks`/`lstrip_blocks` interacting unexpectedly with literal-heavy template content (e.g., generated SV helper classes containing `begin`/`end` blocks) | Medium | When a literal-heavy block must be preserved verbatim, wrap it in `{% raw %}...{% endraw %}` or pass it through as a precomputed `str` field on the view (the `body_lines` mechanism). Phase 3 commit 4 explicitly tests this on the largest SV `_helper_class` block. |
694:| `PackageLoader` does not find templates from a wheel install | Medium | Phase 1 commit 2 verifies wheel packaging immediately by building the wheel and running smoke test once the first `.j2` file lands (Phase 0 commit 4 only configures package-data; Phase 1 commit 2 lands the first template and exercises the wheel path). |
706:- Phase 0 must complete before any of Phase 1/2/3 starts.
707:- Phase 1 → Phase 2 → Phase 3 (FR-5/CL-1).
709:- Within each Phase 1/2/3 sub-step commit sequence, commit N+1 depends on commit N's byte parity verification.
731:- Phase 1: 7 commits (6 migration + 1 perf row)

exec
/bin/zsh -lc 'tail -n 120 specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md' in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '300,370p' specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '520,590p' specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
936:def _render_wide_inline_helpers(
1020:def _cpp_scalar_value_type(*, width: int, signed: bool) -> str:
1031:def _cpp_unsigned_literal(value: int) -> str:
1058:def _is_wide_inline_scalar(*, field_type: FieldTypeIR) -> bool:
1059:    """Return whether one field is an inline scalar wider than 64 bits."""

exec
/bin/zsh -lc "nl -ba src/piketype/backends/cpp/emitter.py | sed -n '980,1075p'" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
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

codex
1. **BLOCKING — FR-8 / Phase 1 commit 5.** `plan.md:284` still says `body_lines` is “always `None`”. That contradicts the iter3 tuple-plus-bool mechanism and FR-8. It must say empty tuple with `has_body_lines=False`, then removal.

2. **BLOCKING — FR-6 / FR-10 / NFR-5 / SV view model.** `SvPackUnpackFnView` still uses `pack_lines` / `unpack_lines` as pre-rendered function bodies (`plan.md:499-502`). Pack/unpack helper structure is meaningful output and must be templated, not hidden as Python-built body strings.

3. **BLOCKING — FR-18 / C++ byte parity.** The C++ dataclasses are explicit, but still miss primitives needed to reproduce current helper branches without Jinja arithmetic: e.g. signed padding branch booleans, byte-total mask literal, and full-range literal for scalar and inline scalar helpers. Implementers would have to derive these in templates or Python body strings.

The namespace and include-order fixes are correct, and `render` now rejects dict contexts.

VERDICT: REVISE
2026-04-29T11:27:54.005907Z ERROR codex_core::session: failed to record rollout items: thread 019dd8fd-5bfd-7490-aab6-2fbfe12085af not found
tokens used
107,061
1. **BLOCKING — FR-8 / Phase 1 commit 5.** `plan.md:284` still says `body_lines` is “always `None`”. That contradicts the iter3 tuple-plus-bool mechanism and FR-8. It must say empty tuple with `has_body_lines=False`, then removal.

2. **BLOCKING — FR-6 / FR-10 / NFR-5 / SV view model.** `SvPackUnpackFnView` still uses `pack_lines` / `unpack_lines` as pre-rendered function bodies (`plan.md:499-502`). Pack/unpack helper structure is meaningful output and must be templated, not hidden as Python-built body strings.

3. **BLOCKING — FR-18 / C++ byte parity.** The C++ dataclasses are explicit, but still miss primitives needed to reproduce current helper branches without Jinja arithmetic: e.g. signed padding branch booleans, byte-total mask literal, and full-range literal for scalar and inline scalar helpers. Implementers would have to derive these in templates or Python body strings.

The namespace and include-order fixes are correct, and `render` now rejects dict contexts.

VERDICT: REVISE

 succeeded in 0ms:
```python
@dataclass(frozen=True, slots=True)
class CppGuardView:
    # When --namespace=NS: macro = "{NS_with_:_replaced_by__}_{basename}_TYPES_HPP".upper()
    # Default: macro = "_".join((*namespace_parts, "types_hpp")).upper().replace(".", "_")
    macro: str                    # exact include guard symbol

@dataclass(frozen=True, slots=True)
class CppNamespaceView:
    # Single C++17 nested-namespace line (matches current emitter):
    #   default:  "::".join(part for part in namespace_parts if part != "piketype")  e.g. "alpha::types"
    #   override: f"{NS}::{basename}"  e.g. "alpha::types"
    qualified: str                # may be "" if there is no namespace
    has_namespace: bool           # True iff qualified != ""
    open_line: str                # f"namespace {qualified} {{" or "" when has_namespace is False
    close_line: str               # f"}}  // namespace {qualified}" or "" when has_namespace is False

@dataclass(frozen=True, slots=True)
class CppConstantView:
    cpp_type: str                 # "std::int32_t", "std::uint64_t" — chosen by _render_cpp_const
    name: str
    value_expr: str               # pre-rendered: literal form ("123U", "456ULL") or expression form

@dataclass(frozen=True, slots=True)
class CppScalarAliasView:
    class_name: str               # e.g. "addr_ct"
    width: int
    signed: bool
    byte_count: int
    storage_type: str             # _cpp_scalar_value_type result; "std::uint32_t" / "std::int32_t" / "std::vector<std::uint8_t>" for wide
    # Mutually-exclusive discriminators (exactly one is True):
    is_narrow_signed: bool        # width <= 64 and signed
    is_narrow_unsigned: bool      # width <= 64 and not signed
    is_wide: bool                 # width > 64 (always unsigned in current emitter)
    # Booleans for emitter branches the template must mirror:
    has_signed_padding: bool      # is_narrow_signed and (byte_count*8 - width) > 0
    has_signed_short_width: bool  # is_narrow_signed and width < 64
    # Literals (each pre-rendered as the C++ source text the template emits verbatim).
    # When a literal is not used by the active branch (e.g. sign_bit_literal in the
    # narrow-unsigned branch), its field value is the empty string and the template
    # never references it.
    min_value_literal: str        # for narrow signed: e.g. "-2147483648"; for narrow unsigned: ""
    max_value_literal: str        # for narrow: signed/unsigned numeric max literal; for wide: _cpp_unsigned_literal(2**width - 1)
    mask_literal: str             # _cpp_unsigned_literal((1 << width) - 1) when width < 64; else _cpp_unsigned_literal(2**64 - 1)
    sign_bit_literal: str         # _cpp_unsigned_literal(1 << (width-1)) when has_signed_short_width; else ""
    full_range_literal: str       # _cpp_unsigned_literal(1 << width) when has_signed_short_width; else ""
    byte_total_mask_literal: str  # _cpp_unsigned_literal((1 << (byte_count*8)) - 1 if byte_count*8 < 64 else 2**64 - 1) when has_signed_padding; else ""
    msb_byte_mask_literal: str    # for wide: _cpp_unsigned_literal((1 << (8 - pad)) - 1) when pad > 0, else "0xFFU"; ""  for non-wide

@dataclass(frozen=True, slots=True)
class CppEnumMemberView:
    name: str
    value_literal: str            # _cpp_unsigned_literal(resolved_value)

@dataclass(frozen=True, slots=True)
class CppEnumView:
    class_name: str               # wrapper class, e.g. "color_ct"
    enum_class_name: str          # underlying enum class, e.g. "color_enum_t"
    width: int
    byte_count: int
    underlying_uint_type: str     # _cpp_scalar_value_type(width=W, signed=False)
    first_member_name: str
    mask_literal: str             # _cpp_unsigned_literal((1 << width) - 1) or 2**64-1 for width=64
    members: tuple[CppEnumMemberView, ...]

@dataclass(frozen=True, slots=True)
class CppFlagFieldView:
    name: str
    bit_index: int                # MSB-first index (storage_bits - 1 - i)
    bit_mask_literal: str         # _cpp_unsigned_literal(1 << bit_index)


 succeeded in 0ms:
    upper_base: str               # base.upper()

@dataclass(frozen=True, slots=True)
class SvPackUnpackFlagsView:
    type_name: str
    base: str
    upper_base: str
    # MSB-first declaration order; pack concatenates `a.<name>` left-to-right.
    flag_names_for_pack: tuple[str, ...]
    # For unpack: `result.<name> = a[<bit_index>];` where bit_index is the
    # reversed-iteration position (matches current emitter line 263).
    unpack_assignments: tuple[tuple[str, int], ...]   # (flag_name, bit_index)

@dataclass(frozen=True, slots=True)
class SvPackUnpackEnumView:
    type_name: str
    base: str
    upper_base: str

@dataclass(frozen=True, slots=True)
class SvPackUnpackStructFieldView:
    name: str
    width: int                    # field data width
    is_type_ref: bool
    inner_base: str               # _type_base_name(target.name) when is_type_ref else ""
    inner_upper: str              # inner_base.upper() when is_type_ref else ""
    has_signed_padding: bool      # field.padding_bits > 0 and field is signed
    padding_bits: int             # field.padding_bits when has_signed_padding else 0
    sign_bit_index: int           # data_width - 1 when has_signed_padding else 0

@dataclass(frozen=True, slots=True)
class SvPackUnpackStructView:
    type_name: str
    base: str
    upper_base: str
    # Pack concatenates fields in declaration order with `pack_<inner>(a.<name>)`
    # for type refs, else `a.<name>`.
    pack_field_parts: tuple[tuple[str, str], ...]   # (name, op) where op is "ref" or "scalar"
    pack_inner_bases: tuple[str, ...]               # parallel to pack_field_parts: inner_base or "" if scalar
    # Unpack iterates fields in REVERSED order (matches current emitter line 284).
    unpack_fields: tuple[SvPackUnpackStructFieldView, ...]

type SvPackUnpackFnView = (
    SvPackUnpackScalarView
    | SvPackUnpackFlagsView
    | SvPackUnpackEnumView
    | SvPackUnpackStructView
)

@dataclass(frozen=True, slots=True)
class SvSynthModuleView:
    header: str
    package_name: str             # <basename>_pkg
    constants: tuple[SvConstantView, ...]
    typedefs: tuple[SvTypedefView, ...]
    pack_unpack_fns: tuple[SvPackUnpackFnView, ...]
    body_lines: tuple[str, ...]   # transitional, FR-8 compliant
    has_body_lines: bool

# --- Test package (one per module if module.types is non-empty) -------------

@dataclass(frozen=True, slots=True)
class SvScalarHelperClassView:
    name: str                     # "addr_helper"
    underlying_typedef: str       # "addr_t"
    width: int
    byte_count: int
    signed: bool
    pack_bits: int                # byte_count * 8
    mask_literal: str             # SV-format literal (e.g. "32'hFFFFFFFF")
    sign_bit_literal: str

exec
/bin/zsh -lc 'rg -n "always None|pack_lines|unpack_lines|body strings|pre-render|precomputed|SvPackUnpackFnView|CppScalarAliasView|VERDICT|BLOCKING|REVISE|APPROVE" specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md specs/010-jinja-template-migration/plan.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
specs/010-jinja-template-migration/plan.md:167:    value_expr: str               # pre-rendered Python expression, e.g. "(1 << 32)" or "MAX_VALUE"
specs/010-jinja-template-migration/plan.md:186:    resolved_value_expr: str      # pre-rendered, e.g. "0", "16"
specs/010-jinja-template-migration/plan.md:219:    annotation: str               # pre-rendered "int", "bytes", "addr_ct | None"
specs/010-jinja-template-migration/plan.md:220:    default_expr: str             # pre-rendered "0", 'b"\\x00" * 4', "field(default_factory=foo_ct)"
specs/010-jinja-template-migration/plan.md:222:    pack_bits: int                # byte_count * 8 (precomputed; FR-10 forbids template arithmetic on this)
specs/010-jinja-template-migration/plan.md:255:    header: str                                  # full pre-rendered header line (FR-13)
specs/010-jinja-template-migration/plan.md:283:4. `feat(py): helper-method skeletons via templates` (FR-6 sub-step 3) — macros gain `to_bytes_block`, `from_bytes_block`, `coerce_block`, `setattr_block`, `clone_block`, `eq_repr_block`. Each block consumes precomputed numeric primitives from the view and emits the helper body skeleton. The transitional `helper_lines` field is removed. **Byte parity preserved.**
specs/010-jinja-template-migration/plan.md:321:    value_expr: str               # pre-rendered: literal form ("123U", "456ULL") or expression form
specs/010-jinja-template-migration/plan.md:324:class CppScalarAliasView:
specs/010-jinja-template-migration/plan.md:337:    # Literals (each pre-rendered as the C++ source text the template emits verbatim).
specs/010-jinja-template-migration/plan.md:386:    decl: str                     # pre-rendered field declaration line, e.g. "  std::uint32_t foo = 0;"
specs/010-jinja-template-migration/plan.md:389:    pack_bits: int                # byte_count * 8 (precomputed; FR-10 forbids template arithmetic)
specs/010-jinja-template-migration/plan.md:414:type CppTypeView = CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView
specs/010-jinja-template-migration/plan.md:436:**Critical:** templates render the `to_bytes`/`from_bytes` *helper skeletons* (the `for` loops, the `if signed { ... }` blocks, the `switch` on flag bit). The view supplies operand values, masks, and storage-type names. Helper bodies are NOT precomputed in Python.
specs/010-jinja-template-migration/plan.md:473:    sv_expr: str                  # pre-rendered SV literal or expression
specs/010-jinja-template-migration/plan.md:482:    sv_type_text: str             # pre-rendered, e.g. "logic signed [31:0]" or "logic [7:0]"
specs/010-jinja-template-migration/plan.md:510:# Pack/unpack functions are templated, not hidden as Python-built body strings.
specs/010-jinja-template-migration/plan.md:512:# the template iterates over. There are no pre-rendered function bodies; each
specs/010-jinja-template-migration/plan.md:562:type SvPackUnpackFnView = (
specs/010-jinja-template-migration/plan.md:575:    pack_unpack_fns: tuple[SvPackUnpackFnView, ...]
specs/010-jinja-template-migration/plan.md:693:| Jinja `trim_blocks`/`lstrip_blocks` interacting unexpectedly with literal-heavy template content (e.g., generated SV helper classes containing `begin`/`end` blocks) | Medium | When a literal-heavy block must be preserved verbatim, wrap it in `{% raw %}...{% endraw %}` or pass it through as a precomputed `str` field on the view (the `body_lines` mechanism). Phase 3 commit 4 explicitly tests this on the largest SV `_helper_class` block. |
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:22:This is iteration 3 of the planning stage. Iteration 2 returned `VERDICT: REVISE` with:
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:24:1. BLOCKING — `tuple[str, ...] | None` violates FR-8.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:25:2. BLOCKING — C++ byte-parity issues in `CppNamespaceView` (nested `piketype`) and `standard_includes` (alphabetization claim).
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:26:3. BLOCKING — C++/SV view-model dataclasses still under-specified.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:46:End with `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:48:Bias APPROVE: only one round of REVISE remains in the maxIterations budget.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:221:    value_expr: str               # pre-rendered Python expression, e.g. "(1 << 32)" or "MAX_VALUE"
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:240:    resolved_value_expr: str      # pre-rendered, e.g. "0", "16"
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:273:    annotation: str               # pre-rendered "int", "bytes", "addr_ct | None"
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:274:    default_expr: str             # pre-rendered "0", 'b"\\x00" * 4', "field(default_factory=foo_ct)"
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:276:    pack_bits: int                # byte_count * 8 (precomputed; FR-10 forbids template arithmetic on this)
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:309:    header: str                                  # full pre-rendered header line (FR-13)
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:340:This is **iteration 2** of the planning stage. Iteration 1 returned `VERDICT: REVISE` with 5 BLOCKING and 3 WARNING issues:
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:342:1. BLOCKING — Phase 1-3 commits ordered by type family, not FR-6 sub-step.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:343:2. BLOCKING — Python view-model sketch incomplete; FlagsFieldView referenced but not defined.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:344:3. BLOCKING — C++ plan precomputed full pack/unpack helper bodies in Python (violates FR-10/NFR-5).
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:345:4. BLOCKING — C++/SV view sketches were "same shape as Phase 1", not actionable.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:346:5. BLOCKING — Byte-parity strategy underspecified for intermediate commits.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:383:- `VERDICT: APPROVE` or `VERDICT: REVISE` on the final line. No text after.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:385:Bias toward APPROVE when no BLOCKING remains and the plan is concretely actionable.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:557:    value_expr: str               # pre-rendered Python expression, e.g. "(1 << 32)" or "MAX_VALUE"
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:576:    resolved_value_expr: str      # pre-rendered, e.g. "0", "16"
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:850:./specs/010-jinja-template-migration/plan.md:283:4. `feat(py): helper-method skeletons via templates` (FR-6 sub-step 3) — macros gain `to_bytes_block`, `from_bytes_block`, `coerce_block`, `setattr_block`, `clone_block`, `eq_repr_block`. Each block consumes precomputed numeric primitives from the view and emits the helper body skeleton. The transitional `helper_lines` field is removed. **Byte parity preserved.**
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:1568:./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:26:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:1737:./specs/010-jinja-template-migration/artifacts/planning/iter3-forge.md:283:4. `feat(py): helper-method skeletons via templates` (FR-6 sub-step 3) — macros gain `to_bytes_block`, `from_bytes_block`, `coerce_block`, `setattr_block`, `clone_block`, `eq_repr_block`. Each block consumes precomputed numeric primitives from the view and emits the helper body skeleton. The transitional `helper_lines` field is removed. **Byte parity preserved.**
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:1778:./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:279:4. `feat(py): helper-method skeletons via templates` (FR-6 sub-step 3) — macros gain `to_bytes_block`, `from_bytes_block`, `coerce_block`, `setattr_block`, `clone_block`, `eq_repr_block`. Each block consumes precomputed numeric primitives from the view and emits the helper body skeleton. The transitional `helper_lines` field is removed. **Byte parity preserved.**
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:1816:./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:305:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:2572:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1492:./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:26:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:2603:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1529:./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:305:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:2796:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1726:./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge-prompt.md:7:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3015:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2179:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5356:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3016:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2180:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5358:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3018:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2184:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5380:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3019:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2185:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5382:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3168:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2364:./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-gauge.md:3:**BLOCKING:** Task 10 claims AC-1 through AC-14 are verified, but the listed commands do not directly verify AC-2 (golden diff), AC-5 (discovery accept/reject), AC-6 (Generated by piketype header), AC-7 (piketype_runtime* names), AC-8 (piketype_manifest.json), or AC-10 (C++ namespace/guard). Add explicit checks.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3221:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2480:   279	4. `feat(py): helper-method skeletons via templates` (FR-6 sub-step 3) — macros gain `to_bytes_block`, `from_bytes_block`, `coerce_block`, `setattr_block`, `clone_block`, `eq_repr_block`. Each block consumes precomputed numeric primitives from the view and emits the helper body skeleton. The transitional `helper_lines` field is removed. **Byte parity preserved.**
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3257:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3341:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3258:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3343:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3260:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3365:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3261:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3367:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3287:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6262:2. **BLOCKING — FR-7 / C++ byte parity.** `CppNamespaceView` examples use nested namespace lines and include `piketype` in `qualified` (`plan.md:298-302`), but the current emitter emits one C++17 namespace line and filters out `piketype`. Also `standard_includes` says sorted at `339`, which can reorder the current `<cstdint>`-first output. Pin the view to the exact current namespace string/open/close and include order.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3289:./specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6292:2. **BLOCKING — FR-7 / C++ byte parity.** `CppNamespaceView` examples use nested namespace lines and include `piketype` in `qualified` (`plan.md:298-302`), but the current emitter emits one C++17 namespace line and filters out `piketype`. Also `standard_includes` says sorted at `339`, which can reorder the current `<cstdint>`-first output. Pin the view to the exact current namespace string/open/close and include order.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3369:./specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:25:2. BLOCKING — C++ byte-parity issues in `CppNamespaceView` (nested `piketype`) and `standard_includes` (alphabetization claim).
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3373:./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge-prompt.md:7:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3374:./specs/008-enum-dsl-type/artifacts/specification/iter3-gauge.md:3:**BLOCKING**: C++20 defaulted equality still mandated while constitution targets C++17. Existing pattern claim is factually true (scalar and struct wrappers already emit it), but does not resolve the spec/constitution conflict. Either change the project target to C++20 or require a manual C++17 equality operator.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3666:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5356:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3667:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5358:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3669:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5380:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3670:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5382:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:3761:./specs/010-jinja-template-migration/artifacts/planning/iter3-gauge-prompt.md:6:2. BLOCKING — C++ byte-parity issues in `CppNamespaceView` (nested `piketype`) and `standard_includes` (alphabetization claim).
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:4002:./specs/008-enum-dsl-type/artifacts/planning/iter3-gauge.md:3:**BLOCKING**: Empty enum with inferred width has no valid path. Freeze computes width from `max_value.bit_length()` but with zero members, `max_value` doesn't exist. Freeze must handle empty enums gracefully (emit width=0, let validation reject).
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:4062:./specs/008-enum-dsl-type/artifacts/task_breakdown/iter1-gauge.md:7:**BLOCKING**: Tasks 6-9 use inline emitters vs Jinja2 templates. (Forge disagrees — approved plan explicitly addresses this as following existing pattern.)
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:4170:./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-gauge.md:3:**BLOCKING:** Task 10 claims AC-1 through AC-14 are verified, but the listed commands do not directly verify AC-2 (golden diff), AC-5 (discovery accept/reject), AC-6 (Generated by piketype header), AC-7 (piketype_runtime* names), AC-8 (piketype_manifest.json), or AC-10 (C++ namespace/guard). Add explicit checks.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:4209:./specs/007-struct-flags-member/artifacts/planning/iter1-gauge.md:9:- **BLOCKING:** C++ Flags `from_bytes` is an instance method, not a static factory. Plan says `<FlagsClass>::from_bytes(...)` which would emit invalid C++.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:4435:      Review criteria: spec coverage, architecture soundness, simplicity, risk assessment, testing strategy, alignment with constitution. End with `VERDICT: APPROVE` or `VERDICT: REVISE`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:4440:   h. If **APPROVE**: break loop. If **REVISE**: critically evaluate feedback against constitution, incorporate valid points, and loop.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5060:/bin/zsh -lc 'rg -n "body_lines|has_body_lines|CppNamespaceView|standard_includes|Cpp.*View|Sv.*View|render context|dict context|Helper|typedef|VERDICT|BLOCKING|WARNING" specs/010-jinja-template-migration/plan.md specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md' in /Users/ezchi/Projects/pike-type
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5074:specs/010-jinja-template-migration/plan.md:324:class CppScalarAliasView:
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5084:specs/010-jinja-template-migration/plan.md:402:type CppTypeView = CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5094:specs/010-jinja-template-migration/plan.md:424:**Critical:** templates render the `to_bytes`/`from_bytes` *helper skeletons* (the `for` loops, the `if signed { ... }` blocks, the `switch` on flag bit). The view supplies operand values, masks, and storage-type names. Helper bodies are NOT precomputed in Python.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5108:specs/010-jinja-template-migration/plan.md:499:class SvPackUnpackFnView:
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5112:specs/010-jinja-template-migration/plan.md:510:    pack_unpack_fns: tuple[SvPackUnpackFnView, ...]
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5139:specs/010-jinja-template-migration/plan.md:628:| Jinja `trim_blocks`/`lstrip_blocks` interacting unexpectedly with literal-heavy template content (e.g., generated SV helper classes containing `begin`/`end` blocks) | Medium | When a literal-heavy block must be preserved verbatim, wrap it in `{% raw %}...{% endraw %}` or pass it through as a precomputed `str` field on the view (the `body_lines` mechanism). Phase 3 commit 4 explicitly tests this on the largest SV `_helper_class` block. |
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5140:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:22:This is **iteration 2** of the planning stage. Iteration 1 returned `VERDICT: REVISE` with 5 BLOCKING and 3 WARNING issues:
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5141:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:24:1. BLOCKING — Phase 1-3 commits ordered by type family, not FR-6 sub-step.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5142:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:25:2. BLOCKING — Python view-model sketch incomplete; FlagsFieldView referenced but not defined.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5143:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:26:3. BLOCKING — C++ plan precomputed full pack/unpack helper bodies in Python (violates FR-10/NFR-5).
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5144:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:27:4. BLOCKING — C++/SV view sketches were "same shape as Phase 1", not actionable.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5145:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:28:5. BLOCKING — Byte-parity strategy underspecified for intermediate commits.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5150:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:65:- `VERDICT: APPROVE` or `VERDICT: REVISE` on the final line. No text after.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5151:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:67:Bias toward APPROVE when no BLOCKING remains and the plan is concretely actionable.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5157:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:387:      Review criteria: spec coverage, architecture soundness, simplicity, risk assessment, testing strategy, alignment with constitution. End with `VERDICT: APPROVE` or `VERDICT: REVISE`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5160:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:724:- Numbered issue list with severity (`BLOCKING`/`WARNING`/`NOTE`), the FR/AC/phase/commit identifier, the problem, and a suggested fix.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5161:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:725:- Final line: exactly `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5162:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:727:A plan can be APPROVED with open `WARNING`/`NOTE` items as long as no `BLOCKING` issue remains.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5163:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:783:      Review criteria: spec coverage, architecture soundness, simplicity, risk assessment, testing strategy, alignment with constitution. End with `VERDICT: APPROVE` or `VERDICT: REVISE`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5225:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1244:./specs/010-jinja-template-migration/plan.md:341:    types: tuple[TypeView, ...]          # CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5227:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1246:./specs/010-jinja-template-migration/plan.md:345:`CppScalarAliasView`, `CppEnumView`, `CppFlagsView` follow the same shape pattern as Python's: precomputed primitives + literal strings, no IR refs, no methods.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5238:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1258:./specs/010-jinja-template-migration/plan.md:485:| Jinja `trim_blocks`/`lstrip_blocks` interacting unexpectedly with literal-heavy template content (e.g., generated SV helper classes containing `begin`/`end` blocks) | Medium | When a literal-heavy block must be preserved verbatim, wrap it in `{% raw %}...{% endraw %}` or pass it through as a precomputed `str` field on the view (the `body_lines` mechanism). Phase 3 commit 4 explicitly tests this on the largest SV `_helper_class` block. |
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5239:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1492:./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge.md:26:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5240:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1529:./specs/010-jinja-template-migration/artifacts/specification/iter4-gauge.md:305:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5242:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1726:./specs/010-jinja-template-migration/artifacts/specification/iter3-gauge-prompt.md:7:1. BLOCKING — NFR-1/AC-F4/AC-F5: spec referenced a nonexistent `gen_main` and an unsupported `--repo` flag. The actual CLI is `piketype gen [--namespace NS] <dsl-file>`; the programmatic entry is `piketype.commands.gen.run_gen(path: str, *, namespace: str | None = None)`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5255:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1819:./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:341:    types: tuple[TypeView, ...]          # CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5257:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1821:./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:345:`CppScalarAliasView`, `CppEnumView`, `CppFlagsView` follow the same shape pattern as Python's: precomputed primitives + literal strings, no IR refs, no methods.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5268:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:1833:./specs/010-jinja-template-migration/artifacts/planning/iter2-forge.md:485:| Jinja `trim_blocks`/`lstrip_blocks` interacting unexpectedly with literal-heavy template content (e.g., generated SV helper classes containing `begin`/`end` blocks) | Medium | When a literal-heavy block must be preserved verbatim, wrap it in `{% raw %}...{% endraw %}` or pass it through as a precomputed `str` field on the view (the `body_lines` mechanism). Phase 3 commit 4 explicitly tests this on the largest SV `_helper_class` block. |
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5344:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2178:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5354:2. **BLOCKING — FR-8 / FR-10 / FR-18 / Phase 1 view model.** The Python view sketch is incomplete. Current Python rendering needs enum class name, enum wrapper width/byte_count/first member/mask, flags field masks/data mask, struct field min/max, padding bits, sign-bit index, and target kind for type refs. `FlagsFieldView` is referenced but not defined. Fix by expanding the sketch into concrete dataclasses that cover every value used by current `_render_py_*` helpers.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5345:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2179:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5356:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5346:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2180:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5358:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5348:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2183:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5378:2. **BLOCKING — FR-8 / FR-10 / FR-18 / Phase 1 view model.** The Python view sketch is incomplete. Current Python rendering needs enum class name, enum wrapper width/byte_count/first member/mask, flags field masks/data mask, struct field min/max, padding bits, sign-bit index, and target kind for type refs. `FlagsFieldView` is referenced but not defined. Fix by expanding the sketch into concrete dataclasses that cover every value used by current `_render_py_*` helpers.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5349:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2184:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5380:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5350:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2185:./specs/010-jinja-template-migration/artifacts/planning/iter1-gauge.md:5382:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5354:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2364:./specs/006-rename-to-pike-type/artifacts/task_breakdown/iter1-gauge.md:3:**BLOCKING:** Task 10 claims AC-1 through AC-14 are verified, but the listed commands do not directly verify AC-2 (golden diff), AC-5 (discovery accept/reject), AC-6 (Generated by piketype header), AC-7 (piketype_runtime* names), AC-8 (piketype_manifest.json), or AC-10 (C++ namespace/guard). Add explicit checks.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5367:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2542:   341	    types: tuple[TypeView, ...]          # CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5369:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2546:   345	`CppScalarAliasView`, `CppEnumView`, `CppFlagsView` follow the same shape pattern as Python's: precomputed primitives + literal strings, no IR refs, no methods.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5370:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2548:   347	**Critical:** templates render the `to_bytes`/`from_bytes` *helper skeletons* (the `for` loops, the `if signed { ... }` blocks, the `switch` on flag bit). The view supplies operand values, masks, and storage-type names. Helper bodies are NOT precomputed in Python.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5391:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:2686:   485	| Jinja `trim_blocks`/`lstrip_blocks` interacting unexpectedly with literal-heavy template content (e.g., generated SV helper classes containing `begin`/`end` blocks) | Medium | When a literal-heavy block must be preserved verbatim, wrap it in `{% raw %}...{% endraw %}` or pass it through as a precomputed `str` field on the view (the `body_lines` mechanism). Phase 3 commit 4 explicitly tests this on the largest SV `_helper_class` block. |
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5397:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3139:    64	- Numbered issue list with severity (`BLOCKING`/`WARNING`/`NOTE`), the FR/AC/phase/commit identifier, the problem, and a suggested fix.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5398:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3140:    65	- Final line: exactly `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5399:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3142:    67	A plan can be APPROVED with open `WARNING`/`NOTE` items as long as no `BLOCKING` issue remains.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5400:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3198:   123	      Review criteria: spec coverage, architecture soundness, simplicity, risk assessment, testing strategy, alignment with constitution. End with `VERDICT: APPROVE` or `VERDICT: REVISE`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5401:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3337:1. **BLOCKING — FR-6 / CL-1 / Phase 1-3 commit sequences.** The backend commits migrate by type family (`scalar`, then `struct`, then `enum/flags`) instead of the required sub-order: module skeleton → top-level type declaration skeletons → helper-method skeletons → expression/field fragments. That violates the spec’s required migration order. Fix by restructuring each backend block around FR-6 sub-steps, not type families.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5402:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3339:2. **BLOCKING — FR-8 / FR-10 / FR-18 / Phase 1 view model.** The Python view sketch is incomplete. Current Python rendering needs enum class name, enum wrapper width/byte_count/first member/mask, flags field masks/data mask, struct field min/max, padding bits, sign-bit index, and target kind for type refs. `FlagsFieldView` is referenced but not defined. Fix by expanding the sketch into concrete dataclasses that cover every value used by current `_render_py_*` helpers.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5403:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3341:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5404:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3343:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5405:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3345:5. **BLOCKING — FR-7 / FR-20 / Phase 1 commits 2-5.** The byte-parity strategy is underspecified. “Template renders header/imports/footer; rest inline” and partial type migration can work only if the plan defines temporary legacy body/type fragments and how ordering is preserved. Fix by either documenting a temporary `InlineFragmentView` strategy with per-commit golden checks, or state that intermediate commits are internal refactors and parity is checked only at backend completion.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5409:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3355:VERDICT: REVISE
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5410:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3361:1. **BLOCKING — FR-6 / CL-1 / Phase 1-3 commit sequences.** The backend commits migrate by type family (`scalar`, then `struct`, then `enum/flags`) instead of the required sub-order: module skeleton → top-level type declaration skeletons → helper-method skeletons → expression/field fragments. That violates the spec’s required migration order. Fix by restructuring each backend block around FR-6 sub-steps, not type families.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5411:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3363:2. **BLOCKING — FR-8 / FR-10 / FR-18 / Phase 1 view model.** The Python view sketch is incomplete. Current Python rendering needs enum class name, enum wrapper width/byte_count/first member/mask, flags field masks/data mask, struct field min/max, padding bits, sign-bit index, and target kind for type refs. `FlagsFieldView` is referenced but not defined. Fix by expanding the sketch into concrete dataclasses that cover every value used by current `_render_py_*` helpers.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5412:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3365:3. **BLOCKING — FR-6 / FR-10 / NFR-5 / Phase 2.** The C++ plan says the view should precompute “full pack/unpack helper bodies.” That hides meaningful generated structure in Python, directly conflicting with template-first generation. Fix by moving helper skeletons into templates and passing only primitive fields/fragments such as masks, storage types, byte counts, guard, namespace open/close strings, enum defaults, field declarations, and literal spellings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5413:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3367:4. **BLOCKING — FR-18 / Phase 2-3 concrete actionability.** C++ and SV view models are not specified enough. “Same shape as Phase 1” does not tell an implementer what fields to build for namespaces, constants, enum wrappers, flags, struct padding, SV localparams, `_pkg`/`_test_pkg`, helper classes, pack/unpack steps, or byte serialization. Fix by adding backend-specific dataclass sketches comparable to the Python sketch.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5414:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3369:5. **BLOCKING — FR-7 / FR-20 / Phase 1 commits 2-5.** The byte-parity strategy is underspecified. “Template renders header/imports/footer; rest inline” and partial type migration can work only if the plan defines temporary legacy body/type fragments and how ordering is preserved. Fix by either documenting a temporary `InlineFragmentView` strategy with per-commit golden checks, or state that intermediate commits are internal refactors and parity is checked only at backend completion.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5418:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:3379:VERDICT: REVISE
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5480:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6256:Phase 1 parity check: Commit 2 preserves the full legacy body through `body_lines`; commit 3 keeps helper bodies as per-type passthrough strings; commit 4 moves helper skeletons while consuming precomputed primitives; commit 5 moves fragments and retires `body_lines`; commit 6 deletes dead helpers after template output owns the backend. That sequence is coherent.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5481:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6260:1. **BLOCKING — FR-8 / Phase 1-3 transitional views.** `body_lines: tuple[str, ...] | None` appears in the Python, C++, and SV view sketches (`plan.md:44`, `250-260`, `331-343`, `396-438`). FR-8 does not allow `None` as a view-model field type. Fix by using `body_lines: tuple[str, ...]` with an empty tuple sentinel, optionally plus a primitive `has_body_lines: bool`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5482:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6262:2. **BLOCKING — FR-7 / C++ byte parity.** `CppNamespaceView` examples use nested namespace lines and include `piketype` in `qualified` (`plan.md:298-302`), but the current emitter emits one C++17 namespace line and filters out `piketype`. Also `standard_includes` says sorted at `339`, which can reorder the current `<cstdint>`-first output. Pin the view to the exact current namespace string/open/close and include order.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5483:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6264:3. **BLOCKING — FR-18 / FR-10 / Phase 2-3 view-model completeness.** `CppScalarAliasView`, `CppEnumView`, `CppFlagsView`, and `CppStructView` are not explicitly defined (`plan.md:345`). SV also lacks final structured views for synth pack/unpack and test helper to/from-bytes steps; `pack_unpack_blocks` is only transitional. Add concrete dataclasses for every primitive, literal, discriminator, padding value, and loop bound the templates need.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5485:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6268:VERDICT: REVISE
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5487:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6286:Phase 1 parity check: Commit 2 preserves the full legacy body through `body_lines`; commit 3 keeps helper bodies as per-type passthrough strings; commit 4 moves helper skeletons while consuming precomputed primitives; commit 5 moves fragments and retires `body_lines`; commit 6 deletes dead helpers after template output owns the backend. That sequence is coherent.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5488:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6290:1. **BLOCKING — FR-8 / Phase 1-3 transitional views.** `body_lines: tuple[str, ...] | None` appears in the Python, C++, and SV view sketches (`plan.md:44`, `250-260`, `331-343`, `396-438`). FR-8 does not allow `None` as a view-model field type. Fix by using `body_lines: tuple[str, ...]` with an empty tuple sentinel, optionally plus a primitive `has_body_lines: bool`.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5489:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6292:2. **BLOCKING — FR-7 / C++ byte parity.** `CppNamespaceView` examples use nested namespace lines and include `piketype` in `qualified` (`plan.md:298-302`), but the current emitter emits one C++17 namespace line and filters out `piketype`. Also `standard_includes` says sorted at `339`, which can reorder the current `<cstdint>`-first output. Pin the view to the exact current namespace string/open/close and include order.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5490:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6294:3. **BLOCKING — FR-18 / FR-10 / Phase 2-3 view-model completeness.** `CppScalarAliasView`, `CppEnumView`, `CppFlagsView`, and `CppStructView` are not explicitly defined (`plan.md:345`). SV also lacks final structured views for synth pack/unpack and test helper to/from-bytes steps; `pack_unpack_blocks` is only transitional. Add concrete dataclasses for every primitive, literal, discriminator, padding value, and loop bound the templates need.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5492:specs/010-jinja-template-migration/artifacts/planning/iter2-gauge.md:6298:VERDICT: REVISE
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5526:   255	    header: str                                  # full pre-rendered header line (FR-13)
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5554:   283	4. `feat(py): helper-method skeletons via templates` (FR-6 sub-step 3) — macros gain `to_bytes_block`, `from_bytes_block`, `coerce_block`, `setattr_block`, `clone_block`, `eq_repr_block`. Each block consumes precomputed numeric primitives from the view and emits the helper body skeleton. The transitional `helper_lines` field is removed. **Byte parity preserved.**
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5592:   321	    value_expr: str               # pre-rendered: literal form ("123U", "456ULL") or expression form
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5595:   324	class CppScalarAliasView:
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5602:   331	    min_value_literal: str        # pre-rendered C++ literal
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5645:   374	    decl: str                     # pre-rendered field declaration line, e.g. "  std::uint32_t foo = 0;"
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5648:   377	    pack_bits: int                # byte_count * 8 (precomputed; FR-10 forbids template arithmetic)
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5673:   402	type CppTypeView = CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5695:   424	**Critical:** templates render the `to_bytes`/`from_bytes` *helper skeletons* (the `for` loops, the `if signed { ... }` blocks, the `switch` on flag bit). The view supplies operand values, masks, and storage-type names. Helper bodies are NOT precomputed in Python.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5732:   461	    sv_expr: str                  # pre-rendered SV literal or expression
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5741:   470	    sv_type_text: str             # pre-rendered, e.g. "logic signed [31:0]" or "logic [7:0]"
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5770:   499	class SvPackUnpackFnView:
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5772:   501	    pack_lines: tuple[str, ...]   # pre-rendered body of pack function (precomputed strings; templates render the function header + body iteration)
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5773:   502	    unpack_lines: tuple[str, ...] # likewise
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5781:   510	    pack_unpack_fns: tuple[SvPackUnpackFnView, ...]
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:5899:   628	| Jinja `trim_blocks`/`lstrip_blocks` interacting unexpectedly with literal-heavy template content (e.g., generated SV helper classes containing `begin`/`end` blocks) | Medium | When a literal-heavy block must be preserved verbatim, wrap it in `{% raw %}...{% endraw %}` or pass it through as a precomputed `str` field on the view (the `body_lines` mechanism). Phase 3 commit 4 explicitly tests this on the largest SV `_helper_class` block. |
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:7860:219:    annotation: str               # pre-rendered "int", "bytes", "addr_ct | None"
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:7881:501:    pack_lines: tuple[str, ...]   # pre-rendered body of pack function (precomputed strings; templates render the function header + body iteration)
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:7882:502:    unpack_lines: tuple[str, ...] # likewise
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:7885:510:    pack_unpack_fns: tuple[SvPackUnpackFnView, ...]
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:7999:1. **BLOCKING — FR-8 / Phase 1 commit 5.** `plan.md:284` still says `body_lines` is “always `None`”. That contradicts the iter3 tuple-plus-bool mechanism and FR-8. It must say empty tuple with `has_body_lines=False`, then removal.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:8001:2. **BLOCKING — FR-6 / FR-10 / NFR-5 / SV view model.** `SvPackUnpackFnView` still uses `pack_lines` / `unpack_lines` as pre-rendered function bodies (`plan.md:499-502`). Pack/unpack helper structure is meaningful output and must be templated, not hidden as Python-built body strings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:8003:3. **BLOCKING — FR-18 / C++ byte parity.** The C++ dataclasses are explicit, but still miss primitives needed to reproduce current helper branches without Jinja arithmetic: e.g. signed padding branch booleans, byte-total mask literal, and full-range literal for scalar and inline scalar helpers. Implementers would have to derive these in templates or Python body strings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:8007:VERDICT: REVISE
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:8011:1. **BLOCKING — FR-8 / Phase 1 commit 5.** `plan.md:284` still says `body_lines` is “always `None`”. That contradicts the iter3 tuple-plus-bool mechanism and FR-8. It must say empty tuple with `has_body_lines=False`, then removal.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:8013:2. **BLOCKING — FR-6 / FR-10 / NFR-5 / SV view model.** `SvPackUnpackFnView` still uses `pack_lines` / `unpack_lines` as pre-rendered function bodies (`plan.md:499-502`). Pack/unpack helper structure is meaningful output and must be templated, not hidden as Python-built body strings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:8015:3. **BLOCKING — FR-18 / C++ byte parity.** The C++ dataclasses are explicit, but still miss primitives needed to reproduce current helper branches without Jinja arithmetic: e.g. signed padding branch booleans, byte-total mask literal, and full-range literal for scalar and inline scalar helpers. Implementers would have to derive these in templates or Python body strings.
specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md:8019:VERDICT: REVISE

codex
The three explicit fixes are present in the plan at the expected locations. I’m doing one pass for contradictions, especially places where the plan still allows pre-rendered helper bodies or asks templates to derive branch logic.
exec
/bin/zsh -lc "sed -n '436,465p' specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '370,435p' specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '500,565p' specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:

@dataclass(frozen=True, slots=True)
class CppFlagsView:
    class_name: str
    num_flags: int
    total_width: int              # num_flags + alignment_bits
    byte_count: int
    storage_bits: int             # byte_count * 8
    storage_type: str             # smallest unsigned scalar type wide enough; or "std::vector<std::uint8_t>" if storage_bits > 64
    is_wide: bool                 # storage_bits > 64
    data_mask_literal: str
    fields: tuple[CppFlagFieldView, ...]

@dataclass(frozen=True, slots=True)
class CppStructFieldView:
    name: str
    decl: str                     # pre-rendered field declaration line, e.g. "  std::uint32_t foo = 0;"
    field_type_str: str           # "std::uint32_t", "std::vector<std::uint8_t>", "alpha_ct"
    byte_count: int
    pack_bits: int                # byte_count * 8 (precomputed; FR-10 forbids template arithmetic)
    is_struct_ref: bool
    is_flags_ref: bool
    is_enum_ref: bool
    is_scalar_ref: bool
    is_narrow_scalar: bool
    is_wide_scalar: bool
    target_class: str             # "" if scalar spec
    width: int
    signed: bool
    min_value_literal: str
    max_value_literal: str
    mask_literal: str
    sign_bit_literal: str
    msb_byte_mask_literal: str

@dataclass(frozen=True, slots=True)
class CppStructView:
    class_name: str
    width: int
    byte_count: int
    alignment_bytes: int
    has_struct_field: bool
    fields: tuple[CppStructFieldView, ...]

type CppTypeView = CppScalarAliasView | CppStructView | CppEnumView | CppFlagsView

@dataclass(frozen=True, slots=True)
class CppModuleView:
    header: str
    guard: CppGuardView
    namespace: CppNamespaceView
    has_types: bool
    has_structs: bool
    has_enums: bool
    has_flags: bool
    # Includes follow the EXACT current emitter order — NOT alphabetized:
    #   ["<cstdint>"]  always, even when has_types is False
    #   plus ["<cstddef>", "<stdexcept>", "<vector>"]  when has_types is True
    # The template iterates standard_includes in slot order; the view encodes the order verbatim.
    standard_includes: tuple[str, ...]
    constants: tuple[CppConstantView, ...]
    types: tuple[CppTypeView, ...]
    body_lines: tuple[str, ...]   # transitional, FR-8 compliant
    has_body_lines: bool
```


 succeeded in 0ms:
**Critical:** templates render the `to_bytes`/`from_bytes` *helper skeletons* (the `for` loops, the `if signed { ... }` blocks, the `switch` on flag bit). The view supplies operand values, masks, and storage-type names. Helper bodies are NOT precomputed in Python.

**`--namespace` CLI override:** the namespace builder respects `emit_cpp(repo, *, namespace=None)`. The view's `CppNamespaceView` is constructed by the same logic as the current emitter (`render_module_hpp` lines 50–55):

- Override path: `qualified = f"{namespace}::{basename}"`; `guard = f"{namespace.replace('::', '_')}_{basename}_types_hpp".upper()`.
- Default path: `qualified = "::".join(p for p in namespace_parts if p != "piketype")`; `guard = "_".join((*namespace_parts, "types_hpp")).upper().replace(".", "_")`.
- `has_namespace = qualified != ""`. If False, `open_line` and `close_line` are empty strings and the template skips them.

`tests/test_view_cpp.py` includes the namespace-override fixture (`tests/fixtures/namespace_override`) end-to-end, asserting the rendered guard macro and namespace open/close strings.

**Commit sequence (Phase 2):** same FR-6 sub-step structure as Phase 1 — 7 commits.

1. `feat(cpp): introduce CppModuleView dataclasses and builders`.
2. `feat(cpp): module skeleton via templates` (header, guard open, includes, namespace open, namespace close, guard close).
3. `feat(cpp): top-level class scaffolding via templates`.
4. `feat(cpp): helper-method skeletons via templates` (pack/unpack loops, scalar inline helpers).
5. `feat(cpp): expression and field-level fragments via templates`.
6. `refactor(cpp): remove inline emitter helpers`.
7. `steel(perf): record cpp-complete perf row`.

**Phase 2 gates:** AC-1-Cpp..AC-7-Cpp.

---

## Phase 3 — SystemVerilog backend migration

Same FR-6 sub-step structure. Two output files per module: `<basename>_pkg.sv` (synth) and `<basename>_test_pkg.sv` (verification). Two primary templates.

**Files:** `src/piketype/backends/sv/view.py`, `templates/{module_synth.j2,module_test.j2,_macros.j2}`, `tests/test_view_sv.py`.


 succeeded in 0ms:
    width: int                    # num_flags

@dataclass(frozen=True, slots=True)
class SvEnumTypedefView:
    name: str                     # enum typedef name
    underlying_width: int
    members: tuple[tuple[str, str], ...]   # (name, value_expr) pairs in declaration order

type SvTypedefView = SvScalarAliasTypedefView | SvStructTypedefView | SvFlagsTypedefView | SvEnumTypedefView

# Pack/unpack functions are templated, not hidden as Python-built body strings.
# Each variant exposes the discriminators and per-field/per-flag step data that
# the template iterates over. There are no pre-rendered function bodies; each
# function body is reconstructed by the template from these primitives.

@dataclass(frozen=True, slots=True)
class SvPackUnpackScalarView:
    # ScalarAlias: pack body is `return a;`, unpack body is `return a;`.
    type_name: str
    base: str                     # _type_base_name(type_name)
    upper_base: str               # base.upper()

@dataclass(frozen=True, slots=True)
class SvPackUnpackFlagsView:
    type_name: str
    base: str
    upper_base: str
    # MSB-first declaration order; pack concatenates `a.<name>` left-to-right.
    flag_names_for_pack: tuple[str, ...]
    # For unpack: `result.<name> = a[<bit_index>];` where bit_index is the
    # reversed-iteration position (matches current emitter line 263).
    unpack_assignments: tuple[tuple[str, int], ...]   # (flag_name, bit_index)

@dataclass(frozen=True, slots=True)
class SvPackUnpackEnumView:
    type_name: str
    base: str
    upper_base: str

@dataclass(frozen=True, slots=True)
class SvPackUnpackStructFieldView:
    name: str
    width: int                    # field data width
    is_type_ref: bool
    inner_base: str               # _type_base_name(target.name) when is_type_ref else ""
    inner_upper: str              # inner_base.upper() when is_type_ref else ""
    has_signed_padding: bool      # field.padding_bits > 0 and field is signed
    padding_bits: int             # field.padding_bits when has_signed_padding else 0
    sign_bit_index: int           # data_width - 1 when has_signed_padding else 0

@dataclass(frozen=True, slots=True)
class SvPackUnpackStructView:
    type_name: str
    base: str
    upper_base: str
    # Pack concatenates fields in declaration order with `pack_<inner>(a.<name>)`
    # for type refs, else `a.<name>`.
    pack_field_parts: tuple[tuple[str, str], ...]   # (name, op) where op is "ref" or "scalar"
    pack_inner_bases: tuple[str, ...]               # parallel to pack_field_parts: inner_base or "" if scalar
    # Unpack iterates fields in REVERSED order (matches current emitter line 284).
    unpack_fields: tuple[SvPackUnpackStructFieldView, ...]

type SvPackUnpackFnView = (
    SvPackUnpackScalarView
    | SvPackUnpackFlagsView
    | SvPackUnpackEnumView

exec
/bin/zsh -lc "rg -n \"always None|\\| None|pack_lines|unpack_lines|pre-rendered function bod|helper bod(y|ies).*precomputed|precomputed.*helper bod(y|ies)|full pack/unpack|body_lines: tuple\\[str, \\.\\.\\.\\] \\| None|alphabet|nested namespace|piketype.*qualified\" specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
219:    annotation: str               # pre-rendered "int", "bytes", "addr_ct | None"
283:4. `feat(py): helper-method skeletons via templates` (FR-6 sub-step 3) — macros gain `to_bytes_block`, `from_bytes_block`, `coerce_block`, `setattr_block`, `clone_block`, `eq_repr_block`. Each block consumes precomputed numeric primitives from the view and emits the helper body skeleton. The transitional `helper_lines` field is removed. **Byte parity preserved.**
425:    # Includes follow the EXACT current emitter order — NOT alphabetized:
512:# the template iterates over. There are no pre-rendered function bodies; each

exec
/bin/zsh -lc "sed -n '120,280p' src/piketype/backends/cpp/emitter.py" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '520,760p' src/piketype/backends/cpp/emitter.py" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
        case _:
            raise ValidationError(f"unsupported C++ expression node {type(expr).__name__}")


# ---------------------------------------------------------------------------
# Scalar alias wrapper class
# ---------------------------------------------------------------------------


def _render_cpp_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
    """Render a C++ scalar wrapper class (big-endian serialization)."""
    class_name = _type_class_name(type_ir.name)
    bc = byte_count(type_ir.resolved_width)
    width = type_ir.resolved_width
    lines = [
        f"class {class_name} {{",
        " public:",
        f"  static constexpr std::size_t WIDTH = {width};",
        f"  static constexpr bool SIGNED = {'true' if type_ir.signed else 'false'};",
        f"  static constexpr std::size_t BYTE_COUNT = {bc};",
    ]
    if width <= 64:
        value_type = _cpp_scalar_value_type(width=width, signed=type_ir.signed)
        mask_literal = _cpp_unsigned_literal(
            (1 << width) - 1 if width < 64 else 2**64 - 1
        )
        lines.extend(
            [
                f"  using value_type = {value_type};",
                "  value_type value;",
            ]
        )
        if type_ir.signed:
            minimum = -(2 ** (width - 1))
            maximum = 2 ** (width - 1) - 1
            pad_bits = bc * 8 - width
            lines.extend(
                [
                    f"  static constexpr value_type MIN_VALUE = static_cast<value_type>({minimum});",
                    f"  static constexpr value_type MAX_VALUE = static_cast<value_type>({maximum});",
                    f"  static constexpr std::uint64_t MASK = {mask_literal};",
                    f"  {class_name}() : value(0) {{}}",
                    f"  {class_name}(value_type value_in) : value(validate_value(value_in)) {{}}",
                    "",
                    "  std::vector<std::uint8_t> to_bytes() const {",
                    "    std::vector<std::uint8_t> bytes(BYTE_COUNT, 0);",
                    "    std::uint64_t bits = static_cast<std::uint64_t>(value) & MASK;",
                ]
            )
            # Sign-extend into padding bits
            if pad_bits > 0:
                lines.extend(
                    [
                        f"    if (value < 0 && WIDTH < BYTE_COUNT * 8U) {{",
                        f"      for (std::size_t i = WIDTH; i < BYTE_COUNT * 8U; ++i) {{",
                        "        bits |= (1ULL << i);",
                        "      }",
                        "    }",
                    ]
                )
            lines.extend(
                [
                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
                    "      bytes[BYTE_COUNT - 1 - idx] = static_cast<std::uint8_t>((bits >> (8U * idx)) & 0xFFU);",
                    "    }",
                    "    return bytes;",
                    "  }",
                    "",
                    "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
                    "    if (bytes.size() != BYTE_COUNT) {",
                    '      throw std::invalid_argument("byte width mismatch");',
                    "    }",
                    "    std::uint64_t bits = 0;",
                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
                    "      bits = (bits << 8U) | bytes[idx];",
                    "    }",
                ]
            )
            # Validate sign extension in padding bits
            if pad_bits > 0:
                byte_mask = _cpp_unsigned_literal((1 << (bc * 8)) - 1 if bc * 8 < 64 else 2**64 - 1)
                lines.extend(
                    [
                        "    std::uint64_t data_bits = bits & MASK;",
                        f"    bool sign_bit = ((data_bits >> ({width - 1}U)) & 1U) != 0U;",
                        f"    std::uint64_t expected_pad = sign_bit ? (~MASK & {byte_mask}) : 0ULL;",
                        f"    if ((bits & ~MASK & {byte_mask}) != expected_pad) {{",
                        '      throw std::invalid_argument("signed padding mismatch");',
                        "    }",
                    ]
                )
            lines.extend(
                [
                    "    bits &= MASK;",
                    "    std::int64_t signed_value = static_cast<std::int64_t>(bits);",
                ]
            )
            if width < 64:
                sign_bit_lit = _cpp_unsigned_literal(1 << (width - 1))
                full_range_lit = _cpp_unsigned_literal(1 << width)
                lines.extend(
                    [
                        f"    if ((bits & {sign_bit_lit}) != 0U && WIDTH < 64) {{",
                        f"      signed_value -= static_cast<std::int64_t>({full_range_lit});",
                        "    }",
                    ]
                )
            lines.extend(
                [
                    "    value = validate_value(static_cast<value_type>(signed_value));",
                    "  }",
                    "",
                    f"  {class_name} clone() const {{",
                    f"    return {class_name}(value);",
                    "  }",
                    "",
                    "  operator value_type() const {",
                    "    return value;",
                    "  }",
                    "",
                    f"  bool operator==(const {class_name}& other) const = default;",
                    "",
                    " private:",
                    "  static value_type validate_value(value_type value_in) {",
                    "    if (value_in < MIN_VALUE || value_in > MAX_VALUE) {",
                    '      throw std::out_of_range("value out of range");',
                    "    }",
                    "    return value_in;",
                    "  }",
                    "};",
                ]
            )
        else:
            # Unsigned <= 64
            maximum = 2**width - 1 if width < 64 else 2**64 - 1
            lines.extend(
                [
                    f"  static constexpr std::uint64_t MASK = {mask_literal};",
                    f"  static constexpr value_type MAX_VALUE = static_cast<value_type>({_cpp_unsigned_literal(maximum)});",
                    f"  {class_name}() : value(0) {{}}",
                    f"  {class_name}(value_type value_in) : value(validate_value(value_in)) {{}}",
                    "",
                    "  std::vector<std::uint8_t> to_bytes() const {",
                    "    std::vector<std::uint8_t> bytes(BYTE_COUNT, 0);",
                    "    std::uint64_t bits = static_cast<std::uint64_t>(value);",
                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
                    "      bytes[BYTE_COUNT - 1 - idx] = static_cast<std::uint8_t>((bits >> (8U * idx)) & 0xFFU);",
                    "    }",
                    "    return bytes;",
                    "  }",
                    "",
                    "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
                    "    if (bytes.size() != BYTE_COUNT) {",
                    '      throw std::invalid_argument("byte width mismatch");',
                    "    }",
                    "    std::uint64_t bits = 0;",
                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
                    "      bits = (bits << 8U) | bytes[idx];",
                    "    }",
                    "    value = validate_value(static_cast<value_type>(bits & MASK));",
                    "  }",

 succeeded in 0ms:
            f"  {class_name} clone() const {{",
            f"    {class_name} cloned;",
            "    cloned.value = value;",
            "    return cloned;",
            "  }",
        ]
    )

    # operator==
    lines.extend(
        [
            "",
            f"  bool operator==(const {class_name}& other) const {{",
            f"    return (value & {data_mask_lit}) == (other.value & {data_mask_lit});",
            "  }",
            "};",
        ]
    )

    return lines


# ---------------------------------------------------------------------------
# Struct wrapper class
# ---------------------------------------------------------------------------


def _render_cpp_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
    """Render a C++ struct wrapper class (per-field byte-aligned, big-endian)."""
    class_name = _type_class_name(type_ir.name)
    data_width = _resolved_type_width(type_ir=type_ir, type_index=type_index)
    total_bc = _type_byte_count(type_ir=type_ir, type_index=type_index)
    lines = [
        f"class {class_name} {{",
        " public:",
        f"  static constexpr std::size_t WIDTH = {data_width};",
        f"  static constexpr std::size_t BYTE_COUNT = {total_bc};",
    ]
    for field_ir in type_ir.fields:
        lines.append(f"  {_render_cpp_field_decl(field_ir=field_ir, type_index=type_index)}")
    lines.extend(
        [
            "",
            f"  {class_name}() = default;",
            "",
            "  std::vector<std::uint8_t> to_bytes() const {",
            "    std::vector<std::uint8_t> bytes;",
            "    bytes.reserve(BYTE_COUNT);",
        ]
    )
    for field_ir in type_ir.fields:
        lines.extend(_render_cpp_struct_pack_step(field_ir=field_ir, type_index=type_index))
    if type_ir.alignment_bits > 0:
        align_bytes = type_ir.alignment_bits // 8
        lines.append(f"    for (std::size_t i = 0; i < {align_bytes}; ++i) bytes.push_back(0);")
    lines.extend(
        [
            "    return bytes;",
            "  }",
            "",
            "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
            "    if (bytes.size() != BYTE_COUNT) {",
            '      throw std::invalid_argument("byte width mismatch");',
            "    }",
            "    std::size_t offset = 0;",
        ]
    )
    for field_ir in type_ir.fields:
        lines.extend(_render_cpp_struct_unpack_step(field_ir=field_ir, type_index=type_index))
    lines.extend(
        [
            "  }",
            "",
            f"  {class_name} clone() const {{",
            f"    {class_name} cloned;",
        ]
    )
    for field_ir in type_ir.fields:
        if _is_struct_ref(field_type=field_ir.type_ir, type_index=type_index) or _is_scalar_ref(
            field_type=field_ir.type_ir, type_index=type_index
        ) or _is_flags_ref(field_type=field_ir.type_ir, type_index=type_index) or _is_enum_ref(
            field_type=field_ir.type_ir, type_index=type_index
        ):
            lines.append(f"    cloned.{field_ir.name} = {field_ir.name}.clone();")
        elif _is_wide_inline_scalar(field_type=field_ir.type_ir):
            lines.append(f"    cloned.{field_ir.name} = {field_ir.name};")
        else:
            lines.append(f"    cloned.{field_ir.name} = {field_ir.name};")
    lines.extend(
        [
            "    return cloned;",
            "  }",
            "",
            f"  bool operator==(const {class_name}& other) const = default;",
        ]
    )
    # Per-field encode/decode helpers
    all_helpers: list[str] = []
    for field_ir in type_ir.fields:
        helper_lines = _render_cpp_inline_scalar_helpers(owner_name=class_name, field_ir=field_ir)
        if helper_lines:
            if all_helpers:
                all_helpers.append("")
            all_helpers.extend(helper_lines)
    if all_helpers:
        lines.append("")
        lines.append(" private:")
        lines.extend(all_helpers)
    lines.append("};")
    return lines


# ---------------------------------------------------------------------------
# Field declarations
# ---------------------------------------------------------------------------


def _render_cpp_field_decl(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
    """Render one public C++ field declaration."""
    type_name = _render_cpp_field_type(field_ir=field_ir, type_index=type_index)
    default = _render_cpp_field_default(field_ir=field_ir, type_index=type_index)
    return f"{type_name} {field_ir.name}{default};"


def _render_cpp_field_type(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
    """Render one C++ field type."""
    match field_ir.type_ir:
        case TypeRefIR(name=name):
            return _type_class_name(type_index[name].name)
        case ScalarTypeSpecIR(signed=signed, resolved_width=resolved_width):
            if resolved_width <= 64:
                return _cpp_scalar_value_type(width=resolved_width, signed=signed)
            return "std::vector<std::uint8_t>"
        case _:
            raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")


def _render_cpp_field_default(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
    """Render one C++ field default initializer."""
    match field_ir.type_ir:
        case TypeRefIR():
            return "{}"
        case ScalarTypeSpecIR(resolved_width=resolved_width):
            if resolved_width <= 64:
                return " = 0"
            bc = byte_count(resolved_width)
            return f"{{std::vector<std::uint8_t>({bc}, 0U)}}"
        case _:
            raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")


# ---------------------------------------------------------------------------
# Struct to_bytes — per-field big-endian serialization
# ---------------------------------------------------------------------------


def _render_cpp_struct_pack_step(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
    """Render one C++ struct packing step (big-endian, per-field byte-aligned)."""
    lines: list[str] = []
    if isinstance(field_ir.type_ir, ScalarTypeSpecIR) and field_ir.type_ir.resolved_width <= 64:
        # Inline scalar ≤64 — use encode helper
        lines.extend(
            [
                "    {",
                f"      auto field_bytes = encode_{field_ir.name}({field_ir.name});",
                "      bytes.insert(bytes.end(), field_bytes.begin(), field_bytes.end());",
                "    }",
            ]
        )
    elif isinstance(field_ir.type_ir, ScalarTypeSpecIR):
        # Wide inline scalar >64 — vector IS big-endian bytes, but need to normalize MSB padding
        bc = byte_count(field_ir.type_ir.resolved_width)
        pad = bc * 8 - field_ir.type_ir.resolved_width
        lines.extend(
            [
                "    {",
                f"      auto field_bytes = encode_{field_ir.name}({field_ir.name});",
                "      bytes.insert(bytes.end(), field_bytes.begin(), field_bytes.end());",
                "    }",
            ]
        )
    elif isinstance(field_ir.type_ir, TypeRefIR):
        target = type_index[field_ir.type_ir.name]
        if isinstance(target, (StructIR, ScalarAliasIR, FlagsIR, EnumIR)):
            lines.extend(
                [
                    "    {",
                    f"      auto field_bytes = {field_ir.name}.to_bytes();",
                    "      bytes.insert(bytes.end(), field_bytes.begin(), field_bytes.end());",
                    "    }",
                ]
            )
        else:
            raise ValidationError(f"unsupported type ref target {type(target).__name__}")
    else:
        raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
    return lines


# ---------------------------------------------------------------------------
# Struct from_bytes — per-field big-endian deserialization
# ---------------------------------------------------------------------------


def _render_cpp_struct_unpack_step(
    *, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]
) -> list[str]:
    """Render one C++ struct unpacking step (big-endian, per-field byte-aligned)."""
    fbc = _field_byte_count(field=field_ir, type_index=type_index)
    lines: list[str] = []
    if isinstance(field_ir.type_ir, ScalarTypeSpecIR) and field_ir.type_ir.resolved_width <= 64:
        lines.extend(
            [
                f"    {field_ir.name} = decode_{field_ir.name}(bytes, offset);",
                f"    offset += {fbc};",
            ]
        )
    elif isinstance(field_ir.type_ir, ScalarTypeSpecIR):
        # Wide inline scalar
        lines.extend(
            [
                f"    {field_ir.name} = decode_{field_ir.name}(bytes, offset);",
                f"    offset += {fbc};",
            ]
        )
    elif isinstance(field_ir.type_ir, TypeRefIR):
        target = type_index[field_ir.type_ir.name]
        if isinstance(target, (StructIR, ScalarAliasIR, FlagsIR, EnumIR)):
            lines.extend(
                [
                    "    {",
                    f"      std::vector<std::uint8_t> field_bytes(bytes.begin() + static_cast<std::ptrdiff_t>(offset),"
                    f" bytes.begin() + static_cast<std::ptrdiff_t>(offset + {fbc}));",
                    f"      {field_ir.name}.from_bytes(field_bytes);",
                    f"      offset += {fbc};",
                    "    }",
                ]
            )
        else:
            raise ValidationError(f"unsupported type ref target {type(target).__name__}")
    else:

exec
/bin/zsh -lc 'rg -n "def _render_cpp_scalar|def _render_cpp_struct|signed|byte_total|full_range|padding|mask|sign_bit|to_bytes|from_bytes|ScalarAliasIR|ScalarTypeSpecIR" src/piketype/backends/cpp/emitter.py' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
1:"""C++ backend — big-endian, byte-aligned padding."""
20:    ScalarAliasIR,
21:    ScalarTypeSpecIR,
68:            signed=const.resolved_signed,
81:        if isinstance(type_ir, ScalarAliasIR):
96:def _render_cpp_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
98:    if width == 32 and signed:
100:    if width == 32 and not signed:
102:    if width == 64 and signed:
104:    if width == 64 and not signed:
106:    raise ValidationError(f"unsupported C++ constant storage: signed={signed}, width={width}")
129:def _render_cpp_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
138:        f"  static constexpr bool SIGNED = {'true' if type_ir.signed else 'false'};",
142:        value_type = _cpp_scalar_value_type(width=width, signed=type_ir.signed)
143:        mask_literal = _cpp_unsigned_literal(
152:        if type_ir.signed:
160:                    f"  static constexpr std::uint64_t MASK = {mask_literal};",
164:                    "  std::vector<std::uint8_t> to_bytes() const {",
169:            # Sign-extend into padding bits
188:                    "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
198:            # Validate sign extension in padding bits
200:                byte_mask = _cpp_unsigned_literal((1 << (bc * 8)) - 1 if bc * 8 < 64 else 2**64 - 1)
204:                        f"    bool sign_bit = ((data_bits >> ({width - 1}U)) & 1U) != 0U;",
205:                        f"    std::uint64_t expected_pad = sign_bit ? (~MASK & {byte_mask}) : 0ULL;",
206:                        f"    if ((bits & ~MASK & {byte_mask}) != expected_pad) {{",
207:                        '      throw std::invalid_argument("signed padding mismatch");',
214:                    "    std::int64_t signed_value = static_cast<std::int64_t>(bits);",
218:                sign_bit_lit = _cpp_unsigned_literal(1 << (width - 1))
219:                full_range_lit = _cpp_unsigned_literal(1 << width)
222:                        f"    if ((bits & {sign_bit_lit}) != 0U && WIDTH < 64) {{",
223:                        f"      signed_value -= static_cast<std::int64_t>({full_range_lit});",
229:                    "    value = validate_value(static_cast<value_type>(signed_value));",
253:            # Unsigned <= 64
257:                    f"  static constexpr std::uint64_t MASK = {mask_literal};",
258:                    f"  static constexpr value_type MAX_VALUE = static_cast<value_type>({_cpp_unsigned_literal(maximum)});",
262:                    "  std::vector<std::uint8_t> to_bytes() const {",
271:                    "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
303:        # Wide unsigned > 64 — vector<uint8_t> in big-endian order
305:        msb_mask = _cpp_unsigned_literal((1 << (8 - pad)) - 1) if pad > 0 else "0xFFU"
313:                "  std::vector<std::uint8_t> to_bytes() const {",
317:                "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
333:                f"    normalized[0] &= {msb_mask};",
354:    uint_type = _cpp_scalar_value_type(width=width, signed=False)
356:    mask_lit = _cpp_unsigned_literal((1 << width) - 1 if width < 64 else 2**64 - 1)
361:    members = ", ".join(f"{v.name} = {_cpp_unsigned_literal(v.resolved_value)}" for v in type_ir.values)
377:        "  std::vector<std::uint8_t> to_bytes() const {",
386:        "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
394:        f"    value = validate_value(static_cast<enum_type>(bits & {mask_lit}));",
436:    # Choose smallest unsigned storage type
437:    value_type = _cpp_scalar_value_type(width=storage_bits, signed=False)
440:    # Data mask: top num_flags bits set, bottom alignment_bits clear
441:    data_mask_val = ((1 << num_flags) - 1) << (storage_bits - num_flags)
443:        data_mask_lit = f"0x{data_mask_val:02X}ULL"
445:        data_mask_lit = f"0x{data_mask_val:02X}U"
455:    # Per-flag mask constants
457:        mask_val = 1 << (storage_bits - 1 - i)
459:            mask_lit = f"0x{mask_val:02X}ULL"
461:            mask_lit = f"0x{mask_val:02X}U"
462:        lines.append(f"  static constexpr value_type {field.name.upper()}_MASK = {mask_lit};")
474:        mask_name = f"{field.name.upper()}_MASK"
478:                f"  bool get_{field.name}() const {{ return (value & {mask_name}) != 0; }}",
479:                f"  void set_{field.name}(bool v) {{ if (v) value |= {mask_name};"
480:                f" else value &= static_cast<value_type>(~{mask_name}); }}",
484:    # to_bytes
488:            "  std::vector<std::uint8_t> to_bytes() const {",
490:            f"    value_type masked = value & {data_mask_lit};",
492:            f"      bytes[BYTE_COUNT - 1 - idx] = static_cast<std::uint8_t>((static_cast<std::uint64_t>(masked) >> (8U * idx)) & 0xFFU);",
499:    # from_bytes
503:            "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
511:            f"    value = static_cast<value_type>(bits) & {data_mask_lit};",
533:            f"    return (value & {data_mask_lit}) == (other.value & {data_mask_lit});",
547:def _render_cpp_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
565:            "  std::vector<std::uint8_t> to_bytes() const {",
580:            "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
649:        case ScalarTypeSpecIR(signed=signed, resolved_width=resolved_width):
651:                return _cpp_scalar_value_type(width=resolved_width, signed=signed)
662:        case ScalarTypeSpecIR(resolved_width=resolved_width):
672:# Struct to_bytes — per-field big-endian serialization
676:def _render_cpp_struct_pack_step(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
679:    if isinstance(field_ir.type_ir, ScalarTypeSpecIR) and field_ir.type_ir.resolved_width <= 64:
689:    elif isinstance(field_ir.type_ir, ScalarTypeSpecIR):
690:        # Wide inline scalar >64 — vector IS big-endian bytes, but need to normalize MSB padding
703:        if isinstance(target, (StructIR, ScalarAliasIR, FlagsIR, EnumIR)):
707:                    f"      auto field_bytes = {field_ir.name}.to_bytes();",
720:# Struct from_bytes — per-field big-endian deserialization
724:def _render_cpp_struct_unpack_step(
730:    if isinstance(field_ir.type_ir, ScalarTypeSpecIR) and field_ir.type_ir.resolved_width <= 64:
737:    elif isinstance(field_ir.type_ir, ScalarTypeSpecIR):
747:        if isinstance(target, (StructIR, ScalarAliasIR, FlagsIR, EnumIR)):
753:                    f"      {field_ir.name}.from_bytes(field_bytes);",
772:    if not isinstance(field_ir.type_ir, ScalarTypeSpecIR):
786:    assert isinstance(field_ir.type_ir, ScalarTypeSpecIR)
787:    signed = field_ir.type_ir.signed
788:    value_type = _cpp_scalar_value_type(width=width, signed=signed)
789:    mask = (1 << width) - 1 if width < 64 else 2**64 - 1
790:    mask_lit = _cpp_unsigned_literal(mask)
793:    if signed:
794:        # --- encode (signed) ---
799:                f"    constexpr std::uint64_t MASK = {mask_lit};",
822:        # --- decode (signed) ---
833:            byte_total_mask = (1 << (bc * 8)) - 1 if bc * 8 < 64 else 2**64 - 1
834:            byte_total_mask_lit = _cpp_unsigned_literal(byte_total_mask)
837:                    f"    constexpr std::uint64_t MASK = {mask_lit};",
839:                    f"    bool sign_bit = ((data_bits >> ({width - 1}U)) & 1U) != 0U;",
840:                    f"    std::uint64_t expected_pad = sign_bit ? (~MASK & {byte_total_mask_lit}) : 0ULL;",
841:                    f"    if ((bits & ~MASK & {byte_total_mask_lit}) != expected_pad) {{",
842:                    '      throw std::invalid_argument("signed padding mismatch");',
848:            lines.append(f"    constexpr std::uint64_t MASK = {mask_lit};")
850:        lines.append("    std::int64_t signed_value = static_cast<std::int64_t>(bits);")
852:            sign_bit_lit = _cpp_unsigned_literal(1 << (width - 1))
853:            full_range_lit = _cpp_unsigned_literal(1 << width)
856:                    f"    if ((bits & {sign_bit_lit}) != 0U) {{",
857:                    f"      signed_value -= static_cast<std::int64_t>({full_range_lit});",
863:                f"    return validate_{field_ir.name}(static_cast<{value_type}>(signed_value));",
869:        # --- encode (unsigned) ---
884:        # --- decode (unsigned) ---
895:            lines.append(f"    bits &= {mask_lit};")
905:    minimum = -(2 ** (width - 1)) if signed else 0
906:    maximum = 2 ** (width - 1) - 1 if signed else (2**width - 1 if width < 64 else 2**64 - 1)
908:    if signed:
921:                f"    constexpr {value_type} MAX_VALUE = static_cast<{value_type}>({_cpp_unsigned_literal(maximum)});",
939:    """Encode/decode helpers for inline scalar > 64 bits (unsigned, vector<uint8_t>, big-endian)."""
940:    msb_mask = _cpp_unsigned_literal((1 << (8 - pad)) - 1) if pad > 0 else "0xFFU"
947:        f"    normalized[0] &= {msb_mask};",
956:        lines.append(f"    result[0] &= {msb_mask};")
973:    if isinstance(type_ir, ScalarAliasIR):
984:    if isinstance(field_type, ScalarTypeSpecIR):
991:    if isinstance(type_ir, ScalarAliasIR):
1004:        case ScalarTypeSpecIR(resolved_width=resolved_width):
1008:            if isinstance(target, ScalarAliasIR):
1020:def _cpp_scalar_value_type(*, width: int, signed: bool) -> str:
1023:        return "std::int8_t" if signed else "std::uint8_t"
1025:        return "std::int16_t" if signed else "std::uint16_t"
1027:        return "std::int32_t" if signed else "std::uint32_t"
1028:    return "std::int64_t" if signed else "std::uint64_t"
1031:def _cpp_unsigned_literal(value: int) -> str:
1032:    """Render an unsigned integer literal for C++."""
1045:    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], ScalarAliasIR)
1060:    return isinstance(field_type, ScalarTypeSpecIR) and field_type.resolved_width > 64

exec
/bin/zsh -lc "sed -n '760,970p' src/piketype/backends/cpp/emitter.py" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
    else:
        raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
    return lines


# ---------------------------------------------------------------------------
# Inline scalar encode/decode helpers (private section of struct class)
# ---------------------------------------------------------------------------


def _render_cpp_inline_scalar_helpers(*, owner_name: str, field_ir: StructFieldIR) -> list[str]:
    """Render private helper functions for one inline scalar field (big-endian)."""
    if not isinstance(field_ir.type_ir, ScalarTypeSpecIR):
        return []
    width = field_ir.type_ir.resolved_width
    bc = byte_count(width)
    pad = bc * 8 - width
    if width <= 64:
        return _render_narrow_inline_helpers(field_ir=field_ir, width=width, bc=bc, pad=pad)
    return _render_wide_inline_helpers(field_ir=field_ir, width=width, bc=bc, pad=pad)


def _render_narrow_inline_helpers(
    *, field_ir: StructFieldIR, width: int, bc: int, pad: int
) -> list[str]:
    """Encode/decode helpers for inline scalar ≤64 bits."""
    assert isinstance(field_ir.type_ir, ScalarTypeSpecIR)
    signed = field_ir.type_ir.signed
    value_type = _cpp_scalar_value_type(width=width, signed=signed)
    mask = (1 << width) - 1 if width < 64 else 2**64 - 1
    mask_lit = _cpp_unsigned_literal(mask)
    lines: list[str] = []

    if signed:
        # --- encode (signed) ---
        lines.extend(
            [
                f"  static std::vector<std::uint8_t> encode_{field_ir.name}({value_type} v) {{",
                f"    validate_{field_ir.name}(v);",
                f"    constexpr std::uint64_t MASK = {mask_lit};",
                "    std::uint64_t bits = static_cast<std::uint64_t>(v) & MASK;",
            ]
        )
        if pad > 0:
            lines.extend(
                [
                    "    if (v < 0) {",
                    "      bits |= ~MASK;",
                    "    }",
                ]
            )
        lines.extend(
            [
                f"    std::vector<std::uint8_t> b({bc}, 0U);",
                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
                f"      b[{bc} - 1 - i] = static_cast<std::uint8_t>((bits >> (8U * i)) & 0xFFU);",
                "    }",
                "    return b;",
                "  }",
                "",
            ]
        )
        # --- decode (signed) ---
        lines.extend(
            [
                f"  static {value_type} decode_{field_ir.name}(const std::vector<std::uint8_t>& bytes, std::size_t offset) {{",
                "    std::uint64_t bits = 0;",
                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
                "      bits = (bits << 8U) | bytes[offset + i];",
                "    }",
            ]
        )
        if pad > 0:
            byte_total_mask = (1 << (bc * 8)) - 1 if bc * 8 < 64 else 2**64 - 1
            byte_total_mask_lit = _cpp_unsigned_literal(byte_total_mask)
            lines.extend(
                [
                    f"    constexpr std::uint64_t MASK = {mask_lit};",
                    "    std::uint64_t data_bits = bits & MASK;",
                    f"    bool sign_bit = ((data_bits >> ({width - 1}U)) & 1U) != 0U;",
                    f"    std::uint64_t expected_pad = sign_bit ? (~MASK & {byte_total_mask_lit}) : 0ULL;",
                    f"    if ((bits & ~MASK & {byte_total_mask_lit}) != expected_pad) {{",
                    '      throw std::invalid_argument("signed padding mismatch");',
                    "    }",
                    "    bits = data_bits;",
                ]
            )
        else:
            lines.append(f"    constexpr std::uint64_t MASK = {mask_lit};")
            lines.append("    bits &= MASK;")
        lines.append("    std::int64_t signed_value = static_cast<std::int64_t>(bits);")
        if width < 64:
            sign_bit_lit = _cpp_unsigned_literal(1 << (width - 1))
            full_range_lit = _cpp_unsigned_literal(1 << width)
            lines.extend(
                [
                    f"    if ((bits & {sign_bit_lit}) != 0U) {{",
                    f"      signed_value -= static_cast<std::int64_t>({full_range_lit});",
                    "    }",
                ]
            )
        lines.extend(
            [
                f"    return validate_{field_ir.name}(static_cast<{value_type}>(signed_value));",
                "  }",
                "",
            ]
        )
    else:
        # --- encode (unsigned) ---
        lines.extend(
            [
                f"  static std::vector<std::uint8_t> encode_{field_ir.name}({value_type} v) {{",
                f"    validate_{field_ir.name}(v);",
                f"    std::vector<std::uint8_t> b({bc}, 0U);",
                "    std::uint64_t bits = static_cast<std::uint64_t>(v);",
                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
                f"      b[{bc} - 1 - i] = static_cast<std::uint8_t>((bits >> (8U * i)) & 0xFFU);",
                "    }",
                "    return b;",
                "  }",
                "",
            ]
        )
        # --- decode (unsigned) ---
        lines.extend(
            [
                f"  static {value_type} decode_{field_ir.name}(const std::vector<std::uint8_t>& bytes, std::size_t offset) {{",
                "    std::uint64_t bits = 0;",
                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
                "      bits = (bits << 8U) | bytes[offset + i];",
                "    }",
            ]
        )
        if pad > 0:
            lines.append(f"    bits &= {mask_lit};")
        lines.extend(
            [
                f"    return validate_{field_ir.name}(static_cast<{value_type}>(bits));",
                "  }",
                "",
            ]
        )

    # --- validate ---
    minimum = -(2 ** (width - 1)) if signed else 0
    maximum = 2 ** (width - 1) - 1 if signed else (2**width - 1 if width < 64 else 2**64 - 1)
    lines.append(f"  static {value_type} validate_{field_ir.name}({value_type} value_in) {{")
    if signed:
        lines.extend(
            [
                f"    constexpr {value_type} MIN_VALUE = static_cast<{value_type}>({minimum});",
                f"    constexpr {value_type} MAX_VALUE = static_cast<{value_type}>({maximum});",
                "    if (value_in < MIN_VALUE || value_in > MAX_VALUE) {",
                '      throw std::out_of_range("value out of range");',
                "    }",
            ]
        )
    else:
        lines.extend(
            [
                f"    constexpr {value_type} MAX_VALUE = static_cast<{value_type}>({_cpp_unsigned_literal(maximum)});",
                "    if (value_in > MAX_VALUE) {",
                '      throw std::out_of_range("value out of range");',
                "    }",
            ]
        )
    lines.extend(
        [
            "    return value_in;",
            "  }",
        ]
    )
    return lines


def _render_wide_inline_helpers(
    *, field_ir: StructFieldIR, width: int, bc: int, pad: int
) -> list[str]:
    """Encode/decode helpers for inline scalar > 64 bits (unsigned, vector<uint8_t>, big-endian)."""
    msb_mask = _cpp_unsigned_literal((1 << (8 - pad)) - 1) if pad > 0 else "0xFFU"
    lines = [
        f"  static std::vector<std::uint8_t> encode_{field_ir.name}(const std::vector<std::uint8_t>& value_in) {{",
        f"    if (value_in.size() != {bc}U) {{",
        '      throw std::invalid_argument("byte width mismatch");',
        "    }",
        "    std::vector<std::uint8_t> normalized = value_in;",
        f"    normalized[0] &= {msb_mask};",
        "    return normalized;",
        "  }",
        "",
        f"  static std::vector<std::uint8_t> decode_{field_ir.name}(const std::vector<std::uint8_t>& bytes, std::size_t offset) {{",
        f"    std::vector<std::uint8_t> result(bytes.begin() + static_cast<std::ptrdiff_t>(offset),"
        f" bytes.begin() + static_cast<std::ptrdiff_t>(offset + {bc}));",
    ]
    if pad > 0:
        lines.append(f"    result[0] &= {msb_mask};")
    lines.extend(
        [
            "    return result;",
            "  }",
        ]
    )
    return lines


# ---------------------------------------------------------------------------
# Width / byte-count resolution helpers
# ---------------------------------------------------------------------------



exec
/bin/zsh -lc "sed -n '1,180p' specs/010-jinja-template-migration/spec.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc 'rg -n "FR-10|FR-8|FR-18|templates contain no semantics|template.*arithmetic|arithmetic|comparison|branch|view" specs/010-jinja-template-migration/spec.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
9:## Overview
15:- **Python prepares typed view models** from frozen IR. View models contain only computed primitive values (names, widths, byte counts, masks, signed/unsigned flags, helper-fragment strings, import lists) and nested frozen view-model dataclasses. Semantic decisions stay in Python.
26:- **US-1.** As a maintainer adding a new generated language construct, I want to edit a focused Jinja template alongside a small view-model addition, so that I can change output structure without re-reading 800-line emitter files.
27:- **US-2.** As a reviewer auditing generated output, I want the file shape (imports, class skeletons, helper bodies, footer) to be visible as a contiguous template, so that I can read the output structure top-to-bottom without reconstructing it from scattered string concatenations.
30:- **US-5.** As a future feature author working on a new backend or backend variant, I want a documented view-model + template pattern to follow, so that new backends start out template-first instead of being reverse-engineered later.
31:- **US-6.** As a maintainer reviewing template-bound code, I want a clear and enforced rule about what may live in templates versus Python, so that templates do not silently accumulate semantic logic over time.
37:- **View model.** A frozen dataclass (`@dataclass(frozen=True, slots=True)`) whose fields are restricted to: primitive types (`int`, `str`, `bool`, `bytes`); `tuple[...]` of primitives or other view-model dataclasses; or other view-model dataclass instances. View models contain no IR references, no callables, and no methods that compute output at render time (frozen-dataclass `__init__` is permitted; user-defined methods are not).
40:- **Fragment.** A short, self-contained string that is not a skeleton: an expression, a single hex literal, a single-line comment string, a comma-separated argument list, a Python initializer expression. Fragments are pre-computed in Python and passed into the view model as `str` fields.
49:- **FR-1.** A new module layer SHALL exist for view models. Each backend (`py`, `cpp`, `sv`) SHALL expose typed, frozen view-model dataclasses. Naming convention: `backends/<lang>/view.py` containing `@dataclass(frozen=True, slots=True)` classes.
53:  - `def render(*, env: jinja2.Environment, template_name: str, context: object) -> str` that renders a template and returns a string whose final character is `"\n"` (consistent with current emitter contracts). The `context` SHALL be a view-model dataclass instance; the helper SHALL pass its fields as the template context (via `dataclasses.asdict` or by passing the instance directly with templates accessing `.field` attributes — implementation choice, but uniform across backends).
54:- **FR-4.** Each backend SHALL keep its existing public emit entry point (`emit_py`, `emit_cpp`, `emit_sv`) with unchanged signatures and unchanged write locations; only the internal rendering pipeline changes. The IR → view-model → template → string flow SHALL be the only public migration surface.
58:- **FR-5.** Migration SHALL proceed in this order: (1) Python backend, (2) C++ backend, (3) SystemVerilog backend. Each backend migration SHALL be a separable, independently reviewable change. A backend's migration is **complete** when its per-backend acceptance criteria (AC-P*, AC-C*, AC-S* below) are all met. Subsequent backends SHALL NOT begin until the prior backend's migration is complete.
67:  **Examples of "trivial fragments" (MAY remain inline in Python and be passed as `str` fields):** a single hex literal (`"0xff"`), a numeric expression rendered for a constant (`"(1 << 32) - 1"`), a single-line type alias initializer, a header comment line, an `__all__` tuple body. These fragments SHALL be pre-computed in Python and exposed as `str` fields on the view model; templates SHALL emit them with `{{ fragment }}` and SHALL NOT recompute them.
73:- **FR-8.** View-model fields SHALL be exactly one of:
75:  - A `tuple[T, ...]` where `T` is itself a view-model field type.
76:  - Another view-model dataclass instance (nesting permitted).
78:  Nesting is permitted but limited: a view model SHALL NOT contain itself transitively (no recursive view models). View-model construction SHALL produce values whose iteration order is stable: any field whose type is `tuple` SHALL preserve the input's declaration order or sort the input deterministically before construction.
87:- **FR-10.** Templates SHALL NOT:
88:  - Compute padding, alignment, byte counts, masks, sign-extension boundaries, or any width-derived numeric value (these arrive as primitive view-model fields).
90:  - Decide signed vs. unsigned behavior. The view model SHALL provide signedness as a `bool` plus pre-computed numeric fragments.
102:- **FR-12.** Templates SHALL live under `backends/<lang>/templates/`. Subdirectories are permitted. Required convention: each backend SHALL have exactly one **primary template** per generated artifact kind (e.g., `module.j2` for a generated `.py`/`.cpp`/`.sv` source file). Macros and partials live in files prefixed `_` (e.g., `_macros.j2`, `_struct.j2`). Reviewers locate generated output by reading the primary template; partials are an implementation detail.
103:- **FR-13.** Template file extensions SHALL be `.j2`. Templates SHALL NOT carry the machine-readable header themselves; the header is produced by `backends/common/headers.py` and passed in as a view-model `header: str` field, then emitted by the template with `{{ header }}`.
114:- **FR-18.** Each backend SHALL place its view-model dataclasses **and** the IR-to-view-model construction functions in a single file `backends/<lang>/view.py`. (A separate `builder.py` is not used; if `view.py` exceeds ~250 lines, splitting it into `view.py` + `builder.py` is permitted as a follow-up refactor outside this spec.) Construction functions SHALL be top-level keyword-only functions named `build_<view_model>(...)`.
116:  Per-backend view-model unit tests SHALL exist:
117:  - `tests/test_view_py.py` — exercises `backends/py/view.py` builders against fixture IR derived from `tests/fixtures/struct_padded`, `tests/fixtures/scalar_wide`, and `tests/fixtures/enum_basic`. At minimum, asserts that view-model fields are populated with expected primitive values for each fixture (one assertion per non-trivial field per fixture).
118:  - `tests/test_view_cpp.py` — analogous, against the same three fixtures plus `tests/fixtures/const_cpp_wide`.
119:  - `tests/test_view_sv.py` — analogous, against the same three fixtures plus `tests/fixtures/scalar_sv_basic` and `tests/fixtures/nested_struct_sv_basic`.
121:  These view-model tests are in addition to (not a replacement for) existing golden-file integration tests. They use `unittest.TestCase` (constitution-compliant).
123:- **FR-19.** When a backend's migration is complete, the inline `render_module_<lang>` function and its `_render_*` helpers in `backends/<lang>/emitter.py` SHALL be removed. The `emit_<lang>` entry point remains and now orchestrates: (1) build view model from IR, (2) construct env, (3) render primary template, (4) write file.
128:  2. `\bbyte_count\b\s*[-+*/]|[-+*/]\s*\bbyte_count\b` — arithmetic on `byte_count` (either operand position).
131:  5. `[-+*/]\s*8\b|\b8\s*[-+*/]` — explicit-byte arithmetic in Jinja.
143:  - The view-model + template architecture, with one worked example for the Python backend (IR → view-model → template → output).
144:  - The "what may live in templates" rule (cross-referenced from FR-10/FR-11) and the indirection-depth bound from FR-11.
146:  - The location of templates and view models per backend.
162:  3. On the feature branch after each backend migration completes, run the same script and record `current_ms`.
170:- **NFR-5. Auditability.** A reviewer SHALL be able to find the full rendering of any generated output construct by reading the backend's primary template (`module.j2`) plus at most one layer of partial templates referenced by it. The two-level indirection bound in FR-11 enforces this.
187:- **AC-4-`<lang>`.** `backends/<lang>/view.py` exists and contains only `@dataclass(frozen=True, slots=True)` classes whose fields satisfy FR-8 (primitives, `tuple` of view-model field types, or other view-model dataclass instances). Verifiable by reading the file and by `basedpyright --strict`.
189:- **AC-6-`<lang>`.** `tests/test_view_<lang_lower>.py` exists, runs, and passes.
215:- **OOS-7.** Replacing `backends/common/headers.py` with a templated header. Headers stay inline string-built and are passed into templates as a `header: str` view-model field (per FR-13).
223:- **CL-1 (was Q-1) — Per-backend commit granularity.** Each backend's migration lands as **multiple contiguous commits** on `feature/010-jinja-template-migration`, one per FR-6 sub-step where the change is non-trivial (skeleton, top-level types, helpers, fragments). The first commit of a backend's migration block introduces `view.py` and the primary template; subsequent commits replace inline emitter sections with template-rendered output. Squash-on-merge is permitted by project policy but SHALL NOT be required by this spec. Reverting any backend's migration is a contiguous-range revert per NFR-6.

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

exec
/bin/zsh -lc 'rg -n "CppStructFieldView|has_signed_padding|has_signed_short_width|full_range_literal|byte_total_mask_literal" specs/010-jinja-template-migration/artifacts/planning/iter4-forge.md specs/010-jinja-template-migration/artifacts/planning/iter4-gauge-prompt.md specs/010-jinja-template-migration/plan.md' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
specs/010-jinja-template-migration/artifacts/planning/iter4-gauge-prompt.md:22:   - `has_signed_padding` and `has_signed_short_width` branch booleans.
specs/010-jinja-template-migration/artifacts/planning/iter4-gauge-prompt.md:23:   - `full_range_literal`, `byte_total_mask_literal`, in addition to the previously existing literals.
specs/010-jinja-template-migration/plan.md:335:    has_signed_padding: bool      # is_narrow_signed and (byte_count*8 - width) > 0
specs/010-jinja-template-migration/plan.md:336:    has_signed_short_width: bool  # is_narrow_signed and width < 64
specs/010-jinja-template-migration/plan.md:344:    sign_bit_literal: str         # _cpp_unsigned_literal(1 << (width-1)) when has_signed_short_width; else ""
specs/010-jinja-template-migration/plan.md:345:    full_range_literal: str       # _cpp_unsigned_literal(1 << width) when has_signed_short_width; else ""
specs/010-jinja-template-migration/plan.md:346:    byte_total_mask_literal: str  # _cpp_unsigned_literal((1 << (byte_count*8)) - 1 if byte_count*8 < 64 else 2**64 - 1) when has_signed_padding; else ""
specs/010-jinja-template-migration/plan.md:384:class CppStructFieldView:
specs/010-jinja-template-migration/plan.md:412:    fields: tuple[CppStructFieldView, ...]
specs/010-jinja-template-migration/plan.md:546:    has_signed_padding: bool      # field.padding_bits > 0 and field is signed
specs/010-jinja-template-migration/plan.md:547:    padding_bits: int             # field.padding_bits when has_signed_padding else 0
specs/010-jinja-template-migration/plan.md:548:    sign_bit_index: int           # data_width - 1 when has_signed_padding else 0
specs/010-jinja-template-migration/artifacts/planning/iter4-forge.md:335:    has_signed_padding: bool      # is_narrow_signed and (byte_count*8 - width) > 0
specs/010-jinja-template-migration/artifacts/planning/iter4-forge.md:336:    has_signed_short_width: bool  # is_narrow_signed and width < 64
specs/010-jinja-template-migration/artifacts/planning/iter4-forge.md:344:    sign_bit_literal: str         # _cpp_unsigned_literal(1 << (width-1)) when has_signed_short_width; else ""
specs/010-jinja-template-migration/artifacts/planning/iter4-forge.md:345:    full_range_literal: str       # _cpp_unsigned_literal(1 << width) when has_signed_short_width; else ""
specs/010-jinja-template-migration/artifacts/planning/iter4-forge.md:346:    byte_total_mask_literal: str  # _cpp_unsigned_literal((1 << (byte_count*8)) - 1 if byte_count*8 < 64 else 2**64 - 1) when has_signed_padding; else ""
specs/010-jinja-template-migration/artifacts/planning/iter4-forge.md:384:class CppStructFieldView:
specs/010-jinja-template-migration/artifacts/planning/iter4-forge.md:412:    fields: tuple[CppStructFieldView, ...]
specs/010-jinja-template-migration/artifacts/planning/iter4-forge.md:546:    has_signed_padding: bool      # field.padding_bits > 0 and field is signed
specs/010-jinja-template-migration/artifacts/planning/iter4-forge.md:547:    padding_bits: int             # field.padding_bits when has_signed_padding else 0
specs/010-jinja-template-migration/artifacts/planning/iter4-forge.md:548:    sign_bit_index: int           # data_width - 1 when has_signed_padding else 0

exec
/bin/zsh -lc 'ls -1 specs/010-jinja-template-migration/artifacts/planning' in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
iter1-forge.md
iter1-gauge-prompt.md
iter1-gauge.md
iter2-forge.md
iter2-gauge-prompt.md
iter2-gauge.md
iter3-forge.md
iter3-gauge-prompt.md
iter3-gauge.md
iter4-forge.md
iter4-gauge-prompt.md
iter4-gauge.md

exec
/bin/zsh -lc "wc -l specs/010-jinja-template-migration/artifacts/planning/iter4-gauge.md && sed -n '1,160p' specs/010-jinja-template-migration/artifacts/planning/iter4-gauge.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
    2300 specs/010-jinja-template-migration/artifacts/planning/iter4-gauge.md
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
session id: 019dd900-6655-7e21-bfda-f173695076f0
--------
user
Read and follow the instructions in /Users/ezchi/Projects/pike-type/specs/010-jinja-template-migration/artifacts/planning/iter4-gauge-prompt.md
codex
I’ll read the planning prompt first, then execute exactly what it asks within the repo context.
exec
/bin/zsh -lc "sed -n '1,240p' specs/010-jinja-template-migration/artifacts/planning/iter4-gauge-prompt.md" in /Users/ezchi/Projects/pike-type
 succeeded in 0ms:
# Gauge Review Prompt — Planning Iteration 4

This is iteration 4. Iteration 3 returned `VERDICT: REVISE` with three BLOCKINGs:

1. Leftover prose at Phase 1 commit 5 still said `body_lines` was "always None" — contradicting the new tuple-plus-bool mechanism.
2. `SvPackUnpackFnView` precomputed `pack_lines` / `unpack_lines` as Python-built body strings — meaningful structure had to move into templates.
3. C++ scalar dataclasses missed primitives needed for current helper branches (signed-padding branch booleans, full-range literal, byte-total mask literal).

All three were addressed in iter4.

## Inputs

- `specs/010-jinja-template-migration/plan.md` (iter4).
- `specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md`.

## Review

1. Confirm the Phase 1 commit 5 description now uses the empty-tuple + `has_body_lines=False` language.
2. Confirm `SvPackUnpackFnView` is now a union of four structured variants (scalar/flags/enum/struct) with no pre-rendered body strings.
3. Confirm `CppScalarAliasView` now exposes:
   - `is_narrow_signed` / `is_narrow_unsigned` / `is_wide` discriminators.
   - `has_signed_padding` and `has_signed_short_width` branch booleans.
   - `full_range_literal`, `byte_total_mask_literal`, in addition to the previously existing literals.
4. Look for any new contradictions introduced by these surgical edits.

This is the **maxIterations=5 budget**. After this round there is one more REVISE allowed before the loop exits without an APPROVE; bias APPROVE if the three BLOCKINGs are mechanically resolved and no new BLOCKING is introduced.

End with `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after.

codex
The prompt is a planning gauge review: I need verify three prior blockers against the current plan and return a strict APPROVE/REVISE verdict. I’m checking the plan and prior gauge notes now.
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/plan.md" in /Users/ezchi/Projects/pike-type
exec
/bin/zsh -lc "sed -n '1,260p' specs/010-jinja-template-migration/artifacts/planning/iter3-gauge.md" in /Users/ezchi/Projects/pike-type
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

Concrete mechanism (FR-8/FR-9 compliant — no `None`, no `set`, no `dict`):
- `ModuleView` carries two fields: `body_lines: tuple[str, ...]` (default empty tuple) and `has_body_lines: bool` (a primitive bool, FR-8 compliant). When `has_body_lines` is `True`, the primary template emits `{{ body_lines | join("\n") }}` for the not-yet-templated portion.
- Each sub-step replaces a portion of `body_lines` with a structured field (`types: tuple[TypeView, ...]`, etc.). The template's body section transitions from `{% if has_body_lines %}{{ body_lines | join("\n") }}{% endif %}` to a structured loop over `types`.
- After sub-step 4 (fragments), `body_lines` is empty and `has_body_lines` is False everywhere. Both fields are retired in the cleanup commit.

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
    """Render a template against a view-model dataclass instance.

    Per FR-3, the production context is always a frozen view-model dataclass.
    Dict contexts are rejected. Tests that need a dict-shaped context build
    their own ad-hoc env via `jinja2.Environment(loader=DictLoader(...))`.
    """
    if not is_dataclass(context) or isinstance(context, type):

codex
1. **BLOCKING — FR-10 / FR-18 / C++ inline scalar helpers.** Iter3’s blocker covered scalar and inline scalar helper branches. `CppScalarAliasView` is now fixed, but `CppStructFieldView` still lacks the same required branch primitives for inline scalar helpers: `has_signed_padding`, `has_signed_short_width`, `full_range_literal`, and `byte_total_mask_literal` (`plan.md:384-407`). Current inline helper emission needs those decisions/literals for signed padding and sign-extension paths (`src/piketype/backends/cpp/emitter.py:793-857`). Without them, templates must derive width/padding logic or emit non-byte-identical helper bodies.

The Phase 1 commit 5 text is fixed, and `SvPackUnpackFnView` is now a structured scalar/flags/enum/struct union with no `pack_lines` / `unpack_lines`.

VERDICT: REVISE
2026-04-29T11:31:10.467698Z ERROR codex_core::session: failed to record rollout items: thread 019dd900-6655-7e21-bfda-f173695076f0 not found
tokens used
71,668
1. **BLOCKING — FR-10 / FR-18 / C++ inline scalar helpers.** Iter3’s blocker covered scalar and inline scalar helper branches. `CppScalarAliasView` is now fixed, but `CppStructFieldView` still lacks the same required branch primitives for inline scalar helpers: `has_signed_padding`, `has_signed_short_width`, `full_range_literal`, and `byte_total_mask_literal` (`plan.md:384-407`). Current inline helper emission needs those decisions/literals for signed padding and sign-extension paths (`src/piketype/backends/cpp/emitter.py:793-857`). Without them, templates must derive width/padding logic or emit non-byte-identical helper bodies.

The Phase 1 commit 5 text is fixed, and `SvPackUnpackFnView` is now a structured scalar/flags/enum/struct union with no `pack_lines` / `unpack_lines`.

VERDICT: REVISE
