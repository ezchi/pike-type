# Task 6: SV emission — Forge Iteration 1

## Files Changed
- `src/piketype/backends/sv/view.py` — modified.
- `src/piketype/backends/sv/templates/module_synth.j2` — modified.

## Key Implementation Decisions
- **`SvVecConstantView`** dataclass: `name`, `sv_type`, `sv_expr` — matches plan exactly. `frozen=True, slots=True` to match other view dataclasses.
- **`_render_sv_vec_literal`** uses Python format specs exactly as in Plan Component 5:
  ```python
  match base:
      case "hex": return f"{width}'h{value:0{(width + 3) // 4}X}"
      case "dec": return f"{width}'d{value}"
      case "bin": return f"{width}'b{value:0{width}b}"
      case _: raise ValueError(...)
  ```
  Smoke-tested all six expected literals: `8'h0F`, `12'h000`, `16'h00AB`, `8'b00001111`, `8'd15`, `4'hF`, `16'h8100`. All correct.
- **`_build_vec_constant_view`** constructs `sv_type = f"logic [{width - 1}:0]"`. For `width=8`: `"logic [7:0]"`. Matches FR-9.
- **`SvSynthModuleView`** extended with `has_vec_constants: bool = False` and `vec_constants: tuple[SvVecConstantView, ...] = ()` defaults. Backwards-compatible with kwargs callers.
- **`_collect_cross_module_synth_imports`** extended: after the existing `_iter_cross_module_typerefs` loop, walk `module.vec_const_imports` and add `(f"{vci.target_module_ref.basename}_pkg", vci.symbol_name)` to the same `pairs: set`. Per-symbol dedup is automatic.
- **`module_synth.j2`**: added a `{% for v in vec_constants %}...{% endfor %}` block immediately after the existing `{% for c in constants %}` block. Updated the surrounding blank-line conditionals to include `has_vec_constants`. Specifically:
  - `{% if has_constants or has_vec_constants or has_types %}` for the blank line BEFORE the localparam blocks.
  - `{% if (has_constants or has_vec_constants) and has_types %}` for the blank line AFTER the localparam blocks (before types).

## Deviations from Plan
- None. Plan Component 5 reproduced exactly.

## Verification
- `_render_sv_vec_literal` smoke check: 7/7 expected outputs.
- `.venv/bin/basedpyright src/piketype/backends/sv/view.py`: 7 errors total (delta-only check below).
- Pre-edit basedpyright on `view.py` (via git stash): same baseline. Delta = 0 new errors introduced by T6.
- Full unittest suite: passes (after T11 regenerated existing manifest goldens — see Risk R-2).

## Tests Added
- None in this task. SV emission is verified at T9/T10 against the new fixture golden tree.
