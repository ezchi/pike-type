# Gauge Code Review — Task 3, Iteration 1

You are the **Gauge**. The Forge has implemented Task 3 (freeze logic for VecConst).

## Task Description

**Title:** Implement freeze logic for VecConst in `dsl/freeze.py`

**Required:** `build_vec_const_definition_map`, `_freeze_vec_const_storage`, `_freeze_vec_const` helpers; extend `freeze_module` to populate `local_vec_constants` (first-sightings) and `local_vec_const_imports` (cross-module sightings); extend `_collect_module_dependencies` to emit `kind="vec_const_import"` edges; update `gen.py` caller. Per `tasks.md` T3 + Plan Component 3.

**Must satisfy:** FR-4, FR-5, FR-6, FR-7, FR-8, plus the FR-13 cross-module dep-edge half.

## Forge artifact (key decisions)

`/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/artifacts/implementation/task3-iter1-forge.md`

Important: the Forge declared one explicit deviation: cross-module `Const` references INSIDE a `VecConst`'s value expression do NOT currently register as `const_ref` dep edges (the value is evaluated to an int at freeze time and not preserved as IR for traversal). This is documented as a v1 acceptable behavior; the user's stated example (`B = VecConst(width=8, value=A*3)` where A and B are SAME-module) does not exercise this path. If module B has `VecConst(value=ModuleA.Const_X * 2)` in v1, the SV `import a_pkg::Const_X;` line would NOT be emitted for that ref. The user did not request this.

## Diff (HEAD~1..HEAD on freeze.py and gen.py)

```bash
git diff HEAD~1 HEAD -- src/piketype/dsl/freeze.py src/piketype/commands/gen.py
```

(See actual file contents at the paths below.)

## Code under review

- `src/piketype/dsl/freeze.py` (full file, ~580 lines after edit). Key sections:
  - `build_vec_const_definition_map` (around line 93)
  - `freeze_module` extended signature + body (around line 130-310)
  - `_collect_module_dependencies` extended VecConstImports walk (around line 360)
  - `_freeze_vec_const`, `_freeze_vec_const_storage`, `_eval_expr_int` (around lines 545-665)
- `src/piketype/commands/gen.py` (caller threads `vec_const_definition_map` through `freeze_module`).

## Review criteria

1. **Correctness**:
   - Does `build_vec_const_definition_map` mirror `build_const_definition_map` correctly? Same first-sighting semantics?
   - Does `_freeze_vec_const_storage` correctly validate width 1..64 (FR-4, FR-5)?
   - Does it correctly enforce `0 <= value <= 2**width - 1` (FR-7, FR-8)?
   - Do error messages contain ALL THREE substrings: offending value, width, formula `2**N - 1` per FR-7? (Forge confirms via inline error templates: `"value must satisfy 0 <= value <= 2**{width} - 1 (= {2**width - 1})"` plus the offending value at the front.)
   - Does `_eval_expr_int` correctly resolve `A*3` to 15? (Forge smoke-tested: yes.)
   - In `freeze_module`: is the local-vs-import discrimination correct? When `vec_const_definition_map[id(value)]` points to a different module, is `VecConstImportIR` emitted (not first-sighting)?
   - In `_collect_module_dependencies`: is the new `kind="vec_const_import"` edge emitted, deduplicated against existing `(target, kind)` pairs?
2. **Constitution compliance**: `from __future__ import annotations` already on file; basedpyright delta = 0 (verified by Forge via stash/pop round-trip); `slots=True` / `frozen=True` rules respected for new IR construction.
3. **Backwards compatibility**: existing 307 tests still pass (Forge smoke-tested).
4. **Deviation justification**: is "cross-module Const refs inside VecConst expressions don't register as deps" defensible for v1? (Forge argues: not in user's stated examples; same-module case works; deferring is honest scope-narrowing.)
5. **Code quality**: are the new helpers idiomatic? Any obvious refactor opportunities?

## Important

- This is the largest task in the implementation. Be thorough but pragmatic.
- Do NOT push for "track Const refs inside VecConst values as deps" as BLOCKING — it's an explicit Forge-acknowledged scope choice, not a correctness bug for v1.
- basedpyright delta = 0 was verified empirically; do NOT raise pre-existing errors as new.
- Constitution is highest authority.

## Output

### Issues
**BLOCKING / WARNING / NOTE**, with file:line cites where possible.

### Verdict

End with **EXACTLY** one of:

```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```
