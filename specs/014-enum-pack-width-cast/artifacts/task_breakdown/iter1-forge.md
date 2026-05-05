# Tasks — 014 Enum Pack Width Cast

**Spec:** `specs/014-enum-pack-width-cast/spec.md`
**Plan:** `specs/014-enum-pack-width-cast/plan.md`
**Branch:** `feature/014-enum-pack-width-cast`

## Plan corrections required

The plan's Phase 2 illustrative shell loop iterates the same name for both
the fixture directory and the golden directory. This is correct for 4 of
the 5 affected goldens, but **wrong** for
`cross_module_type_refs_namespace_proj`: there is no fixture directory
with that name. Confirmed by:

```
$ ls -d tests/fixtures/cross_module_type_refs_namespace_proj
ls: tests/fixtures/cross_module_type_refs_namespace_proj: No such file or directory
```

The `cross_module_type_refs_namespace_proj` golden is generated from the
`cross_module_type_refs` **fixture** with the additional CLI flag
`--namespace=proj::lib` (per `tests/test_gen_cross_module.py:95-107`).
This is the "namespace-flag golden orphan" pattern documented in
`project_golden_regen_pattern.md`.

The tasks below use the per-fixture invocation table that reflects the
actual repo state. The plan should be amended in the implementation
retrospect to add the `--namespace=proj::lib` invocation note.

Additionally: the plan does not state which `<cli_file>` argument to
pass to `piketype.cli gen` for each fixture. The values, derived from
`tests/test_*.py:_run_piketype` / `_gen_fixture` helpers, are listed in
T2 below.

## Per-fixture regeneration invocation table

| Golden directory                                  | Fixture source                | cli_file (relative to repo_dir)   | Extra CLI args         |
|---------------------------------------------------|-------------------------------|-----------------------------------|------------------------|
| `tests/goldens/gen/enum_basic`                    | `enum_basic`                  | `foo/piketype/defs.py`            | (none)                 |
| `tests/goldens/gen/struct_enum_member`            | `struct_enum_member`          | `alpha/piketype/types.py`         | (none)                 |
| `tests/goldens/gen/keyword_enum_value_while_passes` | `keyword_enum_value_while_passes` | `alpha/piketype/types.py`     | (none)                 |
| `tests/goldens/gen/cross_module_type_refs`        | `cross_module_type_refs`      | `alpha/piketype/bar.py`           | (none)                 |
| `tests/goldens/gen/cross_module_type_refs_namespace_proj` | `cross_module_type_refs` | `alpha/piketype/bar.py`           | `--namespace=proj::lib` |

The standard invocation per fixture (mirrors
`tests/test_gen_cross_module.py:_run_piketype`):

```
PYTHONPATH=<project_root>/src \
  python3 -m piketype.cli gen [extra_args] <cli_file>
# run with cwd=<temp copy of fixture project>
```

After each invocation, replace the corresponding subtree under
`tests/goldens/gen/<golden_dir>/sv/` (and any other generated subdirs)
with the freshly generated `<repo_dir>/gen/` output.

---

## Tasks

### T1. Edit `synth_pack_fn` enum branch in `_macros.j2`

**Description.** Apply the single-line correction to the enum branch
of the `synth_pack_fn` Jinja macro. Replace `return logic'(a);` with
`return LP_{{ view.upper_base }}_WIDTH'(a);` at line 98 of the template.

**Files modified.**
- `src/piketype/backends/sv/templates/_macros.j2` (1 line: -1 / +1)

**Files NOT touched** (regression guard).
- Any other line in `_macros.j2` (other macros, scalar-alias / flags /
  struct branches of `synth_pack_fn`, `synth_unpack_fn`, all
  `test_*_helper` macros).
- All Python sources under `src/piketype/`.

**Dependencies.** None (T1 is the entry point).

