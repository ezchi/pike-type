# Gauge Review Prompt — Specification, Iteration 1

You are the **Gauge** in a strict dual-agent Forge-Gauge specification loop. The Forge has produced a draft specification.

## Inputs

- Specification: `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/spec.md`
- Project Constitution (highest authority — note this spec proposes a Constitution amendment in FR-14): `/Users/ezchi/Projects/pike-type/.steel/constitution.md`
- Existing Const code: `/Users/ezchi/Projects/pike-type/src/piketype/dsl/const.py`
- Existing SV const renderer: `/Users/ezchi/Projects/pike-type/src/piketype/backends/sv/view.py:306-321`
- Existing SV synth template: `/Users/ezchi/Projects/pike-type/src/piketype/backends/sv/templates/module_synth.j2`
- Existing SV synth-package goldens with `Const`: `/Users/ezchi/Projects/pike-type/tests/goldens/gen/const_sv_basic/sv/alpha/piketype/constants_pkg.sv`

## Background

This spec adds a NEW DSL primitive `VecConst(width=N, value=V, *, base="hex"|"dec"|"bin")` distinct from existing `Const()`. Direction was selected by the user at the workflow opening (option (a) — new primitive, name `VecConst`). The spec also proposes a Constitution amendment (FR-14) to scope the existing 32/64-bit-restriction to `Const()` only.

## Review Criteria

1. **Completeness** — every FR/NFR/AC populated and substantive? Any user story implied by the feature description left unmodeled? Are validation messages, cross-module rules, manifest impact, and other backend (C++/Python) emission addressed (or properly surfaced as open questions)?
2. **Clarity** — could two implementers read FR-N and produce divergent code? Specifically check FR-9 / FR-10 / FR-11 for unambiguous rendering rules.
3. **Testability** — every AC turn into a concrete automated test (golden, validation negative, basedpyright)? AC-13's "names the offending field by its source location" — is that really testable?
4. **Consistency** — do the FRs contradict each other? Do the FRs contradict the Constitution (modulo the explicitly-proposed FR-14 amendment)? Does FR-12 (verbatim Python name → SV name) match existing `Const` behavior?
5. **Feasibility** — realistic in this codebase given Python 3.12+, basedpyright strict, golden-file testing, Jinja templates? Is the constitution amendment well-scoped and reversible?
6. **Constitution alignment** — Specifically check Constraint 5 (the one being amended). Is the proposed wording in FR-14 internally consistent with the rest of the constitution? Are §Coding Standards Python rules respected for the new DSL surface?
7. **Scope discipline** — does the spec stay within v1 scope (single new primitive, SV emission)? Is anything in scope that should be deferred? Is anything deferred that should be in scope?
8. **Risk assessment** — are R-1/R-2/R-3 real and meaningful? Any unaddressed risks?

## Output Format

### Issues
**BLOCKING / WARNING / NOTE**, citing FR/AC/NFR/Q identifier or section heading. 1-3 sentences each.

### Strengths
1-3 bullets.

### Verdict

End with **EXACTLY** one of:

```
VERDICT: APPROVE
```
or
```
VERDICT: REVISE
```

Approve only if zero BLOCKING issues remain.

## Important

- Be strict and blunt.
- The Constitution is the highest authority. Note that FR-14 explicitly proposes a Constitution amendment as part of this work — do NOT flag the amendment itself as BLOCKING (the user opted into it at workflow start). Do flag if FR-14's proposed wording is internally inconsistent or doesn't actually scope the restriction correctly.
- Do NOT classify optimization suggestions ("use X instead of Y", "extend the list") as BLOCKING unless the Constitution mandates the alternative. Per memory `feedback_minimal_change_preserve_scope.md` and prior workflows, those belong as Open Questions or WARNING.
- Do NOT propose implementation code; review the spec only.
