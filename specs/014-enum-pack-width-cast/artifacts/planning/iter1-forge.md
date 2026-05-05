# Implementation Plan — 014 Enum Pack Width Cast

**Spec:** `specs/014-enum-pack-width-cast/spec.md` (post-clarification)
**Branch:** `feature/014-enum-pack-width-cast`
**Status:** draft (planning iteration 1)

## Architecture Overview

This is a purely additive single-line correction confined to one file in the
SystemVerilog backend:

```
RepoIR ─► sv backend
              └── templates/_macros.j2   (Jinja: enum-pack body)
```

No Python source under `src/piketype/` is modified. No IR change, no DSL
change, no validation change, no view-builder change, no `pack_<base>`
change for `scalar_alias`/`flags`/`struct` kinds, no change to `unpack_<base>`
in any kind, no `_test_pkg` change, no C++ backend, no Python backend, no
runtime package change. The pipeline boundary
(Discovery → DSL → IR → Backends) is preserved: only the last hop
(IR → SV backend → template render) is touched, and only the literal
text in one Jinja branch.

Because the change is byte-for-byte deterministic and Constitution
principle 3 (Deterministic output) plus the user-memory directive
`feedback_byte_parity_per_commit.md` require per-commit byte parity, the
implementation stage edits the template **and** refreshes every affected
golden under `tests/goldens/gen/` in the **same single commit**. The
golden refresh uses the project-standard pattern documented in the
user-memory directive `project_golden_regen_pattern.md`: walk fixtures,
run `piketype gen` against each, replace the corresponding subtree under
`tests/goldens/gen/`.

## Components

### C-1. `synth_pack_fn` macro, enum branch (single-line edit)

**Location.** `src/piketype/backends/sv/templates/_macros.j2`, line 98
(inside the `synth_pack_fn` macro at lines 91-103).

**Responsibility.** Emit a width-correct return expression for the
enum branch of the synth pack function.

**Diff.**

```diff
 {% macro synth_pack_fn(view, pack_unpack) %}
   function automatic logic [LP_{{ view.upper_base }}_WIDTH-1:0] pack_{{ view.base }}({{ view.name }} a);
 {% if view.kind == "scalar_alias" %}
     return a;
 {% elif view.kind == "flags" %}
     return {{ '{' }}{% for n in view.field_names %}a.{{ n }}{% if not loop.last %}, {% endif %}{% endfor %}{{ '}' }};
 {% elif view.kind == "enum" %}
-    return logic'(a);
+    return LP_{{ view.upper_base }}_WIDTH'(a);
 {% elif view.kind == "struct" %}
     return {{ '{' }}{% for p in pack_unpack.pack_parts %}{{ p.expr }}{% if not loop.last %}, {% endif %}{% endfor %}{{ '}' }};
 {% endif %}
   endfunction
 {%- endmacro %}
```

**Why this exact form.** `LP_<UPPER>_WIDTH'(a)` is a SystemVerilog size
cast (LRM 6.24.1). The prefix is required to be a constant integral
expression; `LP_<UPPER>_WIDTH` is declared `localparam int` immediately
above the typedef and pack/unpack functions in every emitted package,
so the constraint is satisfied. The result has exactly that bit width,
matching the function's declared return type. No branching on
`view.is_one_bit` is needed: the same form works uniformly for 1-bit
enums (`LP_FLAG_WIDTH = 1`) and multi-bit enums (`LP_COLOR_WIDTH = 4`,
`LP_BIG_WIDTH = 64`, etc.).

The reuse of `view.upper_base` matches the same identifier already
used on the surrounding lines of the macro (function-return type and
function name parameter `view.base` derived from the same view).
No new view-builder field is introduced.

### C-2. Affected goldens (regenerated, not edited by hand)

**Locations** (5 files, 8 enum-pack-body lines):

1. `tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv`
   (4 lines: `pack_color`, `pack_cmd`, `pack_flag`, `pack_big`)
2. `tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_pkg.sv`
   (1 line)
3. `tests/goldens/gen/keyword_enum_value_while_passes/sv/alpha/piketype/types_pkg.sv`
   (1 line)
4. `tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/foo_pkg.sv`
   (1 line: `pack_cmd`)
5. `tests/goldens/gen/cross_module_type_refs_namespace_proj/sv/alpha/piketype/foo_pkg.sv`
   (1 line: `pack_cmd`)

**Responsibility.** Each golden's enum `pack_<base>` body must change from
`return logic'(a);` to `return LP_<UPPER>_WIDTH'(a);`. No other lines in
these files should change. Files in `_test_pkg.sv` form, runtime files,
and any golden for a fixture without an enum MUST NOT change.

## Data Model

No data-model change. No IR node, view dataclass, validation entry, or
DSL field is added, removed, or modified.

## API Design

No public API change. The synth-package surface emitted to consumers
(`{T_t, LP_<UPPER>_WIDTH, pack_<base>, unpack_<base>}` per
`view.py:780`) is unchanged in shape. Only the *body* of `pack_<base>`
for enum types is corrected; the function name, signature, and return
type are byte-identical to the pre-fix output.

