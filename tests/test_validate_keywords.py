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
import unittest

from tests.test_gen_const_sv import (
    FIXTURES_DIR,
    GOLDENS_DIR,
    PROJECT_ROOT,
    assert_trees_equal,
    copy_tree,
)


class KeywordValidationTest(unittest.TestCase):
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
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            assert_trees_equal(self, expected_root, repo_dir / "gen")
