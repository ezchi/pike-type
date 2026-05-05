"""Validation entry points."""

from __future__ import annotations

from piketype.errors import ValidationError
import re

from piketype.ir.nodes import EnumIR, FlagsIR, ModuleIR, RepoIR, ScalarAliasIR, ScalarTypeSpecIR, StructIR, TypeRefIR
from piketype.validate.keywords import (
    CPP_KEYWORDS,
    PY_HARD_KEYWORDS,
    PY_SOFT_KEYWORDS,
    SV_KEYWORDS,
    keyword_languages,
)


_UPPER_CASE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


_FLAGS_RESERVED_API_NAMES = frozenset({"value", "to_bytes", "from_bytes", "clone", "width", "byte_count"})


def validate_repo(repo: RepoIR) -> None:
    """Validate the frozen repository IR."""
    type_index = {
        (module.ref.python_module_name, type_ir.name): type_ir
        for module in repo.modules
        for type_ir in module.types
    }
    for module in repo.modules:
        if not module.constants and not module.types and not module.vec_constants:
            raise ValidationError(f"{module.ref.repo_relative_path}: piketype file defines no DSL objects")

        seen_names: set[str] = set()
        for const in module.constants:
            if const.name in seen_names:
                raise ValidationError(f"{module.ref.repo_relative_path}: duplicate constant name {const.name}")
            seen_names.add(const.name)
            _validate_const_storage(
                value=const.resolved_value,
                signed=const.resolved_signed,
                width=const.resolved_width,
                module_path=module.ref.repo_relative_path,
                const_name=const.name,
            )
        for vec_const in module.vec_constants:
            if vec_const.name in seen_names:
                raise ValidationError(
                    f"{module.ref.repo_relative_path}: duplicate constant name {vec_const.name}"
                )
            seen_names.add(vec_const.name)
        seen_type_names: set[str] = set()
        for type_ir in module.types:
            if type_ir.name in seen_names or type_ir.name in seen_type_names:
                raise ValidationError(f"{module.ref.repo_relative_path}: duplicate type name {type_ir.name}")
            seen_type_names.add(type_ir.name)
            if not type_ir.name.endswith("_t"):
                raise ValidationError(f"{module.ref.repo_relative_path}: type {type_ir.name} must end with _t")
            if isinstance(type_ir, ScalarAliasIR):
                if type_ir.resolved_width <= 0:
                    raise ValidationError(f"{module.ref.repo_relative_path}: type {type_ir.name} width must be positive")
                continue
            if isinstance(type_ir, StructIR):
                if not type_ir.fields:
                    raise ValidationError(f"{module.ref.repo_relative_path}: struct {type_ir.name} must have at least one field")
                seen_field_names: set[str] = set()
                for field in type_ir.fields:
                    if field.name in seen_field_names:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: struct {type_ir.name} has duplicate field {field.name}"
                        )
                    seen_field_names.add(field.name)
                    if isinstance(field.type_ir, ScalarTypeSpecIR):
                        if field.type_ir.resolved_width <= 0:
                            raise ValidationError(
                                f"{module.ref.repo_relative_path}: struct {type_ir.name} field {field.name} width must be positive"
                            )
                        continue
                    if isinstance(field.type_ir, TypeRefIR):
                        target = type_index.get((field.type_ir.module.python_module_name, field.type_ir.name))
                        if target is None:
                            raise ValidationError(
                                f"{module.ref.repo_relative_path}: struct {type_ir.name} field {field.name} "
                                f"references unknown type {field.type_ir.module.python_module_name}::{field.type_ir.name}"
                            )
                        if not isinstance(target, (ScalarAliasIR, StructIR, FlagsIR, EnumIR)):
                            raise ValidationError(
                                f"{module.ref.repo_relative_path}: struct {type_ir.name} field {field.name} "
                                "must reference a scalar alias, struct, flags, or enum"
                            )
                        continue
                continue
            if isinstance(type_ir, FlagsIR):
                if not type_ir.fields:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: flags {type_ir.name} must have at least one flag"
                    )
                if len(type_ir.fields) > 64:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: flags {type_ir.name} has {len(type_ir.fields)} flags, "
                        "maximum is 64"
                    )
                seen_flag_names: set[str] = set()
                for flag in type_ir.fields:
                    if flag.name in seen_flag_names:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: flags {type_ir.name} has duplicate flag {flag.name}"
                        )
                    seen_flag_names.add(flag.name)
                    if flag.name.endswith("_pad"):
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: flags {type_ir.name} "
                            f"flag '{flag.name}' uses reserved '_pad' suffix"
                        )
                    if flag.name in _FLAGS_RESERVED_API_NAMES:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: flags {type_ir.name} "
                            f"flag '{flag.name}' collides with generated class API name"
                        )
                continue
            if isinstance(type_ir, EnumIR):
                if not type_ir.values:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: enum {type_ir.name} must have at least one value"
                    )
                if type_ir.resolved_width <= 0:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: enum {type_ir.name} width must be positive"
                    )
                if type_ir.resolved_width > 64:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: enum {type_ir.name} width {type_ir.resolved_width} exceeds maximum 64"
                    )
                seen_value_names: set[str] = set()
                seen_resolved_values: set[int] = set()
                for enum_val in type_ir.values:
                    if not _UPPER_CASE_RE.fullmatch(enum_val.name):
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                            f"value name {enum_val.name!r} must be UPPER_CASE"
                        )
                    if enum_val.name in seen_value_names:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                            f"has duplicate value name {enum_val.name!r}"
                        )
                    seen_value_names.add(enum_val.name)
                    if enum_val.resolved_value in seen_resolved_values:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                            f"has duplicate resolved value {enum_val.resolved_value}"
                        )
                    seen_resolved_values.add(enum_val.resolved_value)
                    if enum_val.resolved_value < 0:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                            f"value {enum_val.name} has negative value {enum_val.resolved_value}"
                        )
                    if enum_val.resolved_value >= 2**type_ir.resolved_width:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                            f"value {enum_val.name}={enum_val.resolved_value} does not fit in {type_ir.resolved_width} bits"
                        )
                continue
            raise ValidationError(f"{module.ref.repo_relative_path}: unsupported type node {type(type_ir).__name__}")
        _validate_struct_cycles(module=module, type_index=type_index)
        _validate_pad_suffix_reservation(module=module)
        _validate_signed_width_constraint(module=module, type_index=type_index)
        _validate_generated_identifier_collision(module=module)
        _validate_alignment_bits(module=module)
        _validate_enum_literal_collision(module=module)
    _validate_repo_struct_cycles(repo=repo, type_index=type_index)
    _validate_cross_module_name_conflicts(repo=repo, type_index=type_index)
    _validate_reserved_keywords(repo=repo)


