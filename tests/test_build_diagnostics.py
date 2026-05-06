"""Tests for build-stage diagnostics: cycle detection + underscore skip."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from piketype.discovery.dep_graph import build_module_graph, detect_module_cycles
from piketype.ir.nodes import (
    ModuleDependencyIR,
    ModuleIR,
    ModuleRefIR,
    RepoIR,
    SourceSpanIR,
)


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


def _ref(name: str) -> ModuleRefIR:
    return ModuleRefIR(
        repo_relative_path=f"alpha/piketype/{name}.py",
        python_module_name=f"alpha.piketype.{name}",
        namespace_parts=("alpha", "piketype", name),
        basename=name,
    )


def _module(name: str, deps: tuple[str, ...] = ()) -> ModuleIR:
    src = SourceSpanIR(path=f"alpha/piketype/{name}.py", line=1, column=None)
    return ModuleIR(
        ref=_ref(name),
        source=src,
        constants=(),
        types=(),
        dependencies=tuple(
            ModuleDependencyIR(target=_ref(d), kind="type_ref") for d in deps
        ),
    )


class TestModuleGraph:
    def test_build_graph_extracts_dependencies(self) -> None:
        repo = RepoIR(
            repo_root="/x",
            modules=(
                _module("a"),
                _module("b", deps=("a",)),
                _module("c", deps=("a", "b")),
            ),
            tool_version=None,
        )
        graph = build_module_graph(repo)
        assert graph["alpha.piketype.a"] == set()
        assert graph["alpha.piketype.b"] == {"alpha.piketype.a"}
        assert graph["alpha.piketype.c"] == {"alpha.piketype.a", "alpha.piketype.b"}

    def test_no_cycles_in_acyclic_graph(self) -> None:
        repo = RepoIR(
            repo_root="/x",
            modules=(_module("a"), _module("b", deps=("a",))),
            tool_version=None,
        )
        assert detect_module_cycles(repo) == []

    def test_two_node_cycle_detected(self) -> None:
        repo = RepoIR(
            repo_root="/x",
            modules=(_module("a", deps=("b",)), _module("b", deps=("a",))),
            tool_version=None,
        )
        cycles = detect_module_cycles(repo)
        assert len(cycles) == 1
        assert set(cycles[0]) == {"alpha.piketype.a", "alpha.piketype.b"}

    def test_three_node_cycle_detected(self) -> None:
        repo = RepoIR(
            repo_root="/x",
            modules=(
                _module("a", deps=("b",)),
                _module("b", deps=("c",)),
                _module("c", deps=("a",)),
            ),
            tool_version=None,
        )
        cycles = detect_module_cycles(repo)
        assert len(cycles) >= 1
        names = set(cycles[0])
        assert {"alpha.piketype.a", "alpha.piketype.b", "alpha.piketype.c"}.issubset(names)


class TestUnderscoreSkipIntegration:
    @staticmethod
    def _run_gen(repo_dir: Path, cli_arg: str) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}
        return subprocess.run(
            [sys.executable, "-m", "piketype.cli", "gen", cli_arg],
            cwd=repo_dir, env=env, text=True, capture_output=True, check=False,
        )

    def test_underscore_helper_does_not_produce_output(self) -> None:
        fixture_root = FIXTURES_DIR / "underscore_skip" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self._run_gen(repo_dir, str(cli_file))
            assert result.returncode == 0, result.stderr
            # Helper has no output of its own.
            assert not (repo_dir / "py" / "alpha" / "_helper_types.py").exists()
            assert not (repo_dir / "alpha" / "rtl" / "_helper_pkg.sv").exists()
            # Main types.py DOES produce output.
            assert (repo_dir / "py" / "alpha" / "types_types.py").is_file()

    def test_diagnostics_records_underscore_skip(self) -> None:
        fixture_root = FIXTURES_DIR / "underscore_skip" / "project"
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "project"
            shutil.copytree(fixture_root, repo_dir)
            cli_file = repo_dir / "alpha" / "piketype" / "types.py"
            result = self._run_gen(repo_dir, str(cli_file))
            assert result.returncode == 0, result.stderr

            diag_path = repo_dir / ".piketype-cache" / "diagnostics.json"
            assert diag_path.is_file()
            payload = json.loads(diag_path.read_text())
            entries = payload["diagnostics"]
            underscore_entries = [d for d in entries if d["code"] == "underscore-skip"]
            assert len(underscore_entries) == 1
            assert underscore_entries[0]["severity"] == "info"
            assert "_helper.py" in underscore_entries[0]["message"]


class TestDiagnosticsFile:
    def test_no_errors_for_clean_build(self, tmp_path: Path) -> None:
        # Use an existing clean fixture and verify no error severity.
        fixture_root = FIXTURES_DIR / "scalar_sv_basic" / "project"
        repo_dir = tmp_path / "project"
        shutil.copytree(fixture_root, repo_dir)
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}
        result = subprocess.run(
            [sys.executable, "-m", "piketype.cli", "gen", str(repo_dir / "alpha" / "piketype" / "types.py")],
            cwd=repo_dir, env=env, text=True, capture_output=True, check=False,
        )
        assert result.returncode == 0, result.stderr
        diag = json.loads((repo_dir / ".piketype-cache" / "diagnostics.json").read_text())
        errors = [d for d in diag["diagnostics"] if d["severity"] == "error"]
        assert errors == []
