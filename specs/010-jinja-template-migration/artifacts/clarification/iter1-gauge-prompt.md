# Gauge Review Prompt — Clarification Iteration 1

You are the **Gauge** in a dual-agent Forge-Gauge loop. The specification stage already produced an APPROVED spec. This is the clarification stage: open questions Q-1..Q-4 have been resolved as CL-1..CL-4, and three new requirements (FR-23, FR-24, FR-25) were added to make those resolutions enforceable.

## Inputs to Review

1. **Specification (current):** `specs/010-jinja-template-migration/spec.md` — contains the new "Resolved Clarifications" section, the "Clarification-driven additions" (FR-23..FR-25), and an empty "Open Questions" section.
2. **Clarification forge output:** `specs/010-jinja-template-migration/artifacts/clarification/iter1-forge.md`.
3. **Project Constitution:** `.steel/constitution.md`.

## Review Instructions

This is a **delta** review focused on:

1. **Were Q-1..Q-4 fully resolved?** Check that each question is replaced by a concrete decision (CL-1..CL-4) with no remaining ambiguity, weasel words, or hidden alternatives.

2. **Are CL-1..CL-4 internally consistent with the rest of the spec?**
   - CL-1 vs. NFR-6 (revertability) and AC-F8 (commit ordering).
   - CL-2 vs. FR-10/FR-11 (no semantics in templates) and FR-21 (lint patterns).
   - CL-3 vs. FR-2/FR-3 (loader strategy) and AC-F5 (wheel install).
   - CL-4 vs. NFR-1 (perf measurement) and AC-F4 (perf gate).

3. **Are FR-23, FR-24, FR-25 testable and concrete?**
   - FR-23: is the CLI signature unambiguous? Will a developer build it without further questions?
   - FR-24: does the per-filter checklist match what FR-21 / CL-2 require?
   - FR-25: does the table schema let AC-F4 actually be checked numerically?

4. **Are there any new contradictions introduced by FR-23..FR-25?** In particular:
   - Does FR-23's `--output -` to stdout conflict with the requirement that `perf.md` be the authoritative store (CL-4)? (Answer expected: no, because the implementation captures stdout into `perf.md`.) Confirm.
   - Does FR-25's "feature-final" row require an additional measurement run beyond per-backend rows? Is that run defined elsewhere? If not, flag.

5. **Constitution alignment.** Specifically check Principles 3 (determinism) and 5 (template-first); do any of CL-1..CL-4 or FR-23..FR-25 weaken either principle?

Apply severity tags `BLOCKING`, `WARNING`, `NOTE`. End with exactly `VERDICT: APPROVE` or `VERDICT: REVISE`. No text after the verdict line.

Approve if every Q is resolved as a concrete decision and no new contradiction has been introduced. Bias toward APPROVE when in doubt — the clarification stage's purpose is exactly to lock answers in, not to perpetuate debate.
