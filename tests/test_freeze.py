"""Tests for freeze cross-module behavior (FR-2, FR-4)."""

from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from piketype import __version__
from piketype.discovery.scanner import find_piketype_modules
from piketype.dsl.freeze import (
    build_const_definition_map,
    build_loaded_module,
    build_type_definition_map,
    freeze_module,
    freeze_repo,
)
from piketype.ir.nodes import ConstRefExprIR, ModuleDependencyIR, TypeRefIR
from piketype.loader.python_loader import load_or_get_module, prepare_run


def _build_two_module_fixture(*, foo_body: str, bar_body: str) -> Path:
    """Create a two-module piketype repo in a temp dir; return the repo root."""
    tmpdir = tempfile.mkdtemp()
    root = Path(tmpdir)
    piketype_dir = root / "alpha" / "piketype"
    piketype_dir.mkdir(parents=True)
    (root / "pyproject.toml").write_text("")
    (root / "alpha" / "__init__.py").write_text("")
    (piketype_dir / "__init__.py").write_text("")
    (piketype_dir / "foo.py").write_text(foo_body)
    (piketype_dir / "bar.py").write_text(bar_body)
    return root


def _freeze_repo(root: Path):
    """Run the load/freeze pipeline on the two-module repo."""
    module_paths = find_piketype_modules(root)
    with prepare_run(repo_root=root, module_paths=module_paths):
        loaded = [
            build_loaded_module(
                module=load_or_get_module(p, repo_root=root),
                module_path=p,
                repo_root=root,
            )
            for p in module_paths
        ]
        const_map = build_const_definition_map(loaded_modules=loaded)
        type_map = build_type_definition_map(loaded_modules=loaded)
        frozen = [
            freeze_module(loaded_module=lm, definition_map=const_map, type_definition_map=type_map)
            for lm in loaded
        ]
        return freeze_repo(repo_root=root, frozen_modules=frozen, tool_version=__version__)


class CrossModuleTypeRefTests(unittest.TestCase):
    def test_struct_field_referencing_other_module_produces_type_ref(self) -> None:
        root = _build_two_module_fixture(
            foo_body=textwrap.dedent("""\
                from piketype.dsl import Logic
                byte_t = Logic(8)
            """),
            bar_body=textwrap.dedent("""\
                from piketype.dsl import Struct
                from alpha.piketype.foo import byte_t
                bar_t = Struct().add_member("f", byte_t)
            """),
        )
        repo = _freeze_repo(root)
        bar_module = next(m for m in repo.modules if m.ref.basename == "bar")
        struct_ir = bar_module.types[0]
        field = struct_ir.fields[0]
        self.assertIsInstance(field.type_ir, TypeRefIR)
        assert isinstance(field.type_ir, TypeRefIR)  # narrow for type checker
        self.assertEqual(field.type_ir.module.python_module_name, "alpha.piketype.foo")
        self.assertEqual(field.type_ir.name, "byte_t")


class ModuleDependenciesTests(unittest.TestCase):
    def test_cross_module_type_ref_produces_dependency(self) -> None:
        root = _build_two_module_fixture(
            foo_body=textwrap.dedent("""\
                from piketype.dsl import Logic
                byte_t = Logic(8)
            """),
            bar_body=textwrap.dedent("""\
                from piketype.dsl import Struct
                from alpha.piketype.foo import byte_t
                bar_t = Struct().add_member("f", byte_t)
            """),
        )
        repo = _freeze_repo(root)
        bar_module = next(m for m in repo.modules if m.ref.basename == "bar")
        deps = bar_module.dependencies
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].kind, "type_ref")
        self.assertEqual(deps[0].target.python_module_name, "alpha.piketype.foo")

    def test_same_module_ref_produces_no_dependency(self) -> None:
        root = _build_two_module_fixture(
            foo_body=textwrap.dedent("""\
                from piketype.dsl import Logic
                byte_t = Logic(8)
            """),
            bar_body=textwrap.dedent("""\
                from piketype.dsl import Logic
                local_byte_t = Logic(8)
            """),
        )
        repo = _freeze_repo(root)
        for module in repo.modules:
            self.assertEqual(module.dependencies, ())

    def test_dependencies_sorted_deterministically(self) -> None:
        # bar depends on foo for both type_ref and a constant. The result
        # should be sorted by (target_python_module_name, kind).
        root = _build_two_module_fixture(
            foo_body=textwrap.dedent("""\
                from piketype.dsl import Const, Logic
                SIZE = Const(8)
                byte_t = Logic(8)
            """),
            bar_body=textwrap.dedent("""\
                from piketype.dsl import Logic, Struct
                from alpha.piketype.foo import SIZE, byte_t
                wide_t = Logic(SIZE)
                bar_t = Struct().add_member("f", byte_t)
            """),
        )
        repo = _freeze_repo(root)
        bar_module = next(m for m in repo.modules if m.ref.basename == "bar")
        deps = bar_module.dependencies
        # Two distinct kinds → two entries.
        self.assertEqual(len(deps), 2)
        # Sorted by (module, kind): const_ref then type_ref (alphabetical).
        kinds = [d.kind for d in deps]
        self.assertEqual(kinds, sorted(kinds))


class CrossModuleConstRefTests(unittest.TestCase):
    def test_scalar_alias_width_expr_const_ref(self) -> None:
        root = _build_two_module_fixture(
            foo_body=textwrap.dedent("""\
                from piketype.dsl import Const
                SIZE = Const(16)
            """),
            bar_body=textwrap.dedent("""\
                from piketype.dsl import Logic
                from alpha.piketype.foo import SIZE
                wide_t = Logic(SIZE)
            """),
        )
        repo = _freeze_repo(root)
        bar_module = next(m for m in repo.modules if m.ref.basename == "bar")
        wide_t = bar_module.types[0]
        # Width expr should be a cross-module ConstRefExprIR.
        self.assertIsInstance(wide_t.width_expr, ConstRefExprIR)
        assert isinstance(wide_t.width_expr, ConstRefExprIR)
        self.assertEqual(wide_t.width_expr.module.python_module_name, "alpha.piketype.foo")


if __name__ == "__main__":
    unittest.main()
