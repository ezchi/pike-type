# Backend Templates and View Models

This document describes the architecture introduced by spec
[`010-jinja-template-migration`](../specs/010-jinja-template-migration/spec.md):
backend code emitters split semantics (Python view-model builders)
from presentation (Jinja2 templates).

## Architecture

```
IR (frozen)                             Templates (per backend)
   │                                            ▲
   ▼                                            │
build_module_view(module: ModuleIR)       env.get_template(...).render(**asdict(view))
   │                                            ▲
   ▼                                            │
ModuleView (frozen dataclass)  ─────────────────┘

emit_<lang>(repo) {
    env = make_environment(package="piketype.backends.<lang>")
    for module in repo.modules:
        view  = build_module_view(module=module, ...)
        text  = render(env=env, template_name="module.j2", context=view)
        write(path, text)
}
```

`make_environment` and `render` live in
[`piketype.backends.common.render`](../src/piketype/backends/common/render.py)
and are the only entry points production code uses to build a Jinja
environment or render a template.

## Worked example (Python backend)

For a single-scalar module like `tests/fixtures/scalar_wide`:

1. **IR (frozen):** the loader produces a `ModuleIR` with one
   `ScalarAliasIR(name="addr_t", resolved_width=32, signed=False, ...)`.
2. **View model construction:** `build_module_view_py(module=...)`
   walks the IR and produces a `ModuleView` containing one
   `ScalarAliasView(class_name="addr_ct", width=32, byte_count=4, ...)`
   with every numeric primitive (mask, sign-bit, padding bits, byte
   count) precomputed.
3. **Template rendering:** `module.j2` iterates over `types`,
   dispatches on the type's `kind` discriminator (or boolean
   discriminators), and emits the class header + helper-method
   bodies via macros from `_macros.j2`. The view model values
   appear as `{{ view.field }}` substitutions.
4. **Output:** the rendered string is written to
   `gen/py/alpha/piketype/types_types.py` byte-for-byte identical
   to the pre-migration emitter.

## What may live in templates

Templates render *structure and syntax*. They MAY contain:

- Jinja standard control flow: `{% if %}`, `{% for %}`, `{% set %}`,
  `{% include %}`, `{% extends %}`, `{% block %}`, `{% macro %}`.
- Jinja built-in string filters: `upper`, `lower`, `replace`, `join`,
  `indent`, `trim`.
- Custom filters defined in `backends/common/render.py` (see
  Custom Filters below).

Templates SHALL NOT:

- Compute padding, alignment, byte counts, masks, sign-extension
  boundaries, or any width-derived numeric value. These arrive as
  primitive view-model fields.
- Resolve type references or look up types by name.
- Decide signed vs. unsigned behavior. The view model provides
  signedness as a `bool` plus pre-computed numeric fragments.
- Duplicate validation logic from `validate/engine.py`.
- Embed Python code via the `{% python %}` extension.

The template lint script `tools/check_templates.py` enforces these
rules mechanically. See *Lint script* below.

### Indirection bound

Each backend's primary template (e.g. `module.j2`) may include or
extend at most one layer of macros/partials (e.g. `_macros.j2`).
That layer SHALL NOT include further partials. Inheritance via
`{% extends %}` counts as one level; `{% block %}` overrides do not.

This bound preserves the "find a generated construct in one place"
guarantee from NFR-5.

## Locations

| Backend       | View model + builders                          | Templates                                      |
|---------------|-------------------------------------------------|-----------------------------------------------|
| Python        | `src/piketype/backends/py/view.py`             | `src/piketype/backends/py/templates/`         |
| C++           | `src/piketype/backends/cpp/view.py`            | `src/piketype/backends/cpp/templates/`        |
| SystemVerilog | `src/piketype/backends/sv/view.py`             | `src/piketype/backends/sv/templates/`         |

Each backend has at least one *primary template* (`module.j2` for
Python and C++; `module_synth.j2` and `module_test.j2` for SV).
Macros and partials are file-prefixed with `_` (e.g. `_macros.j2`).

## Adding a new template or extending one

1. **Decide whether the addition belongs in the view model or the
   template.** Anything numeric (widths, byte counts, masks, sign
   bits, padding) belongs in the view model. Anything structural
   (file layout, class scaffolding, helper-method skeletons,
   iteration over fields) belongs in the template.
2. **Extend the view model.** Add the new field(s) to the relevant
   frozen dataclass in `view.py`; default them so existing builder
   call sites keep compiling. Add the field to `tests/test_view_<lang>.py`
   with at least one fixture-level assertion.
