# Gauge Review Prompt — Clarification, Iteration 1

You are the **Gauge** in a strict dual-agent Forge-Gauge clarification loop.

## Inputs

- **Clarifications:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/clarifications.md`
- **Updated spec:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/spec.md`
- **Spec diff:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/artifacts/clarification/iter1-spec-diff.md`
- **Constitution:** `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

## What the Forge resolved

User answered all four open questions. All answers confirmed the spec's existing FR defaults:

- **C-1 [SPEC UPDATE]** — Q-1 closed, REJECT signed values. FR-8 stays; parenthetical Q-1 reference removed from FR-8 + OOS-1.
- **C-2 [NO SPEC CHANGE]** — Q-2 closed, VERBATIM naming. FR-12 stays; parenthetical Q-2 reference removed.
- **C-3 [SPEC UPDATE]** — Q-3 closed, OPTION A (separate `vec_constants` array). FR-18 stays; reinforcing sentence added: "The legacy `constants` array schema MUST remain byte-identical to pre-change — no `kind` discriminator is added to legacy entries." Parenthetical Q-3 reference removed.
- **C-4 [SPEC UPDATE]** — Q-4 closed, KEEP at 64. FR-5 stays; parenthetical Q-3 (stale; should have been Q-4) and OOS-2 (also stale) Q-references removed.

Open Questions section emptied: `(All open questions resolved in Clarification iteration 1. See clarifications.md.)`

## Your task

Re-review the clarifications and the spec edits:

1. **Resolutions** — does each C-N resolution correctly address the corresponding Q-N? Is the user's intent (verbatim quoted in `clarifications.md`) faithfully reflected?
2. **Spec edits** — for each [SPEC UPDATE] clarification, verify the edit was applied to the correct section, only the cited parenthetical was removed, and no FR/NFR/AC semantics changed.
3. **Reinforcement on FR-18** — is the new sentence "no `kind` discriminator is added to legacy entries" consistent with C-3's resolution (it should be — C-3 is exactly that promise)?
4. **Open Questions** — confirm the section now contains only the placeholder text, no leftover Q-entries.
5. **Unrelated sections** — confirm none were modified (cross-check against the "Sections NOT Modified" list in `iter1-spec-diff.md`).
6. **Consistency** — does the revised spec still cohere internally? Any new contradictions introduced?
7. **Constitution alignment** — Constitution still respected? FR-14's amendment proposal still valid?

## Output Format

### Issues
**BLOCKING / WARNING / NOTE**, terse, with C-N / FR-N / AC-N citations.

### Verdict

End with **EXACTLY** one of:

```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

## Important

- Be strict.
- All four Q resolutions are SCOPE NARROWINGS (or confirmations of existing defaults). Per memory `feedback_minimal_change_preserve_scope.md`, do NOT push to expand scope back out (e.g., do NOT raise "should add `signed=` for future-proofing" as BLOCKING).
- The resolutions confirm existing defaults — this is the cleanest possible clarification round. Reject only if the spec edits don't actually match the clarification claims.
- Do not propose implementation code.
