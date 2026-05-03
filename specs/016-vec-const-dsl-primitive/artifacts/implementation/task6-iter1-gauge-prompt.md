# Gauge Code Review — Task 6, Iteration 1

You are the **Gauge**.

## Task
Per Plan Component 5: extend `src/piketype/backends/sv/view.py` and `templates/module_synth.j2` for VecConst SV emission (FR-9..13).

## Files / changes

1. `view.py`:
   - `import VecConstIR` from `piketype.ir.nodes`.
   - New dataclass `SvVecConstantView(name, sv_type, sv_expr)` (frozen, slots).
   - New helper `_render_sv_vec_literal(*, width, value, base) -> str` using Python format specs:
     ```python
     match base:
         case "hex": return f"{width}'h{value:0{(width + 3) // 4}X}"
         case "dec": return f"{width}'d{value}"
         case "bin": return f"{width}'b{value:0{width}b}"
         case _: raise ValueError(...)
     ```
   - New helper `_build_vec_constant_view(*, vec_const_ir) -> SvVecConstantView` constructing `sv_type=f"logic [{width-1}:0]"`.
   - `SvSynthModuleView` extended with `has_vec_constants: bool = False` and `vec_constants: tuple[SvVecConstantView, ...] = ()` (defaults at end).
   - In `build_synth_module_view_sv` assembly site (~line 760): add `has_vec_constants=bool(module.vec_constants)` and `vec_constants=tuple(_build_vec_constant_view(...))`.
   - In `_collect_cross_module_synth_imports`: append `for vci in module.vec_const_imports: pairs.add((f"{vci.target_module_ref.basename}_pkg", vci.symbol_name))`.

2. `module_synth.j2`:
   - Added `{% for v in vec_constants %}localparam {{ v.sv_type }} {{ v.name }} = {{ v.sv_expr }};{% endfor %}` block after the existing `{% for c in constants %}` block.
   - Updated blank-line conditionals: `{% if has_constants or has_vec_constants or has_types %}` and `{% if (has_constants or has_vec_constants) and has_types %}`.

## Forge artifact
`/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/artifacts/implementation/task6-iter1-forge.md`

## Verification empirically run
- `_render_sv_vec_literal` smoke check: `8'h0F`, `12'h000`, `16'h00AB`, `8'b00001111`, `8'd15`, `4'hF`, `16'h8100` — all correct.
- basedpyright on `view.py`: 7 baseline errors (pre-existing, verified via `git stash`/`pop` round-trip). Delta = 0.
- Full unittest suite: 307 passing.

## Review criteria
1. Render rules match FR-9 (shape), FR-10 (hex uppercase), FR-11 (zero-pad rules)?
2. Cross-module import per-symbol pair uses `vci.target_module_ref.basename` correctly to form `<basename>_pkg`?
3. Template emission ordering: constants block, then vec_constants block, then types block — matches user's expected output?
4. Backwards compat: `SvSynthModuleView`'s new fields have `= ()` / `= False` defaults so existing callers stay green?

## Output

### Issues
**BLOCKING / WARNING / NOTE**, terse.

### Verdict
End with **EXACTLY** `VERDICT: APPROVE` or `VERDICT: REVISE`.
