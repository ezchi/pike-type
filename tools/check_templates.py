"""Template-hygiene lint for piketype backend templates.

Implements FR-21 of spec 010-jinja-template-migration. Scans every
``.j2`` file under the given paths (or the three backend template
directories by default) and fails if any Jinja expression block
``{{ ... }}`` or statement block ``{% ... %}`` contains forbidden
patterns. Patterns are applied to Jinja-block contents only — never
to surrounding target-language template text — so that legitimate
generated SystemVerilog like ``padded[WIDTH-1:0]`` or C++ like
``BYTE_COUNT * 8`` is never falsely flagged.

The single exception is pattern 8 (``{% python %}`` extension),
which scans the raw template body because the offending construct
itself sits outside ``{% ... %}`` in some legacy templates.

Usage::

    python tools/check_templates.py
    python tools/check_templates.py path/to/templates

Exit code is 0 if no violations were found; 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

# Patterns are stored as (pattern_id, regex, description). pattern 8 is
# the only one applied to the raw template body; all others are applied
# only to Jinja-block contents.
JINJA_BLOCK_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("P1", re.compile(r"\(\s*1\s*<<\s*"), "bit-shift mask construction"),
    (
        "P2",
        re.compile(r"\bbyte_count\b\s*[-+*/]|[-+*/]\s*\bbyte_count\b"),
        "arithmetic on byte_count",
    ),
    ("P3", re.compile(r"\bhasattr\b|\bgetattr\b|\bisinstance\b"), "runtime type interrogation"),
    ("P4", re.compile(r"\.__class__\b|\btype\s*\("), "type lookup"),
    ("P5", re.compile(r"[-+*/]\s*8\b|\b8\s*[-+*/]"), "explicit byte arithmetic in Jinja"),
    (
        "P6",
        re.compile(r"\bopen\s*\(|\bos\.|\bsys\.|\bsubprocess\."),
        "stdlib/filesystem access",
    ),
    ("P7", re.compile(r"\bnow\s*\(|\brandom\b|\buuid\b"), "non-determinism source"),
)

RAW_BODY_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("P8", re.compile(r"\{%\s*python\b"), "Python-embedding extension"),
)

# Match Jinja blocks. Comments {# ... #} are ignored on purpose: those
# never affect output and we don't lint them.
JINJA_BLOCK_RE = re.compile(r"\{\{(.+?)\}\}|\{%(.+?)%\}", re.DOTALL)

DEFAULT_PATHS: tuple[str, ...] = (
    "src/piketype/backends/py/templates",
    "src/piketype/backends/cpp/templates",
    "src/piketype/backends/sv/templates",
)


class Violation:
    __slots__ = ("path", "line", "column", "pattern_id", "description", "match_text")

    def __init__(
        self,
        *,
        path: Path,
        line: int,
        column: int,
        pattern_id: str,
        description: str,
        match_text: str,
    ) -> None:
        self.path = path
        self.line = line
        self.column = column
        self.pattern_id = pattern_id
        self.description = description
        self.match_text = match_text

    def format(self) -> str:
        return (
            f"{self.path}:{self.line}:{self.column} "
            f"{self.pattern_id} {self.description}: {self.match_text!r}"
        )


def _line_col(source: str, offset: int) -> tuple[int, int]:
    """Compute 1-based line, 1-based column of a string offset."""
    line = source.count("\n", 0, offset) + 1
    last_nl = source.rfind("\n", 0, offset)
    col = offset - last_nl if last_nl != -1 else offset + 1
    return line, col


def scan_template(path: Path) -> list[Violation]:
    """Scan one template file and return any violations found."""
    text = path.read_text(encoding="utf-8")
    violations: list[Violation] = []

    # Patterns 1-7: only inside Jinja blocks.
    for block_match in JINJA_BLOCK_RE.finditer(text):
        # Group 1 is {{ ... }}, group 2 is {% ... %}; exactly one is non-None.
        block_content = block_match.group(1) or block_match.group(2) or ""
        block_start = block_match.start()
        # Block content starts after '{{' or '{%' (2 chars).
        content_offset = block_start + 2
        for pattern_id, regex, description in JINJA_BLOCK_PATTERNS:
            for hit in regex.finditer(block_content):
                hit_offset = content_offset + hit.start()
                line, col = _line_col(text, hit_offset)
                violations.append(
                    Violation(
                        path=path,
                        line=line,
                        column=col,
                        pattern_id=pattern_id,
                        description=description,
                        match_text=hit.group(0),
                    )
                )

    # Pattern 8: raw template body.
    for pattern_id, regex, description in RAW_BODY_PATTERNS:
        for hit in regex.finditer(text):
            line, col = _line_col(text, hit.start())
            violations.append(
                Violation(
                    path=path,
                    line=line,
                    column=col,
                    pattern_id=pattern_id,
                    description=description,
                    match_text=hit.group(0),
                )
            )

    return violations


def collect_templates(paths: Iterable[Path]) -> list[Path]:
    """Collect every .j2 file under the given paths."""
    out: list[Path] = []
    for p in paths:
        if not p.exists():
            continue
        if p.is_file() and p.suffix == ".j2":
            out.append(p)
        elif p.is_dir():
            out.extend(sorted(p.rglob("*.j2")))
    return sorted(out)


def check_paths(paths: Sequence[Path]) -> list[Violation]:
    """Scan every template under the given paths and return all violations."""
    violations: list[Violation] = []
    for template in collect_templates(paths):
        violations.extend(scan_template(template))
    return violations


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_templates")
    parser.add_argument("paths", nargs="*", help="Files or directories to scan.")
    args = parser.parse_args(argv)

    raw_paths = args.paths if args.paths else DEFAULT_PATHS
    paths = [Path(p) for p in raw_paths]
    violations = check_paths(paths)

    for v in violations:
        print(v.format(), file=sys.stderr)

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
