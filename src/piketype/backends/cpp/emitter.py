"""C++ backend — big-endian, byte-aligned padding."""

from __future__ import annotations

from pathlib import Path

from piketype.backends.common.headers import render_header
from piketype.errors import ValidationError
from piketype.ir.nodes import (
    BinaryExprIR,
    ConstRefExprIR,
    EnumIR,
    ExprIR,
    FieldTypeIR,
    FlagFieldIR,
    FlagsIR,
    IntLiteralExprIR,
    ModuleIR,
    RepoIR,
    ScalarAliasIR,
    ScalarTypeSpecIR,
    StructIR,
    StructFieldIR,
    TypeDefIR,
    TypeRefIR,
    UnaryExprIR,
    byte_count,
)
from piketype.paths import cpp_header_output_path


def emit_cpp(repo: RepoIR, *, namespace: str | None = None) -> list[Path]:
    """Emit C++ outputs."""
    written_paths: list[Path] = []
    repo_root = Path(repo.repo_root)
    for module in repo.modules:
        output_path = cpp_header_output_path(
            repo_root=repo_root,
            module_path=repo_root / module.ref.repo_relative_path,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_module_hpp(module, namespace=namespace), encoding="utf-8")
        written_paths.append(output_path)
    return written_paths


def render_module_hpp(module: ModuleIR, *, namespace: str | None = None) -> str:
    """Render a C++ header."""
    header = render_header(source_paths=(module.ref.repo_relative_path,))
    if namespace is not None:
        guard = f"{namespace.replace('::', '_')}_{module.ref.basename}_types_hpp".upper()
        ns = f"{namespace}::{module.ref.basename}"
    else:
        guard = "_".join((*module.ref.namespace_parts, "types_hpp")).upper().replace(".", "_")
        ns = "::".join(part for part in module.ref.namespace_parts if part != "piketype")
    type_index = {type_ir.name: type_ir for type_ir in module.types}
    has_types = bool(module.types)
    body_lines = [f"#ifndef {guard}", f"#define {guard}", "", "#include <cstdint>"]
    if has_types:
        body_lines.extend(["#include <cstddef>", "#include <stdexcept>", "#include <vector>"])
    body_lines.append("")
    if ns:
        body_lines.append(f"namespace {ns} {{")
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
        if isinstance(type_ir, ScalarAliasIR):
            body_lines.extend(_render_cpp_scalar_alias(type_ir=type_ir))
        elif isinstance(type_ir, StructIR):
            body_lines.extend(_render_cpp_struct(type_ir=type_ir, type_index=type_index))
        elif isinstance(type_ir, FlagsIR):
            body_lines.extend(_render_cpp_flags(type_ir=type_ir))
        elif isinstance(type_ir, EnumIR):
            body_lines.extend(_render_cpp_enum(type_ir=type_ir))
    if ns:
        body_lines.append("")
        body_lines.append(f"}}  // namespace {ns}")
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


def _render_cpp_expr(*, expr: ExprIR) -> str:
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


# ---------------------------------------------------------------------------
# Scalar alias wrapper class
# ---------------------------------------------------------------------------


