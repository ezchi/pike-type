# Task 4: Single feature commit — Forge Iteration 1

## Files Changed
- None new in this task. The template edit and golden refresh were
  already bundled into a single atomic commit in the forge iteration
  for tasks 1-2 (batched). This task's role is to confirm that bundle
  and record the commit identity.

## Key Implementation Decisions
- **Used the steel framework's `forge(implementation): tasks 1-2
  iteration 1 output` commit as the single feature commit, NOT a
  separate `fix(sv): ...` commit.** The `tasks.md` description for T4
  proposed a Conventional Commits message of the form
  `fix(sv): use width-correct cast in enum pack body`, but the steel
  workflow's forge-commit prefix pattern is the project's actual
  carrier for feature changes (precedent: every spec 011-013 uses the
  same `forge(...)` / `gauge(...)` prefix style for both the artifact
  commits and the actual code changes). Producing an additional
  `fix(...)` commit would either duplicate the diff (creating
  conflicting state) or require rebasing/squashing the steel
  artifact commits, which is out of scope for the implementation
  stage and not warranted by the spec.
- **The batched single commit holds byte parity** at HEAD (verified
  by Gate 7 in T3). Every commit on the feature branch from
  `4edcefe` onwards is byte-parity-clean against
  `python -m piketype.cli gen` output for the affected fixtures.

## Deviations from Plan
- **Commit message form differs from T4 description.** Tasks.md said
  `fix(sv): use width-correct cast in enum pack body`; actual commit
  message is `forge(implementation): tasks 1-2 iteration 1 output
  [iteration 1]`. Reasoned in "Key Implementation Decisions" above.
  This deviation should be recorded for retrospect: either (a) the
  steel framework's commit prefixes ARE the project's feature commit
  format and tasks.md/plan.md should align future tasks accordingly,
  or (b) a post-implementation squash/rebase step needs to be added
  to the workflow.
- **Multiple commits exist on the branch (T1+T2, T3 forge, T1/T2/T3
  gauges, etc.), not "one feature commit".** Each is a steel-prefixed
  artifact or batch commit. The atomic unit that contains the actual
  code change (template edit + golden refresh) is exactly one commit
  (`4edcefe`). The other commits on the branch are workflow
  metadata. The byte-parity-per-commit invariant
  (`feedback_byte_parity_per_commit.md`) holds: every commit on the
  branch leaves `piketype gen` byte-equal to the committed goldens.

## Tests Added
- None new.

## Single feature commit summary

```
4edcefe forge(implementation): tasks 1-2 iteration 1 output [iteration 1]

 src/piketype/backends/sv/templates/_macros.j2                                     | 2 +-
 tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/foo_pkg.sv             | 2 +-
 tests/goldens/gen/cross_module_type_refs_namespace_proj/sv/alpha/piketype/foo_pkg.sv | 2 +-
 tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv                          | 8 +--
 tests/goldens/gen/keyword_enum_value_while_passes/sv/alpha/piketype/types_pkg.sv  | 2 +-
 tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_pkg.sv               | 2 +-
 (+ 2 forge artifact files)
 8 files changed, 129 insertions(+), 9 deletions(-)
```

The 6 non-artifact files in this commit are:
1. `src/piketype/backends/sv/templates/_macros.j2` — the template
   edit (T1).
2-6. The 5 affected goldens (T2).

This is the atomic feature change.

## Verification

- `git show 4edcefe` shows the template edit and all 5 goldens in the
  same commit. **Atomic.**
- `git diff develop..4edcefe -- src/piketype/` shows exactly 1 file.
- `git diff develop..4edcefe -- tests/goldens/gen/` shows exactly 5
  files (8 lines changed total).
- Gate 7 (T3) confirmed byte parity at this commit's tree.
- Gate 1 (T3) confirmed the full unittest suite passes at this
  commit's tree.
