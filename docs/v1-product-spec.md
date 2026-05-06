# V1 Product Spec

`piketype` is a Python-based code generation tool for FPGA-oriented type definitions. Users write normal executable Python modules under repo `piketype/` directories using a builder-style DSL. `piketype` scans the repo, builds a frozen validated IR, and generates SystemVerilog, Python, and C++ artifacts plus supporting runtime/scaffolding files.

## Goals

`piketype` v1 exists to let users define canonical hardware-oriented types once and generate:

- synthesizable SystemVerilog types
- verification-oriented SystemVerilog helper classes without UVM
- Python modeling/helper code
- C++ controller/simulation/helper code

SystemVerilog is the canonical layout. Python and C++ may use more ergonomic software representations as long as generated conversions are correct.

## Non-Goals

V1 does not target:

- UVM
- commercial simulators
- schema evolution / backward compatibility
- config-file-driven customization
- dynamic SV types
- forward references
- circular type graphs
- plugin-defined new IR node kinds outside the repo

## User Model

Users author normal Python modules inside directories literally named `piketype/`.

Example shape:

```text
foo/piketype/packet_defs.py
bar/piketype/common_types.py
```

The DSL is normal Python, not a separate language. It must support normal imports and normal Python execution so editors/LSP can jump to definitions.

Discovery rules:

- Only non-`__init__.py` files inside `piketype/` are treated as DSL modules.
- Every such file must define at least one DSL object, or it is rejected.
- Anonymous temporary DSL objects are rejected.
- Only direct top-level bindings count as discovered definitions.
- Imported DSL objects are dependencies, not definitions of the importing module.
- If the same DSL object is bound to multiple top-level names in one module, that is an error.
- DSL objects may originate only from `piketype/` modules.
- `piketype_utils.py` may exist anywhere in the repo as helper code, but must not define DSL objects.

Repo root discovery:

- Walk upward from the provided file until `.git` or `pyproject.toml` is found.

## CLI

V1 CLI executable name: `piketype`

Commands:

- `piketype gen <path/to/file.py>`
- `piketype build <path/to/file.py>`
- `piketype test <path/to/file.py>`
- `piketype lint <path/to/file.py>`

Input rules:

- file-path form only
- one root file per invocation
- provided file must be under a `piketype/` directory
- provided file must itself define DSL objects

Repo-wide behavior:

- the provided file is used to validate the request and locate the repo root
- after that, all DSL modules in all `piketype/` directories in the repo are scanned
- generation/scaffolding is repo-wide

Failure behavior:

- stop at first error
- partially written files are allowed
- no automatic cleanup of stale files
- no automatic clearing of `gen/`

## DSL

Builder-style only for v1.

Naming style:

- classes/functions use `CapWords` and `snake_case`
- terminology stays close to SystemVerilog concepts

Core DSL objects in planned v1 order:

- `Const()`
- `Bit(width, signed=False)`
- `Logic(width, signed=False)`
- `Struct().add_member(...)`
- `Array(elem_t, size)`
- `Enum().add_value(...)`
- `Union().add_member(...)`

Examples:

```python
FOO = Const(3)

addr_t = Bit(13)

pkt_t = (
    Struct()
    .add_member("addr", addr_t)
    .add_member("flag", Bit(1), rand=False)
)
```

Field/member API:

- `add_member(...)` returns `self`
- positional shorthand allowed
- per-field options live on `add_member(...)`
- per-field software mapping uses `SoftwareView(...)`
- `SoftwareView(...)` is optional and only used to override defaults

Restrictions:

- only backward references through normal Python execution order
- DSL objects are mutable during construction, then frozen before generation
- direct/indirect self-referential type graphs are rejected
- union members must have same bit width
- packed arrays only, compile-time constant sizes only
- zero-width types and zero-length arrays are rejected

## Supported V1 Semantics

### Constants

V1 constants are module-level only.

Rules:

- `FOO = Const(3)` naming comes from Python variable name
- integer-valued only
- top-level only
- immutable
- plain literals first, then expressions over other `Const()` via overloaded operators
- expression graph preserved only when built through `Const()` objects
- no dependency on type properties in v1
- `FOO = Const(0)` is allowed

