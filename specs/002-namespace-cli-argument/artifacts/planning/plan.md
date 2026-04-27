# Implementation Plan — Spec 002: `--namespace` CLI Argument

## Architecture Decision

**Approach:** Pass-through parameter. The `--namespace` value flows from CLI →
`run_gen()` → `emit_cpp()` → `render_module_hpp()` as a `str | None` parameter.
No IR changes. No new classes. Validation is a standalone pure function in a new
module.

**Rationale:** The feature is C++ backend-only. Modifying IR would violate FR-6
and add complexity for SV/Python backends that don't use it. A simple parameter
thread is the minimum change.

## File Change Map

### New files

1. **`src/typist/validate/namespace.py`** — Namespace validation logic
   - `validate_cpp_namespace(value: str) -> tuple[str, ...]` — Validates and
     returns the parsed segments. Raises `ValidationError` on failure.
   - `CPP17_KEYWORDS: frozenset[str]` — Complete C++17 keyword set (84 keywords):
     `alignas`, `alignof`, `and`, `and_eq`, `asm`, `auto`, `bitand`, `bitor`,
     `bool`, `break`, `case`, `catch`, `char`, `char16_t`, `char32_t`, `class`,
     `compl`, `concept`, `const`, `consteval`, `constexpr`, `constinit`,
     `const_cast`, `continue`, `co_await`, `co_return`, `co_yield`, `decltype`,
     `default`, `delete`, `do`, `double`, `dynamic_cast`, `else`, `enum`,
     `explicit`, `export`, `extern`, `false`, `float`, `for`, `friend`, `goto`,
     `if`, `inline`, `int`, `long`, `mutable`, `namespace`, `new`, `noexcept`,
     `not`, `not_eq`, `nullptr`, `operator`, `or`, `or_eq`, `private`,
     `protected`, `public`, `register`, `reinterpret_cast`, `requires`,
     `return`, `short`, `signed`, `sizeof`, `static`, `static_assert`,
     `static_cast`, `struct`, `switch`, `template`, `this`, `thread_local`,
     `throw`, `true`, `try`, `typedef`, `typeid`, `typename`, `union`,
     `unsigned`, `using`, `virtual`, `void`, `volatile`, `wchar_t`, `while`,
     `xor`, `xor_eq`.
   - `check_duplicate_basenames(module_paths: list[Path]) -> None` — Groups by
     `Path.stem`, raises `ValidationError` with the duplicate basename and all
     conflicting repo-relative paths (sorted deterministically).
   - Pure functions, no side effects, easily unit-testable.

2. **`tests/test_namespace_validation.py`** — Unit tests for validation logic
   - Tests for each segment rule (empty, non-identifier, keyword, leading `_`,
     `__`, trailing `_`, `std`) and the composition check.
   - Keyword coverage: test at least `class`, `alignas`, `constexpr`,
     `thread_local`, `noexcept`, `nullptr`, `static_assert`.
   - Tests for `check_duplicate_basenames` with conflicting and non-conflicting
     paths.
   - Uses `unittest.TestCase`.

3. **`tests/fixtures/namespace_override/project/`** — Multi-module fixture
   - `alpha/typist/constants.py` — Constants (reuse `const_sv_basic` DSL).
   - `beta/typist/more.py` — More constants (different path-derived namespace).
   - `.git/HEAD` — Bare git marker (matches existing fixture pattern).

4. **`tests/goldens/gen/namespace_override/`** — Golden output for the fixture
   - `cpp/alpha/typist/constants_types.hpp` — Namespace `foo::bar::constants`,
     guard `FOO_BAR_CONSTANTS_TYPES_HPP`.
   - `cpp/beta/typist/more_types.hpp` — Namespace `foo::bar::more`,
     guard `FOO_BAR_MORE_TYPES_HPP`.
   - `cpp/runtime/typist_runtime.hpp` — **Unchanged** from baseline (byte-for-byte
     identical to `const_sv_basic` runtime).
   - `cpp/runtime/typist_runtime.cpp` — **Unchanged**.
   - `sv/`, `py/`, `typist_manifest.json` — **Unchanged** from `const_sv_basic`
     baseline (SV/Python/manifest unaffected by `--namespace`).
   - The golden test compares the **full `gen/` tree**, ensuring runtime C++ outputs
     and all non-C++ outputs are byte-for-byte identical.

