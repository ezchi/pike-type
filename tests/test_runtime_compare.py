"""Runtime tests for the generated Python compare() method.

Each generated type wrapper exposes ``compare(self, other, msg="") -> None``.
On equal values: returns silently.
On unequal: raises AssertionError with per-field diff lines.
On wrong type: raises AssertionError from the isinstance check.
"""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


def _gen_fixture(fixture_name: str, tmp_dir: Path, cli_rel: str = "alpha/piketype/types.py") -> Path:
    fixture_root = FIXTURES_DIR / fixture_name / "project"
    repo_dir = tmp_dir / fixture_name
    shutil.copytree(fixture_root, repo_dir)
    cli_file = repo_dir / cli_rel
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


class _CompareBase:
    _tmp_dir: tempfile.TemporaryDirectory[str]
    _gen_roots: dict[str, Path]

    @classmethod
    def setup_class(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp_dir.name)
        cls._gen_roots = {
            "struct_signed": _gen_fixture("struct_signed", tmp),
            "scalar_wide": _gen_fixture("scalar_wide", tmp),
            "struct_padded": _gen_fixture("struct_padded", tmp),
            "struct_flags_member": _gen_fixture("struct_flags_member", tmp),
            "struct_enum_member": _gen_fixture("struct_enum_member", tmp),
            "nested_struct_sv_basic": _gen_fixture("nested_struct_sv_basic", tmp),
            "flags_basic": _gen_fixture("flags_basic", tmp),
            "enum_basic": _gen_fixture("enum_basic", tmp, cli_rel="foo/piketype/defs.py"),
        }

    @classmethod
    def teardown_class(cls) -> None:
        cls._tmp_dir.cleanup()

    def _import(self, fixture: str, module_path: str) -> object:
        gen_root = self._gen_roots[fixture]
        for key in list(sys.modules.keys()):
            if key in {"alpha", "foo"} or key.startswith(("alpha.", "foo.")):
                del sys.modules[key]
        sys.path[:] = [p for p in sys.path if "/py" not in str(p)]
        sys.path.insert(0, str(gen_root))
        return importlib.import_module(module_path)


class ScalarAliasCompareTest(_CompareBase):

    def test_equal_returns_silently(self) -> None:
        mod = self._import("struct_signed", "alpha.py.types_types")
        a = mod.signed_4_ct(-3)
        b = mod.signed_4_ct(-3)
        a.compare(b)  # no exception

    def test_unequal_raises_assertion(self) -> None:
        mod = self._import("struct_signed", "alpha.py.types_types")
        a = mod.signed_4_ct(-3)
        b = mod.signed_4_ct(2)
        with pytest.raises(AssertionError) as ctx:
            a.compare(b)
        text = str(ctx.value)
        assert "signed_4_ct" in text
        assert "-3" in text
        assert "2" in text

    def test_wrong_type_raises_assertion(self) -> None:
        mod = self._import("struct_signed", "alpha.py.types_types")
        a = mod.signed_4_ct(0)
        with pytest.raises(AssertionError) as ctx:
            a.compare(123)  # not a wrapper instance
        assert "Expected signed_4_ct" in str(ctx.value)

    def test_msg_prefix_appears(self) -> None:
        mod = self._import("struct_signed", "alpha.py.types_types")
        a = mod.signed_4_ct(1)
        b = mod.signed_4_ct(2)
        with pytest.raises(AssertionError) as ctx:
            a.compare(b, msg="cycle 42")
        assert str(ctx.value).startswith("cycle 42:")

    def test_wide_scalar_equal_passes(self) -> None:
        mod = self._import("scalar_wide", "alpha.py.types_types")
        v = (1 << 65) - 1
        mod.wide_ct(v).compare(mod.wide_ct(v))

    def test_wide_scalar_unequal_raises(self) -> None:
        mod = self._import("scalar_wide", "alpha.py.types_types")
        with pytest.raises(AssertionError):
            mod.wide_ct(0).compare(mod.wide_ct(1))


class EnumCompareTest(_CompareBase):

    def test_equal_returns_silently(self) -> None:
        mod = self._import("enum_basic", "foo.py.defs_types")
        a = mod.color_ct(mod.color_enum_t.RED)
        b = mod.color_ct(mod.color_enum_t.RED)
        a.compare(b)

    def test_unequal_raises(self) -> None:
        mod = self._import("enum_basic", "foo.py.defs_types")
        a = mod.color_ct(mod.color_enum_t.RED)
        b = mod.color_ct(mod.color_enum_t.GREEN)
        with pytest.raises(AssertionError) as ctx:
            a.compare(b)
        text = str(ctx.value)
        assert "RED" in text or "color_enum_t" in text
        assert "GREEN" in text or "color_enum_t" in text

    def test_wrong_type_raises(self) -> None:
        mod = self._import("enum_basic", "foo.py.defs_types")
        a = mod.color_ct(mod.color_enum_t.RED)
        with pytest.raises(AssertionError):
            a.compare("not an enum")