Supported operators:

- unary `+`, `-`, `~`
- binary `+`, `-`, `*`, `//`, `%`, `&`, `|`, `^`, `<<`, `>>`
- parentheses
- `/` is rejected

Generated forms:

- SystemVerilog: package-scoped `localparam`
- Python: plain module-level constant
- C++: header-only `constexpr`

### Scalars

V1 supports named scalar aliases like:

```python
Addr = Bit(13)
Mask = Logic(8, signed=False)
```

Rules:

- user-defined type names should be `CapWords`; legacy `lower_snake_case_t` names are also accepted
- SystemVerilog typedefs render as `lower_snake_case_t`
- field names must be `snake_case`
- enum values must be `UPPER_CASE`

SystemVerilog scalar emission:

- `Bit` -> `bit`
- `Logic` -> `logic`
- signedness emitted directly in typedef

Examples:

```systemverilog
typedef bit [12:0] addr_t;
typedef logic signed [7:0] data_t;
```

Software behavior:

- Python/C++ wrappers are generated even for named scalar aliases
- wrapper class name replaces trailing `_t` with `_ct`
- example: `addr_t` -> `addr_ct`

Scalar wrapper storage:

- width <= 64:
  - Python `.value`: plain `int`
  - C++ `.value`: fixed-width signed/unsigned integer
- width > 64:
  - Python `.value`: `bytes`
  - C++ `.value`: `std::vector<uint8_t>`

Validation:

- assignments must fit declared width/signedness
- reject out-of-range values
- signed values use normal signed software integers
- packing uses two's-complement truncation to declared width

Python scalar wrapper API:

- public `.value`
- minimal numeric dunders plus common arithmetic
- `__int__`, `__index__`, equality, string representation, common arithmetic

C++ scalar wrapper API:

- public `.value`
- implicit conversion operators where width <= 64
- no implicit conversion when stored as byte vector

SV helper classes are also generated for named scalar aliases and are lightweight.

### Structs

Canonical SV representation:

- `typedef struct packed`

Ordering:

- first field added maps to most-significant bits
- dependency order first, original declaration order as tie-breaker

SV verification helper class:

- separate verification-only package
- helper class name replaces trailing `_t` with `_ct`
- class stores separate field properties as primary state
- no cached packed value
- `pack()`/`unpack()` convert to/from packed typedef
- all fields are `rand` by default
- user may override per field with `rand=False`
- compare/diff is deep field-by-field
- helper capabilities:
  - pretty-print / sprint
  - compare / diff
  - randomization
  - pack / unpack
  - getters/setters
  - copy / clone
  - bitstream conversion
- constraints beyond simple rand control are postponed

Python/C++ struct representation:

- ergonomic class primary state is field values/objects
- packed form recomputed on demand
- nested composite fields default to zero/default objects
- Python may later assign `None` to composite fields, but `to_slv()`/`to_bytes()` then reject
- C++ composite fields do not support `None`-like state

Assignment/coercion:

- named scalar fields may accept plain primitives and auto-wrap
- composite fields require proper generated composite objects
- arrays of named scalars allow primitive coercion
- arrays of composite types require composite objects

### Arrays

V1 arrays:

- packed arrays only
- compile-time constant size only
- first milestone starts with scalar/enum elements only
- later adds arrays in structs and unions

Layout:

- index `0` maps to least-significant packed slice

Ergonomic views:

- Python: ordinary `list[...]`
- C++: `std::vector<T>`

Python uses `default_factory` for mutable defaults.

### Enums

Enum DSL:

- `Enum().add_value(...)`
- returns `self`
- explicit values allowed
- auto-fill allowed for unspecified entries
- default numbering starts at `0` and increments by `1`
- width inferred from largest enumerator value
- non-negative only

SystemVerilog:

- enum typedefs render as `lower_snake_case_t`
- SV helper class for enum type is `<base>_ct`

Python:

