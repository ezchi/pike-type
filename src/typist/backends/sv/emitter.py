"""SystemVerilog backend."""

from __future__ import annotations

from math import ceil
from pathlib import Path

from typist.backends.common.headers import render_header
from typist.ir.nodes import (
    BinaryExprIR,
    ConstRefExprIR,
    IntLiteralExprIR,
    ModuleIR,
    RepoIR,
    ScalarAliasIR,
    ScalarTypeSpecIR,
    StructIR,
    TypeRefIR,
    UnaryExprIR,
)
from typist.paths import sv_module_output_path, sv_test_module_output_path


def emit_sv(repo: RepoIR) -> list[Path]:
    """Emit SystemVerilog package files for all modules."""
    written_paths: list[Path] = []
    repo_root = Path(repo.repo_root)
    for module in repo.modules:
        synth_output_path = sv_module_output_path(
            repo_root=repo_root,
            module_path=repo_root / module.ref.repo_relative_path,
        )
        synth_output_path.parent.mkdir(parents=True, exist_ok=True)
        synth_output_path.write_text(render_module_sv(module), encoding="utf-8")
        written_paths.append(synth_output_path)
        if any(isinstance(type_ir, ScalarAliasIR) for type_ir in module.types):
            test_output_path = sv_test_module_output_path(
                repo_root=repo_root,
                module_path=repo_root / module.ref.repo_relative_path,
            )
            test_output_path.parent.mkdir(parents=True, exist_ok=True)
            test_output_path.write_text(render_module_test_sv(module), encoding="utf-8")
            written_paths.append(test_output_path)
    return written_paths


def render_module_sv(module: ModuleIR) -> str:
    """Render a synthesizable SystemVerilog package."""
    header = render_header(source_paths=(module.ref.repo_relative_path,))
    body_lines = [f"package {module.ref.basename}_pkg;"]
    const_lines: list[str] = []
    type_blocks: list[list[str]] = []
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
        const_lines.append(f"  localparam {sv_type} {const.name} = {sv_expr};")
    for type_ir in module.types:
        if isinstance(type_ir, ScalarAliasIR):
            type_blocks.append([f"  {_render_sv_scalar_alias(type_ir=type_ir)}"])
        elif isinstance(type_ir, StructIR):
            type_blocks.append([f"  {line}" for line in _render_sv_struct(type_ir=type_ir)])
    if const_lines or type_blocks:
        body_lines.append("")
    if const_lines:
        body_lines.extend(const_lines)
    if const_lines and type_blocks:
        body_lines.append("")
    for index, type_block in enumerate(type_blocks):
        if index > 0:
            body_lines.append("")
        body_lines.extend(type_block)
    body_lines.append("endpackage")
    return f"{header}\n" + "\n".join(body_lines) + "\n"


def render_module_test_sv(module: ModuleIR) -> str:
    """Render a verification-only SystemVerilog package."""
    header = render_header(source_paths=(module.ref.repo_relative_path,))
    body_lines = [
        f"package {module.ref.basename}_test_pkg;",
        f"  import {module.ref.basename}_pkg::*;",
    ]
    for type_ir in module.types:
        if not isinstance(type_ir, ScalarAliasIR):
            continue
        body_lines.append("")
        body_lines.extend(f"  {line}" for line in _render_sv_scalar_helper_class(type_ir=type_ir))
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
    if type_ir.resolved_width == 1:
        return f"typedef {base_type}{signed_kw} {type_ir.name};"
    return f"typedef {base_type}{signed_kw} {_render_sv_packed_range(expr=type_ir.width_expr, resolved_width=type_ir.resolved_width)} {type_ir.name};"


def _render_sv_struct(*, type_ir: StructIR) -> list[str]:
    """Render one packed struct typedef."""
    lines = ["typedef struct packed {"]
    for field in type_ir.fields:
        lines.append(f"  {_render_sv_struct_field(field_type=field.type_ir)} {field.name};")
    lines.append(f"}} {type_ir.name};")
    return lines


def _render_sv_struct_field(*, field_type: ScalarTypeSpecIR | TypeRefIR) -> str:
    """Render one packed struct field type."""
    if isinstance(field_type, TypeRefIR):
        return field_type.name
    base_type = field_type.state_kind
    signed_kw = " signed" if field_type.signed else ""
    if field_type.resolved_width == 1:
        return f"{base_type}{signed_kw}"
    return f"{base_type}{signed_kw} {_render_sv_packed_range(expr=field_type.width_expr, resolved_width=field_type.resolved_width)}"


def _render_sv_packed_range(*, expr: IntLiteralExprIR | ConstRefExprIR | UnaryExprIR | BinaryExprIR, resolved_width: int) -> str:
    """Render a packed range, simplifying literal widths."""
    if isinstance(expr, IntLiteralExprIR):
        return f"[{resolved_width - 1}:0]"
    return f"[{_render_sv_expr(expr=expr)}-1:0]"


def _render_sv_scalar_helper_class(*, type_ir: ScalarAliasIR) -> list[str]:
    """Render a lightweight verification helper class for a scalar alias."""
    class_name = _scalar_class_name(type_ir.name)
    width_expr = _render_sv_expr(expr=type_ir.width_expr)
    byte_count = ceil(type_ir.resolved_width / 8)
    return [
        f"class {class_name};",
        f"  localparam int WIDTH = {width_expr};",
        f"  localparam int BYTE_COUNT = {byte_count};",
        f"  rand {type_ir.name} value;",
        "",
        f"  function new({type_ir.name} value_in = '0);",
        "    value = value_in;",
        "  endfunction",
        "",
        f"  function automatic {type_ir.name} to_slv();",
        "    return value;",
        "  endfunction",
        "",
        f"  function void from_slv({type_ir.name} value_in);",
        "    value = value_in;",
        "  endfunction",
        "",
        "  task automatic to_bytes(output byte unsigned bytes[]);",
        "    bit [BYTE_COUNT*8-1:0] packed_bits;",
        "    bytes = new[BYTE_COUNT];",
        "    packed_bits = '0;",
        "    packed_bits[WIDTH-1:0] = value;",
        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
        "      bytes[idx] = packed_bits[idx*8 +: 8];",
        "    end",
        "  endtask",
        "",
        "  function void from_bytes(input byte unsigned bytes[]);",
        "    bit [BYTE_COUNT*8-1:0] packed_bits;",
        "    if (bytes.size() != BYTE_COUNT) begin",
        f'      $fatal(1, "{class_name}.from_bytes size mismatch: expected %0d got %0d", BYTE_COUNT, bytes.size());',
        "    end",
        "    packed_bits = '0;",
        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
        "      packed_bits[idx*8 +: 8] = bytes[idx];",
        "    end",
        f"    value = {type_ir.name}'(packed_bits[WIDTH-1:0]);",
        "  endfunction",
        "",
        f"  function void copy(input {class_name} rhs);",
        "    value = rhs.value;",
        "  endfunction",
        "",
        f"  function automatic {class_name} clone();",
        f"    {class_name} cloned = new();",
        "    cloned.value = value;",
        "    return cloned;",
        "  endfunction",
        "",
        f"  function automatic bit compare(input {class_name} rhs);",
        "    return value === rhs.value;",
        "  endfunction",
        "",
        "  function automatic string sprint();",
        f'    return $sformatf("{class_name}(value=0x%0h)", value);',
        "  endfunction",
        f"endclass : {class_name}",
    ]


def _scalar_class_name(type_name: str) -> str:
    """Convert a scalar alias name to its SV helper class name."""
    if type_name.endswith("_t"):
        return f"{type_name[:-2]}_ct"
    return f"{type_name}_ct"
