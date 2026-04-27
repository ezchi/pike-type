"""Unit tests for C++ namespace validation."""

from __future__ import annotations

import unittest
from pathlib import Path

from typist.errors import ValidationError
from typist.validate.namespace import (
    CPP17_KEYWORDS,
    check_duplicate_basenames,
    validate_cpp_namespace,
)


class ValidateCppNamespaceTest(unittest.TestCase):
    """Tests for validate_cpp_namespace()."""

    # -- Positive cases --

    def test_single_segment(self) -> None:
        self.assertEqual(validate_cpp_namespace("foo"), ("foo",))

    def test_two_segments(self) -> None:
        self.assertEqual(validate_cpp_namespace("foo::bar"), ("foo", "bar"))

    def test_three_segments(self) -> None:
        self.assertEqual(validate_cpp_namespace("a::b::c"), ("a", "b", "c"))

    def test_segment_with_digits(self) -> None:
        self.assertEqual(validate_cpp_namespace("foo2::bar3"), ("foo2", "bar3"))

    # -- Empty / missing segments --

    def test_rejects_empty_string(self) -> None:
        with self.assertRaises(ValidationError):
            validate_cpp_namespace("")

    def test_rejects_double_colon_prefix(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("::foo")
        self.assertIn("empty segment", str(ctx.exception))

    def test_rejects_double_colon_suffix(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("foo::")
        self.assertIn("empty segment", str(ctx.exception))

    def test_rejects_quadruple_colon(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("foo::::bar")
        self.assertIn("empty segment", str(ctx.exception))

    # -- Invalid identifier syntax --

    def test_rejects_leading_digit(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("123bad")
        self.assertIn("not a valid C++ identifier", str(ctx.exception))

    def test_rejects_hyphen(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("foo-bar")
        self.assertIn("not a valid C++ identifier", str(ctx.exception))

    # -- C++ keywords --

    def test_rejects_class_keyword(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("class")
        self.assertIn("C++ keyword", str(ctx.exception))

    def test_rejects_namespace_keyword(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("namespace")
        self.assertIn("C++ keyword", str(ctx.exception))

    def test_rejects_alignas(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("alignas")
        self.assertIn("C++ keyword", str(ctx.exception))

    def test_rejects_constexpr(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("constexpr")
        self.assertIn("C++ keyword", str(ctx.exception))

    def test_rejects_thread_local(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("thread_local")
        self.assertIn("C++ keyword", str(ctx.exception))

    def test_rejects_noexcept(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("noexcept")
        self.assertIn("C++ keyword", str(ctx.exception))

    def test_rejects_nullptr(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("nullptr")
        self.assertIn("C++ keyword", str(ctx.exception))

    def test_rejects_static_assert(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("static_assert")
        self.assertIn("C++ keyword", str(ctx.exception))

    def test_rejects_keyword_in_non_first_segment(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("foo::int")
        self.assertIn("C++ keyword", str(ctx.exception))

    def test_keyword_set_is_nonempty(self) -> None:
        self.assertGreater(len(CPP17_KEYWORDS), 80)

    # -- Leading underscore --

    def test_rejects_leading_underscore_first_segment(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("_foo")
        self.assertIn("underscore", str(ctx.exception))

    def test_rejects_leading_underscore_non_first_segment(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("foo::_bar")
        self.assertIn("underscore", str(ctx.exception))

    def test_rejects_leading_underscore_uppercase(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("foo::_Bar")
        self.assertIn("underscore", str(ctx.exception))

    # -- Double underscore --

    def test_rejects_double_underscore(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("foo__bar")
        self.assertIn("'__'", str(ctx.exception))

    def test_rejects_double_underscore_middle(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("foo::a__b")
        self.assertIn("'__'", str(ctx.exception))

    # -- Trailing underscore --

    def test_rejects_trailing_underscore(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("foo_")
        self.assertIn("underscore", str(ctx.exception))

    def test_rejects_trailing_underscore_non_first(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("foo::bar_")
        self.assertIn("underscore", str(ctx.exception))

    # -- std as first segment --

    def test_rejects_std_first_segment(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_cpp_namespace("std::types")
        self.assertIn("'std'", str(ctx.exception))

    def test_allows_std_in_non_first_segment(self) -> None:
        # std is not a C++ keyword — only rejected as the first segment
        self.assertEqual(validate_cpp_namespace("foo::std"), ("foo", "std"))


class CheckDuplicateBasenamesTest(unittest.TestCase):
    """Tests for check_duplicate_basenames()."""

    def test_no_duplicates_passes(self) -> None:
        paths = [Path("alpha/typist/constants.py"), Path("beta/typist/more.py")]
        check_duplicate_basenames(module_paths=paths)  # should not raise

    def test_duplicates_raises(self) -> None:
        paths = [Path("alpha/typist/types.py"), Path("beta/typist/types.py")]
        with self.assertRaises(ValidationError) as ctx:
            check_duplicate_basenames(module_paths=paths)
        self.assertIn("types", str(ctx.exception))
        self.assertIn("alpha/typist/types.py", str(ctx.exception))
        self.assertIn("beta/typist/types.py", str(ctx.exception))

    def test_single_module_passes(self) -> None:
        paths = [Path("alpha/typist/constants.py")]
        check_duplicate_basenames(module_paths=paths)

    def test_empty_list_passes(self) -> None:
        check_duplicate_basenames(module_paths=[])


if __name__ == "__main__":
    unittest.main()
