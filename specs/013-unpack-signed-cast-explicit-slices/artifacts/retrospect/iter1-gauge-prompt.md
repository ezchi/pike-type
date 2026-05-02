# Gauge Review — Retrospect, Iteration 1

You are the **Gauge** reviewing the retrospect document. The **Forge** has
produced a workflow summary, memory candidates, skill update suggestions,
and process observations. Your job: judge whether the retrospect is
honest, complete, and actionable.

The user's global preferences are: **be blunt, be honest, do not soften
language. Treat every review as high-stakes.**

## Inputs

1. **Project Constitution.**
   File: `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

2. **All workflow artifacts** (browse as needed):
   - `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/spec.md`
   - `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/clarifications.md`
   - `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/plan.md`
   - `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/tasks.md`
   - `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/validation.md`
   - `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/artifacts/**/*.md`

3. **Retrospect (under review).**
   File: `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/retrospect.md`

## What to focus on

1. **Workflow Summary table accuracy.** Cross-check the iteration counts
   and verdict trails against the actual artifacts (e.g., specification
   has `iter1-gauge.md` with `VERDICT: REVISE` and `iter2-gauge.md` with
   `VERDICT: APPROVE`; clarification has same; planning has only iter1).

2. **Memory candidates.** Are M-1 through M-5 substantive (not generic),
   non-obvious, and likely to be useful in future conversations?
   Specifically:
   - M-1 (struct_signed coverage): is the fixture really covering all
     four paths? Spot-check the file.
   - M-2 (golden regen pattern): is this distinct from anything already
     in `/Users/ezchi/.claude/projects/-Users-ezchi-Projects-pike-type/memory/MEMORY.md`?
   - M-3 (namespace_proj orphan): factually correct? Check the test
     file.
   - M-4 (`_is_field_signed` returns True for type-ref): is this a real
     finding from the code, or speculation?
   - M-5 (Verilator 5.046 SIGNED gap): is the claim factually correct
     vs. the validation evidence?

3. **Skill update candidates.** Are S-1 (piketype-sv-backend) and S-2
   (refresh-goldens tool) reasonable proposals, or are they
   nice-to-haves that don't justify the change overhead?

4. **Process observations honesty.** P-1 admits the clarification iter-1
   REVISE was self-inflicted by the Forge. Is the analysis correct, or
   is the Forge being too hard on itself / not hard enough?

5. **Constitution gaps and workflow gaps.** Are the recurring issues
   (pyright baseline, clarification verification) accurately framed?
   Should anything else be flagged?

## Issue Severity

- **BLOCKING** — cannot approve.
- **WARNING** — can ship but reviewer will push back.
- **NOTE** — minor.

## Output Format

```
# Gauge Review — Retrospect, Iteration 1

## Summary
(2–4 sentences.)

## Workflow Summary Audit
(Cross-check the iteration table against artifacts.)

## Memory Candidate Audit
- M-1: substantive / generic / wrong — short note.
- M-2: ...
- M-3: ...
- M-4: ...
- M-5: ...

## Skill Update Audit
- S-1: reasonable / overreach / wrong scope.
- S-2: ...

## Issues

### BLOCKING
- ...

### WARNING
- ...

### NOTE
- ...

## Constitution Alignment
(One paragraph.)

## Verdict
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

The very last line of your output MUST be exactly `VERDICT: APPROVE` or
`VERDICT: REVISE` — no trailing whitespace, no markdown decoration, no
period.

Be strict. If in doubt, REVISE.
