"""Integration tests for milestone-01 constant-only generation."""

from __future__ import annotations

import filecmp
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
GOLDENS_DIR = TESTS_DIR / "goldens" / "gen"


def copy_tree(src: Path, dst: Path) -> None:
    """Copy a fixture tree into a temp directory."""
    shutil.copytree(src, dst, dirs_exist_ok=True)


def assert_trees_equal(test_case: unittest.TestCase, expected: Path, actual: Path) -> None:
    """Compare two directory trees byte-for-byte."""
    comparison = filecmp.dircmp(expected, actual)
    test_case.assertFalse(comparison.left_only, f"missing generated files: {comparison.left_only}")
    test_case.assertFalse(comparison.right_only, f"unexpected generated files: {comparison.right_only}")
    test_case.assertFalse(comparison.funny_files, f"uncomparable files: {comparison.funny_files}")

    for filename in comparison.common_files:
        expected_text = (expected / filename).read_text(encoding="utf-8")
        actual_text = (actual / filename).read_text(encoding="utf-8")
        test_case.assertEqual(expected_text, actual_text, f"content mismatch for {filename}")

    for subdir in comparison.common_dirs:
        assert_trees_equal(test_case, expected / subdir, actual / subdir)


class GenConstSvIntegrationTest(unittest.TestCase):
    """Fixture-style CLI coverage for milestone 01."""

    def run_typist(self, repo_dir: Path, cli_arg: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "typist.cli", "gen", cli_arg],
            cwd=repo_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_generates_all_repo_typist_modules(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        expected_root = GOLDENS_DIR / "const_sv_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "constants.py"

            result = self.run_typist(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generated_python_outputs_are_not_rescanned_as_dsl_modules(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        expected_root = GOLDENS_DIR / "const_sv_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "constants.py"

            first_result = self.run_typist(repo_dir, str(cli_file))
            self.assertEqual(first_result.returncode, 0, msg=first_result.stderr)

            second_result = self.run_typist(repo_dir, str(cli_file))
            self.assertEqual(second_result.returncode, 0, msg=second_result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_safe_cpp_types_for_wide_constants(self) -> None:
        fixture_root = FIXTURES_DIR / "const_cpp_wide" / "project"
        expected_root = GOLDENS_DIR / "const_cpp_wide"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "constants.py"

            result = self.run_typist(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_explicit_uint32_constant_when_requested(self) -> None:
        fixture_root = FIXTURES_DIR / "const_cpp_explicit_uint32" / "project"
        expected_root = GOLDENS_DIR / "const_cpp_explicit_uint32"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "constants.py"

            result = self.run_typist(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_const_expressions(self) -> None:
        fixture_root = FIXTURES_DIR / "const_expr_basic" / "project"
        expected_root = GOLDENS_DIR / "const_expr_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "constants.py"

            result = self.run_typist(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_scalar_aliases_in_sv(self) -> None:
        fixture_root = FIXTURES_DIR / "scalar_sv_basic" / "project"
        expected_root = GOLDENS_DIR / "scalar_sv_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "types.py"

            result = self.run_typist(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_structs_in_sv(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_sv_basic" / "project"
        expected_root = GOLDENS_DIR / "struct_sv_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "types.py"

            result = self.run_typist(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_nested_structs_in_sv(self) -> None:
        fixture_root = FIXTURES_DIR / "nested_struct_sv_basic" / "project"
        expected_root = GOLDENS_DIR / "nested_struct_sv_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "types.py"

            result = self.run_typist(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_rejects_typist_file_with_no_dsl_objects(self) -> None:
        fixture_root = FIXTURES_DIR / "no_dsl" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "empty.py"

            result = self.run_typist(repo_dir, str(cli_file))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("defines no DSL objects", result.stderr)

    # -- New positive golden tests for byte-aligned padding --

    def test_generates_struct_padded(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_padded" / "project"
        expected_root = GOLDENS_DIR / "struct_padded"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "types.py"
            result = self.run_typist(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_struct_signed(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_signed" / "project"
        expected_root = GOLDENS_DIR / "struct_signed"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "types.py"
            result = self.run_typist(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_scalar_wide(self) -> None:
        fixture_root = FIXTURES_DIR / "scalar_wide" / "project"
        expected_root = GOLDENS_DIR / "scalar_wide"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "types.py"
            result = self.run_typist(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    def test_generates_struct_wide(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_wide" / "project"
        expected_root = GOLDENS_DIR / "struct_wide"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "types.py"
            result = self.run_typist(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")

    # -- Negative validation tests --

    def test_rejects_pad_suffix_field(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_pad_collision" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "types.py"
            result = self.run_typist(repo_dir, str(cli_file))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reserved '_pad' suffix", result.stderr)

    def test_rejects_signed_scalar_wider_than_64(self) -> None:
        fixture_root = FIXTURES_DIR / "scalar_signed_wide" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "types.py"
            result = self.run_typist(repo_dir, str(cli_file))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exceeds maximum 64-bit signed width", result.stderr)

    def test_rejects_constant_collision_with_generated_identifier(self) -> None:
        fixture_root = FIXTURES_DIR / "const_collision" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "types.py"
            result = self.run_typist(repo_dir, str(cli_file))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("collides with generated identifier", result.stderr)

    def test_rejects_path_outside_typist_directory(self) -> None:
        fixture_root = FIXTURES_DIR / "outside_typist" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "not_typist" / "plain.py"

            result = self.run_typist(repo_dir, str(cli_file))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("is not under a typist/ directory", result.stderr)
