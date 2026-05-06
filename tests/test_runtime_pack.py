"""Runtime tests for the generated Python pack/unpack methods.

Each generated type wrapper exposes ``pack() -> int`` and
``unpack(int) -> cls``. The flat-int representation matches the SystemVerilog
``pack_<base>`` / ``unpack_<base>`` functions: data-only (no per-field
byte padding, no struct alignment bytes), MSB-first by declaration order,
with sign extension folded into unpack of signed slots.
"""

from __future__ import annotations

import importlib
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


class _RuntimeBase:
    _tmp_dir: tempfile.TemporaryDirectory[str]
    _gen_roots: dict[str, Path]

    @classmethod
    def setup_class(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp_dir.name)
        cls._gen_roots = {
            "struct_signed": _gen_fixture("struct_signed", tmp),
            "scalar_wide": _gen_fixture("scalar_wide", tmp),
            "struct_wide": _gen_fixture("struct_wide", tmp),
            "nested_struct_sv_basic": _gen_fixture("nested_struct_sv_basic", tmp),
            "scalar_sv_basic": _gen_fixture("scalar_sv_basic", tmp),
            "struct_padded": _gen_fixture("struct_padded", tmp),
            "struct_flags_member": _gen_fixture("struct_flags_member", tmp),
            "struct_enum_member": _gen_fixture("struct_enum_member", tmp),
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
        sys.path.insert(0, str(gen_root / "py"))
        return importlib.import_module(module_path)


class ScalarAliasPackTest(_RuntimeBase):

    def test_narrow_unsigned_round_trip(self) -> None:
        mod = self._import("scalar_sv_basic", "alpha.types_types")
        # addr_t — Bit(13), unsigned
        a = mod.addr_ct(0x1ABC)
        assert a.pack() == 0x1ABC
        assert mod.addr_ct.unpack(0x1ABC) == a

    def test_narrow_unsigned_unpack_masks_excess_bits(self) -> None:
        mod = self._import("scalar_sv_basic", "alpha.types_types")
        # addr_t WIDTH=13. Excess high bits are masked away.
        a = mod.addr_ct.unpack(0xFFFF)
        assert a.value == 0x1FFF

    def test_narrow_signed_negative_round_trip(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        # signed_4_t — 4-bit signed
        s = mod.signed_4_ct(-3)
        # -3 in 4-bit two's complement = 0xD
        assert s.pack() == 0xD
        rt = mod.signed_4_ct.unpack(0xD)
        assert rt.value == -3

    def test_narrow_signed_max_positive(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        s = mod.signed_4_ct(7)
        assert s.pack() == 7
        assert mod.signed_4_ct.unpack(7).value == 7

    def test_narrow_signed_min_negative(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        # -8 in 4-bit two's complement = 0x8
        s = mod.signed_4_ct(-8)
        assert s.pack() == 0x8
        assert mod.signed_4_ct.unpack(0x8).value == -8

    def test_wide_unsigned_round_trip(self) -> None:
        mod = self._import("scalar_wide", "alpha.types_types")
        # wide_t — 65-bit unsigned
        v = (1 << 65) - 1  # all ones, 65 bits
        w = mod.wide_ct(v)
        assert w.pack() == v
        rt = mod.wide_ct.unpack(v)
        assert rt.value == w.value

    def test_wide_unpack_masks_excess_bits(self) -> None:
        mod = self._import("scalar_wide", "alpha.types_types")
        # Pass an int wider than 65 bits — upper bits must be discarded.
        rt = mod.wide_ct.unpack((1 << 80) - 1)
        # Stored bytes have the upper byte's pad bits zero.
        assert rt.value[0] == 0x01
        assert rt.value[1:] == b"\xff" * 8


class EnumPackTest(_RuntimeBase):

    def test_pack_returns_int_value(self) -> None:
        mod = self._import("enum_basic", "foo.defs_types")
        c = mod.color_ct(mod.color_enum_t.GREEN)
        assert c.pack() == 5

    def test_unpack_round_trip(self) -> None:
        mod = self._import("enum_basic", "foo.defs_types")
        c = mod.color_ct.unpack(10)
        assert c.value == mod.color_enum_t.BLUE

    def test_unpack_rejects_unknown_value(self) -> None:
        mod = self._import("enum_basic", "foo.defs_types")
        with pytest.raises(ValueError):
            mod.color_ct.unpack(3)

    def test_unpack_masks_high_bits(self) -> None:
        mod = self._import("enum_basic", "foo.defs_types")
        # color_t WIDTH=4, mask=0xF. 0x15 & 0xF = 5 = GREEN.
        c = mod.color_ct.unpack(0x15)
        assert c.value == mod.color_enum_t.GREEN


class FlagsPackTest(_RuntimeBase):

    def test_pack_three_flags_msb_first(self) -> None:
        mod = self._import("flags_basic", "alpha.types_types")
        # triple_t has 3 flags: a, b, c — declaration order, a is MSB.
        f = mod.triple_ct()
        f.a = True
        f.b = False
        f.c = True
        # pack: bit 2 = a, bit 1 = b, bit 0 = c → 0b101 = 5
        assert f.pack() == 0b101

    def test_unpack_round_trip(self) -> None:
        mod = self._import("flags_basic", "alpha.types_types")
        f = mod.triple_ct.unpack(0b011)
        # bit 2 = a = 0, bit 1 = b = 1, bit 0 = c = 1
        assert not f.a
        assert f.b
        assert f.c

    def test_pack_then_unpack_round_trip(self) -> None:
        mod = self._import("flags_basic", "alpha.types_types")
        f = mod.triple_ct()
        f.a = True
        f.b = True
        f.c = False
        rt = mod.triple_ct.unpack(f.pack())
        assert rt == f

    def test_no_alignment_byte_t_round_trip(self) -> None:
        mod = self._import("flags_basic", "alpha.types_types")
        # byte_t — 8 flags, no alignment.
        b = mod.byte_ct()
        b.f0 = True
        b.f7 = True
        # MSB-first: f0=1 (bit 7), f7=1 (bit 0) → 0b10000001 = 0x81
        assert b.pack() == 0x81
        rt = mod.byte_ct.unpack(0x81)
        assert rt.f0
        assert rt.f7
        assert not rt.f1


class StructPackTest(_RuntimeBase):

    # -- Mixed signed struct (data_width = 9: signed_4 + signed 5-bit) --

    def test_struct_signed_pack_matches_concat(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        # field_s = -6 (4-bit two's comp = 0xA), field_u = -1 (5-bit two's comp = 0x1F)
        obj = mod.mixed_ct(field_s=-6, field_u=-1)
        # Concatenated MSB-first: 0b1010_11111 = 0x15F = 351
        assert obj.pack() == 0x15F

    def test_struct_signed_unpack_sign_extends_signed_fields(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        rt = mod.mixed_ct.unpack(0x15F)
        assert rt.field_s.value == -6
        assert rt.field_u == -1

    def test_struct_signed_pack_unpack_round_trip(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        for s in (-8, -1, 0, 7):
            for u in (-16, -1, 0, 15):
                obj = mod.mixed_ct(field_s=s, field_u=u)
                rt = mod.mixed_ct.unpack(obj.pack())
                assert rt.field_s.value == s
                assert rt.field_u == u

    # -- Padded struct (mix of unsigned and aligned padding bytes) --

    def test_struct_padded_pack_no_alignment_bits(self) -> None:
        mod = self._import("struct_padded", "alpha.types_types")
        # bar_t has alignment bytes in to_bytes; pack() must NOT include them.
        obj = mod.bar_ct(flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0)
        # Sum of data widths = 1 + 13 + 4 + 1 = 19 bits.
        # MSB-first: flag_a(1) | field_1(13) | status(4) | flag_b(1)
        expected = (1 << 18) | (0x1FFF << 5) | (0xA << 1) | 0
        assert obj.pack() == expected
        # The pack-only int must fit within 19 data bits.
        assert obj.pack() < 1 << 19

    def test_struct_padded_pack_unpack_round_trip(self) -> None:
        mod = self._import("struct_padded", "alpha.types_types")
        obj = mod.bar_ct(flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0)
        rt = mod.bar_ct.unpack(obj.pack())
        assert rt.flag_a == 1
        assert rt.field_1 == 0x1FFF
        assert rt.status == 0xA
        assert rt.flag_b == 0

    # -- Wide-member struct (>64-bit fields stored as bytes) --

    def test_struct_wide_pack_concatenates_data_bits(self) -> None:
        mod = self._import("struct_wide", "alpha.types_types")
        obj = mod.big_ct()
        obj.data = b"\x01" + b"\xff" * 8  # 65-bit value: 2^64 + ... = (1 << 65) - 1
        obj.flag = 1
        obj.extra = b"\x80" + b"\x00" * 15  # 128-bit: high bit set
        data_int = (1 << 65) - 1
        flag_int = 1
        extra_int = 1 << 127
        # Total width = 65 + 1 + 128 = 194 bits, MSB = data.
        expected = (data_int << 129) | (flag_int << 128) | extra_int
        assert obj.pack() == expected

    def test_struct_wide_unpack_round_trip(self) -> None:
        mod = self._import("struct_wide", "alpha.types_types")
        obj = mod.big_ct()
        obj.data = b"\x01" + b"\xff" * 8
        obj.flag = 1
        obj.extra = b"\x80" + b"\x00" * 15
        rt = mod.big_ct.unpack(obj.pack())
        assert rt.data == obj.data
        assert rt.flag == obj.flag
        assert rt.extra == obj.extra

    # -- Nested struct (header_t inside packet_t) --

    def test_nested_struct_pack_recursive(self) -> None:
        mod = self._import("nested_struct_sv_basic", "alpha.types_types")
        header = mod.header_ct(addr=0x1FFF, enable=1)
        pkt = mod.packet_ct()
        pkt.header = header
        pkt.mode = 2
        pkt.error_code = 5
        # header data_width = 14 (addr 13 + enable 1) → packs to (0x1FFF << 1) | 1 = 0x3FFF
        # packet data_width = 14 + 2 + 3 = 19; layout MSB-first: header | mode | error_code
        expected = (0x3FFF << 5) | (2 << 3) | 5
        assert pkt.pack() == expected

    def test_nested_struct_unpack_recursive(self) -> None:
        mod = self._import("nested_struct_sv_basic", "alpha.types_types")
        rt = mod.packet_ct.unpack((0x3FFF << 5) | (2 << 3) | 5)
        assert rt.header.addr.value == 0x1FFF
        assert rt.header.enable.value == 1
        assert rt.mode == 2
        assert rt.error_code == 5

    def test_nested_struct_raises_when_header_is_none(self) -> None:
        mod = self._import("nested_struct_sv_basic", "alpha.types_types")
        pkt = mod.packet_ct()
        pkt.header = None
        with pytest.raises(ValueError):
            pkt.pack()

    # -- Struct with flags member --

    def test_struct_with_flags_member_pack(self) -> None:
        mod = self._import("struct_flags_member", "alpha.types_types")
        rep = mod.report_ct()
        rep.status.error = True
        rep.status.warning = False
        rep.status.ready = True
        rep.code = 0xA
        # status flat: 0b101 = 5; code = 0xA (5-bit). Concat: (5 << 5) | 10 = 170
        assert rep.pack() == (0b101 << 5) | 0xA

    def test_struct_with_flags_member_unpack(self) -> None:
        mod = self._import("struct_flags_member", "alpha.types_types")
        rt = mod.report_ct.unpack((0b101 << 5) | 0xA)
        assert rt.status.error
        assert not rt.status.warning
        assert rt.status.ready
        assert rt.code == 0xA

    # -- Struct with enum member --

    def test_struct_with_enum_member_round_trip(self) -> None:
        mod = self._import("struct_enum_member", "alpha.types_types")
        pkt = mod.pkt_ct()
        pkt.cmd = mod.cmd_ct(mod.cmd_enum_t.READ)  # value = 1, 2-bit
        pkt.data = 0xAB  # 8-bit
        # cmd data_width = 2, data data_width = 8 → total 10 bits.
        # Concat MSB-first: cmd(2) | data(8) = (1 << 8) | 0xAB
        assert pkt.pack() == (1 << 8) | 0xAB
        rt = mod.pkt_ct.unpack(pkt.pack())
        assert rt.cmd.value == mod.cmd_enum_t.READ
        assert rt.data == 0xAB

    # -- pack() return is data-only (no alignment, no per-field padding) --

    def test_struct_padded_pack_int_width_excludes_alignment(self) -> None:
        mod = self._import("struct_padded", "alpha.types_types")
        obj = mod.bar_ct(flag_a=1, field_1=0x1FFF, status=0xF, flag_b=1)
        # 19 data bits → max value 2^19 - 1.
        assert obj.pack() < 1 << 19
        # to_bytes produces 5 bytes (40 bits) with alignment, so they're NOT equal.
        assert obj.pack() != int.from_bytes(obj.to_bytes(), "big")


class ScalarAliasLvTest(_RuntimeBase):

    def test_narrow_unsigned_to_lv_equals_value(self) -> None:
        mod = self._import("scalar_sv_basic", "alpha.types_types")
        # addr_t — 13-bit unsigned, byte_count=2. to_lv = byte interpretation = self.value.
        a = mod.addr_ct(0x1ABC)
        assert a.to_lv() == 0x1ABC

    def test_narrow_unsigned_from_lv_round_trip(self) -> None:
        mod = self._import("scalar_sv_basic", "alpha.types_types")
        a = mod.addr_ct(0x1ABC)
        rt = mod.addr_ct.from_lv(a.to_lv())
        assert rt.value == 0x1ABC

    def test_narrow_signed_to_lv_includes_sign_extension(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        # signed_4_t with -3: pack=0xD (4 bits), to_lv=0xFD (8 bits, sign-extended).
        s = mod.signed_4_ct(-3)
        assert s.pack() == 0xD
        assert s.to_lv() == 0xFD

    def test_narrow_signed_from_lv_decodes_sign_extension(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        rt = mod.signed_4_ct.from_lv(0xFD)
        assert rt.value == -3

    def test_narrow_signed_from_lv_rejects_invalid_padding(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        # Sign bit of data is 1 but padding bits are 0 → from_bytes raises.
        with pytest.raises(ValueError):
            mod.signed_4_ct.from_lv(0x0D)

    def test_wide_unsigned_to_lv_round_trip(self) -> None:
        mod = self._import("scalar_wide", "alpha.types_types")
        v = (1 << 65) - 1
        w = mod.wide_ct(v)
        assert w.to_lv() == v
        rt = mod.wide_ct.from_lv(v)
        assert rt.value == w.value

    def test_from_lv_masks_excess_bits(self) -> None:
        mod = self._import("scalar_sv_basic", "alpha.types_types")
        # Bytes representation is 16 bits. Excess high bits are masked.
        # 0x1FF1ABC & 0xFFFF = 0x1ABC. Then from_bytes masks data bits to 0x1FFF? No,
        # 0x1ABC fits in 13 bits.
        rt = mod.addr_ct.from_lv(0x1FF1ABC)
        assert rt.value == 0x1ABC


class EnumLvTest(_RuntimeBase):

    def test_to_lv_equals_int_value(self) -> None:
        mod = self._import("enum_basic", "foo.defs_types")
        c = mod.color_ct(mod.color_enum_t.GREEN)
        assert c.to_lv() == 5

    def test_from_lv_round_trip(self) -> None:
        mod = self._import("enum_basic", "foo.defs_types")
        rt = mod.color_ct.from_lv(10)
        assert rt.value == mod.color_enum_t.BLUE

    def test_from_lv_rejects_unknown(self) -> None:
        mod = self._import("enum_basic", "foo.defs_types")
        with pytest.raises(ValueError):
            mod.color_ct.from_lv(3)


class FlagsLvTest(_RuntimeBase):

    def test_to_lv_keeps_alignment_bits_zero(self) -> None:
        mod = self._import("flags_basic", "alpha.types_types")
        # triple_t — 3 flags, alignment_bits=5. Setting all flags:
        # _value bits: a=bit7, b=bit6, c=bit5 → 0b11100000 = 0xE0
        f = mod.triple_ct()
        f.a = True
        f.b = True
        f.c = True
        assert f.to_lv() == 0xE0
        # pack returns the data-only int = 0b111 = 7
        assert f.pack() == 7

    def test_from_lv_round_trip(self) -> None:
        mod = self._import("flags_basic", "alpha.types_types")
        rt = mod.triple_ct.from_lv(0xA0)
        # 0xA0 = 0b10100000 → bit 7 (a) = 1, bit 6 (b) = 0, bit 5 (c) = 1
        assert rt.a
        assert not rt.b
        assert rt.c

    def test_from_lv_masks_alignment_bits(self) -> None:
        mod = self._import("flags_basic", "alpha.types_types")
        # Bits in the alignment region (lower 5) are silently masked by from_bytes.
        rt = mod.triple_ct.from_lv(0xBF)  # 0b10111111: bit 7=1, bit 6=0, bit 5=1
        assert rt.a
        assert not rt.b
        assert rt.c


class StructLvTest(_RuntimeBase):

    def test_struct_signed_to_lv_includes_padding(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        # mixed_t fields: field_s (signed 4-bit, sign-extended into byte) + field_u (signed 5-bit).
        # field_s = -6 → byte 0xFA; field_u = -1 → byte 0xFF.
        # to_bytes = b"\xFA\xFF" → to_lv = 0xFAFF
        obj = mod.mixed_ct(field_s=-6, field_u=-1)
        assert obj.to_lv() == 0xFAFF
        # pack returns 9 bits only.
        assert obj.pack() == 0x15F

    def test_struct_signed_from_lv_round_trip(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        rt = mod.mixed_ct.from_lv(0xFAFF)
        assert rt.field_s.value == -6
        assert rt.field_u == -1

    def test_struct_padded_to_lv_includes_alignment_bytes(self) -> None:
        mod = self._import("struct_padded", "alpha.types_types")
        obj = mod.bar_ct(flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0)
        # to_bytes = b"\x01\x1f\xff\x0a\x00" (5 bytes incl. alignment).
        assert obj.to_lv() == int.from_bytes(b"\x01\x1f\xff\x0a\x00", "big")

    def test_struct_padded_from_lv_round_trip(self) -> None:
        mod = self._import("struct_padded", "alpha.types_types")
        obj = mod.bar_ct(flag_a=1, field_1=0x1FFF, status=0xA, flag_b=0)
        rt = mod.bar_ct.from_lv(obj.to_lv())
        assert rt.flag_a == obj.flag_a
        assert rt.field_1 == obj.field_1
        assert rt.status == obj.status
        assert rt.flag_b == obj.flag_b

    def test_nested_struct_to_lv_round_trip(self) -> None:
        mod = self._import("nested_struct_sv_basic", "alpha.types_types")
        header = mod.header_ct(addr=0x1FFF, enable=1)
        pkt = mod.packet_ct()
        pkt.header = header
        pkt.mode = 2
        pkt.error_code = 5
        rt = mod.packet_ct.from_lv(pkt.to_lv())
        assert rt.header.addr.value == 0x1FFF
        assert rt.header.enable.value == 1
        assert rt.mode == 2
        assert rt.error_code == 5

    def test_struct_to_lv_equals_to_bytes_int(self) -> None:
        mod = self._import("struct_padded", "alpha.types_types")
        obj = mod.bar_ct(flag_a=1, field_1=0x0ABC, status=0x3, flag_b=1)
        assert obj.to_lv() == int.from_bytes(obj.to_bytes(), "big")

    def test_to_lv_differs_from_pack_when_padding_present(self) -> None:
        mod = self._import("struct_signed", "alpha.types_types")
        # mixed_t has signed-narrow fields with byte alignment → to_lv > pack typically.
        obj = mod.mixed_ct(field_s=-1, field_u=-1)
        assert obj.pack() != obj.to_lv()
