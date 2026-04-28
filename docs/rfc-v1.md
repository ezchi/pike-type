# RFC: Pike-type V1

## Status

Draft

## Summary

`piketype` is a Python-based code generator for FPGA-oriented type definitions. Users author normal Python modules under repo `piketype/` directories using a builder-style DSL, and `piketype` generates SystemVerilog, Python, and C++ artifacts from a frozen validated intermediate representation.

SystemVerilog is the canonical layout. Python and C++ generated code may use more ergonomic software representations as long as conversions are correct and deterministic.

V1 focuses on:

- canonical type definition in Python
- SystemVerilog synthesis and verification packages
- Python and C++ software views with generated conversion helpers
- repo-wide deterministic generation
- generated build, lint, and test scaffolding

## Motivation

FPGA projects often need the same data model represented in multiple languages:

- SystemVerilog for RTL and verification
- Python for modeling, verification, and tooling
- C++ for FPGA control, Verilator simulation, and hardware-side utilities

Maintaining those definitions by hand is error-prone, especially when bit layout is important and software-friendly representations differ from hardware-efficient packed encodings. `piketype` addresses that by letting users define types once and generate target-specific code plus conversion helpers.

## Goals

- Let users define hardware-oriented types in normal executable Python modules.
- Keep SystemVerilog as the canonical representation and layout reference.
- Generate both synthesizable and verification-oriented SystemVerilog packages.
- Generate Python and C++ software representations with helper methods such as `to_slv()`, `from_slv()`, `to_bytes()`, and `from_bytes()`.
- Provide a structure that is easy to extend in-repo with new type kinds and new backends.
- Guarantee deterministic output for identical repo content and tool version.
- Support repo-wide regeneration from any valid `piketype/` module path.

## Non-Goals

V1 explicitly does not optimize for:

- UVM
- commercial simulators
- schema evolution / backward compatibility
- dynamic SV types
- forward references
- circular type graphs
- external plugin-defined type systems
- user-configurable style/layout/naming knobs

## User-Facing Design

### Authoring Model

Users write normal Python modules under directories literally named `piketype/`.

Example:

```text
foo/piketype/packet_defs.py
bar/piketype/common_types.py
```

The DSL is normal Python and supports normal imports. Files should remain LSP-friendly and navigable as ordinary Python modules.

### Discovery Rules

- Only non-`__init__.py` files inside `piketype/` are treated as DSL modules.
- Every such file must define at least one DSL object or the command fails.
- Only direct top-level bindings count as discovered definitions.
- Anonymous temporary DSL objects are rejected.
- Imported DSL objects are dependencies, not definitions in the importing module.
- A DSL object bound to multiple top-level names in the same module is an error.
- DSL objects may originate only from `piketype/` modules.
- `piketype_utils.py` may exist anywhere in the repo as helper code, but it must not define DSL objects.

### CLI

V1 commands:

- `piketype gen <path/to/file.py>`
- `piketype build <path/to/file.py>`
- `piketype test <path/to/file.py>`
- `piketype lint <path/to/file.py>`

CLI input rules:

- file path only
- one root file per invocation
- provided file must be under a `piketype/` directory
- provided file must itself define DSL objects

Repo root discovery:

- walk upward from the provided file until `.git` or `pyproject.toml` is found

Repo-wide behavior:

- the provided file is used only as a validity anchor and repo-root locator
- once accepted, the tool scans all `piketype/` modules across the repo
- generation and scaffolding are repo-wide

## DSL Overview

V1 uses a builder-style API only.

Core constructs:

- `Const()`
- `Bit(width, signed=False)`
- `Logic(width, signed=False)`
- `Struct().add_member(...)`
- `Array(elem_t, size)`
- `Enum().add_value(...)`
- `Union().add_member(...)`

Example:

```python
FOO = Const(3)

addr_t = Bit(13)

packet_t = (
    Struct()
    .add_member("addr", addr_t)
    .add_member("flag", Bit(1), rand=False)
)
```

Naming rules:

- user-defined type names must end with `_t`
- generated software/helper class names replace trailing `_t` with `_ct`
- field names must be `snake_case`
- enum value names must be `UPPER_CASE`

Restrictions:

- only backward references through normal Python execution order
- packed arrays only
- compile-time constant array sizes only
- zero-width types are invalid
- zero-length arrays are invalid
- self-referential type graphs are invalid
- union members must have equal width

## Semantics

### Constants

V1 constants are:

- top-level only
- integer-valued only
- immutable
- named by Python variable binding

Examples:

