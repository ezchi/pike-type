# `piketype.yaml` configuration reference

`piketype.yaml` is the single source of truth for a piketype project.
It anchors the project root, declares which language backends to emit,
and configures per-backend output locations.

## Discovery

The tool finds `piketype.yaml` two ways:

1. **`--config <path>`** — explicit; wins if provided.
2. **Upward walk from CWD** — convenience for `cd` + run.

The directory containing `piketype.yaml` is the **project root**. All
relative paths in the YAML are anchored at the project root, never at
the caller's CWD.

## Generating a default

```
piketype init [--force] [--path DIR]
```

Writes a starter `piketype.yaml` to `DIR` (default: cwd). Refuses to
overwrite an existing file unless `--force` is passed.

The default file declares all four built-in backends:

```yaml
backends:
  sv:
    backend_root: ""    # empty -> project root
    language_id: rtl
  sim:
    backend_root: ""
    language_id: sim
  py:
    backend_root: py
    language_id: ""
  cpp:
    backend_root: cpp
    language_id: ""
```

## Schema

```yaml
frontend:               # optional
  piketype_root: ...    # optional, default = project root
  ir_cache: ...         # optional, default = <project_root>/.piketype-cache
  exclude: [...]        # optional, list of glob strings (reserved)

backends:               # optional but typically required
  <backend_id>:
    backend_root: ...   # optional, default = project root
    language_id: ...    # optional, default = ""
```

Unknown keys at any level cause a hard error so typos surface early.

### `frontend` section

| Key             | Type           | Default                          | Purpose |
|-----------------|----------------|----------------------------------|---------|
| `piketype_root` | path           | project root                     | the directory tree the build walks looking for `<sub>/piketype/<base>.py` |
| `ir_cache`      | path           | `<project_root>/.piketype-cache` | where the build writes per-module IR JSON, the index, and `diagnostics.json` |
| `exclude`       | list of globs  | `[]`                             | reserved for future glob-based exclusion (currently unused) |

### `backends` section

Each entry is a backend identifier mapped to its config. The four
canonical IDs and what they emit:

| ID    | Emits                                  | Basename suffix | Extension |
|-------|----------------------------------------|-----------------|-----------|
| `sv`  | SystemVerilog synthesis package        | `_pkg`          | `.sv`     |
| `sim` | SystemVerilog test/verification package| `_test_pkg`     | `.sv`     |
| `py`  | Python wrapper module                  | `_types`        | `.py`     |
| `cpp` | C++ header                             | `_types`        | `.hpp`    |

Each backend section accepts:

| Key            | Type   | Default           | Purpose |
|----------------|--------|-------------------|---------|
| `backend_root` | path   | project root      | output root for this backend's files; empty resolves to project root |
| `language_id`  | string | `""`              | optional single-segment subdirectory inserted before the file (e.g. `rtl`, `sim`, `cpp`) |

A backend that is not listed in `backends:` is **disabled** — no files
are emitted for it, and it does not appear in the manifest's
`generated_outputs` map.

## Path mapping

For input `<piketype_root>/<sub>/piketype/<base>.py` the output is:

```
<backend.backend_root>/<sub>/[<backend.language_id>/]<base><suffix><ext>
```

Steps:

1. Strip `piketype_root` prefix from the input path.
2. Drop the trailing `piketype/<base>.py` segment, keeping `<sub>`.
3. Join: `<backend_root>/<sub>/[<language_id>/]<base><suffix><ext>`.
   Empty `language_id` collapses that segment.

### Example: HDL role next to source, language packages above source

Config:

```yaml
backends:
  sv:  {language_id: rtl}             # backend_root defaults to project root
  sim: {language_id: sim}
  py:  {backend_root: py}             # language_id defaults to ""
  cpp: {backend_root: cpp}
```

Input `alpha/piketype/foo.py` produces:

```
alpha/rtl/foo_pkg.sv             (HDL role lives next to source)
alpha/sim/foo_test_pkg.sv
py/alpha/foo_types.py            (package root above source)
cpp/alpha/foo_types.hpp
```

### Example: per-language output roots with a language subdirectory

Config:

```yaml
backends:
  py:
    backend_root: python_lib
  cpp:
    backend_root: includes
    language_id: cpp
```

Input `services/auth/piketype/user.py` (default `piketype_root`) produces:

| Backend | Output |
|---------|--------|
| py      | `python_lib/services/auth/user_types.py` |
| cpp     | `includes/services/auth/cpp/user_types.hpp` |

If `frontend.piketype_root: services` is set, the same input produces:

| Backend | Output |
|---------|--------|
| py      | `python_lib/auth/user_types.py` |
| cpp     | `includes/auth/cpp/user_types.hpp` |

## Source layout requirements

DSL source files **must** live at `<sub>/piketype/<base>.py` — the
parent directory of every DSL file must be exactly `piketype/`.

Files whose basename starts with `_` (e.g. `_helper.py`, `_common.py`)
are skipped: they remain importable from sibling DSL modules but
produce no output. The skip is recorded in `diagnostics.json` with code
`underscore-skip`.

`__init__.py` is always skipped.

## Discovery exclusions

The build skips these directory names anywhere under `piketype_root`:
`.venv`, `venv`, `.git`, `node_modules`, `.tox`, `__pycache__`.

## Python import contract

The Python backend assumes `backends.py.backend_root` is on
`PYTHONPATH` at runtime. Generated files therefore import each other by
`<sub>`-rooted paths, not by their on-disk location:

* Same `<sub>` (intra-prefix): relative import,
  e.g. `from .foo_types import foo_ct`.
* Different `<sub>` (cross-prefix): absolute import,
  e.g. `from auth.user_types import user_ct`.

## Diagnostics

After every build, the tool writes `<ir_cache>/diagnostics.json`:

```json
{
  "diagnostics": [
    {"severity": "info",  "code": "underscore-skip", "message": "..."},
    {"severity": "error", "code": "module-cycle",    "message": "..."}
  ]
}
```

Severities:

| Severity  | Meaning |
|-----------|---------|
| `info`    | informational; e.g. an underscore-prefixed file was skipped |
| `warning` | non-fatal issue; build proceeds |
| `error`   | fatal; build exits non-zero, downstream `gen` refuses to emit |

Codes used today: `underscore-skip`, `module-cycle`. Additional codes
may be introduced; consumers should match by code when filtering.

## Two-stage execution model

`piketype` runs as two cooperating stages:

```
piketype build   →  reads sources, executes Python, writes IR cache
piketype gen     →  reads IR cache, runs language backends
piketype gen     →  if invoked alone, runs build first in-process,
                    then runs all enabled backends
```

The IR cache is at `<frontend.ir_cache>` and contains:

| File                                | Purpose |
|-------------------------------------|---------|
| `_index.json`                       | schema_version, tool_version, module summaries with source hashes |
| `<sub>/<base>.ir.json`              | per-module IR (mirrors source tree) |
| `diagnostics.json`                  | build diagnostics |

Backends never read source files — they read the cache. This makes
language backends independent and parallelizable, and it lets future
incremental builds skip Python re-execution when sources have not
changed.

## Schema versioning

The cache index carries a `schema_version` integer. A version mismatch
on read raises a hard error with a "regenerate IR cache" message. Bump
the version on any breaking change to IR shape (renamed/removed
fields, changed encoding); additive-only changes (new optional fields
with defaults) do not require a bump.
