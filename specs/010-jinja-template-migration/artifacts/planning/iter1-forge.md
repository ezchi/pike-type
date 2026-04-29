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
build_module_view(module: ModuleIR)              env.get_template(...).render(view)
   │                                                  ▲
   ▼                                                  │
ModuleView (frozen dataclass)  ───────────────────────┘

emit_<lang>(repo) {
    env = make_environment("piketype.backends.<lang>")
    for module in repo.modules:
        view  = build_module_view(module, ...)
        text  = render(env=env, template_name="module.j2", context=view)
        write(path, text)
}
```

**Key invariants** (all enforced by AC-* gates):
- View models are read-only frozen dataclasses with primitive fields plus nested view-model dataclasses (FR-8/9).
- Templates contain no semantics (FR-10), enforced by `tools/check_templates.py` (FR-21).
- `render` returns a string ending in `\n` (FR-3); identical to current emitter contracts.
- `emit_<lang>` signature unchanged (FR-4, NFR-7).
- Output is byte-for-byte identical at each per-backend completion (FR-7).

---

## Phase 0 — Shared infrastructure (one commit block, before any backend migration)

**Goal:** Land everything that must exist before the first backend migration. After this phase, the repository builds, all existing tests pass, and the new tools are runnable. No emitter changes yet.

**Files created/modified:**

| Path                                          | Action  | Purpose |
|-----------------------------------------------|---------|---------|
| `src/piketype/backends/common/render.py`      | rewrite | Stub → `make_environment(*, package: str) -> jinja2.Environment` and `render(*, env, template_name, context) -> str`. Custom-filter registration site (FR-2/3, CL-2). |
| `tools/check_templates.py`                    | new     | Template-hygiene lint (FR-21). |
| `tests/test_check_templates.py`               | new     | Lint script unit tests (FR-21 last paragraph). |
| `tests/test_render.py`                        | new     | `make_environment` / `render` smoke tests; placeholder for future custom-filter tests (CL-2). |
| `tools/perf_bench.py`                         | new     | Benchmark CLI (FR-23). |
| `pyproject.toml`                              | edit    | `[tool.setuptools.package-data]` recursive globs `templates/**/*.j2` for `piketype.backends.{py,cpp,sv}` (FR-14). Empty `templates/` dirs are created so `package-data` matches once templates land. |
| `MANIFEST.in`                                 | new/edit| Include `src/piketype/backends/{py,cpp,sv}/templates/**/*.j2` (FR-14, defensive). |
| `docs/templates.md`                           | new     | Architecture, view-model + template rule, indirection-depth bound, custom-filters section, lint/bench instructions (FR-22, FR-24). |
| `specs/010-jinja-template-migration/perf.md`  | new     | Pre-migration `baseline_ms` row (CL-4, FR-25). Captured with `python tools/perf_bench.py > /dev/stdout`, then formatted into the FR-25 table. |
| `src/piketype/backends/{py,cpp,sv}/templates/`| new dirs| Empty placeholder so `package-data` glob matches; `.gitkeep` if needed. |

**Commit sequence (Phase 0):**

1. `feat(common): add make_environment and render helpers` — `render.py` + `tests/test_render.py`.
2. `feat(tools): add check_templates lint script` — `tools/check_templates.py` + `tests/test_check_templates.py`.
3. `feat(tools): add perf_bench CLI` — `tools/perf_bench.py`.
4. `feat(build): package backend templates with the wheel` — `pyproject.toml`, `MANIFEST.in`, empty `templates/` dirs.
5. `docs(templates): add developer-facing architecture doc` — `docs/templates.md`.
6. `steel(perf): capture pre-migration baseline_ms` — runs `tools/perf_bench.py` on `develop`@HEAD-equivalent and writes `specs/010-.../perf.md`. Per CL-4 this commit lands while emitters are still inline; the captured number reflects pre-migration timing.

**Critical gates after Phase 0 (no backend migration started yet):**
- Existing test suite still passes (no emitter change yet).
- `python tools/check_templates.py` exits 0 (no templates to flag).
- `python tools/perf_bench.py` produces a numeric line.
- `python -m unittest tests.test_render tests.test_check_templates` passes.
- `basedpyright --strict src/ tools/` passes.

---

## Phase 1 — Python backend migration (target backend, simplest output)

**Why first:** Per FR-5/CL-1, Python is the easiest target (no `#include`/preprocessor, no SV-specific packed-struct pragmas) so migration mechanics are validated on the simplest case before attacking C++/SV.

