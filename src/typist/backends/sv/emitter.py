"""SystemVerilog backend."""

from __future__ import annotations

from pathlib import Path

from typist.backends.common.headers import render_header
from typist.ir.nodes import BinaryExprIR, ConstRefExprIR, IntLiteralExprIR, ModuleIR, RepoIR, ScalarAliasIR, UnaryExprIR
from typist.paths import sv_module_output_path


def emit_sv(repo: RepoIR) -> list[Path]:
    """Emit SystemVerilog package files for all modules."""
    written_paths: list[Path] = []
    repo_root = Path(repo.repo_root)
    for module in repo.modules:
        output_path = sv_module_output_path(
            repo_root=repo_root,
            module_path=repo_root / module.ref.repo_relative_path,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_module_sv(module), encoding="utf-8")
        written_paths.append(output_path)
    return written_paths


def render_module_sv(module: ModuleIR) -> str:
    """Render a constant-only SystemVerilog package."""
    header = render_header(source_paths=(module.ref.repo_relative_path,))
    body_lines = [f"package {module.ref.basename}_pkg;"]
    for const in module.constants:
        sv_type, sv_literal = _render_sv_const(
            value=const.resolved_value,
            signed=const.resolved_signed,
            width=const.resolved_width,
        )
        if isinstance(const.expr, IntLiteralExprIR):
            sv_expr = sv_literal
        else:
            sv_expr = _render_sv_expr(expr=const.expr)
        body_lines.append(f"  localparam {sv_type} {const.name} = {sv_expr};")
    for scalar_alias in module.types:
        body_lines.append(f"  {_render_sv_scalar_alias(type_ir=scalar_alias)}")
    body_lines.append("endpackage")
    return f"{header}\n" + "\n".join(body_lines) + "\n"


def _render_sv_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
    """Choose a safe SystemVerilog constant type and literal spelling."""
    if width == 32 and signed:
        return ("int", _sv_signed_literal(width=32, value=value))
    if width == 32 and not signed:
        return ("int unsigned", f"32'd{value}")
    if width == 64 and signed:
        return ("longint", _sv_signed_literal(width=64, value=value))
    if width == 64 and not signed:
        return ("longint unsigned", f"64'd{value}")
    raise ValueError(f"unsupported SystemVerilog constant storage: signed={signed}, width={width}")


def _sv_signed_literal(*, width: int, value: int) -> str:
    """Render a signed decimal SystemVerilog literal."""
    if value < 0:
        return f"-{width}'sd{abs(value)}"
    return f"{width}'sd{value}"


def _render_sv_expr(*, expr: IntLiteralExprIR | ConstRefExprIR | UnaryExprIR | BinaryExprIR) -> str:
    """Render an expression into SystemVerilog syntax."""
    match expr:
        case IntLiteralExprIR(value=value):
            return str(value)
        case ConstRefExprIR(name=name):
            return name
        case UnaryExprIR(op=op, operand=operand):
            return f"({op}{_render_sv_expr(expr=operand)})"
        case BinaryExprIR(op=op, lhs=lhs, rhs=rhs):
            return f"({_render_sv_expr(expr=lhs)} {op} {_render_sv_expr(expr=rhs)})"
        case _:
            raise ValueError(f"unsupported SV expression node {type(expr).__name__}")


def _render_sv_scalar_alias(*, type_ir: ScalarAliasIR) -> str:
    """Render a named scalar typedef."""
    base_type = type_ir.state_kind
    signed_kw = " signed" if type_ir.signed else ""
    width_expr = _render_sv_expr(expr=type_ir.width_expr)
    if type_ir.resolved_width == 1:
        return f"typedef {base_type}{signed_kw} {type_ir.name};"
    return f"typedef {base_type}{signed_kw} [{width_expr}-1:0] {type_ir.name};"
