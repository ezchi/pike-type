"""Integration tests for spec 011 cross-module type references."""

from __future__ import annotations

import filecmp
import os
import re
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


def _assert_trees_equal(_unused: object, expected: Path, actual: Path) -> None:
    """Compare two directory trees byte-for-byte (recursive)."""
    comparison = filecmp.dircmp(expected, actual)
    left_only = [n for n in comparison.left_only if n not in _SKIP_DIRS]
    right_only = [n for n in comparison.right_only if n not in _SKIP_DIRS]
    assert not left_only, f"missing generated files: {left_only}"
    assert not right_only, f"unexpected generated files: {right_only}"
    assert not comparison.funny_files, f"uncomparable files: {comparison.funny_files}"
    for filename in comparison.common_files:
        expected_text = (expected / filename).read_text(encoding="utf-8")
        actual_text = (actual / filename).read_text(encoding="utf-8")
        assert expected_text == actual_text, f"content mismatch for {filename}"
    for subdir in comparison.common_dirs:
        if subdir in _SKIP_DIRS:
            continue
        _assert_trees_equal(None, expected / subdir, actual / subdir)


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


class CrossModuleTypeRefsIntegrationTest:
    """End-to-end fixture comparison for cross_module_type_refs."""

    def test_generates_expected_outputs(self) -> None:
        fixture_root = FIXTURES_DIR / "cross_module_type_refs" / "project"
        expected_root = GOLDENS_DIR / "cross_module_type_refs"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir, dirs_exist_ok=True)
            cli_file = repo_dir / "alpha" / "piketype" / "bar.py"
            result = _run_piketype(repo_dir=repo_dir, cli_arg=str(cli_file))
            assert result.returncode == 0, result.stderr
            _assert_trees_equal(self, expected_root, repo_dir)

    def test_idempotent(self) -> None:
        fixture_root = FIXTURES_DIR / "cross_module_type_refs" / "project"
        expected_root = GOLDENS_DIR / "cross_module_type_refs"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir, dirs_exist_ok=True)
            cli_file = repo_dir / "alpha" / "piketype" / "bar.py"
            r1 = _run_piketype(repo_dir=repo_dir, cli_arg=str(cli_file))
            assert r1.returncode == 0, r1.stderr
            r2 = _run_piketype(repo_dir=repo_dir, cli_arg=str(cli_file))
            assert r2.returncode == 0, r2.stderr
            _assert_trees_equal(self, expected_root, repo_dir)

    def test_bar_pkg_uses_cross_module_byte_t(self) -> None:
        """AC-2, AC-3: explicit per-symbol imports for cross-module type refs."""
        bar_pkg_path = GOLDENS_DIR / "cross_module_type_refs" / "alpha" / "rtl" / "bar_pkg.sv"
        text = bar_pkg_path.read_text(encoding="utf-8")
        # AC-2: explicit per-symbol imports (no wildcard) for the byte_t bundle.
        assert "import foo_pkg::*;" not in text
        for sym in ("byte_t", "LP_BYTE_WIDTH", "pack_byte", "unpack_byte"):
            assert f"import foo_pkg::{sym};" in text
        # AC-3: typedef uses byte_t (not logic [7:0]) for both fields.
        assert "byte_t field1;" in text
        assert "byte_t field2;" in text
        assert "logic [7:0] field1" not in text
        assert "logic [7:0] field2" not in text
        # unpack uses LP_BYTE_WIDTH and unpack_byte by unqualified name.
        assert "LP_BYTE_WIDTH" in text
        assert "unpack_byte(" in text


class CrossModuleNamespaceIntegrationTest:
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
            assert result.returncode == 0, result.stderr
            _assert_trees_equal(self, expected_root, repo_dir)

    def test_bar_types_hpp_uses_qualified_byte(self) -> None:
        """AC-6: with --namespace=proj::lib, cross-module field types render the
        shortest unambiguous qualifier (sibling-namespace lookup)."""
        bar_hpp = GOLDENS_DIR / "cross_module_type_refs_namespace_proj" / "cpp" / "alpha" / "bar_types.hpp"
        text = bar_hpp.read_text(encoding="utf-8")
        # Inside namespace proj::lib::bar, foo::Byte resolves to proj::lib::foo::Byte
        # via sibling-namespace lookup. clang-format may pad the gap between
        # type and identifier for AlignConsecutiveDeclarations, so match flexibly.
        assert re.search(r"foo::Byte\s+field1\b", text)
        assert re.search(r"foo::Byte\s+field2\b", text)
        # The include path is unaffected by --namespace.
        assert '#include "alpha/piketype/foo_types.hpp"' in text


class CrossModuleStructMultipleOfIntegrationTest:
    """AC-18 / FR-3: cross-module struct member with multiple_of() trailing alignment."""

    def test_generates_expected_outputs(self) -> None:
        fixture_root = FIXTURES_DIR / "cross_module_struct_multiple_of" / "project"
        expected_root = GOLDENS_DIR / "cross_module_struct_multiple_of"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir, dirs_exist_ok=True)
            cli_file = repo_dir / "alpha" / "piketype" / "bar.py"
            result = _run_piketype(repo_dir=repo_dir, cli_arg=str(cli_file))
            assert result.returncode == 0, result.stderr
            _assert_trees_equal(self, expected_root, repo_dir)

    def test_bar_pkg_alignment_byte_count(self) -> None:
        """Three byte_t fields = 24 data bits; multiple_of(32) → 4-byte total."""
        bar_pkg = GOLDENS_DIR / "cross_module_struct_multiple_of" / "alpha" / "rtl" / "bar_pkg.sv"
        text = bar_pkg.read_text(encoding="utf-8")
        assert "LP_BAR_WIDTH = 24;" in text
        assert "LP_BAR_BYTE_COUNT = 4;" in text
        assert "_align_pad" in text
