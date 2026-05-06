"""Manifest writing helpers."""

from __future__ import annotations

import json
from pathlib import Path

from piketype.config import Config
from piketype.ir.nodes import EnumIR, FlagsIR, ModuleIR, RepoIR, ScalarAliasIR, StructIR
from piketype.paths import backend_output_path, manifest_output_path


_MANIFEST_BACKENDS: tuple[tuple[str, str, str, str, bool], ...] = (
    # (manifest_key, backend_id, basename_suffix, ext, requires_types)
    ("sv", "sv", "_pkg", ".sv", False),
    ("sv_test", "sim", "_test_pkg", ".sv", True),
    ("py", "py", "_types", ".py", False),
    ("cpp", "cpp", "_types", ".hpp", False),
)


def _serialize_type_ir(*, type_ir: ScalarAliasIR | StructIR | FlagsIR | EnumIR, project_root: Path) -> dict[str, object]:
    """Serialize one type IR node to a manifest dictionary."""
    source = {
        "path": str(Path(type_ir.source.path).resolve().relative_to(project_root.resolve())),
        "line": type_ir.source.line,
        "column": type_ir.source.column,
    }
    if isinstance(type_ir, ScalarAliasIR):
        return {
            "name": type_ir.name,
            "kind": "scalar_alias",
            "state_kind": type_ir.state_kind,
            "signed": type_ir.signed,
            "resolved_width": type_ir.resolved_width,
            "source": source,
        }
    if isinstance(type_ir, StructIR):
        return {
            "name": type_ir.name,
            "kind": "struct",
            "field_count": len(type_ir.fields),
            "source": source,
        }
    if isinstance(type_ir, EnumIR):
        return {
            "name": type_ir.name,
            "kind": "enum",
            "resolved_width": type_ir.resolved_width,
            "value_count": len(type_ir.values),
            "values": [
                {"name": v.name, "resolved_value": v.resolved_value}
                for v in type_ir.values
            ],
            "source": source,
        }
    return {
        "name": type_ir.name,
        "kind": "flags",
        "flag_count": len(type_ir.fields),
        "flag_names": [flag.name for flag in type_ir.fields],
        "source": source,
    }


def _generated_outputs(*, module: ModuleIR, config: Config, project_root: Path) -> dict[str, str]:
    """Compute the generated_outputs dict for one module, restricted to enabled backends."""
    module_path = project_root / module.ref.repo_relative_path
    outputs: dict[str, str] = {}
    for manifest_key, backend_id, suffix, ext, requires_types in _MANIFEST_BACKENDS:
        backend = config.get_backend(backend_id)
        if backend is None:
            continue
        if requires_types and not module.types:
            continue
        path = backend_output_path(
            backend=backend,
            project_root=project_root,
            piketype_root=config.frontend.piketype_root,
            module_path=module_path,
            basename_suffix=suffix,
            ext=ext,
        )
        outputs[manifest_key] = str(path.relative_to(project_root))
    return outputs


def write_manifest(repo: RepoIR, *, config: Config) -> Path:
    """Write the machine-readable manifest."""
    project_root = config.project_root
    output_path = manifest_output_path(project_root=project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "repo_root": ".",
        "tool_version": repo.tool_version,
        "modules": [
            {
                "repo_relative_path": module.ref.repo_relative_path,
                "python_module_name": module.ref.python_module_name,
                "namespace_parts": list(module.ref.namespace_parts),
                "basename": module.ref.basename,
                "source": {
                    "path": str(Path(module.source.path).resolve().relative_to(project_root.resolve())),
                    "line": module.source.line,
                    "column": module.source.column,
                },
                "constants": [
                    {
                        "name": const.name,
                        "resolved_value": const.resolved_value,
                        "resolved_signed": const.resolved_signed,
                        "resolved_width": const.resolved_width,
                        "source": {
                            "path": str(Path(const.source.path).resolve().relative_to(project_root.resolve())),
                            "line": const.source.line,
                            "column": const.source.column,
                        },
                    }
                    for const in module.constants
                ],
                "types": [
                    _serialize_type_ir(type_ir=type_ir, project_root=project_root)
                    for type_ir in module.types
                ],
                "dependencies": [
                    {
                        "target_module": dep.target.python_module_name,
                        "kind": dep.kind,
                    }
                    for dep in module.dependencies
                ],
                "vec_constants": [
                    {
                        "name": v.name,
                        "width": v.width,
                        "value": v.value,
                        "base": v.base,
                        "source": {
                            "path": str(Path(v.source.path).resolve().relative_to(project_root.resolve())),
                            "line": v.source.line,
                            "column": v.source.column,
                        },
                    }
                    for v in module.vec_constants
                ],
                "generated_outputs": _generated_outputs(
                    module=module, config=config, project_root=project_root
                ),
            }
            for module in repo.modules
        ],
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path
