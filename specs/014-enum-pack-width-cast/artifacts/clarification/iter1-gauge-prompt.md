# Gauge Review Task — Clarification Stage, Iteration 1

You are the **Gauge** in a Forge-Gauge dual-agent clarification loop. Your role
is to critically review the clarifications produced by the Forge AND verify
that the spec.md updates were correctly applied.

## Inputs

1. **Project Constitution** (highest authority):
   `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

2. **The clarifications under review**:
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/clarifications.md`

3. **The updated specification**:
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/spec.md`
   (compare against the iter1-forge baseline if you want to see the
   pre-clarification version:
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/artifacts/specification/iter1-forge.md`)

4. **The spec-diff artifact** (before → after for each modified section):
   `/Users/ezchi/Projects/pike-type/specs/014-enum-pack-width-cast/artifacts/clarification/iter1-spec-diff.md`

5. **The codebase** — you may grep / read source to verify factual claims.
   Particularly relevant:
   - `src/piketype/backends/sv/templates/_macros.j2` (the bug site at line 98)
   - `tests/goldens/gen/**/*.sv` (the affected goldens, all 5 fixtures)
   - `src/piketype/backends/sv/view.py` (view fields available to templates)

## Review Instructions

You must check three classes of issues:

### A. Quality of clarifications (clarifications.md)

1. **Completeness of resolution.** Does every `[NEEDS CLARIFICATION]`
   marker in the iter-1 spec have a clear, justified resolution in
   clarifications.md? Are there ambiguities the Forge missed?
2. **Logic.** Are the rationales sound? In particular:
   - C-1's rejection of an SV-execution harness — is this justified
     given the Project Constitution's emphasis on golden-file testing
     (Testing section) and Principle 4 (Correctness over convenience)?
   - C-2's grep claim — verify by running the grep yourself; does the
     evidence actually show only one occurrence in the templates?
   - C-3's claim that 8 hits exist across 5 fixtures — verify by running
     the grep yourself.
   - C-6's Verilator size-cast compatibility claim — is the cast
     `LP_<UPPER>_WIDTH'(a)` actually legal SV with a `localparam int`
     prefix? Spot-check this.
3. **Constitution alignment.** Does any clarification contradict the
   constitution? Pay attention to Principle 5 (Template-first
   generation) — C-7 reaffirms this, which is good.

### B. Correctness of spec.md updates

For each `[SPEC UPDATE]` clarification (C-2, C-3, C-4):

1. **Was the change actually applied to spec.md?** Read the relevant
   section of the current spec.md and verify the new text is present
   and the old text is gone.
2. **Is the change consistent with the rest of the spec?** Specifically:
   - The new FR-3.1 5-fixture list — does it contradict anything in
     FR-3.2 / FR-3.3 / NFR-2 / AC-6 / AC-7?
   - The new AC-2 with exact count of 8 — does the 8 reconcile with the
     pre-fix grep count and with FR-3.1's "8 lines change" statement?
   - The Open Questions section — has it been collapsed correctly, with
     pointers to C-1 and C-2?
3. **Was anything unintended modified?** Compare the iter1-forge
   baseline to current spec.md for sections OTHER than FR-3.1, AC-2, and
   Open Questions. Sections like FR-1, FR-2, NFRs, and Out of Scope MUST
   be unchanged.
4. **Changelog accuracy.** The new `## Changelog` section at the bottom
   of spec.md — does each entry accurately describe its change?

### C. Missed updates

Are there clarifications marked `[NO SPEC CHANGE]` that arguably should
have been `[SPEC UPDATE]`? In particular:

- C-5 (golden regen pattern) — should this be a sentence in spec.md
  instead of clarifications-only? (The Forge argues no — it's a
  planning-stage detail. Evaluate.)
- C-6 (Verilator size-cast compatibility) — same question.
- C-7 (`view.upper_base` availability) — same question.
- C-8 (per-commit byte parity) — NFR-2 already covers this. Confirm
  the Forge's [NO SPEC CHANGE] judgement is correct.

## Output Format

```
# Gauge Review — Clarification Stage, Iteration 1

## Summary
(2-4 sentences: top-line judgement on clarifications + spec updates)

## Issues

### BLOCKING
(If none, write "None.")

### WARNING
(If none, write "None.")

### NOTE
(Minor remarks.)

## Verification of Spec Updates
(Per [SPEC UPDATE] clarification: was it applied correctly? Cite
section/line evidence.)

## Constitution Alignment
(One paragraph.)

## Verdict

VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

Be strict. The verdict line MUST appear verbatim, on its own line.
