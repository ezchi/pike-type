# Task 3: Implement freeze logic for VecConst — Forge Iteration 1

## Files Changed
- `src/piketype/dsl/freeze.py` — modified.
- `src/piketype/commands/gen.py` — modified (caller updated to pass `vec_const_definition_map`).

## Key Implementation Decisions
- **Three new helpers**: `build_vec_const_definition_map` (mirrors `build_const_definition_map`), `_freeze_vec_const` (top-level entry), `_freeze_vec_const_storage` (validation + IR construction), and `_eval_expr_int` (recursive expression evaluator returning ints — needed because `_freeze_expr` produces IR nodes, not ints).
- **Why a separate `_eval_expr_int`?** `_freeze_expr` produces `ConstRefExprIR` for cross-module Const references. For VecConst, we need the *value* of the resolved expression at freeze time (FR-6: "evaluate at IR-build time and emit the resolved scalar integer"), not a symbolic IR. The new `_eval_expr_int` recursively evaluates ConstExprs to ints by walking through `target.value` for `const_ref` (which is already a resolved int, set by `Const.__init__` via `_eval_expr` in `dsl/const.py`).
- **Cross-module Const-in-VecConst-value works for free**: when `value=A * 3` and `A` is a `Const` from another module, `vec_const.value_expr` is a `ConstExpr(kind="binary_op", lhs=ConstExpr(kind="const_ref", target=A), ...)`. `_eval_expr_int` resolves `target.value` to `A.value` (already evaluated at A's `Const.__init__`) and computes `A.value * 3 = 15`. No new dependency edge code needed for this path; the existing `_collect_module_dependencies` walks `module.constants[].expr` for `ConstRefExprIR` nodes — but VecConst's value isn't stored as IR (it's a resolved int). For cross-module Const refs INSIDE a VecConst's expression to register as a `const_ref` dep edge, we'd need to traverse `vec_const.value_expr` separately. **Deferred** as a follow-up — for v1, cross-module dependency tracking covers (a) cross-module `VecConst` import sightings and (b) cross-module `Const` refs in `Const`/type expressions (existing behavior). Cross-module `Const` refs *inside a VecConst's value expression* don't currently register as deps. Acceptable for v1: if module B's VecConst uses module A's Const, B's Python `from a import A` import already runs (because A is referenced at module load time), so the runtime works; the only missing piece is the SV-side dep edge for the import line — which is a refinement, not a correctness bug for the user's stated examples.
- **`freeze_module` signature change**: added `vec_const_definition_map: dict[...] | None = None` keyword-only parameter at the END so existing positional callers (none in-tree, but defensive) continue to work. Default `None` is treated as empty `{}`.
- **First-sighting vs cross-module**: in `freeze_module`'s scan loop, when the value is a `VecConst`:
  - If the map says this VecConst's defining module is THIS module (or no map entry): emit `local_vec_constants` via `_freeze_vec_const`.
  - Else: emit `local_vec_const_imports` via `VecConstImportIR(target_module_ref, symbol_name)`.
- **`_collect_module_dependencies`** extended: walks `module_ir.vec_const_imports`, emits `("<target>.python_module_name", "vec_const_import")` keys deduplicated against existing `(target, kind)` pairs.
- **Error messages** in `_freeze_vec_const_storage` carry the FR-7 three-substring contract: offending value, declared width, and the literal `2**N - 1` formula (with N substituted).

## Deviations from Plan
- Plan said one helper `_freeze_vec_const_storage(*, width, value, base, source) -> VecConstIR`. I split the work into two helpers: `_freeze_vec_const` (handles expression evaluation) and `_freeze_vec_const_storage` (handles validation + IR construction). Separation is cleaner: storage validation can be unit-tested independently. No semantic deviation.
- Added `_eval_expr_int` rather than reusing `dsl/const.py`'s `_eval_expr`. The latter takes a `ConstExpr` and returns an int, which IS what we need — but it's currently called from `Const.__init__` with no cross-module map (because `Const` is constructed before `vec_const_definition_map` exists). For VecConst, the const-target's value is already resolved (it's a `Const` whose `value` is set at `Const.__init__`), so the cross-module map isn't actually needed at evaluation time — it's just plumbing for future. Choosing to add `_eval_expr_int` in `freeze.py` keeps the freeze-time evaluator co-located with the rest of the freeze logic.

## Verification
- `python -c "..."` smoke check: `A=Const(5); B=VecConst(width=8, value=A*3, base='dec')` then `_freeze_vec_const(name='B', vec_const=B, const_definition_map={})` returns `VecConstIR(name='B', width=8, value=15, base='dec', ...)`. ✓
- basedpyright on `freeze.py` and `commands/gen.py`: 29 errors before my edits, 29 errors after — confirmed by `git stash`/`pop` round-trip. **Zero NEW errors introduced by T3.** ✓ (per project memory `project_basedpyright_baseline_drift.md`, delta-only measurement.)

## Tests Added
- None in this task. Comprehensive negative tests for `_freeze_vec_const_storage` validation live in T4.
