# Task Breakdown — Jinja Template Migration

**Spec ID:** 010-jinja-template-migration
**Stage:** task_breakdown
**Source plan:** `specs/010-jinja-template-migration/plan.md`

Each task corresponds to one git commit on `feature/010-jinja-template-migration` (per CL-1). Tasks are listed in dependency order; T-N must complete before T-(N+1) starts unless explicitly noted as parallel-safe.

Format per task: `T-NN`, subject, files touched, exit criteria, AC mapping.

---

## Phase 0 — Shared Infrastructure

### T-01: Add `make_environment` and `render` helpers
- **Files:** `src/piketype/backends/common/render.py` (rewrite from stub), `tests/test_render.py` (new).
- **Implementation:**
  - `render.py` exposes `make_environment(*, package: str) -> jinja2.Environment` with the exact options pinned in plan.md (`PackageLoader(package, "templates")`, `keep_trailing_newline=True`, `trim_blocks=True`, `lstrip_blocks=True`, `undefined=jinja2.StrictUndefined`, `autoescape=False`).
  - `render(*, env, template_name, context)` rejects non-dataclass and class-type context; calls `asdict(context)`; appends a trailing `\n` if the rendered template does not end in one.
  - `tests/test_render.py` uses `unittest.TestCase`. Cases: (a) dataclass context renders correctly; (b) dict context raises `TypeError`; (c) trailing newline is added when missing; (d) `make_environment` returns an Environment whose `loader` is a `PackageLoader` and whose `undefined` is `StrictUndefined`.
- **Exit criteria:** `python -m unittest tests.test_render` passes; `basedpyright --strict src/piketype/backends/common/render.py tests/test_render.py` clean.
- **AC mapping:** FR-2, FR-3, FR-16. Foundational for AC-2-Py/Cpp/Sv.

### T-02: Add `tools/check_templates.py` lint script
- **Files:** `tools/check_templates.py` (new), `tests/test_check_templates.py` (new).
- **Implementation:**
  - CLI: `python tools/check_templates.py [<path>...]`. With no args, defaults to scanning `src/piketype/backends/{py,cpp,sv}/templates/`.
  - Parses each `.j2` file and extracts text inside `{{ ... }}` and `{% ... %}` blocks (not `{# ... #}` comments). Implementation uses `re.finditer` with two patterns: `r"\{\{(.+?)\}\}"` and `r"\{%(.+?)%\}"`, both non-greedy, both with `re.DOTALL`.
  - Forbidden patterns (regex over Jinja-block contents only): per FR-21 patterns 1–7. Pattern 8 (`{%\s*python\b`) scans the raw template body.
  - Returns non-zero exit and prints `<file>:<line>:<column> <pattern-id> <matched-text>` for each violation.
  - `tests/test_check_templates.py` (`unittest.TestCase`): one `assertNotEqual(0, exit_code)` test per FR-21 pattern using a `tempfile.NamedTemporaryFile` containing a minimal `.j2` whose Jinja block hits exactly that pattern; one `assertEqual(0, exit_code)` test showing target-language text outside Jinja blocks (e.g. raw `padded[WIDTH-1:0]` SystemVerilog) is not flagged.
- **Exit criteria:** `python -m unittest tests.test_check_templates` passes; `python tools/check_templates.py src/piketype/backends/` exits 0 (no templates yet).
- **AC mapping:** FR-21. Foundational for AC-5-*, AC-F3, AC-F7.

### T-03: Add `tools/perf_bench.py`
- **Files:** `tools/perf_bench.py` (new).
- **Implementation:**
  - CLI per FR-23: `python tools/perf_bench.py [--fixture <name>] [--iterations <N>] [--output <path>]`. Defaults: `--fixture struct_padded`, `--iterations 5`, `--output -`.
  - For each iteration: copies `tests/fixtures/<fixture>/project/` to `tempfile.mkdtemp()`, calls `piketype.commands.gen.run_gen(<tmp>/alpha/piketype/types.py)` with `time.perf_counter` measurement, discards the temp dir.
  - Discards iteration 0 as warm-up; computes median/min/max of remaining iterations in milliseconds.
  - Output: single line `<fixture>\t<median_ms>\t<min_ms>\t<max_ms>\n` with three-decimal-place numbers.