3. **Edit the template.** Reference the new field. If the change
   warrants a new macro, add it to `_macros.j2` and call it from
   the primary template.
4. **Run goldens.** `python -m unittest discover tests`. If output
   bytes change, see *Changing generated output* below.
5. **Run the lint:** `python tools/check_templates.py`. If the lint
   reports a violation in your edit, the template is doing
   semantics work — move it back to the view model.

## Adding a custom Jinja filter

Custom filters MAY be added on demand. They SHALL be:

- Pure functions over primitives (no IR access, no I/O,
  deterministic).
- Defined and registered only in
  `src/piketype/backends/common/render.py` (CL-2/FR-16 — single-site
  audit).
- Documented under *Custom Filters* below.
- Tested in `tests/test_render.py`.

To add a filter:

1. Define it in `backends/common/render.py` as a top-level
   `def my_filter(value: ...) -> str` function.
2. Inside `make_environment`, register it: `env.filters["my_filter"] = my_filter`
   immediately after constructing the `Environment`.
3. Append a row to *Custom Filters* below.
4. Add a unit test in `tests/test_render.py`.

### Custom Filters

Currently no custom filters are registered. Future entries
SHALL list: name, signature, deterministic guarantee, test
file location.

## Changing generated output

If a deliberate change to generated bytes is needed (for example,
to fix a long-standing whitespace bug discovered during migration):

1. Make the change in a separate, single-purpose commit BEFORE the
   template-landing commit. Subject: `fix(<scope>): ...` with a
   description of the byte change.
2. Regenerate the relevant goldens: copy the new output into
   `tests/goldens/gen/<case>/<lang>/...`. Commit the regenerated
   goldens alongside the fix.
3. The template-landing commit (or any subsequent migration commit)
   SHALL produce byte-identical output to the new goldens. No
   migration commit may include both a byte change and a template
   move.

This is the spec's FR-20 procedure. It exists so that template
moves remain mechanically verifiable as no-ops.

## Lint script

`python tools/check_templates.py [<path>...]` scans every `.j2`
file under the given paths (default: the three backend
`templates/` directories) for forbidden patterns inside Jinja
expression `{{ ... }}` and statement `{% ... %}` blocks.

Forbidden patterns (FR-21):

| ID   | Pattern (regex over Jinja-block contents)                        | Description                                |
|------|------------------------------------------------------------------|--------------------------------------------|
| P1   | `\(\s*1\s*<<\s*`                                                 | bit-shift mask construction                |
| P2   | `\bbyte_count\b\s*[-+*/]` or `[-+*/]\s*\bbyte_count\b`           | arithmetic on `byte_count` (either side)  |
| P3   | `\bhasattr\b` / `\bgetattr\b` / `\bisinstance\b`                 | runtime type interrogation                 |
| P4   | `\.__class__\b` / `\btype\s*\(`                                  | type lookup                                |
| P5   | `[-+*/]\s*8\b` / `\b8\s*[-+*/]`                                  | explicit byte arithmetic in Jinja          |
| P6   | `\bopen\s*\(` / `\bos\.` / `\bsys\.` / `\bsubprocess\.`         | stdlib/filesystem access                   |
| P7   | `\bnow\s*\(` / `\brandom\b` / `\buuid\b`                         | non-determinism source                     |
| P8 * | `\{%\s*python\b` (raw template body)                             | Python-embedding extension                 |

The patterns P1–P7 are scoped to Jinja-block contents only, so
target-language text outside blocks (e.g. SV `padded[WIDTH-1:0]`
or C++ `BYTE_COUNT * 8`) is never flagged. P8 is the only pattern
applied to the raw template body.

The lint is CI-mandatory: AC-F3/F7 require `tools/check_templates.py`
to exit 0 over all backend templates.

## Performance benchmark

`python tools/perf_bench.py [--fixture <name>] [--iterations <N>]`
runs `piketype gen` against a temp copy of the fixture and reports
median/min/max wall-clock time in milliseconds as a single
tab-separated line:

```
<fixture>\t<median_ms>\t<min_ms>\t<max_ms>
```

The output line is appended to
[`specs/010-jinja-template-migration/perf.md`](../specs/010-jinja-template-migration/perf.md)
to record per-stage measurements. The feature-final regression
budget is 1.25× the pre-migration baseline (NFR-1, AC-F4).
