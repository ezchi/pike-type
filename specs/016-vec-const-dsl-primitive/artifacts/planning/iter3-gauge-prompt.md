# Gauge Review Prompt — Planning, Iteration 3

You are the **Gauge**. The Forge revised the plan in response to your iter2 BLOCKING.

## Inputs

- **Updated plan:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/plan.md`
- **Your iter2 review:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/artifacts/planning/iter2-gauge.md`
- **Spec:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/spec.md`
- **Constitution:** `/Users/ezchi/Projects/pike-type/.steel/constitution.md`
- **Existing SV cross-module import collection:** `/Users/ezchi/Projects/pike-type/src/piketype/backends/sv/view.py:756-794`
- **Existing per-symbol cross-module golden:** `/Users/ezchi/Projects/pike-type/tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/bar_pkg.sv` (lines 2-17)

## What changed in iter3

**BLOCKING (FR-13 / Component 5 / *; vs per-symbol):** Resolved by:

1. **Component 2 (IR)** now adds a SECOND new IR node `VecConstImportIR(target_module_ref, symbol_name)` and a SECOND new `ModuleIR` field `vec_const_imports: tuple[VecConstImportIR, ...] = ()`. Cross-module VecConst sightings are now first-class IR records carrying the imported symbol's name.
2. **Component 3 (freeze)** clarified: `module.vec_constants` is **first-sightings only** (locally defined VecConsts). Non-local sightings populate `module.vec_const_imports` (per-symbol record) AND `module.dependencies` (manifest dep tracking).
3. **Component 5 (SV view)** now explicitly extends `_collect_cross_module_synth_imports` (line 774) with a small block that iterates `module.vec_const_imports` and adds `(pkg, symbol)` pairs to the existing dedup `set`. Concrete diff is shown in the plan.
4. **Wildcard vs per-symbol:** the plan now explicitly states that the codebase's actual cross-module convention is per-symbol (verified against the existing `bar_pkg.sv` golden which uses `import foo_pkg::byte_t;`, not `import foo_pkg::*;`). Spec FR-13's literal `import a_pkg::*;` is interpreted as "the codebase's per-symbol equivalent". Functional effect (importing module sees the name) is identical.

**WARNING (Component 3 dedup):** Resolved by clarification: `(target, kind)` is the natural dedup key for `ModuleDependencyIR`; per-symbol dedup happens separately at the `(pkg, symbol)` set level in the SV view. Both layers have explicit, defensible dedup defaults.

## Your task

Re-review focused on the iter3 delta:

1. **BLOCKING resolution check.** Confirm the SV view side now has explicit code to consume `module.vec_const_imports` and emit `(pkg, symbol)` pairs into `synth_cross_module_imports`. Read `src/piketype/backends/sv/view.py:774-794` to verify the proposed diff fits. Is the location correct? Are the field references (`vci.target_module_ref.basename`, `vci.symbol_name`) consistent with the IR shape proposed in Component 2?

2. **Per-symbol vs wildcard.** Confirm the plan's interpretation that FR-13's literal `*;` text is functionally equivalent to the codebase's per-symbol import convention. Specifically, look at `tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/bar_pkg.sv` lines 2-17: every cross-module import there is `import foo_pkg::name;`, NOT `import foo_pkg::*;`. The plan now matches this convention.

3. **WARNING resolution check.** Confirm the dedup discussion is now defensible.

4. **NEW issues check.** The iter3 delta added a second IR node (`VecConstImportIR`). Does this complicate the IR surface unnecessarily, or is it appropriate? (Answer should be: appropriate — first-sighting and import-sighting carry different semantic intent and need different fields.)

5. **No regression.** Confirm no unrelated plan sections were modified.

## Output Format

### Issues
**BLOCKING / WARNING / NOTE**, terse.

### Carry-Over from Iter 2
For each iter2 issue: RESOLVED / STILL BLOCKING / DOWNGRADED / WITHDRAWN.

### Verdict

End with **EXACTLY** one of:

```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

## Important

- Be strict.
- The user explicitly approved scope; do NOT re-litigate the fact that VecConst is a v1 primitive.
- The plan now uses per-symbol imports because that's the actual codebase convention. Do NOT push for wildcard `*;` — that would conflict with `tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/bar_pkg.sv` style.
- Do NOT propose implementation code; review the plan only.