- **Exit criteria:** `python tools/perf_bench.py` produces a numeric line; `basedpyright --strict tools/perf_bench.py` clean.
- **AC mapping:** FR-23. Foundational for AC-F4.

### T-04: Configure wheel packaging for templates
- **Files:** `pyproject.toml` (edit), `MANIFEST.in` (new or edit).
- **Implementation:**
  - Add `[tool.setuptools.package-data]` entries: `"piketype.backends.py" = ["templates/**/*.j2"]`, `"piketype.backends.cpp" = ["templates/**/*.j2"]`, `"piketype.backends.sv" = ["templates/**/*.j2"]`.
  - `MANIFEST.in` adds `recursive-include src/piketype/backends/py/templates *.j2` and analogous lines for `cpp` and `sv`.
  - **No template directories created yet.** First `.j2` file lands in T-09 (Phase 1 commit 2).
- **Exit criteria:** `pip wheel . -w /tmp/pike_wheel_t04/ --no-deps` succeeds (wheel produced; templates package-data globs match zero files at this point, which is allowed).
- **AC mapping:** FR-14. Foundational for AC-F5.

### T-05: Add `docs/templates.md`
- **Files:** `docs/templates.md` (new).
- **Implementation:**
  - Sections per FR-22 + FR-24:
    1. Architecture overview (IR → view-model → template → output) with one Python worked example.
    2. "What may live in templates" rule with cross-references to FR-10 / FR-11 and the two-level indirection bound.
    3. How to add a new template or extend an existing one.
    4. Location of templates and view models per backend.
    5. Procedure for changing generated output (regen goldens, separate commit per FR-20).
    6. How to run `python tools/check_templates.py` and what it enforces.
    7. **Custom Filters** section (per FR-24): one paragraph stating that filters are defined and registered only in `backends/common/render.py`; followed by an empty bullet list "Currently no custom filters." This list is appended-to as filters are added during migration.
- **Exit criteria:** Document exists and is internally cross-referenced.
- **AC mapping:** FR-22, FR-24. Foundational for AC-F6.

### T-06: Capture pre-migration baseline_ms
- **Files:** `specs/010-jinja-template-migration/perf.md` (new).
- **Implementation:**
  - Run `python tools/perf_bench.py --fixture struct_padded`. Capture stdout.
  - Format `perf.md` per FR-25:
    ```
    | stage          | backend | median_ms | min_ms | max_ms |
    |----------------|---------|-----------|--------|--------|
    | baseline       | -       | <num>     | <num>  | <num>  |
    ```
  - Subsequent rows (`py-complete`, `cpp-complete`, `sv-complete`, `feature-final`) are appended in T-15, T-22, T-29, T-32 respectively.
- **Exit criteria:** `perf.md` exists with the baseline row populated.
- **AC mapping:** CL-4, FR-25. Foundational for AC-F4.

**Phase 0 gate (after T-06):** `python -m unittest discover tests` passes; `basedpyright --strict src/ tools/` passes; `pip wheel . -w /tmp/pike_wheel/ --no-deps` succeeds. No emitter changes yet.

---

## Phase 1 — Python Backend Migration

### T-07: Introduce `backends/py/view.py` and view-model tests
- **Files:** `src/piketype/backends/py/view.py` (new), `tests/test_view_py.py` (new).
- **Implementation:**
  - All view-model dataclasses per plan.md Phase 1 sketch: `ConstantView`, `ScalarAliasView`, `EnumMemberView`, `EnumView`, `FlagFieldView`, `FlagsView`, `StructFieldView`, `StructView`, `ModuleView` (with `body_lines: tuple[str, ...]` + `has_body_lines: bool`).
  - Builders: `build_module_view_py(*, module: ModuleIR) -> ModuleView`, `_build_scalar_alias_view`, `_build_struct_view`, `_build_struct_field_view`, `_build_enum_view`, `_build_flags_view`, `_build_constant_view`. All keyword-only.
  - Tests against fixtures `struct_padded`, `scalar_wide`, `enum_basic`. One assertion per non-trivial view-model field per fixture.
  - Emitter unchanged at this point. View module is dormant.
- **Exit criteria:** `python -m unittest tests.test_view_py` passes; `basedpyright --strict src/piketype/backends/py/view.py tests/test_view_py.py` clean; existing tests still pass.
- **AC mapping:** FR-1, FR-8, FR-9, FR-18. Lays foundation for AC-1-Py..AC-7-Py.

