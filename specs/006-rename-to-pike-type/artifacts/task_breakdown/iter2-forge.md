# Tasks — Spec 006: Rename to pike-type

## Task 1: Clean build artifacts
**Plan Step:** 1
**FRs:** NFR-5
**Description:** Delete all `__pycache__/` directories under `src/` and `tests/`, and remove `src/*.egg-info/` directories.
**Verification:** No `__pycache__` or `.egg-info` dirs remain under `src/` or `tests/fixtures/`.
**Files:**
- (cache/build artifacts only — no tracked files)

---

## Task 2: Rename source package and update all source code
**Plan Step:** 2 (atomic)
**FRs:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-15
**Description:** Atomic step: `git mv src/typist src/piketype`, update `pyproject.toml`, then update all imports, function names, class names, string literals, and docstrings across every `.py` file in `src/piketype/`.
**Verification:** `basedpyright src/piketype/` passes. `grep -rI -i "typist" src/piketype/` returns no matches.
**Files:**
- `pyproject.toml` — name, scripts entry
- `src/piketype/__init__.py` — docstring
- `src/piketype/cli.py` — prog name, imports
- `src/piketype/errors.py` — TypistError → PikeTypeError, docstring
- `src/piketype/paths.py` — runtime/manifest path constants
- `src/piketype/repo.py` — imports
- `src/piketype/discovery/scanner.py` — function renames, string literals, imports
- `src/piketype/discovery/module_name.py` — imports
- `src/piketype/loader/python_loader.py` — imports
- `src/piketype/commands/gen.py` — imports, function calls, error message
- `src/piketype/commands/build.py` — imports
- `src/piketype/commands/test.py` — imports
- `src/piketype/commands/lint.py` — imports
- `src/piketype/validate/engine.py` — error message, imports
- `src/piketype/validate/collisions.py` — imports
- `src/piketype/validate/naming.py` — imports
- `src/piketype/validate/widths.py` — imports
- `src/piketype/validate/namespace.py` — imports
- `src/piketype/validate/cross_language.py` — imports
- `src/piketype/validate/topology.py` — imports
- `src/piketype/backends/common/headers.py` — header string
- `src/piketype/backends/py/emitter.py` — header string, imports
- `src/piketype/backends/sv/emitter.py` — imports
- `src/piketype/backends/cpp/emitter.py` — namespace filter, imports
- `src/piketype/backends/runtime/emitter.py` — runtime names, header, imports
- `src/piketype/backends/test/emitter.py` — imports
- `src/piketype/backends/lint/emitter.py` — imports
- `src/piketype/backends/registry.py` — imports
- `src/piketype/backends/common/ordering.py` — imports
- `src/piketype/backends/common/render.py` — imports
- `src/piketype/loader/module_context.py` — imports
- `src/piketype/dsl/*.py` — imports (all files including `__init__.py`)
- `src/piketype/ir/*.py` — imports (all files including `__init__.py`)
- `src/piketype/manifest/*.py` — imports (all files including `__init__.py`)
- All other `__init__.py` files in subpackages — imports if any

---

## Task 3: Rename test fixture directories and update fixture imports
**Plan Step:** 3
**FRs:** FR-10
**Description:** Rename all `*/typist/` directories in `tests/fixtures/` to `*/piketype/`. Rename `outside_typist` → `outside_piketype` and `not_typist` → `not_piketype`. Update DSL import statements in all fixture `.py` files.
**Verification:** `find tests/fixtures -name '*typist*' -o -type d -name typist` returns empty. `grep -rI -i "typist" tests/fixtures/ --exclude-dir=__pycache__ --exclude='*.pyc'` returns no matches.
**Files:**
- `tests/fixtures/*/project/alpha/typist/` → `*/alpha/piketype/` (all fixtures)
- `tests/fixtures/*/project/beta/typist/` → `*/beta/piketype/` (const_sv_basic, namespace_override)
- `tests/fixtures/outside_typist/` → `tests/fixtures/outside_piketype/`
- `tests/fixtures/outside_piketype/project/alpha/not_typist/` → `*/not_piketype/`
- All `.py` files in fixtures: `from typist.dsl` → `from piketype.dsl`

---

## Task 4: Rename golden file paths
**Plan Step:** 4
**FRs:** FR-11 (paths only)
**Description:** Rename all `typist_manifest.json` → `piketype_manifest.json`, all `typist/` directories → `piketype/`, all `typist_runtime*` → `piketype_runtime*` files in `tests/goldens/gen/`.
**Verification:** `find tests/goldens -name '*typist*' -o -type d -name typist` returns empty.
**Files:**
- 14 `typist_manifest.json` files → `piketype_manifest.json`
- All `*/alpha/typist/`, `*/beta/typist/` directories → `*/piketype/`
- All `typist_runtime*` files → `piketype_runtime*`

---

## Task 5: Regenerate golden file content
**Plan Step:** 5
**FRs:** FR-11 (content)
**Description:** Install the package with `pip install -e .` and regenerate golden output for all 14 positive fixtures by running `piketype gen` on each. Copy `gen/` output to `tests/goldens/gen/<case>/`. The `namespace_override` fixture requires `--namespace foo::bar`.
**Verification:** `piketype gen` output matches golden files byte-for-byte. `grep -rI "typist" tests/goldens/` returns no matches (excluding binary).
**Fixtures:** const_cpp_explicit_uint32, const_cpp_wide, const_expr_basic, const_sv_basic, flags_basic, namespace_override, nested_struct_sv_basic, scalar_sv_basic, scalar_wide, struct_multiple_of, struct_padded, struct_signed, struct_sv_basic, struct_wide

