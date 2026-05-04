"""Executable Python runtime tests for to_bytes/from_bytes with spec-derived test vectors."""

from __future__ import annotations

import os
import pytest
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


def gen_fixture(fixture_name: str, tmp_dir: Path) -> Path:
    """Run piketype gen on a fixture and return the gen/py root."""
    fixture_root = FIXTURES_DIR / fixture_name / "project"
    repo_dir = tmp_dir / fixture_name
    shutil.copytree(fixture_root, repo_dir)
    cli_file = repo_dir / "alpha" / "piketype" / "types.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "piketype.cli", "gen", str(cli_file)],
        cwd=repo_dir,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return repo_dir


class RuntimeBytesTest:
    """Executable runtime tests for to_bytes/from_bytes."""

    _tmp_dir: tempfile.TemporaryDirectory[str]
    _gen_roots: dict[str, Path]

    @classmethod
    def setup_class(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp_dir.name)
        cls._gen_roots = {}
        for fixture_name in ("struct_padded", "struct_signed", "scalar_wide",
                             "struct_wide", "nested_struct_sv_basic", "scalar_sv_basic"):
            cls._gen_roots[fixture_name] = gen_fixture(fixture_name, tmp)

    @classmethod
    def teardown_class(cls) -> None:
        cls._tmp_dir.cleanup()

    def _import_module(self, fixture_name: str) -> object:
        """Import the generated Python types module for a fixture."""
        gen_py = self._gen_roots[fixture_name]
        import importlib
        # Clear all cached alpha.* modules so reimport works
        for key in list(sys.modules.keys()):
            if key == "alpha" or key.startswith("alpha."):
                del sys.modules[key]
        # Remove old gen/py paths from sys.path
        sys.path[:] = [p for p in sys.path if "/py" not in str(p)]
        sys.path.insert(0, str(gen_py))
        return importlib.import_module("alpha.py.types_types")

    # -- AC-6: bar_t to_bytes produces {0x01, 0x1F, 0xFF, 0x0A, 0x00} --

    def test_struct_padded_to_bytes(self) -> None:
        mod = self._import_module("struct_padded")
        bar = mod.bar_ct(flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0)
        assert bar.to_bytes() == b"\x01\x1f\xff\x0a\x00"

    # -- AC-12: from_bytes with nonzero unsigned padding accepted --

    def test_struct_padded_from_bytes_nonzero_padding(self) -> None:
        mod = self._import_module("struct_padded")
        bar1 = mod.bar_ct.from_bytes(b"\x01\x1f\xff\x0a\x00")
        bar2 = mod.bar_ct.from_bytes(b"\x81\x1f\xff\x0a\x00")
        assert bar1.flag_a == bar2.flag_a
        assert bar1.field_1 == bar2.field_1
        assert bar1.status == bar2.status
        assert bar1.flag_b == bar2.flag_b

    # -- AC-15: 13-bit unsigned from_bytes masks padding --

    def test_scalar_13bit_from_bytes_masks_padding(self) -> None:
        mod = self._import_module("struct_padded")
        foo = mod.foo_ct.from_bytes(b"\xff\xff")
        assert foo.value == 0x1FFF

    # -- AC-16: signed 5-bit to_bytes/from_bytes --

    def test_signed_5bit_negative(self) -> None:
        mod = self._import_module("struct_signed")
        s5 = mod.signed_5_ct(-1)
        assert s5.to_bytes() == b"\xff"
        rt = mod.signed_5_ct.from_bytes(b"\xff")
        assert rt.value == -1

    def test_signed_5bit_positive(self) -> None:
        mod = self._import_module("struct_signed")
        s5 = mod.signed_5_ct(5)
        assert s5.to_bytes() == b"\x05"
        rt = mod.signed_5_ct.from_bytes(b"\x05")
        assert rt.value == 5

    # -- AC-22: signed 4-bit struct member to_bytes --

    def test_signed_4bit_struct_member(self) -> None:
        mod = self._import_module("struct_signed")
        obj = mod.mixed_ct(field_s=-6, field_u=-1)
        raw = obj.to_bytes()
        assert raw[0] == 0xFA

    # -- AC-23: from_bytes with mismatched signed padding raises error --

    def test_signed_4bit_from_bytes_padding_mismatch(self) -> None:
        mod = self._import_module("struct_signed")
        with pytest.raises(ValueError):
            mod.signed_4_ct.from_bytes(b"\x0a")

    def test_signed_5bit_from_bytes_padding_mismatch(self) -> None:
        mod = self._import_module("struct_signed")
        with pytest.raises(ValueError):
            mod.signed_5_ct.from_bytes(b"\x1f")

    # -- AC-24: 65-bit unsigned round-trip --

    def test_wide_65bit_to_bytes(self) -> None:
        mod = self._import_module("scalar_wide")
        w = mod.wide_ct(0x1_FFFF_FFFF_FFFF_FFFF)
        expected = b"\x01" + b"\xff" * 8
        assert w.to_bytes() == expected

    def test_wide_65bit_from_bytes_masks_padding(self) -> None:
        mod = self._import_module("scalar_wide")
        w = mod.wide_ct.from_bytes(b"\xff" * 9)
        # Wide scalar stores value as bytes; padding masked in MSB byte
        assert w.value == b"\x01" + b"\xff" * 8

    # -- AC-25: struct with 65-bit member + 1-bit flag --

    def test_struct_wide_to_bytes(self) -> None:
        mod = self._import_module("struct_wide")
        obj = mod.big_ct()
        obj.data = b"\x01" + b"\xff" * 8
        obj.flag = 1
        obj.extra = b"\x00" * 16
        raw = obj.to_bytes()
        assert len(raw) == 9 + 1 + 16
        assert raw[:9] == b"\x01" + b"\xff" * 8
        assert raw[9] == 0x01

    # -- AC-7: nested struct --

    def test_nested_struct_to_bytes(self) -> None:
        mod = self._import_module("nested_struct_sv_basic")
        header = mod.header_ct(addr=0x1FFF, enable=1)
        pkt = mod.packet_ct()
        pkt.header = header
        pkt.mode = 0
        pkt.error_code = 0
        raw = pkt.to_bytes()
        header_bytes = header.to_bytes()
        assert raw[:len(header_bytes)] == header_bytes
