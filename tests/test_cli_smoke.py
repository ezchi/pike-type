"""CLI smoke tests."""

from __future__ import annotations

import unittest

from piketype.cli import build_parser


class CliSmokeTest(unittest.TestCase):
    """Basic parser-level coverage."""

    def test_cli_has_expected_commands(self) -> None:
        parser = build_parser()
        help_text = parser.format_help()
        self.assertIn("gen", help_text)
        self.assertIn("build", help_text)
        self.assertIn("test", help_text)
        self.assertIn("lint", help_text)
