"""Manifest writing helpers."""

from __future__ import annotations

import json
from pathlib import Path

from piketype.ir.nodes import EnumIR, FlagsIR, RepoIR, ScalarAliasIR, StructIR
from piketype.paths import (
    cpp_header_output_path,
    cpp_runtime_header_output_path,
    cpp_runtime_source_output_path,
    manifest_output_path,
    py_module_output_path,
    py_runtime_output_path,
    sv_module_output_path,
    sv_test_module_output_path,
    sv_runtime_output_path,
)


def _serialize_type_ir(*, type_ir: ScalarAliasIR | StructIR | FlagsIR | EnumIR, repo_root: Path) -> dict[str, object]:
    """Serialize one type IR node to a manifest dictionary."""
    source = {
        "path": str(Path(type_ir.source.path).resolve().relative_to(repo_root.resolve())),
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


def write_manifest(repo: RepoIR) -> Path:
    """Write the machine-readable manifest."""
    repo_root = Path(repo.repo_root)
    output_path = manifest_output_path(repo_root=repo_root)
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
                    "path": str(Path(module.source.path).resolve().relative_to(repo_root.resolve())),
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
                            "path": str(Path(const.source.path).resolve().relative_to(repo_root.resolve())),
                            "line": const.source.line,
                            "column": const.source.column,
                        },
                    }
                    for const in module.constants
                ],
                "types": [
                    _serialize_type_ir(type_ir=type_ir, repo_root=repo_root)
                    for type_ir in module.types
                ],
                "dependencies": [],
                "generated_outputs": {
                    "sv": str(
                        sv_module_output_path(
                            repo_root=repo_root,
                            module_path=repo_root / module.ref.repo_relative_path,
                        ).relative_to(repo_root)
                    ),
                    **(
                        {
                            "sv_test": str(
                                sv_test_module_output_path(
                                    repo_root=repo_root,
                                    module_path=repo_root / module.ref.repo_relative_path,
                                ).relative_to(repo_root)
                            )
                        }
                        if module.types
                        else {}
                    ),
                    "py": str(
                        py_module_output_path(
                            repo_root=repo_root,
                            module_path=repo_root / module.ref.repo_relative_path,
                        ).relative_to(repo_root)
                    ),
                    "cpp": str(
                        cpp_header_output_path(
                            repo_root=repo_root,
                            module_path=repo_root / module.ref.repo_relative_path,
                        ).relative_to(repo_root)
                    ),
                },
            }
            for module in repo.modules
        ],
        "runtime_outputs": {
            "sv": str(sv_runtime_output_path(repo_root=repo_root).relative_to(repo_root)),
            "py": str(py_runtime_output_path(repo_root=repo_root).relative_to(repo_root)),
            "cpp_header": str(cpp_runtime_header_output_path(repo_root=repo_root).relative_to(repo_root)),
            "cpp_source": str(cpp_runtime_source_output_path(repo_root=repo_root).relative_to(repo_root)),
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output_path
