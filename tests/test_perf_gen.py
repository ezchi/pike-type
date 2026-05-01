"""Performance gate for `piketype gen` (NFR-4).

Opt-in via env var ``PIKETYPE_PERF_TEST=1``. Compares median wall-clock per
fixture against ``tests/perf_baseline.json``. Fails if total median exceeds
baseline by more than 5% or any single fixture exceeds its baseline by more
than 10%.
"""

from __future__ import annotations

import json
import os
import shutil
import statistics
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_BASELINE_FILE = Path(__file__).resolve().parent / "perf_baseline.json"
_TOTAL_BUDGET = 1.05  # 5% total
_PER_FIXTURE_BUDGET = 1.10  # 10% per-fixture
_RUNS_PER_FIXTURE = 5


def _measure_fixture(fixture_dir: Path) -> float:
    """Run `piketype gen` on the fixture's CLI module and return median seconds."""
    samples: list[float] = []
    for _ in range(_RUNS_PER_FIXTURE):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            shutil.copytree(fixture_dir / "project", tmp_path / "project", dirs_exist_ok=True)
            project_dir = tmp_path / "project"
            cli_module = project_dir / "alpha" / "piketype" / "types.py"
            if not cli_module.exists():
                # Multi-module fixture: pick first .py
                candidates = sorted(project_dir.glob("**/*.py"))
                cli_module = next(p for p in candidates if "piketype" in str(p) and "__init__" not in p.name)
            t0 = time.perf_counter()
            subprocess.run(
                ["uv", "run", "piketype", "gen", str(cli_module)],
                cwd=project_dir,
                check=True,
                capture_output=True,
            )
            samples.append(time.perf_counter() - t0)
    return statistics.median(samples)


@unittest.skipUnless(os.environ.get("PIKETYPE_PERF_TEST") == "1", "set PIKETYPE_PERF_TEST=1 to enable")
class PerfGateTests(unittest.TestCase):
    """Compare current `piketype gen` latency against committed baseline."""

    def test_within_budget(self) -> None:
        if not _BASELINE_FILE.exists():
            self.skipTest("perf baseline not yet captured; run with PIKETYPE_PERF_CAPTURE=1 to create one")

        baseline: dict[str, float] = json.loads(_BASELINE_FILE.read_text())

        current: dict[str, float] = {}
        fixture_dirs = sorted(p for p in _FIXTURES.iterdir() if (p / "project").is_dir())
        for fixture_dir in fixture_dirs:
            current[fixture_dir.name] = _measure_fixture(fixture_dir)

        # Per-fixture check
        for name, current_t in current.items():
            if name not in baseline:
                continue  # new fixture, no baseline yet
            limit = baseline[name] * _PER_FIXTURE_BUDGET
            self.assertLessEqual(
                current_t, limit,
                f"{name}: {current_t:.3f}s exceeds {limit:.3f}s ({_PER_FIXTURE_BUDGET:.0%} of baseline)",
            )

        # Total check
        total_baseline = sum(baseline.get(name, 0.0) for name in current)
        total_current = sum(current.values())
        if total_baseline > 0:
            limit = total_baseline * _TOTAL_BUDGET
            self.assertLessEqual(
                total_current, limit,
                f"total {total_current:.3f}s exceeds {limit:.3f}s ({_TOTAL_BUDGET:.0%} of baseline)",
            )


if __name__ == "__main__":
    if os.environ.get("PIKETYPE_PERF_CAPTURE") == "1":
        # Capture baseline mode.
        baseline: dict[str, float] = {}
        fixture_dirs = sorted(p for p in _FIXTURES.iterdir() if (p / "project").is_dir())
        for fixture_dir in fixture_dirs:
            t = _measure_fixture(fixture_dir)
            baseline[fixture_dir.name] = t
            print(f"{fixture_dir.name}: {t:.4f}s")
        _BASELINE_FILE.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")
        print(f"wrote {_BASELINE_FILE}")
    else:
        unittest.main()