def _render_cpp_scalar_alias(*, type_ir: ScalarAliasIR) -> list[str]:
    """Render a C++ scalar wrapper class (big-endian serialization)."""
    class_name = _type_class_name(type_ir.name)
    bc = byte_count(type_ir.resolved_width)
    width = type_ir.resolved_width
    lines = [
        f"class {class_name} {{",
        " public:",
        f"  static constexpr std::size_t WIDTH = {width};",
        f"  static constexpr bool SIGNED = {'true' if type_ir.signed else 'false'};",
        f"  static constexpr std::size_t BYTE_COUNT = {bc};",
    ]
    if width <= 64:
        value_type = _cpp_scalar_value_type(width=width, signed=type_ir.signed)
        mask_literal = _cpp_unsigned_literal(
            (1 << width) - 1 if width < 64 else 2**64 - 1
        )
        lines.extend(
            [
                f"  using value_type = {value_type};",
                "  value_type value;",
            ]
        )
        if type_ir.signed:
            minimum = -(2 ** (width - 1))
            maximum = 2 ** (width - 1) - 1
            pad_bits = bc * 8 - width
            lines.extend(
                [
                    f"  static constexpr value_type MIN_VALUE = static_cast<value_type>({minimum});",
                    f"  static constexpr value_type MAX_VALUE = static_cast<value_type>({maximum});",
                    f"  static constexpr std::uint64_t MASK = {mask_literal};",
                    f"  {class_name}() : value(0) {{}}",
                    f"  {class_name}(value_type value_in) : value(validate_value(value_in)) {{}}",
                    "",
                    "  std::vector<std::uint8_t> to_bytes() const {",
                    "    std::vector<std::uint8_t> bytes(BYTE_COUNT, 0);",
                    "    std::uint64_t bits = static_cast<std::uint64_t>(value) & MASK;",
                ]
            )
            # Sign-extend into padding bits
            if pad_bits > 0:
                lines.extend(
                    [
                        f"    if (value < 0 && WIDTH < BYTE_COUNT * 8U) {{",
                        f"      for (std::size_t i = WIDTH; i < BYTE_COUNT * 8U; ++i) {{",
                        "        bits |= (1ULL << i);",
                        "      }",
                        "    }",
                    ]
                )
            lines.extend(
                [
                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
                    "      bytes[BYTE_COUNT - 1 - idx] = static_cast<std::uint8_t>((bits >> (8U * idx)) & 0xFFU);",
                    "    }",
                    "    return bytes;",
                    "  }",
                    "",
                    "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
                    "    if (bytes.size() != BYTE_COUNT) {",
                    '      throw std::invalid_argument("byte width mismatch");',
                    "    }",
                    "    std::uint64_t bits = 0;",
                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
                    "      bits = (bits << 8U) | bytes[idx];",
                    "    }",
                ]
            )
            # Validate sign extension in padding bits
            if pad_bits > 0:
                byte_mask = _cpp_unsigned_literal((1 << (bc * 8)) - 1 if bc * 8 < 64 else 2**64 - 1)
                lines.extend(
                    [
                        "    std::uint64_t data_bits = bits & MASK;",
                        f"    bool sign_bit = ((data_bits >> ({width - 1}U)) & 1U) != 0U;",
                        f"    std::uint64_t expected_pad = sign_bit ? (~MASK & {byte_mask}) : 0ULL;",
                        f"    if ((bits & ~MASK & {byte_mask}) != expected_pad) {{",
                        '      throw std::invalid_argument("signed padding mismatch");',
                        "    }",
                    ]
                )
            lines.extend(
                [
                    "    bits &= MASK;",
                    "    std::int64_t signed_value = static_cast<std::int64_t>(bits);",
                ]
            )
            if width < 64:
                sign_bit_lit = _cpp_unsigned_literal(1 << (width - 1))
                full_range_lit = _cpp_unsigned_literal(1 << width)
                lines.extend(
                    [
                        f"    if ((bits & {sign_bit_lit}) != 0U && WIDTH < 64) {{",
                        f"      signed_value -= static_cast<std::int64_t>({full_range_lit});",
                        "    }",
                    ]
                )
            lines.extend(
                [
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
                    f"  bool operator==(const {class_name}& other) const = default;",
                    "",
                    " private:",
                    "  static value_type validate_value(value_type value_in) {",
                    "    if (value_in < MIN_VALUE || value_in > MAX_VALUE) {",
                    '      throw std::out_of_range("value out of range");',
                    "    }",
                    "    return value_in;",
                    "  }",
                    "};",
                ]
            )
        else:
            # Unsigned <= 64
            maximum = 2**width - 1 if width < 64 else 2**64 - 1
            lines.extend(
                [
                    f"  static constexpr std::uint64_t MASK = {mask_literal};",
                    f"  static constexpr value_type MAX_VALUE = static_cast<value_type>({_cpp_unsigned_literal(maximum)});",
                    f"  {class_name}() : value(0) {{}}",
                    f"  {class_name}(value_type value_in) : value(validate_value(value_in)) {{}}",
                    "",
                    "  std::vector<std::uint8_t> to_bytes() const {",
                    "    std::vector<std::uint8_t> bytes(BYTE_COUNT, 0);",
                    "    std::uint64_t bits = static_cast<std::uint64_t>(value);",
                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
                    "      bytes[BYTE_COUNT - 1 - idx] = static_cast<std::uint8_t>((bits >> (8U * idx)) & 0xFFU);",
                    "    }",
                    "    return bytes;",
                    "  }",
                    "",
                    "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
                    "    if (bytes.size() != BYTE_COUNT) {",
                    '      throw std::invalid_argument("byte width mismatch");',
                    "    }",
                    "    std::uint64_t bits = 0;",
                    "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
                    "      bits = (bits << 8U) | bytes[idx];",
                    "    }",
                    "    value = validate_value(static_cast<value_type>(bits & MASK));",
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
                    f"  bool operator==(const {class_name}& other) const = default;",
                    "",
                    " private:",
                    "  static value_type validate_value(value_type value_in) {",
                    "    if (value_in > MAX_VALUE) {",
                    '      throw std::out_of_range("value out of range");',
                    "    }",
                    "    return value_in;",
                    "  }",
                    "};",
                ]
            )
    else:
        # Wide unsigned > 64 — vector<uint8_t> in big-endian order
        pad = bc * 8 - width
        msb_mask = _cpp_unsigned_literal((1 << (8 - pad)) - 1) if pad > 0 else "0xFFU"
        lines.extend(
            [
                "  using value_type = std::vector<std::uint8_t>;",
                "  value_type value;",
                f"  {class_name}() : value(BYTE_COUNT, 0U) {{}}",
                f"  {class_name}(const value_type& value_in) : value(validate_value(value_in)) {{}}",
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
                f"  bool operator==(const {class_name}& other) const = default;",
                "",
                " private:",
                "  static value_type validate_value(const value_type& value_in) {",
                "    if (value_in.size() != BYTE_COUNT) {",
                '      throw std::invalid_argument("byte width mismatch");',
                "    }",
                "    value_type normalized = value_in;",
                f"    normalized[0] &= {msb_mask};",
                "    return normalized;",
                "  }",
                "};",
            ]
        )
    return lines


