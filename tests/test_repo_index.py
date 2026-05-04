"""Tests for build_repo_type_index (FR-7)."""

from __future__ import annotations


from piketype.ir.nodes import (
    EnumIR,
    EnumValueIR,
    FlagFieldIR,
    FlagsIR,
    IntLiteralExprIR,
    ModuleIR,
    ModuleRefIR,
    RepoIR,
    ScalarAliasIR,
    SourceSpanIR,
    StructFieldIR,
    StructIR,
    TypeRefIR,
)
from piketype.ir.repo_index import build_repo_type_index


def _src() -> SourceSpanIR:
    return SourceSpanIR(path="x", line=1, column=None)


def _scalar(name: str) -> ScalarAliasIR:
    return ScalarAliasIR(
        name=name,
        source=_src(),
        state_kind="logic",
        signed=False,
        width_expr=IntLiteralExprIR(value=8, source=_src()),
        resolved_width=8,
    )


def _ref(*, repo_relative: str, python_module: str, basename: str) -> ModuleRefIR:
    return ModuleRefIR(
        repo_relative_path=repo_relative,
        python_module_name=python_module,
        namespace_parts=tuple(python_module.split(".")) ,
        basename=basename,
    )


class BuildRepoTypeIndexTests:
    def test_empty_repo_returns_empty_index(self) -> None:
        repo = RepoIR(repo_root=".", modules=(), tool_version=None)
        assert build_repo_type_index(repo) == {}

    def test_single_module_with_one_type(self) -> None:
        ref = _ref(repo_relative="alpha/piketype/foo.py", python_module="alpha.piketype.foo", basename="foo")
        module = ModuleIR(
            ref=ref,
            source=_src(),
            constants=(),
            types=(_scalar("byte_t"),),
            dependencies=(),
        )
        repo = RepoIR(repo_root=".", modules=(module,), tool_version=None)
        index = build_repo_type_index(repo)
        assert set(index.keys()) == {("alpha.piketype.foo", "byte_t")}
        assert index[("alpha.piketype.foo", "byte_t")] is module.types[0]

    def test_multi_module_same_type_name_distinct_keys(self) -> None:
        ref_a = _ref(repo_relative="a/piketype/foo.py", python_module="a.piketype.foo", basename="foo")
        ref_b = _ref(repo_relative="b/piketype/bar.py", python_module="b.piketype.bar", basename="bar")
        mod_a = ModuleIR(ref=ref_a, source=_src(), constants=(), types=(_scalar("shared_t"),), dependencies=())
        mod_b = ModuleIR(ref=ref_b, source=_src(), constants=(), types=(_scalar("shared_t"),), dependencies=())
        repo = RepoIR(repo_root=".", modules=(mod_a, mod_b), tool_version=None)
        index = build_repo_type_index(repo)
        assert len(index) == 2
        assert index[("a.piketype.foo", "shared_t")] is mod_a.types[0]
        assert index[("b.piketype.bar", "shared_t")] is mod_b.types[0]
        assert index[("a.piketype.foo", "shared_t")] is not index[("b.piketype.bar", "shared_t")]

    def test_multiple_type_kinds_indexed(self) -> None:
        ref = _ref(repo_relative="alpha/piketype/foo.py", python_module="alpha.piketype.foo", basename="foo")
        struct = StructIR(
            name="hdr_t",
            source=_src(),
            fields=(
                StructFieldIR(
                    name="x",
                    source=_src(),
                    type_ir=TypeRefIR(module=ref, name="byte_t", source=_src()),
                    rand=True,
                    padding_bits=0,
                ),
            ),
            alignment_bits=0,
        )
        flags = FlagsIR(name="perms_t", source=_src(), fields=(FlagFieldIR(name="read", source=_src()),), alignment_bits=7)
        enum = EnumIR(
            name="cmd_t",
            source=_src(),
            width_expr=IntLiteralExprIR(value=2, source=_src()),
            resolved_width=2,
            values=(EnumValueIR(name="IDLE", source=_src(), expr=IntLiteralExprIR(value=0, source=_src()), resolved_value=0),),
        )
        module = ModuleIR(
            ref=ref,
            source=_src(),
            constants=(),
            types=(_scalar("byte_t"), struct, flags, enum),
            dependencies=(),
        )
        repo = RepoIR(repo_root=".", modules=(module,), tool_version=None)
        index = build_repo_type_index(repo)
        assert len(index) == 4
        for type_name in ("byte_t", "hdr_t", "perms_t", "cmd_t"):
            assert ("alpha.piketype.foo", type_name) in index
