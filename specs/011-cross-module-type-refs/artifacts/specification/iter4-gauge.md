# Gauge Review — Iteration 4

## Summary
Iter4 fixes the three carried warnings: the stale C++ namespace sentence is gone, FR-9a now states the current duplicate-basename message before defining the new one, and FR-8 now gives both enum-literal collision diagnostics. B4 is still only partially resolved because AC-23's `.join` rule does not formally catch the exact `" ".join(["import", basename, "_pkg::*"])` candidate it claims to catch.

## Carried-Forward Issue Resolution

- ~ partial — **B4: template-first acceptance test.** AC-23 now correctly covers f-string prefixes, `+` concatenation chains, `.format(...)`, and the single allowlisted existing same-module synth import (`specs/011-cross-module-type-refs/spec.md:388-396`). The allowlist matches the current source line exactly: `src/piketype/backends/sv/view.py:704` is `f"  import {module.ref.basename}_pkg::*;"` (`src/piketype/backends/sv/view.py:701-705`). However, the `.join` bullet is internally inconsistent: it says the test flags `.join` "on a string Constant that begins with" `import`, `#include`, or `from`, then claims this captures `" ".join(["import", basename, "_pkg::*"])` (`specs/011-cross-module-type-refs/spec.md:393`). In that AST, the receiver constant is `" "`, not a generated-output prefix, so a direct implementation of the written rule does not flag the candidate. That leaves a split string-construction escape hatch against FR-13/NFR-7 (`specs/011-cross-module-type-refs/spec.md:305-309`, `specs/011-cross-module-type-refs/spec.md:361-362`) and the constitution's template-first rule (`.steel/constitution.md:49-51`). The `%` formatting bullet also needs clearer AST wording: Python parses `"import %s_pkg::*;" % target` as `ast.BinOp(op=Mod)`, not as an `ast.Call` (`specs/011-cross-module-type-refs/spec.md:394`). This is secondary to the `.join` miss, but it should be made explicit.

- ✓ resolved — **W3: stale FR-12 namespace sentence.** FR-12 now says `_build_namespace_view` filters the literal `"piketype"` segment and gives `alpha::foo` or `{user_namespace}::foo`, not the stale `alpha::piketype::foo` form (`specs/011-cross-module-type-refs/spec.md:290-300`). That matches the current source: `_build_namespace_view` filters `p != "piketype"` in the default case and uses `{namespace}::{basename}` under `--namespace` (`src/piketype/backends/cpp/view.py:241-245`).

- ✓ resolved — **W4: FR-9a duplicate-basename wording.** FR-9a no longer claims the new message is the same wording as today. It quotes the current source message, then defines the updated message that drops the `--namespace` precondition (`specs/011-cross-module-type-refs/spec.md:261-265`). The quoted current message matches `src/piketype/validate/namespace.py:117-119`.

- ✓ resolved — **W5: enum literal collision diagnostics.** FR-8 now states both imported-vs-imported and local-vs-imported enum literal collision messages explicitly (`specs/011-cross-module-type-refs/spec.md:238-240`). The distinction is grounded in the SV templates: flag bits are struct fields, while enum literals are package-level enum members (`src/piketype/backends/sv/templates/_macros.j2:64-84`).

## New Issues

### BLOCKING
None beyond the carried-forward partial B4 above.

### WARNING
- **AC-23 `%` formatting AST wording is imprecise.** The spec intends to catch `"import %s_pkg::*;" % target`, but `%` string formatting is represented as `ast.BinOp(op=Mod)`, not `ast.Call`. Since AC-23 is an implementation-facing acceptance test, it should name the AST node shape directly (`specs/011-cross-module-type-refs/spec.md:394`).

### NOTE
- I do not see a false-positive blocker from AC-23's `.join` or `%` rules as written. Current legitimate `.join` uses in the inspected backend files use separators like `"_"`, `"::"`, or `", "` and do not start with generated-output prefixes (`src/piketype/backends/cpp/view.py:237`, `src/piketype/backends/cpp/view.py:245`, `src/piketype/backends/sv/view.py:610-611`, `src/piketype/backends/sv/view.py:636-637`). Current `%` uses are arithmetic modulo or SV display-format fragments, not generated import/include/from-import construction (`src/piketype/backends/py/view.py:245`, `src/piketype/backends/py/view.py:404`, `src/piketype/backends/sv/view.py:539`, `src/piketype/backends/sv/view.py:594-597`).
- The changelog accurately lists the intended iter4 edits (`specs/011-cross-module-type-refs/spec.md:419-422`), but AC-23's `.join` formal rule still does not implement the stated intent.

## Strengths
- FR-8's collision rules are now complete enough for direct negative tests.
- FR-9a now cleanly separates current behavior from required behavior.
- The f-string and `+` concatenation portions of AC-23 are materially stronger than iter3 and cover most likely inline-generation regressions.

VERDICT: REVISE
