"""AC-19: Python runtime byte-value test for cross-module struct fields.

Imports the generated `bar_types` and `foo_types` modules from the
`cross_module_type_refs` golden tree, then asserts:
- Constructing `bar_t` with explicit cross-module field values produces
  the expected byte sequence.
- `bar_t.from_bytes(bytes)` round-trips back to the same object state.

This test guards against the "lockstep golden bug" where the generated
code and the golden could both be wrong in matching ways.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType

GOLDENS_DIR = Path(__file__).resolve().parent / "goldens" / "gen"
PY_GOLDEN_ROOT = GOLDENS_DIR / "cross_module_type_refs"


def _load_module_from_path(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CrossModuleRuntimeBytesTest(unittest.TestCase):
    """End-to-end runtime test for AC-19."""

    @classmethod
    def setUpClass(cls) -> None:
        # Clear any prior `alpha.*` modules left over from other tests' fixture
        # loads (each fixture has its own `alpha.piketype.*` namespace).
        for name in list(sys.modules):
            if name == "alpha" or name.startswith("alpha."):
                del sys.modules[name]
        # Add the generated py root to sys.path so `alpha.piketype.foo_types`
        # imports work via the absolute path that bar_types uses.
        cls._sys_path_entry = str(PY_GOLDEN_ROOT)
        if cls._sys_path_entry not in sys.path:
            sys.path.insert(0, cls._sys_path_entry)
        # Load via standard import so bar_types' `from alpha.piketype.foo_types`
        # resolves correctly.
        cls.foo_types = importlib.import_module("alpha.py.foo_types")
        cls.bar_types = importlib.import_module("alpha.py.bar_types")

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._sys_path_entry in sys.path:
            sys.path.remove(cls._sys_path_entry)
        for name in list(sys.modules):
            if name == "alpha" or name.startswith("alpha."):
                del sys.modules[name]

    def test_byte_t_round_trip(self) -> None:
        b = self.foo_types.byte_ct(0xAB)
        self.assertEqual(b.to_bytes(), b"\xab")
        round_tripped = self.foo_types.byte_ct.from_bytes(b"\xab")
        self.assertEqual(round_tripped.value, 0xAB)

    def test_bar_t_to_bytes_two_byte_fields(self) -> None:
        """Construct bar_t with two cross-module byte_ct fields; assert exact bytes for those fields.

        bar_t layout: field1 (byte 0) | field2 (byte 1) | hdr (2 bytes) | op (1 byte) | perm (1 byte).
        """
        bar = self.bar_types.bar_ct()
        bar.field1 = self.foo_types.byte_ct(0xAB)
        bar.field2 = self.foo_types.byte_ct(0xCD)
        raw = bar.to_bytes()
        self.assertEqual(len(raw), self.bar_types.bar_ct.BYTE_COUNT)
        # The first two bytes are the two cross-module byte_ct fields.
        self.assertEqual(raw[0], 0xAB)
        self.assertEqual(raw[1], 0xCD)

    def test_bar_t_round_trip_full(self) -> None:
        """Full round-trip: build bar_t, to_bytes, from_bytes, compare."""
        bar = self.bar_types.bar_ct()
        bar.field1 = self.foo_types.byte_ct(0xAB)
        bar.field2 = self.foo_types.byte_ct(0xCD)
        raw = bar.to_bytes()
        restored = self.bar_types.bar_ct.from_bytes(raw)
        self.assertEqual(restored.field1.value, 0xAB)
        self.assertEqual(restored.field2.value, 0xCD)


if __name__ == "__main__":
    unittest.main()
