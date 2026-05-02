# Task 19: Update docs/architecture.md (NFR-5) — Forge Iteration 1

## Files Changed

- `docs/architecture.md` — modified. Added one paragraph to the `### validate/` subsection (after the "validation should be implemented as explicit passes" sentence) describing the reserved-keyword validation pass: where it runs in the pipeline, what identifiers it checks, what languages it targets, where the keyword sets live (`validate/keywords.py`), and an explicit example contrasting `logic.py` (accepted) vs. `class.py` (rejected) to convey the per-language emitted-form check.

## Key Implementation Decisions

- Single paragraph, ~7 sentences. Resists the temptation to over-document — `validate/keywords.py` itself has the deeper reference comment per NFR-5.
- Explicitly mentions `_validate_reserved_keywords` and `validate/keywords.py` so readers can grep into the source.
- Worked example (logic vs class) makes the FR-1.6 per-language semantic concrete.

## Deviations from Plan

None.

## Tests Added

None — docs only. Verification: `git diff docs/architecture.md` shows only an addition (no changes to surrounding paragraphs).
