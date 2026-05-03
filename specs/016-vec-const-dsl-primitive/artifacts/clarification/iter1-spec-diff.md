# Spec Diff — Clarification Iteration 1

All edits are parenthetical-removal (cross-references to now-resolved Open Questions) plus one reinforcing sentence on FR-18 and Open Questions section emptying. **No FR/NFR/AC semantics changed.**

## FR-5

**Before:** `... the natural SV typed-literal range. (See Open Q-3 for whether to lift this.)`
**After:** `... the natural SV typed-literal range.`
**Source:** C-4 (Q-4 resolved → keep at 64).

## FR-8

**Before:** `Negative resolved values are rejected. (See Open Q-1 for whether to allow signed two's-complement representation.)`
**After:** `Negative resolved values are rejected.`
**Source:** C-1 (Q-1 resolved → reject signed values).

## FR-12

**Before:** `... This matches existing Const() behavior. (See Open Q-2 for whether to mandate LP_ prefix or uppercase.)`
**After:** `... This matches existing Const() behavior.`
**Source:** C-2 (Q-2 resolved → verbatim, no enforcement).

## FR-18

**Before:** `... so cross-module reference validation and downstream tools can see them. (See Open Q-3 for whether to fold into constants instead.)`
**After:** `... so cross-module reference validation and downstream tools can see them. The legacy constants array schema MUST remain byte-identical to pre-change — no kind discriminator is added to legacy entries.`
**Source:** C-3 (Q-3 resolved → Option A separate `vec_constants` array; reinforcing sentence added to lock in byte-identity guarantee for legacy goldens).

## OOS-1

**Before:** `... raise ValidationError on negative resolved values. (See Open Q-1.)`
**After:** `... raise ValidationError on negative resolved values.`
**Source:** C-1.

## OOS-2

**Before:** `... not requested. (See Open Q-3.)`
**After:** `... not requested.`
**Source:** C-4 (note: stale Q-3 reference, should have been Q-4 after iter2 renumbering — fixed by removal).

## Open Questions section

**Before:** Q-1 (signed), Q-2 (naming), Q-3 (manifest), Q-4 (width>64) — four `[NEEDS CLARIFICATION]` entries.
**After:** `(All open questions resolved in Clarification iteration 1. See clarifications.md.)`

## Changelog

Two new entries appended documenting the clarification round.

## Header

Status updated `Draft (Forge iteration 2)` → `Clarified (post-Clarification iteration 1)`.

## Sections NOT Modified

- Overview, Background, User Stories
- FR-1, FR-2, FR-3, FR-4, FR-6, FR-7, FR-9, FR-10, FR-11, FR-13, FR-14, FR-15, FR-16, FR-17
- All NFRs (NFR-1..5)
- All ACs (AC-1..16)
- OOS-3 through OOS-9
- Risks (R-1, R-2, R-3)
- References
