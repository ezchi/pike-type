"""SystemVerilog backend."""

from __future__ import annotations

from pathlib import Path

from piketype.backends.common.headers import render_header
from piketype.ir.nodes import (
    BinaryExprIR,
    ConstRefExprIR,
    ExprIR,
    FieldTypeIR,
    FlagFieldIR,
    FlagsIR,
    IntLiteralExprIR,
    ModuleIR,
    RepoIR,
    ScalarAliasIR,
    ScalarTypeSpecIR,
    StructFieldIR,
    StructIR,
    TypeDefIR,
    TypeRefIR,
    UnaryExprIR,
    byte_count,
)
from piketype.paths import sv_module_output_path, sv_test_module_output_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


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
        if module.types:
            test_output_path = sv_test_module_output_path(
                repo_root=repo_root,
                module_path=repo_root / module.ref.repo_relative_path,
            )
            test_output_path.parent.mkdir(parents=True, exist_ok=True)
            test_output_path.write_text(render_module_test_sv(module), encoding="utf-8")
            written_paths.append(test_output_path)
    return written_paths


# ---------------------------------------------------------------------------
# Synthesizable package
# ---------------------------------------------------------------------------


def render_module_sv(module: ModuleIR) -> str:
    """Render a synthesizable SystemVerilog package."""
    header = render_header(source_paths=(module.ref.repo_relative_path,))
    type_index: dict[str, TypeDefIR] = {t.name: t for t in module.types}
    body_lines = [f"package {module.ref.basename}_pkg;"]

    const_lines: list[str] = []
    for const in module.constants:
        sv_type, sv_literal = _render_sv_const(
            value=const.resolved_value,
            signed=const.resolved_signed,
            width=const.resolved_width,
        )
        sv_expr = sv_literal if isinstance(const.expr, IntLiteralExprIR) else _render_sv_expr(expr=const.expr)
        const_lines.append(f"  localparam {sv_type} {const.name} = {sv_expr};")

    type_blocks: list[list[str]] = []
    for type_ir in module.types:
        type_blocks.append(_render_sv_type_block(type_ir=type_ir, type_index=type_index))

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


