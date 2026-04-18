"""Unit tests for the constant DSL node."""

from __future__ import annotations

import unittest

from typist.dsl import Const


class ConstDslTest(unittest.TestCase):
    """Coverage for Const construction behavior."""

    def test_constructs_with_integer_literal(self) -> None:
        const = Const(3)
        self.assertEqual(const.value, 3)
        self.assertGreaterEqual(const.source.line, 1)
