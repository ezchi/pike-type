# Gauge Review — Specification Stage, Iteration 5 (Final)

You are the **Gauge** in a Forge-Gauge dual-LLM specification loop. This is iteration 5 — the maximum per `.steel/config.json` (`maxIterations: 5`). The Forge has revised the spec to address iter4's last carried partial item (B4 — AC-23 `.join` and `%` rules).

## What changed since iter4

- AC-23: `.join` rule rewritten to reduce join to a static skeleton and flag if the skeleton starts with a generated-output prefix.
- AC-23: `%` rule corrected from `ast.Call` to `ast.BinOp(op=Mod)`.

These are the only changes since iter4.

## What to do

1. Re-read iter4 review at `specs/011-cross-module-type-refs/artifacts/specification/iter4-gauge.md`.
2. Read iter5 spec at `specs/011-cross-module-type-refs/spec.md`.
3. Verify the two AC-23 fixes resolve B4 fully.
4. Confirm no regression introduced by these edits.

## What to evaluate (specific to iter5)

For each candidate inline-construction example, trace through the iter5 AC-23 rule and confirm whether the rule flags it:

- `f"  import {target}_pkg::*;"` — JoinedStr prefix rule.
- `"import " + target + "_pkg::*;"` — BinOp Add chain rule.
- `"import {}_pkg::*;".format(target)` — `.format` rule.
- `" ".join(["import", basename, "_pkg::*"])` — `.join` rule (this is the iter4 escape hatch; verify the iter5 rewrite catches it).
- `"import %s_pkg::*;" % target` — `BinOp(op=Mod)` rule.
- `"#include \"" + path + "\""` — BinOp Add.
- `f"from {m}_types import {c}"` — JoinedStr prefix.
- The existing `view.py:704` line — allowlisted.

Confirm:

- The `.join` rule correctly produces the skeleton `"import <DYN> _pkg::*"` (or similar) when reduced and that this skeleton starts with `"import "`. Walk through the reduction and confirm.
- The `%` rule's AST shape `ast.BinOp(op=Mod, left=Constant(value=str))` is exactly what Python produces for `"...%s..." % x`.

## Output format

```
# Gauge Review — Iteration 5

## Summary
(2 sentences)

## Carried-Forward Issue Resolution

For each item carried from iter4 (B4 partial; W3, W4, W5 already resolved):
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

If B4 is fully resolved AND no new BLOCKING emerges, APPROVE. WARNINGs and NOTEs alone do not require revision.

This is the last forge-gauge iteration in the budget; the verdict here determines whether the spec advances to the human approval gate.

Save the review to `specs/011-cross-module-type-refs/artifacts/specification/iter5-gauge.md`.

Be strict. Cite line numbers. Verify against source.