### T-08: First Python template — module skeleton (FR-6 sub-step 1)
- **Files:** `src/piketype/backends/py/templates/module.j2` (new), `src/piketype/backends/py/emitter.py` (edit).
- **Implementation:**
  - `module.j2`: renders `{{ header }}\n` + import block (`{% if has_types %}from __future__ import annotations\n{% if has_structs %}\nfrom dataclasses import dataclass, field\n{% endif %}{% if has_enums %}\nfrom enum import IntEnum\n{% endif %}\n{% endif %}` per current emitter rules) + `{% if has_body_lines %}{{ body_lines | join("\n") }}\n{% endif %}` for the rest.
  - `emit_py` constructs `ModuleView` with `body_lines = tuple(legacy_render_body_lines(module))` (a temporary helper that returns the post-header lines from the legacy `render_module_py`) and `has_body_lines = True`.
  - All other view fields are populated but unused by `module.j2` at this point.
- **Exit criteria:** `python -m unittest discover tests` passes — every `gen/py/**` golden byte-identical.
- **AC mapping:** FR-6 sub-step 1, FR-7. Wheel packaging now exercises one real template.
- **Wheel smoke check (sub-AC-F5):** `pip wheel . -w /tmp/pike_wheel_t08/ --no-deps && unzip -l /tmp/pike_wheel_t08/pike_type-*.whl | grep "piketype/backends/py/templates/module.j2"` must show one match.

### T-09: Top-level type declaration skeletons (FR-6 sub-step 2)
- **Files:** `src/piketype/backends/py/templates/_macros.j2` (new), `templates/module.j2` (edit), `view.py` (edit), `emitter.py` (edit).
- **Implementation:**
  - `_macros.j2` defines `scalar_class_skeleton(view)`, `struct_class_skeleton(view)`, `enum_classes_skeleton(view)`, `flags_class_skeleton(view)`. Each emits *only* the class header lines (e.g., `class addr_ct:\n    WIDTH = 32\n    SIGNED = False\n    BYTE_COUNT = 4\n`).
  - `module.j2` adds a `{% for type in types %}{% if type.kind == "scalar" %}{{ macros.scalar_class_skeleton(type) }}...{% endif %}{% endfor %}` loop, using a `kind: str` discriminator added to each TypeView (`"scalar" | "struct" | "enum" | "flags"`).
  - View gains a per-TypeView transitional `helper_lines: tuple[str, ...]` field carrying the pre-helper-method body still being rendered inline. `module.j2` emits this verbatim after the class skeleton block.
  - `body_lines` is now populated only with module-level constant lines and inter-type blank lines.
- **Exit criteria:** All `gen/py/**` goldens byte-identical. Test suite passes.
- **AC mapping:** FR-6 sub-step 2, FR-7.

### T-10: Helper-method skeletons (FR-6 sub-step 3)
- **Files:** `templates/_macros.j2` (edit), `view.py` (edit), `emitter.py` (edit).
- **Implementation:**
  - Macros gain `to_bytes_block(view)`, `from_bytes_block(view)`, `coerce_block(view)`, `setattr_block(view)`, `clone_block(view)`, `eq_repr_block(view)`. Each consumes precomputed numeric primitives from the relevant View dataclass.
  - The per-TypeView `helper_lines` transitional field is removed; its content is now produced by the macros.
  - `body_lines` is now populated only with module-level constant lines.
- **Exit criteria:** All `gen/py/**` goldens byte-identical. Test suite passes.
- **AC mapping:** FR-6 sub-step 3, FR-7.

### T-11: Expression and field-level fragments (FR-6 sub-step 4)
- **Files:** `templates/_macros.j2` (edit), `templates/module.j2` (edit), `view.py` (edit), `emitter.py` (edit).
- **Implementation:**
  - Constants are now rendered from `ConstantView.value_expr` directly (no Python concatenation in `emit_py`).
  - Struct field annotations/defaults/coercer literals are rendered from view fields (`StructFieldView.annotation`, `.default_expr`).
  - Enum member values use `EnumMemberView.resolved_value_expr`.
  - Flag mask literals use `FlagFieldView.bit_mask`.
  - `body_lines` is now an empty tuple in all cases; `has_body_lines` is `False`. The `{% if has_body_lines %}` block in `module.j2` becomes dead code (still present but never triggered).
