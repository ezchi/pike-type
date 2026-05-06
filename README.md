# pike-type

`piketype` is a Python-based code generator for FPGA-oriented type definitions.

Define canonical hardware-oriented types once in normal Python modules and generate:

- synthesizable SystemVerilog (`sv` backend)
- verification-oriented SystemVerilog helpers without UVM (`sim` backend)
- Python wrapper modules with `pack`/`unpack`/`to_lv`/`from_lv`/`compare` helpers (`py` backend)
- C++ headers for controllers / sims / helpers (`cpp` backend)

SystemVerilog is the canonical layout. Python and C++ are generated as software-facing views.

## Status

Implemented:

- DSL: `Const`, `VecConst`, scalar aliases via `Bit()`/`Logic()`, `Struct` (with padding,
  `multiple_of`, signed fields), `Enum`, `Flags`, nested structs, cross-module type refs
- Backends: `sv`, `sim`, `py`, `cpp`
- Python runtime helpers: `pack` / `unpack` / `to_lv` / `from_lv` / `compare`
- `piketype.yaml`-driven projects with explicit project root and per-backend output layout
- Frontend / backend split: `piketype build` writes a JSON IR cache;
  `piketype gen` reads the cache and runs backends without executing user Python
- Build-stage diagnostics (skipped modules, import cycles) persisted to
  `<ir_cache>/diagnostics.json`
- Generated `piketype_manifest.json`
- Fixture-based golden tests across all backends

## Repository Docs

- [docs/piketype-yaml.md](docs/piketype-yaml.md): `piketype.yaml` configuration reference
- [docs/rfc-v1.md](docs/rfc-v1.md): shorter RFC-style product document
- [docs/v1-product-spec.md](docs/v1-product-spec.md): fuller v1 product spec
- [docs/architecture.md](docs/architecture.md): internal package/module architecture
- [docs/ir-schema.md](docs/ir-schema.md): frozen IR design

## Quick start

Scaffold a default config in the current directory:

```bash
piketype init
```

This writes `piketype.yaml` declaring all four backends with co-located output dirs:

```yaml
frontend:
  ir_cache: .piketype-cache

backends:
  sv:  { out: rtl }
  sim: { out: sim }
  py:  { out: py }
  cpp: { out: cpp }
```

Place DSL modules under `<sub>/piketype/<name>.py` anywhere below the directory
holding `piketype.yaml`. For example:

```python
# alpha/piketype/types.py
from piketype.dsl import Const, Struct, U

FOO = Const(3)

class Header(Struct):
    version: U(4)
    length:  U(12)
```

Then run:

```bash
piketype gen
```

`piketype.yaml` is found by walking up from the current directory (or pass
`--config <path>` to override). For the example above, output lands at:

```text
rtl/alpha/types_pkg.sv          # from sv backend (suffix layout)
sim/alpha/types_test_pkg.sv     # from sim backend
py/alpha/types_types.py         # from py backend (prefix layout)
cpp/alpha/types_types.hpp       # from cpp backend
piketype_manifest.json
.piketype-cache/                # IR cache + diagnostics.json
```

## CLI

```bash
piketype init [--force] [--path DIR]    # write a default piketype.yaml
piketype build [--config PATH]          # frontend only: refresh IR cache
piketype gen   [--config PATH] [--lang sv|sim|py|cpp] [--namespace NS]
piketype test  [PATH]
piketype lint  [PATH]
```

`piketype gen` runs the build in-process to refresh the cache, then reads the
cache and runs the selected backends. It never executes user Python — all
language-running happens in the build stage. `--lang` restricts to one backend;
omit it to run all enabled backends.

## Project Layout

```text
src/piketype/
  cli.py                # argparse entry point
  commands/             # init, build, gen, test, lint
  config/               # piketype.yaml schema + loader + discovery
  discovery/            # module scanner + dep-graph cycle detection
  dsl/                  # user-facing DSL (Const, Struct, Enum, ...)
  ir/                   # frozen IR node types
  ir_io/                # JSON cache: codec, schema, diagnostics
  loader/               # Python module loader for the build stage
  validate/             # IR validation passes
  backends/             # sv / sim / py / cpp emitters (Jinja-based)
  manifest/             # piketype_manifest.json writer
  paths.py              # backend output-path computation

docs/
tests/
```

High-level flow:

1. **Discover** — find `piketype.yaml` (explicit `--config` or upward walk).
2. **Build (frontend)** — scan `<piketype_root>` for `<sub>/piketype/<base>.py`,
   load with normal import semantics, freeze into IR, validate.
3. **Cache** — write per-module `*.ir.json` + `_index.json` + `diagnostics.json`
   under `frontend.ir_cache`. Build fails (after persisting diagnostics) if any
   error-severity diagnostic is recorded — e.g. an import cycle.
4. **Gen (backend)** — read the cache, run each enabled backend's emitter,
   write `piketype_manifest.json`.

The `SCHEMA_VERSION` pinned in `_index.json` forces a rebuild whenever the IR
on-disk shape changes.

## Development

- Python 3.12+
- `basedpyright` for strict static checking
- `pytest` as the test runner

Local verification:

```bash
python3 -m compileall src tests
pytest
pytest -n auto                          # parallel via pytest-xdist
pytest tests/test_ir_cache.py           # single file
```

## Packaging

```bash
pip install -e .
piketype init
piketype gen
```
