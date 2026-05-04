"""Tests for the per-run loader contract (FR-1)."""

from __future__ import annotations

import pytest
import sys
import tempfile
import textwrap
from pathlib import Path

from piketype.discovery.scanner import find_piketype_modules
from piketype.loader.python_loader import load_or_get_module, prepare_run

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


class PrepareRunSnapshotRestoreTests:
    """Verify prepare_run snapshots and restores sys.modules."""

    def test_owned_keys_removed_during_scope_then_restored(self) -> None:
        repo_root = _FIXTURES / "struct_sv_basic" / "project"
        module_paths = find_piketype_modules(repo_root)
        owned_name = "alpha.piketype.types"

        # Inject a sentinel before the run.
        sentinel = object()
        sys.modules[owned_name] = sentinel  # type: ignore[assignment]
        try:
            with prepare_run(repo_root=repo_root, module_paths=module_paths):
                # Inside the scope, the owned key was popped (or replaced via load).
                assert sys.modules.get(owned_name) is not sentinel
            # After the scope, the original sentinel is restored.
            assert sys.modules.get(owned_name) is sentinel
        finally:
            sys.modules.pop(owned_name, None)

    def test_keys_absent_before_run_are_absent_after(self) -> None:
        repo_root = _FIXTURES / "struct_sv_basic" / "project"
        module_paths = find_piketype_modules(repo_root)
        owned_name = "alpha.piketype.types"

        # Ensure the key is not in sys.modules before the run.
        sys.modules.pop(owned_name, None)

        with prepare_run(repo_root=repo_root, module_paths=module_paths):
            load_or_get_module(module_paths[0], repo_root=repo_root)
            # The module is now cached in sys.modules.
            assert owned_name in sys.modules

        # After the scope, the key is gone again (no leak).
        assert owned_name not in sys.modules

    def test_sequential_runs_do_not_leak_between_fixtures(self) -> None:
        # Two different fixtures with different alpha.piketype.types modules.
        # After loading both sequentially, neither is in sys.modules.
        fixture_a = _FIXTURES / "struct_sv_basic" / "project"
        fixture_b = _FIXTURES / "scalar_signed_wide" / "project"

        owned_name = "alpha.piketype.types"
        sys.modules.pop(owned_name, None)

        paths_a = find_piketype_modules(fixture_a)
        with prepare_run(repo_root=fixture_a, module_paths=paths_a):
            mod_a = load_or_get_module(paths_a[0], repo_root=fixture_a)
            assert sys.modules[owned_name] is mod_a

        assert owned_name not in sys.modules

        paths_b = find_piketype_modules(fixture_b)
        with prepare_run(repo_root=fixture_b, module_paths=paths_b):
            mod_b = load_or_get_module(paths_b[0], repo_root=fixture_b)
            # Different fixture, different module object.
            assert mod_a is not mod_b

        assert owned_name not in sys.modules

    def test_nested_prepare_run_raises(self) -> None:
        repo_root = _FIXTURES / "struct_sv_basic" / "project"
        module_paths = find_piketype_modules(repo_root)
        with prepare_run(repo_root=repo_root, module_paths=module_paths):
            with pytest.raises(RuntimeError):
                with prepare_run(repo_root=repo_root, module_paths=module_paths):
                    pass


class LoadOrGetModuleTests:
    """Verify load_or_get_module identity and scope-enforcement contract."""

    def test_outside_scope_raises_runtime_error(self) -> None:
        repo_root = _FIXTURES / "struct_sv_basic" / "project"
        module_paths = find_piketype_modules(repo_root)
        with pytest.raises(RuntimeError):
            load_or_get_module(module_paths[0], repo_root=repo_root)

    def test_repeated_calls_return_same_object(self) -> None:
        repo_root = _FIXTURES / "struct_sv_basic" / "project"
        module_paths = find_piketype_modules(repo_root)
        with prepare_run(repo_root=repo_root, module_paths=module_paths):
            mod1 = load_or_get_module(module_paths[0], repo_root=repo_root)
            mod2 = load_or_get_module(module_paths[0], repo_root=repo_root)
            assert mod1 is mod2


class CrossModuleIdentityTests:
    """Reproduce the FR-1 bug: cross-module type identity must be preserved.

    Builds a two-module fixture at runtime where bar.py imports byte_t from
    foo.py and uses it in a struct. With load_or_get_module + prepare_run,
    the byte_t object visible in bar.py's __dict__ must be identical to the
    byte_t object visible in foo.py's __dict__.
    """

    def setup_method(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        piketype_dir = root / "alpha" / "piketype"
        piketype_dir.mkdir(parents=True)
        (root / "pyproject.toml").write_text("")  # repo-root marker
        (root / "alpha" / "__init__.py").write_text("")
        (piketype_dir / "__init__.py").write_text("")
        (piketype_dir / "foo.py").write_text(textwrap.dedent("""\
            from piketype.dsl import Logic
            byte_t = Logic(8)
        """))
        (piketype_dir / "bar.py").write_text(textwrap.dedent("""\
            from piketype.dsl import Struct
            from alpha.piketype.foo import byte_t
            bar_t = (
                Struct()
                .add_member("field1", byte_t)
                .add_member("field2", byte_t)
            )
        """))
        self.repo_root = root

    def teardown_method(self) -> None:
        self._tmp.cleanup()

    def test_cross_module_byte_t_has_stable_identity(self) -> None:
        module_paths = find_piketype_modules(self.repo_root)
        # Two paths: foo.py and bar.py, sorted.
        assert len(module_paths) == 2

        with prepare_run(repo_root=self.repo_root, module_paths=module_paths):
            modules = {p.stem: load_or_get_module(p, repo_root=self.repo_root) for p in module_paths}
            byte_t_in_foo = modules["foo"].byte_t
            byte_t_in_bar = modules["bar"].byte_t
            # The fix this test guards: identity must be stable across modules.
            assert byte_t_in_foo is byte_t_in_bar

    def test_load_path_not_in_owned_set_raises(self) -> None:
        all_paths = find_piketype_modules(self.repo_root)
        foo_path = next(p for p in all_paths if p.stem == "foo")
        bar_path = next(p for p in all_paths if p.stem == "bar")
        # Prepare with only foo in the owned set; bar's module name is therefore unowned.
        with prepare_run(repo_root=self.repo_root, module_paths=[foo_path]):
            with pytest.raises(RuntimeError) as ctx:
                load_or_get_module(bar_path, repo_root=self.repo_root)
            assert "not in the active prepare_run owned-key set" in str(ctx.value)
