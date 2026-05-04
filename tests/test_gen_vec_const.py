"""Integration tests for VecConst SV emission and cross-module imports."""

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


def _copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _assert_trees_equal(test_case: unittest.TestCase, expected: Path, actual: Path) -> None:
    _SKIP_DIRS = {"__pycache__"}
    _SKIP_SUFFIXES = (".pyc",)
    comparison = filecmp.dircmp(expected, actual)
    left_only = [n for n in comparison.left_only if n not in _SKIP_DIRS and not n.endswith(_SKIP_SUFFIXES)]
    right_only = [n for n in comparison.right_only if n not in _SKIP_DIRS and not n.endswith(_SKIP_SUFFIXES)]
    test_case.assertFalse(left_only, f"missing generated files: {left_only}")
    test_case.assertFalse(right_only, f"unexpected generated files: {right_only}")
    test_case.assertFalse(comparison.funny_files, f"uncomparable files: {comparison.funny_files}")
    for filename in comparison.common_files:
        if filename.endswith(_SKIP_SUFFIXES):
            continue
        expected_text = (expected / filename).read_text(encoding="utf-8")
        actual_text = (actual / filename).read_text(encoding="utf-8")
        test_case.assertEqual(expected_text, actual_text, f"content mismatch for {filename}")
    for subdir in comparison.common_dirs:
        if subdir in _SKIP_DIRS:
            continue
        _assert_trees_equal(test_case, expected / subdir, actual / subdir)


class GenVecConstIntegrationTest(unittest.TestCase):
    """Fixture-style CLI coverage for VecConst (spec 016)."""

    def _run_piketype_gen(self, repo_dir: Path, *cli_args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "piketype.cli", "gen", *cli_args],
            cwd=repo_dir,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_vec_const_basic_generates_expected_tree(self) -> None:
        """AC-1, AC-2, AC-3, AC-9, AC-10 — basic VecConst rendering."""
        fixture_root = FIXTURES_DIR / "vec_const_basic" / "project"
        expected_root = GOLDENS_DIR / "vec_const_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "repo"
            _copy_tree(fixture_root, repo_dir)
            result = self._run_piketype_gen(repo_dir, "alpha/piketype/vecs.py")
            self.assertEqual(result.returncode, 0, f"piketype gen failed: {result.stderr}")
            _assert_trees_equal(self, expected_root, repo_dir)

    def test_vec_const_cross_module_emits_per_symbol_import(self) -> None:
        """AC-11 — module b's synth pkg contains `import a_pkg::LP_X;`."""
        fixture_root = FIXTURES_DIR / "vec_const_cross_module" / "project"
        expected_root = GOLDENS_DIR / "vec_const_cross_module"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "repo"
            _copy_tree(fixture_root, repo_dir)
            result = self._run_piketype_gen(repo_dir, "alpha/piketype/a.py")
            self.assertEqual(result.returncode, 0, f"piketype gen failed: {result.stderr}")
            _assert_trees_equal(self, expected_root, repo_dir)
            b_pkg_text = (repo_dir / "alpha" / "rtl" / "b_pkg.sv").read_text()
            self.assertIn("import a_pkg::LP_X;", b_pkg_text)


if __name__ == "__main__":
    unittest.main()