# ---------------------------------------------------------------------------
# Enum class + wrapper
# ---------------------------------------------------------------------------


def _render_cpp_enum(*, type_ir: EnumIR) -> list[str]:
    """Render a C++ enum class and wrapper class."""
    base = type_ir.name[:-2] if type_ir.name.endswith("_t") else type_ir.name
    enum_class_name = f"{base}_enum_t"
    class_name = _type_class_name(type_ir.name)
    width = type_ir.resolved_width
    bc = byte_count(width)
    uint_type = _cpp_scalar_value_type(width=width, signed=False)
    first_member = type_ir.values[0].name if type_ir.values else "0"
    mask_lit = _cpp_unsigned_literal((1 << width) - 1 if width < 64 else 2**64 - 1)

    lines: list[str] = []

    # enum class
    members = ", ".join(f"{v.name} = {_cpp_unsigned_literal(v.resolved_value)}" for v in type_ir.values)
    lines.append(f"enum class {enum_class_name} : {uint_type} {{{members}}};")
    lines.append("")

    # wrapper class
    lines.extend([
        f"class {class_name} {{",
        " public:",
        f"  static constexpr std::size_t WIDTH = {width};",
        f"  static constexpr std::size_t BYTE_COUNT = {bc};",
        f"  using enum_type = {enum_class_name};",
        f"  enum_type value;",
        "",
        f"  {class_name}() : value({enum_class_name}::{first_member}) {{}}",
        f"  explicit {class_name}(enum_type value_in) : value(validate_value(value_in)) {{}}",
        "",
        "  std::vector<std::uint8_t> to_bytes() const {",
        f"    std::vector<std::uint8_t> bytes({bc}, 0);",
        f"    std::uint64_t bits = static_cast<std::uint64_t>(value);",
        f"    for (std::size_t idx = 0; idx < {bc}; ++idx) {{",
        f"      bytes[{bc} - 1 - idx] = static_cast<std::uint8_t>((bits >> (8U * idx)) & 0xFFU);",
        "    }",
        "    return bytes;",
        "  }",
        "",
        "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
        f"    if (bytes.size() != {bc}) {{",
        '      throw std::invalid_argument("byte width mismatch");',
        "    }",
        "    std::uint64_t bits = 0;",
        f"    for (std::size_t idx = 0; idx < {bc}; ++idx) {{",
        "      bits = (bits << 8U) | bytes[idx];",
        "    }",
        f"    value = validate_value(static_cast<enum_type>(bits & {mask_lit}));",
        "  }",
        "",
        f"  {class_name} clone() const {{",
        f"    return {class_name}(value);",
        "  }",
        "",
        "  operator enum_type() const {",
        "    return value;",
        "  }",
        "",
        f"  bool operator==(const {class_name}& other) const = default;",
        "",
        " private:",
        "  static enum_type validate_value(enum_type v) {",
        "    switch (v) {",
    ])
    for v in type_ir.values:
        lines.append(f"      case {enum_class_name}::{v.name}: return v;")
    lines.extend([
        "      default:",
        '        throw std::invalid_argument("unknown enum value");',
        "    }",
        "  }",
        "};",
    ])
    return lines


# ---------------------------------------------------------------------------
# Flags wrapper class
# ---------------------------------------------------------------------------


