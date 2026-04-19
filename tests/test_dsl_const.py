"""Unit tests for the constant DSL node."""

from __future__ import annotations

import unittest

from typist.dsl import Bit, Const, Logic, Struct


class ConstDslTest(unittest.TestCase):
    """Coverage for Const construction behavior."""

    def test_constructs_with_integer_literal(self) -> None:
        const = Const(3)
        self.assertEqual(const.value, 3)
        self.assertGreaterEqual(const.source.line, 1)

    def test_accepts_explicit_signed_and_width(self) -> None:
        const = Const(3, signed=False, width=32)
        self.assertFalse(const.signed)
        self.assertEqual(const.width, 32)

    def test_builds_expression_and_resolves_value(self) -> None:
        base = Const(3)
        expr_const = Const((base << 2) | 1)
        self.assertEqual(expr_const.value, 13)

    def test_rejects_true_division_operator(self) -> None:
        base = Const(3)
        with self.assertRaisesRegex(Exception, "// only"):
            _ = base / 2

    def test_builds_scalar_aliases(self) -> None:
        bit_t = Bit(13)
        logic_t = Logic(8, signed=True)
        self.assertEqual(bit_t.state_kind, "bit")
        self.assertEqual(bit_t.width_value, 13)
        self.assertEqual(logic_t.state_kind, "logic")
        self.assertTrue(logic_t.signed)

    def test_builds_struct_members(self) -> None:
        packet_t = Struct().add_member("addr", Bit(13)).add_member("valid", Logic(1))
        self.assertEqual(len(packet_t.members), 2)
        self.assertEqual(packet_t.members[0].name, "addr")
        self.assertEqual(packet_t.members[1].type.state_kind, "logic")
