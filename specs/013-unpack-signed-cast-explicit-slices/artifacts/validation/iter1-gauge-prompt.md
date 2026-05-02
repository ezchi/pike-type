# Gauge Review — Validation, Iteration 1

You are the **Gauge** reviewing the validation report. The **Forge** has
executed the test/lint/typecheck suites and recorded an AC-by-AC verdict.
Your job: judge whether the validation evidence actually supports each
verdict.

The user's global preferences are: **be blunt, be honest, do not soften
language. Treat every review as high-stakes.**

## Inputs

1. **Project Constitution.**
   File: `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

2. **Specification.**
   File: `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/spec.md`

3. **Clarifications.**
   File: `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/clarifications.md`

4. **Validation Report (under review).**
   File: `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/validation.md`

5. **Test output artifact.**
   File: `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/artifacts/validation/iter1-test-output.txt`

6. **Regenerated golden files (cite in evidence).**
   - `/Users/ezchi/Projects/pike-type/tests/goldens/gen/struct_signed/sv/alpha/piketype/types_pkg.sv`
   - `/Users/ezchi/Projects/pike-type/tests/goldens/gen/nested_struct_sv_basic/sv/alpha/piketype/types_pkg.sv`
   - `/Users/ezchi/Projects/pike-type/tests/goldens/gen/scalar_sv_basic/sv/alpha/piketype/types_pkg.sv`

## What to focus on

1. **AC verdicts.** For every AC marked PASS, is the cited evidence
   factually correct? Open the cited golden file and confirm the line
   the report quotes.

2. **PARTIAL verdicts.** AC-8 / NFR-3 are recorded as PARTIAL because
   of pre-existing pyright errors. Is the framing honest, or is the
   spec's NFR-3 actually being violated and the Forge is hand-waving?

3. **Hidden failures.** Did the unittest output truly show 303 pass / 3
   skip? Inspect `iter1-test-output.txt`. Are the 3 skips pre-existing
   (perf gate etc.) or is one of them a test we should have run?

4. **AC-9 lint claim.** Does the delta-check claim hold up? The Forge
   reports 4 pre-existing UNUSEDPARAM/UNUSEDSIGNAL warnings unchanged.
   Is this consistent with what Verilator would actually report? If
   Verilator 5.046 with -Wall does NOT flag signed-mismatch as a
   warning by default (Forge's NOTE), is this feature's lint-clean
   claim still meaningful? Or is the spec's "lint clean" goal partially
   illusory?

5. **Completeness.** Has any FR or AC been left unverified? Is there
   evidence the Forge skipped a check?

6. **Constitution alignment.** Does the validation respect "correctness
   over convenience" (no glossed-over failures), "deterministic output"
   (delta verified), and the test-strategy mandates?

## Issue Severity

- **BLOCKING** — cannot approve.
- **WARNING** — can ship but reviewer will push back.
- **NOTE** — minor.

## Output Format

```
# Gauge Review — Validation, Iteration 1

## Summary
(2–4 sentences.)

## AC Verdict Audit
- AC-1: ...
- AC-2: ...
- (each AC)

## NFR Audit
- (each NFR)

## Issues

### BLOCKING
- ...

### WARNING
- ...

### NOTE
- ...

## Constitution Alignment
(One paragraph.)

## Verdict
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

The very last line of your output MUST be exactly `VERDICT: APPROVE` or
`VERDICT: REVISE` — no trailing whitespace, no markdown decoration, no
period.

Be strict. If in doubt, REVISE.
