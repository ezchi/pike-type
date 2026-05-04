"""Negative validation tests for VecConst (AC-4..AC-8)."""

from __future__ import annotations

import unittest

from piketype.dsl import Const, VecConst
from piketype.errors import ValidationError
from piketype.ir.nodes import (
    ConstIR,
    IntLiteralExprIR,
    ModuleIR,
    ModuleRefIR,
    RepoIR,
    SourceSpanIR,
    VecConstIR,
)
from piketype.validate.engine import validate_repo


_DUMMY_SOURCE = SourceSpanIR(path="<test>", line=1, column=None)


class VecConstValidationTests(unittest.TestCase):
    """Cover the eager-resolution validation rules for VecConst (post-016 follow-up
    moved validation from freeze-time to __init__-time)."""

    def test_overflow_8bit_300(self) -> None:
        """AC-4: value 300 in width 8 raises with FR-7 three-substring contract."""
        with self.assertRaises(ValidationError) as ctx:
            VecConst(8, 300, base="dec")
        message = str(ctx.exception)
        self.assertIn("300", message)
        self.assertIn("8", message)
        self.assertIn("2**8 - 1", message)

    def test_negative_value_rejected(self) -> None:
        """AC-5: negative resolved value raises ValidationError."""
        with self.assertRaises(ValidationError) as ctx:
            VecConst(8, -1, base="dec")
        message = str(ctx.exception)
        self.assertIn("-1", message)
        self.assertIn("negative", message.lower())

    def test_zero_or_negative_width_rejected(self) -> None:
        """AC-6: width=0 and width<0 raise ValidationError."""
        for bad_width in (0, -1, -64):
            with self.subTest(width=bad_width):
                with self.assertRaises(ValidationError):
                    VecConst(bad_width, 0, base="dec")

    def test_width_above_64_rejected(self) -> None:
        """AC-7: width=65 (above the 64-bit cap) raises ValidationError."""
        with self.assertRaises(ValidationError):
            VecConst(65, 0, base="hex")

    def test_default_base_is_dec(self) -> None:
        """Post-016 follow-up: omitting `base` defaults to 'dec'."""
        v = VecConst(5, 3)
        self.assertEqual(v.base, "dec")
        self.assertEqual(v.value, 3)
        self.assertEqual(v.width, 5)

    def test_vec_const_as_const_operand(self) -> None:
        """Post-016 follow-up: VecConst is a ConstOperand; arithmetic resolves eagerly."""
        F = VecConst(5, 3)
        G = VecConst(5, F * 4)
        self.assertEqual(G.value, 12)
        self.assertEqual(G.width, 5)

        # Const accepts VecConst too.
        K = Const(F * 5)
        self.assertEqual(K.value, 15)

    def test_unsupported_base_rejected(self) -> None:
        """AC-8: base='oct' raises at VecConst construction time."""
        with self.assertRaises(ValidationError) as ctx:
            VecConst(width=8, value=0, base="oct")
        message = str(ctx.exception)
        self.assertIn("oct", message)
        self.assertIn("base=", message)

    def test_positional_width_and_value_accepted(self) -> None:
        """FR-2 signature: width and value MUST be positional-or-keyword;
        only `base` is keyword-only."""
        v = VecConst(8, 15, base="dec")
        self.assertEqual(v.base, "dec")
        # base remains keyword-only.
        with self.assertRaises(TypeError):
            VecConst(8, 15, "dec")  # pyright: ignore[reportCallIssue]


class VecConstNameValidationTests(unittest.TestCase):
    """VecConst names participate in the same validation passes as Const names
    (gauge-T validation iter1 BLOCKING fix)."""

    def _make_repo_with_vec_const(self, name: str) -> "RepoIR":
        """Build a minimal RepoIR with a single module containing one VecConst."""

        module = ModuleIR(
            ref=ModuleRefIR(
                repo_relative_path="t/m.py",
                python_module_name="t.m",
                namespace_parts=("t", "m"),
                basename="m",
            ),
            source=_DUMMY_SOURCE,
            constants=(),
            types=(),
            dependencies=(),
            vec_constants=(
                VecConstIR(
                    name=name, source=_DUMMY_SOURCE, width=8, value=0, base="dec"
                ),
            ),
        )
        return RepoIR(repo_root=".", modules=(module,), tool_version=None)

    def test_vec_const_name_keyword_collision_rejected(self) -> None:
        """A VecConst named 'while' (Python/SV keyword) is rejected."""
        repo = self._make_repo_with_vec_const("while")
        with self.assertRaises(ValidationError) as ctx:
            validate_repo(repo)
        self.assertIn("while", str(ctx.exception))

    def test_vec_const_duplicate_with_const_rejected(self) -> None:
        """A VecConst with the same name as a Const in the same module is rejected."""
        module = ModuleIR(
            ref=ModuleRefIR(
                repo_relative_path="t/m.py",
                python_module_name="t.m",
                namespace_parts=("t", "m"),
                basename="m",
            ),
            source=_DUMMY_SOURCE,
            constants=(
                ConstIR(
                    name="X",
                    source=_DUMMY_SOURCE,
                    expr=IntLiteralExprIR(value=1, source=_DUMMY_SOURCE),
                    resolved_value=1,
                    resolved_signed=True,
                    resolved_width=32,
                ),
            ),
            types=(),
            dependencies=(),
            vec_constants=(
                VecConstIR(name="X", source=_DUMMY_SOURCE, width=8, value=0, base="dec"),
            ),
        )
        repo = RepoIR(repo_root=".", modules=(module,), tool_version=None)
        with self.assertRaises(ValidationError) as ctx:
            validate_repo(repo)
        self.assertIn("duplicate constant name X", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