def _validate_const_storage(*, value: int, signed: bool, width: int, module_path: str, const_name: str) -> None:
    """Validate that constant IR storage is internally consistent."""
    if width not in (32, 64):
        raise ValidationError(f"{module_path}: constant {const_name} has unsupported width {width}")
    if signed:
        minimum = -(2 ** (width - 1))
        maximum = 2 ** (width - 1) - 1
    else:
        minimum = 0
        maximum = 2**width - 1
    if value < minimum or value > maximum:
        raise ValidationError(
            f"{module_path}: constant {const_name} out of supported range for "
            f"{'signed' if signed else 'unsigned'} {width}-bit storage [{minimum}, {maximum}]"
        )


def _validate_struct_cycles(*, module, type_index: dict[tuple[str, str], object]) -> None:
    """Reject same-module struct cycles (preserves existing wording for golden compat).

    Cross-module struct cycles are detected by `_validate_repo_struct_cycles`
    over the full repo graph; this per-module pass keeps the existing single-
    module error wording for the existing negative-test golden.
    """
    struct_graph: dict[str, set[str]] = {}
    for type_ir in module.types:
        if not isinstance(type_ir, StructIR):
            continue
        deps: set[str] = set()
        for field in type_ir.fields:
            if not isinstance(field.type_ir, TypeRefIR):
                continue
            # Same-module cycle detection only — cross-module cycles handled at repo level.
            if field.type_ir.module.python_module_name != module.ref.python_module_name:
                continue
            target = type_index.get((field.type_ir.module.python_module_name, field.type_ir.name))
            if isinstance(target, StructIR):
                deps.add(target.name)
        struct_graph[type_ir.name] = deps

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in visiting:
            raise ValidationError(f"{module.ref.repo_relative_path}: recursive struct dependency detected at {name}")
        visiting.add(name)
        for dep in struct_graph.get(name, set()):
            visit(dep)
        visiting.remove(name)
        visited.add(name)

    for name in struct_graph:
        visit(name)


