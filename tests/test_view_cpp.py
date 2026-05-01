"""View-model tests for the C++ backend."""

from __future__ import annotations

import unittest
from pathlib import Path

from piketype import __version__
from piketype.backends.cpp.view import (
    CppGuardView,
    CppNamespaceView,
    build_module_view_cpp,
)
from piketype.discovery.scanner import find_piketype_modules
from piketype.dsl.freeze import (
    build_const_definition_map,
    build_loaded_module,
    build_type_definition_map,
    freeze_module,
    freeze_repo,
)
from piketype.ir.nodes import ModuleIR
from piketype.loader.python_loader import load_or_get_module, prepare_run

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_fixture_module(fixture_name: str) -> ModuleIR:
    repo_root = _FIXTURES / fixture_name / "project"
    module_paths = find_piketype_modules(repo_root)
    with prepare_run(repo_root=repo_root, module_paths=module_paths):
        loaded_modules = [
            build_loaded_module(
                module=load_or_get_module(p, repo_root=repo_root),
                module_path=p,
                repo_root=repo_root,
            )
            for p in module_paths
        ]
        const_map = build_const_definition_map(loaded_modules=loaded_modules)
        type_map = build_type_definition_map(loaded_modules=loaded_modules)
        frozen = [
            freeze_module(loaded_module=lm, definition_map=const_map, type_definition_map=type_map)
            for lm in loaded_modules
        ]
        repo = freeze_repo(repo_root=repo_root, frozen_modules=frozen, tool_version=__version__)
        return repo.modules[0]


class GuardViewTests(unittest.TestCase):
    def test_default_namespace_guard(self) -> None:
        module = _load_fixture_module("scalar_wide")
        view = build_module_view_cpp(module=module)
        self.assertIsInstance(view.guard, CppGuardView)
        self.assertTrue(view.guard.macro.endswith("_TYPES_HPP"))
        # Guard is upper-snake derived from namespace parts.
        self.assertEqual(view.guard.macro, view.guard.macro.upper())

    def test_namespace_override_guard(self) -> None:
        module = _load_fixture_module("scalar_wide")
        view = build_module_view_cpp(module=module, namespace="proj::lib")
        self.assertEqual(view.guard.macro, "PROJ_LIB_TYPES_TYPES_HPP")


class NamespaceViewTests(unittest.TestCase):
    def test_default_namespace_strips_piketype(self) -> None:
        module = _load_fixture_module("scalar_wide")
        view = build_module_view_cpp(module=module)
        self.assertIsInstance(view.namespace, CppNamespaceView)
        self.assertNotIn("piketype", view.namespace.qualified)

    def test_namespace_override_used_directly(self) -> None:
        module = _load_fixture_module("scalar_wide")
        view = build_module_view_cpp(module=module, namespace="proj::lib")
        self.assertTrue(view.namespace.qualified.startswith("proj::lib"))
        self.assertTrue(view.namespace.has_namespace)
        self.assertTrue(view.namespace.open_line.startswith("namespace "))


class IncludesAndTypesTests(unittest.TestCase):
    def test_standard_includes_with_types_in_declaration_order(self) -> None:
        module = _load_fixture_module("scalar_wide")
        view = build_module_view_cpp(module=module)
        self.assertEqual(
            view.standard_includes,
            ("<cstdint>", "<cstddef>", "<stdexcept>", "<vector>"),
        )

    def test_module_view_carries_one_type_per_ir_type(self) -> None:
        module = _load_fixture_module("scalar_wide")
        view = build_module_view_cpp(module=module)
        self.assertEqual(len(view.types), len(module.types))

    def test_type_view_kinds_are_recognized(self) -> None:
        module = _load_fixture_module("struct_padded")
        view = build_module_view_cpp(module=module)
        for t in view.types:
            self.assertIn(t.kind, {"scalar_alias", "struct", "enum", "flags"})


class ConstViewTests(unittest.TestCase):
    def test_constants_have_pre_rendered_expression_text(self) -> None:
        module = _load_fixture_module("const_cpp_wide")
        view = build_module_view_cpp(module=module)
        for c in view.constants:
            self.assertIsInstance(c.cpp_type, str)
            self.assertIsInstance(c.value_expr, str)
            self.assertGreater(len(c.value_expr), 0)


if __name__ == "__main__":
    unittest.main()
