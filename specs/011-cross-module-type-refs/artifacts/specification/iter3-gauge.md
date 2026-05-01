# Gauge Review — Iteration 3

## Summary
Iter3 resolves the C++ namespace blocker, the loader restore blocker, the SV test-package import blocker, the duplicate-basename blocker, the flag-bit warning, and the emitter-wiring warning. It still leaves the template-first acceptance test incomplete: AC-23 is now more concrete, but it does not actually require detection of split string construction for generated imports/includes/from-imports, so iter2 B4 remains partially unresolved.

## Iter2 Issue Resolution

- ✓ resolved — **B1: C++ qualified name.** FR-12 now gives the correct default field type `::alpha::foo::byte_t_ct` and the correct namespace-override form `::N::foo::byte_t_ct` (`specs/011-cross-module-type-refs/spec.md:296-300`, `specs/011-cross-module-type-refs/spec.md:369`). That matches `_build_namespace_view`: `--namespace` becomes `{namespace}::{basename}`, while default generation filters out the literal `"piketype"` segment (`src/piketype/backends/cpp/view.py:241-245`). The current golden also proves the filtered form with `namespace alpha::types` (`tests/goldens/gen/struct_sv_basic/cpp/alpha/piketype/types_types.hpp:13`).

- ✓ resolved — **B2: loader restore contract.** FR-1 now snapshots original owned `sys.modules` entries, pre-cleans owned keys, loads without per-module repopping, then pops run instances and restores originals in `finally` (`specs/011-cross-module-type-refs/spec.md:140-151`). That fixes the pre-existing-key bug from iter2; the restore order is correct because the run instance is removed before the original module object is assigned back.

- ✓ resolved — **B3: SV test-package imports.** FR-10 now requires both cross-module synth imports and cross-module test imports in the test package (`specs/011-cross-module-type-refs/spec.md:270-276`). AC-4 specifies the exact order: same-module synth import, cross-module synth block, then cross-module test block (`specs/011-cross-module-type-refs/spec.md:367`). This covers the raw typedef helper field path in `_render_sv_helper_field_decl` (`src/piketype/backends/sv/view.py:370-376`) and the existing same-module synth import (`src/piketype/backends/sv/view.py:704`).

- ~ partial — **B4: template-first acceptance test.** AC-23 is no longer a useless grep: it names the test file, the backend files to parse, AST walking, string literals, f-string parts, and the grandfathered same-module import allowlist (`specs/011-cross-module-type-refs/spec.md:386`). But it still does not require reconstructing `JoinedStr` or `BinOp` string assembly, so code such as `"  import " + target + "_pkg::*;"`, `"#include " + quoted_path`, or `"from " + module_name + " import " + wrapper_name` can still be written in backend Python while evading the literal-substring rule. That violates FR-13 and NFR-7, which ban Python-side generated-line construction (`specs/011-cross-module-type-refs/spec.md:303-307`, `specs/011-cross-module-type-refs/spec.md:360`) and the constitution's template-first rule (`.steel/constitution.md:49-51`). This is still a blocking testability gap.

- ✓ resolved — **B5: duplicate package basenames.** FR-9a makes duplicate-basename validation unconditional for every `piketype gen` invocation (`specs/011-cross-module-type-refs/spec.md:261-264`), fixing the previous basename-deduplication hole. The current code only runs that check under `--namespace` (`src/piketype/commands/gen.py:31-32`), and the existing checker finds duplicate stems across module paths (`src/piketype/validate/namespace.py:99-119`). I checked the current fixture projects; none contain duplicate piketype module stems within a single fixture, so this stricter rule should not break existing fixtures.

- ✓ resolved — **W1: flag-bit literal collision wording.** FR-8 now scopes wildcard literal collision to enum literals and explicitly excludes flag-bit names (`specs/011-cross-module-type-refs/spec.md:238-240`). AC-14 also excludes flag bits (`specs/011-cross-module-type-refs/spec.md:377`). That matches the templates: flag bits are struct fields (`src/piketype/backends/sv/templates/_macros.j2:64-76`), while enum literals are package-level enum members (`src/piketype/backends/sv/templates/_macros.j2:80-84`).

- ✓ resolved — **W2: emitter wiring.** FR-7 now explicitly requires each emitter to build the repo-wide type index once and pass it to every module-view build call (`specs/011-cross-module-type-refs/spec.md:224-229`). That removes the ambiguity against the current emitter calls, which pass only `module` / `namespace` today (`src/piketype/backends/sv/emitter.py:37-49`, `src/piketype/backends/py/emitter.py:40-44`, `src/piketype/backends/cpp/emitter.py:33-35`).

## New Issues

### BLOCKING
None beyond the carried-forward partial B4 above.

### WARNING
- **W3 — FR-12 still has a stale namespace sentence.** The FR-12 introduction says `_build_namespace_view` places the default generated module under `alpha::piketype::foo` (`specs/011-cross-module-type-refs/spec.md:290`), but the actual source and the corrected bullets say default namespaces filter out `"piketype"` (`src/piketype/backends/cpp/view.py:241-245`, `specs/011-cross-module-type-refs/spec.md:296-300`). AC-6 is correct, so this is not blocking, but the stale sentence should be fixed.

- **W4 — FR-9a's "same wording as today" claim is false.** FR-9a says the duplicate-basename error message is `"duplicate piketype module basename {basename}: {path1}, {path2}"` and calls it the same wording as today (`specs/011-cross-module-type-refs/spec.md:261-262`). Current code raises `"--namespace requires unique module basenames, but duplicates were found:\n  '{stem}': ..."` (`src/piketype/validate/namespace.py:113-119`). The explicit new message is clear, and current tests assert only fragments (`tests/test_namespace_validation.py:176-182`), so this is only a wording correction.

- **W5 — Local-vs-imported enum literal collision lacks an exact error message.** FR-8 gives a concrete message for imported-vs-imported enum literal collisions, then says the same rule applies to local-vs-imported collisions (`specs/011-cross-module-type-refs/spec.md:238`). AC-14 requires the local-vs-imported case too (`specs/011-cross-module-type-refs/spec.md:377`). The rejection behavior is clear, but the exact local-vs-imported diagnostic is not.

### NOTE
- The revised FR-1 owned-key set includes every prefix of each discovered module name (`specs/011-cross-module-type-refs/spec.md:140-147`), which covers implicit namespace packages created during imports.
- The stricter duplicate-basename rule is compatible with the current fixture set based on a per-fixture scan of `tests/fixtures/*/project`.

## Strengths
- The snapshot-and-restore loader contract is now implementable and exception-safe.
- SV test-package import ordering is now explicit enough to avoid relying on transitive package imports.
- The corrected C++ namespace rule now matches both source and goldens, including the `--namespace` case.

VERDICT: REVISE
