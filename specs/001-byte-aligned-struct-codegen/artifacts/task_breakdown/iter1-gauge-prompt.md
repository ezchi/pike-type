# Gauge Review: Task Breakdown — Iteration 1

You are the Gauge reviewer. Critically review the task breakdown for completeness, ordering, dependencies, and granularity.

## Files to Review

1. **Task breakdown:** `specs/001-byte-aligned-struct-codegen/tasks.md`
2. **Implementation plan:** `specs/001-byte-aligned-struct-codegen/plan.md`
3. **Specification:** `specs/001-byte-aligned-struct-codegen/spec.md`
4. **Constitution:** `.steel/constitution.md`

## Review Criteria

### 1. Completeness
- Do the 26 tasks cover ALL functional requirements (FR-1 through FR-14)?
- Do they cover ALL non-functional requirements (NFR-1 through NFR-6)?
- Do they cover ALL 25 acceptance criteria?
- Is any spec requirement missed?

### 2. Ordering and Dependencies
- Are task dependencies correct? Can each task be implemented after its dependencies are complete?
- Is there a circular dependency?
- Are tasks ordered to minimize risk (foundation first, then backends, then testing)?

### 3. Granularity
- Are tasks small enough to implement individually but large enough to be meaningful?
- Are there tasks that should be split or merged?
- Are "update golden files" tasks appropriately placed (after the code changes that affect them)?

### 4. File Mapping
- Do all "files to modify" references point to correct paths?
- Are there missing files that need modification?

### 5. Verification Criteria
- Does each task have clear, testable verification criteria?
- Are the criteria sufficient to prove the task is complete?

### 6. Constitution Alignment
- Do tasks follow the project's testing strategy (golden-file integration tests)?
- Do tasks use frozen dataclasses, basedpyright strict, etc.?

End with `VERDICT: APPROVE` or `VERDICT: REVISE`.