- real generated enum type exists separately
- naming: `State` -> Python enum type `StateEnum`; legacy `state_t` -> `state_enum_t`
- ergonomic wrapper class: `State`; legacy `state_t` -> `state_ct`
- wrapper stores actual enum member as primary state
- constructors accept generated enum members only
- `from_slv()` / `from_bytes()` reject unknown numeric values

### Unions

Canonical SV representation:

- `typedef union packed`
- only named member views in DSL
- all members must have same width
- direct exposure of all views
- first member is the canonical member for helper-generation decisions
- this rule must be documented/emitted in generated code/comments/diagnostics

Python/C++ union representation:

- one canonical underlying packed storage as primary state
- all views stay synced
- setting one view overwrites shared storage and changes all others on next access
- direct exposure of all views
- `clone()` copies underlying shared storage only

## Cross-Language Conversion Rules

SystemVerilog is canonical.

Global policies:

- one strict global ordering policy
- little-endian bytes globally
- packed struct ordering matches SV packed struct ordering
- array index `0` is least-significant slice
- enum packed value is underlying inferred integer value

Software conversion APIs:

- Python/C++ classes provide:
  - `to_slv()`
  - `from_slv()`
  - `to_bytes()`
  - `from_bytes()`

Return/input contracts:

- Python `to_slv()`: plain `int`
- Python `from_slv()`: accepts plain `int` only
- Python `to_bytes()`: canonical little-endian bytes
- Python `from_bytes()`: accepts `bytes` and `bytearray`

- C++ `to_slv()`: `std::vector<uint8_t>`
- C++ `from_slv()`: `std::vector<uint8_t>` only
- C++ `to_bytes()`: canonical little-endian bytes
- C++ `from_bytes()`: `std::vector<uint8_t>` only

`Logic` in software:

- `Logic(...)` is 4-state in SV
- Python/C++ use 2-state representation only
- `X`/`Z` coerce to `0`
- warning printed only if global verbose/debug flag is enabled

## Generated Output Layout

Default output root: `gen/`

Separate language roots, preserving source-path structure beneath them.

Example source:

```text
foo/piketype/packet_defs.py
```

Outputs:

```text
gen/sv/foo/piketype/packet_defs_pkg.sv
gen/sv/foo/piketype/packet_defs_test_pkg.sv
gen/py/foo/piketype/packet_defs_types.py
gen/cpp/foo/piketype/packet_defs_types.hpp
gen/cpp/foo/piketype/packet_defs_types.cpp
```

Generated runtime support lives in stable tool-owned paths:

```text
gen/sv/runtime/piketype_runtime_pkg.sv
gen/py/runtime/piketype_runtime.py
gen/cpp/runtime/piketype_runtime.hpp
gen/cpp/runtime/piketype_runtime.cpp
```

Runtime prefix is fixed and tool-owned: `piketype_`

Runtime artifacts are regenerated on every `gen` run.

## Namespacing

One DSL file is one namespace.

SystemVerilog:

- package name uses module basename only
- example: `packet_defs_pkg`
- same for verification package: `packet_defs_test_pkg`
- user is responsible for avoiding module-name collisions
- collision is an error

Python:

- actual package/module layout mirrors filesystem path and keeps literal `piketype`
- generated module suffix: `_types.py`
- `__init__.py` files generated as needed

Example import:

```python
from gen.py.foo.piketype.packet_defs_types import packet_ct
```

C++:

- namespaces derived from path relative to repo root, but skip literal `piketype`
- example: `foo/piketype/packet_defs.py` -> `namespace foo::packet_defs`
- include paths keep literal `piketype`

Example:

```cpp
#include "foo/piketype/packet_defs_types.hpp"
namespace foo::packet_defs { ... }
```

## Generated File Headers

Every generated file includes stable header metadata with no run-specific data.

Minimum header content:

- generated by `piketype`
- source DSL module path(s)
- do not edit by hand warning

Headers are module/source-file level only.

## Internal Architecture

Required architecture split:

- DSL runtime objects during Python execution
- frozen validated IR
- backend-specific generators

Backends must not read mutable DSL objects after IR construction.

IR requirements:

- language-agnostic core IR
- target-specific behavior represented as neutral semantic policies/annotations
- per-field software mapping stored semantically, not as direct Python/C++ types
- manifest derived from frozen validated IR only