```python
FOO = Const(3)
BAR = Const(FOO + 5)
```

Expression support is preserved only when users build expressions through `Const()` objects and supported overloaded operators.

Generated forms:

- SystemVerilog: package-scoped `localparam`
- Python: plain module constant
- C++: header-only `constexpr`

### Scalars

Named scalar aliases such as `addr_t = Bit(13)` are supported.

SystemVerilog:

- `Bit` maps to `bit`
- `Logic` maps to `logic`
- signedness is emitted directly in the typedef

Python and C++:

- named scalar aliases generate lightweight wrapper classes
- wrapper names replace `_t` with `_ct`
- width <= 64 uses integer storage
- width > 64 uses bytes/vector storage

Validation:

- values must fit declared width and signedness
- out-of-range assignment is rejected
- signed software values use normal signed integers
- packing uses two's-complement truncation to width

### Structs

Canonical SV form:

- `typedef struct packed`

Rules:

- first added field maps to the most-significant bits
- dependency order is primary
- original declaration order is the tie-breaker

Generated SV verification helpers:

- live in a separate verification package
- store field properties as primary state
- no cached packed value
- `pack()` and `unpack()` convert to and from the packed typedef
- all fields are `rand` by default, overridable per field

Generated Python and C++ classes:

- store field values/objects as primary state
- recompute packed form on demand
- named scalar member assignment may accept plain primitives and auto-wrap
- composite member assignment requires proper generated composite objects

### Arrays

V1 arrays are:

- packed only
- constant-sized only

Layout rule:

- element index `0` maps to the least-significant packed slice

Software ergonomic views:

- Python: ordinary `list[...]`
- C++: `std::vector<T>`

### Enums

Enums support:

- explicit values
- auto-filled unspecified values
- numbering starting at `0`
- inferred width from largest enumerator value
- non-negative values only

Generated software forms:

- real enum type exists separately
- naming example: `state_t` -> `state_enum_t`
- wrapper class naming example: `state_t` -> `state_ct`

The wrapper stores the enum member as primary state. Unknown encoded values from `from_slv()` or `from_bytes()` are rejected.

### Unions

Canonical SV form:

- `typedef union packed`

Rules:

- only named member views in the DSL
- direct exposure of all views
- first member is treated as canonical for helper-generation decisions
- that rule must be documented in generated output

Generated Python and C++ unions:

- store one canonical packed backing state
- all views remain synchronized through that shared storage

## Cross-Language Conversion Rules

Global policies:

- SystemVerilog is canonical
- one strict global bit-ordering policy
- little-endian byte order globally
- packed struct ordering matches SV packed struct ordering
- array index `0` maps to least-significant slice
- enum packed value is the inferred underlying integer value

Generated API:

- `to_slv()`
- `from_slv()`
- `to_bytes()`
- `from_bytes()`

Python:

- `to_slv()` returns `int`
- `from_slv()` accepts `int`
- `from_bytes()` accepts `bytes` and `bytearray`

C++:

- `to_slv()` returns `std::vector<uint8_t>`
- `from_slv()` accepts `std::vector<uint8_t>`
- `from_bytes()` accepts `std::vector<uint8_t>`

`Logic(...)` in software:

- represented as 2-state only
- `X` and `Z` coerce to `0`
- warning is emitted only when a shared runtime verbose/debug flag is enabled

## Namespacing and Output Layout

Default output root:

```text
gen/
```

Per-language output roots:

```text
gen/sv/
gen/py/
gen/cpp/
```

Example source:

```text
foo/piketype/packet_defs.py
```

Example outputs:

```text
gen/sv/foo/piketype/packet_defs_pkg.sv
gen/sv/foo/piketype/packet_defs_test_pkg.sv
gen/py/foo/piketype/packet_defs_types.py
gen/cpp/foo/piketype/packet_defs_types.hpp
gen/cpp/foo/piketype/packet_defs_types.cpp
```

Runtime support files are generated into stable tool-owned paths:

```text
gen/sv/runtime/piketype_runtime_pkg.sv
gen/py/runtime/piketype_runtime.py
gen/cpp/runtime/piketype_runtime.hpp
gen/cpp/runtime/piketype_runtime.cpp
```

SystemVerilog namespace rule:

- package name comes from module basename only
- collision detection is enforced
- users are responsible for avoiding basename collisions

Python namespace rule:

- generated package structure mirrors filesystem layout
- the literal `piketype` directory is preserved
- `__init__.py` files are generated as needed

C++ namespace rule:

