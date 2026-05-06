"""Command-line entry point for piketype."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from piketype.commands.build import run_build
from piketype.commands.gen import run_gen
from piketype.commands.init import run_init
from piketype.commands.lint import run_lint
from piketype.commands.test import run_test
from piketype.errors import PikeTypeError


_SUPPORTED_LANGS: tuple[str, ...] = ("sv", "sim", "py", "cpp")


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level CLI parser."""
    parser = argparse.ArgumentParser(prog="piketype")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("gen", help="run frontend build + selected backends")
    gen_parser.add_argument("--config", default=None, help="path to piketype.yaml")
    gen_parser.add_argument("--namespace", default=None, help="C++ namespace override")
    gen_parser.add_argument(
        "--lang", default=None, choices=_SUPPORTED_LANGS,
        help="restrict generation to one backend (omit to run all enabled)",
    )
    gen_parser.add_argument("path", nargs="?", default=None, help="legacy: DSL .py file (optional)")

    build_parser_obj = subparsers.add_parser("build", help="frontend stage: write IR cache only")
    build_parser_obj.add_argument("--config", default=None)
    build_parser_obj.add_argument("path", nargs="?", default=None)

    init_parser = subparsers.add_parser("init", help="write a default piketype.yaml")
    init_parser.add_argument("--force", action="store_true", help="overwrite existing piketype.yaml")
    init_parser.add_argument("--path", default=None, help="target directory (default: cwd)")

    for name in ("test", "lint"):
        command_parser = subparsers.add_parser(name)
        command_parser.add_argument("--config", default=None)
        command_parser.add_argument("path", nargs="?", default=None)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        match args.command:
            case "gen":
                run_gen(
                    path=args.path, config_path=_to_path(args.config),
                    namespace=args.namespace, lang=args.lang,
                )
            case "build":
                run_build(config_path=_to_path(args.config), start=_legacy_start(args.path))
            case "init":
                target = run_init(path=_to_path(args.path), force=args.force)
                print(f"wrote {target}")
            case "test":
                run_test(args.path or ".")
            case "lint":
                run_lint(args.path or ".")
            case _:
                parser.error(f"unsupported command: {args.command}")
    except PikeTypeError as exc:
        parser.exit(status=1, message=f"error: {exc}\n")

    return 0


def _to_path(value: str | None) -> Path | None:
    return Path(value) if value is not None else None


def _legacy_start(path: str | None) -> Path | None:
    """Translate a legacy positional path into an upward-walk start dir."""
    if path is None:
        return None
    return Path(path).resolve().parent


if __name__ == "__main__":
    raise SystemExit(main())
