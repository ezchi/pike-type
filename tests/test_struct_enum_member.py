"""Integration and runtime tests for Struct with Enum member (Spec 009)."""

from __future__ import annotations

import importlib
import os
import pytest
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from piketype.dsl import Enum, Struct, Bit
from piketype.errors import ValidationError
from piketype.ir.nodes import (
    EnumIR,
    EnumValueIR,
    IntLiteralExprIR,
    ModuleIR,
    ModuleRefIR,
    RepoIR,
    SourceSpanIR,
    StructFieldIR,
    StructIR,
    TypeRefIR,
)
from piketype.validate.engine import validate_repo


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


class StructEnumMemberDSLTest:
    """DSL acceptance tests for Enum as struct member."""

    def test_add_enum_member_accepted(self) -> None:
        """AC-1: Struct().add_member() accepts EnumType."""
        cmd_t = Enum().add_value("IDLE", 0).add_value("READ", 1).add_value("WRITE", 2)
        s = Struct().add_member("cmd", cmd_t)
        assert len(s.members) == 1
        assert s.members[0].name == "cmd"

    def test_add_enum_and_scalar_member(self) -> None:
        """Struct can have both Enum and scalar members."""
        cmd_t = Enum().add_value("A", 0)
        s = Struct().add_member("cmd", cmd_t).add_member("data", Bit(8))
        assert len(s.members) == 2

    def test_reject_invalid_type(self) -> None:
        """Non-DSL types are still rejected."""
        with pytest.raises(ValidationError):
            Struct().add_member("bad", 42)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Freeze tests
# ---------------------------------------------------------------------------


class StructEnumMemberFreezeTest:
    """Freeze pipeline tests for Enum as struct member."""

    def _make_loaded_module(self, module_dict: dict[str, object], name: str = "alpha.piketype.types"):
        """Create a LoadedModule from a dict of DSL objects."""
        import types as pytypes
        from piketype.dsl.freeze import LoadedModule

        mod = pytypes.ModuleType(name)
        # Use the first DSL object's source path as the module path
        mod_path = None
        for v in module_dict.values():
            if hasattr(v, "source"):
                mod_path = Path(v.source.path).resolve()
                break
        if mod_path is None:
            mod_path = Path("/tmp/test.py")
        mod.__dict__.update(module_dict)
        module_ref = ModuleRefIR(
            repo_relative_path=str(mod_path),
            python_module_name=name,
            namespace_parts=("alpha",),
            basename="types",
        )
        return LoadedModule(module=mod, module_path=mod_path, module_ref=module_ref)

    def _freeze_fixture(self):
        """Freeze a struct with an enum member and return FrozenModule."""
        from piketype.dsl.freeze import (
            build_const_definition_map,
            build_type_definition_map,
            freeze_module,
        )

        cmd_t = Enum().add_value("IDLE", 0).add_value("READ", 1).add_value("WRITE", 2)
        pkt_t = Struct().add_member("cmd", cmd_t).add_member("data", Bit(8))
        loaded = self._make_loaded_module({"cmd_t": cmd_t, "pkt_t": pkt_t})
        const_map = build_const_definition_map(loaded_modules=[loaded])
        type_map = build_type_definition_map(loaded_modules=[loaded])
        return freeze_module(
            loaded_module=loaded,
            definition_map=const_map,
            type_definition_map=type_map,
        )

    def test_freeze_produces_type_ref_ir(self) -> None:
        """AC-2: Frozen StructIR field has TypeRefIR pointing to EnumIR."""
        frozen = self._freeze_fixture()
        struct_types = [t for t in frozen.module_ir.types if isinstance(t, StructIR)]
        assert len(struct_types) >= 1
        pkt = struct_types[0]
        cmd_field = pkt.fields[0]
        assert isinstance(cmd_field.type_ir, TypeRefIR)
        assert cmd_field.type_ir.name == "cmd_t"

    def test_freeze_padding_bits_2bit(self) -> None:
        """AC-3: 2-bit enum gets 6 padding bits."""
        frozen = self._freeze_fixture()
        struct_types = [t for t in frozen.module_ir.types if isinstance(t, StructIR)]
        pkt = struct_types[0]
        cmd_field = pkt.fields[0]
        assert cmd_field.padding_bits == 6

    def test_freeze_padding_bits_8bit(self) -> None:
        """AC-3: 8-bit enum gets 0 padding bits."""
        from piketype.dsl.freeze import (
            build_const_definition_map,
            build_type_definition_map,
            freeze_module,
        )

        wide_t = Enum(8).add_value("A", 0).add_value("B", 255)
        s_t = Struct().add_member("w", wide_t)
        loaded = self._make_loaded_module({"wide_t": wide_t, "s_t": s_t}, name="test")
        const_map = build_const_definition_map(loaded_modules=[loaded])
        type_map = build_type_definition_map(loaded_modules=[loaded])
        frozen = freeze_module(
            loaded_module=loaded,
            definition_map=const_map,
            type_definition_map=type_map,
        )
        struct_types = [t for t in frozen.module_ir.types if isinstance(t, StructIR)]
        s = struct_types[0]
        w_field = s.fields[0]
        assert w_field.padding_bits == 0

    def test_freeze_rejects_anonymous_enum(self) -> None:
        """AC-5, AC-23: Anonymous inline Enum is rejected during freeze."""
        from piketype.dsl.freeze import (
            build_const_definition_map,
            build_type_definition_map,
            freeze_module,
        )

        anon_enum = Enum().add_value("X", 0)
        s_t = Struct().add_member("e", anon_enum)
        loaded = self._make_loaded_module({"s_t": s_t}, name="test")
        const_map = build_const_definition_map(loaded_modules=[loaded])
        type_map = build_type_definition_map(loaded_modules=[loaded])
        with pytest.raises(ValidationError) as ctx:
            freeze_module(
                loaded_module=loaded,
                definition_map=const_map,
                type_definition_map=type_map,
            )
        assert "anonymous enum" in str(ctx.value)


