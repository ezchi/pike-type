"""Tests for tools/check_templates.py."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Make tools/ importable.
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "tools"))

from check_templates import check_paths  # noqa: E402


def _write_template(directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


class JinjaBlockPatternTests:
    """Each forbidden pattern in a Jinja block must produce at least one violation."""

    def _scan(self, body: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _write_template(tmp_path, "t.j2", body)
            return [v.pattern_id for v in check_paths([tmp_path])]

    def test_p1_bit_shift_mask(self) -> None:
        assert "P1" in self._scan("{{ (1 << 32) - 1 }}\n")

    def test_p2_byte_count_arithmetic_left(self) -> None:
        assert "P2" in self._scan("{{ byte_count * 8 }}\n")

    def test_p2_byte_count_arithmetic_right(self) -> None:
        assert "P2" in self._scan("{{ 2 * byte_count }}\n")

    def test_p3_runtime_type_interrogation(self) -> None:
        assert "P3" in self._scan("{% if isinstance(x, int) %}{% endif %}\n")

    def test_p4_type_lookup(self) -> None:
        assert "P4" in self._scan("{{ x.__class__ }}\n")

    def test_p5_explicit_byte_arithmetic(self) -> None:
        assert "P5" in self._scan("{{ width // 8 }}\n")

    def test_p6_filesystem_access(self) -> None:
        assert "P6" in self._scan("{{ open('foo') }}\n")

    def test_p7_non_determinism(self) -> None:
        assert "P7" in self._scan("{{ random.randrange(10) }}\n")


class RawBodyPatternTests:
    """Pattern 8 scans the raw template body."""

    def test_p8_python_extension(self) -> None:
        body = "{% python %}\nfoo = 1\n{% endpython %}\n"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _write_template(tmp_path, "t.j2", body)
            patterns = [v.pattern_id for v in check_paths([tmp_path])]
        assert "P8" in patterns


class NegativeCasesTests:
    """Target-language text outside Jinja blocks must not be flagged."""

    def test_systemverilog_width_arithmetic_outside_blocks(self) -> None:
        # Raw SV bit-slice and shift in target output is fine.
        body = "logic [WIDTH-1:0] padded;\nassign mask = (1 << WIDTH) - 1;\n"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _write_template(tmp_path, "t.j2", body)
            assert [] == check_paths([tmp_path])

    def test_cpp_byte_count_arithmetic_outside_blocks(self) -> None:
        body = "for (std::size_t i = 0; i < BYTE_COUNT * 8U; ++i) {}\n"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _write_template(tmp_path, "t.j2", body)
            assert [] == check_paths([tmp_path])

    def test_python_field_access_in_jinja_block(self) -> None:
        # Plain field access in Jinja is allowed; only the seven
        # forbidden patterns inside blocks should flag.
        body = "{{ field.byte_count }} {{ field.name }}\n"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _write_template(tmp_path, "t.j2", body)
            assert [] == check_paths([tmp_path])

    def test_empty_directory_no_violations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            assert [] == check_paths([tmp_path])


class CliTests:
    """End-to-end exit-code behaviour."""

    def test_main_exits_zero_when_no_templates(self) -> None:
        from check_templates import main

        with tempfile.TemporaryDirectory() as tmp:
            assert 0 == main([tmp])

    def test_main_exits_one_on_violation(self) -> None:
        from check_templates import main

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _write_template(tmp_path, "bad.j2", "{{ (1 << 32) }}\n")
            assert 1 == main([str(tmp_path)])
