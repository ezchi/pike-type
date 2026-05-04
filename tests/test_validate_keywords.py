"""Integration tests for reserved-keyword validation (FR-1..FR-9).

Each test copies a fixture under ``tests/fixtures/keyword_*/project/`` to a
temp directory and invokes ``piketype gen`` as a subprocess. Negative tests
assert non-zero exit and a stable substring of the FR-3 normative error
message in stderr. Positive tests assert clean exit and a byte-for-byte
match against the corresponding golden tree.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile

from tests.test_gen_const_sv import (
    FIXTURES_DIR,
    GOLDENS_DIR,
    PROJECT_ROOT,
    assert_trees_equal,
    copy_tree,
)


class KeywordValidationTest:
    """End-to-end CLI tests for the reserved-keyword validator."""

    def run_piketype(
        self,
        repo_dir: Path,
        cli_arg: str,
        *extra_args: str,
    ) -> subprocess.CompletedProcess[str]:
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

    # -- Positive tests -----------------------------------------------------

    def test_keyword_near_miss_type_id_passes(self) -> None:
        """AC-7: a struct field whose name contains a keyword as a substring
        (here ``type_id``) is accepted; only exact-token matches are rejected."""
        fixture_root = FIXTURES_DIR / "keyword_near_miss" / "project"
        expected_root = GOLDENS_DIR / "keyword_near_miss"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            assert result.returncode == 0, result.stderr
            assert_trees_equal(self, expected_root, repo_dir)

    def test_module_name_logic_is_accepted(self) -> None:
        """AC-4b: module file ``logic.py`` produces SV ``logic_pkg`` (not a
        keyword) and bare ``logic`` for C++/Python (not keywords either).
        Validation accepts."""
        fixture_root = FIXTURES_DIR / "keyword_module_name_logic_passes" / "project"
        expected_root = GOLDENS_DIR / "keyword_module_name_logic_passes"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "logic.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            assert result.returncode == 0, result.stderr
            assert_trees_equal(self, expected_root, repo_dir)

    def test_type_name_class_t_is_accepted(self) -> None:
        """AC-2: ``class_t`` (full type name) is not a keyword; the base form
        ``class`` is never emitted standalone (only as substring of
        ``pack_class``, ``LP_CLASS_WIDTH``, ``class_ct``). Validation accepts."""
        fixture_root = FIXTURES_DIR / "keyword_type_name_class_t_passes" / "project"
        expected_root = GOLDENS_DIR / "keyword_type_name_class_t_passes"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            assert result.returncode == 0, result.stderr
            assert_trees_equal(self, expected_root, repo_dir)

    def test_enum_value_while_is_accepted(self) -> None:
        """AC-3: exact-case keyword matching — ``WHILE`` (uppercase) is not the
        keyword ``while`` (lowercase) in any of the three target languages."""
        fixture_root = FIXTURES_DIR / "keyword_enum_value_while_passes" / "project"
        expected_root = GOLDENS_DIR / "keyword_enum_value_while_passes"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            assert result.returncode == 0, result.stderr
            assert_trees_equal(self, expected_root, repo_dir)

    # -- Negative tests -----------------------------------------------------

    def test_struct_field_type_is_rejected(self) -> None:
        """AC-1: struct field named ``type`` collides with SystemVerilog and
        Python (soft); generation must be aborted."""
        fixture_root = FIXTURES_DIR / "keyword_struct_field_type" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            assert result.returncode != 0
            assert (
                "field 'type' is a reserved keyword in target language(s): "
                "Python (soft), SystemVerilog"
            ) in result.stderr

    def test_flags_field_try_is_rejected(self) -> None:
        """AC-6: flags field named ``try`` collides with C++ and Python."""
        fixture_root = FIXTURES_DIR / "keyword_flags_field_try" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            assert result.returncode != 0
            assert (
                "flag 'try' is a reserved keyword in target language(s): "
                "C++, Python"
            ) in result.stderr

    def test_constant_for_is_rejected(self) -> None:
        """AC-5: constant ``for`` collides with C++, Python, and SystemVerilog."""
        fixture_root = FIXTURES_DIR / "keyword_constant_for" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            assert result.returncode != 0
            assert (
                "constant 'for' is a reserved keyword in target language(s): "
                "C++, Python, SystemVerilog"
            ) in result.stderr

    def test_module_name_class_is_rejected(self) -> None:
        """AC-4: module file ``class.py`` emits C++ namespace ``class`` and
        Python module ``class`` (both keywords); SV form ``class_pkg`` is not
        a keyword so SV is not in the language list."""
        fixture_root = FIXTURES_DIR / "keyword_module_name_class" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "class.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            assert result.returncode != 0
            assert (
                "module name 'class' is a reserved keyword in target language(s): "
                "C++, Python"
            ) in result.stderr

    def test_uppercase_check_fires_before_keyword_check(self) -> None:
        """AC-11: a lowercase enum value (here ``for``) violates the
        UPPER_CASE structural rule, which must fire before the keyword check.
        The error reports the structural defect, not the keyword collision."""
        fixture_root = FIXTURES_DIR / "keyword_enum_ordering_for" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            copy_tree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self.run_piketype(repo_dir, str(cli_file))
            assert result.returncode != 0
            assert "UPPER_CASE" in result.stderr
            assert "reserved keyword" not in result.stderr
