"""Negative validation tests for VecConst (AC-4..AC-8)."""

from __future__ import annotations

import unittest

from piketype.dsl import VecConst
from piketype.dsl.freeze import _freeze_vec_const_storage
from piketype.errors import ValidationError
from piketype.ir.nodes import SourceSpanIR


_DUMMY_SOURCE = SourceSpanIR(path="<test>", line=1, column=None)


class VecConstValidationTests(unittest.TestCase):
    """Cover the storage-level validation rules for VecConst."""

    def test_overflow_8bit_300(self) -> None:
        """AC-4: value 300 in width 8 raises with FR-7 three-substring contract."""
        with self.assertRaises(ValidationError) as ctx:
            _freeze_vec_const_storage(
                width=8, value=300, base="dec", source=_DUMMY_SOURCE, name="X"
            )
        message = str(ctx.exception)
        self.assertIn("300", message)
        self.assertIn("8", message)
        self.assertIn("2**8 - 1", message)

    def test_negative_value_rejected(self) -> None:
        """AC-5: negative resolved value raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            _freeze_vec_const_storage(
                width=8, value=-1, base="dec", source=_DUMMY_SOURCE, name="X"
            )
        message = str(ctx.exception)
        self.assertIn("-1", message)
        self.assertIn("negative", message.lower())

    def test_zero_or_negative_width_rejected(self) -> None:
        """AC-6: width=0 and width<0 raise ValidationError."""
        for bad_width in (0, -1, -64):
            with self.subTest(width=bad_width):
                with self.assertRaises(ValidationError):
                    _freeze_vec_const_storage(
                        width=bad_width, value=0, base="dec", source=_DUMMY_SOURCE, name="X"
                    )

    def test_width_above_64_rejected(self) -> None:
        """AC-7: width=65 (above the 64-bit cap) raises ValidationError."""
        with self.assertRaises(ValidationError):
            _freeze_vec_const_storage(
                width=65, value=0, base="hex", source=_DUMMY_SOURCE, name="X"
            )

    def test_unsupported_base_rejected(self) -> None:
        """AC-8: base='oct' raises at VecConst construction time."""
        with self.assertRaises(ValidationError) as ctx:
            VecConst(width=8, value=0, base="oct")
        message = str(ctx.exception)
        self.assertIn("oct", message)
        self.assertIn("base=", message)


if __name__ == "__main__":
    unittest.main()
