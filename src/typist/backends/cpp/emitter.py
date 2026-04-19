"""C++ backend."""

from __future__ import annotations

from math import ceil
from pathlib import Path

from typist.backends.common.headers import render_header
from typist.errors import ValidationError
from typist.ir.nodes import BinaryExprIR, ConstRefExprIR, IntLiteralExprIR, ModuleIR, RepoIR, ScalarAliasIR, UnaryExprIR
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
    body_lines = [f"#ifndef {guard}", f"#define {guard}", "", "#include <cstdint>"]
    if module.types:
        body_lines.extend(["#include <stdexcept>", "#include <vector>"])
    body_lines.append("")
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
    if module.constants and module.types:
        body_lines.append("")
    for index, type_ir in enumerate(module.types):
        if index > 0:
            body_lines.append("")
        body_lines.extend(_render_cpp_scalar_alias(type_ir=type_ir))
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


def _render_cpp_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
    """Render a C++ scalar wrapper class."""
    class_name = _scalar_class_name(type_ir.name)
    byte_count = ceil(type_ir.resolved_width / 8)
    lines = [
        f"class {class_name} {{",
        " public:",
        f"  static constexpr std::size_t kWidth = {type_ir.resolved_width};",
        f"  static constexpr bool kSigned = {'true' if type_ir.signed else 'false'};",
        f"  static constexpr std::size_t kByteCount = {byte_count};",
    ]
    if type_ir.resolved_width <= 64:
        value_type = _cpp_scalar_value_type(type_ir=type_ir)
        mask_literal = _cpp_unsigned_literal((1 << type_ir.resolved_width) - 1 if type_ir.resolved_width < 64 else 2**64 - 1)
        lines.extend(
            [
                f"  using value_type = {value_type};",
                "  value_type value;",
            ]
        )
        if type_ir.signed:
            minimum = -(2 ** (type_ir.resolved_width - 1))
            maximum = 2 ** (type_ir.resolved_width - 1) - 1
            lines.extend(
                [
                    f"  static constexpr value_type kMinValue = static_cast<value_type>({minimum});",
                    f"  static constexpr value_type kMaxValue = static_cast<value_type>({maximum});",
                    f"  static constexpr std::uint64_t kMask = {mask_literal};",
                    f"  {class_name}() : value(0) {{}}",
                    f"  explicit {class_name}(value_type value_in) : value(validate_value(value_in)) {{}}",
                    "",
                    "  std::vector<std::uint8_t> to_bytes() const {",
                    "    std::vector<std::uint8_t> bytes(kByteCount, 0);",
                    "    std::uint64_t bits = static_cast<std::uint64_t>(value) & kMask;",
                    "    for (std::size_t idx = 0; idx < kByteCount; ++idx) {",
                    "      bytes[idx] = static_cast<std::uint8_t>((bits >> (8U * idx)) & 0xFFU);",
                    "    }",
                    "    return bytes;",
                    "  }",
                    "",
                    "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
                    "    if (bytes.size() != kByteCount) {",
                    '      throw std::invalid_argument("byte width mismatch");',
                    "    }",
                    "    std::uint64_t bits = 0;",
                    "    for (std::size_t idx = 0; idx < kByteCount; ++idx) {",
                    "      bits |= static_cast<std::uint64_t>(bytes[idx]) << (8U * idx);",
                    "    }",
                    "    bits &= kMask;",
                    "    std::int64_t signed_value = static_cast<std::int64_t>(bits);",
                    f"    if ((bits & {_cpp_unsigned_literal(1 << (type_ir.resolved_width - 1))}) != 0U && kWidth < 64) {{",
                    f"      signed_value -= static_cast<std::int64_t>({_cpp_unsigned_literal(1 << type_ir.resolved_width)});",
                    "    }",
                    "    value = validate_value(static_cast<value_type>(signed_value));",
                    "  }",
                    "",
                    f"  {class_name} clone() const {{",
                    f"    return {class_name}(value);",
                    "  }",
                    "",
                    "  operator value_type() const {",
                    "    return value;",
                    "  }",
                    "",
                    "  bool operator==(const "
                    f"{class_name}& other) const = default;",
                    "",
                    " private:",
                    "  static value_type validate_value(value_type value_in) {",
                    "    if (value_in < kMinValue || value_in > kMaxValue) {",
                    '      throw std::out_of_range("value out of range");',
                    "    }",
                    "    return value_in;",
                    "  }",
                    "};",
                ]
            )
        else:
            maximum = 2 ** type_ir.resolved_width - 1 if type_ir.resolved_width < 64 else 2**64 - 1
            lines.extend(
                [
                    f"  static constexpr value_type kMaxValue = static_cast<value_type>({_cpp_unsigned_literal(maximum)});",
                    f"  {class_name}() : value(0) {{}}",
                    f"  explicit {class_name}(value_type value_in) : value(validate_value(value_in)) {{}}",
                    "",
                    "  std::vector<std::uint8_t> to_bytes() const {",
                    "    std::vector<std::uint8_t> bytes(kByteCount, 0);",
                    "    std::uint64_t bits = static_cast<std::uint64_t>(value);",
                    "    for (std::size_t idx = 0; idx < kByteCount; ++idx) {",
                    "      bytes[idx] = static_cast<std::uint8_t>((bits >> (8U * idx)) & 0xFFU);",
                    "    }",
                    "    return bytes;",
                    "  }",
                    "",
                    "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
                    "    if (bytes.size() != kByteCount) {",
                    '      throw std::invalid_argument("byte width mismatch");',
                    "    }",
                    "    std::uint64_t bits = 0;",
                    "    for (std::size_t idx = 0; idx < kByteCount; ++idx) {",
                    "      bits |= static_cast<std::uint64_t>(bytes[idx]) << (8U * idx);",
                    "    }",
                    "    value = validate_value(static_cast<value_type>(bits));",
                    "  }",
                    "",
                    f"  {class_name} clone() const {{",
                    f"    return {class_name}(value);",
                    "  }",
                    "",
                    "  operator value_type() const {",
                    "    return value;",
                    "  }",
                    "",
                    "  bool operator==(const "
                    f"{class_name}& other) const = default;",
                    "",
                    " private:",
                    "  static value_type validate_value(value_type value_in) {",
                    "    if (value_in > kMaxValue) {",
                    '      throw std::out_of_range("value out of range");',
                    "    }",
                    "    return value_in;",
                    "  }",
                    "};",
                ]
            )
    else:
        lines.extend(
            [
                "  using value_type = std::vector<std::uint8_t>;",
                "  value_type value;",
                f"  {class_name}() : value(kByteCount, 0U) {{}}",
                f"  explicit {class_name}(const value_type& value_in) : value(validate_value(value_in)) {{}}",
                "",
                "  std::vector<std::uint8_t> to_bytes() const {",
                "    return value;",
                "  }",
                "",
                "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
                "    value = validate_value(bytes);",
                "  }",
                "",
                f"  {class_name} clone() const {{",
                f"    return {class_name}(value);",
                "  }",
                "",
                "  bool operator==(const "
                f"{class_name}& other) const = default;",
                "",
                " private:",
                "  static value_type validate_value(const value_type& value_in) {",
                "    if (value_in.size() != kByteCount) {",
                '      throw std::invalid_argument("byte width mismatch");',
                "    }",
                "    return value_in;",
                "  }",
                "};",
            ]
        )
    return lines


def _cpp_scalar_value_type(*, type_ir: ScalarAliasIR) -> str:
    """Choose the public C++ storage type for a scalar alias."""
    if type_ir.resolved_width <= 8:
        return "std::int8_t" if type_ir.signed else "std::uint8_t"
    if type_ir.resolved_width <= 16:
        return "std::int16_t" if type_ir.signed else "std::uint16_t"
    if type_ir.resolved_width <= 32:
        return "std::int32_t" if type_ir.signed else "std::uint32_t"
    return "std::int64_t" if type_ir.signed else "std::uint64_t"


def _cpp_unsigned_literal(value: int) -> str:
    """Render an unsigned integer literal for C++."""
    if value <= 0xFFFFFFFF:
        return f"{value}U"
    return f"{value}ULL"


def _scalar_class_name(type_name: str) -> str:
    """Convert a scalar alias name to its software wrapper class name."""
    if type_name.endswith("_t"):
        return f"{type_name[:-2]}_ct"
    return f"{type_name}_ct"
