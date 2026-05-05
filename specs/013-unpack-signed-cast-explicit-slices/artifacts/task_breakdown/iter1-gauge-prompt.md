# Gauge Review — Task Breakdown, Iteration 1

You are the **Gauge** reviewing the implementation task list. The **Forge**
broke the plan into ordered, atomic, byte-parity-preserving tasks.
Your job: find what's missing, what's wrong, what an implementer could
get stuck on, and what would leave a commit in a half-finished state.

The user's global preferences are: **be blunt, be honest, do not soften
language. Treat every review as high-stakes.**

## Inputs

1. **Project Constitution.**
   File: `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

2. **Specification.**
   File: `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/spec.md`

3. **Clarifications.**
   File: `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/clarifications.md`

4. **Plan.**
   File: `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/plan.md`

5. **Tasks (under review).**
   File: `/Users/ezchi/Projects/pike-type/specs/013-unpack-signed-cast-explicit-slices/tasks.md`

6. **Codebase context** (read-only):
   - `/Users/ezchi/Projects/pike-type/src/piketype/backends/sv/templates/_macros.j2`
   - `/Users/ezchi/Projects/pike-type/src/piketype/backends/sv/view.py`
   - `/Users/ezchi/Projects/pike-type/tests/goldens/gen/struct_signed/sv/alpha/piketype/types_pkg.sv`

## What to focus on

1. **Atomicity.** Does T-001 leave the suite green (yes — new fields are
   unused)? Does T-002 leave the suite green (yes — template + goldens
   refresh atomically)? Could either commit be split such that one half
   passes and the other doesn't? If yes, flag.

2. **Coverage of plan components.** C-1 / C-2 → T-001. C-3 → T-002.
   C-4 → T-002. C-5 → "skipped, collapsed into T-001 verify". Does any
   plan element have no task?

3. **Acceptance traceability.** Every AC in the spec must map to a
   verify step in some task. The traceability table at the bottom of
   tasks.md is a good start; check it for gaps. Does AC-9 belong to
   the validation stage, or should it be partially verified at
   implementation time?

4. **Implementation-note correctness.** In T-001 the formula
   `is_signed = is_signed_eff and not is_type_ref` — does this correctly
   force False for type-refs? In T-002 the branch ordering — does
   `f.is_type_ref` first / `f.is_signed` second / fallback last
   correctly partition? Are there type-ref fields that could ALSO be
   signed-padded such that the new branch order breaks the padding
   line?

5. **Golden-refresh procedure.** Is "follow the manual refresh pattern
   from prior specs" sufficient, or does the implementer need a more
   concrete command? Does the project actually have a "regen goldens"
   command (e.g. `piketype gen --update-goldens` or a dev-tool script)?
   Inspect the repo if needed; if no such command exists, T-002 may
   leave the implementer guessing.

6. **Commit messages.** Conventional Commits format: `<type>(<scope>):
   <description>`. `refactor(sv): ...` and `feat(sv): ...` — fine?

7. **Verify-step rigour.** Are the grep / hand-check verifications
   precise enough that an implementer can mechanically pass/fail them?

## Issue Severity

- **BLOCKING** — cannot approve.
- **WARNING** — can ship but reviewer will push back.
- **NOTE** — minor.

## Output Format

```
# Gauge Review — Task Breakdown, Iteration 1

## Summary
(2–4 sentences.)

## Plan-to-Task Coverage
- C-1 (`SvSynthStructUnpackFieldView`): covered-by T-00x / missing.
- C-2 (`_build_struct_pack_unpack`): ...
- C-3.1 (scalar_alias macro): ...
- C-3.2 (struct macro): ...
- C-4 (golden refresh): ...
- C-5 (view-test alignment): ...

## AC Traceability
(Walk every AC; flag any AC not verified by some task.)

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
