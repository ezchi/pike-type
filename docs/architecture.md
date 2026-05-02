# Pike-type Architecture

## Purpose

This document turns the v1 product spec into an implementation shape for the `piketype` codebase. It defines the internal package boundaries, the end-to-end execution pipeline, and the ownership of major responsibilities.

The design goal is to keep these boundaries stable:

- Python DSL execution stays separate from validated IR
- validation stays separate from code generation
- backends consume only frozen IR
- generated runtime support is treated as a backend output, not handwritten infrastructure

## Design Principles

- Keep the core IR language-agnostic.
- Keep the CLI thin and orchestration-focused.
- Keep backend-specific policy out of the DSL runtime.
- Prefer explicit immutable boundaries over implicit shared state.
- Optimize for deterministic output and fixture-based testing.

## Top-Level Flow

The end-to-end flow for every command is:

1. Resolve the repo root from the provided file path.
2. Validate that the provided file is a valid DSL module under `piketype/`.
3. Scan the repo for all DSL modules under all `piketype/` directories.
4. Load those Python modules with normal Python import semantics.
5. Capture top-level DSL definitions and dependencies.
6. Freeze the discovered DSL object graph into IR input state.
7. Build the frozen validated IR.
8. Run validation passes over the IR.
9. Emit generated outputs for the selected command.
10. Emit or update the repo-level manifest.

The same discovery and IR pipeline is shared by:

- `piketype gen`
- `piketype build`
- `piketype test`
- `piketype lint`

The only difference is the emitter set and output roots used by the command.

## Proposed Package Layout

```text
src/piketype/
  __init__.py
  cli.py
  errors.py
  paths.py
  repo.py
  discovery/
    __init__.py
    scanner.py
    module_name.py
  loader/
    __init__.py
    python_loader.py
    module_context.py
  dsl/
    __init__.py
    base.py
    const.py
    scalar.py
    struct.py
    array.py
    enum.py
    union.py
    field_options.py
    software_view.py
    source_info.py
    registry.py
    freeze.py
  ir/
    __init__.py
    nodes.py
    builders.py
    manifest_view.py
  validate/
    __init__.py
    engine.py
    naming.py
    topology.py
    widths.py
    collisions.py
    cross_language.py
  backends/
    __init__.py
    registry.py
    common/
      __init__.py
      headers.py
      ordering.py
      render.py
    sv/
      __init__.py
      emitter.py
      templates/
    py/
      __init__.py
      emitter.py
      templates/
    cpp/
      __init__.py
      emitter.py
      templates/
    runtime/
      __init__.py
      emitter.py
      templates/
    build/
      __init__.py
      emitter.py
      templates/
    test/
      __init__.py
      emitter.py
      templates/
    lint/
      __init__.py
      emitter.py
      templates/
  manifest/
    __init__.py
    model.py
    write_json.py
  commands/
    __init__.py
    gen.py
    build.py
    test.py
    lint.py
```

## Responsibilities By Package

### `cli.py`

Owns:

- top-level `argparse` wiring
- command dispatch
- top-level error-to-exit-code mapping

Does not own:

- repo scanning logic
- Python module execution
- validation
- code generation

### `repo.py` and `paths.py`

Own:

- repo-root detection
- canonical path calculations
- output-root resolution
- mapping source modules to generated file paths

These modules should be the single source of truth for path and naming conventions used across commands and backends.

### `discovery/`

Owns:

- repo-wide scanning for `piketype/` modules
- filtering out `__init__.py`
- enforcing the “all non-`__init__.py` files in `piketype/` are DSL modules” rule
- calculating module identity from path

Should not import the DSL runtime directly.

### `loader/`

Owns:

- loading DSL modules with normal Python import execution
- installing any temporary load context needed for DSL object registration
- tracking which discovered definitions belong to which source module

The loader is responsible for executing Python. It should be the narrowest possible layer that touches import machinery.

### `dsl/`

Owns:

- runtime DSL object model
- builder-style mutation APIs
- source-location capture
- temporary mutable construction state
- freezing DSL objects into IR input state

Important boundary:

- DSL objects are mutable only during module execution
- after freezing, backends and validators must not consume these objects directly

### `ir/`

Owns:

- frozen immutable domain model consumed by validators and backends
- IR construction from frozen DSL state
- helper projections used by manifest generation

The IR is the most important architectural boundary in the project.

### `validate/`

Owns:

- all semantic checks over the frozen IR
- validation ordering
- stop-at-first-error behavior
- cross-language compatibility checks

Validation should be implemented as explicit passes, not hidden inside emitters.

