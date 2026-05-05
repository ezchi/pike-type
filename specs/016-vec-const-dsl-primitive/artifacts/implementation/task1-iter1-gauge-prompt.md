# Gauge Code Review — Task 1, Iteration 1

You are the **Gauge** in a strict dual-agent Forge-Gauge implementation loop. The Forge has implemented Task 1 of spec `016-vec-const-dsl-primitive`.

## Task Description

**Title:** Add VecConstIR and VecConstImportIR to ir/nodes.py; extend ModuleIR

**From `tasks.md` T1:** Add two new frozen dataclasses (`VecConstIR`, `VecConstImportIR`) and two new fields on `ModuleIR` (`vec_constants`, `vec_const_imports`), each defaulting to `()`.

## Constitution coding standards

- `from __future__ import annotations` (line 3 already present).
- `@dataclass(frozen=True, slots=True)` for all IR nodes.
- `UPPER_SNAKE_CASE` for module-level constants (no new constants here).
- basedpyright strict clean.

## Diff (HEAD~1..HEAD on `src/piketype/ir/nodes.py`)

```diff
+@dataclass(frozen=True, slots=True)
+class VecConstIR:
+    """Frozen logic-vector constant definition (locally defined)."""
+
+    name: str
+    source: SourceSpanIR
+    width: int
+    value: int
+    base: str
+
+
+@dataclass(frozen=True, slots=True)
+class VecConstImportIR:
+    """Cross-module VecConst sighting (this module imports it from another)."""
+
+    target_module_ref: ModuleRefIR
+    symbol_name: str
+
+
 @dataclass(frozen=True, slots=True)
 class ModuleIR:
     """Frozen module node."""

     ref: ModuleRefIR
     source: SourceSpanIR
     constants: tuple[ConstIR, ...]
     types: tuple[TypeDefIR, ...]
     dependencies: tuple[ModuleDependencyIR, ...]
+    vec_constants: tuple[VecConstIR, ...] = ()
+    vec_const_imports: tuple[VecConstImportIR, ...] = ()
```

## Forge artifact

`/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/artifacts/implementation/task1-iter1-forge.md`

## Review criteria

1. **Correctness** — does `VecConstIR` carry exactly what the SV view needs (resolved width, value, base, name, source)? Does `VecConstImportIR` carry exactly what cross-module per-symbol import emission needs (target module ref, symbol name)? Plan Component 2 spec match?
2. **Constitution compliance** — `frozen=True, slots=True` on both? `from __future__ import annotations` already on file (line 3)?
3. **Backwards compat** — both new `ModuleIR` fields have `= ()` defaults at the END of the field list. All in-tree callers use kwargs. Will they keep working?
4. **basedpyright strict** — verified at 0/0/0.
5. **No scope creep** — no other classes touched. No new imports added.

## Important

- This is purely IR scaffolding. No logic. Be brief.
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
