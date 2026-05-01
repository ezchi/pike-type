"""Integration tests for spec 011 cross-module type references."""

from __future__ import annotations

import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
GOLDENS_DIR = TESTS_DIR / "goldens" / "gen"


def _assert_trees_equal(test_case: unittest.TestCase, expected: Path, actual: Path) -> None:
    """Compare two directory trees byte-for-byte (recursive)."""
    comparison = filecmp.dircmp(expected, actual)
    test_case.assertFalse(comparison.left_only, f"missing generated files: {comparison.left_only}")
    test_case.assertFalse(comparison.right_only, f"unexpected generated files: {comparison.right_only}")
    test_case.assertFalse(comparison.funny_files, f"uncomparable files: {comparison.funny_files}")
    for filename in comparison.common_files:
        expected_text = (expected / filename).read_text(encoding="utf-8")
        actual_text = (actual / filename).read_text(encoding="utf-8")
        test_case.assertEqual(expected_text, actual_text, f"content mismatch for {filename}")
    for subdir in comparison.common_dirs:
        _assert_trees_equal(test_case, expected / subdir, actual / subdir)


def _run_piketype(*, repo_dir: Path, cli_arg: str, extra_args: tuple[str, ...] = ()) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "piketype.cli", "gen", *extra_args, cli_arg],
        cwd=repo_dir,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


class CrossModuleTypeRefsIntegrationTest(unittest.TestCase):
    """End-to-end fixture comparison for cross_module_type_refs."""

    def test_generates_expected_outputs(self) -> None:
        fixture_root = FIXTURES_DIR / "cross_module_type_refs" / "project"
        expected_root = GOLDENS_DIR / "cross_module_type_refs"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir, dirs_exist_ok=True)
            cli_file = repo_dir / "alpha" / "piketype" / "bar.py"
            result = _run_piketype(repo_dir=repo_dir, cli_arg=str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            _assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_idempotent(self) -> None:
        fixture_root = FIXTURES_DIR / "cross_module_type_refs" / "project"
        expected_root = GOLDENS_DIR / "cross_module_type_refs"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir, dirs_exist_ok=True)
            cli_file = repo_dir / "alpha" / "piketype" / "bar.py"
            r1 = _run_piketype(repo_dir=repo_dir, cli_arg=str(cli_file))
            self.assertEqual(r1.returncode, 0, msg=r1.stderr)
            r2 = _run_piketype(repo_dir=repo_dir, cli_arg=str(cli_file))
            self.assertEqual(r2.returncode, 0, msg=r2.stderr)
            _assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_bar_pkg_uses_cross_module_byte_t(self) -> None:
        """AC-2, AC-3: explicit per-symbol imports for cross-module type refs."""
        bar_pkg_path = GOLDENS_DIR / "cross_module_type_refs" / "sv" / "alpha" / "piketype" / "bar_pkg.sv"
        text = bar_pkg_path.read_text(encoding="utf-8")
        # AC-2: explicit per-symbol imports (no wildcard) for the byte_t bundle.
        self.assertNotIn("import foo_pkg::*;", text)
        for sym in ("byte_t", "LP_BYTE_WIDTH", "pack_byte", "unpack_byte"):
            self.assertIn(f"import foo_pkg::{sym};", text)
        # AC-3: typedef uses byte_t (not logic [7:0]) for both fields.
        self.assertIn("byte_t field1;", text)
        self.assertIn("byte_t field2;", text)
        self.assertNotIn("logic [7:0] field1", text)
        self.assertNotIn("logic [7:0] field2", text)
        # unpack uses LP_BYTE_WIDTH and unpack_byte by unqualified name.
        self.assertIn("LP_BYTE_WIDTH", text)
        self.assertIn("unpack_byte(", text)


class CrossModuleNamespaceIntegrationTest(unittest.TestCase):
    """AC-6 user-namespace path: piketype gen --namespace=proj::lib."""

    def test_namespace_proj_generates_qualified_field_types(self) -> None:
        fixture_root = FIXTURES_DIR / "cross_module_type_refs" / "project"
        expected_root = GOLDENS_DIR / "cross_module_type_refs_namespace_proj"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir, dirs_exist_ok=True)
            cli_file = repo_dir / "alpha" / "piketype" / "bar.py"
            result = _run_piketype(
                repo_dir=repo_dir, cli_arg=str(cli_file),
                extra_args=("--namespace=proj::lib",),
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            _assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_bar_types_hpp_uses_qualified_byte_ct(self) -> None:
        """AC-6: with --namespace=proj::lib, cross-module field types are ::proj::lib::foo::*_ct."""
        bar_hpp = GOLDENS_DIR / "cross_module_type_refs_namespace_proj" / "cpp" / "alpha" / "piketype" / "bar_types.hpp"
        text = bar_hpp.read_text(encoding="utf-8")
        self.assertIn("::proj::lib::foo::byte_ct field1", text)
        self.assertIn("::proj::lib::foo::byte_ct field2", text)
        # The include path is unaffected by --namespace.
        self.assertIn('#include "alpha/piketype/foo_types.hpp"', text)


class CrossModuleStructMultipleOfIntegrationTest(unittest.TestCase):
    """AC-18 / FR-3: cross-module struct member with multiple_of() trailing alignment."""

    def test_generates_expected_outputs(self) -> None:
        fixture_root = FIXTURES_DIR / "cross_module_struct_multiple_of" / "project"
        expected_root = GOLDENS_DIR / "cross_module_struct_multiple_of"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir, dirs_exist_ok=True)
            cli_file = repo_dir / "alpha" / "piketype" / "bar.py"
            result = _run_piketype(repo_dir=repo_dir, cli_arg=str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            _assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_bar_pkg_alignment_byte_count(self) -> None:
        """Three byte_t fields = 24 data bits; multiple_of(32) → 4-byte total."""
        bar_pkg = GOLDENS_DIR / "cross_module_struct_multiple_of" / "sv" / "alpha" / "piketype" / "bar_pkg.sv"
        text = bar_pkg.read_text(encoding="utf-8")
        self.assertIn("LP_BAR_WIDTH = 24;", text)
        self.assertIn("LP_BAR_BYTE_COUNT = 4;", text)
        self.assertIn("_align_pad", text)


if __name__ == "__main__":
    unittest.main()