**Files created/modified:**

| Path                                              | Action  | Purpose |
|---------------------------------------------------|---------|---------|
| `src/piketype/backends/py/view.py`                | new     | View-model dataclasses + `build_*` functions (FR-1/8/18). |
| `src/piketype/backends/py/templates/module.j2`    | new     | Primary module template (FR-12). |
| `src/piketype/backends/py/templates/_macros.j2`   | new     | Shared macros: `scalar_alias`, `struct`, `flags`, `enum` (FR-12). |
| `src/piketype/backends/py/emitter.py`             | rewrite | Shrink to: build view → render → write. Remove `_render_*` helpers (FR-19). |
| `tests/test_view_py.py`                           | new     | View-model tests against `struct_padded`, `scalar_wide`, `enum_basic` (FR-18). |
| `specs/010-.../perf.md`                           | append  | `py-complete` row (FR-25). |

**View-model shape (sketch):**

```python
@dataclass(frozen=True, slots=True)
class ScalarAliasView:
    class_name: str
    width: int
    byte_count: int
    signed: bool
    min_value: int
    max_value: int
    mask: int            # 0 if width > 64
    sign_bit: int        # 0 if not signed
    pad_bits: int        # bytes_for_packing * 8 - width
    msb_byte_mask: int   # for wide unsigned tail mask
    is_wide: bool        # width > 64

@dataclass(frozen=True, slots=True)
class StructFieldView:
    name: str
    annotation: str        # pre-rendered "int", "bytes", "Foo | None"
    default_expr: str      # pre-rendered "field(default_factory=Foo)"
    is_struct_ref: bool
    target_class: str | None
    byte_count: int
    is_signed_scalar: bool
    is_wide_scalar: bool
    width: int
    mask: int              # 0 for wide
    pack_bits: int         # byte_count * 8 — pre-computed; FR-10 forbids template arithmetic
    sign_bit_value: int    # 0 if not signed
    msb_byte_mask: int

@dataclass(frozen=True, slots=True)
class StructView:
    class_name: str
    width: int
    byte_count: int
    fields: tuple[StructFieldView, ...]
    has_struct_fields: bool
    alignment_bytes: int

@dataclass(frozen=True, slots=True)
class EnumMemberView:
    name: str
    value_expr: str       # pre-rendered

@dataclass(frozen=True, slots=True)
class EnumView:
    class_name: str
    members: tuple[EnumMemberView, ...]
    underlying_int_type: str   # currently always "IntEnum"

@dataclass(frozen=True, slots=True)
class FlagsView:
    class_name: str
    width: int
    byte_count: int
    fields: tuple[FlagsFieldView, ...]   # detailed shape determined by current emitter

@dataclass(frozen=True, slots=True)
class ConstantView:
    name: str
    value_expr: str       # pre-rendered Python expression

@dataclass(frozen=True, slots=True)
class ModuleView:
    header: str                                            # from headers.py, FR-13
    has_types: bool
    has_structs: bool
    has_enums: bool
    has_flags: bool
    constants: tuple[ConstantView, ...]
    types: tuple[ScalarAliasView | StructView | EnumView | FlagsView, ...]
```

**Commit sequence (Phase 1):**

