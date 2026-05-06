"""End-to-end test for use case 4: per-language output directories."""

from __future__ import annotations

import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
GOLDENS_DIR = TESTS_DIR / "goldens" / "gen"

_SKIP_DIRS = {"__pycache__", ".piketype-cache"}


def _assert_trees_equal(expected: Path, actual: Path) -> None:
    comparison = filecmp.dircmp(expected, actual)
    left_only = [n for n in comparison.left_only if n not in _SKIP_DIRS]
    right_only = [n for n in comparison.right_only if n not in _SKIP_DIRS]
    assert not left_only, f"missing: {left_only} (under {expected})"
    assert not right_only, f"unexpected: {right_only} (under {actual})"
    for filename in comparison.common_files:
        expected_text = (expected / filename).read_text(encoding="utf-8")
        actual_text = (actual / filename).read_text(encoding="utf-8")
        assert expected_text == actual_text, f"content mismatch for {expected / filename}"
    for subdir in comparison.common_dirs:
        if subdir in _SKIP_DIRS:
            continue
        _assert_trees_equal(expected / subdir, actual / subdir)


def _run_gen(repo_dir: Path, cli_arg: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "piketype.cli", "gen", cli_arg],
        cwd=repo_dir, env=env, text=True, capture_output=True, check=False,
    )


class MultiRootLayoutTest:
    """Validates per-language output dirs and language_id segment."""

    def test_generates_expected_tree(self) -> None:
        fixture_root = FIXTURES_DIR / "multi_root_layout" / "project"
        expected_root = GOLDENS_DIR / "multi_root_layout"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir)
            cli_file = repo_dir / "dir2" / "piketype" / "c.py"
            result = _run_gen(repo_dir, str(cli_file))
            assert result.returncode == 0, result.stderr
            _assert_trees_equal(expected_root, repo_dir)

    def test_independent_module_d_emitted(self) -> None:
        """dir3/d.py has no deps — its outputs still land under all backends."""
        fixture_root = FIXTURES_DIR / "multi_root_layout" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir)
            cli_file = repo_dir / "dir2" / "piketype" / "c.py"
            result = _run_gen(repo_dir, str(cli_file))
            assert result.returncode == 0, result.stderr
            assert (repo_dir / "python_lib" / "dir3" / "d_types.py").is_file()
            assert (repo_dir / "includes" / "dir3" / "cpp" / "d_types.hpp").is_file()
            assert (repo_dir / "dir3" / "rtl" / "d_pkg.sv").is_file()

    def test_language_id_segment_inserted_for_cpp(self) -> None:
        """`language_id: cpp` for cpp inserts a `cpp/` directory segment."""
        fixture_root = FIXTURES_DIR / "multi_root_layout" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir)
            cli_file = repo_dir / "dir0" / "piketype" / "a.py"
            result = _run_gen(repo_dir, str(cli_file))
            assert result.returncode == 0, result.stderr
            # cpp has language_id=cpp → includes/dir0/cpp/a_types.hpp
            assert (repo_dir / "includes" / "dir0" / "cpp" / "a_types.hpp").is_file()
            # py has language_id="" → python_lib/dir0/a_types.py (no `py/` segment)
            assert (repo_dir / "python_lib" / "dir0" / "a_types.py").is_file()
            assert not (repo_dir / "python_lib" / "dir0" / "py" / "a_types.py").exists()

    def test_cross_prefix_python_import_uses_dotted_path(self) -> None:
        """Cross-prefix Python emits ``from <sub>.<base>_types import ...``."""
        fixture_root = FIXTURES_DIR / "multi_root_layout" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir)
            cli_file = repo_dir / "dir1" / "piketype" / "b.py"
            result = _run_gen(repo_dir, str(cli_file))
            assert result.returncode == 0, result.stderr
            # b imports a from dir0; emitted file should reference dir0.a_types.
            text = (repo_dir / "python_lib" / "dir1" / "b_types.py").read_text(encoding="utf-8")
            assert "from dir0.a_types import" in text
