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

    def test_rejects_typist_file_with_no_dsl_objects(self) -> None:
        fixture_root = FIXTURES_DIR / "no_dsl" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "typist" / "empty.py"

            result = self.run_typist(repo_dir, str(cli_file))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("defines no DSL objects", result.stderr)

    def test_rejects_path_outside_typist_directory(self) -> None:
        fixture_root = FIXTURES_DIR / "outside_typist" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "not_typist" / "plain.py"

            result = self.run_typist(repo_dir, str(cli_file))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("is not under a typist/ directory", result.stderr)
