"""Command-line entry point for typist."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from typist.commands.build import run_build
from typist.commands.gen import run_gen
from typist.commands.lint import run_lint
from typist.commands.test import run_test
from typist.errors import TypistError


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level CLI parser."""
    parser = argparse.ArgumentParser(prog="typist")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("gen", "build", "test", "lint"):
        command_parser = subparsers.add_parser(name)
        command_parser.add_argument("path")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        match args.command:
            case "gen":
                run_gen(args.path)
            case "build":
                run_build(args.path)
            case "test":
                run_test(args.path)
            case "lint":
                run_lint(args.path)
            case _:
                parser.error(f"unsupported command: {args.command}")
    except TypistError as exc:
        parser.exit(status=1, message=f"error: {exc}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
