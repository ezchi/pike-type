"""C++ backend."""

from __future__ import annotations

from pathlib import Path

from typist.backends.common.headers import render_header
from typist.errors import ValidationError
from typist.ir.nodes import BinaryExprIR, ConstRefExprIR, IntLiteralExprIR, ModuleIR, RepoIR, UnaryExprIR
from typist.paths import cpp_header_output_path


def emit_cpp(repo: RepoIR) -> list[Path]:
    """Emit C++ outputs."""
    written_paths: list[Path] = []
    repo_root = Path(repo.repo_root)
    for module in repo.modules:
        output_path = cpp_header_output_path(
            repo_root=repo_root,
            module_path=repo_root / module.ref.repo_relative_path,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_module_hpp(module), encoding="utf-8")
        written_paths.append(output_path)
    return written_paths


def render_module_hpp(module: ModuleIR) -> str:
    """Render a constant-only C++ header."""
    header = render_header(source_paths=(module.ref.repo_relative_path,))
    guard = "_".join((*module.ref.namespace_parts, "types_hpp")).upper().replace(".", "_")
    namespace = "::".join(part for part in module.ref.namespace_parts if part != "typist")
    body_lines = [f"#ifndef {guard}", f"#define {guard}", "", "#include <cstdint>", ""]
    if namespace:
        body_lines.append(f"namespace {namespace} {{")
        body_lines.append("")
    for const in module.constants:
        cpp_type, cpp_literal = _render_cpp_const(
            value=const.resolved_value,
            signed=const.resolved_signed,
            width=const.resolved_width,
        )
        if isinstance(const.expr, IntLiteralExprIR):
            cpp_expr = cpp_literal
        else:
            cpp_expr = _render_cpp_expr(expr=const.expr)
        body_lines.append(f"constexpr {cpp_type} {const.name} = {cpp_expr};")
    if namespace:
        body_lines.append("")
        body_lines.append(f"}}  // namespace {namespace}")
    body_lines.extend(["", f"#endif  // {guard}"])
    return f"{header}\n" + "\n".join(body_lines) + "\n"


def _render_cpp_const(*, value: int, signed: bool, width: int) -> tuple[str, str]:
    """Choose a safe C++ constant type and literal spelling."""
    if width == 32 and signed:
        return ("std::int32_t", str(value))
    if width == 32 and not signed:
        return ("std::uint32_t", f"{value}U")
    if width == 64 and signed:
        return ("std::int64_t", f"{value}LL")
    if width == 64 and not signed:
        return ("std::uint64_t", f"{value}ULL")
    raise ValidationError(f"unsupported C++ constant storage: signed={signed}, width={width}")


def _render_cpp_expr(*, expr: IntLiteralExprIR | ConstRefExprIR | UnaryExprIR | BinaryExprIR) -> str:
    """Render an expression into C++ syntax."""
    match expr:
        case IntLiteralExprIR(value=value):
            return str(value)
        case ConstRefExprIR(name=name):
            return name
        case UnaryExprIR(op=op, operand=operand):
            return f"({op}{_render_cpp_expr(expr=operand)})"
        case BinaryExprIR(op=op, lhs=lhs, rhs=rhs):
            return f"({_render_cpp_expr(expr=lhs)} {op} {_render_cpp_expr(expr=rhs)})"
        case _:
            raise ValidationError(f"unsupported C++ expression node {type(expr).__name__}")