Internal API (Jinja macro signatures, view-dataclass fields) is also
unchanged. `synth_pack_fn(view, pack_unpack)` keeps the same parameter
list; the enum branch already had access to `view.upper_base` via the
surrounding macro lines.

## Dependencies

No external dependencies are added. No new internal imports. The
implementation uses only existing project tooling:

- Jinja2 (existing runtime dep, version >= 3.1 per Constitution).
- `piketype.cli gen` (existing entry point, used to regenerate goldens).
- Standard library `unittest` (existing test runner).
- `basedpyright` strict mode (existing dev gate).

No version bump, no new pyproject.toml entry, no CI change.

## Implementation Strategy

A single feature commit. Three internal phases, all squashed into the
same commit so byte parity holds at every git head on the branch.

### Phase 1 — Edit the template

Apply the C-1 diff to
`src/piketype/backends/sv/templates/_macros.j2:98`. Verify the edit by
diffing against `master`:

```
git diff master -- src/piketype/backends/sv/templates/_macros.j2
```

The diff must show exactly one removed line and one added line at
line 98. No other line in the file changes.

### Phase 2 — Regenerate affected goldens

Run the project-standard regeneration loop (per
`project_golden_regen_pattern.md`):

```
for fixture in enum_basic struct_enum_member keyword_enum_value_while_passes \
               cross_module_type_refs cross_module_type_refs_namespace_proj; do
    rm -rf /tmp/pike-014/$fixture
    cp -R tests/fixtures/$fixture/project /tmp/pike-014/$fixture
    cd /tmp/pike-014/$fixture && piketype gen && cd -
    rm -rf tests/goldens/gen/$fixture/sv
    cp -R /tmp/pike-014/$fixture/gen/sv tests/goldens/gen/$fixture/
done
```

(Exact shell loop is illustrative; the implementation may use the
project's existing helper script if one exists, or a hand-rolled
sequence — the result is what matters: the 5 fixture subtrees are
overwritten with freshly generated output.)

After this phase:

- `git diff master -- tests/goldens/gen/` shows changes only in the 5
  enumerated files.
- Inside each changed file, the only diff lines are the
  `return logic'(a);` → `return LP_<UPPER>_WIDTH'(a);` replacements.
- No `_test_pkg.sv` file changes.
- No file under `tests/goldens/gen/` for a fixture without an enum
  changes.

### Phase 3 — Verify (pre-commit gates)

Run the verification battery from the project root:

1. `python -m unittest discover` (full test suite) — must pass.
2. `basedpyright src/piketype/` — must report zero errors.
3. `grep -r "return logic'(a);" tests/goldens/gen/` — must return zero
   matches.
4. `grep -r "return LP_[A-Z_]*_WIDTH'(a);" tests/goldens/gen/ | wc -l` —
   must return exactly `8`.
5. `git diff --stat master -- src/piketype/` — must show changes only
   to `src/piketype/backends/sv/templates/_macros.j2`.
6. `git diff --stat master -- tests/goldens/gen/` — must show changes
   only in the 5 enumerated files.
7. Re-run `piketype gen` against each fixture and `diff -r` the
   regenerated `gen/` against the committed `tests/goldens/gen/<case>/`
   subtree — must show no differences (idempotency / byte parity).
8. (Optional but recommended) Run the project's Verilator lint flow on
   each regenerated `_pkg.sv` and confirm zero new warnings vs. the
   pre-fix baseline.

If any gate fails, do NOT commit. Diagnose and fix; only commit when
all gates pass.

### Phase 4 — Single commit

