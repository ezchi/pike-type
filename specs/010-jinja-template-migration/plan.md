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
    types: tuple[TypeView, ...]
    # Transitional passthrough: non-empty during sub-steps 1–3, empty at sub-step 4. Both fields removed in commit 6.
    body_lines: tuple[str, ...]
    has_body_lines: bool
```

**Builder functions (top-level in `view.py`, keyword-only per FR-18):**
- `build_module_view_py(*, module: ModuleIR) -> ModuleView`
- `_build_scalar_alias_view(*, type_ir: ScalarAliasIR) -> ScalarAliasView` (private helper)
- `_build_struct_view(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> StructView`
- `_build_struct_field_view(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> StructFieldView`
- `_build_enum_view(*, type_ir: EnumIR) -> EnumView`
- `_build_flags_view(*, type_ir: FlagsIR) -> FlagsView`
- `_build_constant_view(*, const_ir: ConstantIR) -> ConstantView`

Builders are pure functions, no side effects, no IR mutation. Tests in `tests/test_view_py.py` assert that for a fixture's IR, the builder produces a view whose primitive fields equal expected literal values (e.g., for `enum_basic`, `EnumView.mask == 7`).

**Commit sequence (Phase 1) — strictly FR-6 sub-step ordered:**

1. `feat(py): introduce ModuleView dataclasses and builders` — `view.py` complete, `tests/test_view_py.py` complete. `emitter.py` unchanged. View module is dormant; tests pass against it directly.
2. `feat(py): module skeleton via templates` (FR-6 sub-step 1) — `module.j2` renders header + imports + footer. `emit_py` constructs `ModuleView` with `body_lines = tuple(legacy_render_body_lines(module))` and the template emits `{{ body_lines | join("\n") }}` for the body. **Byte parity preserved.**
3. `feat(py): top-level type declaration skeletons via templates` (FR-6 sub-step 2) — `_macros.j2` adds `scalar_class_skeleton`, `struct_class_skeleton`, `enum_classes_skeleton`, `flags_class_skeleton` macros that emit *only the class header lines* (`class X:`, `WIDTH = ...`, `BYTE_COUNT = ...`). Helper-method bodies and expression fragments still arrive as `body_lines_per_type: tuple[str, ...]` strings on each TypeView. The view is augmented with `helper_lines: tuple[str, ...]` per TypeView temporarily. **Byte parity preserved.**
4. `feat(py): helper-method skeletons via templates` (FR-6 sub-step 3) — macros gain `to_bytes_block`, `from_bytes_block`, `coerce_block`, `setattr_block`, `clone_block`, `eq_repr_block`. Each block consumes precomputed numeric primitives from the view and emits the helper body skeleton. The transitional `helper_lines` field is removed. **Byte parity preserved.**
5. `feat(py): expression and field-level fragments` (FR-6 sub-step 4) — expressions like Python constants, enum member values, and flag mask literals are now rendered from view-model `*_expr: str` fields directly in templates (no Python concatenation). Also handles struct field annotations/defaults/coercer literals. The transitional `body_lines: tuple[str, ...]` field on `ModuleView` is now always the empty tuple and `has_body_lines: bool` is always `False` after this commit. (Both fields remain on the dataclass with default values until the cleanup commit; the template no longer reads them after this commit.) **Byte parity preserved.**
6. `refactor(py): remove inline emitter helpers` (FR-19) — delete every `_render_py_*` function and the legacy `render_module_py`. `emit_py` becomes ≤ ~40 lines. **Byte parity preserved.**
7. `steel(perf): record py-complete perf row` — appends `py-complete` row to `perf.md` (FR-25).

**Phase 1 gates (per-backend):** AC-1-Py..AC-7-Py, all tested at the end of commit 7.

---

## Phase 2 — C++ backend migration

Same FR-6 sub-step structure. Backend-specific shape differences:

**Files:** `src/piketype/backends/cpp/view.py`, `templates/{module.j2,_macros.j2,_pack.j2}`, `tests/test_view_cpp.py`.

**Concrete view-model dataclasses (C++ backend) — pinned to current `render_module_hpp` byte output:**

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
    # Type discriminators (exactly one is True).
    is_struct_ref: bool
    is_flags_ref: bool
    is_enum_ref: bool
    is_scalar_ref: bool
    is_narrow_scalar: bool        # ScalarTypeSpec, width <= 64
    is_wide_scalar: bool          # ScalarTypeSpec, width > 64
    target_class: str             # "" if scalar spec
    width: int                    # data width for scalar specs (0 for refs)
    signed: bool
    # Inline-scalar helper branch primitives (parallel to CppScalarAliasView).
    # Required for byte-identical reproduction of _render_narrow_inline_helpers
    # and _render_wide_inline_helpers (cpp emitter lines 793-857).
    has_signed_padding: bool      # is_narrow_scalar and signed and (pack_bits - width) > 0
    has_signed_short_width: bool  # is_narrow_scalar and signed and width < 64
    min_value_literal: str
    max_value_literal: str
    mask_literal: str             # _cpp_unsigned_literal((1 << width) - 1) for narrow; "" for wide
    sign_bit_literal: str         # _cpp_unsigned_literal(1 << (width-1)) when has_signed_short_width; else ""
    full_range_literal: str       # _cpp_unsigned_literal(1 << width) when has_signed_short_width; else ""
    byte_total_mask_literal: str  # _cpp_unsigned_literal((1 << pack_bits) - 1 if pack_bits < 64 else 2**64 - 1) when has_signed_padding; else ""
    msb_byte_mask_literal: str    # for wide: _cpp_unsigned_literal((1 << (8 - pad)) - 1) when pad > 0, else "0xFFU"; "" for non-wide

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

**Concrete view-model dataclasses (SystemVerilog backend) — pinned to current `render_module_sv` and `render_module_test_sv`:**

```python
@dataclass(frozen=True, slots=True)
class SvConstantView:
    sv_type: str                  # _render_sv_const result, e.g. "int signed", "logic [31:0]", "longint unsigned"
    name: str
    sv_expr: str                  # pre-rendered SV literal or expression

# --- Synth package (one per module) -----------------------------------------

@dataclass(frozen=True, slots=True)
class SvScalarAliasTypedefView:
    name: str                     # type name as-is (e.g. "addr_t")
    width: int
    signed: bool
    sv_type_text: str             # pre-rendered, e.g. "logic signed [31:0]" or "logic [7:0]"

@dataclass(frozen=True, slots=True)
class SvStructFieldDeclView:
    name: str
    sv_type_text: str             # _render_sv_struct_field_type result
    is_composite_ref: bool        # references another typedef (struct/flags/enum) by name

@dataclass(frozen=True, slots=True)
class SvStructTypedefView:
    name: str                     # struct typedef name
    fields: tuple[SvStructFieldDeclView, ...]
    width: int                    # data width

@dataclass(frozen=True, slots=True)
class SvFlagsTypedefView:
    name: str
    field_names: tuple[str, ...]  # MSB-first declaration order
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

@dataclass(frozen=True, slots=True)
class SvHelperStructFieldView:
    name: str
    sv_type_text: str             # field declaration type text, e.g. "logic signed [31:0]"
    byte_count: int
    width: int
    signed: bool
    pack_bits: int
    is_composite_ref: bool        # struct/flags/enum target
    target_helper_class: str      # e.g. "foo_helper" (when is_composite_ref) else ""
    mask_literal: str
    sign_bit_literal: str

@dataclass(frozen=True, slots=True)
class SvStructHelperClassView:
    name: str
    underlying_typedef: str
    width: int
    byte_count: int
    fields: tuple[SvHelperStructFieldView, ...]
    alignment_bytes: int

@dataclass(frozen=True, slots=True)
class SvFlagsHelperClassView:
    name: str
    underlying_typedef: str
    num_flags: int
    byte_count: int
    field_names: tuple[str, ...]
    data_mask_literal: str

@dataclass(frozen=True, slots=True)
class SvEnumHelperClassView:
    name: str
    underlying_typedef: str
    underlying_width: int
    byte_count: int
    member_names: tuple[str, ...]
    mask_literal: str

type SvHelperClassView = (
    SvScalarHelperClassView
    | SvStructHelperClassView
    | SvFlagsHelperClassView
    | SvEnumHelperClassView
)

@dataclass(frozen=True, slots=True)
class SvTestModuleView:
    header: str
    package_name: str             # <basename>_test_pkg
    synth_package_import: str     # "import <basename>_pkg::*;"
    helper_classes: tuple[SvHelperClassView, ...]
    body_lines: tuple[str, ...]   # transitional, FR-8 compliant
    has_body_lines: bool
```

Builder produces both views from one `ModuleIR`:
- `build_synth_module_view_sv(*, module: ModuleIR) -> SvSynthModuleView`
- `build_test_module_view_sv(*, module: ModuleIR) -> SvTestModuleView`

The test-package builder shares helpers with the synth builder where possible.

**Commit sequence (Phase 3):**

1. `feat(sv): introduce SvSynthModuleView and SvTestModuleView dataclasses and builders`.
2. `feat(sv): synth and test package skeletons via templates` (FR-6 sub-step 1, both packages handled in one commit since they share most skeleton rules).
3. `feat(sv): synth typedef scaffolding and test helper-class scaffolding via templates` (FR-6 sub-step 2).
4. `feat(sv): pack/unpack functions and verification helper-method skeletons via templates` (FR-6 sub-step 3 — the largest chunk for SV).
5. `feat(sv): expression and field-level fragments via templates` (FR-6 sub-step 4).
6. `refactor(sv): remove inline emitter helpers`.
7. `steel(perf): record sv-complete perf row`.

**Phase 3 gates:** AC-1-Sv..AC-7-Sv.

---

## Phase 4 — Feature-final validation

Runs during the spec's `validation` Steel-Kit stage.

**Steps:**

1. `python -m unittest discover tests` → must pass cleanly. **AC-F1.**
2. `basedpyright --strict src/ tools/` → zero errors. **AC-F2.**
3. `python tools/check_templates.py src/piketype/backends/{py,cpp,sv}/templates/` → exit 0. **AC-F3.**
4. `python tools/perf_bench.py` → append result as `feature-final` row to `perf.md`. Verify `feature-final.median_ms ≤ 1.25 * baseline.median_ms`. **AC-F4 / FR-25.**
5. Wheel packaging: `pip wheel . -w /tmp/pike_wheel/ --no-deps`; `unzip -l /tmp/pike_wheel/pike_type-*.whl` shows the expected primary templates per backend (`piketype/backends/py/templates/module.j2`, `piketype/backends/cpp/templates/module.j2`, `piketype/backends/sv/templates/module_synth.j2`, `piketype/backends/sv/templates/module_test.j2`, plus each backend's `_macros.j2`). The exact set of `.j2` files is checked against the actual files committed in `src/piketype/backends/{py,cpp,sv}/templates/` (i.e., the wheel must contain every `.j2` that exists in source, no more no less). Install into clean venv → `piketype gen <tmp-copy>/alpha/piketype/types.py` → diff against from-source generation. **AC-F5.**
6. `docs/templates.md` covers FR-22 + FR-24 items (manual checklist). **AC-F6.**
7. `python tools/check_templates.py src/piketype/backends/{py,cpp,sv}/templates/` exits 0 (same script as AC-F3, repeated for AC-F7's audit form).
8. `git log --oneline develop..HEAD` shows commits grouped by Phase 0..3 in order; `git revert <sha-range>` dry-runs cleanly per backend. **AC-F8.**

**Validation commit:** `steel(validation): record feature-final results` — appends row to `perf.md`, no source changes.

---

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Whitespace drift on first template render breaks goldens | High | `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True` in `make_environment`. Migrate one sub-step at a time and diff goldens after each commit. The transitional `body_lines | join("\n")` mechanism preserves line-by-line legacy output verbatim until each sub-step replaces it. |
| Jinja `trim_blocks`/`lstrip_blocks` interacting unexpectedly with literal-heavy template content (e.g., generated SV helper classes containing `begin`/`end` blocks) | Medium | When a literal-heavy block must be preserved verbatim, wrap it in `{% raw %}...{% endraw %}` or pass it through as a precomputed `str` field on the view (the `body_lines` mechanism). Phase 3 commit 4 explicitly tests this on the largest SV `_helper_class` block. |
| `PackageLoader` does not find templates from a wheel install | Medium | Phase 1 commit 2 verifies wheel packaging immediately by building the wheel and running smoke test once the first `.j2` file lands (Phase 0 commit 4 only configures package-data; Phase 1 commit 2 lands the first template and exercises the wheel path). |
| View-model construction order vs. frozen-IR semantics | Low | Builders use only IR read-access; they construct view models with explicit tuples in IR's declaration order (no `set` or `dict` traversal). `tests/test_view_py.py`/`test_view_cpp.py`/`test_view_sv.py` each include a test asserting that field/member tuples preserve declaration order from the source fixture. IR is never mutated — verified by the existing immutable-IR contract. |
| View-model tests over-couple to internal numeric values | Low | Tests assert public-contract values (class names, widths, byte counts, mask literals) — the same values that already appear in goldens. |
| Performance regression > 25% from Jinja template loading overhead | Low–Medium | Measured at every per-backend completion (FR-25). `jinja2.Environment` caches compiled templates by default within a process. `emit_<lang>` constructs the env once per call, so all modules in a single `gen` invocation share compiled-template caches. Mitigation if exceeded: switch to `jinja2.PackageLoader` with bytecode caching enabled. |
| `frozen=True, slots=True` prevents `__post_init__` validation cleanly | Low | Validation lives in builder functions (before construction), so `__post_init__` is rarely needed. If it is needed, `object.__setattr__` is the documented escape. |
| C++ `--namespace` CLI override regression | Medium | `tests/test_view_cpp.py` runs the namespace-override fixture (`tests/fixtures/namespace_override`) end-to-end, asserting the rendered guard macro and namespace open/close strings. This catches regressions before goldens. |
| SV verification helpers contain large mostly-static blocks where parity is brittle | Medium | Phase 3 splits synth and test rendering into separate templates so a parity break is localized to one file. Goldens fail-fast on byte diff. The largest helper-class blocks (`*_helper` classes) are migrated in Phase 3 commit 4 with extra golden checks. |

---

## Dependencies and ordering

- Phase 0 must complete before any of Phase 1/2/3 starts.
- Phase 1 → Phase 2 → Phase 3 (FR-5/CL-1).
- Phase 4 must be the last phase.
- Within each Phase 1/2/3 sub-step commit sequence, commit N+1 depends on commit N's byte parity verification.
- Filter additions (CL-2) and lint-pattern adjustments (FR-21) happen on the sub-step commit that introduces the need; both land via `backends/common/render.py` (CL-2/FR-16) and `tools/check_templates.py` respectively.

## Out of plan (deliberately deferred)

- New view-model fields beyond what's needed to render current goldens.
- Refactoring `headers.py` (OOS-7).
- Migrating `runtime`/`build`/`lint`/`test` sub-backends (OOS-2).
- Splitting `view.py` into `view.py + builder.py` if line count grows past ~250 (FR-18 permits as a future refactor; not in this plan).

## Testing strategy

- **Existing golden integration tests:** unchanged. Run after every commit. Each commit's correctness criterion is golden bytes parity.
- **New view-model tests** (`tests/test_view_<lang>.py`): introduced in Phase N commit 1. They assert primitive-field values per fixture (one assertion per non-trivial field).
- **New helper tests** (`tests/test_render.py`, `tests/test_check_templates.py`): land in Phase 0 commits 1–2.
- **Idempotency tests** (existing): unchanged; pass throughout because the migration changes how output is produced, not what is produced.
- **C++ namespace override tests:** explicit end-to-end run of the namespace-override fixture in `tests/test_view_cpp.py`.
- **SV synth/test split tests:** explicit assertion in `tests/test_view_sv.py` that synth and test packages produce independent views (no shared mutable state).

## Estimated commit count

- Phase 0: 6 commits
- Phase 1: 7 commits (6 migration + 1 perf row)
- Phase 2: 7 commits
- Phase 3: 7 commits
- Phase 4: 1 commit
- Total: ~28 commits on `feature/010-jinja-template-migration`.
