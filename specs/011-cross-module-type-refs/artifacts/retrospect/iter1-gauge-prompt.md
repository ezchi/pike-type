# Gauge Verification — Retrospect Stage, Iteration 1

You are the **Gauge** in a retrospect loop. Your job is to verify that every claim in the retrospect report is supported by the cited artifacts.

## Inputs

- Retrospect report: `specs/011-cross-module-type-refs/retrospect.md`
- Spec: `specs/011-cross-module-type-refs/spec.md`
- Validation: `specs/011-cross-module-type-refs/validation.md`
- All iter*-forge.md and iter*-gauge.md under `specs/011-cross-module-type-refs/artifacts/`
- Source code referenced by claims (e.g., `src/piketype/loader/python_loader.py`, `src/piketype/backends/sv/templates/_macros.j2`)

## What to verify

### 1. Memory candidates (M1-M6)

For each candidate memory, read the cited evidence and verify:
- The cited artifact actually exists.
- The quoted passage actually appears in that artifact (or matches the artifact's substance).
- The memory is non-obvious — not derivable from existing constitution or codebase docs.
- The memory is actionable — has a clear "How to apply" pathway.

Reject any memory where the evidence is missing, misquoted, or the conclusion doesn't follow.

### 2. Skill updates (S1-S4)

For each proposed update:
- Did the issue actually occur as described in the cited artifact?
- Is the proposed change specific enough that someone could apply the edit?
- Would it actually have prevented the issue?

Reject vague suggestions (e.g., "improve X" without a concrete edit).

### 3. Process improvements (P1-P6)

- For each bottleneck claim, verify the iteration count by reading the artifact filenames.
- For each REVISE classification (real defect / valid standard / churn), verify the characterization against the cited gauge artifact.
- Reject any mischaracterization (e.g., calling a real defect "churn").

### 4. Missing insights

Are there patterns in the artifacts the Forge missed? Specifically scan for:
- Any recurring gauge complaint that the report doesn't surface.
- Any skill that was clearly needed but not invoked.
- Any constitution gap not addressed.

## Output format

```
# Gauge Verification — Retrospect Iteration 1

## Memory Verification

For each M1-M6:
- ✓ supported (cite evidence)
- ✗ unsupported (explain)
- ~ partial (explain)

## Skill Update Verification

For each S1-S4:
- ✓ specific enough to apply
- ✗ too vague / wrong issue
- ~ partial

## Process Improvement Verification

For each P1-P6:
- ✓ accurate
- ✗ mischaracterized
- ~ partial

## Missing Insights

(any patterns the Forge missed)

## Issues
### BLOCKING
...

VERDICT: APPROVE
```
or `VERDICT: REVISE`.

If every cited claim checks out and no missing insight is BLOCKING, APPROVE.

Save to `specs/011-cross-module-type-refs/artifacts/retrospect/iter1-gauge.md`.

Be strict. Cite artifact paths and line numbers.