def _render_cpp_flags(*, type_ir: FlagsIR) -> list[str]:
    """Render a C++ flags wrapper class (big-endian, MSB-first bit packing)."""
    class_name = _type_class_name(type_ir.name)
    num_flags = len(type_ir.fields)
    total_width = num_flags + type_ir.alignment_bits
    bc = byte_count(total_width)
    storage_bits = bc * 8

    # Choose smallest unsigned storage type
    value_type = _cpp_scalar_value_type(width=storage_bits, signed=False)
    is_64 = storage_bits > 32

    # Data mask: top num_flags bits set, bottom alignment_bits clear
    data_mask_val = ((1 << num_flags) - 1) << (storage_bits - num_flags)
    if is_64:
        data_mask_lit = f"0x{data_mask_val:02X}ULL"
    else:
        data_mask_lit = f"0x{data_mask_val:02X}U"

    lines = [
        f"class {class_name} {{",
        " public:",
        f"  static constexpr std::size_t WIDTH = {num_flags};",
        f"  static constexpr std::size_t BYTE_COUNT = {bc};",
        f"  using value_type = {value_type};",
    ]

    # Per-flag mask constants
    for i, field in enumerate(type_ir.fields):
        mask_val = 1 << (storage_bits - 1 - i)
        if is_64:
            mask_lit = f"0x{mask_val:02X}ULL"
        else:
            mask_lit = f"0x{mask_val:02X}U"
        lines.append(f"  static constexpr value_type {field.name.upper()}_MASK = {mask_lit};")

    lines.extend(
        [
            "  value_type value = 0;",
            "",
            f"  {class_name}() = default;",
        ]
    )

    # Per-flag get/set accessors
    for field in type_ir.fields:
        mask_name = f"{field.name.upper()}_MASK"
        lines.extend(
            [
                "",
                f"  bool get_{field.name}() const {{ return (value & {mask_name}) != 0; }}",
                f"  void set_{field.name}(bool v) {{ if (v) value |= {mask_name};"
                f" else value &= static_cast<value_type>(~{mask_name}); }}",
            ]
        )

    # to_bytes
    lines.extend(
        [
            "",
            "  std::vector<std::uint8_t> to_bytes() const {",
            "    std::vector<std::uint8_t> bytes(BYTE_COUNT, 0);",
            f"    value_type masked = value & {data_mask_lit};",
            "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
            f"      bytes[BYTE_COUNT - 1 - idx] = static_cast<std::uint8_t>((static_cast<std::uint64_t>(masked) >> (8U * idx)) & 0xFFU);",
            "    }",
            "    return bytes;",
            "  }",
        ]
    )

    # from_bytes
    lines.extend(
        [
            "",
            "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
            "    if (bytes.size() != BYTE_COUNT) {",
            '      throw std::invalid_argument("byte width mismatch");',
            "    }",
            "    std::uint64_t bits = 0;",
            "    for (std::size_t idx = 0; idx < BYTE_COUNT; ++idx) {",
            "      bits = (bits << 8U) | bytes[idx];",
            "    }",
            f"    value = static_cast<value_type>(bits) & {data_mask_lit};",
            "  }",
        ]
    )

    # clone
    lines.extend(
        [
            "",
            f"  {class_name} clone() const {{",
            f"    {class_name} cloned;",
            "    cloned.value = value;",
            "    return cloned;",
            "  }",
        ]
    )

    # operator==
    lines.extend(
        [
            "",
            f"  bool operator==(const {class_name}& other) const {{",
            f"    return (value & {data_mask_lit}) == (other.value & {data_mask_lit});",
            "  }",
            "};",
        ]
    )

    return lines


# ---------------------------------------------------------------------------
# Struct wrapper class
# ---------------------------------------------------------------------------


