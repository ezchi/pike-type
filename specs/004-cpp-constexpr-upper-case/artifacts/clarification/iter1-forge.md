# Clarification — Iteration 1

## Ambiguity Analysis

The specification is well-scoped and mechanical. After reviewing the emitter source code, I found no significant ambiguities. Below is a systematic walk-through:

### Q1: Are all `constexpr` identifiers in generated C++ catalogued?

**RESOLVED.** A grep of `src/typist/backends/cpp/emitter.py` and `src/typist/backends/runtime/emitter.py` confirms the following exhaustive list of generated `constexpr` names:

**Scalar alias class statics** (`_render_cpp_scalar_alias`):
- `kWidth`, `kSigned`, `kByteCount`, `kMask`, `kMaxValue`, `kMinValue`

**Struct class statics** (`_render_cpp_struct`):
- `kWidth`, `kByteCount`

**Helper function locals** (`_render_narrow_inline_helpers`):
- `kMaxValue`, `kMinValue` (in `validate_<field>`)
- `mask` (in `encode_<field>` and `decode_<field>`)

**Runtime** (`render_runtime_hpp`):
- `kVerboseDefault`

No other `constexpr` identifiers exist in the emitter code. This matches FR-1 through FR-4 exactly.

### Q2: Could the rename collide with user-defined names?

**NO RISK.** User-defined constants are emitted at namespace scope (not inside classes), and their names come directly from DSL definitions which are already `UPPER_SNAKE_CASE`. The renamed class-static and function-local constants live in different scopes and cannot collide.

### Q3: Does `mask` appear as both a declaration and a reference?

**YES — handled.** In signed encode/decode helpers, `mask` is declared as a local `constexpr` and then referenced in subsequent expressions (`bits & mask`, `~mask`, etc.). FR-3 requires updating both declarations and references, which is correct.

### Q4: Are there any downstream consumers of these C++ symbols that would break?

**OUT OF SCOPE.** The generated C++ is output artifacts — there are no in-tree consumers that depend on specific constant names. External consumers would need to update, but that's expected for a generated-code style change.

## Clarification Questions for Spec

None. The spec is complete and unambiguous for implementation.

## Updated Spec Sections

No changes needed.