def _validate_pad_suffix_reservation(*, module: ModuleIR) -> None:
    """FR-11: Reject struct fields whose name ends with _pad."""
    for type_ir in module.types:
        if not isinstance(type_ir, StructIR):
            continue
        for field in type_ir.fields:
            if field.name.endswith("_pad"):
                raise ValidationError(
                    f"{module.ref.repo_relative_path}: struct {type_ir.name} "
                    f"field '{field.name}' uses reserved '_pad' suffix"
                )


def _validate_signed_width_constraint(
    *,
    module: ModuleIR,
    type_index: dict[tuple[str, str], object],
) -> None:
    """FR-13: Reject signed scalars with width > 64."""
    for type_ir in module.types:
        if isinstance(type_ir, ScalarAliasIR):
            if type_ir.signed and type_ir.resolved_width > 64:
                raise ValidationError(
                    f"{module.ref.repo_relative_path}: signed scalar {type_ir.name} "
                    f"width {type_ir.resolved_width} exceeds maximum 64-bit signed width"
                )
        elif isinstance(type_ir, StructIR):
            for field in type_ir.fields:
                if isinstance(field.type_ir, ScalarTypeSpecIR):
                    if field.type_ir.signed and field.type_ir.resolved_width > 64:
                        raise ValidationError(
                            f"{module.ref.repo_relative_path}: struct {type_ir.name} "
                            f"signed field '{field.name}' width {field.type_ir.resolved_width} "
                            "exceeds maximum 64-bit signed width"
                        )


def _validate_generated_identifier_collision(*, module: ModuleIR) -> None:
    """FR-14: Reject modules where constant names collide with generated identifiers."""
    reserved: dict[str, str] = {}
    for type_ir in module.types:
        base = type_ir.name[:-2] if type_ir.name.endswith("_t") else type_ir.name
        upper_base = base.upper()
        for ident in (
            f"LP_{upper_base}_WIDTH",
            f"LP_{upper_base}_BYTE_COUNT",
            f"pack_{base}",
            f"unpack_{base}",
        ):
            reserved[ident] = type_ir.name
    const_names = {const.name for const in module.constants} | {v.name for v in module.vec_constants}
    for const_name in const_names:
        if const_name in reserved:
            raise ValidationError(
                f"{module.ref.repo_relative_path}: constant '{const_name}' "
                f"collides with generated identifier for type '{reserved[const_name]}'"
            )
    for type_ir in module.types:
        if isinstance(type_ir, EnumIR):
            for enum_val in type_ir.values:
                if enum_val.name in reserved:
                    raise ValidationError(
                        f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                        f"value '{enum_val.name}' collides with generated identifier for type '{reserved[enum_val.name]}'"
                    )