def _render_cpp_struct(*, type_ir: StructIR, type_index: dict[str, TypeDefIR]) -> list[str]:
    """Render a C++ struct wrapper class (per-field byte-aligned, big-endian)."""
    class_name = _type_class_name(type_ir.name)
    data_width = _resolved_type_width(type_ir=type_ir, type_index=type_index)
    total_bc = _type_byte_count(type_ir=type_ir, type_index=type_index)
    lines = [
        f"class {class_name} {{",
        " public:",
        f"  static constexpr std::size_t WIDTH = {data_width};",
        f"  static constexpr std::size_t BYTE_COUNT = {total_bc};",
    ]
    for field_ir in type_ir.fields:
        lines.append(f"  {_render_cpp_field_decl(field_ir=field_ir, type_index=type_index)}")
    lines.extend(
        [
            "",
            f"  {class_name}() = default;",
            "",
            "  std::vector<std::uint8_t> to_bytes() const {",
            "    std::vector<std::uint8_t> bytes;",
            "    bytes.reserve(BYTE_COUNT);",
        ]
    )
    for field_ir in type_ir.fields:
        lines.extend(_render_cpp_struct_pack_step(field_ir=field_ir, type_index=type_index))
    if type_ir.alignment_bits > 0:
        align_bytes = type_ir.alignment_bits // 8
        lines.append(f"    for (std::size_t i = 0; i < {align_bytes}; ++i) bytes.push_back(0);")
    lines.extend(
        [
            "    return bytes;",
            "  }",
            "",
            "  void from_bytes(const std::vector<std::uint8_t>& bytes) {",
            "    if (bytes.size() != BYTE_COUNT) {",
            '      throw std::invalid_argument("byte width mismatch");',
            "    }",
            "    std::size_t offset = 0;",
        ]
    )
    for field_ir in type_ir.fields:
        lines.extend(_render_cpp_struct_unpack_step(field_ir=field_ir, type_index=type_index))
    lines.extend(
        [
            "  }",
            "",
            f"  {class_name} clone() const {{",
            f"    {class_name} cloned;",
        ]
    )
    for field_ir in type_ir.fields:
        if _is_struct_ref(field_type=field_ir.type_ir, type_index=type_index) or _is_scalar_ref(
            field_type=field_ir.type_ir, type_index=type_index
        ) or _is_flags_ref(field_type=field_ir.type_ir, type_index=type_index):
            lines.append(f"    cloned.{field_ir.name} = {field_ir.name}.clone();")
        elif _is_wide_inline_scalar(field_type=field_ir.type_ir):
            lines.append(f"    cloned.{field_ir.name} = {field_ir.name};")
        else:
            lines.append(f"    cloned.{field_ir.name} = {field_ir.name};")
    lines.extend(
        [
            "    return cloned;",
            "  }",
            "",
            f"  bool operator==(const {class_name}& other) const = default;",
        ]
    )
    # Per-field encode/decode helpers
    all_helpers: list[str] = []
    for field_ir in type_ir.fields:
        helper_lines = _render_cpp_inline_scalar_helpers(owner_name=class_name, field_ir=field_ir)
        if helper_lines:
            if all_helpers:
                all_helpers.append("")
            all_helpers.extend(helper_lines)
    if all_helpers:
        lines.append("")
        lines.append(" private:")
        lines.extend(all_helpers)
    lines.append("};")
    return lines


# ---------------------------------------------------------------------------
# Field declarations
# ---------------------------------------------------------------------------


