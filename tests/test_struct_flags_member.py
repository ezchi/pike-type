"""Integration and runtime tests for Struct with Flags member (Spec 007)."""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from piketype.dsl import Flags, Struct, Bit
from piketype.errors import ValidationError


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
FIXTURES_DIR = TESTS_DIR / "fixtures"


def gen_fixture(fixture_name: str, tmp_dir: Path) -> Path:
    """Run piketype gen on a fixture and return the repo dir."""
    fixture_root = FIXTURES_DIR / fixture_name / "project"
    repo_dir = tmp_dir / fixture_name
    shutil.copytree(fixture_root, repo_dir)
    cli_file = repo_dir / "alpha" / "piketype" / "types.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    subprocess.run(
        [sys.executable, "-m", "piketype.cli", "gen", str(cli_file)],
        cwd=repo_dir,
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )
    return repo_dir


# ---------------------------------------------------------------------------
# DSL-level tests
# ---------------------------------------------------------------------------


class StructFlagsMemberDSLTest(unittest.TestCase):
    """DSL acceptance tests for Flags as struct member."""

    def test_add_flags_member_accepted(self) -> None:
        """AC-1: Struct().add_member() accepts FlagsType."""
        flags_t = Flags().add_flag("a").add_flag("b")
        s = Struct().add_member("f", flags_t)
        self.assertEqual(len(s.members), 1)
        self.assertEqual(s.members[0].name, "f")

    def test_add_flags_and_scalar_member(self) -> None:
        """Struct can have both Flags and scalar members."""
        flags_t = Flags().add_flag("x")
        s = Struct().add_member("flags", flags_t).add_member("val", Bit(5))
        self.assertEqual(len(s.members), 2)

    def test_reject_invalid_type(self) -> None:
        """Non-DSL types are still rejected."""
        with self.assertRaises(ValidationError):
            Struct().add_member("bad", 42)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Golden file comparison tests
# ---------------------------------------------------------------------------


class StructFlagsMemberGoldenTest(unittest.TestCase):
    """Golden file comparison tests for struct_flags_member fixture."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def test_golden_match(self) -> None:
        """AC-20: Golden file integration tests pass."""
        repo_dir = gen_fixture("struct_flags_member", Path(self.tmp))
        gen_root = repo_dir / "gen"
        golden_root = TESTS_DIR / "goldens" / "gen" / "struct_flags_member"
        for golden_file in golden_root.rglob("*"):
            if golden_file.is_dir():
                continue
            relative = golden_file.relative_to(golden_root)
            generated = gen_root / relative
            self.assertTrue(generated.exists(), f"missing generated file: {relative}")
            expected = golden_file.read_text(encoding="utf-8")
            actual = generated.read_text(encoding="utf-8")
            self.assertEqual(expected, actual, f"mismatch in {relative}")

    def test_idempotent(self) -> None:
        """AC-21: piketype gen is idempotent."""
        repo_dir = gen_fixture("struct_flags_member", Path(self.tmp))
        gen_root = repo_dir / "gen"
        first_run: dict[str, str] = {}
        for f in gen_root.rglob("*"):
            if f.is_dir():
                continue
            first_run[str(f.relative_to(gen_root))] = f.read_text(encoding="utf-8")
        cli_file = repo_dir / "alpha" / "piketype" / "types.py"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        subprocess.run(
            [sys.executable, "-m", "piketype.cli", "gen", str(cli_file)],
            cwd=repo_dir,
            check=True,
            env=env,
            text=True,
            capture_output=True,
        )
        for rel, expected in first_run.items():
            actual = (gen_root / rel).read_text(encoding="utf-8")
            self.assertEqual(expected, actual, f"idempotency failed for {rel}")


# ---------------------------------------------------------------------------
# Python runtime tests
# ---------------------------------------------------------------------------


class StructFlagsMemberRuntimeTest(unittest.TestCase):
    """Python runtime tests for struct with Flags member."""

    _tmp_dir: tempfile.TemporaryDirectory[str]
    _gen_py: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp_dir = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp_dir.name)
        cls._gen_py = gen_fixture("struct_flags_member", tmp) / "gen" / "py"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp_dir.cleanup()

    def _import_types(self):
        for key in list(sys.modules.keys()):
            if key == "alpha" or key.startswith("alpha."):
                del sys.modules[key]
        sys.path[:] = [p for p in sys.path if "gen/py" not in str(p)]
        sys.path.insert(0, str(self._gen_py))
        return importlib.import_module("alpha.piketype.types_types")

    def test_round_trip_report(self) -> None:
        """AC-11, AC-12: to_bytes -> from_bytes round-trip for report_t."""
        mod = self._import_types()
        report = mod.report_ct()
        report.status.error = True
        report.status.ready = True
        report.code = 21
        raw = report.to_bytes()
        restored = mod.report_ct.from_bytes(raw)
        self.assertTrue(restored.status.error)
        self.assertFalse(restored.status.warning)
        self.assertTrue(restored.status.ready)
        self.assertEqual(restored.code, 21)

    def test_expected_bytes_report(self) -> None:
        """AC-19: to_bytes produces specific expected byte values."""
        mod = self._import_types()
        report = mod.report_ct()
        # status_t: 3 flags (error, warning, ready) -> 1 byte, MSB-packed
        # error=1, warning=0, ready=1 -> bits 7,6,5 = 1,0,1 -> 0xA0
        report.status.error = True
        report.status.ready = True
        # code = 21 (5 bits) -> 1 byte, padded: bits 4:0 = 10101 = 0x15
        # Unsigned 5-bit value 21 in 1 byte: pad=000, val=10101 -> 0x15
        report.code = 21
        raw = report.to_bytes()
        self.assertEqual(len(raw), 2)
        # First byte: status flags (error=1, warning=0, ready=1, pad=00000) = 0xA0
        self.assertEqual(raw[0], 0xA0)
        # Second byte: code=21 (5 bits) padded to byte = 0b000_10101 = 0x15
        self.assertEqual(raw[1], 0x15)

    def test_flags_field_not_nullable(self) -> None:
        """AC-10: Flags field coercer rejects None."""
        mod = self._import_types()
        report = mod.report_ct()
        with self.assertRaises(TypeError):
            report.status = None  # type: ignore[assignment]

    def test_flags_field_rejects_wrong_type(self) -> None:
        """AC-10: Flags field coercer rejects wrong type."""
        mod = self._import_types()
        report = mod.report_ct()
        with self.assertRaises(TypeError):
            report.status = 42  # type: ignore[assignment]

    def test_multiple_of_byte_count(self) -> None:
        """AC-25: multiple_of() struct has correct byte count."""
        mod = self._import_types()
        aligned = mod.aligned_report_ct()
        raw = aligned.to_bytes()
        # aligned_report_t: flags (1 byte) + data (1 byte) = 2 bytes natural
        # multiple_of(32) -> 4 bytes
        self.assertEqual(len(raw), 4)

    def test_multiple_of_round_trip(self) -> None:
        """Round-trip for multiple_of struct with Flags member."""
        mod = self._import_types()
        aligned = mod.aligned_report_ct()
        aligned.flags.error = True
        aligned.flags.warning = True
        aligned.data = 5
        raw = aligned.to_bytes()
        self.assertEqual(len(raw), 4)
        restored = mod.aligned_report_ct.from_bytes(raw)
        self.assertTrue(restored.flags.error)
        self.assertTrue(restored.flags.warning)
        self.assertFalse(restored.flags.ready)
        self.assertEqual(restored.data, 5)


if __name__ == "__main__":
    unittest.main()
