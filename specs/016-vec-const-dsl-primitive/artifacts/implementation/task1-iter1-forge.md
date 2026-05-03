# Task 1: Add VecConstIR and VecConstImportIR to ir/nodes.py — Forge Iteration 1

## Files Changed
- `src/piketype/ir/nodes.py` — modified. Added two new frozen dataclasses (`VecConstIR`, `VecConstImportIR`) and two new fields on `ModuleIR` (`vec_constants`, `vec_const_imports`), each defaulting to `()`.

## Key Implementation Decisions
- Both new dataclasses use `@dataclass(frozen=True, slots=True)` exactly matching the existing IR-node convention (see `ConstIR` at line 175 for the template).
- `VecConstIR` field order: `name`, `source`, `width`, `value`, `base` — chosen so `name` and `source` come first (matches `ConstIR`); `width`, `value`, `base` are the resolution outputs that the SV view consumes. No `expr` field — VecConst's value is fully resolved at freeze time per FR-6.
- `VecConstImportIR` carries only `target_module_ref` and `symbol_name`. No `source` field because the import-sighting source is the importing module's `__dict__` walk, not a source line; for diagnostic purposes the SV view doesn't need it.
- `ModuleIR.vec_constants` and `vec_const_imports` are added at the END of the field list with `= ()` defaults. This keeps existing kwargs-positional callers working (verified: all in-tree call sites in `freeze.py` use kwargs).

## Deviations from Plan
- None. Implementation follows Plan Component 2 exactly.

## Verification
- `python -c "from piketype.ir.nodes import VecConstIR, VecConstImportIR, ModuleIR; print(VecConstIR.__match_args__)"` → `('name', 'source', 'width', 'value', 'base')`. ✓
- `python -c "... print(ModuleIR.__match_args__)"` → `('ref', 'source', 'constants', 'types', 'dependencies', 'vec_constants', 'vec_const_imports')`. ✓
- `.venv/bin/basedpyright src/piketype/ir/nodes.py` → `0 errors, 0 warnings, 0 notes`. ✓

## Tests Added
- None in this task. Tests live in T4 and T10.
