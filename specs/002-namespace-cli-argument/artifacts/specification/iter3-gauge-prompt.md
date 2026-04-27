# Gauge Review: Specification 002 — `--namespace` CLI Argument (Iteration 3)

You are reviewing revision 3 of a feature specification for **typist**, a Python-based
hardware type code generator. Your role is **Gauge** — a strict, independent reviewer.

## Changes Since Iteration 2

1. **[BLOCKING] Reserved C++ identifiers** — FR-2 now rejects: (a) any segment
   containing `__` anywhere, (b) first segment starting with `_` (global scope),
   (c) `std` as first segment. AC-7, AC-8, AC-9 test each case.

2. **[WARNING] Runtime header scope** — FR-5 now explicitly states runtime C++
   headers are unaffected. FR-7 reworded to "all discovered module headers".

3. **[WARNING] Multi-module positive test** — AC-12 now requires the golden
   fixture to contain at least two modules with different path-derived namespaces.

## Your Task

Read the updated specification at `specs/002-namespace-cli-argument/spec.md` and the
project constitution at `.steel/constitution.md`, then re-review focusing on:

1. Whether ALL previously raised issues (iterations 1 and 2) are adequately resolved
2. Whether any new issues were introduced
3. Overall completeness, clarity, testability, consistency, feasibility

## Review Format

For each issue found, use this format:

```
### [SEVERITY] Issue Title
- **Requirement:** FR-X / NFR-X / AC-X / (general)
- **Issue:** Description of the problem
- **Suggestion:** How to fix it
```

Severity levels:
- **BLOCKING** — Must be fixed before implementation
- **WARNING** — Should be fixed, but not a showstopper
- **NOTE** — Minor suggestion or observation

## Final Verdict

End your review with exactly one of these lines:

```
VERDICT: APPROVE
```

or

```
VERDICT: REVISE
```

Use APPROVE only if there are zero BLOCKING issues.