- **Exit criteria:** All `gen/py/**` goldens byte-identical. Test suite passes.
- **AC mapping:** FR-6 sub-step 4, FR-7.

### T-12: Remove inline emitter helpers (cleanup)
- **Files:** `src/piketype/backends/py/emitter.py` (edit, large deletion), `view.py` (edit, remove `body_lines`/`has_body_lines`/`helper_lines`).
- **Implementation:**
  - Delete every `_render_py_*` helper and the legacy `render_module_py` body. `emit_py` becomes ≤ ~40 lines: build view, construct env, render `module.j2`, write file.
  - Remove transitional `body_lines` and `has_body_lines` from `ModuleView` (and any per-TypeView transitional fields). Update `module.j2` to remove the `{% if has_body_lines %}` block.
- **Exit criteria:** `wc -l src/piketype/backends/py/emitter.py` ≪ 792; `find src/piketype/backends/py/templates -name '*.j2'` ≥ 2; `grep "from piketype.backends.common.render" src/piketype/backends/py/emitter.py` matches; all goldens byte-identical; `python tools/check_templates.py src/piketype/backends/py/templates/` exits 0.
- **AC mapping:** AC-1-Py..AC-5-Py, AC-7-Py, FR-19.

### T-13: Record `py-complete` perf row
- **Files:** `specs/010-jinja-template-migration/perf.md` (edit, append row).
- **Implementation:** Run `python tools/perf_bench.py --fixture struct_padded`, append `py-complete` row to the table.
- **Exit criteria:** `perf.md` contains both `baseline` and `py-complete` rows.
- **AC mapping:** FR-25.

**Phase 1 gate (after T-13):** AC-1-Py..AC-7-Py all met. Verifiable by:
- Golden tests pass (AC-1-Py).
- `find src/piketype/backends/py/templates -name '*.j2' | wc -l` ≥ 2 and `grep "from piketype.backends.common.render" src/piketype/backends/py/emitter.py` (AC-2-Py).
- `wc -l src/piketype/backends/py/emitter.py` < 792 (AC-3-Py).
- View-model field types are FR-8 compliant (AC-4-Py).
- `python tools/check_templates.py src/piketype/backends/py/templates/` (AC-5-Py).
- `python -m unittest tests.test_view_py` (AC-6-Py).
- Existing idempotency test passes (AC-7-Py).

---

## Phase 2 — C++ Backend Migration

### T-14: Introduce `backends/cpp/view.py` and tests
- **Files:** `src/piketype/backends/cpp/view.py` (new), `tests/test_view_cpp.py` (new).
- **Implementation:** All Cpp* dataclasses per plan.md Phase 2 sketch. Builders: `build_module_view_cpp(*, module, namespace=None) -> CppModuleView`, helpers per type kind. Tests against `struct_padded`, `scalar_wide`, `enum_basic`, `const_cpp_wide`, plus the `namespace_override` fixture for `--namespace` override.
- **Exit criteria:** `python -m unittest tests.test_view_cpp` passes; basedpyright clean; existing tests pass.
- **AC mapping:** FR-1, FR-8, FR-9, FR-18.

### T-15: C++ module skeleton (FR-6 sub-step 1)
- **Files:** `templates/cpp/module.j2` (new), `cpp/emitter.py` (edit).
- **Implementation:** `module.j2` emits header + guard `#ifndef`/`#define` + standard includes (in declaration order from `standard_includes` tuple) + namespace open + body passthrough + namespace close + guard `#endif`. `emit_cpp` populates `body_lines` from the legacy renderer.
- **Exit criteria:** All `gen/cpp/**` goldens byte-identical, including `namespace_override` fixture.
- **AC mapping:** FR-6 sub-step 1.

### T-16: C++ top-level class scaffolding (FR-6 sub-step 2)
- **Files:** `templates/cpp/_macros.j2` (new), edits to `module.j2`, `view.py`, `emitter.py`.
- **Implementation:** Macros for `scalar_class_skeleton`, `struct_class_skeleton`, `enum_classes_skeleton`, `flags_class_skeleton`. Helper-method bodies still rendered inline as transitional `helper_lines: tuple[str, ...]` per TypeView.
- **Exit criteria:** All `gen/cpp/**` goldens byte-identical.