def _validate_alignment_bits(*, module: ModuleIR) -> None:
    """Validate that struct alignment_bits is a multiple of 8."""
    for type_ir in module.types:
        if not isinstance(type_ir, StructIR):
            continue
        if type_ir.alignment_bits > 0 and type_ir.alignment_bits % 8 != 0:
            raise ValidationError(
                f"{module.ref.repo_relative_path}: struct {type_ir.name} "
                f"alignment_bits {type_ir.alignment_bits} is not a multiple of 8"
            )


def _validate_enum_literal_collision(*, module: ModuleIR) -> None:
    """FR-17: Reject enum value names that collide across enums or with constants."""
    const_names = {const.name for const in module.constants} | {v.name for v in module.vec_constants}
    all_enum_value_names: dict[str, str] = {}
    for type_ir in module.types:
        if not isinstance(type_ir, EnumIR):
            continue
        for enum_val in type_ir.values:
            if enum_val.name in const_names:
                raise ValidationError(
                    f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                    f"value '{enum_val.name}' collides with constant name in same module"
                )
            if enum_val.name in all_enum_value_names:
                raise ValidationError(
                    f"{module.ref.repo_relative_path}: enum {type_ir.name} "
                    f"value '{enum_val.name}' collides with value in enum {all_enum_value_names[enum_val.name]}"
                )
            all_enum_value_names[enum_val.name] = type_ir.name


def _validate_repo_struct_cycles(*, repo: RepoIR, type_index: dict[tuple[str, str], object]) -> None:
    """FR-6: Reject cross-module struct cycles using a repo-level dependency graph.

    Same-module cycles are caught first by `_validate_struct_cycles` per module
    (preserving existing wording). This pass detects cycles whose path crosses
    a module boundary at least once.
    """
    Node = tuple[str, str]  # (module_python_name, struct_name)
    graph: dict[Node, set[Node]] = {}
    for module in repo.modules:
        for type_ir in module.types:
            if not isinstance(type_ir, StructIR):
                continue
            node: Node = (module.ref.python_module_name, type_ir.name)
            edges: set[Node] = set()
            for field in type_ir.fields:
                if not isinstance(field.type_ir, TypeRefIR):
                    continue
                target_key = (field.type_ir.module.python_module_name, field.type_ir.name)
                target = type_index.get(target_key)
                if isinstance(target, StructIR):
                    edges.add(target_key)
            graph[node] = edges

    visiting: list[Node] = []
    visited: set[Node] = set()

    def visit(node: Node) -> None:
        if node in visited:
            return
        if node in visiting:
            cycle_start = visiting.index(node)
            cycle = visiting[cycle_start:] + [node]
            # Same-module cycles already raised; skip those here.
            modules_on_cycle = {n[0] for n in cycle}
            if len(modules_on_cycle) >= 2:
                # Rotate so lex-smallest node is first.
                lex_min_idx = cycle.index(min(cycle))
                rotated = cycle[lex_min_idx:-1] + cycle[:lex_min_idx]
                rotated_with_close = rotated + [rotated[0]]
                path_str = " -> ".join(f"{m}::{n}" for (m, n) in rotated_with_close)
                raise ValidationError(
                    f"recursive cross-module struct dependency detected: {path_str}"
                )
            return
        visiting.append(node)
        for dep in graph.get(node, set()):
            visit(dep)
        visiting.pop()
        visited.add(node)

    for node in sorted(graph.keys()):
        visit(node)


