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
    _SKIP_DIRS = {"__pycache__"}
    _SKIP_FILE_SUFFIXES = (".pyc",)
    comparison = filecmp.dircmp(expected, actual)
    left_only = [n for n in comparison.left_only if n not in _SKIP_DIRS and not n.endswith(_SKIP_FILE_SUFFIXES)]
    right_only = [n for n in comparison.right_only if n not in _SKIP_DIRS and not n.endswith(_SKIP_FILE_SUFFIXES)]
    test_case.assertFalse(left_only, f"missing generated files: {left_only}")
    test_case.assertFalse(right_only, f"unexpected generated files: {right_only}")
    test_case.assertFalse(comparison.funny_files, f"uncomparable files: {comparison.funny_files}")

    for filename in comparison.common_files:
        if filename.endswith(_SKIP_FILE_SUFFIXES):
            continue
        expected_text = (expected / filename).read_text(encoding="utf-8")
        actual_text = (actual / filename).read_text(encoding="utf-8")
        test_case.assertEqual(expected_text, actual_text, f"content mismatch for {filename}")

    for subdir in comparison.common_dirs:
        if subdir in _SKIP_DIRS:
            continue
        assert_trees_equal(test_case, expected / subdir, actual / subdir)


class GenConstSvIntegrationTest(unittest.TestCase):
    """Fixture-style CLI coverage for milestone 01."""

    def run_piketype(self, repo_dir: Path, cli_arg: str, *extra_args: str) -> subprocess.CompletedProcess[str]:
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

    def test_generates_all_repo_piketype_modules(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        expected_root = GOLDENS_DIR / "const_sv_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"

            result = self.run_piketype(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_generated_python_outputs_are_not_rescanned_as_dsl_modules(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        expected_root = GOLDENS_DIR / "const_sv_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"

            first_result = self.run_piketype(repo_dir, str(cli_file))
            self.assertEqual(first_result.returncode, 0, msg=first_result.stderr)

            second_result = self.run_piketype(repo_dir, str(cli_file))
            self.assertEqual(second_result.returncode, 0, msg=second_result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_generates_safe_cpp_types_for_wide_constants(self) -> None:
        fixture_root = FIXTURES_DIR / "const_cpp_wide" / "project"
        expected_root = GOLDENS_DIR / "const_cpp_wide"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"

            result = self.run_piketype(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_generates_explicit_uint32_constant_when_requested(self) -> None:
        fixture_root = FIXTURES_DIR / "const_cpp_explicit_uint32" / "project"
        expected_root = GOLDENS_DIR / "const_cpp_explicit_uint32"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"

            result = self.run_piketype(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_generates_const_expressions(self) -> None:
        fixture_root = FIXTURES_DIR / "const_expr_basic" / "project"
        expected_root = GOLDENS_DIR / "const_expr_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"

            result = self.run_piketype(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_generates_scalar_aliases_in_sv(self) -> None:
        fixture_root = FIXTURES_DIR / "scalar_sv_basic" / "project"
        expected_root = GOLDENS_DIR / "scalar_sv_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"

            result = self.run_piketype(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_generates_structs_in_sv(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_sv_basic" / "project"
        expected_root = GOLDENS_DIR / "struct_sv_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"

            result = self.run_piketype(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_generates_nested_structs_in_sv(self) -> None:
        fixture_root = FIXTURES_DIR / "nested_struct_sv_basic" / "project"
        expected_root = GOLDENS_DIR / "nested_struct_sv_basic"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"

            result = self.run_piketype(repo_dir, str(cli_file))

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_rejects_piketype_file_with_no_dsl_objects(self) -> None:
        fixture_root = FIXTURES_DIR / "no_dsl" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "empty.py"

            result = self.run_piketype(repo_dir, str(cli_file))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("defines no DSL objects", result.stderr)

    # -- New positive golden tests for byte-aligned padding --

    def test_generates_struct_padded(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_padded" / "project"
        expected_root = GOLDENS_DIR / "struct_padded"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_generates_struct_signed(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_signed" / "project"
        expected_root = GOLDENS_DIR / "struct_signed"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_generates_scalar_wide(self) -> None:
        fixture_root = FIXTURES_DIR / "scalar_wide" / "project"
        expected_root = GOLDENS_DIR / "scalar_wide"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_generates_struct_wide(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_wide" / "project"
        expected_root = GOLDENS_DIR / "struct_wide"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_generates_struct_multiple_of(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_multiple_of" / "project"
        expected_root = GOLDENS_DIR / "struct_multiple_of"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    # -- Negative validation tests --

    def test_rejects_pad_suffix_field(self) -> None:
        fixture_root = FIXTURES_DIR / "struct_pad_collision" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reserved '_pad' suffix", result.stderr)

    def test_rejects_signed_scalar_wider_than_64(self) -> None:
        fixture_root = FIXTURES_DIR / "scalar_signed_wide" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exceeds maximum 64-bit signed width", result.stderr)

    def test_rejects_constant_collision_with_generated_identifier(self) -> None:
        fixture_root = FIXTURES_DIR / "const_collision" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("collides with generated identifier", result.stderr)

    def test_rejects_path_outside_piketype_directory(self) -> None:
        fixture_root = FIXTURES_DIR / "outside_piketype" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "not_piketype" / "plain.py"

            result = self.run_piketype(repo_dir, str(cli_file))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must be at <prefix>/piketype/<name>.py", result.stderr)

    # -- Namespace override tests --

    def test_namespace_override_multi_module(self) -> None:
        fixture_root = FIXTURES_DIR / "namespace_override" / "project"
        expected_root = GOLDENS_DIR / "namespace_override"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"
            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::bar")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir)

    def test_namespace_rejects_empty_segment(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"
            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::::bar")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("empty segment", result.stderr)

    def test_namespace_rejects_non_identifier(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"
            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "123bad")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not a valid C++ identifier", result.stderr)

    def test_namespace_rejects_cpp_keyword(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"
            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "class")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("C++ keyword", result.stderr)

    def test_namespace_rejects_double_underscore(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"
            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo__bar")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("'__'", result.stderr)

    def test_namespace_rejects_leading_underscore(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"
            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "_foo")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("underscore", result.stderr)

    def test_namespace_rejects_std_first_segment(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"
            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "std::types")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("'std'", result.stderr)

    def test_namespace_rejects_trailing_underscore(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"
            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo_")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("underscore", result.stderr)

    def test_namespace_rejects_leading_underscore_non_first(self) -> None:
        fixture_root = FIXTURES_DIR / "const_sv_basic" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "constants.py"
            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::_bar")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("underscore", result.stderr)

    def test_namespace_rejects_duplicate_basenames(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            repo_dir.mkdir()
            (repo_dir / ".git").mkdir()
            (repo_dir / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
            (repo_dir / "alpha" / "piketype").mkdir(parents=True)
            (repo_dir / "beta" / "piketype").mkdir(parents=True)
            (repo_dir / "alpha" / "piketype" / "types.py").write_text(
                "from piketype.dsl import Const\nX = Const(1)\n"
            )
            (repo_dir / "beta" / "piketype" / "types.py").write_text(
                "from piketype.dsl import Const\nY = Const(2)\n"
            )
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file), "--namespace", "foo::bar")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("types", result.stderr)
            self.assertIn("duplicate", result.stderr.lower())
