"""Negative and runtime tests for Struct.multiple_of(N)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from typist.dsl import Struct, Logic
from typist.errors import ValidationError


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


class MultipleOfValidationTest(unittest.TestCase):
    """DSL-level negative tests for multiple_of()."""

    def test_multiple_of_zero(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(0)
        self.assertIn("must be positive", str(ctx.exception))

    def test_multiple_of_negative(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(-1)
        self.assertIn("must be positive", str(ctx.exception))

    def test_multiple_of_not_multiple_of_8_val_5(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(5)
        self.assertIn("must be a multiple of 8", str(ctx.exception))

    def test_multiple_of_not_multiple_of_8_val_3(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(3)
        self.assertIn("must be a multiple of 8", str(ctx.exception))

    def test_multiple_of_bool(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(True)
        self.assertIn("must be int", str(ctx.exception))

    def test_multiple_of_twice(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(32).multiple_of(64)
        self.assertIn("already set", str(ctx.exception))

    def test_add_member_after_multiple_of(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(32).add_member("b", Logic(8))
        self.assertIn("cannot add", str(ctx.exception))


def gen_fixture(fixture_name: str, tmp_dir: Path) -> Path:
    """Run typist gen on a fixture and return the gen/py root."""
    fixture_root = FIXTURES_DIR / fixture_name / "project"
    repo_dir = tmp_dir / fixture_name
    shutil.copytree(fixture_root, repo_dir)
    cli_file = repo_dir / "alpha" / "typist" / "types.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    subprocess.run(
        [sys.executable, "-m", "typist.cli", "gen", str(cli_file)],
        cwd=repo_dir,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return repo_dir / "gen" / "py"


class MultipleOfRuntimeTest(unittest.TestCase):
    """Runtime round-trip tests for to_bytes/from_bytes with alignment."""

    _tmp_dir: tempfile.TemporaryDirectory[str]
    _gen_py: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp_dir.name)
        cls._gen_py = gen_fixture("struct_multiple_of", tmp)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp_dir.cleanup()

    def _import_module(self) -> object:
        import importlib
        gen_py = self._gen_py
        for key in list(sys.modules.keys()):
            if key == "alpha" or key.startswith("alpha."):
                del sys.modules[key]
        sys.path[:] = [p for p in sys.path if "gen/py" not in str(p)]
        sys.path.insert(0, str(gen_py))
        return importlib.import_module("alpha.typist.types_types")

    def test_aligned_struct_byte_count(self) -> None:
        mod = self._import_module()
        self.assertEqual(mod.aligned_ct.BYTE_COUNT, 4)
        self.assertEqual(mod.aligned_ct.WIDTH, 17)

    def test_aligned_struct_round_trip(self) -> None:
        mod = self._import_module()
        obj = mod.aligned_ct()
        obj.a = 0x1F
        obj.b = 0xABC
        raw = obj.to_bytes()
        self.assertEqual(len(raw), 4)
        restored = mod.aligned_ct.from_bytes(raw)
        self.assertEqual(restored.a, 0x1F)
        self.assertEqual(restored.b, 0xABC)

    def test_no_extra_pad_byte_count(self) -> None:
        mod = self._import_module()
        self.assertEqual(mod.no_extra_pad_ct.BYTE_COUNT, 3)

    def test_no_extra_pad_round_trip(self) -> None:
        mod = self._import_module()
        obj = mod.no_extra_pad_ct()
        obj.a = 5
        obj.b = 100
        raw = obj.to_bytes()
        self.assertEqual(len(raw), 3)
        restored = mod.no_extra_pad_ct.from_bytes(raw)
        self.assertEqual(restored.a, 5)
        self.assertEqual(restored.b, 100)

    def test_inner_aligned_byte_count(self) -> None:
        mod = self._import_module()
        self.assertEqual(mod.inner_ct.BYTE_COUNT, 2)

    def test_outer_with_nested_aligned_byte_count(self) -> None:
        mod = self._import_module()
        self.assertEqual(mod.outer_ct.BYTE_COUNT, 3)

    def test_outer_nested_round_trip(self) -> None:
        mod = self._import_module()
        obj = mod.outer_ct()
        obj.inner = mod.inner_ct()
        obj.inner.x = 5
        obj.y = 42
        raw = obj.to_bytes()
        self.assertEqual(len(raw), 3)
        restored = mod.outer_ct.from_bytes(raw)
        self.assertEqual(restored.inner.x, 5)
        self.assertEqual(restored.y, 42)


if __name__ == "__main__":
    unittest.main()
