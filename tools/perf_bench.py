"""Wall-clock benchmark for ``piketype gen``.

Implements FR-23 of spec 010-jinja-template-migration. Runs
``run_gen`` against a fixture in a fresh temp directory across
several iterations, reports median/min/max wall-clock time in
milliseconds.

Usage::

    python tools/perf_bench.py
    python tools/perf_bench.py --fixture struct_padded --iterations 10

Output (stdout, single line tab-separated, suitable for direct
append into the perf.md table)::

    <fixture>\t<median_ms>\t<min_ms>\t<max_ms>

The first iteration is treated as a warm-up and discarded; the
remaining iterations contribute to the median/min/max.
"""

from __future__ import annotations

import argparse
import shutil
import statistics
import sys
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from piketype.commands.gen import run_gen  # noqa: E402


def _bench_once(*, fixture_dir: Path) -> float:
    """Run one ``run_gen`` invocation against a fresh copy and return milliseconds."""
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "project"
        shutil.copytree(fixture_dir, target)
        # Convention used across the fixture suite: the DSL file is
        # at <project>/alpha/piketype/types.py.
        dsl_file = target / "alpha" / "piketype" / "types.py"
        if not dsl_file.exists():
            raise FileNotFoundError(f"expected fixture DSL file at {dsl_file}")
        start = time.perf_counter()
        run_gen(str(dsl_file))
        end = time.perf_counter()
    return (end - start) * 1000.0


def bench(*, fixture: str, iterations: int) -> tuple[float, float, float]:
    """Run iterations+1 timings (one warm-up, ``iterations`` measured) and return ms stats."""
    if iterations < 1:
        raise ValueError("iterations must be >= 1")
    fixture_root = _REPO_ROOT / "tests" / "fixtures" / fixture / "project"
    if not fixture_root.exists():
        raise FileNotFoundError(f"fixture {fixture!r} not found at {fixture_root}")

    # Warm-up.
    _bench_once(fixture_dir=fixture_root)
    samples = [_bench_once(fixture_dir=fixture_root) for _ in range(iterations)]
    return statistics.median(samples), min(samples), max(samples)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="perf_bench")
    parser.add_argument("--fixture", default="struct_padded")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--output", default="-", help="path to write the result line, or - for stdout")
    args = parser.parse_args(argv)

    median_ms, min_ms, max_ms = bench(fixture=args.fixture, iterations=args.iterations)
    line = f"{args.fixture}\t{median_ms:.3f}\t{min_ms:.3f}\t{max_ms:.3f}\n"

    if args.output == "-":
        sys.stdout.write(line)
    else:
        Path(args.output).write_text(line, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
