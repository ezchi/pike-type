"""Tests for piketype.backends.common.render.

The ``make_environment`` factory is exercised indirectly by the
per-backend tests once those backends own a ``templates/`` directory
(Phase 1 commit 2 onward). Here we test the ``render`` helper, which
has all the type-enforcement logic, against ad-hoc DictLoader envs.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass

import jinja2

from piketype.backends.common.render import render


@dataclass(frozen=True, slots=True)
class _ExampleView:
    name: str
    count: int


class RenderTests(unittest.TestCase):
    def _make_dict_loader_env(self, templates: dict[str, str]) -> jinja2.Environment:
        return jinja2.Environment(
            loader=jinja2.DictLoader(templates),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,
            autoescape=False,
        )

    def test_renders_dataclass_context(self) -> None:
        env = self._make_dict_loader_env({"t.j2": "name={{ name }} count={{ count }}\n"})
        view = _ExampleView(name="alpha", count=3)
        out = render(env=env, template_name="t.j2", context=view)
        self.assertEqual(out, "name=alpha count=3\n")

    def test_appends_trailing_newline_when_missing(self) -> None:
        env = self._make_dict_loader_env({"t.j2": "name={{ name }}"})
        out = render(env=env, template_name="t.j2", context=_ExampleView(name="x", count=0))
        self.assertTrue(out.endswith("\n"))

    def test_rejects_dict_context(self) -> None:
        env = self._make_dict_loader_env({"t.j2": "{{ name }}\n"})
        with self.assertRaises(TypeError):
            render(env=env, template_name="t.j2", context={"name": "alpha"})

    def test_rejects_dataclass_class_object(self) -> None:
        env = self._make_dict_loader_env({"t.j2": "{{ name }}\n"})
        with self.assertRaises(TypeError):
            render(env=env, template_name="t.j2", context=_ExampleView)

    def test_rejects_plain_object(self) -> None:
        env = self._make_dict_loader_env({"t.j2": "{{ name }}\n"})
        with self.assertRaises(TypeError):
            render(env=env, template_name="t.j2", context="not-a-dataclass")


if __name__ == "__main__":
    unittest.main()
