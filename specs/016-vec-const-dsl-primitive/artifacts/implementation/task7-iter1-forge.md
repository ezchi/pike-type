# Task 7: Amend Constitution §Constraints item 5 — Forge Iteration 1

## Files Changed
- `.steel/constitution.md` — modified. §Constraints item 5 paragraph rewritten per spec FR-14.

## Key Implementation Decisions
- One-paragraph amendment, no other Constitution clause touched (FR-15).
- Wording matches FR-14 verbatim: scopes the 32/64-bit restriction to `Const()`; admits `VecConst()` at widths 1..64; both validated by the validation layer.

## Deviations from Plan
- None.

## Verification
- `git diff .steel/constitution.md` shows only the §Constraints item 5 paragraph changed; no other clause touched. Spot-verified by reading the file before and after.

## Tests Added
- None.
