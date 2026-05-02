# Gauge Review Task — Task Breakdown Stage, Iteration 1

You are the **Gauge** in a Forge-Gauge dual-agent task-breakdown loop. Your
role is to critically review the task list produced by the Forge.

## Inputs

1. **Project Constitution**:
   `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

2. **Specification** (post-clarification):
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/spec.md`

3. **Implementation plan**:
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/plan.md`

4. **The task breakdown under review**:
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/tasks.md`

5. **The codebase** — verify any factual claim by grep / read.
   Particularly check:
   - The "Plan corrections required" section in tasks.md flags that
     `tests/fixtures/cross_module_type_refs_namespace_proj/` does not
     exist as a fixture directory. Verify with
     `ls tests/fixtures/cross_module_type_refs_namespace_proj` (should
     fail) and `grep -n "namespace_proj" tests/test_gen_cross_module.py`.
   - The per-fixture invocation table in tasks.md lists the correct
     `cli_file` argument for each fixture. Verify by reading
     `tests/test_gen_enum.py:34-50`,
     `tests/test_struct_enum_member.py:36-52`,
     `tests/test_validate_keywords.py:94-107`,
     `tests/test_gen_cross_module.py:34-44`, and
     `tests/test_gen_cross_module.py:95-107`.

## Review Criteria

1. **Task completeness.** Does the task list cover every step needed
   to satisfy every spec FR / NFR / AC?
2. **Ordering.** Are tasks ordered such that each task's dependencies
   are satisfied by earlier tasks?
3. **Dependencies.** Are inter-task dependencies declared explicitly
   and correctly?
4. **Granularity.** Are tasks the right size? For a one-line template
   fix plus a 5-fixture golden refresh, four tasks (T1: edit; T2:
   regen; T3: verify; T4: commit) is plausible. Is anything missing or
   superfluous?
5. **Plan corrections.** The tasks.md flags one plan correction (the
   missing `cross_module_type_refs_namespace_proj` fixture / the
   missing `--namespace=proj::lib` CLI flag in the plan). Is this
   correction itself accurate? Are there other plan-vs-repo mismatches
   the Forge missed?
6. **Verification criteria.** Does each task have concrete,
   automatable verification (grep, diff, test command)?
7. **Constitution alignment.** Specifically:
   - Branching & Commits — does the proposed commit message follow
     Conventional Commits?
   - Testing — are golden-file integration tests the right
     verification?
   - Per-commit byte parity (`feedback_byte_parity_per_commit.md`) —
     does T4 enforce a single atomic commit?

## Output Format

```
# Gauge Review — Task Breakdown Stage, Iteration 1

## Summary
(2-4 sentences.)

## Issues

### BLOCKING
(If none, write "None.")

### WARNING
(If none, write "None.")

### NOTE
(Minor remarks.)

## Plan-corrections check
(Did the Forge correctly flag the namespace_proj plan gap? Are there
other gaps the Forge missed?)

## Spec coverage matrix
(For each FR/NFR/AC, name the task(s) that satisfy it.)

## Constitution Alignment
(One paragraph.)

## Verdict

VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

Be strict. The verdict line MUST appear verbatim, on its own line.
