"""Integration and runtime tests for Flags() DSL type."""

from __future__ import annotations

import os
import pytest
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from piketype.dsl import Flags
from piketype.dsl.freeze import build_const_definition_map, build_loaded_module, build_type_definition_map, freeze_module
from piketype.errors import ValidationError
from piketype.ir.nodes import FlagsIR
from piketype.validate.engine import validate_repo
from piketype.dsl.freeze import freeze_repo


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


def gen_fixture(fixture_name: str, tmp_dir: Path) -> Path:
    """Run piketype gen on a fixture and return the repo dir."""
    fixture_root = FIXTURES_DIR / fixture_name / "project"
    repo_dir = tmp_dir / fixture_name
    shutil.copytree(fixture_root, repo_dir)
    cli_file = repo_dir / "alpha" / "piketype" / "types.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    subprocess.run(
        [sys.executable, "-m", "piketype.cli", "gen", str(cli_file)],
        cwd=repo_dir,
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )
    return repo_dir


# ---------------------------------------------------------------------------
# DSL-level tests
# ---------------------------------------------------------------------------


class FlagsDSLTest:
    """DSL-level tests for Flags()."""

    def test_width_property(self) -> None:
        f = Flags().add_flag("a").add_flag("b").add_flag("c")
        assert f.width == 3

    def test_width_zero(self) -> None:
        assert Flags().width == 0

    def test_add_flag_chaining(self) -> None:
        f = Flags().add_flag("x").add_flag("y")
        assert len(f.flags) == 2
        assert f.flags[0].name == "x"
        assert f.flags[1].name == "y"

    def test_rejects_duplicate_flag(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            Flags().add_flag("a").add_flag("a")
        assert "duplicate" in str(ctx.value)

    def test_rejects_non_snake_case_uppercase(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            Flags().add_flag("BadName")
        assert "snake_case" in str(ctx.value)

    def test_rejects_non_snake_case_leading_digit(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            Flags().add_flag("1bad")
        assert "snake_case" in str(ctx.value)

    def test_rejects_empty_name(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            Flags().add_flag("")
        assert "snake_case" in str(ctx.value)


# ---------------------------------------------------------------------------
# IR validation tests
# ---------------------------------------------------------------------------


class FlagsValidationTest:
    """IR-level validation tests via validate_repo()."""

    def _build_repo_with_flags(self, name: str, flag_names: list[str]) -> None:
        """Build a minimal repo IR with one flags type and validate it."""
        from piketype.ir.nodes import (
            FlagFieldIR,
            FlagsIR,
            ModuleIR,
            ModuleRefIR,
            RepoIR,
            SourceSpanIR,
        )

        source = SourceSpanIR(path="test.py", line=1, column=None)
        ref = ModuleRefIR(
            repo_relative_path="alpha/piketype/types.py",
            python_module_name="alpha.piketype.types",
            namespace_parts=("alpha", "piketype", "types"),
            basename="types",
        )
        flags_ir = FlagsIR(
            name=name,
            source=source,
            fields=tuple(FlagFieldIR(name=n, source=source) for n in flag_names),
            alignment_bits=(-len(flag_names)) % 8,
        )
        module_ir = ModuleIR(
            ref=ref,
            source=source,
            constants=(),
            types=(flags_ir,),
            dependencies=(),
        )
        repo = RepoIR(repo_root="/tmp/test", modules=(module_ir,), tool_version=None)
        validate_repo(repo)

    def test_rejects_zero_flags(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            self._build_repo_with_flags("empty_t", [])
        assert "at least one flag" in str(ctx.value)

    def test_rejects_more_than_64_flags(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            self._build_repo_with_flags("huge_t", [f"f{i}" for i in range(65)])
        assert "maximum is 64" in str(ctx.value)

    def test_rejects_duplicate_flag_names(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            self._build_repo_with_flags("dup_t", ["a", "a"])
        assert "duplicate flag" in str(ctx.value)

    def test_rejects_pad_suffix(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            self._build_repo_with_flags("pad_t", ["align_pad"])
        assert "_pad" in str(ctx.value)

    def test_rejects_reserved_name_value(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            self._build_repo_with_flags("res_t", ["value"])
        assert "class API" in str(ctx.value)

    def test_rejects_reserved_name_to_bytes(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            self._build_repo_with_flags("res_t", ["to_bytes"])
        assert "class API" in str(ctx.value)

    def test_rejects_reserved_name_from_bytes(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            self._build_repo_with_flags("res_t", ["from_bytes"])
        assert "class API" in str(ctx.value)

    def test_rejects_missing_t_suffix(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            self._build_repo_with_flags("no_suffix", ["a"])
        assert "must end with _t" in str(ctx.value)

    def test_accepts_valid_flags(self) -> None:
        self._build_repo_with_flags("ok_t", ["a", "b", "c"])

    def test_accepts_64_flags(self) -> None:
        self._build_repo_with_flags("max_t", [f"f{i}" for i in range(64)])


# ---------------------------------------------------------------------------
# Golden file tests
# ---------------------------------------------------------------------------


class FlagsGoldenTest:
    """Golden file comparison tests."""

    def setup_method(self) -> None:
        self.tmp = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        shutil.rmtree(self.tmp)

    def test_generates_flags_golden(self) -> None:
        repo_dir = gen_fixture("flags_basic", Path(self.tmp))
        gen_root = repo_dir
        golden_root = TESTS_DIR / "goldens" / "gen" / "flags_basic"
        for golden_file in golden_root.rglob("*"):
            if golden_file.is_dir():
                continue
            if "__pycache__" in golden_file.parts or golden_file.suffix == ".pyc":
                continue
            relative = golden_file.relative_to(golden_root)
            generated = gen_root / relative
            assert generated.exists(), f"missing generated file: {relative}"
            expected = golden_file.read_text(encoding="utf-8")
            actual = generated.read_text(encoding="utf-8")
            assert expected == actual, f"mismatch in {relative}"

    def test_idempotent(self) -> None:
        repo_dir = gen_fixture("flags_basic", Path(self.tmp))
        gen_root = repo_dir
        first_run: dict[str, str] = {}
        for f in gen_root.rglob("*"):
            if f.is_dir():
                continue
            if "__pycache__" in f.parts or f.suffix == ".pyc":
                continue
            first_run[str(f.relative_to(gen_root))] = f.read_text(encoding="utf-8")
        # Run again
        cli_file = repo_dir / "alpha" / "piketype" / "types.py"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        subprocess.run(
            [sys.executable, "-m", "piketype.cli", "gen", str(cli_file)],
            cwd=repo_dir,
            check=True,
            env=env,
            text=True,
            capture_output=True,
        )
        for rel, expected in first_run.items():
            actual = (gen_root / rel).read_text(encoding="utf-8")
            assert expected == actual, f"idempotency failed for {rel}"


# ---------------------------------------------------------------------------
# Python runtime round-trip tests
# ---------------------------------------------------------------------------


class FlagsRuntimeTest:
    """Python runtime round-trip tests with explicit byte vectors."""

    _tmp_dir: tempfile.TemporaryDirectory[str]
    _gen_py: Path

    @classmethod
    def setup_class(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp_dir.name)
        cls._gen_py = gen_fixture("flags_basic", tmp)

    @classmethod
    def teardown_class(cls) -> None:
        cls._tmp_dir.cleanup()

    def _import_types(self):
        import importlib
        for key in list(sys.modules.keys()):
            if key == "alpha" or key.startswith("alpha."):
                del sys.modules[key]
        sys.path[:] = [p for p in sys.path if "/py" not in str(p)]
        sys.path.insert(0, str(self._gen_py / "py"))
        return importlib.import_module("alpha.types_types")

    # -- single_t (1 flag) --

    def test_single_flag_true(self) -> None:
        mod = self._import_types()
        obj = mod.single_ct()
        obj.flag = True
        assert obj.to_bytes() == b"\x80"

    def test_single_flag_false(self) -> None:
        mod = self._import_types()
        obj = mod.single_ct()
        obj.flag = False
        assert obj.to_bytes() == b"\x00"

    def test_single_from_bytes(self) -> None:
        mod = self._import_types()
        obj = mod.single_ct.from_bytes(b"\x80")
        assert obj.flag

    # -- triple_t (3 flags) --

    def test_triple_a_c(self) -> None:
        mod = self._import_types()
        obj = mod.triple_ct()
        obj.a = True
        obj.c = True
        assert obj.to_bytes() == b"\xa0"

    def test_triple_all(self) -> None:
        mod = self._import_types()
        obj = mod.triple_ct()
        obj.a = True
        obj.b = True
        obj.c = True
        assert obj.to_bytes() == b"\xe0"

    def test_triple_from_bytes(self) -> None:
        mod = self._import_types()
        obj = mod.triple_ct.from_bytes(b"\xa0")
        assert obj.a
        assert not obj.b
        assert obj.c

    # -- byte_t (8 flags, no padding) --

    def test_byte_all_on(self) -> None:
        mod = self._import_types()
        obj = mod.byte_ct()
        for i in range(8):
            setattr(obj, f"f{i}", True)
        assert obj.to_bytes() == b"\xff"

    def test_byte_all_off(self) -> None:
        mod = self._import_types()
        obj = mod.byte_ct()
        assert obj.to_bytes() == b"\x00"

    def test_byte_f0_only(self) -> None:
        mod = self._import_types()
        obj = mod.byte_ct()
        obj.f0 = True
        assert obj.to_bytes() == b"\x80"

    # -- wide_t (9 flags) --

    def test_wide_f0_only(self) -> None:
        mod = self._import_types()
        obj = mod.wide_ct()
        obj.f0 = True
        assert obj.to_bytes() == b"\x80\x00"

    def test_wide_f8_only(self) -> None:
        mod = self._import_types()
        obj = mod.wide_ct()
        obj.f8 = True
        assert obj.to_bytes() == b"\x00\x80"

    def test_wide_all_on(self) -> None:
        mod = self._import_types()
        obj = mod.wide_ct()
        for i in range(9):
            setattr(obj, f"f{i}", True)
        assert obj.to_bytes() == b"\xff\x80"

    # -- very_wide_t (33 flags) --

    def test_very_wide_f0_only(self) -> None:
        mod = self._import_types()
        obj = mod.very_wide_ct()
        obj.f0 = True
        assert obj.to_bytes() == b"\x80\x00\x00\x00\x00"

    def test_very_wide_f32_only(self) -> None:
        mod = self._import_types()
        obj = mod.very_wide_ct()
        obj.f32 = True
        assert obj.to_bytes() == b"\x00\x00\x00\x00\x80"

    # -- Round-trip --

    def test_round_trip_triple(self) -> None:
        mod = self._import_types()
        obj = mod.triple_ct()
        obj.a = True
        obj.c = True
        obj2 = mod.triple_ct.from_bytes(obj.to_bytes())
        assert obj == obj2

    def test_round_trip_wide(self) -> None:
        mod = self._import_types()
        obj = mod.wide_ct()
        obj.f0 = True
        obj.f8 = True
        obj2 = mod.wide_ct.from_bytes(obj.to_bytes())
        assert obj == obj2

    # -- Nonzero padding masking --

    def test_nonzero_padding_masked(self) -> None:
        mod = self._import_types()
        # b'\xa3' = 0xA3 = 10100011 — a=1, b=0, c=1, padding=00011 (nonzero)
        obj = mod.triple_ct.from_bytes(b"\xa3")
        clean = mod.triple_ct.from_bytes(b"\xa0")
        assert obj == clean
        assert obj.to_bytes() == b"\xa0"

    # -- from_bytes wrong size --

    def test_from_bytes_wrong_size(self) -> None:
        mod = self._import_types()
        with pytest.raises(ValueError):
            mod.triple_ct.from_bytes(b"\x00\x00")

    # -- Clone --

    def test_clone(self) -> None:
        mod = self._import_types()
        obj = mod.triple_ct()
        obj.a = True
        cloned = obj.clone()
        assert obj == cloned
        cloned.a = False
        assert obj != cloned