---

## Task 6: Update test source files
**Plan Step:** 6
**FRs:** FR-12
**Description:** Update all `tests/test_*.py` files: imports, CLI invocations, fixture path references, method names, string literals, and expected error messages.
**Verification:** `grep -rI "typist" tests/test_*.py` returns no matches. Tests compile (no import errors).
**Files:**
- `tests/test_gen_const_sv.py`
- `tests/test_gen_flags.py`
- `tests/test_struct_multiple_of.py`
- `tests/test_cli_smoke.py`
- `tests/test_dsl_const.py`
- `tests/test_const_ranges.py`
- `tests/test_runtime_bytes.py`
- `tests/test_namespace_validation.py`

---

## Task 7: Update documentation
**Plan Step:** 7
**FRs:** FR-13
**Description:** Replace all `typist` references in documentation files with `piketype` (CLI/package) or `pike-type` (project name). All `typist_` prefixes become `piketype_`.
**Verification:** `grep -rI -i "typist" README.md docs/` returns no matches.
**Files:**
- `README.md`
- `docs/rfc-v1.md`
- `docs/architecture.md`
- `docs/v1-product-spec.md`
- `docs/milestone-01-const-sv.md`
- `docs/requirements.org`
- `docs/planning.org`
- `docs/ir-schema.md`

---

## Task 8: Update project constitution
**Plan Step:** 8
**FRs:** FR-14
**Description:** Update `.steel/constitution.md` to replace all `typist` references.
**Verification:** `grep -i "typist" .steel/constitution.md` returns no matches.
**Files:**
- `.steel/constitution.md`

---

## Task 9: Regenerate uv.lock
**Plan Step:** 9
**FRs:** FR-16
**Description:** Run `uv lock` to regenerate `uv.lock` with the new package name.
**Verification:** `grep -q 'name = "pike-type"' uv.lock && ! grep -q 'name = "typist"' uv.lock`
**Files:**
- `uv.lock`

---

## Task 10: Full verification
**Plan Step:** 10
**FRs:** AC-1 through AC-14
**Description:** Run all acceptance criteria checks. Clean artifacts first (NFR-5), then verify each AC explicitly.
**Verification:** All 14 ACs pass.
**Commands:**
```bash
# NFR-5: Clean artifacts
find src/ tests/ -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
rm -rf src/*.egg-info

# AC-1: Install and verify CLI command exists
pip install -e .
which piketype

# AC-2: Run piketype gen on a fixture and diff against golden
# (covered by test suite — each golden test does exactly this)

# AC-3: Run test suite (primary: unittest per constitution, secondary: pytest)
python3 -m unittest discover -s tests
python3 -m pytest

# AC-4: No stale "typist" references in file contents
! grep -rI -i "typist" --exclude-dir=__pycache__ --exclude-dir='*.egg-info' --exclude='*.pyc' src/ tests/ pyproject.toml README.md docs/ .steel/constitution.md

# AC-5: Discovery scanner accept/reject (covered by test suite; explicit check):
python3 -c "
from pathlib import Path
from piketype.discovery.scanner import is_under_piketype_dir
assert is_under_piketype_dir(Path('alpha/piketype/types.py'))
assert not is_under_piketype_dir(Path('alpha/other/types.py'))
print('AC-5: PASS')
"

# AC-6: Generated file headers say "Generated by piketype"
grep -r "Generated by piketype" tests/goldens/gen/const_sv_basic/ && echo "AC-6: PASS"

# AC-7: Generated runtime files named piketype_runtime*
find tests/goldens -name 'piketype_runtime*' | head -1 && echo "AC-7: PASS"

# AC-8: Manifest named piketype_manifest.json
find tests/goldens -name 'piketype_manifest.json' | head -1 && echo "AC-8: PASS"

# AC-9: Type checking
basedpyright src/piketype/

# AC-10: C++ namespace and header guard
grep -q "namespace piketype_runtime" tests/goldens/gen/const_sv_basic/cpp/runtime/piketype_runtime.hpp && echo "AC-10 namespace: PASS"
grep -q "PIKETYPE_RUNTIME_HPP" tests/goldens/gen/const_sv_basic/cpp/runtime/piketype_runtime.hpp && echo "AC-10 guard: PASS"

# AC-11: Import check
python3 -c "import piketype; print(piketype.__version__)"

# AC-12: Exception class hierarchy
python3 -c "
from piketype.errors import PikeTypeError, DiscoveryError, ValidationError, EmissionError
assert issubclass(DiscoveryError, PikeTypeError)
assert issubclass(ValidationError, PikeTypeError)
assert issubclass(EmissionError, PikeTypeError)
print('AC-12: PASS')
"

# AC-13: uv.lock verification
grep -q 'name = "pike-type"' uv.lock && ! grep -q 'name = "typist"' uv.lock && echo "AC-13: PASS"

# AC-14: No stale paths
test -z "$(find src/ tests/ -name '*typist*' 2>/dev/null)" && echo "AC-14: PASS"
```
