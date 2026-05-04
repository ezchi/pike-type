"""Direct RepoIR unit tests for validation extensions (FR-5, etc.)."""

from __future__ import annotations

import pytest

from piketype.errors import ValidationError
from piketype.ir.nodes import (
    ModuleIR,
    ModuleRefIR,
    RepoIR,
    ScalarAliasIR,
    SourceSpanIR,
    StructFieldIR,
    StructIR,
    TypeRefIR,
    IntLiteralExprIR,
)
from piketype.validate.engine import validate_repo


def _src() -> SourceSpanIR:
    return SourceSpanIR(path="x.py", line=1, column=None)


def _ref(*, basename: str) -> ModuleRefIR:
    return ModuleRefIR(
        repo_relative_path=f"alpha/piketype/{basename}.py",
        python_module_name=f"alpha.piketype.{basename}",
        namespace_parts=("alpha", "piketype", basename),
        basename=basename,
    )


class UnknownTypeRejectionTests:
    """FR-5: TypeRefIR pointing at an unknown (module, name) is rejected."""

    def test_unknown_target_module_raises(self) -> None:
        # bar's struct references foo::missing_t, but foo has no such type.
        foo_ref = _ref(basename="foo")
        bar_ref = _ref(basename="bar")

        struct_in_bar = StructIR(
            name="bar_t",
            source=_src(),
            fields=(
                StructFieldIR(
                    name="x",
                    source=_src(),
                    type_ir=TypeRefIR(module=foo_ref, name="missing_t", source=_src()),
                    rand=True,
                    padding_bits=0,
                ),
            ),
            alignment_bits=0,
        )
        # foo defines unrelated_t; missing_t is not present.
        unrelated = ScalarAliasIR(
            name="unrelated_t",
            source=_src(),
            state_kind="logic",
            signed=False,
            width_expr=IntLiteralExprIR(value=8, source=_src()),
            resolved_width=8,
        )
        foo_module = ModuleIR(ref=foo_ref, source=_src(), constants=(), types=(unrelated,), dependencies=())
        bar_module = ModuleIR(ref=bar_ref, source=_src(), constants=(), types=(struct_in_bar,), dependencies=())
        repo = RepoIR(repo_root=".", modules=(foo_module, bar_module), tool_version=None)

        with pytest.raises(ValidationError) as ctx:
            validate_repo(repo)
        msg = str(ctx.value)
        # Error must include both module and type name.
        assert "alpha.piketype.foo" in msg
        assert "missing_t" in msg
        assert "references unknown type" in msg


class CrossModuleTypeRefAcceptedTests:
    """FR-5: cross-module TypeRefIR with a known target validates."""

    def test_cross_module_scalar_alias_accepted(self) -> None:
        foo_ref = _ref(basename="foo")
        bar_ref = _ref(basename="bar")

        byte_t = ScalarAliasIR(
            name="byte_t",
            source=_src(),
            state_kind="logic",
            signed=False,
            width_expr=IntLiteralExprIR(value=8, source=_src()),
            resolved_width=8,
        )
        struct_in_bar = StructIR(
            name="bar_t",
            source=_src(),
            fields=(
                StructFieldIR(
                    name="x",
                    source=_src(),
                    type_ir=TypeRefIR(module=foo_ref, name="byte_t", source=_src()),
                    rand=True,
                    padding_bits=0,
                ),
            ),
            alignment_bits=0,
        )
        foo_module = ModuleIR(ref=foo_ref, source=_src(), constants=(), types=(byte_t,), dependencies=())
        bar_module = ModuleIR(ref=bar_ref, source=_src(), constants=(), types=(struct_in_bar,), dependencies=())
        repo = RepoIR(repo_root=".", modules=(foo_module, bar_module), tool_version=None)

        # Should not raise.
        validate_repo(repo)


def _enum(*, name: str, value_name: str = "IDLE") -> "EnumIR":
    from piketype.ir.nodes import EnumIR, EnumValueIR
    return EnumIR(
        name=name,
        source=_src(),
        width_expr=IntLiteralExprIR(value=2, source=_src()),
        resolved_width=2,
        values=(
            EnumValueIR(name=value_name, source=_src(), expr=IntLiteralExprIR(value=0, source=_src()), resolved_value=0),
        ),
    )


def _struct_with_field(*, name: str, target_module: ModuleRefIR, target_type_name: str) -> StructIR:
    return StructIR(
        name=name,
        source=_src(),
        fields=(
            StructFieldIR(
                name="x",
                source=_src(),
                type_ir=TypeRefIR(module=target_module, name=target_type_name, source=_src()),
                rand=True,
                padding_bits=0,
            ),
        ),
        alignment_bits=0,
    )


class CrossModuleStructCycleTests:
    """FR-6: cross-module struct cycles are detected."""

    def test_two_node_cross_module_cycle(self) -> None:
        # foo::a_t -> bar::b_t -> foo::a_t
        foo_ref = _ref(basename="foo")
        bar_ref = _ref(basename="bar")
        a_t = _struct_with_field(name="a_t", target_module=bar_ref, target_type_name="b_t")
        b_t = _struct_with_field(name="b_t", target_module=foo_ref, target_type_name="a_t")
        foo_module = ModuleIR(ref=foo_ref, source=_src(), constants=(), types=(a_t,), dependencies=())
        bar_module = ModuleIR(ref=bar_ref, source=_src(), constants=(), types=(b_t,), dependencies=())
        repo = RepoIR(repo_root=".", modules=(foo_module, bar_module), tool_version=None)
        with pytest.raises(ValidationError) as ctx:
            validate_repo(repo)
        assert "recursive cross-module struct dependency detected" in str(ctx.value)


class CrossModuleNameCollisionTests:
    """FR-8: name collision rules."""

    def test_local_vs_imported_type_name(self) -> None:
        foo_ref = _ref(basename="foo")
        bar_ref = _ref(basename="bar")
        # foo defines byte_t; bar defines its own byte_t locally AND has a struct
        # field referencing foo::byte_t.
        foo_byte_t = ScalarAliasIR(
            name="byte_t", source=_src(), state_kind="logic", signed=False,
            width_expr=IntLiteralExprIR(value=8, source=_src()), resolved_width=8,
        )
        bar_byte_t = ScalarAliasIR(
            name="byte_t", source=_src(), state_kind="logic", signed=False,
            width_expr=IntLiteralExprIR(value=8, source=_src()), resolved_width=8,
        )
        bar_t = _struct_with_field(name="bar_t", target_module=foo_ref, target_type_name="byte_t")
        foo_module = ModuleIR(ref=foo_ref, source=_src(), constants=(), types=(foo_byte_t,), dependencies=())
        bar_module = ModuleIR(ref=bar_ref, source=_src(), constants=(), types=(bar_byte_t, bar_t), dependencies=())
        repo = RepoIR(repo_root=".", modules=(foo_module, bar_module), tool_version=None)
        with pytest.raises(ValidationError) as ctx:
            validate_repo(repo)
        assert "shadows cross-module reference" in str(ctx.value)