def _validate_cross_module_name_conflicts(*, repo: RepoIR, type_index: dict[tuple[str, str], object]) -> None:
    """FR-8: Reject local-vs-imported, imported-vs-imported type-name and enum-literal collisions."""
    for module in repo.modules:
        # Direct cross-module targets (one entry per distinct target module).
        cross_targets: dict[str, set[str]] = {}  # target_module -> set of imported type names
        for type_ir in module.types:
            if not isinstance(type_ir, StructIR):
                continue
            for field in type_ir.fields:
                if isinstance(field.type_ir, TypeRefIR):
                    target_module = field.type_ir.module.python_module_name
                    if target_module == module.ref.python_module_name:
                        continue
                    cross_targets.setdefault(target_module, set()).add(field.type_ir.name)

        if not cross_targets:
            continue

        local_type_names = {t.name for t in module.types}

        # Local-vs-imported type-name conflict.
        for target_module, names in cross_targets.items():
            for n in names:
                if n in local_type_names:
                    raise ValidationError(
                        f"module {module.ref.python_module_name}: "
                        f"local type {n} shadows cross-module reference to {target_module}::{n}"
                    )

        # Imported-vs-imported type-name conflict.
        # Each cross-module target's wildcard import brings ALL of its types into scope, so
        # we need to consider all types defined in those target modules, not just the ones
        # the current module references.
        wildcard_type_owners: dict[str, list[str]] = {}  # type_name -> [target_modules]
        for target_module in cross_targets:
            target_module_ir = next(
                (m for m in repo.modules if m.ref.python_module_name == target_module),
                None,
            )
            if target_module_ir is None:
                continue
            for t in target_module_ir.types:
                wildcard_type_owners.setdefault(t.name, []).append(target_module)
        for type_name, owners in wildcard_type_owners.items():
            if len(owners) >= 2:
                raise ValidationError(
                    f"module {module.ref.python_module_name}: cross-module references to "
                    f"{owners[0]}::{type_name} and {owners[1]}::{type_name} create an ambiguous import"
                )

        # Enum literal collisions across wildcard imports.
        wildcard_enum_literals: dict[str, list[str]] = {}  # literal_name -> [target_modules]
        for target_module in cross_targets:
            target_module_ir = next(
                (m for m in repo.modules if m.ref.python_module_name == target_module),
                None,
            )
            if target_module_ir is None:
                continue
            for t in target_module_ir.types:
                if isinstance(t, EnumIR):
                    for v in t.values:
                        wildcard_enum_literals.setdefault(v.name, []).append(target_module)
        # Imported-vs-imported enum literal collision.
        for lit, owners in wildcard_enum_literals.items():
            if len(owners) >= 2:
                raise ValidationError(
                    f"module {module.ref.python_module_name}: wildcard import of "
                    f"{owners[0]} and {owners[1]} creates ambiguous enum literal {lit}"
                )
        # Local-vs-imported enum literal collision.
        local_enum_literals = {
            v.name
            for t in module.types
            if isinstance(t, EnumIR)
            for v in t.values
        }
        for lit, owners in wildcard_enum_literals.items():
            if lit in local_enum_literals:
                raise ValidationError(
                    f"module {module.ref.python_module_name}: local enum literal {lit} "
                    f"collides with wildcard import from {owners[0]}"
                )


def _format_top_level_msg(
    *,
    module_path: str,
    kind: str,
    identifier: str,
    langs: tuple[str, ...],
) -> str:
    """Build the FR-3 normative error string for a top-level identifier
    (constant, type, or module name)."""
    return (
        f"{module_path}: {kind} '{identifier}' is a reserved keyword in "
        f"target language(s): {', '.join(langs)}. Rename it."
    )


def _format_field_msg(
    *,
    module_path: str,
    kind: str,
    type_name: str,
    role: str,
    identifier: str,
    langs: tuple[str, ...],
) -> str:
    """Build the FR-3 normative error string for an identifier nested inside
    a type (struct field, flags flag, enum value)."""
    return (
        f"{module_path}: {kind} {type_name} {role} '{identifier}' is a "
        f"reserved keyword in target language(s): {', '.join(langs)}. Rename it."
    )


