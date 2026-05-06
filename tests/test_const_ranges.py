"""Boundary tests for constant type rendering and supported range."""

from __future__ import annotations

import pytest

from piketype.backends.cpp.view import _render_cpp_const
from piketype.backends.sv.view import _render_sv_const
from piketype.dsl.freeze import _resolve_const_storage
from piketype.errors import ValidationError
from piketype.ir.nodes import ConstIR, IntLiteralExprIR, ModuleIR, ModuleRefIR, RepoIR, SourceSpanIR
from piketype.validate.engine import validate_repo


class ConstRangeTest:
    """Lock down supported constant boundaries."""

    def test_cpp_const_boundaries(self) -> None:
        assert _render_cpp_const(value=-(2**31), signed=True, width=32) == ("int32_t", str(-(2**31)))
        assert _render_cpp_const(value=2**31 - 1, signed=True, width=32) == ("int32_t", str(2**31 - 1))
        assert _render_cpp_const(value=2**31, signed=False, width=32) == ("uint32_t", f"{2**31}U")
        assert _render_cpp_const(value=2**32 - 1, signed=False, width=32) == ("uint32_t", f"{2**32 - 1}U")
        assert _render_cpp_const(value=-(2**63), signed=True, width=64) == ("int64_t", f"-{2**63}LL")
        assert _render_cpp_const(value=2**63 - 1, signed=True, width=64) == ("int64_t", f"{2**63 - 1}LL")
        assert _render_cpp_const(value=2**63, signed=False, width=64) == ("uint64_t", f"{2**63}ULL")
        assert _render_cpp_const(value=2**64 - 1, signed=False, width=64) == ("uint64_t", f"{2**64 - 1}ULL")

    def test_sv_const_boundaries(self) -> None:
        assert _render_sv_const(value=-(2**31), signed=True, width=32) == ("int", f"-32'sd{2**31}")
        assert _render_sv_const(value=2**31 - 1, signed=True, width=32) == ("int", f"32'sd{2**31 - 1}")
        assert _render_sv_const(value=2**31, signed=False, width=32) == ("int unsigned", f"32'd{2**31}")
        assert _render_sv_const(value=2**32 - 1, signed=False, width=32) == ("int unsigned", f"32'd{2**32 - 1}")
        assert _render_sv_const(value=-(2**63), signed=True, width=64) == ("longint", f"-64'sd{2**63}")
        assert _render_sv_const(value=2**63 - 1, signed=True, width=64) == ("longint", f"64'sd{2**63 - 1}")
        assert _render_sv_const(value=2**63, signed=False, width=64) == ("longint unsigned", f"64'd{2**63}")
        assert _render_sv_const(value=2**64 - 1, signed=False, width=64) == ("longint unsigned", f"64'd{2**64 - 1}")

    def test_storage_resolution_defaults_and_overrides(self) -> None:
        assert _resolve_const_storage(value=3, signed=None, width=None) == (True, 32)
        assert _resolve_const_storage(value=3, signed=False, width=32) == (False, 32)
        assert _resolve_const_storage(value=2**40, signed=False, width=None) == (False, 64)
        assert _resolve_const_storage(value=2**40, signed=True, width=None) == (True, 64)
        assert _resolve_const_storage(value=2**31, signed=False, width=None) == (False, 32)
        assert _resolve_const_storage(value=2**31, signed=True, width=None) == (True, 64)

    def test_storage_resolution_rejects_invalid_override(self) -> None:
        with pytest.raises(ValidationError, match="unsigned 32-bit constant value"):
            _resolve_const_storage(value=-1, signed=False, width=32)
        with pytest.raises(ValidationError, match="signed 32-bit constant value"):
            _resolve_const_storage(value=2**31, signed=True, width=32)

    def test_validation_rejects_above_uint64_max(self) -> None:
        repo = _repo_with_single_const(name="TOO_BIG", value=2**64)
        with pytest.raises(ValidationError, match="out of supported range"):
            validate_repo(repo)

    def test_validation_rejects_below_int64_min(self) -> None:
        repo = _repo_with_single_const(name="TOO_SMALL", value=-(2**63) - 1)
        with pytest.raises(ValidationError, match="out of supported range"):
            validate_repo(repo)


def _repo_with_single_const(*, name: str, value: int) -> RepoIR:
    source = SourceSpanIR(path="alpha/piketype/constants.py", line=1, column=None)
    const = ConstIR(
        name=name,
        source=source,
        expr=IntLiteralExprIR(value=value, source=source),
        resolved_value=value,
        resolved_signed=value < 0,
        resolved_width=64,
    )
    module = ModuleIR(
        ref=ModuleRefIR(
            repo_relative_path="alpha/piketype/constants.py",
            python_module_name="alpha.piketype.constants",
            namespace_parts=("alpha", "piketype", "constants"),
            basename="constants",
        ),
        source=source,
        constants=(const,),
        types=(),
        dependencies=(),
    )
    return RepoIR(repo_root=".", modules=(module,), tool_version="0.1.0")
