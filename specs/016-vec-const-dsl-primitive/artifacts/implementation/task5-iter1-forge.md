# Task 5: Update manifest/write_json.py to emit vec_constants array — Forge Iteration 1

## Files Changed
- `src/piketype/manifest/write_json.py` — modified. Added `"vec_constants": [...]` array sibling to `"constants"` in the per-module dict.

## Key Implementation Decisions
- Added the new array AFTER the existing `"dependencies"` block in source order. The output is dumped with `sort_keys=True`, so alphabetical ordering puts `"vec_constants"` last in each module dict (after `"basename"`, `"constants"`, `"dependencies"`, `"generated_outputs"`, `"namespace_parts"`, `"python_module_name"`, `"repo_relative_path"`, `"source"`, `"types"`).
- Each entry has fields `name`, `width`, `value`, `base`, and `source` per FR-18. Field ordering inside each entry is also alphabetical due to `sort_keys=True`: `base`, `name`, `source`, `value`, `width`.
- Existing `"constants"` array shape is BYTE-IDENTICAL to pre-change (FR-18 reinforced clarification). No `kind` discriminator added to legacy entries.

## Deviations from Plan
- None. Implementation follows Plan Component 8 exactly.

## Verification
- `.venv/bin/basedpyright src/piketype/manifest/write_json.py`: `0 errors, 0 warnings, 0 notes`. ✓

## Tests Added
- None in this task. Manifest output is verified at T9/T10 (new fixture goldens) and T11 (regenerated existing goldens).