**Verification.**
- `git diff master -- src/piketype/backends/sv/templates/_macros.j2`
  shows exactly one removed line (`    return logic'(a);`) and one
  added line (`    return LP_{{ view.upper_base }}_WIDTH'(a);`).
- `git diff --stat master -- src/piketype/` lists only this one file.
- Whitespace and indentation of the new line match the surrounding
  template (4-space indent inside the macro body).

### T2. Regenerate all 5 affected goldens

**Description.** For each row in the per-fixture regeneration
invocation table above, run `piketype.cli gen` against a temp copy of
the fixture and overwrite the corresponding golden subtree. Five
fixtures, but six runs *if* you choose to regenerate
`cross_module_type_refs_namespace_proj` separately (recommended,
because its CLI args differ).

**Files modified.**
- `tests/goldens/gen/enum_basic/sv/foo/piketype/defs_pkg.sv` (4
  pack-body lines)
- `tests/goldens/gen/struct_enum_member/sv/alpha/piketype/types_pkg.sv`
  (1 pack-body line)
- `tests/goldens/gen/keyword_enum_value_while_passes/sv/alpha/piketype/types_pkg.sv`
  (1 pack-body line)
- `tests/goldens/gen/cross_module_type_refs/sv/alpha/piketype/foo_pkg.sv`
  (1 pack-body line)
- `tests/goldens/gen/cross_module_type_refs_namespace_proj/sv/alpha/piketype/foo_pkg.sv`
  (1 pack-body line)

**Files NOT touched** (regression guard).
- Any `_test_pkg.sv` under any fixture (per spec AC-6).
- Any runtime golden (`piketype_runtime_pkg.sv` and equivalents).
- Any C++ or Python golden (`*.hpp`, `*_types.py`, `__init__.py`).
- Any golden for a fixture without an enum.

**Dependencies.** Depends on T1 — without the template edit, the
regeneration produces the original buggy output and the diff is empty.

**Verification.**
- `grep -r "return logic'(a);" tests/goldens/gen/` returns zero
  matches (per spec AC-1).
- `grep -r "return LP_[A-Z_]*_WIDTH'(a);" tests/goldens/gen/ | wc -l`
  returns exactly `8` (per spec AC-2).
- `git diff --stat master -- tests/goldens/gen/` lists only the 5
  enumerated `_pkg.sv` files. No `_test_pkg.sv` file appears.
- `git diff --stat master -- tests/goldens/gen/**/*_test_pkg.sv` is
  empty (per spec AC-6).

### T3. Run pre-commit verification gates

**Description.** Run the full verification battery from the project
root before staging anything for commit. Every gate must pass; if any
gate fails, do NOT commit — diagnose and fix first.

**Gates.**
1. **Test suite.** `python3 -m unittest discover -s tests`
   (or whatever the project's standard invocation is — match what is
   already used in CI). Must report zero failures and zero errors.
   The byte-equal-trees comparison inside the affected test files
   (`test_gen_enum.py`, `test_struct_enum_member.py`,
   `test_validate_keywords.py` for keyword fixtures,
   `test_gen_cross_module.py`) is the primary correctness check that
   the regenerated goldens match what the codegen now produces.
2. **Static type check.** `basedpyright src/piketype/` reports zero
   errors. (Strict mode per Constitution Coding Standards.)
3. **Bug-line absence.**
   `grep -rn "return logic'(a);" tests/goldens/gen/` returns no
   matches. (AC-1.)
4. **Fix-line presence count.**
   `grep -r "return LP_[A-Z_]*_WIDTH'(a);" tests/goldens/gen/ | wc -l`
   returns exactly `8`. (AC-2.)
5. **Python diff scope.**
   `git diff --stat master -- src/piketype/` lists exactly one file:
   `src/piketype/backends/sv/templates/_macros.j2`. (AC-5.)