One such cross-language check is the **reserved-keyword validation pass** (`_validate_reserved_keywords` in `validate/engine.py`). It runs after all structural and cross-module passes and rejects user-supplied DSL identifiers (type names, struct fields, flags fields, enum values, constants, module basenames) whose emitted form collides with a reserved keyword in any active target language (SystemVerilog, C++20, Python 3.12). The keyword sets live in `validate/keywords.py` as frozen `frozenset[str]` snapshots — IEEE 1800-2017 ∪ 1800-2023 for SV, ISO C++20 (N4861 §2.13) reserved keywords plus alternative tokens plus `import`/`module` for C++, and `keyword.kwlist ∪ keyword.softkwlist` snapshotted from CPython 3.12.x for Python. The module-name check uses per-language emitted forms (SV: `<base>_pkg`; C++/Python: bare base) so that, for example, a module file named `logic.py` is accepted (the SV package becomes `logic_pkg`, not a keyword) while `class.py` is rejected (C++ namespace `class` and Python module `class` are both keywords).

### `backends/`

Own:

- file emission from IR
- template rendering
- generated headers
- stable output ordering
- command-specific scaffolding outputs

The backend registry should allow the command layer to say “emit generation outputs” or “emit build scaffolding” without embedding backend knowledge in the CLI.

### `manifest/`

Owns:

- the JSON manifest model
- stable serialization
- writing `gen/piketype_manifest.json`

The manifest should be derived entirely from frozen IR plus output-path resolution.

### `commands/`

Own:

- high-level command orchestration over shared pipeline pieces
- selecting the emitter set for the command

These modules should remain thin glue layers.

## Data Model Boundaries

There are four important states in the pipeline.

### 1. Discovered Source Modules

This is path- and repo-oriented metadata:

- repo root
- DSL module file paths
- Python import/module identities
- source namespace identities

This state exists before any Python execution.

### 2. Mutable DSL Runtime Graph

This is the result of executing user Python modules:

- runtime DSL objects
- top-level bindings
- dependency references
- source locations captured from stack inspection

This state is not safe for backends to consume directly.

### 3. Frozen IR

This is the stable, immutable semantic graph:

- modules
- constants
- types
- members
- expressions
- source locations
- dependencies

This is the primary input to validation and generation.

### 4. Generated Output Plan

This is a command-specific projection of IR into files to write:

- target file path
- backend identity
- rendered content

Keeping this as a separate step makes testing easier and keeps file I/O away from semantic logic.

## Command Architecture

Each command should follow the same orchestration template:

1. Build repository context.
2. Discover repo-wide DSL modules.
3. Load and freeze DSL modules.
4. Build IR.
5. Validate IR.
6. Emit command-specific outputs.
7. Write manifest.

### `piketype gen`

Emits:

- SV source
- Python source
- C++ source
- shared runtime support
- manifest

### `piketype build`

Emits:

- top-level CMake scaffolding
- build runner scripts
- manifest

### `piketype test`

Emits:

- generated test source files
- top-level test scripts
- manifest

### `piketype lint`

Emits:

- lint config/scaffolding
- lint runner scripts
- manifest

## Error Model

Errors should be explicit, typed exceptions. Proposed categories:

- repo/discovery errors
- module loading errors
- DSL freezing errors
- IR build errors
- validation errors
- emission/rendering errors

Every error should carry:

- a user-readable message
- source path and line information when available
- generated target path when relevant

The command layer converts these into concise terminal output and a non-zero exit code.

## Determinism Strategy

Determinism should be enforced structurally, not treated as a formatter side-effect.

Key rules:

- deterministic discovery ordering by canonical path
- deterministic module and definition ordering in IR
- dependency order first, declaration order second
- no timestamps or run-specific metadata in generated output
- stable JSON serialization for manifest output
- stable template context construction

## Template Strategy

Jinja2 is the rendering engine, but templates should not be asked to compute semantics.

Recommended structure:

1. Build a backend-specific view model from IR.
2. Hand that view model to the template.
3. Keep templates mostly declarative.

This avoids semantic drift across templates and makes output easier to test.

## Source Location Strategy

Source locations are captured in the DSL runtime via stack inspection on:

- object creation
- `add_member(...)`
- `add_value(...)`

Locations are carried into the IR and then into validation errors and manifest entries.

The system should prefer exact DSL source locations over generated paths, but preserve both when available.

## Runtime Support Generation

Shared runtime support is generated, not handwritten.

Generated runtime roots:

```text
gen/sv/runtime/
gen/py/runtime/
gen/cpp/runtime/
```

These runtime artifacts should be emitted on every `gen` run, regardless of whether user DSL modules changed.

Runtime support is conceptually its own backend because:

- it is generated
- it is shared by many module outputs
- it should be versioned and tested like any other backend output

## Testing Implications

This architecture is chosen to support fixture-driven testing cleanly.

Recommended test split:

- unit tests for repo/discovery/path logic
- unit tests for DSL object behavior
- unit tests for IR construction
- unit tests for validation passes
- golden-file integration tests for command outputs over fixture repos

Because the file-output plan is separated from IR and validation, golden tests can be written at either:

- rendered-output level
- file-plan level

## Recommended First Implementation Slice

The first implementation slice should reach this boundary:

- working repo-root detection
- working repo-wide DSL discovery
- minimal `Const()` DSL runtime
- frozen IR for constants only
- validation for constant naming/top-level-only/literal-only
- SV backend for package-scoped `localparam`
- manifest generation
- fixture-based CLI tests

This slice is small enough to validate the architecture and large enough to exercise every major layer.
