"""AC-23: forbid Python-side construction of generated import/include/from-import lines.

This static AST check enforces FR-13 / NFR-7: all `import`, `#include`, and
`from ... import` lines in generated outputs (SV/C++/Python) must come from
Jinja templates with view-model data — never from Python string construction
in backend `view.py` or `emitter.py`.

Detection covers six AST shapes:
- `Constant(value=str)` whose value matches a generated-output prefix.
- `JoinedStr` (f-string) whose static prefix matches.
- `BinOp(Add)` chains whose leaf constants concatenate to a matching prefix.
- `Call(Attribute(attr='format'|'format_map'))` on a matching Constant receiver.
- `Call(Attribute(attr='join'))` whose first List/Tuple argument's static
  skeleton starts with a matching prefix.
- `BinOp(Mod)` with a matching Constant left operand.

After Commit D's template-first refactor, the allowlist is empty.
"""

from __future__ import annotations

import ast
import pytest
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSPECTED_FILES = (
    PROJECT_ROOT / "src" / "piketype" / "backends" / "sv" / "view.py",
    PROJECT_ROOT / "src" / "piketype" / "backends" / "sv" / "emitter.py",
    PROJECT_ROOT / "src" / "piketype" / "backends" / "py" / "view.py",
    PROJECT_ROOT / "src" / "piketype" / "backends" / "py" / "emitter.py",
    PROJECT_ROOT / "src" / "piketype" / "backends" / "cpp" / "view.py",
    PROJECT_ROOT / "src" / "piketype" / "backends" / "cpp" / "emitter.py",
)

# (file_path, line_number) entries permitted to construct an import-style line in Python.
# Empty after Commit D's template-first refactor.
ALLOWLIST: frozenset[tuple[str, int]] = frozenset()

# Strict regex: matches a fully-formed generated-output line (used for Constant strings).
_STRICT_RE = re.compile(
    r"^\s*("
    r"import\s+\w+_(?:pkg|test_pkg)"  # SV `import foo_pkg::*;` etc.
    r"|#include\s+\""                 # C++ `#include "..."`
    r"|from\s+\S+_types\s+import\b"   # Python `from foo_types import bar_ct`
    r")"
)

# Relaxed regex: matches a static prefix where the dynamic part fills the rest
# (used for JoinedStr static prefix, BinOp/format/join skeletons).
_RELAXED_RE = re.compile(r"^\s*(import\s|#include\s|from\s)")


def _looks_strict(s: str) -> bool:
    return _STRICT_RE.match(s) is not None


def _looks_relaxed(s: str) -> bool:
    return _RELAXED_RE.match(s) is not None


