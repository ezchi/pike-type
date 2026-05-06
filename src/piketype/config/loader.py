"""Parse and validate piketype.yaml into a frozen Config.

Loading rules:

* The directory containing the YAML is the project root.
* Relative paths in the YAML are anchored at the project root.
* Absolute paths are used as-is (after ``expanduser``).
* Defaults: ``frontend.piketype_root`` = project root,
  ``frontend.ir_cache`` = ``<project_root>/.piketype-cache``.
* Backend ``out`` is required. Backend ``language_id`` defaults to ``False``.
* Unknown keys raise ``ConfigError`` so typos surface immediately.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from piketype.config.schema import BackendConfig, Config, FrontendConfig
from piketype.errors import PikeTypeError


class ConfigError(PikeTypeError):
    """Raised when piketype.yaml fails to parse or validate."""


_TOP_LEVEL_KEYS = frozenset({"frontend", "backends"})
_FRONTEND_KEYS = frozenset({"piketype_root", "ir_cache", "exclude"})
_BACKEND_KEYS = frozenset({"out", "out_layout", "language_id"})
_VALID_LAYOUTS = frozenset({"prefix", "suffix"})

# HDL roles place the role directory next to the source (`<sub>/<role>/`);
# language packages place a single output root above the source tree
# (`<root>/<sub>/`). Backends not listed here default to ``prefix``.
_DEFAULT_OUT_LAYOUTS: dict[str, str] = {
    "sv": "suffix",
    "sim": "suffix",
    "py": "prefix",
    "cpp": "prefix",
}


def load_config(config_path: Path) -> Config:
    """Load and validate the YAML at ``config_path`` into a ``Config``."""
    config_path = config_path.resolve()
    project_root = config_path.parent

    raw = _read_yaml(config_path)
    _check_unknown_keys(raw, _TOP_LEVEL_KEYS, where="<root>", config_path=config_path)

    frontend = _parse_frontend(raw.get("frontend"), project_root, config_path)
    backends = _parse_backends(raw.get("backends"), project_root, config_path)

    return Config(
        project_root=project_root,
        config_path=config_path,
        frontend=frontend,
        backends=backends,
    )


def _read_yaml(config_path: Path) -> dict[str, Any]:
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"could not read config: {config_path}: {exc}") from exc

    try:
        loaded: object = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"{config_path}: invalid YAML: {exc}") from exc

    if loaded is None:
        return {}
    return _as_mapping(loaded, where="<root>", config_path=config_path)


def _parse_frontend(raw: object, project_root: Path, config_path: Path) -> FrontendConfig:
    if raw is None:
        return FrontendConfig(
            piketype_root=project_root,
            ir_cache=(project_root / ".piketype-cache").resolve(),
        )
    body = _as_mapping(raw, where="frontend", config_path=config_path)
    _check_unknown_keys(body, _FRONTEND_KEYS, where="frontend", config_path=config_path)

    piketype_root_raw = body.get("piketype_root")
    piketype_root = (
        _resolve_path(piketype_root_raw, project_root, "frontend.piketype_root", config_path)
        if piketype_root_raw is not None
        else project_root
    )

    ir_cache_raw = body.get("ir_cache")
    ir_cache = (
        _resolve_path(ir_cache_raw, project_root, "frontend.ir_cache", config_path)
        if ir_cache_raw is not None
        else (project_root / ".piketype-cache").resolve()
    )

    exclude_globs: tuple[str, ...] = ()
    exclude_raw = body.get("exclude")
    if exclude_raw is not None:
        exclude_globs = tuple(
            _require_str(item, "frontend.exclude[]", config_path)
            for item in _as_list(exclude_raw, where="frontend.exclude", config_path=config_path)
        )

    return FrontendConfig(
        piketype_root=piketype_root,
        ir_cache=ir_cache,
        exclude_globs=exclude_globs,
    )


def _parse_backends(raw: object, project_root: Path, config_path: Path) -> tuple[BackendConfig, ...]:
    if raw is None:
        return ()
    body = _as_mapping(raw, where="backends", config_path=config_path)

    backends: list[BackendConfig] = []
    for name_raw, body_raw in body.items():
        if not name_raw:
            raise ConfigError(f"{config_path}: backend names must be non-empty strings")
        backend_body = _as_mapping(body_raw, where=f"backends.{name_raw}", config_path=config_path)
        _check_unknown_keys(backend_body, _BACKEND_KEYS, where=f"backends.{name_raw}", config_path=config_path)

        if "out" not in backend_body:
            raise ConfigError(f"{config_path}: 'backends.{name_raw}.out' is required")
        out = _resolve_path(backend_body["out"], project_root, f"backends.{name_raw}.out", config_path)

        layout_default = _DEFAULT_OUT_LAYOUTS.get(name_raw, "prefix")
        layout_raw = backend_body.get("out_layout", layout_default)
        if not isinstance(layout_raw, str) or layout_raw not in _VALID_LAYOUTS:
            raise ConfigError(
                f"{config_path}: 'backends.{name_raw}.out_layout' must be one of "
                f"{sorted(_VALID_LAYOUTS)}, got {layout_raw!r}"
            )

        language_id_raw = backend_body.get("language_id", False)
        if not isinstance(language_id_raw, bool):
            raise ConfigError(f"{config_path}: 'backends.{name_raw}.language_id' must be bool")

        backends.append(
            BackendConfig(name=name_raw, out=out, out_layout=layout_raw, language_id=language_id_raw)
        )

    return tuple(backends)


def _as_mapping(value: object, *, where: str, config_path: Path) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{config_path}: '{where}' must be a mapping")
    typed: dict[str, Any] = {}
    for k, v in value.items():  # pyright: ignore[reportUnknownVariableType]
        typed[str(k)] = v  # pyright: ignore[reportUnknownArgumentType]
    return typed


def _as_list(value: object, *, where: str, config_path: Path) -> list[Any]:
    if not isinstance(value, list):
        raise ConfigError(f"{config_path}: '{where}' must be a list of glob strings")
    typed: list[Any] = []
    for item in value:  # pyright: ignore[reportUnknownVariableType]
        typed.append(item)  # pyright: ignore[reportUnknownArgumentType]
    return typed


def _resolve_path(value: object, project_root: Path, key: str, config_path: Path) -> Path:
    s = _require_str(value, key, config_path)
    p = Path(s).expanduser()
    if not p.is_absolute():
        p = project_root / p
    return p.resolve()


def _require_str(value: object, key: str, config_path: Path) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{config_path}: '{key}' must be a string, got {type(value).__name__}")
    return value


def _check_unknown_keys(
    body: dict[str, Any], allowed: frozenset[str], *, where: str, config_path: Path
) -> None:
    unknown = set(body.keys()) - allowed
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ConfigError(f"{config_path}: unknown key(s) under '{where}': {names}")