### T-17: C++ helper-method skeletons (FR-6 sub-step 3)
- **Files:** `templates/cpp/_macros.j2` (edit), `view.py` (edit), `emitter.py` (edit).
- **Implementation:** Macros render `to_bytes`/`from_bytes` helper bodies, signed-padding branches, sign-extension blocks, switch validators. Consumes view-model literal-form primitives (`mask_literal`, `sign_bit_literal`, `full_range_literal`, `byte_total_mask_literal`, `msb_byte_mask_literal`) and discriminators (`is_narrow_signed`, `has_signed_padding`, `has_signed_short_width`).
- **Exit criteria:** All `gen/cpp/**` goldens byte-identical.

### T-18: C++ expression and field-level fragments (FR-6 sub-step 4)
- **Files:** `templates/cpp/_macros.j2` (edit), `view.py` (edit), `emitter.py` (edit).
- **Implementation:** Constants rendered from `CppConstantView.value_expr`; enum member literals from `CppEnumMemberView.value_literal`; struct field declarations from `CppStructFieldView.decl`. `body_lines` becomes empty.
- **Exit criteria:** All `gen/cpp/**` goldens byte-identical.

### T-19: Remove inline C++ emitter helpers (cleanup)
- **Files:** `cpp/emitter.py` (large deletion), `view.py` (remove transitional fields).
- **Exit criteria:** AC-1-Cpp..AC-5-Cpp, AC-7-Cpp met. `wc -l src/piketype/backends/cpp/emitter.py` ≪ 1067.

### T-20: Record `cpp-complete` perf row
- **Files:** `perf.md` (append).
- **Exit criteria:** Row appended.
- **AC mapping:** FR-25.

**Phase 2 gate (after T-20):** AC-1-Cpp..AC-7-Cpp met.

---

## Phase 3 — SystemVerilog Backend Migration

### T-21: Introduce `backends/sv/view.py` and tests
- **Files:** `src/piketype/backends/sv/view.py` (new), `tests/test_view_sv.py` (new).
- **Implementation:** All Sv* dataclasses per plan.md Phase 3 sketch. Builders: `build_synth_module_view_sv` and `build_test_module_view_sv`. Tests against `struct_padded`, `scalar_wide`, `enum_basic`, `scalar_sv_basic`, `nested_struct_sv_basic`.
- **Exit criteria:** `python -m unittest tests.test_view_sv` passes.

### T-22: SV synth + test package skeletons (FR-6 sub-step 1)
- **Files:** `templates/sv/module_synth.j2` (new), `templates/sv/module_test.j2` (new), `sv/emitter.py` (edit).
- **Implementation:** Both primary templates emit package open/close + header + body passthrough.
- **Exit criteria:** All `gen/sv/**` goldens byte-identical.

### T-23: SV synth typedef scaffolding + test helper-class scaffolding (FR-6 sub-step 2)
- **Files:** `templates/sv/_macros.j2` (new), edits.
- **Implementation:** Macros for synth typedefs (scalar/struct/flags/enum) and test helper-class skeletons. Pack/unpack function bodies and helper-method bodies still passthrough.
- **Exit criteria:** All `gen/sv/**` goldens byte-identical.

### T-24: SV pack/unpack functions + test helper-method skeletons (FR-6 sub-step 3 — largest commit for SV)
- **Files:** `templates/sv/_macros.j2` (edit), `view.py` (edit), `emitter.py` (edit).
- **Implementation:**
  - Pack functions: macro selects on `SvPackUnpackScalarView` / `Flags` / `Enum` / `Struct` discriminator and emits the appropriate function body (identity / concat / cast / field-concat).
  - Unpack functions: same selection, with reversed field iteration for struct unpack and per-bit unpack for flags.
  - Helper-class methods (`to_bytes`/`from_bytes`/`pack`/`unpack`) emit through dedicated macros consuming `SvHelperStructFieldView.mask_literal`, `.sign_bit_literal`, `.pack_bits`, etc.
- **Exit criteria:** All `gen/sv/**` goldens byte-identical, including the largest fixtures (`struct_padded`, `nested_struct_sv_basic`).

