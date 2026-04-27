# Spec 002: `--namespace` CLI Argument for C++ Namespace Override

## Overview

Add a `--namespace` CLI argument to `typist gen` that lets users specify a custom
top-level C++ namespace prefix. Today, the C++ namespace is derived entirely from
the DSL module's file-system path (with the `typist` directory segment filtered
out). This feature gives users explicit control over the generated C++ namespace
without restructuring their source tree.

**Example:**

```
typist gen --namespace foo::bar constants.py
```

Produces a C++ header containing:

```cpp
namespace foo::bar::constants {
// ...
}  // namespace foo::bar::constants
```

Instead of the current path-derived namespace (e.g., `alpha::constants`).

## User Stories

1. **As a hardware/firmware engineer**, I want to specify the C++ namespace for
   generated headers so that they integrate cleanly into my project's existing
   namespace hierarchy, without being forced to mirror the DSL file-system layout.

2. **As a build engineer**, I want a single CLI flag that controls the generated
   namespace so that CI scripts can target different namespace schemes per build
   configuration without moving files around.

## Functional Requirements

### FR-1: New `--namespace` argument on the `gen` subcommand

The `gen` subcommand accepts an optional `--namespace <value>` argument.

- `<value>` is a `::` -separated C++ namespace path (e.g., `foo`, `foo::bar`,
  `foo::bar::baz`).
- The argument is **optional**. When omitted, behaviour is identical to today
  (path-derived namespace with `typist` segment filtered).

### FR-2: Namespace value validation

The CLI validates `<value>` before any processing begins:

- Each segment between `::` must be a valid C++ identifier:
  `[a-zA-Z_][a-zA-Z0-9_]*`.
- Empty segments are rejected (e.g., `foo::::bar`, `::foo`, `foo::`).
- A single non-qualified identifier is valid (e.g., `foo`).
- **C++17 keywords** are rejected as namespace segments. The implementation
  maintains a set of C++17 reserved words (e.g., `class`, `namespace`, `return`,
  `int`, `void`, etc.) and rejects any segment that matches.
- **Implementation-reserved identifiers** are rejected per the C++ standard
  ([lex.name]):
  - Any segment containing a double underscore (`__`) anywhere in the name.
  - Any segment beginning with an underscore followed by an uppercase letter
    (e.g., `_Foo`).
  - The first segment must not begin with an underscore (reserved at global
    scope).
- **`std` is rejected** as the first segment. Declaring names inside `std` is
  undefined behaviour per the C++ standard.
- Validation errors produce a clear message and non-zero exit code.

### FR-3: C++ namespace composition

When `--namespace` is provided, the generated C++ namespace for a module is:

```
<namespace_value>::<module_basename>
```

Where `<module_basename>` is the DSL file stem (e.g., `constants` from
`constants.py`). The existing logic that filters out `typist` from path-derived
parts is bypassed entirely — the user-provided namespace replaces it.

When `--namespace` is **not** provided, the existing path-derived behaviour is
preserved unchanged.

### FR-4: C++ include guard composition

When `--namespace` is provided, the include guard follows the same composition:

```
<NAMESPACE_VALUE>_<MODULE_BASENAME>_TYPES_HPP
```

With `::` replaced by `_` and the result uppercased (e.g.,
`FOO_BAR_CONSTANTS_TYPES_HPP`).

When omitted, the existing guard derivation from `namespace_parts` is unchanged.

### FR-5: Scope limited to C++ module headers

The `--namespace` argument affects **only** generated C++ module headers (the
per-module `*_types.hpp` files). It does **not** affect:

- SystemVerilog package names or output paths
- Python module paths or output files
- Manifest `namespace_parts`
- File output paths (C++ files stay under `gen/cpp/<path-derived>/`)
- **Runtime C++ headers** (`typist_runtime.hpp`, `typist_runtime.cpp`) — these
  keep their existing `typist_runtime` namespace and include guards unchanged.

Rationale: SV packages and Python modules have their own naming conventions that
are file-path-derived. Runtime headers have a fixed, well-known namespace.
A C++ namespace override should not silently alter any of these.

### FR-6: Plumbing through the pipeline

