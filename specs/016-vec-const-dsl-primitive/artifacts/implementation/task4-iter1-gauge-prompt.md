# Gauge Code Review — Task 4, Iteration 1

You are the **Gauge**.

## Task
Per Plan T4: validation negative tests for VecConst (AC-4..AC-8). Use `unittest.TestCase`, `tempfile.TemporaryDirectory()` if needed, no pytest fixtures, no parametrize.

## Code under review

```python
"""Negative validation tests for VecConst (AC-4..AC-8)."""

from __future__ import annotations

import unittest

from piketype.dsl import VecConst
from piketype.dsl.freeze import _freeze_vec_const_storage
from piketype.errors import ValidationError
from piketype.ir.nodes import SourceSpanIR


_DUMMY_SOURCE = SourceSpanIR(path="<test>", line=1, column=None)


class VecConstValidationTests(unittest.TestCase):
    def test_overflow_8bit_300(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            _freeze_vec_const_storage(width=8, value=300, base="dec", source=_DUMMY_SOURCE, name="X")
        message = str(ctx.exception)
        self.assertIn("300", message)
        self.assertIn("8", message)
        self.assertIn("2**8 - 1", message)

    def test_negative_value_rejected(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            _freeze_vec_const_storage(width=8, value=-1, base="dec", source=_DUMMY_SOURCE, name="X")
        message = str(ctx.exception)
        self.assertIn("-1", message)
        self.assertIn("negative", message.lower())

    def test_zero_or_negative_width_rejected(self) -> None:
        for bad_width in (0, -1, -64):
            with self.subTest(width=bad_width):
                with self.assertRaises(ValidationError):
                    _freeze_vec_const_storage(width=bad_width, value=0, base="dec", source=_DUMMY_SOURCE, name="X")

    def test_width_above_64_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            _freeze_vec_const_storage(width=65, value=0, base="hex", source=_DUMMY_SOURCE, name="X")

    def test_unsupported_base_rejected(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            VecConst(width=8, value=0, base="oct")
        message = str(ctx.exception)
        self.assertIn("oct", message)
        self.assertIn("base=", message)
```

## Verification
- All 5 tests pass.

## Review
1. Each AC mapped to a test? (AC-4 / AC-5 / AC-6 / AC-7 / AC-8 — confirmed.)
2. AC-4 checks the FR-7 three-substring contract correctly?
3. `subTest` is acceptable per Constitution §Testing? (Yes — it's plain unittest, not parametrize.)
4. Test isolation: each test constructs its own offending input; no shared state.

## Output
### Issues
**BLOCKING / WARNING / NOTE**, terse.

### Verdict
End with **EXACTLY** `VERDICT: APPROVE` or `VERDICT: REVISE`.
