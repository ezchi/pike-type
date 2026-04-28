# Pike-type IR Schema

## Purpose

This document defines the frozen validated IR for `piketype` v1. The IR is the semantic boundary between:

- mutable DSL runtime execution
- validation
- backend generation
- manifest generation

Backends and validators consume IR only. They must not read DSL runtime objects directly.

## Core Properties

The IR must be:

- immutable
- deterministic in ordering
- language-agnostic
- source-location-aware
- rich enough for manifest generation

## Global Model

The root object is a repository-level graph containing all discovered DSL modules.

Proposed root:

```text
RepoIR
```

Fields:

- `repo_root: Path`
- `modules: tuple[ModuleIR, ...]`
- `tool_version: str | None`

Module ordering:

- canonical path order across the repo

## Common Supporting Types

### `SourceSpanIR`

Represents where a DSL object was declared.

Fields:

- `path: str`
- `line: int`
- `column: int | None`

### `ModuleRefIR`

Stable module identity.

Fields:

- `repo_relative_path: str`
- `python_module_name: str`
- `namespace_parts: tuple[str, ...]`
- `basename: str`

### `ExprIR`

Expression node used for constants and, later, width/size expressions.

V1 expression kinds:

- `int_literal`
- `const_ref`
- `unary_op`
- `binary_op`

Common fields:

- `kind: str`
- `source: SourceSpanIR`

Node-specific content:

- `IntLiteralExprIR(value: int)`
- `ConstRefExprIR(module: ModuleRefIR, name: str)`
- `UnaryExprIR(op: str, operand: ExprIR)`
- `BinaryExprIR(op: str, lhs: ExprIR, rhs: ExprIR)`

For v1 milestone 1, only `int_literal` is required.

## Repository Module Node

### `ModuleIR`

Represents one DSL source file.

Fields:

- `ref: ModuleRefIR`
- `source: SourceSpanIR`
- `constants: tuple[ConstIR, ...]`
- `types: tuple[TypeIR, ...]`
- `dependencies: tuple[ModuleDependencyIR, ...]`

Ordering:

- dependency order first
- declaration order second

The module is the unit of generated output for SV, Python, and C++ backends.

## Dependency Node

### `ModuleDependencyIR`

Represents that one module depends on another module.

Fields:

- `target: ModuleRefIR`
- `kind: Literal["import"]`

V1 uses import-based dependencies only.

## Constants

### `ConstIR`

Represents one module-level constant.

Fields:

- `name: str`
- `source: SourceSpanIR`
- `expr: ExprIR`
- `resolved_value: int`

V1 rules represented here:

- module-level only
- integer-valued only
- immutable

The IR stores both:

- the expression graph
- the resolved integer value

That allows both human-readable diagnostics and easy backend emission.

## Type Hierarchy

The core type union is:

```text
TypeIR = ScalarAliasIR | StructIR | ArrayAliasIR | EnumIR | UnionIR
```

Not every member is used in milestone 1, but the shape should be fixed early.

Every type node shares:

- `name: str`
- `source: SourceSpanIR`
- `kind: str`

## Scalars

### `ScalarBaseIR`

Represents a primitive bit-vector type before aliasing.

Fields:

- `state_kind: Literal["bit", "logic"]`
- `signed: bool`
- `width_expr: ExprIR`
- `resolved_width: int`

This node is usually embedded inside aliases or members rather than emitted as a top-level named definition by itself.

### `ScalarAliasIR`

Represents a named scalar alias such as `addr_t = Bit(13)`.

Fields:

- `name: str`
- `source: SourceSpanIR`
- `base: ScalarBaseIR`

## Software View Policy

The IR must store software-mapping policy semantically rather than as direct target-language types.

### `SoftwareViewIR`

Fields:

- `view_kind: Literal["default", "scalar", "enum", "object", "sequence"]`
- `storage_hint: Literal["auto", "int", "bytes"]`
- `width_hint: int | None`

This is intentionally neutral. It expresses intent, not exact Python/C++ type names.

## Members

### `MemberIR`

Represents a struct or union member.

Fields:

- `name: str`
- `source: SourceSpanIR`
- `type_ref: TypeRefIR`
- `rand: bool`
- `software_view: SoftwareViewIR | None`

## Type References

The IR should not embed arbitrary recursive type objects directly. Use explicit references.

### `TypeRefIR`

Kinds:

- `local_type`
- `external_type`
- `inline_scalar`
- `array`

Suggested variants:

- `NamedTypeRefIR(module: ModuleRefIR, name: str)`
- `InlineScalarRefIR(base: ScalarBaseIR)`
- `ArrayTypeRefIR(element: TypeRefIR, size_expr: ExprIR, resolved_size: int)`

This allows:

- members referencing local named types
- members referencing imported named types
- members using raw inline `Bit(...)` / `Logic(...)`
- arrays over either form

## Structs

### `StructIR`

Fields:

- `name: str`
- `source: SourceSpanIR`
- `members: tuple[MemberIR, ...]`

Ordering is preserved exactly as validated declaration order.

## Arrays

There are two relevant array uses:

- inline array member types
- potentially named array aliases later

V1 can represent arrays through `ArrayTypeRefIR` without requiring a separate top-level array-alias node immediately.

If a top-level named array alias is added, it can be:

### `ArrayAliasIR`

Fields:

- `name: str`
- `source: SourceSpanIR`
- `element: TypeRefIR`
- `size_expr: ExprIR`
- `resolved_size: int`

## Enums

### `EnumValueIR`

Fields:

- `name: str`
- `source: SourceSpanIR`
- `expr: ExprIR`
- `resolved_value: int`

### `EnumIR`

Fields:

- `name: str`
- `source: SourceSpanIR`
- `width_expr: ExprIR`
- `resolved_width: int`
- `values: tuple[EnumValueIR, ...]`

The width is stored explicitly in IR even though it is inferred, because backends should not recompute it independently.

## Unions

### `UnionIR`

Fields:

- `name: str`
- `source: SourceSpanIR`
- `members: tuple[MemberIR, ...]`
- `canonical_member_index: int`

For v1, `canonical_member_index` is always `0`, but it is worth representing explicitly in IR because:

- it is a true semantic rule
- diagnostics and comments need it
- future versions may allow explicit override

## Validation-Derived Properties

The IR itself should remain semantic and source-oriented. Validation-derived convenience values may be attached either:

- directly on IR nodes when they are stable semantic facts
- or in a backend view-model layer when they are backend-specific

Examples of stable semantic facts:

- resolved constant value
- resolved scalar width
- resolved array size
- enum inferred width

Examples that should stay out of core IR:

- final SV package name
- final generated Python import path
- final C++ include path

Those belong to path and backend layers.

## Manifest Projection

The manifest should be generated from IR plus path-resolution helpers.

The IR contains enough information to project:

- module inventory
- constant and type names
- dependencies
- source locations
- semantic ordering

The manifest layer then adds generated file paths derived from command/path logic.

## Milestone 1 Minimal IR

The first working milestone only requires:

- `RepoIR`
- `ModuleIR`
- `ModuleDependencyIR`
- `SourceSpanIR`
- `ModuleRefIR`
- `ExprIR` with `int_literal` only
- `ConstIR`

Everything else can be scaffolded as placeholders but should not be implemented prematurely.

## Recommended Implementation Style

Use frozen Python dataclasses for IR nodes.

Reasons:

- strong fit for immutability
- easy to inspect in tests
- straightforward `basedpyright` typing
- easy to serialize into manifest projections

Suggested rule:

- IR dataclasses are frozen
- tuples instead of lists
- no methods that mutate or perform backend logic
