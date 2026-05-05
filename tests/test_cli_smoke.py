"""CLI smoke tests."""

from __future__ import annotations


from piketype.cli import build_parser


class CliSmokeTest:
    """Basic parser-level coverage."""

    def test_cli_has_expected_commands(self) -> None:
        parser = build_parser()
        help_text = parser.format_help()
        assert "gen" in help_text
        assert "build" in help_text
        assert "test" in help_text
        assert "lint" in help_text
