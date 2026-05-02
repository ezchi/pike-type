# Task 1: Edit synth_pack_fn enum branch in _macros.j2 — Forge Iteration 1

(Batched with Task 2 in a single forge iteration / single commit, per
spec NFR-2 / `feedback_byte_parity_per_commit.md`. The template edit
without the golden refresh would fail per-commit byte parity.)

## Files Changed
- `src/piketype/backends/sv/templates/_macros.j2` — modified (1 line:
  `-1 / +1` at line 98 inside the `synth_pack_fn` macro, enum branch).

## Key Implementation Decisions
- **Used the size cast `LP_<UPPER>_WIDTH'(a)` (not `view.name'(a)` and
  not bare `return a;`).** Three forms were considered:
  1. `return LP_<UPPER>_WIDTH'(a);` — chosen. Width-correct,
     constant-integral prefix (the localparam declared above the
     typedef), uniform across 1-bit and multi-bit enums, lint-clean
     under Verilator size-cast rules.
  2. `return view.name'(a);` (i.e. `return color_t'(a);`). Rejected:
     this is a typed cast back to the enum type, which would be
     redundant since `a` already has the enum type. It also doesn't
     match the function's declared return type (`logic [W-1:0]`,
     not the enum typedef).
  3. `return a;`. Legal SystemVerilog (enum-to-base assignment is
     permitted), but the explicit width cast is preferred for diff
     readability and parallels the `view.name'(a)` form on the
     unpack side. Spec FR-1.1 mandates the cast form.
- **No branching on `view.is_one_bit`.** Per spec FR-1.4, a single
  uniform form is used for both 1-bit and multi-bit enums. The
  `LP_<UPPER>_WIDTH` localparam evaluates to 1 for one-bit enums
  (e.g. `flag_t`), and `1'(a)` is well-formed SV.
- **Reused `view.upper_base`, no new view-builder field.** Per spec
  FR-1.3, the `view.upper_base` value already used on the
  surrounding macro lines (function return type and on the localparam
  above) is sufficient. No edit to `src/piketype/backends/sv/view.py`.

## Deviations from Plan
- None — implementation follows plan section C-1 and Phase 1 exactly.

## Tests Added
- None new. The fix is verified by the existing golden-file
  integration tests under `tests/test_gen_enum.py`,
  `tests/test_struct_enum_member.py`, `tests/test_validate_keywords.py`,
  and `tests/test_gen_cross_module.py`. The regenerated goldens (Task
  2) are byte-compared against fresh `piketype gen` output by these
  tests; passing tests confirm the fix renders identically.