1. `feat(py): introduce view module and build helpers` — `view.py` (dataclasses + `build_module_view_py`), `tests/test_view_py.py`. Emitter still uses inline rendering at this point; view module is dormant.
2. `feat(py): module/file skeleton via template` — add `module.j2` rendering only the header + imports + footer; rest of body still inline. Verify byte parity.
3. `feat(py): scalar alias and constants via templates` — extract `_render_py_scalar_alias` body and constants block into `_macros.j2`. Verify byte parity.
4. `feat(py): struct rendering via templates` — extract struct dataclass scaffold, coercers, `to_bytes`, `from_bytes`, `clone` into macros. Verify byte parity.
5. `feat(py): enum and flags rendering via templates` — extract remaining type kinds. Verify byte parity.
6. `refactor(py): remove inline emitter helpers` — delete `_render_py_*` helpers (FR-19). `emit_py` now ≤ ~100 lines.
7. `steel(perf): record py-complete perf row` — append to `perf.md` (FR-25).

**Critical gates after Phase 1 (per-backend):**
- AC-1-Py: Golden bytes unchanged for all `gen/py/**` outputs.
- AC-2-Py: `find ... templates -name '*.j2'` ≥ 1; emitter imports `render`.
- AC-3-Py: `wc -l src/piketype/backends/py/emitter.py` strictly less than pre-migration 792.
- AC-4-Py: `view.py` contains only frozen dataclasses + `build_*` functions; basedpyright clean.
- AC-5-Py: `python tools/check_templates.py src/piketype/backends/py/templates/` exits 0.
- AC-6-Py: `python -m unittest tests.test_view_py` passes.
- AC-7-Py: idempotency test passes.

---

## Phase 2 — C++ backend migration

Same shape as Phase 1, with these adjustments specific to C++:

- View must precompute namespace nesting strings, include-guard symbol, and full pack/unpack helper bodies.
- Templates: `module.j2`, `_macros.j2` for `scalar_alias`, `struct`, `enum`, `flags`, plus a shared `_pack.j2` for the `to_bytes`/`from_bytes` skeleton if it improves clarity.
- C++ uses `#ifndef` include guards (constitution): the guard symbol is a precomputed `str` field on `ModuleView`.

**Files:** `src/piketype/backends/cpp/{view.py,templates/module.j2,templates/_macros.j2}`, `tests/test_view_cpp.py`.

**Commits:**
1. `feat(cpp): introduce view module and build helpers`.
2. `feat(cpp): module/file skeleton via template (header, includes, namespace open/close, guard)`.
3. `feat(cpp): scalar alias and constants via templates`.
4. `feat(cpp): struct rendering via templates`.
5. `feat(cpp): enum and flags rendering via templates`.
6. `refactor(cpp): remove inline emitter helpers`.
7. `steel(perf): record cpp-complete perf row`.

**Per-backend gates:** AC-*-Cpp.

---

## Phase 3 — SystemVerilog backend migration

Same shape, with SV-specific shape:

- Two output files per module: `<basename>_pkg.sv` and `<basename>_test_pkg.sv`. Two primary templates: `module_synth.j2` and `module_test.j2`. The build helper produces two view models (`ModuleSynthView`, `ModuleTestView`) sharing a common `BaseModuleView` of types and constants.
- SV `typedef struct packed { ... }` requires careful field-order preservation; the view's `fields` tuple iteration order is the IR's declaration order.
- Verification helper classes in `_test_pkg` are large fragments — they live as macros in `_macros.j2`.

**Files:** `src/piketype/backends/sv/{view.py,templates/module_synth.j2,templates/module_test.j2,templates/_macros.j2}`, `tests/test_view_sv.py`.

**Commits:**
1. `feat(sv): introduce view module and build helpers (synth + test views)`.
2. `feat(sv): synth package skeleton via template`.
3. `feat(sv): synth typedef rendering via templates`.
4. `feat(sv): test package skeleton via template`.
5. `feat(sv): verification helper classes via templates`.
6. `refactor(sv): remove inline emitter helpers`.
7. `steel(perf): record sv-complete perf row`.

**Per-backend gates:** AC-*-Sv.

---

## Phase 4 — Feature-final validation

Runs during the spec's `validation` Steel-Kit stage.

**Steps (each a single commit if a code change is needed):**

