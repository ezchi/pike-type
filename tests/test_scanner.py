"""Tests for piketype.discovery.scanner.find_piketype_modules."""

from __future__ import annotations

import tempfile
from pathlib import Path

from piketype.discovery.scanner import find_piketype_modules


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


class FindPiketypeModulesTests:
    """Cover the discovery scanner's exclusion behavior."""

    def test_excludes_venv_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Strict layout: DSL must be exactly <prefix>/piketype/<name>.py.
            real = root / "src" / "piketype" / "foo.py"
            venv_dup = (
                root
                / ".venv"
                / "lib"
                / "python3.13"
                / "site-packages"
                / "piketype"
                / "foo.py"
            )
            _touch(real)
            _touch(venv_dup)

            assert find_piketype_modules(root) == [real]

    def test_all_six_excluded_names_rejected(self) -> None:
        excluded_names = (".venv", "venv", ".git", "node_modules", ".tox", "__pycache__")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in excluded_names:
                _touch(root / name / "piketype" / "foo.py")

            assert find_piketype_modules(root) == []

    def test_clean_repo_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src" / "piketype" / "foo.py"
            _touch(target)

            assert find_piketype_modules(root) == [target]

    def test_sorted_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zzz = root / "src" / "piketype" / "zzz.py"
            aaa = root / "src" / "piketype" / "aaa.py"
            _touch(zzz)
            _touch(aaa)

            result = find_piketype_modules(root)
            assert result == sorted(result)
            assert result == [aaa, zzz]
