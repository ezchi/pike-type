"""Tests for piketype.yaml config loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from piketype.config import ConfigError, find_config, load_config
from piketype.errors import PikeTypeError


def _write(tmp: Path, text: str) -> Path:
    path = tmp / "piketype.yaml"
    path.write_text(text, encoding="utf-8")
    return path


class TestLoadConfig:
    def test_minimal_empty_yaml(self, tmp_path: Path) -> None:
        config = load_config(_write(tmp_path, ""))
        assert config.project_root == tmp_path.resolve()
        assert config.frontend.piketype_root == tmp_path.resolve()
        assert config.frontend.ir_cache == (tmp_path / ".piketype-cache").resolve()
        assert config.frontend.exclude_globs == ()
        assert config.backends == ()

    def test_full_config(self, tmp_path: Path) -> None:
        text = """
        frontend:
          piketype_root: services
          ir_cache: build/.piketype-cache
          exclude:
            - "**/_*.py"
        backends:
          py:
            backend_root: python_lib
          cpp:
            backend_root: includes
            language_id: cpp
          sv:
            language_id: rtl
        """
        config = load_config(_write(tmp_path, text))
        assert config.frontend.piketype_root == (tmp_path / "services").resolve()
        assert config.frontend.ir_cache == (tmp_path / "build/.piketype-cache").resolve()
        assert config.frontend.exclude_globs == ("**/_*.py",)

        py = config.get_backend("py")
        cpp = config.get_backend("cpp")
        sv = config.get_backend("sv")
        assert py is not None and py.backend_root == (tmp_path / "python_lib").resolve()
        assert py.language_id == ""
        assert cpp is not None and cpp.language_id == "cpp"
        assert cpp.backend_root == (tmp_path / "includes").resolve()
        # Empty / omitted backend_root defaults to project root.
        assert sv is not None and sv.backend_root == tmp_path.resolve()
        assert sv.language_id == "rtl"

    def test_absolute_paths_preserved(self, tmp_path: Path) -> None:
        abs_root = tmp_path / "abs_out"
        text = f"""
        backends:
          py:
            backend_root: {abs_root}
        """
        config = load_config(_write(tmp_path, text))
        py = config.get_backend("py")
        assert py is not None
        assert py.backend_root == abs_root.resolve()

    def test_backend_root_defaults_to_project_root(self, tmp_path: Path) -> None:
        text = """
        backends:
          sv:
            language_id: rtl
        """
        config = load_config(_write(tmp_path, text))
        sv = config.get_backend("sv")
        assert sv is not None
        assert sv.backend_root == tmp_path.resolve()
        assert sv.language_id == "rtl"

    def test_language_id_defaults_to_empty(self, tmp_path: Path) -> None:
        text = """
        backends:
          py:
            backend_root: python_lib
        """
        config = load_config(_write(tmp_path, text))
        py = config.get_backend("py")
        assert py is not None
        assert py.language_id == ""

    def test_get_backend_missing(self, tmp_path: Path) -> None:
        config = load_config(_write(tmp_path, ""))
        assert config.get_backend("py") is None

    def test_unknown_top_level_key_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigError, match="unknown key"):
            load_config(_write(tmp_path, "fronted: {}\n"))

    def test_unknown_frontend_key_rejected(self, tmp_path: Path) -> None:
        text = """
        frontend:
          piketyperoot: services
        """
        with pytest.raises(ConfigError, match="unknown key"):
            load_config(_write(tmp_path, text))

    def test_unknown_backend_key_rejected(self, tmp_path: Path) -> None:
        text = """
        backends:
          py:
            backend_root: x
            languageid: rtl
        """
        with pytest.raises(ConfigError, match="unknown key"):
            load_config(_write(tmp_path, text))

    def test_legacy_out_key_rejected(self, tmp_path: Path) -> None:
        text = """
        backends:
          py:
            out: python_lib
        """
        with pytest.raises(ConfigError, match="unknown key"):
            load_config(_write(tmp_path, text))

    def test_backend_language_id_must_be_string(self, tmp_path: Path) -> None:
        text = """
        backends:
          py:
            backend_root: x
            language_id: true
        """
        with pytest.raises(ConfigError, match="must be a string"):
            load_config(_write(tmp_path, text))

    def test_backend_language_id_rejects_path_separators(self, tmp_path: Path) -> None:
        text = """
        backends:
          py:
            language_id: "py/extra"
        """
        with pytest.raises(ConfigError, match="single path segment"):
            load_config(_write(tmp_path, text))

    def test_invalid_yaml(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigError, match="invalid YAML"):
            load_config(_write(tmp_path, "frontend: : :\n"))

    def test_top_level_not_mapping(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigError, match="must be a mapping"):
            load_config(_write(tmp_path, "- a\n- b\n"))

    def test_exclude_must_be_list(self, tmp_path: Path) -> None:
        text = """
        frontend:
          exclude: "**/_*.py"
        """
        with pytest.raises(ConfigError, match="must be a list"):
            load_config(_write(tmp_path, text))

    def test_paths_resolved_to_absolute(self, tmp_path: Path) -> None:
        config = load_config(_write(tmp_path, "frontend:\n  piketype_root: ./svc\n"))
        assert config.frontend.piketype_root.is_absolute()

    def test_config_is_frozen(self, tmp_path: Path) -> None:
        config = load_config(_write(tmp_path, ""))
        with pytest.raises(AttributeError):
            config.project_root = Path("/")  # type: ignore[misc]


class TestFindConfig:
    def test_explicit_path_wins(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "")
        assert find_config(explicit=path) == path.resolve()

    def test_explicit_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(PikeTypeError, match="config not found"):
            find_config(explicit=tmp_path / "nope.yaml")

    def test_upward_walk_finds_in_start_dir(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "")
        assert find_config(start=tmp_path) == path.resolve()

    def test_upward_walk_finds_in_ancestor(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "")
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        assert find_config(start=nested) == path.resolve()

    def test_upward_walk_no_match_raises(self, tmp_path: Path) -> None:
        with pytest.raises(PikeTypeError, match="could not find piketype.yaml"):
            find_config(start=tmp_path)
