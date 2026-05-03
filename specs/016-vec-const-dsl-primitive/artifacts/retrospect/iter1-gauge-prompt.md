# Gauge Verification Prompt — Retrospect, Iteration 1

You are the **Gauge** in a strict dual-agent Forge-Gauge retrospect loop. Verify every claim against the cited evidence.

## Inputs

- **Retrospect under review:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/retrospect.md`
- **All workflow artifacts:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/artifacts/{specification,clarification,planning,task_breakdown,implementation,validation}/`
- **Spec/plan/clarifications/tasks/validation:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/{spec,plan,clarifications,tasks,validation}.md`
- **State:** `/Users/ezchi/Projects/pike-type/.steel/state.json`
- **Constitution:** `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

## Required Verification Checks

### 1. Workflow summary table

Confirm iteration counts and verdicts per stage:
- Spec: 2 iters (REVISE → APPROVE).
- Clarification: 1 iter (APPROVE).
- Planning: 3 iters (REVISE → REVISE → APPROVE).
- Task breakdown: 1 iter (APPROVE).
- Implementation: 13 tasks, T4 has 2 iters (iter1 REVISE, iter2 APPROVE), all others 1 APPROVE.
- Validation: 2 iters (REVISE → APPROVE).

Verify by listing `iter*-gauge.md` per stage and reading VERDICT lines.

### 2. Memory candidates

For each of M-1, M-2, M-3:
- Open the cited artifact files.
- Confirm the quoted passages exist verbatim.
- Check the memory is non-obvious (not derivable from `grep`/git history/Constitution).
- Check it's of one of: user / feedback / project / reference.
- Verify "How to apply" is concrete.

Specifically:
- **M-1** evidence cite: `artifacts/validation/iter1-gauge.md` quoting all four missed passes. Verify the quote.
- **M-2** evidence cite: T11 forge artifact + 307 tests passing.
- **M-3** evidence cite: planning iter1 + iter2 + iter3 artifacts.

### 3. Skill update verification

For each of S-1, S-2, S-3:
- Did the issue actually occur as described?
- Is the proposed change specific enough to apply?
- Would it actually have prevented the issue in this run?

Specifically:
- **S-1**: validate/engine.py extension was missing — `artifacts/validation/iter1-gauge.md` BLOCKING confirms.
- **S-2**: wildcard `*;` vs per-symbol convention confusion — `artifacts/planning/iter2-gauge.md` BLOCKING.
- **S-3**: T3 forge artifact didn't list downstream validation touchpoints — read T3 forge artifact + validation iter1 artifact.

### 4. Process improvement verification

For P-1, P-2, P-3, P-4: confirm REVISE classifications match the actual gauge verdicts. The Forge classifies all 6 REVISE as "(a) caught a real defect, 0 churn." Verify by reading each REVISE gauge artifact.

### 5. Missing insights

Look for patterns in the artifacts the Forge missed. Examples:
- A skill that was needed but not invoked (e.g., did `sv-style-check` need to fire?).
- A recurring gauge complaint never surfaced as a memory or skill update.
- Constitution principles tested implicitly worth surfacing.

### 6. Self-check

Confirm the Forge's "23 forge-gauge cycles" tally matches: 2 (spec) + 1 (clar) + 3 (plan) + 1 (tasks) + 14 (impl: 13 tasks + T4 iter2) + 2 (validation) = 23. ✓

## Output

### Issues
**BLOCKING / WARNING / NOTE**, with concrete cites (file:passage).

### Verdict

End with **EXACTLY** one of:

```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

Approve only if zero BLOCKING issues remain.

## Important

- Be adversarial. Same-agent (Claude) was the Forge; do not assume good faith.
- Reject memories whose evidence is missing or misquoted.
- Reject skill updates that are too vague.
- The Constitution is highest authority.
