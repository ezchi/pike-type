# Gauge Review — Task Breakdown Stage, Iteration 1

You are the **Gauge** in a Forge-Gauge dual-LLM task-breakdown loop. The forge has produced an ordered task list for spec 011.

## What to do

1. Read spec at `specs/011-cross-module-type-refs/spec.md`.
2. Read plan at `specs/011-cross-module-type-refs/plan.md`.
3. Read tasks at `specs/011-cross-module-type-refs/tasks.md`.
4. Read `.steel/constitution.md`.

## What to evaluate

### A. Task completeness

- Does every FR (FR-1 through FR-16) have at least one task that implements it?
- Does every NFR have a verification path (test or check)?
- Does every AC (AC-1 through AC-24) have a task that produces evidence for it?
- Does every clarification (CL-1 through CL-10) have a corresponding task?

Build a quick coverage table.

### B. Ordering and dependencies

- Are dependencies correctly stated? (e.g., T8 depends on T7, T18 depends on T17, etc.)
- Is the sequence consistent with the staging note (Commits A-F)? Specifically:
  - Commit A tasks (T1-T6) all complete before any Commit B task starts.
  - Commit B (T7-T11) before Commit C (T12-T17).
  - etc.
- Are there parallelization opportunities the plan misses?

### C. Granularity

- Are any tasks too large to estimate? (e.g., spans more than 4 hours of focused work.)
- Are any tasks trivially small? (e.g., a single line change with no meaningful test.)
- Are integration-check tasks (T6, T11, T17, T28, T35, T37) clearly distinct from implementation tasks?

### D. Verification criteria

- Is each task's verification objective and runnable?
- Do tasks that touch goldens specify how to verify byte-parity?

### E. Risk coverage

- Are the 8 risks from the plan (R1-R8) addressed by specific tasks?
- Are there hidden risks not covered?

### F. Constitution alignment

- Tasks involve no work that contradicts constitution principles 1-6.
- Tasks involve no new external dependencies (constraint 6).

## Output format

```
# Gauge Review — Task Breakdown Iteration 1

## Summary
(2-3 sentences)

## Coverage Audit

(Quick table or list: every FR/NFR/AC/CL mapped to task IDs. Flag gaps.)

## Issues

### BLOCKING
- (issue with task ID and suggested fix)

### WARNING
- ...

### NOTE
- ...

## Strengths
- ...

VERDICT: APPROVE
```
or `VERDICT: REVISE`.

If every FR/NFR/AC has at least one task, dependencies are sound, and no BLOCKING gap is found, APPROVE.

Save to `specs/011-cross-module-type-refs/artifacts/task_breakdown/iter1-gauge.md`.

Be strict. Cite line numbers. Verify against the spec/plan/tasks/source.
