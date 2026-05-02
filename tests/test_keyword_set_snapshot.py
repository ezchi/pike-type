"""Snapshot canary for the Python keyword sets in `piketype.validate.keywords`.

The keyword module captures CPython 3.12.x ``keyword.kwlist`` and
``keyword.softkwlist`` as literal frozensets to keep error output
byte-identical across Python patch upgrades. This test verifies the
snapshots match the live ``keyword`` module under a CPython 3.12.x
interpreter. On other Python minor versions the test skips with an
explanatory message — drift is then expected and is governed by a
separate Python-version-bump PR.
"""

from __future__ import annotations

import keyword
import sys
import unittest

from piketype.validate.keywords import PY_HARD_KEYWORDS, PY_SOFT_KEYWORDS


_PY_312_REASON = (
    "Python keyword snapshot is pinned to CPython 3.12.x; "
    f"running on {sys.version_info.major}.{sys.version_info.minor} — drift expected."
)


@unittest.skipUnless(sys.version_info[:2] == (3, 12), _PY_312_REASON)
class PythonKeywordSnapshotTests(unittest.TestCase):
    """NFR-3: Python keyword snapshot vs. live ``keyword`` module."""

    def test_hard_keyword_snapshot_matches_keyword_kwlist(self) -> None:
        self.assertEqual(PY_HARD_KEYWORDS, frozenset(keyword.kwlist))

    def test_soft_keyword_snapshot_matches_keyword_softkwlist(self) -> None:
        self.assertEqual(PY_SOFT_KEYWORDS, frozenset(keyword.softkwlist))


if __name__ == "__main__":
    unittest.main()