def _render_sv_type_block(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
    """Render localparams, typedef, and pack/unpack for one type."""
    base = _type_base_name(type_ir.name)
    upper_base = base.upper()

    lines = [
        f"  localparam int LP_{upper_base}_WIDTH = {_render_sv_width_value(type_ir=type_ir, type_index=type_index)};",
        f"  localparam int LP_{upper_base}_BYTE_COUNT = {_type_byte_count(type_ir=type_ir, type_index=type_index)};",
        "",
    ]

    if isinstance(type_ir, ScalarAliasIR):
        lines.append(f"  {_render_sv_scalar_alias(type_ir=type_ir)}")
    elif isinstance(type_ir, StructIR):
        lines.extend(f"  {line}" for line in _render_sv_struct(type_ir=type_ir))
    elif isinstance(type_ir, FlagsIR):
        lines.extend(f"  {line}" for line in _render_sv_flags(type_ir=type_ir))

    lines.append("")
    lines.extend(f"  {line}" for line in _render_sv_pack_fn(type_ir=type_ir, type_index=type_index))
    lines.append("")
    lines.extend(f"  {line}" for line in _render_sv_unpack_fn(type_ir=type_ir, type_index=type_index))

    return lines


def _render_sv_width_value(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> str:
    """Render the width value for a localparam."""
    if isinstance(type_ir, ScalarAliasIR):
        return _render_sv_expr(expr=type_ir.width_expr)
    return str(_data_width(type_ir=type_ir, type_index=type_index))


def _render_sv_scalar_alias(*, type_ir: ScalarAliasIR) -> str:
    """Render a named scalar typedef using the LP_WIDTH localparam."""
    base = _type_base_name(type_ir.name)
    upper_base = base.upper()
    base_type = type_ir.state_kind
    signed_kw = " signed" if type_ir.signed else ""
    if type_ir.resolved_width == 1:
        return f"typedef {base_type}{signed_kw} {type_ir.name};"
    return f"typedef {base_type}{signed_kw} [LP_{upper_base}_WIDTH-1:0] {type_ir.name};"


def _render_sv_struct(*, type_ir: StructIR) -> list[str]:
    """Render one packed struct typedef with per-member padding."""
    lines = ["typedef struct packed {"]
    for field in type_ir.fields:
        pad = field.padding_bits
        if pad > 0:
            if pad == 1:
                lines.append(f"  logic {field.name}_pad;")
            else:
                lines.append(f"  logic [{pad - 1}:0] {field.name}_pad;")
        lines.append(f"  {_render_sv_struct_field_type(field_type=field.type_ir)} {field.name};")
    if type_ir.alignment_bits > 0:
        if type_ir.alignment_bits == 1:
            lines.append("  logic _align_pad;")
        else:
            lines.append(f"  logic [{type_ir.alignment_bits - 1}:0] _align_pad;")
    lines.append(f"}} {type_ir.name};")
    return lines


def _render_sv_struct_field_type(*, field_type: FieldTypeIR) -> str:
    """Render one packed struct field type (without padding)."""
    if isinstance(field_type, TypeRefIR):
        return field_type.name
    base_type = field_type.state_kind
    signed_kw = " signed" if field_type.signed else ""
    if field_type.resolved_width == 1:
        return f"{base_type}{signed_kw}"
    return f"{base_type}{signed_kw} [{field_type.resolved_width - 1}:0]"


def _render_sv_flags(*, type_ir: FlagsIR) -> list[str]:
    """Render one packed flags typedef."""
    lines = ["typedef struct packed {"]
    for flag in type_ir.fields:
        lines.append(f"  logic {flag.name};")
    if type_ir.alignment_bits > 0:
        if type_ir.alignment_bits == 1:
            lines.append("  logic _align_pad;")
        else:
            lines.append(f"  logic [{type_ir.alignment_bits - 1}:0] _align_pad;")
    lines.append(f"}} {type_ir.name};")
    return lines


def _render_sv_pack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
    """Render a pack_<base> function."""
    base = _type_base_name(type_ir.name)
    upper_base = base.upper()

    if isinstance(type_ir, ScalarAliasIR):
        return [
            f"function automatic logic [LP_{upper_base}_WIDTH-1:0] pack_{base}({type_ir.name} a);",
            "  return a;",
            "endfunction",
        ]

    if isinstance(type_ir, FlagsIR):
        parts = [f"a.{flag.name}" for flag in type_ir.fields]
        concat = ", ".join(parts)
        return [
            f"function automatic logic [LP_{upper_base}_WIDTH-1:0] pack_{base}({type_ir.name} a);",
            f"  return {{{concat}}};",
            "endfunction",
        ]

    parts: list[str] = []
    for field in type_ir.fields:
        if isinstance(field.type_ir, TypeRefIR):
            target = type_index[field.type_ir.name]
            inner_base = _type_base_name(target.name)
            parts.append(f"pack_{inner_base}(a.{field.name})")
        else:
            parts.append(f"a.{field.name}")
    concat = ", ".join(parts)
    return [
        f"function automatic logic [LP_{upper_base}_WIDTH-1:0] pack_{base}({type_ir.name} a);",
        f"  return {{{concat}}};",
        "endfunction",
    ]


def _render_sv_unpack_fn(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> list[str]:
    """Render an unpack_<base> function."""
    base = _type_base_name(type_ir.name)
    upper_base = base.upper()

    if isinstance(type_ir, ScalarAliasIR):
        return [
            f"function automatic {type_ir.name} unpack_{base}(logic [LP_{upper_base}_WIDTH-1:0] a);",
            "  return a;",
            "endfunction",
        ]

    if isinstance(type_ir, FlagsIR):
        lines = [
            f"function automatic {type_ir.name} unpack_{base}(logic [LP_{upper_base}_WIDTH-1:0] a);",
            f"  {type_ir.name} result;",
            "  result = '0;",
        ]
        for bit_idx, flag in enumerate(reversed(type_ir.fields)):
            lines.append(f"  result.{flag.name} = a[{bit_idx}];")
        lines.append("  return result;")
        lines.append("endfunction")
        return lines

    lines = [
        f"function automatic {type_ir.name} unpack_{base}(logic [LP_{upper_base}_WIDTH-1:0] a);",
        f"  {type_ir.name} result;",
        "  int unsigned offset;",
        "  result = '0;",
        "  offset = 0;",
    ]

    for field in reversed(type_ir.fields):
        fw = _field_data_width(field=field, type_index=type_index)
        if isinstance(field.type_ir, TypeRefIR):
            target = type_index[field.type_ir.name]
            inner_base = _type_base_name(target.name)
            inner_upper = inner_base.upper()
            lines.append(f"  result.{field.name} = unpack_{inner_base}(a[offset +: LP_{inner_upper}_WIDTH]);")
            lines.append(f"  offset += LP_{inner_upper}_WIDTH;")
        else:
            lines.append(f"  result.{field.name} = a[offset +: {fw}];")
            lines.append(f"  offset += {fw};")

        if field.padding_bits > 0 and _is_field_signed(field=field, type_index=type_index):
            w = _field_data_width(field=field, type_index=type_index)
            p = field.padding_bits
            lines.append(f"  result.{field.name}_pad = {{{p}{{result.{field.name}[{w - 1}]}}}};")

    lines.append("  return result;")
    lines.append("endfunction")
    return lines


# ---------------------------------------------------------------------------
# Verification (test) package
# ---------------------------------------------------------------------------


def render_module_test_sv(module: ModuleIR) -> str:
    """Render a verification-only SystemVerilog package."""
    header = render_header(source_paths=(module.ref.repo_relative_path,))
    type_index: dict[str, TypeDefIR] = {t.name: t for t in module.types}
    body_lines = [
        f"package {module.ref.basename}_test_pkg;",
        f"  import {module.ref.basename}_pkg::*;",
    ]
    for type_ir in module.types:
        body_lines.append("")
        if isinstance(type_ir, ScalarAliasIR):
            body_lines.extend(f"  {line}" for line in _render_sv_scalar_helper_class(type_ir=type_ir))
        elif isinstance(type_ir, StructIR):
            body_lines.extend(f"  {line}" for line in _render_sv_struct_helper_class(type_ir=type_ir, type_index=type_index))
        elif isinstance(type_ir, FlagsIR):
            body_lines.extend(f"  {line}" for line in _render_sv_flags_helper_class(type_ir=type_ir))
    body_lines.append("endpackage")
    return f"{header}\n" + "\n".join(body_lines) + "\n"


def _render_sv_scalar_helper_class(*, type_ir: ScalarAliasIR) -> list[str]:
    """Render a verification helper class for a scalar alias."""
    class_name = _helper_class_name(type_ir.name)
    base = _type_base_name(type_ir.name)
    upper_base = base.upper()
    bc = byte_count(type_ir.resolved_width)
    pad_bits = (-type_ir.resolved_width) % 8

    lines = [
        f"class {class_name};",
        f"  localparam int WIDTH = LP_{upper_base}_WIDTH;",
        f"  localparam int BYTE_COUNT = LP_{upper_base}_BYTE_COUNT;",
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
    ]

    # to_bytes: big-endian, per-field serialization
    lines.extend([
        "  task automatic to_bytes(output byte unsigned bytes[]);",
        f"    logic [{bc * 8 - 1}:0] padded;",
        "    bytes = new[BYTE_COUNT];",
        "    padded = '0;",
        f"    padded[WIDTH-1:0] = value;",
    ])
    if pad_bits > 0 and type_ir.signed:
        lines.append(f"    for (int i = WIDTH; i < BYTE_COUNT*8; i++) padded[i] = value[WIDTH-1];")
    lines.extend([
        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
        "      bytes[idx] = padded[(BYTE_COUNT - 1 - idx)*8 +: 8];",
        "    end",
        "  endtask",
        "",
    ])

    # from_bytes: big-endian, mask/validate padding
    lines.extend([
        "  function void from_bytes(input byte unsigned bytes[]);",
        f"    logic [{bc * 8 - 1}:0] padded;",
        "    if (bytes.size() != BYTE_COUNT) begin",
        f'      $fatal(1, "{class_name}.from_bytes size mismatch: expected %0d got %0d", BYTE_COUNT, bytes.size());',
        "    end",
        "    padded = '0;",
        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
        "      padded[(BYTE_COUNT - 1 - idx)*8 +: 8] = bytes[idx];",
        "    end",
    ])
    if pad_bits > 0 and type_ir.signed:
        lines.extend([
            f"    for (int i = WIDTH; i < BYTE_COUNT*8; i++) begin",
            "      if (padded[i] !== padded[WIDTH-1]) begin",
            f'        $fatal(1, "{class_name}.from_bytes signed padding mismatch");',
            "      end",
            "    end",
        ])
    lines.extend([
        f"    value = {type_ir.name}'(padded[WIDTH-1:0]);",
        "  endfunction",
        "",
    ])

    lines.extend([
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
    ])
    return lines


def _render_sv_struct_helper_class(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
    """Render a field-oriented verification helper class for a struct."""
    class_name = _helper_class_name(type_ir.name)
    base = _type_base_name(type_ir.name)
    upper_base = base.upper()

    lines = [
        f"class {class_name};",
        f"  localparam int WIDTH = LP_{upper_base}_WIDTH;",
        f"  localparam int BYTE_COUNT = LP_{upper_base}_BYTE_COUNT;",
    ]
    for field in type_ir.fields:
        lines.append(f"  {_render_sv_helper_field_decl(field=field, type_index=type_index)}")

    # Constructor
    lines.extend(["", "  function new();"])
    for field in type_ir.fields:
        if _is_sv_struct_ref(field_type=field.type_ir, type_index=type_index):
            lines.append(f"    {field.name} = new();")
        else:
            lines.append(f"    {field.name} = '0;")
    lines.append("  endfunction")

    # to_slv: assemble padded typedef with proper padding fill
    lines.extend(["", f"  function automatic {type_ir.name} to_slv();", f"    {type_ir.name} packed_value;"])
    for field in type_ir.fields:
        if _is_sv_struct_ref(field_type=field.type_ir, type_index=type_index):
            lines.append(f"    packed_value.{field.name} = {field.name}.to_slv();")
        else:
            lines.append(f"    packed_value.{field.name} = {field.name};")
        if field.padding_bits > 0:
            if _is_field_signed(field=field, type_index=type_index):
                w = _field_data_width(field=field, type_index=type_index)
                p = field.padding_bits
                lines.append(f"    packed_value.{field.name}_pad = {{{p}{{packed_value.{field.name}[{w - 1}]}}}};")
            else:
                lines.append(f"    packed_value.{field.name}_pad = '0;")
    if type_ir.alignment_bits > 0:
        lines.append("    packed_value._align_pad = '0;")
    lines.extend(["    return packed_value;", "  endfunction"])

    # from_slv: extract field values, ignore padding
    lines.extend(["", f"  function void from_slv({type_ir.name} value_in);"])
    for field in type_ir.fields:
        if _is_sv_struct_ref(field_type=field.type_ir, type_index=type_index):
            lines.append(f"    {field.name}.from_slv(value_in.{field.name});")
        else:
            lines.append(f"    {field.name} = value_in.{field.name};")
    lines.append("  endfunction")

    # to_bytes: per-field big-endian serialization
    lines.extend([
        "",
        "  task automatic to_bytes(output byte unsigned bytes[]);",
        "    int byte_idx;",
        "    bytes = new[BYTE_COUNT];",
        "    byte_idx = 0;",
    ])
    for field in type_ir.fields:
        lines.extend(_render_sv_helper_to_bytes_step(field=field, type_index=type_index))
    if type_ir.alignment_bits > 0:
        align_bytes = type_ir.alignment_bits // 8
        lines.append("    begin")
        lines.append(f"      for (int i = 0; i < {align_bytes}; i++) bytes[byte_idx + i] = 8'h00;")
        lines.append(f"      byte_idx += {align_bytes};")
        lines.append("    end")
    lines.append("  endtask")

    # from_bytes: per-field deserialization with signed validation
    lines.extend([
        "",
        "  function void from_bytes(input byte unsigned bytes[]);",
        "    int byte_idx;",
        "    if (bytes.size() != BYTE_COUNT) begin",
        f'      $fatal(1, "{class_name}.from_bytes size mismatch: expected %0d got %0d", BYTE_COUNT, bytes.size());',
        "    end",
        "    byte_idx = 0;",
    ])
    for field in type_ir.fields:
        lines.extend(_render_sv_helper_from_bytes_step(field=field, type_index=type_index, class_name=class_name))
    if type_ir.alignment_bits > 0:
        align_bytes = type_ir.alignment_bits // 8
        lines.append(f"    byte_idx += {align_bytes};")
    lines.append("  endfunction")

    # copy
    lines.extend(["", f"  function void copy(input {class_name} rhs);"])
    for field in type_ir.fields:
        if _is_sv_struct_ref(field_type=field.type_ir, type_index=type_index):
            lines.append(f"    {field.name}.copy(rhs.{field.name});")
        else:
            lines.append(f"    {field.name} = rhs.{field.name};")
    lines.append("  endfunction")

    # clone
    lines.extend([
        "",
        f"  function automatic {class_name} clone();",
        f"    {class_name} cloned = new();",
        "    cloned.copy(this);",
        "    return cloned;",
        "  endfunction",
    ])

    # compare
    lines.extend(["", f"  function automatic bit compare(input {class_name} rhs);", "    bit match;", "    match = 1'b1;"])
    for field in type_ir.fields:
        if _is_sv_struct_ref(field_type=field.type_ir, type_index=type_index):
            lines.append(f"    match &= {field.name}.compare(rhs.{field.name});")
        else:
            lines.append(f"    match &= ({field.name} === rhs.{field.name});")
    lines.extend(["    return match;", "  endfunction"])

    # sprint
    fmt_parts: list[str] = []
    arg_parts: list[str] = []
    for field in type_ir.fields:
        if _is_sv_struct_ref(field_type=field.type_ir, type_index=type_index):
            fmt_parts.append(f"{field.name}=%s")
            arg_parts.append(f"{field.name}.sprint()")
        else:
            fmt_parts.append(f"{field.name}=0x%0h")
            arg_parts.append(field.name)
    fmt = ", ".join(fmt_parts)
    args = ", ".join(arg_parts)
    lines.extend([
        "",
        "  function automatic string sprint();",
        f'    return $sformatf("{class_name}({fmt})", {args});',
        "  endfunction",
        f"endclass : {class_name}",
    ])
    return lines


def _render_sv_flags_helper_class(*, type_ir: FlagsIR) -> list[str]:
    """Render a verification helper class for a flags type."""
    class_name = _helper_class_name(type_ir.name)
    base = _type_base_name(type_ir.name)
    upper_base = base.upper()
    num_flags = len(type_ir.fields)
    bc = byte_count(num_flags)
    total_bits = bc * 8

    lines = [
        f"class {class_name};",
        f"  localparam int WIDTH = {num_flags};",
        f"  localparam int BYTE_COUNT = {bc};",
    ]
    for flag in type_ir.fields:
        lines.append(f"  rand logic {flag.name};")

    # Constructor
    lines.extend(["", "  function new();"])
    for flag in type_ir.fields:
        lines.append(f"    {flag.name} = '0;")
    lines.append("  endfunction")

    # to_slv
    lines.extend(["", f"  function automatic {type_ir.name} to_slv();", f"    {type_ir.name} packed_value;"])
    for flag in type_ir.fields:
        lines.append(f"    packed_value.{flag.name} = {flag.name};")
    if type_ir.alignment_bits > 0:
        lines.append("    packed_value._align_pad = '0;")
    lines.extend(["    return packed_value;", "  endfunction"])

    # from_slv
    lines.extend(["", f"  function void from_slv({type_ir.name} value_in);"])
    for flag in type_ir.fields:
        lines.append(f"    {flag.name} = value_in.{flag.name};")
    lines.append("  endfunction")

    # to_bytes
    lines.extend([
        "",
        "  task automatic to_bytes(output byte unsigned bytes[]);",
        f"    logic [{total_bits - 1}:0] bv;",
        "    bytes = new[BYTE_COUNT];",
        "    bv = '0;",
    ])
    # Pack flag bits into a bit vector (MSB = first flag)
    for idx, flag in enumerate(type_ir.fields):
        bit_pos = num_flags - 1 - idx
        lines.append(f"    bv[{bit_pos}] = {flag.name};")
    lines.extend([
        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
        "      bytes[idx] = bv[(BYTE_COUNT - 1 - idx)*8 +: 8];",
        "    end",
        "  endtask",
    ])

    # from_bytes
    lines.extend([
        "",
        "  function void from_bytes(input byte unsigned bytes[]);",
        f"    logic [{total_bits - 1}:0] bv;",
        "    if (bytes.size() != BYTE_COUNT) begin",
        f'      $fatal(1, "{class_name}.from_bytes size mismatch: expected %0d got %0d", BYTE_COUNT, bytes.size());',
        "    end",
        "    bv = '0;",
        "    for (int idx = 0; idx < BYTE_COUNT; idx++) begin",
        "      bv[(BYTE_COUNT - 1 - idx)*8 +: 8] = bytes[idx];",
        "    end",
    ])
    for idx, flag in enumerate(type_ir.fields):
        bit_pos = num_flags - 1 - idx
        lines.append(f"    {flag.name} = bv[{bit_pos}];")
    lines.append("  endfunction")

    # copy
    lines.extend(["", f"  function void copy(input {class_name} rhs);"])
    for flag in type_ir.fields:
        lines.append(f"    {flag.name} = rhs.{flag.name};")
    lines.append("  endfunction")

    # clone
    lines.extend([
        "",
        f"  function automatic {class_name} clone();",
        f"    {class_name} cloned = new();",
        "    cloned.copy(this);",
        "    return cloned;",
        "  endfunction",
    ])

    # compare
    lines.extend(["", f"  function automatic bit compare(input {class_name} rhs);", "    bit match;", "    match = 1'b1;"])
    for flag in type_ir.fields:
        lines.append(f"    match &= ({flag.name} === rhs.{flag.name});")
    lines.extend(["    return match;", "  endfunction"])

    # sprint
    fmt_parts = [f"{flag.name}=%0b" for flag in type_ir.fields]
    arg_parts = [flag.name for flag in type_ir.fields]
    fmt = ", ".join(fmt_parts)
    args = ", ".join(arg_parts)
    lines.extend([
        "",
        "  function automatic string sprint();",
        f'    return $sformatf("{class_name}({fmt})", {args});',
        "  endfunction",
        f"endclass : {class_name}",
    ])
    return lines


def _render_sv_helper_field_decl(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
    """Render one struct helper field declaration."""
    if isinstance(field.type_ir, TypeRefIR):
        target = type_index[field.type_ir.name]
        if isinstance(target, StructIR):
            return f"{_helper_class_name(target.name)} {field.name};"
        rand_kw = "rand " if field.rand else ""
        return f"{rand_kw}{target.name} {field.name};"
    rand_kw = "rand " if field.rand else ""
    return f"{rand_kw}{_render_sv_struct_field_type(field_type=field.type_ir)} {field.name};"


def _render_sv_helper_to_bytes_step(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
    """Render one to_bytes serialization step for a struct field."""
    lines: list[str] = []
    if _is_sv_struct_ref(field_type=field.type_ir, type_index=type_index):
        fbc = _field_byte_count(field=field, type_index=type_index)
        lines.extend([
            "    begin",
            "      byte unsigned field_bytes[];",
            f"      {field.name}.to_bytes(field_bytes);",
            f"      for (int i = 0; i < {fbc}; i++) bytes[byte_idx + i] = field_bytes[i];",
            f"      byte_idx += {fbc};",
            "    end",
        ])
    else:
        fbc = _field_byte_count(field=field, type_index=type_index)
        w = _field_data_width(field=field, type_index=type_index)
        total_bits = fbc * 8
        signed = _is_field_signed(field=field, type_index=type_index)
        pad = field.padding_bits
        lines.append("    begin")
        lines.append(f"      logic [{total_bits - 1}:0] fb;")
        lines.append("      fb = '0;")
        lines.append(f"      fb[{w - 1}:0] = {field.name};")
        if pad > 0 and signed:
            lines.append(f"      for (int i = {w}; i < {total_bits}; i++) fb[i] = {field.name}[{w - 1}];")
        lines.append(f"      for (int i = 0; i < {fbc}; i++) bytes[byte_idx + i] = fb[({fbc} - 1 - i)*8 +: 8];")
        lines.append(f"      byte_idx += {fbc};")
        lines.append("    end")
    return lines


def _render_sv_helper_from_bytes_step(
    *,
    field: StructFieldIR,
    type_index: dict[str, TypeDefIR],
    class_name: str,
) -> list[str]:
    """Render one from_bytes deserialization step for a struct field."""
    lines: list[str] = []
    if _is_sv_struct_ref(field_type=field.type_ir, type_index=type_index):
        fbc = _field_byte_count(field=field, type_index=type_index)
        lines.extend([
            "    begin",
            f"      byte unsigned field_bytes[] = new[{fbc}];",
            f"      for (int i = 0; i < {fbc}; i++) field_bytes[i] = bytes[byte_idx + i];",
            f"      {field.name}.from_bytes(field_bytes);",
            f"      byte_idx += {fbc};",
            "    end",
        ])
    else:
        fbc = _field_byte_count(field=field, type_index=type_index)
        w = _field_data_width(field=field, type_index=type_index)
        total_bits = fbc * 8
        signed = _is_field_signed(field=field, type_index=type_index)
        pad = field.padding_bits
        lines.append("    begin")
        lines.append(f"      logic [{total_bits - 1}:0] fb;")
        lines.append("      fb = '0;")
        lines.append(f"      for (int i = 0; i < {fbc}; i++) fb[({fbc} - 1 - i)*8 +: 8] = bytes[byte_idx + i];")
        if pad > 0 and signed:
            lines.extend([
                f"      for (int i = {w}; i < {total_bits}; i++) begin",
                f"        if (fb[i] !== fb[{w - 1}]) begin",
                f'          $fatal(1, "{class_name}.from_bytes signed padding mismatch for field {field.name}");',
                "        end",
                "      end",
            ])
        lines.append(f"      {field.name} = fb[{w - 1}:0];")
        lines.append(f"      byte_idx += {fbc};")
        lines.append("    end")
    return lines


# ---------------------------------------------------------------------------
# Constant rendering (unchanged)
# ---------------------------------------------------------------------------


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


def _render_sv_expr(*, expr: ExprIR) -> str:
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


# ---------------------------------------------------------------------------
# Width / byte-count resolution helpers
# ---------------------------------------------------------------------------


def _type_base_name(name: str) -> str:
    """Strip trailing _t from a type name."""
    return name[:-2] if name.endswith("_t") else name


def _data_width(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
    """Total data width (excluding padding) of a type."""
    if isinstance(type_ir, ScalarAliasIR):
        return type_ir.resolved_width
    if isinstance(type_ir, FlagsIR):
        return len(type_ir.fields)
    return sum(_field_data_width(field=f, type_index=type_index) for f in type_ir.fields)


def _field_data_width(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> int:
    """Data width of one struct field."""
    if isinstance(field.type_ir, ScalarTypeSpecIR):
        return field.type_ir.resolved_width
    target = type_index[field.type_ir.name]
    return _data_width(type_ir=target, type_index=type_index)


def _type_byte_count(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
    """Total byte count (including padding and alignment) of a type."""
    if isinstance(type_ir, ScalarAliasIR):
        return byte_count(type_ir.resolved_width)
    if isinstance(type_ir, FlagsIR):
        return byte_count(len(type_ir.fields))
    field_bytes = sum(_field_byte_count(field=f, type_index=type_index) for f in type_ir.fields)
    return field_bytes + type_ir.alignment_bits // 8


def _field_byte_count(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> int:
    """Byte count of one struct field."""
    if isinstance(field.type_ir, ScalarTypeSpecIR):
        return byte_count(field.type_ir.resolved_width)
    target = type_index[field.type_ir.name]
    return _type_byte_count(type_ir=target, type_index=type_index)


def _is_field_signed(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> bool:
    """Whether a scalar-typed field is signed."""
    if isinstance(field.type_ir, ScalarTypeSpecIR):
        return field.type_ir.signed
    target = type_index.get(field.type_ir.name)
    if isinstance(target, ScalarAliasIR):
        return target.signed
    return False


def _is_sv_struct_ref(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> bool:
    """Return whether one SV field references a named struct."""
    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], StructIR)


def _helper_class_name(type_name: str) -> str:
    """Convert a type name to its SV helper class name."""
    if type_name.endswith("_t"):
        return f"{type_name[:-2]}_ct"
    return f"{type_name}_ct"
