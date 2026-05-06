"""Round-trip tests for IR cache encode/decode and on-disk read/write."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from piketype.config import load_config
from piketype.ir.nodes import (
    BinaryExprIR,
    ConstIR,
    EnumIR,
    EnumValueIR,
    FlagFieldIR,
    FlagsIR,
    IntLiteralExprIR,
    ModuleDependencyIR,
    ModuleIR,
    ModuleRefIR,
    RepoIR,
    ScalarAliasIR,
    ScalarTypeSpecIR,
    SourceSpanIR,
    StructFieldIR,
    StructIR,
    TypeRefIR,
    UnaryExprIR,
    VecConstImportIR,
    VecConstIR,
)
from piketype.ir_io import (
    IRSchemaMismatchError,
    SCHEMA_VERSION,
    decode_repo,
    encode_repo,
    read_cache,
    write_cache,
)


def _src(path: str = "alpha/piketype/foo.py", line: int = 1) -> SourceSpanIR:
    return SourceSpanIR(path=path, line=line, column=None)


def _module_ref(name: str = "foo") -> ModuleRefIR:
    return ModuleRefIR(
        repo_relative_path=f"alpha/piketype/{name}.py",
        python_module_name=f"alpha.piketype.{name}",
        namespace_parts=("alpha", "piketype", name),
        basename=name,
    )


def _build_repo() -> RepoIR:
    """Construct a RepoIR exercising every IR node kind."""
    src = _src()
    foo_ref = _module_ref("foo")
    bar_ref = _module_ref("bar")

    # Expressions: int, ref, unary, binary
    int_lit = IntLiteralExprIR(value=8, source=src)
    unary = UnaryExprIR(op="-", operand=int_lit, source=src)
    binary = BinaryExprIR(op="+", lhs=int_lit, rhs=unary, source=src)

    # Types
    scalar = ScalarAliasIR(
        name="byte_t", source=src, state_kind="logic", signed=False,
        width_expr=int_lit, resolved_width=8,
    )
    scalar_spec = ScalarTypeSpecIR(
        source=src, state_kind="logic", signed=True,
        width_expr=int_lit, resolved_width=8,
    )
    type_ref = TypeRefIR(module=bar_ref, name="other_t", source=src)
    struct = StructIR(
        name="addr_t",
        source=src,
        fields=(
            StructFieldIR(name="lo", source=src, type_ir=scalar_spec, rand=False),
            StructFieldIR(name="hi", source=src, type_ir=type_ref, rand=True, padding_bits=4),
        ),
        alignment_bits=8,
    )
    flags = FlagsIR(
        name="perms_t", source=src,
        fields=(FlagFieldIR(name="r", source=src), FlagFieldIR(name="w", source=src)),
    )
    enum = EnumIR(
        name="cmd_t", source=src, width_expr=int_lit, resolved_width=2,
        values=(
            EnumValueIR(name="IDLE", source=src, expr=int_lit, resolved_value=0),
            EnumValueIR(name="GO", source=src, expr=binary, resolved_value=8),
        ),
    )

    const = ConstIR(
        name="LP_X", source=src, expr=binary,
        resolved_value=8, resolved_signed=False, resolved_width=4,
    )
    vec = VecConstIR(name="LP_V", source=src, width=8, value=0xAA, base="hex")
    vec_imp = VecConstImportIR(target_module_ref=bar_ref, symbol_name="LP_Y")
    dep = ModuleDependencyIR(target=bar_ref, kind="type_ref")

    module = ModuleIR(
        ref=foo_ref,
        source=src,
        constants=(const,),
        types=(scalar, struct, flags, enum),
        dependencies=(dep,),
        vec_constants=(vec,),
        vec_const_imports=(vec_imp,),
    )
    return RepoIR(repo_root="/abs/project", modules=(module,), tool_version="0.7.0")


class TestCodecRoundTrip:
    def test_round_trip_preserves_repo(self) -> None:
        repo = _build_repo()
        encoded = encode_repo(repo)
        decoded = decode_repo(encoded)
        assert decoded == repo

    def test_encoded_is_json_safe(self) -> None:
        encoded = encode_repo(_build_repo())
        # Must round-trip through JSON without loss.
        re_encoded = json.loads(json.dumps(encoded))
        assert decode_repo(re_encoded) == decode_repo(encoded)

    def test_kind_discriminator_present(self) -> None:
        encoded = encode_repo(_build_repo())
        assert encoded["__kind__"] == "RepoIR"
        assert encoded["modules"][0]["__kind__"] == "ModuleIR"
        assert encoded["modules"][0]["types"][0]["__kind__"] == "ScalarAliasIR"

    def test_decode_unknown_kind_rejected(self) -> None:
        with pytest.raises(ValueError, match="unknown IR kind"):
            decode_repo({"__kind__": "NotAnIRType"})

    def test_decode_missing_kind_rejected(self) -> None:
        with pytest.raises(ValueError, match="missing or invalid __kind__"):
            decode_repo({"modules": []})


class TestCacheReadWrite:
    @staticmethod
    def _setup_config(tmp_path: Path) -> tuple[Path, Path]:
        (tmp_path / "alpha" / "piketype").mkdir(parents=True)
        source = tmp_path / "alpha" / "piketype" / "foo.py"
        source.write_text("# fixture\n", encoding="utf-8")
        config_path = tmp_path / "piketype.yaml"
        config_path.write_text(
            "frontend:\n  ir_cache: build/cache\n"
            "backends:\n  py: {backend_root: py}\n",
            encoding="utf-8",
        )
        return source, config_path

    def test_round_trip_through_disk(self, tmp_path: Path) -> None:
        _source, config_path = self._setup_config(tmp_path)
        config = load_config(config_path)
        repo = _build_repo()
        # Patch repo_root to tmp_path so source-hash works for the file we wrote.
        repo = RepoIR(repo_root=str(tmp_path), modules=repo.modules, tool_version=repo.tool_version)
        cache_root = write_cache(repo=repo, config=config)
        assert cache_root == config.frontend.ir_cache
        assert (cache_root / "_index.json").is_file()
        assert (cache_root / "alpha" / "piketype" / "foo.ir.json").is_file()

        decoded = read_cache(config=config)
        # Repo root in decoded is config.project_root (absolute resolved path).
        assert decoded.modules == repo.modules
        assert decoded.tool_version == repo.tool_version

    def test_index_records_schema_version(self, tmp_path: Path) -> None:
        _source, config_path = self._setup_config(tmp_path)
        config = load_config(config_path)
        repo = RepoIR(repo_root=str(tmp_path), modules=_build_repo().modules, tool_version="0.7.0")
        write_cache(repo=repo, config=config)
        index = json.loads((config.frontend.ir_cache / "_index.json").read_text())
        assert index["schema_version"] == SCHEMA_VERSION
        assert len(index["modules"]) == 1
        assert index["modules"][0]["source_hash"].startswith("sha256:")

    def test_schema_mismatch_raises(self, tmp_path: Path) -> None:
        _source, config_path = self._setup_config(tmp_path)
        config = load_config(config_path)
        repo = RepoIR(repo_root=str(tmp_path), modules=_build_repo().modules, tool_version="0.7.0")
        write_cache(repo=repo, config=config)

        index_path = config.frontend.ir_cache / "_index.json"
        idx = json.loads(index_path.read_text())
        idx["schema_version"] = 999
        index_path.write_text(json.dumps(idx))

        with pytest.raises(IRSchemaMismatchError, match="schema_version"):
            read_cache(config=config)

    def test_missing_cache_raises(self, tmp_path: Path) -> None:
        _source, config_path = self._setup_config(tmp_path)
        config = load_config(config_path)
        with pytest.raises(FileNotFoundError, match="run `piketype build`"):
            read_cache(config=config)
