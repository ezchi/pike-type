"""Integration, golden-file, and runtime tests for Enum() DSL type."""

from __future__ import annotations

import importlib
import os
import pytest
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from piketype.errors import ValidationError
from piketype.ir.nodes import (
    EnumIR,
    EnumValueIR,
    FlagFieldIR,
    FlagsIR,
    IntLiteralExprIR,
    ModuleIR,
    ModuleRefIR,
    RepoIR,
    SourceSpanIR,
)
from piketype.validate.engine import validate_repo


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


def _gen_fixture(fixture_name: str, tmp_dir: Path, cli_file_rel: str = "foo/piketype/defs.py") -> Path:
    """Run piketype gen on a fixture and return the repo dir."""
    fixture_root = FIXTURES_DIR / fixture_name / "project"
    repo_dir = tmp_dir / fixture_name
    shutil.copytree(fixture_root, repo_dir)
    cli_file = repo_dir / cli_file_rel
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


def _make_enum_ir(
    name: str,
    values: list[tuple[str, int]],
    width: int | None = None,
) -> EnumIR:
    """Build a minimal EnumIR for validation tests."""
    source = SourceSpanIR(path="test.py", line=1, column=None)
    if width is None:
        if not values:
            resolved_width = 0
        else:
            max_val = max(v for _, v in values)
            resolved_width = max(1, max_val.bit_length())
    else:
        resolved_width = width
    return EnumIR(
        name=name,
        source=source,
        width_expr=IntLiteralExprIR(value=resolved_width, source=source),
        resolved_width=resolved_width,
        values=tuple(
            EnumValueIR(
                name=vname,
                source=source,
                expr=IntLiteralExprIR(value=vval, source=source),
                resolved_value=vval,
            )
            for vname, vval in values
        ),
    )


def _validate_enum(name: str, values: list[tuple[str, int]], width: int | None = None) -> None:
    """Build a minimal repo with one enum and validate it."""
    source = SourceSpanIR(path="test.py", line=1, column=None)
    ref = ModuleRefIR(
        repo_relative_path="foo/piketype/defs.py",
        python_module_name="foo.piketype.defs",
        namespace_parts=("foo", "piketype", "defs"),
        basename="defs",
    )
    enum_ir = _make_enum_ir(name, values, width)
    module_ir = ModuleIR(
        ref=ref,
        source=source,
        constants=(),
        types=(enum_ir,),
        dependencies=(),
    )
    repo = RepoIR(repo_root="/tmp/test", modules=(module_ir,), tool_version=None)
    validate_repo(repo)


# ---------------------------------------------------------------------------
# DSL-level tests
# ---------------------------------------------------------------------------


class EnumDSLTest:
    """Eager DSL-time validation tests."""

    def test_rejects_non_upper_case(self) -> None:
        from piketype.dsl import Enum

        with pytest.raises(ValidationError) as ctx:
            Enum().add_value("lowercase")
        assert "UPPER_CASE" in str(ctx.value)

    def test_rejects_duplicate_name(self) -> None:
        from piketype.dsl import Enum

        with pytest.raises(ValidationError) as ctx:
            Enum().add_value("A", 0).add_value("A", 1)
        assert "duplicate" in str(ctx.value)

    def test_rejects_negative_value(self) -> None:
        from piketype.dsl import Enum

        with pytest.raises(ValidationError) as ctx:
            Enum().add_value("A", -1)
        assert "non-negative" in str(ctx.value)

    def test_rejects_width_zero(self) -> None:
        from piketype.dsl import Enum

        with pytest.raises(ValidationError) as ctx:
            Enum(0)
        assert "[1, 64]" in str(ctx.value)

    def test_rejects_width_65(self) -> None:
        from piketype.dsl import Enum

        with pytest.raises(ValidationError) as ctx:
            Enum(65)
        assert "[1, 64]" in str(ctx.value)

    def test_rejects_float_width(self) -> None:
        from piketype.dsl import Enum

        with pytest.raises(ValidationError) as ctx:
            Enum(1.5)  # type: ignore[arg-type]
        assert "integer" in str(ctx.value)

    def test_auto_fill_sequential(self) -> None:
        from piketype.dsl import Enum
        from piketype.dsl.freeze import _resolve_enum_values

        e = Enum().add_value("A", 0).add_value("B", 2).add_value("C").add_value("D")
        resolved = _resolve_enum_values(e)
        assert resolved == [("A", 0), ("B", 2), ("C", 3), ("D", 4)]

    def test_explicit_width(self) -> None:
        from piketype.dsl import Enum

        e = Enum(8).add_value("A", 0)
        assert e.width == 8

    def test_inferred_width(self) -> None:
        from piketype.dsl import Enum

        e = Enum().add_value("A", 0).add_value("B", 7)
        assert e.width == 3


