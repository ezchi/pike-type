# Milestone 01: `Const()` SV-Only

## Objective

Deliver the smallest end-to-end slice that proves the architecture:

- repo-root resolution
- repo-wide DSL discovery
- normal Python module loading
- top-level `Const()` discovery
- frozen IR for constants only
- validation
- SystemVerilog package generation
- manifest generation
- CLI integration tests with golden outputs

This milestone intentionally supports only literal integer constants and only SystemVerilog emission.

## Scope

### In Scope

- `typist gen <file.py>`
- repo-root detection via `.git` or `pyproject.toml`
- repo-wide scan of `typist/` directories
- rejection of invalid `typist/` files
- minimal DSL runtime with `Const()`
- module-level direct-top-level constant discovery
- literal integer constants only
- package-scoped SV `localparam` generation
- generated file headers
- `gen/typist_manifest.json`

### Out of Scope

- Python generation
- C++ generation
- `Const()` expressions
- any type nodes beyond constants
- build/test/lint scaffolding

## User-Facing Behavior

Example input:

```python
# foo/typist/defs.py
FOO = Const(3)
BAR = Const(0)
```

Command:

```bash
typist gen foo/typist/defs.py
```

Expected outputs:

```text
gen/sv/foo/typist/defs_pkg.sv
gen/sv/runtime/typist_runtime_pkg.sv
gen/typist_manifest.json
```

## DSL Rules For This Milestone

- `Const()` may only appear at module top level as a direct binding.
- The Python variable name is the constant name.
- The argument must be an integer literal.
- Imported constants are dependencies, not local definitions.
- Anonymous temporaries do not count.
- A `typist/` file with zero discovered DSL objects is an error.

## Minimal Internal Design

### DSL Runtime

Needed pieces:

- `Const` runtime object
- base DSL object with source-location capture
- module-local registration mechanism
- final freeze into constant-only IR

The runtime object only needs:

- literal integer value
- source location
- binding name populated during discovery/freeze

### IR

Needed nodes:

- `RepoIR`
- `ModuleIR`
- `ModuleRefIR`
- `SourceSpanIR`
- `ConstIR`
- `IntLiteralExprIR`

### Validation

Needed checks:

- provided CLI file is under `typist/`
- provided CLI file defines DSL objects
- every scanned `typist/` non-`__init__.py` file defines at least one DSL object
- discovered DSL objects in scanned files are constants only
- constant names are unique within module
- constant values are integers

### SV Backend

Needed output:

- one package per module
- file naming: `<module>_pkg.sv`
- package-scoped `localparam`
- stable header metadata

Minimal package shape:

```systemverilog
package defs_pkg;
  localparam int FOO = 3;
  localparam int BAR = 0;
endpackage
```

The exact `int` vs width-specific parameter typing can remain simple in this milestone. Refinement can happen later if needed.

### Runtime Backend

This milestone should still generate:

- `gen/sv/runtime/typist_runtime_pkg.sv`

Even if it is effectively an empty placeholder package at first, generating it validates the stable runtime-path contract early.

### Manifest

The manifest must include:

- repo root
- discovered modules
- source paths
- constants
- source locations
- generated file paths

## Proposed Package Work Breakdown

### `repo.py` / `paths.py`

Implement:

- repo-root detection
- output-path helpers for SV packages, runtime package, manifest

### `discovery/scanner.py`

Implement:

- recursive repo scan
- `typist/` filtering
- `__init__.py` exclusion

### `loader/python_loader.py`

Implement:

- module execution from path
- normal import behavior rooted at repo

### `dsl/const.py`

Implement:

- `Const`

### `dsl/source_info.py`

Implement:

- stack-inspection-based location capture

### `ir/nodes.py`

Implement:

- minimal constant-only frozen dataclasses

### `validate/engine.py`

Implement:

- ordered validation entry point

### `backends/sv/emitter.py`

Implement:

- constant-only SV package emission

### `backends/runtime/emitter.py`

Implement:

- minimal runtime package emission

### `manifest/write_json.py`

Implement:

- stable manifest serialization

### `commands/gen.py`

Implement:

- orchestration for this milestone only

## Golden Test Plan

Fixture layout should model a small repo, for example:

```text
tests/fixtures/const_sv_basic/
  project/
    .git/
    foo/
      typist/
        defs.py
  expected/
    gen/
      sv/
      typist_manifest.json
```

Tests:

- success case with one module and multiple constants
- success case with multiple `typist/` modules in one repo
- failure when CLI path is not under `typist/`
- failure when a `typist/` file contains no DSL objects
- failure when a non-constant DSL object appears

Comparison mode:

- byte-for-byte golden comparison

## Exit Criteria

Milestone 01 is complete when:

- `typist gen <valid typist file>` works for constant-only fixture repos
- SV output matches goldens byte-for-byte
- runtime placeholder package is emitted in stable path
- manifest is emitted and stable
- invalid fixture repos fail with deterministic diagnostics
