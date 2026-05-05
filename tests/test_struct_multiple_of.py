"""Negative and runtime tests for Struct.multiple_of(N)."""

from __future__ import annotations

import os
import pytest
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from piketype.dsl import Struct, Logic
from piketype.errors import ValidationError


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


class MultipleOfValidationTest:
    """DSL-level negative tests for multiple_of()."""

    def test_multiple_of_zero(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(0)
        assert "must be positive" in str(ctx.value)

    def test_multiple_of_negative(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(-1)
        assert "must be positive" in str(ctx.value)

    def test_multiple_of_not_multiple_of_8_val_5(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(5)
        assert "must be a multiple of 8" in str(ctx.value)

    def test_multiple_of_not_multiple_of_8_val_3(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(3)
        assert "must be a multiple of 8" in str(ctx.value)

    def test_multiple_of_bool(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(True)
        assert "must be int" in str(ctx.value)

    def test_multiple_of_twice(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(32).multiple_of(64)
        assert "already set" in str(ctx.value)

    def test_add_member_after_multiple_of(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            Struct().add_member("a", Logic(8)).multiple_of(32).add_member("b", Logic(8))
        assert "cannot add" in str(ctx.value)


def gen_fixture(fixture_name: str, tmp_dir: Path) -> Path:
    """Run piketype gen on a fixture and return the gen/py root."""
    fixture_root = FIXTURES_DIR / fixture_name / "project"
    repo_dir = tmp_dir / fixture_name
    shutil.copytree(fixture_root, repo_dir)
    cli_file = repo_dir / "alpha" / "piketype" / "types.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    subprocess.run(
        [sys.executable, "-m", "piketype.cli", "gen", str(cli_file)],
        cwd=repo_dir,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return repo_dir


class MultipleOfRuntimeTest:
    """Runtime round-trip tests for to_bytes/from_bytes with alignment."""

    _tmp_dir: tempfile.TemporaryDirectory[str]
    _gen_py: Path

    @classmethod
    def setup_class(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp_dir.name)
        cls._gen_py = gen_fixture("struct_multiple_of", tmp)

    @classmethod
    def teardown_class(cls) -> None:
        cls._tmp_dir.cleanup()

    def _import_module(self) -> object:
        import importlib
        gen_py = self._gen_py
        for key in list(sys.modules.keys()):
            if key == "alpha" or key.startswith("alpha."):
                del sys.modules[key]
        sys.path[:] = [p for p in sys.path if "/py" not in str(p)]
        sys.path.insert(0, str(gen_py))
        return importlib.import_module("alpha.py.types_types")

    def test_aligned_struct_byte_count(self) -> None:
        mod = self._import_module()
        assert mod.aligned_ct.BYTE_COUNT == 4
        assert mod.aligned_ct.WIDTH == 17

    def test_aligned_struct_round_trip(self) -> None:
        mod = self._import_module()
        obj = mod.aligned_ct()
        obj.a = 0x1F
        obj.b = 0xABC
        raw = obj.to_bytes()
        assert len(raw) == 4
        restored = mod.aligned_ct.from_bytes(raw)
        assert restored.a == 0x1F
        assert restored.b == 0xABC

    def test_no_extra_pad_byte_count(self) -> None:
        mod = self._import_module()
        assert mod.no_extra_pad_ct.BYTE_COUNT == 3

    def test_no_extra_pad_round_trip(self) -> None:
        mod = self._import_module()
        obj = mod.no_extra_pad_ct()
        obj.a = 5
        obj.b = 100
        raw = obj.to_bytes()
        assert len(raw) == 3
        restored = mod.no_extra_pad_ct.from_bytes(raw)
        assert restored.a == 5
        assert restored.b == 100

    def test_inner_aligned_byte_count(self) -> None:
        mod = self._import_module()
        assert mod.inner_ct.BYTE_COUNT == 2

    def test_outer_with_nested_aligned_byte_count(self) -> None:
        mod = self._import_module()
        assert mod.outer_ct.BYTE_COUNT == 3

    def test_outer_nested_round_trip(self) -> None:
        mod = self._import_module()
        obj = mod.outer_ct()
        obj.inner = mod.inner_ct()
        obj.inner.x = 5
        obj.y = 42
        raw = obj.to_bytes()
        assert len(raw) == 3
        restored = mod.outer_ct.from_bytes(raw)
        assert restored.inner.x == 5
        assert restored.y == 42
