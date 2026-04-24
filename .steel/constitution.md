# Project Constitution

## Governing Principles

1. **Single source of truth.** Hardware-oriented types are defined once in Python DSL modules. All generated outputs (SystemVerilog, C++, Python) are derived from that single definition.
2. **Immutable boundaries.** The pipeline has four distinct stages (Discovery -> DSL -> IR -> Backends) with frozen, immutable handoff between them. Backends and validators consume only frozen IR, never mutable DSL objects.
3. **Deterministic output.** Generated code must be byte-for-byte reproducible given the same inputs. No timestamps, run-specific metadata, or non-deterministic ordering.
4. **Correctness over convenience.** Strict type checking, explicit validation passes, and golden-file testing guard against silent regressions. If something cannot be validated, it should not be generated.
5. **Templates are declarative.** Rendering logic must not compute semantics. Backend-specific view models are built from IR first, then handed to the rendering step.
6. **Generated runtime, not handwritten.** Shared runtime support packages are generated outputs, not manually maintained infrastructure.

## Technology Stack

| Component            | Technology                | Version/Notes                                |
|----------------------|---------------------------|----------------------------------------------|
| Implementation       | Python                    | >= 3.12                                      |
| Package build        | setuptools + wheel        | setuptools >= 69                             |
| Project metadata     | `pyproject.toml`          | PEP 621                                      |
| Template engine      | Jinja2                    | >= 3.1 (declared; backends currently render via string building) |
| Static type checking | basedpyright              | >= 1.20.0, strict mode                       |
| Test runner          | unittest (stdlib)         | Golden-file / fixture-based integration tests |
| CLI framework        | argparse (stdlib)         | Thin dispatch layer                          |
| License              | GPL-3.0-or-later          |                                              |
| Target outputs       | SystemVerilog, C++17, Python 3.12+ |                                      |

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
- SystemVerilog outputs use `_pkg` suffix for synthesizable packages and `_test_pkg` for verification-only packages.
- C++ headers use include guards (`#ifndef`/`#define`/`#endif`), not `#pragma once`.
- Python generated modules include `__init__.py` files for the full package chain.

### Project Layout

```
src/typist/          -- implementation source
  cli.py             -- thin CLI entry point
  commands/          -- command orchestration (gen, build, test, lint)
  discovery/         -- repo scanning for typist/ modules
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
  2. Runs `typist gen` via subprocess.
  3. Compares the full `gen/` output tree byte-for-byte against `tests/goldens/gen/<case>/`.
- **Idempotency tests** verify that running `typist gen` twice on the same input produces identical output and does not rescan generated files as DSL modules.
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