# ---------------------------------------------------------------------------
# Golden file comparison tests
# ---------------------------------------------------------------------------


class StructEnumMemberGoldenTest:
    """Golden file comparison tests for struct_enum_member fixture."""

    def setup_method(self) -> None:
        self.tmp = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        shutil.rmtree(self.tmp)

    def test_golden_match(self) -> None:
        """AC-6–9, AC-10, AC-14, AC-15, AC-19: Golden file integration tests pass."""
        repo_dir = gen_fixture("struct_enum_member", Path(self.tmp))
        gen_root = repo_dir
        golden_root = TESTS_DIR / "goldens" / "gen" / "struct_enum_member"
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
        """AC-20: piketype gen is idempotent."""
        repo_dir = gen_fixture("struct_enum_member", Path(self.tmp))
        gen_root = repo_dir
        first_run: dict[str, str] = {}
        for f in gen_root.rglob("*"):
            if f.is_dir():
                continue
            if "__pycache__" in f.parts or f.suffix == ".pyc":
                continue
            first_run[str(f.relative_to(gen_root))] = f.read_text(encoding="utf-8")
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
# Python runtime tests
# ---------------------------------------------------------------------------


class StructEnumMemberRuntimeTest:
    """Python runtime tests for struct with Enum member."""

    _tmp_dir: tempfile.TemporaryDirectory[str]
    _gen_py: Path

    @classmethod
    def setup_class(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp_dir.name)
        cls._gen_py = gen_fixture("struct_enum_member", tmp)

    @classmethod
    def teardown_class(cls) -> None:
        cls._tmp_dir.cleanup()

    def _import_types(self):
        for key in list(sys.modules.keys()):
            if key == "alpha" or key.startswith("alpha."):
                del sys.modules[key]
        sys.path[:] = [p for p in sys.path if "/py" not in str(p)]
        sys.path.insert(0, str(self._gen_py))
        return importlib.import_module("alpha.py.types_types")

    def test_round_trip(self) -> None:
        """AC-12, AC-13: to_bytes -> from_bytes round-trip for pkt_t."""
        mod = self._import_types()
        pkt = mod.pkt_ct()
        pkt.cmd = mod.cmd_ct(mod.cmd_enum_t.WRITE)
        pkt.data = 42
        raw = pkt.to_bytes()
        restored = mod.pkt_ct.from_bytes(raw)
        assert int(restored.cmd.value) == int(mod.cmd_enum_t.WRITE)
        assert restored.data == 42

    def test_expected_bytes(self) -> None:
        """AC-18: to_bytes produces specific expected byte values."""
        mod = self._import_types()
        pkt = mod.pkt_ct()
        pkt.cmd = mod.cmd_ct(mod.cmd_enum_t.WRITE)  # WRITE=2
        pkt.data = 0xFF
        raw = pkt.to_bytes()
        # cmd_t: 2-bit enum, WRITE=2 -> 1 byte: 0x02 (6 MSB padding bits = 0)
        # data: 8 bits -> 1 byte: 0xFF
        assert raw == b"\x02\xff"

    def test_multiple_of_byte_count(self) -> None:
        """AC-16, AC-17: multiple_of() struct has correct byte count."""
        mod = self._import_types()
        aligned = mod.aligned_pkt_ct()
        raw = aligned.to_bytes()
        # aligned_pkt_t: cmd (1 byte) + data (1 byte) = 2 bytes natural
        # multiple_of(32) -> 4 bytes
        assert len(raw) == 4

    def test_coercer_rejects_none(self) -> None:
        """AC-11: Enum field coercer rejects None."""
        mod = self._import_types()
        pkt = mod.pkt_ct()
        with pytest.raises(TypeError):
            pkt.cmd = None  # type: ignore[assignment]

    def test_coercer_rejects_raw_enum(self) -> None:
        """AC-11: Enum field coercer rejects raw IntEnum value."""
        mod = self._import_types()
        pkt = mod.pkt_ct()
        with pytest.raises(TypeError):
            pkt.cmd = mod.cmd_enum_t.WRITE  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Negative tests
