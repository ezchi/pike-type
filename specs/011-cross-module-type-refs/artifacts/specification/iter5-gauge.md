# Gauge Review — Iteration 5

## Summary
Iter5 resolves the last carried B4 gap: AC-23 now catches the split `.join` construction and correctly specifies `%` formatting as `ast.BinOp(op=Mod)`. The scoped edits do not introduce a new blocking issue; the spec can advance to the human approval gate.

## Carried-Forward Issue Resolution

- ✓ resolved — **B4 partial: AC-23 `.join` and `%` rules.** Iter4's remaining objection was precise: the old `.join` rule inspected the receiver string, so `" ".join(["import", basename, "_pkg::*"])` escaped because the receiver was `" "`, not an import/include/from prefix (`specs/011-cross-module-type-refs/artifacts/specification/iter4-gauge.md:8`). Iter5 rewrites the rule to inspect `ast.Call(func=Attribute(attr="join"))`, require a literal `List`/`Tuple` first argument, reduce each element to either its constant string or `"<DYN>"`, join those skeleton elements with the receiver string, and flag the resulting skeleton if it starts with a generated-output prefix (`specs/011-cross-module-type-refs/spec.md:395-399`). For `" ".join(["import", basename, "_pkg::*"])`, Python parses the first argument as `List([Constant("import"), Name("basename"), Constant("_pkg::*")])`; reduction produces `["import", "<DYN>", "_pkg::*"]`, receiver `" "` joins it into `"import <DYN> _pkg::*"`, and that starts with `"import "`, so the rule now flags the iter4 escape hatch.
- ✓ resolved — **B4 partial: `%` formatting AST shape.** Iter5 replaces the old imprecise call wording with `ast.BinOp(op=Mod, left=Constant(value=str))`, which is exactly how Python parses `"import %s_pkg::*;" % target` (`specs/011-cross-module-type-refs/spec.md:400`). The rule also scopes detection to left-hand constant strings that begin with `import `, `#include `, or `from `, matching the generated-output token model in AC-23 (`specs/011-cross-module-type-refs/spec.md:388-400`).
- ✓ remains resolved — **W3, W4, W5.** Iter5 did not edit the FR-12 namespace rule, FR-9a duplicate-basename wording, or FR-8 enum-literal collision diagnostics that iter4 already marked resolved (`specs/011-cross-module-type-refs/artifacts/specification/iter4-gauge.md:10-14`). No regression is visible in the scoped AC-23/changelog diff.

## New Issues

### BLOCKING
None.

### WARNING
None.

### NOTE
None.

## Strengths

- AC-23 now gives implementable AST shapes for every candidate inline construction instead of mixing intent with ambiguous prose (`specs/011-cross-module-type-refs/spec.md:390-400`).
- The specified checks flag the required examples: `f"  import {target}_pkg::*;"` via `JoinedStr` static prefix (`specs/011-cross-module-type-refs/spec.md:391`); `"import " + target + "_pkg::*;"` and `"#include \"" + path + "\""` via `BinOp(op=Add)` flattening (`specs/011-cross-module-type-refs/spec.md:392`); `"import {}_pkg::*;".format(target)` via `.format` receiver inspection (`specs/011-cross-module-type-refs/spec.md:393`); `" ".join(["import", basename, "_pkg::*"])` via skeleton reduction (`specs/011-cross-module-type-refs/spec.md:395-399`); `"import %s_pkg::*;" % target` via `BinOp(op=Mod)` (`specs/011-cross-module-type-refs/spec.md:400`); and `f"from {m}_types import {c}"` via `JoinedStr` static prefix (`specs/011-cross-module-type-refs/spec.md:391`).
- The existing same-module synth import is still explicitly allowlisted by file and line, and the source still matches that line: `synth_package_import=f"  import {module.ref.basename}_pkg::*;"` at `src/piketype/backends/sv/view.py:704` (`specs/011-cross-module-type-refs/spec.md:402`, `src/piketype/backends/sv/view.py:701-704`).

VERDICT: APPROVE