def _render_cpp_field_decl(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
    """Render one public C++ field declaration."""
    type_name = _render_cpp_field_type(field_ir=field_ir, type_index=type_index)
    default = _render_cpp_field_default(field_ir=field_ir, type_index=type_index)
    return f"{type_name} {field_ir.name}{default};"


def _render_cpp_field_type(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
    """Render one C++ field type."""
    match field_ir.type_ir:
        case TypeRefIR(name=name):
            return _type_class_name(type_index[name].name)
        case ScalarTypeSpecIR(signed=signed, resolved_width=resolved_width):
            if resolved_width <= 64:
                return _cpp_scalar_value_type(width=resolved_width, signed=signed)
            return "std::vector<std::uint8_t>"
        case _:
            raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")


def _render_cpp_field_default(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> str:
    """Render one C++ field default initializer."""
    match field_ir.type_ir:
        case TypeRefIR():
            return "{}"
        case ScalarTypeSpecIR(resolved_width=resolved_width):
            if resolved_width <= 64:
                return " = 0"
            bc = byte_count(resolved_width)
            return f"{{std::vector<std::uint8_t>({bc}, 0U)}}"
        case _:
            raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")


# ---------------------------------------------------------------------------
# Struct to_bytes — per-field big-endian serialization
# ---------------------------------------------------------------------------


def _render_cpp_struct_pack_step(*, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]) -> list[str]:
    """Render one C++ struct packing step (big-endian, per-field byte-aligned)."""
    lines: list[str] = []
    if isinstance(field_ir.type_ir, ScalarTypeSpecIR) and field_ir.type_ir.resolved_width <= 64:
        # Inline scalar ≤64 — use encode helper
        lines.extend(
            [
                "    {",
                f"      auto field_bytes = encode_{field_ir.name}({field_ir.name});",
                "      bytes.insert(bytes.end(), field_bytes.begin(), field_bytes.end());",
                "    }",
            ]
        )
    elif isinstance(field_ir.type_ir, ScalarTypeSpecIR):
        # Wide inline scalar >64 — vector IS big-endian bytes, but need to normalize MSB padding
        bc = byte_count(field_ir.type_ir.resolved_width)
        pad = bc * 8 - field_ir.type_ir.resolved_width
        lines.extend(
            [
                "    {",
                f"      auto field_bytes = encode_{field_ir.name}({field_ir.name});",
                "      bytes.insert(bytes.end(), field_bytes.begin(), field_bytes.end());",
                "    }",
            ]
        )
    elif isinstance(field_ir.type_ir, TypeRefIR):
        target = type_index[field_ir.type_ir.name]
        if isinstance(target, (StructIR, ScalarAliasIR, FlagsIR)):
            lines.extend(
                [
                    "    {",
                    f"      auto field_bytes = {field_ir.name}.to_bytes();",
                    "      bytes.insert(bytes.end(), field_bytes.begin(), field_bytes.end());",
                    "    }",
                ]
            )
        else:
            raise ValidationError(f"unsupported type ref target {type(target).__name__}")
    else:
        raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
    return lines


# ---------------------------------------------------------------------------
# Struct from_bytes — per-field big-endian deserialization
# ---------------------------------------------------------------------------


def _render_cpp_struct_unpack_step(
    *, field_ir: StructFieldIR, type_index: dict[str, TypeDefIR]
) -> list[str]:
    """Render one C++ struct unpacking step (big-endian, per-field byte-aligned)."""
    fbc = _field_byte_count(field=field_ir, type_index=type_index)
    lines: list[str] = []
    if isinstance(field_ir.type_ir, ScalarTypeSpecIR) and field_ir.type_ir.resolved_width <= 64:
        lines.extend(
            [
                f"    {field_ir.name} = decode_{field_ir.name}(bytes, offset);",
                f"    offset += {fbc};",
            ]
        )
    elif isinstance(field_ir.type_ir, ScalarTypeSpecIR):
        # Wide inline scalar
        lines.extend(
            [
                f"    {field_ir.name} = decode_{field_ir.name}(bytes, offset);",
                f"    offset += {fbc};",
            ]
        )
    elif isinstance(field_ir.type_ir, TypeRefIR):
        target = type_index[field_ir.type_ir.name]
        if isinstance(target, (StructIR, ScalarAliasIR, FlagsIR)):
            lines.extend(
                [
                    "    {",
                    f"      std::vector<std::uint8_t> field_bytes(bytes.begin() + static_cast<std::ptrdiff_t>(offset),"
                    f" bytes.begin() + static_cast<std::ptrdiff_t>(offset + {fbc}));",
                    f"      {field_ir.name}.from_bytes(field_bytes);",
                    f"      offset += {fbc};",
                    "    }",
                ]
            )
        else:
            raise ValidationError(f"unsupported type ref target {type(target).__name__}")
    else:
        raise ValidationError(f"unsupported C++ struct field type {type(field_ir.type_ir).__name__}")
    return lines


# ---------------------------------------------------------------------------
# Inline scalar encode/decode helpers (private section of struct class)
# ---------------------------------------------------------------------------


def _render_cpp_inline_scalar_helpers(*, owner_name: str, field_ir: StructFieldIR) -> list[str]:
    """Render private helper functions for one inline scalar field (big-endian)."""
    if not isinstance(field_ir.type_ir, ScalarTypeSpecIR):
        return []
    width = field_ir.type_ir.resolved_width
    bc = byte_count(width)
    pad = bc * 8 - width
    if width <= 64:
        return _render_narrow_inline_helpers(field_ir=field_ir, width=width, bc=bc, pad=pad)
    return _render_wide_inline_helpers(field_ir=field_ir, width=width, bc=bc, pad=pad)


def _render_narrow_inline_helpers(
    *, field_ir: StructFieldIR, width: int, bc: int, pad: int
) -> list[str]:
    """Encode/decode helpers for inline scalar ≤64 bits."""
    assert isinstance(field_ir.type_ir, ScalarTypeSpecIR)
    signed = field_ir.type_ir.signed
    value_type = _cpp_scalar_value_type(width=width, signed=signed)
    mask = (1 << width) - 1 if width < 64 else 2**64 - 1
    mask_lit = _cpp_unsigned_literal(mask)
    lines: list[str] = []

    if signed:
        # --- encode (signed) ---
        lines.extend(
            [
                f"  static std::vector<std::uint8_t> encode_{field_ir.name}({value_type} v) {{",
                f"    validate_{field_ir.name}(v);",
                f"    constexpr std::uint64_t MASK = {mask_lit};",
                "    std::uint64_t bits = static_cast<std::uint64_t>(v) & MASK;",
            ]
        )
        if pad > 0:
            lines.extend(
                [
                    "    if (v < 0) {",
                    "      bits |= ~MASK;",
                    "    }",
                ]
            )
        lines.extend(
            [
                f"    std::vector<std::uint8_t> b({bc}, 0U);",
                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
                f"      b[{bc} - 1 - i] = static_cast<std::uint8_t>((bits >> (8U * i)) & 0xFFU);",
                "    }",
                "    return b;",
                "  }",
                "",
            ]
        )
        # --- decode (signed) ---
        lines.extend(
            [
                f"  static {value_type} decode_{field_ir.name}(const std::vector<std::uint8_t>& bytes, std::size_t offset) {{",
                "    std::uint64_t bits = 0;",
                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
                "      bits = (bits << 8U) | bytes[offset + i];",
                "    }",
            ]
        )
        if pad > 0:
            byte_total_mask = (1 << (bc * 8)) - 1 if bc * 8 < 64 else 2**64 - 1
            byte_total_mask_lit = _cpp_unsigned_literal(byte_total_mask)
            lines.extend(
                [
                    f"    constexpr std::uint64_t MASK = {mask_lit};",
                    "    std::uint64_t data_bits = bits & MASK;",
                    f"    bool sign_bit = ((data_bits >> ({width - 1}U)) & 1U) != 0U;",
                    f"    std::uint64_t expected_pad = sign_bit ? (~MASK & {byte_total_mask_lit}) : 0ULL;",
                    f"    if ((bits & ~MASK & {byte_total_mask_lit}) != expected_pad) {{",
                    '      throw std::invalid_argument("signed padding mismatch");',
                    "    }",
                    "    bits = data_bits;",
                ]
            )
        else:
            lines.append(f"    constexpr std::uint64_t MASK = {mask_lit};")
            lines.append("    bits &= MASK;")
        lines.append("    std::int64_t signed_value = static_cast<std::int64_t>(bits);")
        if width < 64:
            sign_bit_lit = _cpp_unsigned_literal(1 << (width - 1))
            full_range_lit = _cpp_unsigned_literal(1 << width)
            lines.extend(
                [
                    f"    if ((bits & {sign_bit_lit}) != 0U) {{",
                    f"      signed_value -= static_cast<std::int64_t>({full_range_lit});",
                    "    }",
                ]
            )
        lines.extend(
            [
                f"    return validate_{field_ir.name}(static_cast<{value_type}>(signed_value));",
                "  }",
                "",
            ]
        )
    else:
        # --- encode (unsigned) ---
        lines.extend(
            [
                f"  static std::vector<std::uint8_t> encode_{field_ir.name}({value_type} v) {{",
                f"    validate_{field_ir.name}(v);",
                f"    std::vector<std::uint8_t> b({bc}, 0U);",
                "    std::uint64_t bits = static_cast<std::uint64_t>(v);",
                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
                f"      b[{bc} - 1 - i] = static_cast<std::uint8_t>((bits >> (8U * i)) & 0xFFU);",
                "    }",
                "    return b;",
                "  }",
                "",
            ]
        )
        # --- decode (unsigned) ---
        lines.extend(
            [
                f"  static {value_type} decode_{field_ir.name}(const std::vector<std::uint8_t>& bytes, std::size_t offset) {{",
                "    std::uint64_t bits = 0;",
                f"    for (std::size_t i = 0; i < {bc}; ++i) {{",
                "      bits = (bits << 8U) | bytes[offset + i];",
                "    }",
            ]
        )
        if pad > 0:
            lines.append(f"    bits &= {mask_lit};")
        lines.extend(
            [
                f"    return validate_{field_ir.name}(static_cast<{value_type}>(bits));",
                "  }",
                "",
            ]
        )

    # --- validate ---
    minimum = -(2 ** (width - 1)) if signed else 0
    maximum = 2 ** (width - 1) - 1 if signed else (2**width - 1 if width < 64 else 2**64 - 1)
    lines.append(f"  static {value_type} validate_{field_ir.name}({value_type} value_in) {{")
    if signed:
        lines.extend(
            [
                f"    constexpr {value_type} MIN_VALUE = static_cast<{value_type}>({minimum});",
                f"    constexpr {value_type} MAX_VALUE = static_cast<{value_type}>({maximum});",
                "    if (value_in < MIN_VALUE || value_in > MAX_VALUE) {",
                '      throw std::out_of_range("value out of range");',
                "    }",
            ]
        )
    else:
        lines.extend(
            [
                f"    constexpr {value_type} MAX_VALUE = static_cast<{value_type}>({_cpp_unsigned_literal(maximum)});",
                "    if (value_in > MAX_VALUE) {",
                '      throw std::out_of_range("value out of range");',
                "    }",
            ]
        )
    lines.extend(
        [
            "    return value_in;",
            "  }",
        ]
    )
    return lines


def _render_wide_inline_helpers(
    *, field_ir: StructFieldIR, width: int, bc: int, pad: int
) -> list[str]:
    """Encode/decode helpers for inline scalar > 64 bits (unsigned, vector<uint8_t>, big-endian)."""
    msb_mask = _cpp_unsigned_literal((1 << (8 - pad)) - 1) if pad > 0 else "0xFFU"
    lines = [
        f"  static std::vector<std::uint8_t> encode_{field_ir.name}(const std::vector<std::uint8_t>& value_in) {{",
        f"    if (value_in.size() != {bc}U) {{",
        '      throw std::invalid_argument("byte width mismatch");',
        "    }",
        "    std::vector<std::uint8_t> normalized = value_in;",
        f"    normalized[0] &= {msb_mask};",
        "    return normalized;",
        "  }",
        "",
        f"  static std::vector<std::uint8_t> decode_{field_ir.name}(const std::vector<std::uint8_t>& bytes, std::size_t offset) {{",
        f"    std::vector<std::uint8_t> result(bytes.begin() + static_cast<std::ptrdiff_t>(offset),"
        f" bytes.begin() + static_cast<std::ptrdiff_t>(offset + {bc}));",
    ]
    if pad > 0:
        lines.append(f"    result[0] &= {msb_mask};")
    lines.extend(
        [
            "    return result;",
            "  }",
        ]
    )
    return lines


# ---------------------------------------------------------------------------
# Width / byte-count resolution helpers
# ---------------------------------------------------------------------------


def _resolved_type_width(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
    """Resolve the data width (sum of field data widths) of one type."""
    if isinstance(type_ir, ScalarAliasIR):
        return type_ir.resolved_width
    if isinstance(type_ir, FlagsIR):
        return len(type_ir.fields)
    if isinstance(type_ir, EnumIR):
        return type_ir.resolved_width
    return sum(_resolved_field_width(field_type=field.type_ir, type_index=type_index) for field in type_ir.fields)


def _resolved_field_width(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> int:
    """Resolve the data width of one field type."""
    if isinstance(field_type, ScalarTypeSpecIR):
        return field_type.resolved_width
    return _resolved_type_width(type_ir=type_index[field_type.name], type_index=type_index)


def _type_byte_count(*, type_ir: TypeDefIR, type_index: dict[str, TypeDefIR]) -> int:
    """Compute the byte-aligned byte count for a type (sum of per-field byte counts + alignment)."""
    if isinstance(type_ir, ScalarAliasIR):
        return byte_count(type_ir.resolved_width)
    if isinstance(type_ir, FlagsIR):
        return (len(type_ir.fields) + type_ir.alignment_bits) // 8
    if isinstance(type_ir, EnumIR):
        return byte_count(type_ir.resolved_width)
    field_bytes = sum(_field_byte_count(field=field, type_index=type_index) for field in type_ir.fields)
    return field_bytes + type_ir.alignment_bits // 8


def _field_byte_count(*, field: StructFieldIR, type_index: dict[str, TypeDefIR]) -> int:
    """Compute the byte-aligned byte count for one field."""
    match field.type_ir:
        case ScalarTypeSpecIR(resolved_width=resolved_width):
            return byte_count(resolved_width)
        case TypeRefIR(name=name):
            target = type_index[name]
            if isinstance(target, ScalarAliasIR):
                return byte_count(target.resolved_width)
            return _type_byte_count(type_ir=target, type_index=type_index)
        case _:
            raise ValidationError(f"unsupported field type {type(field.type_ir).__name__}")


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------


def _cpp_scalar_value_type(*, width: int, signed: bool) -> str:
    """Choose the public C++ storage type for a scalar width."""
    if width <= 8:
        return "std::int8_t" if signed else "std::uint8_t"
    if width <= 16:
        return "std::int16_t" if signed else "std::uint16_t"
    if width <= 32:
        return "std::int32_t" if signed else "std::uint32_t"
    return "std::int64_t" if signed else "std::uint64_t"


def _cpp_unsigned_literal(value: int) -> str:
    """Render an unsigned integer literal for C++."""
    if value <= 0xFFFFFFFF:
        return f"{value}U"
    return f"{value}ULL"


def _is_struct_ref(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> bool:
    """Return whether one field references a named struct."""
    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], StructIR)


def _is_scalar_ref(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> bool:
    """Return whether one field references a named scalar alias."""
    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], ScalarAliasIR)


def _is_flags_ref(*, field_type: FieldTypeIR, type_index: dict[str, TypeDefIR]) -> bool:
    """Return whether one field references a named flags type."""
    return isinstance(field_type, TypeRefIR) and isinstance(type_index[field_type.name], FlagsIR)


def _is_wide_inline_scalar(*, field_type: FieldTypeIR) -> bool:
    """Return whether one field is an inline scalar wider than 64 bits."""
    return isinstance(field_type, ScalarTypeSpecIR) and field_type.resolved_width > 64


def _type_class_name(type_name: str) -> str:
    """Convert a generated type name to its software wrapper class name."""
    if type_name.endswith("_t"):
        return f"{type_name[:-2]}_ct"
    return f"{type_name}_ct"
