# Gauge Review — Specification Stage, Iteration 2

You are the **Gauge** in a Forge-Gauge dual-LLM specification loop. Your job is to critically review the **second iteration** of a specification document for the pike-type project.

## What changed since iter1

Iter1 review (`specs/011-cross-module-type-refs/artifacts/specification/iter1-gauge.md`) issued **VERDICT: REVISE** with 9 BLOCKING and 3 WARNING items. The forge has revised the spec in iter2. The major changes are documented in the spec's Changelog section at the bottom of `specs/011-cross-module-type-refs/spec.md`, but in summary:

- Q1 resolved → FR-1: per-run scoped `sys.modules` snapshot/cleanup.
- Q2 resolved → FR-9: wildcard SV import for synth packages.
- Q3 resolved → FR-12: fully-qualified C++ field type.
- New FR-7: repo-wide type index across all backend view builders.
- New FR-8: cross-module name-collision validation.
- New FR-13 + NFR-7: template-first emission as a hard requirement.
- New FR-10: test-package transitive import for cross-module helper classes (separated from synth FR-9).
- FR-4 sort key broadened to `(module, kind)` full tuple.
- FR-16 test plan: replaced infeasible unknown-type integration fixture with a `RepoIR` unit test.
- New "Implementation Staging Note" added to satisfy byte-parity-per-commit.
- Overview wording corrected re: discovery order.

## What to do

1. **Re-read the project constitution** at `.steel/constitution.md`.
2. **Read iter2 spec** at `specs/011-cross-module-type-refs/spec.md`.
3. **Read iter1 review** at `specs/011-cross-module-type-refs/artifacts/specification/iter1-gauge.md` — for each iter1 BLOCKING and WARNING item, evaluate whether iter2 actually resolves it.
4. **Spot-check the source code** for any new claims iter2 makes (e.g., that helper classes live in `_test_pkg`, the C++ namespace structure, Jinja template locations).
5. **Look for new issues introduced by iter2.**

## What to evaluate

Same axes as iter1:

- **Completeness:** Are all four type kinds and all three backends now coherently covered? Is the staging plan realistic?
- **Clarity:** Is each FR specific enough that two implementers would write the same code?
- **Testability:** Does each AC have an objective check?
- **Consistency:** Internal contradictions? Constitution alignment?
- **Feasibility:** FR-1 (scoped sys.modules), FR-7 (repo-wide type index plumbed through three backends), FR-8 (collision detection) — are they realistically implementable in their stated commits?

Specifically scrutinize:

1. **FR-1 (scoped sys.modules).** Does it correctly handle the case where a piketype module's parent package (e.g., `alpha.piketype` itself) is created by the import system as an empty namespace package? Does the cleanup rule cover those parent entries?
2. **FR-7 (repo-wide type index).** Is the proposed plumbing through three backends actually plumbed in iter2's text, or is it described abstractly without concrete signature changes?
3. **FR-8 (name collisions).** Are the three sub-rules genuinely necessary given FR-9's wildcard, or is one of them redundant? Is the wildcard literal-collision rule (third sub-rule) practical to implement given current `_validate_enum_literal_collision` is module-local?
4. **FR-12 (C++ qualified type).** The spec asserts `::alpha::piketype::foo::byte_t_ct`. Verify by reading `src/piketype/backends/cpp/view.py:241-253` that the namespace really is `alpha::piketype::foo` (not e.g. `piketype::foo` or just `foo`). Check the `namespace_parts` filtering at line 245 (`p for p in module.ref.namespace_parts if p != "piketype"`).
5. **Staging plan.** Commit C asserts no existing-golden diff. Verify this is plausible — does adding `dependencies` entries to the manifest break any existing manifest golden?
6. **AC-23 (grep check for inline imports).** Is this AC well-formed? It greps for `import {pkg}_pkg` in three view files. Will the grep produce false positives from existing literal strings (e.g., the existing same-module test-package import at `view.py:704`)?

## Output format

```
# Gauge Review — Iteration 2

## Summary
(2-3 sentences)

## Iter1 Issue Resolution

For each iter1 BLOCKING and WARNING, mark:
- ✓ resolved
- ✗ unresolved (explain)
- ~ partially resolved (explain what's missing)

## New Issues

### BLOCKING
- (issue, with FR/AC reference and suggested fix)
...

### WARNING
- ...

### NOTE
- ...

## Strengths
- ...

VERDICT: APPROVE
```
or `VERDICT: REVISE`.

If iter1's blockers are all resolved AND no new blocker emerges, APPROVE. Otherwise REVISE.

After producing the review, save it to `specs/011-cross-module-type-refs/artifacts/specification/iter2-gauge.md`.

Be strict. Cite line numbers. Verify by reading source — do not take iter2's claims at face value.
