"""Unit tests for C++ namespace validation."""

from __future__ import annotations

from pathlib import Path
import pytest

from piketype.errors import ValidationError
from piketype.validate.namespace import (
    CPP17_KEYWORDS,
    check_duplicate_basenames,
    validate_cpp_namespace,
)


class ValidateCppNamespaceTest:
    """Tests for validate_cpp_namespace()."""

    # -- Positive cases --

    def test_single_segment(self) -> None:
        assert validate_cpp_namespace("foo") == ("foo",)

    def test_two_segments(self) -> None:
        assert validate_cpp_namespace("foo::bar") == ("foo", "bar")

    def test_three_segments(self) -> None:
        assert validate_cpp_namespace("a::b::c") == ("a", "b", "c")

    def test_segment_with_digits(self) -> None:
        assert validate_cpp_namespace("foo2::bar3") == ("foo2", "bar3")

    # -- Empty / missing segments --

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValidationError):
            validate_cpp_namespace("")

    def test_rejects_double_colon_prefix(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("::foo")
        assert "empty segment" in str(ctx.value)

    def test_rejects_double_colon_suffix(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("foo::")
        assert "empty segment" in str(ctx.value)

    def test_rejects_quadruple_colon(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("foo::::bar")
        assert "empty segment" in str(ctx.value)

    # -- Invalid identifier syntax --

    def test_rejects_leading_digit(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("123bad")
        assert "not a valid C++ identifier" in str(ctx.value)

    def test_rejects_hyphen(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("foo-bar")
        assert "not a valid C++ identifier" in str(ctx.value)

    # -- C++ keywords --

    def test_rejects_class_keyword(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("class")
        assert "C++ keyword" in str(ctx.value)

    def test_rejects_namespace_keyword(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("namespace")
        assert "C++ keyword" in str(ctx.value)

    def test_rejects_alignas(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("alignas")
        assert "C++ keyword" in str(ctx.value)

    def test_rejects_constexpr(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("constexpr")
        assert "C++ keyword" in str(ctx.value)

    def test_rejects_thread_local(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("thread_local")
        assert "C++ keyword" in str(ctx.value)

    def test_rejects_noexcept(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("noexcept")
        assert "C++ keyword" in str(ctx.value)

    def test_rejects_nullptr(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("nullptr")
        assert "C++ keyword" in str(ctx.value)

    def test_rejects_static_assert(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("static_assert")
        assert "C++ keyword" in str(ctx.value)

    def test_rejects_keyword_in_non_first_segment(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("foo::int")
        assert "C++ keyword" in str(ctx.value)

    def test_keyword_set_is_nonempty(self) -> None:
        assert len(CPP17_KEYWORDS) > 80

    # -- Leading underscore --

    def test_rejects_leading_underscore_first_segment(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("_foo")
        assert "underscore" in str(ctx.value)

    def test_rejects_leading_underscore_non_first_segment(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("foo::_bar")
        assert "underscore" in str(ctx.value)

    def test_rejects_leading_underscore_uppercase(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("foo::_Bar")
        assert "underscore" in str(ctx.value)

    # -- Double underscore --

    def test_rejects_double_underscore(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("foo__bar")
        assert "'__'" in str(ctx.value)

    def test_rejects_double_underscore_middle(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("foo::a__b")
        assert "'__'" in str(ctx.value)

    # -- Trailing underscore --

    def test_rejects_trailing_underscore(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("foo_")
        assert "underscore" in str(ctx.value)

    def test_rejects_trailing_underscore_non_first(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("foo::bar_")
        assert "underscore" in str(ctx.value)

    # -- std as first segment --

    def test_rejects_std_first_segment(self) -> None:
        with pytest.raises(ValidationError) as ctx:
            validate_cpp_namespace("std::types")
        assert "'std'" in str(ctx.value)

    def test_allows_std_in_non_first_segment(self) -> None:
        # std is not a C++ keyword — only rejected as the first segment
        assert validate_cpp_namespace("foo::std") == ("foo", "std")


class CheckDuplicateBasenamesTest:
    """Tests for check_duplicate_basenames()."""

    def test_no_duplicates_passes(self) -> None:
        paths = [Path("alpha/piketype/constants.py"), Path("beta/piketype/more.py")]
        check_duplicate_basenames(module_paths=paths)  # should not raise

    def test_duplicates_raises(self) -> None:
        paths = [Path("alpha/piketype/types.py"), Path("beta/piketype/types.py")]
        with pytest.raises(ValidationError) as ctx:
            check_duplicate_basenames(module_paths=paths)
        assert "types" in str(ctx.value)
        assert "alpha/piketype/types.py" in str(ctx.value)
        assert "beta/piketype/types.py" in str(ctx.value)

    def test_single_module_passes(self) -> None:
        paths = [Path("alpha/piketype/constants.py")]
        check_duplicate_basenames(module_paths=paths)

    def test_empty_list_passes(self) -> None:
        check_duplicate_basenames(module_paths=[])
