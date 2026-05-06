"""Tests for ``piketype init``."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from piketype.commands.init import run_init
from piketype.config import load_config
from piketype.errors import PikeTypeError


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent


class TestRunInit:
    def test_writes_default_yaml(self, tmp_path: Path) -> None:
        target = run_init(path=tmp_path)
        assert target == (tmp_path / "piketype.yaml").resolve()
        text = target.read_text(encoding="utf-8")
        assert "backends:" in text
        assert "language_id: rtl" in text
        assert "language_id: sim" in text
        assert "backend_root: py" in text
        assert "backend_root: cpp" in text

    def test_default_yaml_loads_cleanly(self, tmp_path: Path) -> None:
        target = run_init(path=tmp_path)
        config = load_config(target)
        assert {b.name for b in config.backends} == {"sv", "sim", "py", "cpp"}
        by_name = {b.name: b for b in config.backends}
        assert by_name["sv"].language_id == "rtl"
        assert by_name["sim"].language_id == "sim"
        assert by_name["py"].language_id == ""
        assert by_name["cpp"].language_id == ""

    def test_refuses_to_overwrite_existing(self, tmp_path: Path) -> None:
        run_init(path=tmp_path)
        with pytest.raises(PikeTypeError, match="already exists"):
            run_init(path=tmp_path)

    def test_force_overwrites(self, tmp_path: Path) -> None:
        target = run_init(path=tmp_path)
        target.write_text("custom content\n", encoding="utf-8")
        run_init(path=tmp_path, force=True)
        assert "backends:" in target.read_text(encoding="utf-8")

    def test_target_must_be_directory(self, tmp_path: Path) -> None:
        not_a_dir = tmp_path / "missing"
        with pytest.raises(PikeTypeError, match="not a directory"):
            run_init(path=not_a_dir)


class TestInitCli:
    @staticmethod
    def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}
        return subprocess.run(
            [sys.executable, "-m", "piketype.cli", *args],
            cwd=cwd, env=env, text=True, capture_output=True, check=False,
        )

    def test_init_via_cli(self, tmp_path: Path) -> None:
        result = self._run(["init"], cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "piketype.yaml").is_file()
        assert "wrote" in result.stdout

    def test_init_path_flag(self, tmp_path: Path) -> None:
        result = self._run(["init", "--path", str(tmp_path)], cwd=Path.cwd())
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "piketype.yaml").is_file()

    def test_init_force_flag(self, tmp_path: Path) -> None:
        first = self._run(["init"], cwd=tmp_path)
        assert first.returncode == 0, first.stderr
        # Second run without --force fails.
        second = self._run(["init"], cwd=tmp_path)
        assert second.returncode != 0
        assert "already exists" in second.stderr
        # Third run with --force succeeds.
        third = self._run(["init", "--force"], cwd=tmp_path)
        assert third.returncode == 0, third.stderr

    def test_init_then_gen_works_end_to_end(self, tmp_path: Path) -> None:
        # init writes config, then a fresh DSL file under <cwd>/alpha/piketype/ generates output.
        result = self._run(["init"], cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        (tmp_path / "alpha" / "piketype").mkdir(parents=True)
        (tmp_path / "alpha" / "piketype" / "types.py").write_text(
            "from piketype.dsl import Logic\n\nfoo_t = Logic(8)\n",
            encoding="utf-8",
        )
        gen_result = self._run(
            ["gen", str(tmp_path / "alpha" / "piketype" / "types.py")],
            cwd=tmp_path,
        )
        assert gen_result.returncode == 0, gen_result.stderr
        assert (tmp_path / "py" / "alpha" / "types_types.py").is_file()
        assert (tmp_path / "alpha" / "rtl" / "types_pkg.sv").is_file()
