# Task 2: Add VecConst class — Forge Iteration 1

## Files Changed
- `src/piketype/dsl/const.py` — modified. Added `VecConst` class after the existing `Const` class and before `_binary_expr`.
- `src/piketype/dsl/__init__.py` — modified. Added `VecConst` to imports and `__all__`.

## Key Implementation Decisions
- `@dataclass(slots=True)` (mutable, matching existing `Const` per Constitution §Coding Standards Python "Mutable dataclasses with slots=True for DSL runtime objects").
- Inherits from `DslNode` (carries `source`).
- `SUPPORTED_BASES: ClassVar[set[str]] = {"hex", "dec", "bin"}` is a `ClassVar` to avoid being a per-instance field. Validated in `__init__` against any other value (raises `ValidationError` with the offending value and the supported set).
- `__init__` is keyword-only (`*` separator) per FR-2.
- `width_expr` and `value_expr` are stored as `ConstExpr` after coercion via the existing `_coerce_operand`. The constructor does NOT call `_eval_expr` — freeze (T3) evaluates with the cross-module map.
- No `__add__`/`__or__`/etc. — VecConst is NOT a `ConstOperand`. (Plan R-3 / Spec note.)
- No `width: int` field — only `width_expr: ConstExpr`. The resolved `width` int comes from `VecConstIR` after freeze, not from this DSL class. Same for `value`.

## Deviations from Plan
- Plan Component 1 sketch had `width: int` and `value: int` fields on `VecConst` directly. I removed them: at DSL-construction time, `width` and `value` may be `Const`/`ConstExpr` (not yet evaluable without the cross-module definition_map), so storing only the expressions until freeze is cleaner. The IR's `VecConstIR` carries the resolved ints. (No semantic deviation; the spec talks about resolved values, which is exactly what IR holds.)

## Verification
- `from piketype.dsl import VecConst` succeeds.
- `VecConst(width=8, value=0xab, base="hex")` constructs successfully; `.base == "hex"`, `.width_expr.kind == "int_literal"`, `.value_expr.kind == "int_literal"`.
- `VecConst(width=8, value=0, base="oct")` raises `ValidationError` with message `"VecConst() base= must be one of ['bin', 'dec', 'hex'], got 'oct'"` (AC-8 sentinel).
- `.venv/bin/basedpyright src/piketype/dsl/const.py src/piketype/dsl/__init__.py`: 2 errors reported, BOTH at pre-existing lines (24 and 131) NOT in code I modified. Delta on the new VecConst class: 0 errors.

## Tests Added
- None in this task. Comprehensive negative tests live in T4.