# ---------------------------------------------------------------------------


class StructEnumMemberCrossModuleTest:
    """Cross-module Enum references are accepted (spec 011 relaxes the spec 009 restriction)."""

    def test_cross_module_enum_accepted(self) -> None:
        """Spec 011 FR-5: a struct field referencing an Enum from another module passes validation."""
        src = SourceSpanIR(path="test.py", line=1, column=0)
        module_a_ref = ModuleRefIR(
            repo_relative_path="a/piketype/types.py",
            python_module_name="a.piketype.types",
            namespace_parts=("a",),
            basename="types",
        )
        module_b_ref = ModuleRefIR(
            repo_relative_path="b/piketype/types.py",
            python_module_name="b.piketype.types",
            namespace_parts=("b",),
            basename="types",
        )
        enum_ir = EnumIR(
            name="cmd_t",
            source=src,
            width_expr=IntLiteralExprIR(source=src, value=2),
            resolved_width=2,
            values=(
                EnumValueIR(
                    name="IDLE",
                    source=src,
                    expr=IntLiteralExprIR(source=src, value=0),
                    resolved_value=0,
                ),
            ),
        )
        struct_ir = StructIR(
            name="pkt_t",
            source=src,
            fields=(
                StructFieldIR(
                    name="cmd",
                    source=src,
                    type_ir=TypeRefIR(module=module_a_ref, name="cmd_t", source=src),
                    rand=True,
                    padding_bits=6,
                ),
            ),
        )
        module_a = ModuleIR(
            ref=module_a_ref,
            source=src,
            constants=(),
            types=(enum_ir,),
            dependencies=(),
        )
        module_b = ModuleIR(
            ref=module_b_ref,
            source=src,
            constants=(),
            types=(struct_ir,),
            dependencies=(),
        )
        repo = RepoIR(repo_root="/tmp", modules=(module_a, module_b), tool_version=None)
        # Should not raise — cross-module references are now allowed.
        validate_repo(repo)