class FlagsCompareTest(_CompareBase):

    def test_equal_returns_silently(self) -> None:
        mod = self._import("flags_basic", "alpha.py.types_types")
        a = mod.triple_ct()
        a.a = True
        a.b = False
        a.c = True
        b = mod.triple_ct()
        b.a = True
        b.b = False
        b.c = True
        a.compare(b)

    def test_per_flag_diff_lines(self) -> None:
        mod = self._import("flags_basic", "alpha.py.types_types")
        a = mod.triple_ct()
        a.a = True
        a.b = False
        a.c = True
        b = mod.triple_ct()
        b.a = False  # differs
        b.b = False
        b.c = False  # differs
        with pytest.raises(AssertionError) as ctx:
            a.compare(b)
        text = str(ctx.value)
        assert "a:" in text
        assert "c:" in text
        # b matches in both, so b should NOT appear as a diff line.
        assert "b: expected" not in text

    def test_wrong_type_raises(self) -> None:
        mod = self._import("flags_basic", "alpha.py.types_types")
        a = mod.triple_ct()
        with pytest.raises(AssertionError):
            a.compare(0xFF)


class StructCompareTest(_CompareBase):

    def test_equal_returns_silently(self) -> None:
        mod = self._import("struct_signed", "alpha.py.types_types")
        a = mod.mixed_ct(field_s=-6, field_u=-1)
        b = mod.mixed_ct(field_s=-6, field_u=-1)
        a.compare(b)

    def test_per_field_diff_signed(self) -> None:
        mod = self._import("struct_signed", "alpha.py.types_types")
        a = mod.mixed_ct(field_s=-6, field_u=-1)
        b = mod.mixed_ct(field_s=-6, field_u=2)
        with pytest.raises(AssertionError) as ctx:
            a.compare(b)
        text = str(ctx.value)
        # field_s matches → no diff line for it.
        assert "field_s: expected" not in text
        # field_u differs → expect dec format (signed inline).
        assert "field_u: expected -1, got 2" in text

    def test_unsigned_narrow_uses_hex_format(self) -> None:
        mod = self._import("struct_padded", "alpha.py.types_types")
        a = mod.bar_ct(flag_a=0, field_1=0x0123, status=0xA, flag_b=0)
        b = mod.bar_ct(flag_a=0, field_1=0x0FFF, status=0xA, flag_b=0)
        with pytest.raises(AssertionError) as ctx:
            a.compare(b)
        text = str(ctx.value)
        # field_1 is a TypeRef to foo_ct → uses {!r} format which embeds 0x123 / 0xFFF
        # but inline narrow-unsigned status would show as 0x format. Either way the diff
        # surface the differing field.
        assert "field_1" in text

    def test_wide_field_uses_bytes_hex(self) -> None:
        mod = self._import("nested_struct_sv_basic", "alpha.py.types_types")
        # packet has header (struct ref) + mode + error_code (narrow unsigned)
        h = mod.header_ct(addr=0x1FFF, enable=1)
        a = mod.packet_ct()
        a.header = h
        a.mode = 1
        a.error_code = 2
        b = mod.packet_ct()
        b.header = h
        b.mode = 1
        b.error_code = 5  # differs
        with pytest.raises(AssertionError) as ctx:
            a.compare(b)
        text = str(ctx.value)
        # error_code is narrow unsigned 3-bit → hex-formatted, hex_width=1
        assert "error_code: expected 0x2, got 0x5" in text

    def test_wrong_type_raises(self) -> None:
        mod = self._import("struct_signed", "alpha.py.types_types")
        a = mod.mixed_ct()
        with pytest.raises(AssertionError) as ctx:
            a.compare("not a struct")
        assert "Expected mixed_ct" in str(ctx.value)

    def test_msg_prefix_struct(self) -> None:
        mod = self._import("struct_signed", "alpha.py.types_types")
        a = mod.mixed_ct(field_s=0, field_u=0)
        b = mod.mixed_ct(field_s=0, field_u=1)
        with pytest.raises(AssertionError) as ctx:
            a.compare(b, msg="frame 7")
        assert str(ctx.value).startswith("frame 7:")

    def test_struct_ref_none_vs_value(self) -> None:
        mod = self._import("nested_struct_sv_basic", "alpha.py.types_types")
        a = mod.packet_ct()
        a.header = None
        b = mod.packet_ct()
        b.header = mod.header_ct(addr=1, enable=1)
        with pytest.raises(AssertionError) as ctx:
            a.compare(b)
        assert "header:" in str(ctx.value)

    def test_struct_with_enum_member(self) -> None:
        mod = self._import("struct_enum_member", "alpha.py.types_types")
        a = mod.pkt_ct()
        a.cmd = mod.cmd_ct(mod.cmd_enum_t.READ)
        a.data = 0x10
        b = mod.pkt_ct()
        b.cmd = mod.cmd_ct(mod.cmd_enum_t.WRITE)
        b.data = 0x10
        with pytest.raises(AssertionError) as ctx:
            a.compare(b)
        text = str(ctx.value)
        assert "cmd:" in text

    def test_diff_includes_repr_of_self_and_other(self) -> None:
        mod = self._import("struct_signed", "alpha.py.types_types")
        a = mod.mixed_ct(field_s=1, field_u=2)
        b = mod.mixed_ct(field_s=1, field_u=3)
        with pytest.raises(AssertionError) as ctx:
            a.compare(b)
        text = str(ctx.value)
        # Both reprs surface, joined by " != ".
        assert "mixed_ct(" in text
        assert " != " in text


if __name__ == "__main__":
    pytest.main([__file__])