1. Run `python -m unittest discover tests` → must pass cleanly. **AC-F1.**
2. Run `basedpyright --strict src/ tools/` → zero errors. **AC-F2.**
3. Run `python tools/check_templates.py src/piketype/backends/{py,cpp,sv}/templates/` → exit 0. **AC-F3.**
4. Run `python tools/perf_bench.py`, append result as `feature-final` row to `perf.md`. Verify ≤ 1.25× baseline. **AC-F4.**
5. `pip wheel . -w /tmp/pike_wheel/ --no-deps` → `unzip -l /tmp/pike_wheel/pike_type-*.whl | grep templates/.*\.j2` shows nine .j2 files (3 backends × ≥3 templates each, modulo SV's 2-template count). Install into clean venv → run `piketype gen` against temp-copied fixture → diff against from-source generation. **AC-F5.**
6. `docs/templates.md` covers FR-22 + FR-24 items (manual checklist). **AC-F6.**
7. `python tools/check_templates.py src/piketype/backends/{py,cpp,sv}/templates/` exits 0 (same as AC-F3, repeated as AC-F7's audit form).
8. `git log --oneline develop..HEAD` shows commits grouped by Phase 0..3 in order; `git revert <range>` dry-runs cleanly per backend. **AC-F8.**

**Validation commit:** `steel(validation): record feature-final results` — appends row to `perf.md`, no source changes.

---

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Whitespace drift on first template render breaks goldens | High | Use `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True`. Migrate one helper at a time and diff goldens after each commit. |
| `PackageLoader` does not find templates from a wheel install | Medium | Phase 0 commit 4 verifies wheel packaging immediately by building the wheel and running smoke test before any backend touches templates. |
| View-model tests over-couple to internal numeric values that may change with refactors | Low | Tests assert public-contract values only (class names, widths, byte counts) — the same values that show up in goldens. |
| Performance regression > 25% from Jinja template loading overhead | Low–Medium | Measured at every per-backend completion (FR-25). Mitigation if exceeded: cache compiled templates at module-import time using `jinja2.Environment` cache (already enabled by default); switch from `PackageLoader` to a precompiled-modules loader if regression persists. |
| `frozen=True, slots=True` prevents `__post_init__` validation cleanly | Low | `__post_init__` may call `object.__setattr__` if needed; documented in `view.py` if any view requires post-init checks. View construction already validates upstream in builder functions, so post-init is rarely needed. |
| SV test-package verification helpers contain large mostly-static blocks that look "trivial" but matter for parity | Medium | Phase 3 splits synth and test rendering into separate templates so a parity break is localized to one file. Goldens fail-fast on byte diff. |

---

## Dependencies and ordering

- Phase 0 must complete before any of Phase 1/2/3 starts.
- Phase 1 → Phase 2 → Phase 3 (FR-5/CL-1).
- Phase 4 must be the last phase.
- Within each Phase 1/2/3 commit sequence, commit N+1 depends on commit N's byte parity verification.

## Out of plan (deliberately deferred)

- New view-model fields beyond what's needed to render current goldens.
- Refactoring `headers.py` (OOS-7).
- Migrating `runtime`/`build`/`lint`/`test` sub-backends (OOS-2).
- Splitting `view.py` into `view.py + builder.py` if line count grows past ~250 (FR-18 permits as a future refactor; not in this plan).

## Testing strategy

- **Existing golden integration tests:** unchanged. Run after every commit. Each commit's correctness criterion is golden bytes parity.
- **New view-model tests** (`tests/test_view_<lang>.py`): run after the Phase N introduction commit. They are leading indicators — they fail before goldens diverge.
- **New helper tests** (`tests/test_render.py`, `tests/test_check_templates.py`): run as part of Phase 0; the lint script is exercised against intentionally-bad fixture template strings (in-memory `DictLoader`).
- **Idempotency test:** unchanged; passes throughout because the migration changes how output is produced, not what is produced.

## Estimated commit count

- Phase 0: 6 commits
- Phase 1: 7 commits
- Phase 2: 7 commits
- Phase 3: 7 commits
- Phase 4: 1 commit
- Total: ~28 commits on `feature/010-jinja-template-migration`. Squash-on-merge optional per CL-1.