Stage both the template edit and the regenerated goldens, then commit
with a Conventional Commits message under the `fix` type and the
appropriate scope (the bug is in the SV emitter; scope is `sv` per
the Constitution's Branching & Commits section):

```
git add src/piketype/backends/sv/templates/_macros.j2 \
        tests/goldens/gen/enum_basic \
        tests/goldens/gen/struct_enum_member \
        tests/goldens/gen/keyword_enum_value_while_passes \
        tests/goldens/gen/cross_module_type_refs \
        tests/goldens/gen/cross_module_type_refs_namespace_proj
git commit -m "fix(sv): use width-correct cast in enum pack body"
```

(Commit body: a short paragraph reproducing the spec's Overview and
referencing the spec ID `014-enum-pack-width-cast`.)

This single commit is the entire feature. No follow-up commits, no
amendments, no rebases beyond what the project's branching policy
otherwise requires.

## Risks and Mitigations

### R-1. Template edit accidentally changes nearby lines

**Risk.** Hand-editing line 98 risks accidentally reformatting nearby
whitespace, reordering branches, or introducing a typo in the cast
expression that produces invalid SV (e.g. `LP_<UPPER>_WIDTH(a)` without
the apostrophe — a function call, not a cast).

**Mitigation.** Use `Edit` with a tight `old_string` (the exact line
`    return logic'(a);` with leading spaces) and a tight `new_string`
(the exact line `    return LP_{{ view.upper_base }}_WIDTH'(a);`). After
edit, run a focused diff: `git diff src/piketype/backends/sv/templates/_macros.j2`
must show exactly +1 / -1 inside the `synth_pack_fn` macro and nothing
else. Phase 3 gate 5 catches a wider blast radius.

### R-2. Golden regeneration leaks scope

**Risk.** Regenerating a fixture that contains content unrelated to
enums (e.g. struct unpack bodies recently rewritten in spec 013, byte
helpers in `_test_pkg`, runtime packages) might introduce diffs in
those non-enum sections — for instance, if some upstream change since
the goldens were last regenerated has been silently absorbed.

**Mitigation.** Phase 3 gate 6 (`git diff --stat master -- tests/goldens/gen/`)
flags any unexpected file in the changeset. Phase 3 also runs the full
test suite; any pre-existing latent drift would surface as a test
failure before commit. If a golden file outside the 5-fixture list
shows a diff, stop and investigate — do not bundle unrelated changes.

### R-3. Verilator does not accept the size-cast form

**Risk.** Although `LP_<UPPER>_WIDTH'(a)` is standard SystemVerilog,
some Verilator versions historically had restrictions around the
left-hand side of the size cast.

**Mitigation.** Verilator 5.046 (project baseline) supports size casts
with `localparam int` prefixes. C-6 in `clarifications.md` already
verified this. Phase 3 gate 8 (the optional Verilator lint run) catches
any regression. If a future Verilator version regresses, the fallback
form `{LP_<UPPER>_WIDTH{1'b0}} | {(LP_<UPPER>_WIDTH-1)'(0), a[0]}`-style
expressions are NOT acceptable; the correct fallback would be bare
`return a;` (legal enum-to-base assignment). Plan does NOT pre-emptively
adopt the fallback; it is recorded only as a contingency.

### R-4. `LP_<UPPER>_WIDTH'(a)` is parsed as a function call by some
linters or older parsers

**Risk.** A naive parser might confuse the size-cast operator
`<int>'(...)` with a function call.

**Mitigation.** The single-quote operator is unambiguous in the
SystemVerilog grammar (LRM 11.8.2). Project's Verilator baseline
parses it correctly; commercial-tool compatibility is out of scope
per the spec's Out of Scope section. No mitigation beyond trusting the
LRM.

### R-5. Regression in `_test_pkg` helper-class behaviour

**Risk.** Although the spec confines the change to `synth_pack_fn`
enum branch, a misapplied edit (e.g. accidentally editing
`test_enum_helper` in the same file) could change `_test_pkg.sv`
goldens.

**Mitigation.** Phase 3 gate 6 plus a focused
`git diff --stat master -- tests/goldens/gen/**/*_test_pkg.sv` (must be
empty per spec AC-6). Caught before commit.

### R-6. Byte parity not held at intermediate states

**Risk.** Splitting the template edit and the golden refresh into
separate commits violates `feedback_byte_parity_per_commit.md` — every
commit on the branch must pass `piketype gen` byte-identical against
its committed goldens.

**Mitigation.** Phase 4 explicitly mandates a single commit. The plan
does not contain any "land template, refresh goldens later" pathway.

## Testing Strategy

**Primary mechanism: golden-file integration tests.** This is the
project's primary correctness mechanism per Constitution principle 4 and
the Testing section of the Constitution. The existing
`tests/test_gen_const_sv.py` (and any sibling test file in `tests/` that
exercises the affected fixtures) compares the generated `gen/` tree to
`tests/goldens/gen/<case>/` byte-for-byte; with the goldens refreshed
in the same commit as the template edit, these tests pass automatically.

**No new test file is added.** The bug under fix is data-correctness in
generated output — exactly the failure mode golden-file tests are
designed to catch. The fact that the original bug was *not* caught by
existing tests is a coverage gap (the `_test_pkg` helper class for
enums bypasses `pack_<enum>`), not a methodology gap; closing that gap
would mean refactoring the helper class to route through `pack_<enum>`,
which the spec explicitly puts out of scope (FR-2.3).

**Idempotency / byte parity.** Pre-commit gate 7 runs `piketype gen`
twice against each fixture and confirms the second run matches the
committed goldens. This is the same idempotency check the existing
test suite already runs in `tests/test_gen_*` files.

**Type checks.** `basedpyright src/piketype/` (gate 2) ensures no
Python regression. Since this feature does not edit Python, the gate
is a guard against accidental Python edits, not an active validation.

**Lint / Verilator.** Optional gate 8 runs the project's existing
Verilator lint flow against the regenerated `_pkg.sv` outputs and
diffs the warning set against the pre-fix baseline. NFR-5 requires no
new warnings of category WIDTH, UNSIGNED, SIGNED, CASTCONST, or
ASSIGNDLY.

**Verification of correctness by inspection.** AC-4 permits
hand-inspection plus golden diff as the evidence path that
`pack_<enum>` returns the correct bit pattern. Concretely: read each
regenerated `pack_<enum>` body, confirm the cast width matches the
return-type width, and confirm the same enum value typedef on lines
above. This is mechanical and unambiguous.

**Regression coverage going forward.** With the goldens fixed, any
future change that re-introduces `return logic'(a);` (or any
non-width-correct expression) into the enum-pack body fails Phase 3
gates 3 and 4 and the golden tests. The regression bar is high.