# ---------------------------------------------------------------------------
# Validation-level tests
# ---------------------------------------------------------------------------


class EnumValidationTest:
    """IR-level validation tests."""

    def test_rejects_empty_enum(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            _validate_enum("empty_t", [])
        assert "at least one value" in str(ctx.value)

    def test_rejects_duplicate_resolved_values(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            _validate_enum("dup_t", [("A", 1), ("B", 1)])
        assert "duplicate resolved value" in str(ctx.value)

    def test_rejects_invalid_type_name_style(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            _validate_enum("no_suffix", [("A", 0)])
        assert "must be CapWords or lower_snake_case ending with _t" in str(ctx.value)

    def test_rejects_value_exceeds_width(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            _validate_enum("small_t", [("A", 4)], width=2)
        assert "does not fit" in str(ctx.value)

    def test_accepts_valid_enum(self) -> None:
        _validate_enum("ok_t", [("A", 0), ("B", 1), ("C", 2)])

    def test_accepts_capwords_type_name(self) -> None:
        _validate_enum("OkEnum", [("A", 0), ("B", 1), ("C", 2)])

    def test_accepts_explicit_width_larger_than_minimum(self) -> None:
        _validate_enum("wide_t", [("A", 0), ("B", 1)], width=8)

    def test_rejects_enum_literal_collision_with_constant(self) -> None:
        """FR-17: Enum value name collides with constant name."""
        from piketype.ir.nodes import ConstIR

        source = SourceSpanIR(path="test.py", line=1, column=None)
        ref = ModuleRefIR(
            repo_relative_path="foo/piketype/defs.py",
            python_module_name="foo.piketype.defs",
            namespace_parts=("foo", "piketype", "defs"),
            basename="defs",
        )
        const_ir = ConstIR(
            name="IDLE",
            source=source,
            expr=IntLiteralExprIR(value=0, source=source),
            resolved_value=0,
            resolved_signed=True,
            resolved_width=32,
        )
        enum_ir = _make_enum_ir("state_t", [("IDLE", 0)])
        module_ir = ModuleIR(
            ref=ref,
            source=source,
            constants=(const_ir,),
            types=(enum_ir,),
            dependencies=(),
        )
        repo = RepoIR(repo_root="/tmp/test", modules=(module_ir,), tool_version=None)
        with pytest.raises(ValidationError) as ctx:
            validate_repo(repo)
        assert "collides with constant" in str(ctx.value)

    def test_rejects_cross_enum_literal_collision(self) -> None:
        """FR-17: Same value name in two different enums."""
        source = SourceSpanIR(path="test.py", line=1, column=None)
        ref = ModuleRefIR(
            repo_relative_path="foo/piketype/defs.py",
            python_module_name="foo.piketype.defs",
            namespace_parts=("foo", "piketype", "defs"),
            basename="defs",
        )
        enum1 = _make_enum_ir("state_t", [("IDLE", 0)])
        enum2 = _make_enum_ir("mode_t", [("IDLE", 0)])
        module_ir = ModuleIR(
            ref=ref,
            source=source,
            constants=(),
            types=(enum1, enum2),
            dependencies=(),
        )
        repo = RepoIR(repo_root="/tmp/test", modules=(module_ir,), tool_version=None)
        with pytest.raises(ValidationError) as ctx:
            validate_repo(repo)
        assert "collides with value in enum" in str(ctx.value)


# ---------------------------------------------------------------------------
# Golden file tests
# ---------------------------------------------------------------------------


class EnumGoldenTest:
    """Golden file comparison tests."""

    def setup_method(self) -> None:
        self.tmp = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        shutil.rmtree(self.tmp)

    def test_enum_basic(self) -> None:
        repo_dir = _gen_fixture("enum_basic", Path(self.tmp))
        gen_root = repo_dir
        golden_root = TESTS_DIR / "goldens" / "gen" / "enum_basic"
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

    def test_enum_basic_idempotent(self) -> None:
        repo_dir = _gen_fixture("enum_basic", Path(self.tmp))
        gen_root = repo_dir
        first_run: dict[str, str] = {}
        for f in gen_root.rglob("*"):
            if f.is_dir():
                continue
            if "__pycache__" in f.parts or f.suffix == ".pyc":
                continue
            first_run[str(f.relative_to(gen_root))] = f.read_text(encoding="utf-8")
        cli_file = repo_dir / "foo" / "piketype" / "defs.py"
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


class EnumRuntimeTest:
    """Python runtime round-trip tests with explicit byte vectors."""

    _tmp_dir: tempfile.TemporaryDirectory[str]
    _gen_py: Path

    @classmethod
    def setup_class(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp_dir.name)
        cls._gen_py = _gen_fixture("enum_basic", tmp)

    @classmethod
    def teardown_class(cls) -> None:
        cls._tmp_dir.cleanup()

    def _import_types(self):
        for key in list(sys.modules.keys()):
            if key == "foo" or key.startswith("foo."):
                del sys.modules[key]
        sys.path[:] = [p for p in sys.path if "/py" not in str(p)]
        sys.path.insert(0, str(self._gen_py / "py"))
        return importlib.import_module("foo.defs_types")

    # -- color_t (4-bit, values 0, 5, 10) --

    def test_color_to_bytes_red(self) -> None:
        mod = self._import_types()
        obj = mod.color_ct(mod.color_enum_t.RED)
        assert obj.to_bytes() == b"\x00"

    def test_color_to_bytes_blue(self) -> None:
        mod = self._import_types()
        obj = mod.color_ct(mod.color_enum_t.BLUE)
        assert obj.to_bytes() == b"\x0a"

    def test_color_from_bytes_green(self) -> None:
        mod = self._import_types()
        obj = mod.color_ct.from_bytes(b"\x05")
        assert obj.value == mod.color_enum_t.GREEN

    def test_color_from_bytes_rejects_unknown(self) -> None:
        mod = self._import_types()
        with pytest.raises(ValueError):
            mod.color_ct.from_bytes(b"\x03")

    def test_color_constructor_rejects_int(self) -> None:
        mod = self._import_types()
        with pytest.raises(TypeError):
            mod.color_ct(5)

    def test_color_clone(self) -> None:
        mod = self._import_types()
        obj = mod.color_ct(mod.color_enum_t.GREEN)
        cloned = obj.clone()
        assert obj == cloned
        assert obj is not cloned

    def test_color_int(self) -> None:
        mod = self._import_types()
        obj = mod.color_ct(mod.color_enum_t.BLUE)
        assert int(obj) == 10

    def test_color_repr(self) -> None:
        mod = self._import_types()
        obj = mod.color_ct(mod.color_enum_t.RED)
        assert "color_ct" in repr(obj)

    # -- cmd_t (8-bit explicit width, auto-fill values 0, 5, 6, 7) --

    def test_cmd_to_bytes_nop(self) -> None:
        mod = self._import_types()
        obj = mod.cmd_ct(mod.cmd_enum_t.NOP)
        assert obj.to_bytes() == b"\x00"

    def test_cmd_to_bytes_reset(self) -> None:
        mod = self._import_types()
        obj = mod.cmd_ct(mod.cmd_enum_t.RESET)
        assert obj.to_bytes() == b"\x07"

    def test_cmd_from_bytes_rejects_unknown(self) -> None:
        mod = self._import_types()
        with pytest.raises(ValueError):
            mod.cmd_ct.from_bytes(b"\x08")

    # -- flag_t (1-bit, single value SET=0) --

    def test_flag_to_bytes(self) -> None:
        mod = self._import_types()
        obj = mod.flag_ct(mod.flag_enum_t.SET)
        assert obj.to_bytes() == b"\x00"

    def test_flag_from_bytes_rejects_unknown(self) -> None:
        mod = self._import_types()
        with pytest.raises(ValueError):
            mod.flag_ct.from_bytes(b"\x01")

    # -- big_t (64-bit, value 2**63) --

    def test_big_to_bytes_large(self) -> None:
        mod = self._import_types()
        obj = mod.big_ct(mod.big_enum_t.LARGE)
        assert obj.to_bytes() == b"\x80\x00\x00\x00\x00\x00\x00\x00"

    def test_big_from_bytes_small(self) -> None:
        mod = self._import_types()
        obj = mod.big_ct.from_bytes(b"\x00\x00\x00\x00\x00\x00\x00\x00")
        assert obj.value == mod.big_enum_t.SMALL

    def test_eq(self) -> None:
        mod = self._import_types()
        a = mod.color_ct(mod.color_enum_t.RED)
        b = mod.color_ct(mod.color_enum_t.RED)
        assert a == b

    def test_neq(self) -> None:
        mod = self._import_types()
        a = mod.color_ct(mod.color_enum_t.RED)
        b = mod.color_ct(mod.color_enum_t.BLUE)
        assert a != b