The namespace override value is carried from CLI → `run_gen` → C++ emitter. It
does **not** modify `ModuleRefIR.namespace_parts` in the IR. Instead, it is
passed as a separate parameter to the C++ emission functions so that the IR
remains a faithful representation of the source layout.

### FR-7: Applicability to all discovered modules

When `--namespace` is specified, it applies to **every** module discovered in the
generation run, not just the CLI-targeted module. All emitted C++ module headers
in the run use the same namespace prefix.

Rationale: A single `typist gen` invocation discovers and generates all modules
in the repo. Applying the namespace only to the targeted module would create an
inconsistent set of headers.

### FR-8: Duplicate basename rejection

When `--namespace` is specified, the tool validates that no two discovered
modules share the same basename (file stem). If duplicates exist, the tool
reports a clear error listing the conflicting modules and exits with a non-zero
code.

Rationale: With `--namespace`, the C++ namespace is `<prefix>::<basename>`. If
two modules share a basename (e.g., `alpha/typist/types.py` and
`beta/typist/types.py`), they would produce identical namespaces
(`foo::bar::types`), violating the one-definition rule. The path-derived default
avoids this because it includes the full directory path.

## Non-Functional Requirements

### NFR-1: Deterministic output

Generated output remains byte-for-byte reproducible given the same inputs and
`--namespace` value, consistent with the project constitution.

### NFR-2: No new runtime dependencies

The feature is implemented with stdlib only (`re` for validation). No new
packages are added.

### NFR-3: Backward compatibility

When `--namespace` is omitted, all generated outputs are byte-for-byte identical
to the current behaviour. No golden file for existing test cases changes.

## Acceptance Criteria

1. `typist gen --namespace foo::bar <path>` produces C++ headers where every
   module's namespace is `foo::bar::<module_basename>`.
2. `typist gen --namespace foo::bar <path>` produces C++ headers where the
   include guard is `FOO_BAR_<MODULE_BASENAME>_TYPES_HPP`.
3. `typist gen <path>` (no `--namespace`) produces output identical to the
   current behaviour.
4. `typist gen --namespace "foo::::bar" <path>` exits with a validation error
   and non-zero exit code.
5. `typist gen --namespace "123bad" <path>` exits with a validation error and
   non-zero exit code.
6. `typist gen --namespace "class" <path>` exits with a validation error
   rejecting the C++ keyword.
7. `typist gen --namespace "foo__bar" <path>` exits with a validation error
   rejecting the reserved identifier (double underscore anywhere).
8. `typist gen --namespace "_foo" <path>` exits with a validation error
   rejecting the leading underscore at global scope.
9. `typist gen --namespace "std::types" <path>` exits with a validation error
   rejecting `std` as the first segment.
10. `typist gen --namespace foo::bar <path>` does **not** alter SV, Python,
    manifest, file output paths, or runtime C++ headers.
11. When `--namespace` is used on a repo with two modules sharing the same
    basename, the tool reports an error listing the conflicting modules.
12. Golden-file integration test: at least one positive case using `--namespace`
    with a fixture containing **at least two modules** with different
    path-derived namespaces. The test verifies that both C++ headers use the
    override prefix while SV, Python, and manifest outputs are unaffected.
13. Negative CLI tests: at least one test per invalid-namespace category (empty
    segment, non-identifier, C++ keyword, double underscore, leading underscore
    at global scope, `std` as first segment, duplicate basename). Each asserts
    non-zero exit code and a specific error substring.
14. Existing golden-file tests pass without modification.

## Out of Scope

- Per-module namespace overrides (one namespace for module A, another for B).
- Namespace configuration via a config file (`.typist.toml` or similar).
- Namespace override for SystemVerilog or Python backends.
- Modifying the IR `namespace_parts` field — it stays path-derived.
- Changing the output file path based on `--namespace` — files stay in the
  path-derived location under `gen/cpp/`.
- Validating `module_basename` against C++ keywords — the basename comes from
  user-controlled file names and is already emitted into namespaces by the
  existing codebase without keyword checks. Adding that would be a separate
  change with broader scope.

## Open Questions

*None — the scope is narrow and the design is straightforward.*
