"""View-model tests for the Python backend.

Implements FR-18 of spec 010-jinja-template-migration. Asserts that
``build_module_view_py`` produces the expected primitive values for
representative fixtures.
"""

from __future__ import annotations

from pathlib import Path

from piketype import __version__
from piketype.backends.py.view import (
    EnumView,
    FlagsView,
    ScalarAliasView,
    StructView,
    build_module_view_py,
)
from piketype.discovery.scanner import find_piketype_modules
from piketype.dsl.freeze import (
    build_const_definition_map,
    build_loaded_module,
    build_type_definition_map,
    freeze_module,
    freeze_repo,
)
from piketype.ir.nodes import ModuleIR
from piketype.loader.python_loader import load_or_get_module, prepare_run

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load_fixture_module(fixture_name: str) -> ModuleIR:
    """Load and freeze the alpha/piketype/types.py module of a fixture."""
    repo_root = _FIXTURES / fixture_name / "project"
    module_paths = find_piketype_modules(repo_root)
    with prepare_run(repo_root=repo_root, module_paths=module_paths):
        loaded_modules = [
            build_loaded_module(
                module=load_or_get_module(p, repo_root=repo_root),
                module_path=p,
                repo_root=repo_root,
            )
            for p in module_paths
        ]
        const_map = build_const_definition_map(loaded_modules=loaded_modules)
        type_map = build_type_definition_map(loaded_modules=loaded_modules)
        frozen_modules = [
            freeze_module(
                loaded_module=lm,
                definition_map=const_map,
                type_definition_map=type_map,
            )
            for lm in loaded_modules
        ]
        repo = freeze_repo(
            repo_root=repo_root,
            frozen_modules=frozen_modules,
            tool_version=__version__,
        )
        # Return the only module in single-module fixtures.
        return repo.modules[0]


class StructPaddedFixtureTests:
    """Asserts struct view fields against tests/fixtures/struct_padded."""

    @classmethod
    def setup_class(cls) -> None:
        cls.module = _load_fixture_module("struct_padded")
        cls.view = build_module_view_py(module=cls.module, header="# header\n")

    def test_module_has_struct(self) -> None:
        assert self.view.has_types
        assert self.view.has_structs
        assert not self.view.has_enums

    def test_struct_view_byte_count_includes_alignment(self) -> None:
        structs = [t for t in self.view.types if isinstance(t, StructView)]
        assert len(structs) >= 1
        s = structs[0]
        # struct_padded fixture has alignment, so byte_count > sum of field bytes.
        field_bytes = sum(f.byte_count for f in s.fields)
        assert s.byte_count == field_bytes + s.alignment_bytes

    def test_struct_field_pack_bits_is_byte_count_times_eight(self) -> None:
        structs = [t for t in self.view.types if isinstance(t, StructView)]
        s = structs[0]
        for f in s.fields:
            assert f.pack_bits == f.byte_count * 8

    def test_struct_field_discriminators_mutually_exclusive(self) -> None:
        structs = [t for t in self.view.types if isinstance(t, StructView)]
        s = structs[0]
        for f in s.fields:
            flags = (
                f.is_struct_ref,
                f.is_flags_ref,
                f.is_enum_ref,
                f.is_scalar_ref,
                f.is_narrow_scalar,
                f.is_wide_scalar,
            )
            assert sum(flags) == 1, f"field {f.name}: discriminators={flags}"


class ScalarWideFixtureTests:
    """Asserts scalar alias view fields against tests/fixtures/scalar_wide."""

    @classmethod
    def setup_class(cls) -> None:
        cls.module = _load_fixture_module("scalar_wide")
        cls.view = build_module_view_py(module=cls.module, header="# header\n")

    def test_has_scalar_alias(self) -> None:
        scalars = [t for t in self.view.types if isinstance(t, ScalarAliasView)]
        assert len(scalars) >= 1

    def test_wide_alias_msb_byte_mask_set(self) -> None:
        scalars = [t for t in self.view.types if isinstance(t, ScalarAliasView)]
        # scalar_wide includes at least one wide (>64) alias.
        wide = [s for s in scalars if s.is_wide]
        assert len(wide) >= 1
        for s in wide:
            assert s.msb_byte_mask > 0
            assert s.mask == 0
            assert s.sign_bit == 0

    def test_wide_alias_class_name_uses_ct_suffix(self) -> None:
        scalars = [t for t in self.view.types if isinstance(t, ScalarAliasView)]
        for s in scalars:
            assert s.class_name.endswith("_ct"), f"{s.class_name}"


class EnumBasicFixtureTests:
    """Asserts enum view fields against tests/fixtures/enum_basic."""

    @classmethod
    def setup_class(cls) -> None:
        cls.module = _load_fixture_module("enum_basic")
        cls.view = build_module_view_py(module=cls.module, header="# header\n")

    def test_has_enum(self) -> None:
        assert self.view.has_enums

    def test_enum_view_has_required_fields(self) -> None:
        enums = [t for t in self.view.types if isinstance(t, EnumView)]
        assert len(enums) >= 1
        e = enums[0]
        assert e.class_name.endswith("_ct")
        assert e.enum_class_name.endswith("_enum_t")
        assert e.mask == (1 << e.width) - 1
        assert len(e.members) >= 1
        assert e.first_member_name == e.members[0].name


class FlagsBasicFixtureTests:
    """Asserts flags view fields against tests/fixtures/flags_basic."""

    @classmethod
    def setup_class(cls) -> None:
        cls.module = _load_fixture_module("flags_basic")
        cls.view = build_module_view_py(module=cls.module, header="# header\n")

    def test_has_flags(self) -> None:
        assert self.view.has_flags

    def test_flags_view_data_mask_msb_first(self) -> None:
        flags = [t for t in self.view.types if isinstance(t, FlagsView)]
        assert len(flags) >= 1
        f = flags[0]
        # bit_mask is MSB-first: first flag has the highest bit.
        first_mask = f.fields[0].bit_mask
        assert first_mask == 1 << (f.total_bits - 1)
        assert f.total_bits == f.byte_count * 8