6. **Golden diff scope.**
   `git diff --stat master -- tests/goldens/gen/` lists exactly the
   5 `_pkg.sv` files enumerated in T2. No `_test_pkg.sv`, no runtime
   golden, no fixture-without-enum golden. (AC-6, AC-7.)
7. **Idempotency / byte parity.** Re-run T2 against a fresh temp
   directory for at least one fixture (recommended:
   `cross_module_type_refs_namespace_proj` because it exercises the
   `--namespace` flag path) and `diff -r` the regenerated `gen/`
   tree against the just-staged golden subtree. Output must show no
   differences. (NFR-2 / `feedback_byte_parity_per_commit.md`.)
8. **(Optional, recommended) Verilator lint.** Run the project's
   existing Verilator lint flow (under `src/piketype/backends/lint/`)
   on each regenerated `_pkg.sv` and confirm no new warnings of
   category WIDTH, UNSIGNED, SIGNED, CASTCONST, ASSIGNDLY relative
   to the pre-fix baseline. (NFR-5 / AC-10.)

**Dependencies.** Depends on T1 and T2.

**Verification.** Each gate above is itself a verification step;
record the output of each in the implementation work log.

### T4. Single feature commit

**Description.** Stage the template edit and the regenerated goldens
together and commit them as one atomic feature commit. Do NOT split
into two commits (`feedback_byte_parity_per_commit.md`).

**Commit message.** Conventional Commits format per Constitution:

```
fix(sv): use width-correct cast in enum pack body

The synth-package pack_<enum> function was emitting `return logic'(a);`,
which casts the enum value to single-bit `logic`, then implicitly
zero-extends back to the function's declared LP_<UPPER>_WIDTH-bit
return type. For any multi-bit enum this returns the LSB of the enum
value zero-extended, instead of the encoded bit pattern. The bug was
silent in tests because the _test_pkg helper class for enums uses
direct typedef assignment (`to_slv()` returns `value`) and does not
exercise pack_<enum>. Replace the cast with the size-cast form
LP_<UPPER>_WIDTH'(a), which is uniform across 1-bit and multi-bit
enums and matches the function's declared return width.

Spec: 014-enum-pack-width-cast
```

**Files staged.**

```
git add src/piketype/backends/sv/templates/_macros.j2 \
        tests/goldens/gen/enum_basic \
        tests/goldens/gen/struct_enum_member \
        tests/goldens/gen/keyword_enum_value_while_passes \
        tests/goldens/gen/cross_module_type_refs \
        tests/goldens/gen/cross_module_type_refs_namespace_proj
git commit -m "$(printf '...the message above...')"
```

(The exact `-m` body is the message above; quote it with a HEREDOC if
shell-quoting becomes awkward.)

**Dependencies.** Depends on T1, T2, T3.

**Verification.**
- `git log --stat -1` shows exactly the files listed in T1 + T2 and
  no others.
- `git diff master..HEAD --stat` is identical to the pre-commit
  expected diff scope (Phase 3 gates 5 and 6).
- Working tree is clean: `git status` shows nothing to commit.
- Re-running T3 gate 1 (`unittest discover`) on the committed state
  passes.

---

## Out-of-task scope (explicit non-tasks)

The following are NOT tasks for this implementation. Listed to
foreclose scope leak:

- Refactor `test_enum_helper` to route through `pack_<enum>`. (Spec
  FR-2.3 puts this out of scope.)
- Add a SystemVerilog testbench harness that compiles and executes
  `pack_<enum>` calls. (Clarification C-1 keeps this out of scope.)
- Edit any other branch of `synth_pack_fn` (scalar_alias, flags,
  struct). (Spec FR-2.1.)
- Edit any branch of `synth_unpack_fn`. (Spec FR-2.2.)
- Touch any C++ or Python backend or runtime package. (Spec FR-2.4.)
- Add a new fixture or golden directory. The 5 affected goldens are
  exhaustive; no new fixture is needed for AC coverage.
- Amend the commit, rebase, or split into multiple commits.