### T-25: SV expression and field-level fragments (FR-6 sub-step 4)
- **Files:** `templates/sv/_macros.j2` (edit), `view.py` (edit), `emitter.py` (edit).
- **Implementation:** Constants render via `SvConstantView.sv_expr`; enum members via the `(name, value_expr)` tuples; flag field declarations via `SvFlagsTypedefView.field_names`. `body_lines` empty everywhere.
- **Exit criteria:** All `gen/sv/**` goldens byte-identical.

### T-26: Remove inline SV emitter helpers (cleanup)
- **Files:** `sv/emitter.py` (large deletion), `view.py` (remove transitional fields).
- **Exit criteria:** AC-1-Sv..AC-5-Sv, AC-7-Sv met. `wc -l src/piketype/backends/sv/emitter.py` ≪ 949.

### T-27: Record `sv-complete` perf row
- **Files:** `perf.md` (append).
- **AC mapping:** FR-25.

**Phase 3 gate (after T-27):** AC-1-Sv..AC-7-Sv met.

---

## Phase 4 — Validation

### T-28: Run feature-final test suite and lint
- **Action:** `python -m unittest discover tests`; `basedpyright --strict src/ tools/`; `python tools/check_templates.py src/piketype/backends/{py,cpp,sv}/templates/`.
- **Exit criteria:** All exit 0.
- **AC mapping:** AC-F1, AC-F2, AC-F3, AC-F7.

### T-29: Run feature-final perf and verify gate
- **Action:** Run `python tools/perf_bench.py --fixture struct_padded`. Append `feature-final` row to `perf.md`. Compute `feature-final.median_ms / baseline.median_ms` and verify ≤ 1.25.
- **Exit criteria:** Gate satisfied or perf-regression issue documented.
- **AC mapping:** AC-F4, FR-25.

### T-30: Wheel install end-to-end
- **Action:** `pip wheel . -w /tmp/pike_wheel_validation/ --no-deps`. `unzip -l /tmp/pike_wheel_validation/pike_type-*.whl` and grep all `*.j2` paths; diff against `find src/piketype/backends/{py,cpp,sv}/templates -name '*.j2'`. Install into clean venv. Run `piketype gen` against a temp copy of `tests/fixtures/struct_padded/project/` from both source and wheel installs; diff outputs.
- **Exit criteria:** Identical generated bytes; identical `.j2` file list.
- **AC mapping:** AC-F5.

### T-31: Manual checklist of `docs/templates.md`
- **Action:** Cross-check `docs/templates.md` against FR-22 + FR-24 enumeration. All items present.
- **AC mapping:** AC-F6.

### T-32: Commit-history audit
- **Action:** `git log --oneline develop..HEAD` shows Phase 0..3 commits in order, contiguous per backend. Dry-run `git revert <sha-range>` for each backend's commit range.
- **AC mapping:** AC-F8.

### T-33: Validation summary commit
- **Files:** `perf.md` (already updated in T-29).
- **Commit subject:** `steel(validation): record feature-final results`.

**Phase 4 gate (after T-33):** AC-F1..AC-F8 all met.

---

## Retrospect (Phase 5)

### T-34: Record retrospect notes
- **Files:** `specs/010-jinja-template-migration/retrospect.md` (new).
- **Action:** Document lessons learned, memory candidates (none expected since the migration is structural and the patterns are now codified in `docs/templates.md`), workflow improvements.

---

## Dependency graph

```
T-01 → T-02 → T-03 → T-04 → T-05 → T-06   (Phase 0)
                                    ↓
T-07 → T-08 → T-09 → T-10 → T-11 → T-12 → T-13   (Phase 1)
                                          ↓
T-14 → T-15 → T-16 → T-17 → T-18 → T-19 → T-20   (Phase 2)
                                          ↓
T-21 → T-22 → T-23 → T-24 → T-25 → T-26 → T-27   (Phase 3)
                                          ↓
T-28 → T-29 → T-30 → T-31 → T-32 → T-33   (Phase 4)
                                    ↓
T-34   (Phase 5 retrospect)
```

T-01..T-06 are strictly sequential within Phase 0 (each has prerequisite tooling). T-07 may begin in parallel with later Phase 0 tasks once T-01 lands (it only depends on `render.py` for the import path), but the plan keeps them serial for review clarity.

## Total: 34 tasks → ~28 commits (T-28..T-32 are validation actions, not commits; T-33 is the only validation commit).
