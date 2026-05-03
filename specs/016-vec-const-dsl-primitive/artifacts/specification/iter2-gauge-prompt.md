# Gauge Review Prompt — Specification, Iteration 2

You are the **Gauge**. The Forge has revised in response to your iter1 review.

## Inputs

- **Updated spec:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/spec.md`
- **Your iter1 review:** `/Users/ezchi/Projects/pike-type/specs/016-vec-const-dsl-primitive/artifacts/specification/iter1-gauge.md`
- **Constitution:** `/Users/ezchi/Projects/pike-type/.steel/constitution.md`

## What changed in iter2

The Forge addressed your iter1 issues:

1. **BLOCKING (Q-4 / Principle 1)** → Resolved by adding **FR-16** (C++ no-op for v1), **FR-17** (Python no-op for v1), **FR-18** (manifest gets a new `vec_constants` array). OOS-9 rewritten to declare cross-language emission as deferred, not undefined. Q-4 and Q-5 removed from Open Questions.
2. **WARNING (FR-7 message format)** → Adopted. FR-7 now mandates the three substrings (offending value, declared width, formula `2**N - 1`) in the validation error message, with an example phrasing.
3. **NOTE (FR-5 width cap)** → Acknowledged. The 64-bit cap stays for v1; Q-4 (renumbered, was Q-3) keeps the lifting discussion alive for the clarification stage and now explicitly cites your IPv6 / hash-constant examples.

A `## Changelog` section was added at the bottom recording the changes.

## Your task

Re-review focused on the iter2 delta:

1. Confirm BLOCKING is resolved: is the C++/Python no-op policy now an *explicit, declared property* of v1 (not an oversight)? Is FR-16 / FR-17 / FR-18 internally consistent?
2. Confirm WARNING is adopted: does FR-7 now mandate enough specificity that two implementers will produce equivalent error text?
3. Confirm Q-4/Q-5 truly removed and OOS-9 rewritten.
4. Look for NEW issues introduced by the targeted edits (especially in FR-18's manifest field list — is it complete? sufficient?).
5. Confirm no unrelated sections were modified.

## Output Format

### Issues
**BLOCKING / WARNING / NOTE**, terse.

### Carry-Over from Iter 1
For each iter1 issue: RESOLVED / STILL BLOCKING / DOWNGRADED / WITHDRAWN.

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
- Do NOT re-raise the resolved BLOCKING / WARNING items as still-open unless the Forge's resolution is genuinely insufficient.
- Do NOT promote NOTE-level items to BLOCKING in iter2.
- Per project memory `feedback_minimal_change_preserve_scope.md`: do NOT push to add C++/Python emission as BLOCKING — the user explicitly asked for SV-only and FR-16/17 honor that.
- Do not propose implementation code.