- namespace is derived from repo-relative path
- the literal `piketype` directory is skipped in the namespace
- the filesystem include path keeps `piketype`

## Architecture

The required internal split is:

- DSL runtime objects during module execution
- frozen validated IR
- backend-specific generators

Backends must not consume mutable DSL runtime objects directly.

IR requirements:

- language-agnostic core representation
- target-specific choices represented as neutral semantic policies/annotations
- manifest derived from the frozen validated IR only

Generation style:

- template-based
- Jinja2

Extensibility:

- new type kinds are added in-repo by extending the core IR and generators
- language backends use an in-repo registry model
- no external plugin system for type kinds in v1

## Diagnostics

Diagnostics should point to both:

- original DSL source locations
- generated file locations where relevant

Source tracking should be captured automatically through DSL runtime stack inspection on object creation and builder calls.

Validation behavior:

- fail fast
- stop at first error
- reject invalid widths/sizes
- reject self-referential type graphs
- reject duplicate generated names within a namespace
- reject invalid `piketype/` files with no DSL objects

## Manifest

The tool generates:

```text
gen/piketype_manifest.json
```

Purpose:

- internal tooling and scripts

Contents:

- discovered modules
- source paths
- namespaces
- types and constants
- dependencies
- source locations
- generated output paths
- semantic inventory from frozen validated IR

## Build, Test, and Lint Scaffolding

These commands generate scaffolding rather than executing external tools directly.

### Build

`piketype build` generates top-level build-system scaffolding for the repo.

V1 build scope:

- CMake only
- focused on C++ and Verilator flows
- separate SV and C++ targets
- generated convenience runner:
  - `gen/build/run_build.sh`

### Test

`piketype test` generates:

- per-module generated tests
- top-level runner scaffolding

Generated top-level test runners:

- `gen/test/run_sv_test.sh`
- `gen/test/run_cpp_test.sh`
- `gen/test/run_py_test.sh`

Frameworks:

- SystemVerilog: custom class-based piketype pattern, no UVM
- Python: `pytest`
- cocotb is a hard dependency and runs through the pytest flow
- C++: GoogleTest

Generated test coverage should include:

- roundtrip packing
- byte roundtrip
- getters/setters
- equality/inequality
- string representation smoke
- clone/copy behavior
- compare/diff behavior
- randomization smoke
- union shared-storage behavior
- array packing order

Cross-language tests use shared canonical test vectors generated automatically by `piketype`.

### Lint

`piketype lint` generates repo-wide lint config/scaffolding and runners.

Recommended v1 tools:

- Python: `ruff`
- tool codebase typing: `basedpyright`
- C++: `clang-tidy`, `clang-format`
- SystemVerilog: `verilator --lint-only`, `slang`

Generated lint runners:

- `gen/lint/run_lint.sh`
- `gen/lint/run_lint.py`

V1 is check-only and does not auto-fix.

## Determinism

The tool should guarantee byte-for-byte identical output across runs when:

- repo content is unchanged
- tool version is unchanged

Generated file headers should include:

- generated by `piketype`
- source DSL module path(s)
- do not edit by hand warning

Headers must avoid timestamps and other run-specific data.

## Testing Strategy For Pike-type Itself

The `piketype` codebase itself is:

- pure Python 3.12+
- installable as a normal Python package with a CLI entry point
- statically checked with `basedpyright` only

Tool tests:

- Python `pytest` only
- CLI-driven integration tests over checked-in fixture repos
- golden-file comparison byte-for-byte
- fixture repos should represent repo-wide scenarios with one or more `piketype/` directories
- golden outputs should include runtime support files
- `gen`, `build`, `test`, and `lint` should have separate golden expectations

## Milestones

Planned v1 implementation order:

1. `Const()` SV-only, literal integers only
2. `Const()` across all three languages
3. `Const()` expressions
4. named scalar aliases with `Bit()` / `Logic()` in SV
5. named scalar aliases in Python/C++
6. `Struct()` in SV
7. `Struct()` in Python/C++
8. nested structs
9. arrays in structs
10. `Enum()` in SV
11. `Enum()` in Python/C++
12. `Union()` in SV with scalar/raw members
13. `Union()` in Python/C++
14. struct members in unions
15. arrays in unions

Staging rule:

- for each new type feature, complete SystemVerilog first
- then add Python/C++
- then add generated test/build/lint scaffolding for that feature
- then move to the next type feature

## Open Questions Deferred Beyond V1

- constants depending on type properties such as widths
- additional constraint support beyond simple `rand` control
- dynamic SV types
- broader software representations for 4-state values
- config-file-driven customization
