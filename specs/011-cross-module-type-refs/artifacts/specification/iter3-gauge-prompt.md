# Gauge Review — Specification Stage, Iteration 3

You are the **Gauge** in a Forge-Gauge dual-LLM specification loop. Iter2 issued REVISE with 5 BLOCKING + 2 WARNING items. The forge has revised the spec in iter3.

## What changed since iter2

Per the spec's Changelog (bottom of `specs/011-cross-module-type-refs/spec.md`), the changes since iter2 are:

- FR-1: rewrote restore semantics to snapshot-and-restore.
- FR-7: added explicit emitter-wiring sub-section.
- FR-8: removed flag-bit names; only enum literals.
- FR-9: dedupe by `python_module_name` not basename.
- New FR-9a: unconditional duplicate-basename validation.
- FR-10: test packages emit BOTH cross-module synth and cross-module test imports.
- FR-12: corrected C++ qualified type to `::alpha::foo::byte_t_ct`.
- AC-4, AC-6, AC-14, AC-23 updated.

## What to do

1. Re-read `.steel/constitution.md`.
2. Read iter3 spec at `specs/011-cross-module-type-refs/spec.md`.
3. Read iter2 review `specs/011-cross-module-type-refs/artifacts/specification/iter2-gauge.md` and check whether each iter2 BLOCKING (B1-B5) and WARNING (W1, W2) is actually resolved in iter3.
4. Spot-check source for any new claims iter3 makes:
   - C++ namespace structure: `src/piketype/backends/cpp/view.py:241-253`.
   - Existing C++ goldens to confirm `alpha::foo` style: e.g., `tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:13`.
   - SV view existing inline import: `src/piketype/backends/sv/view.py:704`.
   - Duplicate-basename validation: `src/piketype/validate/namespace.py`, `src/piketype/commands/gen.py:31-32`.
5. Look for new issues introduced by iter3.

## What to evaluate (specific to iter3)

- **B1 resolution.** AC-6 and FR-12 now say `::alpha::foo::byte_t_ct`. Verify against the goldens this matches existing namespace policy. Confirm the wording handles the `--namespace=N` case correctly: should it be `::N::foo::byte_t_ct` (target's basename appended to user namespace) or `::N::piketype::foo::byte_t_ct`? Read `_build_namespace_view`.
- **B2 resolution.** FR-1 now snapshots originals and restores them. Verify the restore order (pop run instance → assign original) doesn't have a race / missed-key edge case.
- **B3 resolution.** FR-10 emits both `_pkg::*` and `_test_pkg::*` from cross-module targets in the test package. Verify ordering in AC-4 is unambiguous.
- **B4 resolution.** AC-23 is now an AST-walk unit test. Is the description detailed enough that an implementer would write a working test, or is it still hand-wavy?
- **B5 resolution.** FR-9a makes basename uniqueness unconditional. Will this break any existing fixture? Check `tests/fixtures/` for same-basename modules across different paths.
- **W1 resolution.** FR-8 third sub-rule and AC-14 dropped flag-bit names. Confirm the wording is consistent.
- **W2 resolution.** FR-7 emitter-wiring section explicit?
- **New issues.** Did iter3 introduce any inconsistency or testability gap?

## Output format

```
# Gauge Review — Iteration 3

## Summary
(2-3 sentences)

## Iter2 Issue Resolution

For each iter2 BLOCKING and WARNING (B1-B5, W1, W2):
- ✓ resolved
- ✗ unresolved (explain)
- ~ partial (explain)

## New Issues

### BLOCKING
...

### WARNING
...

### NOTE
...

## Strengths
...

VERDICT: APPROVE
```
or `VERDICT: REVISE`.

If iter2's B1-B5 are all resolved AND no new BLOCKING emerges, APPROVE.

Save to `specs/011-cross-module-type-refs/artifacts/specification/iter3-gauge.md`.

Be strict. Cite line numbers. Verify against source.