Generator implementation:

- template-based
- Jinja2

Extensibility model:

- new type kinds added in-repo by editing core IR and generators
- language backends registered through an in-repo backend registry
- no external type-kind plugin mechanism in v1

## Diagnostics and Validation

Diagnostics should point to both:

- user DSL source locations
- generated file locations

DSL runtime captures source locations automatically via stack inspection at object creation and `add_member(...)`/`add_value(...)` time.

Validation rules include:

- fail fast
- stop at first error
- cross-language compatibility checks
- reject invalid widths/sizes
- reject self-referential type graphs
- reject duplicate generated names within a namespace
- reject files under `piketype/` with no DSL objects
- reject imported DSL objects originating outside `piketype/`
- reject same DSL object bound to multiple top-level names in one module

## Manifest

Generated internal manifest:

```text
gen/piketype_manifest.json
```

Purpose:

- internal tooling and scripts

Format:

- JSON

Contents include:

- discovered DSL modules
- source paths
- namespaces
- types and constants
- dependencies
- source locations
- generated output paths
- semantic inventory from frozen validated IR

## Build / Test / Lint Commands

These commands are repurposed to generate scaffolding, not execute external tools themselves.

### `piketype build`

Generates top-level build-system files for the whole repo.

V1 build system:

- CMake for C++ and Verilator flows only
- one top-level generated build system
- separate targets for pure SV test flow and C++ test flow
- generated shell convenience runner:
  - `gen/build/run_build.sh`

### `piketype test`

Generates:

- per-module generated test sources
- top-level test runner scaffolding

Test roots are parallel output roots.

Generated top-level scripts:

- `gen/test/run_sv_test.sh`
- `gen/test/run_cpp_test.sh`
- `gen/test/run_py_test.sh`

`run_py_test.sh` covers pytest and cocotb through pytest flow.

### `piketype lint`

Generates repo-wide lint config/scaffolding and runner scripts for all files.

Recommended lint/tooling set:

- Python: `ruff`
- tool codebase static typing: `basedpyright`
- C++: `clang-tidy`, `clang-format`
- SystemVerilog: `verilator --lint-only`, `slang`

Generated runners:

- `gen/lint/run_lint.sh`
- `gen/lint/run_lint.py`

No auto-fix in v1.

## Generated Tests

Generated tests are not emitted by `gen`. They are emitted by `piketype test`.

Frameworks:

- Python: `pytest`
- cocotb is a hard dependency
- C++: GoogleTest
- SystemVerilog tests use a custom piketype-designed class-based pattern, not UVM

Top-level testbench structure:

- one top-level SV testbench per source module
- same generated SV top should support both Verilator-native SV flow and cocotb flow

Default generated test coverage for each supported type includes all analogous checks where applicable:

- pack/unpack correctness
- `to_slv()` / `from_slv()` roundtrip
- `to_bytes()` / `from_bytes()` roundtrip
- nested field access/mutation
- getter/setter correctness
- equality/inequality
- string representation smoke
- clone/copy behavior
- compare/diff behavior
- randomize smoke behavior
- union shared-storage semantics
- array packing order

Cross-language test strategy:

- shared canonical test vectors across SV, Python, and C++
- automatically generated by `piketype`
- one representative fixed sample case per type shape
- no generated tests for invalid constructs, because invalid constructs must be rejected before codegen

## Tool Implementation Requirements

The `piketype` tool itself is:

- pure Python 3.12+
- installable Python package with CLI entry point
- strict static checking from day one using `basedpyright` only

Tool test strategy:

- Python `pytest` only
- CLI-driven integration tests over checked-in fixture repos
- golden-file comparison, byte-for-byte
- fixture repos represent small whole-repo scenarios
- golden outputs include runtime support files
- separate golden expectations for `gen`, `build`, `test`, and `lint`

## Planned V1 Delivery Order

High-level implementation order:

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

- for each new type feature: SystemVerilog first
- then Python/C++
- then generated test/build/lint scaffolding for that feature
- then move to the next type feature