def _flatten_binop_add(node: ast.AST) -> list[ast.AST]:
    """Flatten `a + b + c` into a list of leaves."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _flatten_binop_add(node.left) + _flatten_binop_add(node.right)
    return [node]


def _joined_str_static_prefix(node: ast.JoinedStr) -> str:
    """Return the static (non-formatted) leading text of an f-string."""
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        else:
            break
    return "".join(parts)


def _join_skeleton(call: ast.Call) -> str | None:
    """Reduce `sep.join(args)` to a static skeleton, or None if not statically reducible.

    Each arg becomes its constant value, or "<DYN>" if not a Constant string.
    The skeleton is the elements joined with the separator (or "<DYN>" if the
    separator is also dynamic).
    """
    if not (isinstance(call.func, ast.Attribute) and call.func.attr == "join"):
        return None
    if not call.args:
        return None
    arg = call.args[0]
    if not isinstance(arg, (ast.List, ast.Tuple)):
        return None
    elements: list[str] = []
    for el in arg.elts:
        if isinstance(el, ast.Constant) and isinstance(el.value, str):
            elements.append(el.value)
        else:
            elements.append("<DYN>")
    sep_node = call.func.value
    if isinstance(sep_node, ast.Constant) and isinstance(sep_node.value, str):
        sep = sep_node.value
    else:
        sep = "<DYN>"
    return sep.join(elements)


class _Visitor(ast.NodeVisitor):
    def __init__(self, *, file_path: Path) -> None:
        self.file_path = file_path
        self.violations: list[tuple[Path, int, str, str]] = []  # (path, line, kind, snippet)

    def _record(self, *, node: ast.AST, kind: str, snippet: str) -> None:
        line = getattr(node, "lineno", 0)
        if (str(self.file_path), line) in ALLOWLIST:
            return
        self.violations.append((self.file_path, line, kind, snippet))

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and _looks_strict(node.value):
            self._record(node=node, kind="Constant", snippet=node.value[:60])
        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        prefix = _joined_str_static_prefix(node)
        if _looks_relaxed(prefix):
            self._record(node=node, kind="JoinedStr", snippet=prefix[:60])
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if isinstance(node.op, ast.Add):
            leaves = _flatten_binop_add(node)
            skeleton_parts: list[str] = []
            for leaf in leaves:
                if isinstance(leaf, ast.Constant) and isinstance(leaf.value, str):
                    skeleton_parts.append(leaf.value)
                else:
                    skeleton_parts.append("<DYN>")
            skeleton = "".join(skeleton_parts)
            if _looks_relaxed(skeleton):
                self._record(node=node, kind="BinOp(Add)", snippet=skeleton[:60])
        elif isinstance(node.op, ast.Mod):
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                if _looks_relaxed(node.left.value):
                    self._record(node=node, kind="BinOp(Mod)", snippet=node.left.value[:60])
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            recv = node.func.value
            if attr in ("format", "format_map"):
                if isinstance(recv, ast.Constant) and isinstance(recv.value, str):
                    if _looks_relaxed(recv.value):
                        self._record(node=node, kind=f"Call({attr})", snippet=recv.value[:60])
            elif attr == "join":
                skeleton = _join_skeleton(node)
                if skeleton is not None and _looks_relaxed(skeleton):
                    self._record(node=node, kind="Call(join)", snippet=skeleton[:60])
        self.generic_visit(node)


def _scan(file_path: Path) -> list[tuple[Path, int, str, str]]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    visitor = _Visitor(file_path=file_path)
    visitor.visit(tree)
    return visitor.violations


class NoInlineImportsTests:
    """AC-23 enforcement: backend Python must not construct generated import lines."""

    def test_backend_files_have_no_inline_import_construction(self) -> None:
        all_violations: list[tuple[Path, int, str, str]] = []
        for path in INSPECTED_FILES:
            assert path.exists(), f"inspected file does not exist: {path}"
            all_violations.extend(_scan(path))
        if all_violations:
            lines = [
                f"  {path.name}:{lineno} [{kind}] {snippet!r}"
                for path, lineno, kind, snippet in all_violations
            ]
            pytest.fail(
                "found Python-side construction of generated import/include/from-import lines:\n"
                + "\n".join(lines)
            )


class StaticCheckRuleTests:
    """Unit tests for the AC-23 detection rules — both negative (must flag) and positive (must NOT flag)."""

    def _scan_source(self, src: str) -> list[tuple[str, str]]:
        # Returns (kind, snippet) tuples.
        tree = ast.parse(src)
        v = _Visitor(file_path=Path("<test>"))
        v.visit(tree)
        return [(kind, snippet) for _, _, kind, snippet in v.violations]

    # ---- Negative cases (MUST flag) ----

    def test_flags_constant_import_pkg(self) -> None:
        v = self._scan_source('x = "import foo_pkg::*;"')
        assert any(k == "Constant" for k, _ in v), v

    def test_flags_constant_include_quote(self) -> None:
        v = self._scan_source('x = \'#include "alpha/foo.hpp"\'')
        assert any(k == "Constant" for k, _ in v), v

    def test_flags_joined_str_import_pkg(self) -> None:
        v = self._scan_source('x = f"import {target}_pkg::*;"')
        assert any(k == "JoinedStr" for k, _ in v), v

    def test_flags_joined_str_from_types(self) -> None:
        v = self._scan_source('x = f"from {m}_types import {c}"')
        assert any(k == "JoinedStr" for k, _ in v), v

    def test_flags_binop_add_concat(self) -> None:
        v = self._scan_source('x = "import " + target + "_pkg::*;"')
        assert any(k == "BinOp(Add)" for k, _ in v), v

    def test_flags_binop_mod_format(self) -> None:
        v = self._scan_source('x = "import %s_pkg::*;" % target')
        assert any(k == "BinOp(Mod)" for k, _ in v), v

    def test_flags_format_method(self) -> None:
        v = self._scan_source('x = "import {}_pkg::*;".format(target)')
        assert any(k == "Call(format)" for k, _ in v), v

    def test_flags_join_skeleton(self) -> None:
        v = self._scan_source('x = " ".join(["import", basename, "_pkg::*"])')
        assert any(k == "Call(join)" for k, _ in v), v

    # ---- Positive cases (MUST NOT flag) ----

    def test_does_not_flag_join_underscore(self) -> None:
        v = self._scan_source('x = "_".join(parts)')
        assert not v, v

    def test_does_not_flag_format_define(self) -> None:
        v = self._scan_source('x = "#define {} {}".format(name, value)')
        assert not v, v

    def test_does_not_flag_arithmetic_mod(self) -> None:
        v = self._scan_source('x = (w + 7) % 8')
        assert not v, v

    def test_does_not_flag_unrelated_constants(self) -> None:
        v = self._scan_source('x = "alignment_bits"; y = "scalar_alias"')
        assert not v, v

    def test_does_not_flag_namespace_join(self) -> None:
        v = self._scan_source('x = "::".join(namespace_parts)')
        assert not v, v
