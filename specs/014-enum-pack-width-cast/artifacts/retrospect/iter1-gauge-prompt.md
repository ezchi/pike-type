# Gauge Review — Retrospect Stage, Iteration 1

You are the **Gauge** in the Forge-Gauge retrospect loop. Your job is
to verify that every claim in the retrospect report is grounded in the
cited evidence, and to flag insights the Forge missed.

## Inputs

1. **Retrospect report under review**:
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/retrospect.md`

2. **All workflow artifacts** (cited throughout the report):
   - `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/spec.md`
   - `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/clarifications.md`
   - `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/plan.md`
   - `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/tasks.md`
   - `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/validation.md`
   - All `iter*-forge.md` and `iter*-gauge.md` files under
     `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/artifacts/<stage>/`

3. **Project Constitution**:
   `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

4. **Existing user-memory directory**:
   `/Users/ezchi/.claude/projects/-Users-ezchi-Projects-pike-type/memory/`
   (You may grep this directory to verify whether a proposed memory
   duplicates an existing one.)

## Verification Tasks

### Task A — Verify proposed memories (M-1 through M-4)

For each candidate memory:

1. Read the cited artifact and confirm the evidence quote is real
   (grep the artifact for the cited string).
2. Verify the memory is genuinely non-obvious — not derivable from
   reading the codebase or git log.
3. Check whether it duplicates an existing memory in the user-memory
   directory. If it overlaps, the report should refine the existing
   memory rather than create a new one. (M-1 explicitly refines an
   existing memory; verify the refinement is real.)
4. Flag any memory whose evidence does not actually support the
   conclusion.

### Task B — Verify proposed skill updates (S-1 through S-3)

For each skill update:

1. Did the issue actually occur in this run? Re-read the cited
   artifact and confirm the quoted passage exists.
2. Is the proposed change specific enough to apply (concrete edit, not
   "improve guidance")?
3. Would the change actually have prevented the issue? Spot-check the
   logic.

### Task C — Verify process improvements (PI-1 through PI-4)

For each PI:

1. PI-1 (no bottlenecks, gauge earned its keep): re-read at least 2
   gauge artifacts. Did they actually contain spot-checks, or were
   they paragraph-of-prose rubber stamps? Cite the spot-check or its
   absence.
2. PI-2 (Constitution gap on commit prefixes): verify the
   Constitution does NOT list `forge` / `gauge` as allowed types,
   and verify the actual feature commit `4edcefe` does use the
   `forge(implementation):` prefix.
3. PI-3 (no redundant stages): the report claims dropping any stage
   would have lost a defect. Spot-check this claim for clarification:
   did clarification really catch the FR-3.1 undercount, or did it
   just rephrase the existing 3-fixture list?
4. PI-4 (Gemini fallback): verify the T4 gauge artifact has the
   "Reviewer note: Gemini was unavailable" block. Verify the
   workflow actually fell back to Claude.

### Task D — Missing insights

Are there patterns in the artifacts the Forge missed? Examples to
look for:

- Did any gauge artifact recommend a follow-up that the retrospect
  doesn't surface?
- Did any forge artifact deviate from the plan in a way the
  retrospect doesn't list as a learning?
- Did the user-memory directory lack a memory that this run reveals
  is needed?

## Output Format

```
# Gauge Review — Retrospect Stage, Iteration 1

## Summary
(2-4 sentences.)

## Findings

### Disputed memory candidates
(For each: which memory, what's wrong, evidence.)

### Disputed skill updates
(Same.)

### Disputed process improvements
(Same.)

### Missing insights
(Patterns the Forge didn't surface.)

## Verdict

VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```
