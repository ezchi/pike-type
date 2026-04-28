# Spec Diff — Clarification Iteration 2

## CL-2: Dependency Ordering (FR-5)

**Before:**
> **Dependency ordering (all backends):** The Flags type definition must appear before the Struct definition in all generated output (SV packages, Python modules, C++ headers). The current type output order is sorted by `(source.line, name)`. For conventional DSL usage — where the Flags object is assigned to a module-level variable before being passed to `add_member()` — source-line order naturally places the Flags type first. This is not a topological sort; it relies on the convention that DSL types are defined at module scope in sequential order. Edge cases (same-line definitions, helper-function-constructed objects) are not addressed by this spec and are pre-existing limitations.

**After:**
> **Dependency ordering (all backends):** For correct generated output, the Flags type definition should appear before the Struct that references it. The current type output order is sorted by `(source.line, name)`, which produces correct ordering for conventional DSL usage (Flags assigned to a module-level variable before being passed to `add_member()`). This spec does not add topological sorting — it relies on the same `(source.line, name)` mechanism that already works for nested structs. Edge cases (same-line definitions, helper-function-constructed objects) are pre-existing limitations not addressed here.

**Rationale:** Removed the "must" hard requirement since there's no topological sort to enforce it. Changed to "should" with explanation of how the existing mechanism achieves it.

## CL-3: Cross-Module AC (AC-27)

**Added:**
> - **AC-27:** Validation rejects a Struct member referencing a Flags type from a different module with the existing cross-module error message.

**Rationale:** FR-4/NFR-4 mention cross-module restriction but no AC tested it.
