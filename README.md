# typist

`typist` is a Python-based code generator for FPGA-oriented type definitions.

The long-term goal is to let users define canonical hardware-oriented types once in normal Python modules and generate:

- synthesizable SystemVerilog
- verification-oriented SystemVerilog helpers without UVM
- Python modeling/helper code
- C++ controller/simulation/helper code

SystemVerilog is the canonical layout. Python and C++ are generated as software-facing views with conversion helpers.

## Status

This repository is in early development.

Implemented today:

- project architecture and RFC/spec documents
- installable Python package scaffold with CLI entry point
- milestone 01 end-to-end flow for `Const()` only
- repo-wide scanning of `typist/` modules
- SystemVerilog package generation for module-level integer constants
- generated runtime placeholder package
- generated JSON manifest
- fixture-style integration tests

Current milestone:

- `Const()` SV-only generation

Not implemented yet:

- Python generation
- C++ generation
- constant expressions
- scalar aliases with `Bit()` / `Logic()`
- structs, arrays, enums, unions
- build/test/lint scaffolding generation

## Repository Docs

- [docs/rfc-v1.md](docs/rfc-v1.md): shorter RFC-style product document
- [docs/v1-product-spec.md](docs/v1-product-spec.md): fuller v1 product spec
- [docs/architecture.md](docs/architecture.md): internal package/module architecture
- [docs/ir-schema.md](docs/ir-schema.md): frozen IR design
- [docs/milestone-01-const-sv.md](docs/milestone-01-const-sv.md): current milestone scope

## Current DSL Example

Today, milestone 01 supports only top-level integer constants:

```python
from typist.dsl import Const

FOO = Const(3)
BAR = Const(0)
```

When placed in a file such as:

```text
alpha/typist/constants.py
```

running:

```bash
typist gen alpha/typist/constants.py
```

generates:

```text
gen/sv/alpha/typist/constants_pkg.sv
gen/sv/runtime/typist_runtime_pkg.sv
gen/typist_manifest.json
```

with SV output shaped like:

```systemverilog
package constants_pkg;
  localparam int FOO = 3;
  localparam int BAR = 0;
endpackage
```

## Project Layout

```text
src/typist/
  cli.py
  commands/
  discovery/
  dsl/
  ir/
  loader/
  validate/
  backends/
  manifest/

docs/
tests/
```

High-level flow:

1. Find repo root from the provided file path.
2. Scan the repo for all Python files under `typist/`.
3. Load those modules with normal Python import semantics.
4. Freeze discovered DSL objects into IR.
5. Validate the IR.
6. Emit generated outputs.
7. Write `gen/typist_manifest.json`.

## CLI

Planned commands:

```bash
typist gen <path/to/file.py>
typist build <path/to/file.py>
typist test <path/to/file.py>
typist lint <path/to/file.py>
```

Only `typist gen` has milestone-01 behavior implemented.

## Development

This project targets:

- Python 3.12+
- `basedpyright` for strict static checking
- `pytest` for the long-term test runner

Current local verification commands:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Packaging

The repo is scaffolded as an installable Python package with CLI entry point:

```bash
pip install -e .
```

Then:

```bash
typist gen path/to/repo/module/typist/file.py
```

## Roadmap

Planned near-term sequence:

1. `Const()` across all three languages
2. `Const()` expressions
3. named scalar aliases with `Bit()` / `Logic()`
4. `Struct()`
5. nested structs
6. arrays in structs
7. `Enum()`
8. `Union()`

The detailed milestone order is documented in [docs/v1-product-spec.md](docs/v1-product-spec.md).
