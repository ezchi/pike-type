# Spec Diff — Clarification Iteration 2

Records the additional `spec.md` edit applied in clarification iteration 2,
on top of the iteration-1 changes (already recorded in `iter1-spec-diff.md`).

---

## Change 4 — Open Questions (OQ-3 resolution refined)

**Before** (iteration 1 / iteration 2 spec text)

> ## Open Questions
>
> (All open questions raised in iteration 1 are resolved in this iteration:
> OQ-1 → part-select `a[i:i]` form; OQ-2 → cast operator `signed'(...)` form;
> OQ-3 → new fixture, do not edit existing fixtures. No outstanding open
> questions remain.)

**After** (post clarification iteration 2)

> ## Open Questions
>
> (All open questions raised in iteration 1 are resolved:
> OQ-1 → part-select `a[i:i]` form;
> OQ-2 → cast operator `signed'(...)` form;
> OQ-3 → reuse the existing `tests/fixtures/struct_signed/` fixture, which
> already exercises a signed inline `Logic(N, signed=True)` field — no new
> fixture is created (resolution refined by Clarification Q1, supersedes
> the iteration-2 wording that mandated a new fixture).
> No outstanding open questions remain.)

**Source.** Gauge BLOCKING #1 — iteration-1 left an internal contradiction
between AC-4 (rebound to existing fixture) and OQ-3 (still saying "new
fixture"). Iteration 2 aligns OQ-3's resolution with AC-4.

---

## Change 5 — clarifications.md summary table corrected

Not a `spec.md` edit, but recorded here for completeness because the
gauge flagged it: the iteration-1 summary table in `clarifications.md`
incorrectly listed "Out of Scope" as a strike target. The actual target
of the strike was the OQ-3 line in "Open Questions". Iteration 2 fixes
the summary table, removes the Out-of-Scope row, and adds an explicit
"Open Questions" row plus a footnote disambiguating the previous wording.

**Source.** Gauge BLOCKING #2.

---

## Change 6 — Q7 added to clarifications (NO SPEC CHANGE)

A new question (Q7) was added to `clarifications.md` to make explicit the
need to add `slice_low: int`, `slice_high: int`, and `is_signed: bool`
fields to `SvSynthStructUnpackFieldView`. This is implementation surface
captured to prevent the planning stage from missing it. No `spec.md` change.

**Source.** Gauge WARNING #1.
