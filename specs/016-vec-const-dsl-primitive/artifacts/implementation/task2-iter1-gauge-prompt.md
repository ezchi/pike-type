# Gauge Code Review — Task 2, Iteration 1

You are the **Gauge**. The Forge has implemented Task 2.

## Task Description

**Title:** Add `VecConst` class to `dsl/const.py`; export from `dsl/__init__.py`

**From `tasks.md` T2:** Add `VecConst` mutable dataclass(slots=True). Validate base ∈ {hex,dec,bin} at __init__. Capture source via `capture_source_info()`. Store `width_expr` and `value_expr` (from `_coerce_operand`); do NOT `_eval_expr` at construction. Do NOT define `__add__`/etc — VecConst is NOT a `ConstOperand`. Export from `piketype.dsl`.

**Must satisfy:** FR-1, FR-2, FR-3.

## Constitution Standards

- `from __future__ import annotations` (line 3 already present in `const.py`).
- `@dataclass(slots=True)` for DSL runtime objects (mutable).
- `UPPER_SNAKE_CASE` for `SUPPORTED_BASES` (it's a ClassVar constant) ✓.
- basedpyright strict — measure delta per project memory.

## Code under review — `src/piketype/dsl/const.py` lines 220-248

```python
type ConstOperand = Const | ConstExpr | int


@dataclass(slots=True)
class VecConst(DslNode):
    """Fixed-width logic vector constant with explicit base."""

    SUPPORTED_BASES: ClassVar[set[str]] = {"hex", "dec", "bin"}

    width_expr: ConstExpr
    value_expr: ConstExpr
    base: str

    def __init__(
        self,
        *,
        width: int | Const | ConstExpr,
        value: int | Const | ConstExpr,
        base: str,
    ) -> None:
        if base not in VecConst.SUPPORTED_BASES:
            raise ValidationError(
                f"VecConst() base= must be one of {sorted(VecConst.SUPPORTED_BASES)}, got {base!r}"
            )
        source = capture_source_info()
        DslNode.__init__(self, source=source)
        self.width_expr = _coerce_operand(width, source=source)
        self.value_expr = _coerce_operand(value, source=source)
        self.base = base
```

## Code under review — `src/piketype/dsl/__init__.py`

```python
"""DSL surface for piketype."""

from piketype.dsl.const import Const, VecConst
from piketype.dsl.enum import Enum
from piketype.dsl.flags import Flags
from piketype.dsl.scalar import Bit, Logic
from piketype.dsl.struct import Struct

__all__ = ["Bit", "Const", "Enum", "Flags", "Logic", "Struct", "VecConst"]
```

## Forge artifact

`/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/artifacts/implementation/task2-iter1-forge.md`

The Forge notes one deviation from Plan Component 1: the class stores ONLY `width_expr` / `value_expr`, not separate resolved `width: int` / `value: int` fields. The reasoning: at DSL-construction time, `width` and `value` may be `Const`/`ConstExpr` (not yet evaluable without the cross-module definition_map); storing only expressions until freeze keeps things clean. The IR's `VecConstIR` carries the resolved ints. No semantic deviation.

## Review criteria

1. **Correctness** — does FR-1 (import), FR-2 (signature), FR-3 (base validation) match? Is `_coerce_operand` the right call (it accepts `int | Const | ConstExpr`)?
2. **Constitution compliance** — `slots=True`, `ClassVar` annotation on `SUPPORTED_BASES`, `from __future__` (already on file).
3. **Deviation justification** — is "store expressions, not resolved ints" defensible per the plan's stated intent ("freeze evaluates width and value")?
4. **Scope discipline** — VecConst is NOT a `ConstOperand`. The class does not define `__add__` etc. Verified.
5. **Error message quality** — does the AC-8 error message clearly name the offending base? Verified by smoke test: `"VecConst() base= must be one of ['bin', 'dec', 'hex'], got 'oct'"`.

## Important

- This is a small DSL surface change. Be brief.
- Do NOT raise "make it a ConstOperand" — out of scope per spec OOS and the user's explicit minimal scope.
- Constitution is highest authority.

## Output

### Issues
**BLOCKING / WARNING / NOTE**, terse.

### Verdict

End with **EXACTLY** one of:

```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```
