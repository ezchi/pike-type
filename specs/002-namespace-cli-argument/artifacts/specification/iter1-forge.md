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

### FR-5: Scope limited to C++ backend

The `--namespace` argument affects **only** the C++ code generation backend.
SystemVerilog package names, Python module paths, manifest `namespace_parts`, and
file output paths are **not** changed by this flag.

Rationale: SV packages and Python modules have their own naming conventions that
are file-path-derived. A C++ namespace override should not silently alter those.

### FR-6: Plumbing through the pipeline

The namespace override value is carried from CLI → `run_gen` → C++ emitter. It
does **not** modify `ModuleRefIR.namespace_parts` in the IR. Instead, it is
passed as a separate parameter to the C++ emission functions so that the IR
remains a faithful representation of the source layout.

### FR-7: Applicability to all modules in the gen run

When `--namespace` is specified, it applies to **every** module discovered in the
generation run, not just the CLI-targeted module. All emitted C++ headers in the
run use the same namespace prefix.

Rationale: A single `typist gen` invocation discovers and generates all modules
in the repo. Applying the namespace only to the targeted module would create an
inconsistent set of headers.

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
4. `typist gen --namespace "foo::::bar" <path>` exits with a validation error.
5. `typist gen --namespace "123bad" <path>` exits with a validation error.
6. `typist gen --namespace foo::bar <path>` does **not** alter SV, Python,
   manifest, or file output paths.
7. Golden-file integration tests exist for at least one positive case
   (`--namespace` with constants and types) and one negative case (invalid
   namespace value).
8. Existing golden-file tests pass without modification.

## Out of Scope

- Per-module namespace overrides (one namespace for module A, another for B).
- Namespace configuration via a config file (`.typist.toml` or similar).
- Namespace override for SystemVerilog or Python backends.
- Modifying the IR `namespace_parts` field — it stays path-derived.
- Changing the output file path based on `--namespace` — files stay in the
  path-derived location under `gen/cpp/`.

## Open Questions

*None — the scope is narrow and the design is straightforward.*