def _module_name_languages(*, basename: str) -> tuple[str, ...]:
    """Per-language emitted-form keyword check for a module basename (FR-1.6).

    SV emits ``<basename>_pkg`` (the suffix is checked against the SV set);
    C++ and Python emit the bare basename. The hard-vs-soft Python tiebreaker
    matches ``keyword_languages``: hard wins.
    """
    sv_form = f"{basename}_pkg"
    hits: list[str] = []
    if basename in CPP_KEYWORDS:
        hits.append("C++")
    if basename in PY_HARD_KEYWORDS:
        hits.append("Python")
    elif basename in PY_SOFT_KEYWORDS:
        hits.append("Python (soft)")
    if sv_form in SV_KEYWORDS:
        hits.append("SystemVerilog")
    hits.sort()
    return tuple(hits)


def _validate_reserved_keywords(*, repo: RepoIR) -> None:
    """FR-1..FR-9: reject DSL identifiers that collide with target-language keywords.

    Iterates the repo in deterministic declaration order, raising
    :class:`ValidationError` on the first identifier whose emitted form is a
    reserved keyword in any active target language. The message shape is
    pinned by FR-3 of the spec.
    """
    for module in repo.modules:
        module_path = module.ref.repo_relative_path

        # FR-1.6 — module basename, per-language emitted form.
        module_langs = _module_name_languages(basename=module.ref.basename)
        if module_langs:
            raise ValidationError(
                _format_top_level_msg(
                    module_path=module_path,
                    kind="module name",
                    identifier=module.ref.basename,
                    langs=module_langs,
                )
            )

        # FR-1.5 — constants.
        for const in module.constants:
            const_langs = keyword_languages(identifier=const.name)
            if const_langs:
                raise ValidationError(
                    _format_top_level_msg(
                        module_path=module_path,
                        kind="constant",
                        identifier=const.name,
                        langs=const_langs,
                    )
                )
        for vec_const in module.vec_constants:
            vec_const_langs = keyword_languages(identifier=vec_const.name)
            if vec_const_langs:
                raise ValidationError(
                    _format_top_level_msg(
                        module_path=module_path,
                        kind="constant",
                        identifier=vec_const.name,
                        langs=vec_const_langs,
                    )
                )

        # FR-1.1..FR-1.4 — types and their nested identifiers.
        for type_ir in module.types:
            type_langs = keyword_languages(identifier=type_ir.name)
            if type_langs:
                kind = _type_kind(type_ir=type_ir)
                raise ValidationError(
                    _format_top_level_msg(
                        module_path=module_path,
                        kind=kind,
                        identifier=type_ir.name,
                        langs=type_langs,
                    )
                )

            if isinstance(type_ir, StructIR):
                for field in type_ir.fields:
                    field_langs = keyword_languages(identifier=field.name)
                    if field_langs:
                        raise ValidationError(
                            _format_field_msg(
                                module_path=module_path,
                                kind="struct",
                                type_name=type_ir.name,
                                role="field",
                                identifier=field.name,
                                langs=field_langs,
                            )
                        )
            elif isinstance(type_ir, FlagsIR):
                for flag in type_ir.fields:
                    flag_langs = keyword_languages(identifier=flag.name)
                    if flag_langs:
                        raise ValidationError(
                            _format_field_msg(
                                module_path=module_path,
                                kind="flags",
                                type_name=type_ir.name,
                                role="flag",
                                identifier=flag.name,
                                langs=flag_langs,
                            )
                        )
            elif isinstance(type_ir, EnumIR):
                for enum_val in type_ir.values:
                    value_langs = keyword_languages(identifier=enum_val.name)
                    if value_langs:
                        raise ValidationError(
                            _format_field_msg(
                                module_path=module_path,
                                kind="enum",
                                type_name=type_ir.name,
                                role="value",
                                identifier=enum_val.name,
                                langs=value_langs,
                            )
                        )


def _type_kind(*, type_ir: object) -> str:
    """Return the user-facing type-kind label for an IR type node."""
    if isinstance(type_ir, StructIR):
        return "struct"
    if isinstance(type_ir, FlagsIR):
        return "flags"
    if isinstance(type_ir, EnumIR):
        return "enum"
    if isinstance(type_ir, ScalarAliasIR):
        return "scalar alias"
    return "type"