### Modified files

5. **`src/typist/cli.py`** — Add `--namespace` to `gen` subparser
   - Break out `gen` from the shared loop to add `--namespace` as an optional arg.
   - Pass `args.namespace` (which is `None` when omitted) to `run_gen`.

6. **`src/typist/commands/gen.py`** — Accept and thread `namespace` parameter
   - `run_gen(path: str, *, namespace: str | None = None)` — New kwarg.
   - Call `validate_cpp_namespace()` before discovery if `namespace` is not None.
   - After discovery, if `namespace` is set, call `check_duplicate_basenames()`.
   - Pass `namespace` to `emit_cpp()`.

7. **`src/typist/backends/cpp/emitter.py`** — Use namespace override
   - `emit_cpp(repo, *, namespace: str | None = None)` — New kwarg.
   - `render_module_hpp(module, *, namespace: str | None = None)` — New kwarg.
   - When `namespace` is not None:
     - `guard = f"{namespace.replace('::', '_')}_{module.ref.basename}_TYPES_HPP".upper()`
     - `ns = f"{namespace}::{module.ref.basename}"`
   - When `namespace` is None: existing logic unchanged.

8. **`tests/test_gen_const_sv.py`** — Add integration tests
   - **Update `run_typist` helper** to accept `*extra_args: str` so it can pass
     `--namespace foo::bar` before the path argument. Signature:
     `run_typist(self, repo_dir: Path, cli_arg: str, *extra_args: str)`.
     Command becomes `[sys.executable, "-m", "typist.cli", "gen", *extra_args, cli_arg]`.
   - Positive golden test: `--namespace foo::bar` with `namespace_override` fixture.
   - Negative tests for each validation category:
     - Empty segment: `--namespace "foo::::bar"`
     - Non-identifier: `--namespace "123bad"`
     - C++ keyword: `--namespace "class"`
     - Double underscore: `--namespace "foo__bar"`
     - Leading underscore: `--namespace "_foo"`
     - `std` first segment: `--namespace "std::types"`
     - Trailing underscore: `--namespace "foo_"`
     - Leading underscore non-first: `--namespace "foo::_bar"`
     - Duplicate basename: use `const_sv_basic` fixture (has `alpha/typist/constants.py`
       and `beta/typist/more.py` — different basenames, so need a temp fixture with
       same basenames, e.g. `alpha/typist/types.py` + `beta/typist/types.py`).

## Ordering

```
1. validate/namespace.py  (new, no deps)
2. test_namespace_validation.py  (unit tests for ^, run to verify)
3. cli.py  (arg parsing change)
4. commands/gen.py  (plumbing + duplicate check)
5. backends/cpp/emitter.py  (namespace override logic)
6. fixture + goldens  (test data — generate by running tool, verify manually)
7. test_gen_const_sv.py  (integration tests — update helper, add tests)
8. Run full test suite, fix any regressions
```

## Risk Assessment

- **Low risk:** CLI change is additive (new optional arg). Existing tests
  exercise `namespace=None` path.
- **Low risk:** C++ emitter change is guarded by `if namespace is not None`.
  Default path is untouched.
- **Medium risk:** Golden files for the new fixture must be generated correctly
  on first attempt. Mitigated by running the tool and manually verifying before
  committing goldens.

## Constitution Compliance

- **Deterministic output:** Preserved — namespace is an explicit input, not
  environment-dependent.
- **Immutable IR:** Respected — IR `namespace_parts` untouched.
- **Golden-file testing:** New fixture + golden added, full `gen/` tree compared.
- **Template-first:** The C++ backend currently uses inline string building (not
  templates). This feature follows the existing pattern; migrating to templates
  is a separate concern.
- **No new deps:** Uses stdlib `re` only.
- **basedpyright strict:** All new code will pass strict mode.
- **Keyword-only args:** New parameters use `*` for keyword-only enforcement.
