"""View-model tests for the SystemVerilog backend."""

from __future__ import annotations

import unittest
from pathlib import Path

from piketype import __version__
from piketype.backends.sv.view import (
    SvSynthModuleView,
    SvTestModuleView,
    build_synth_module_view_sv,
    build_test_module_view_sv,
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
from piketype.loader.python_loader import load_module_from_path

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_fixture_module(fixture_name: str) -> ModuleIR:
    repo_root = _FIXTURES / fixture_name / "project"
    module_paths = find_piketype_modules(repo_root)
    loaded_modules = [
        build_loaded_module(
            module=load_module_from_path(p, repo_root=repo_root),
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


class SynthViewTests(unittest.TestCase):
    def test_package_name_uses_pkg_suffix(self) -> None:
        module = _load_fixture_module("scalar_sv_basic")
        view = build_synth_module_view_sv(module=module)
        self.assertIsInstance(view, SvSynthModuleView)
        self.assertTrue(view.package_name.endswith("_pkg"))
        self.assertFalse(view.package_name.endswith("_test_pkg"))

    def test_synth_view_has_one_type_per_ir(self) -> None:
        module = _load_fixture_module("scalar_sv_basic")
        view = build_synth_module_view_sv(module=module)
        self.assertEqual(len(view.types), len(module.types))

    def test_synth_type_body_text_is_indented(self) -> None:
        module = _load_fixture_module("nested_struct_sv_basic")
        view = build_synth_module_view_sv(module=module)
        for t in view.types:
            self.assertTrue(t.body_text.startswith("  "), f"body for {t.name} not indented")


class TestPackageViewTests(unittest.TestCase):
    def test_test_package_name_suffix(self) -> None:
        module = _load_fixture_module("scalar_sv_basic")
        view = build_test_module_view_sv(module=module)
        self.assertIsInstance(view, SvTestModuleView)
        self.assertTrue(view.package_name.endswith("_test_pkg"))

    def test_synth_package_import_present(self) -> None:
        module = _load_fixture_module("scalar_sv_basic")
        view = build_test_module_view_sv(module=module)
        self.assertIn("import", view.synth_package_import)
        self.assertIn("_pkg::*", view.synth_package_import)


class CombinedFixtureTests(unittest.TestCase):
    def test_synth_and_test_views_for_struct_padded(self) -> None:
        module = _load_fixture_module("struct_padded")
        synth = build_synth_module_view_sv(module=module)
        test = build_test_module_view_sv(module=module)
        # The two views describe the same module from different angles.
        self.assertEqual(len(synth.types), len(test.types))
        for s, t in zip(synth.types, test.types, strict=True):
            self.assertEqual(s.name, t.name)


if __name__ == "__main__":
    unittest.main()
