"""Template rendering helpers for piketype backends.

This module is the single auditable site (FR-16, CL-2) for the Jinja2
environment used by every backend code emitter and for any custom
filters or globals registered on it.

Production code constructs an environment with ``make_environment`` and
renders templates with ``render``. The render function only accepts a
view-model dataclass instance as context (FR-3); dict contexts are
rejected so all production rendering goes through typed view models.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass

import jinja2


def make_environment(*, package: str) -> jinja2.Environment:
    """Construct the per-call Jinja environment for a backend package.

    The package argument is a dotted Python package name (e.g.
    ``"piketype.backends.py"``). Templates are loaded from the
    ``templates`` subdirectory of that package via ``PackageLoader``,
    which works equivalently from a source checkout and an installed
    wheel.

    Environment options are pinned by FR-2 and SHALL NOT be changed
    without a spec amendment.
    """
    return jinja2.Environment(
        loader=jinja2.PackageLoader(package, "templates"),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=jinja2.StrictUndefined,
        autoescape=False,
    )


def render(*, env: jinja2.Environment, template_name: str, context: object) -> str:
    """Render a template against a view-model dataclass instance.

    Per FR-3, the production context is always a frozen view-model
    dataclass. Dict contexts are rejected. Tests that need a dict-shaped
    context build their own ad-hoc env via
    ``jinja2.Environment(loader=DictLoader(...))`` rather than going
    through this helper.

    The returned string is guaranteed to end in ``"\\n"`` (FR-3),
    matching the contract of the legacy inline emitters.
    """
    if isinstance(context, type) or not is_dataclass(context):
        raise TypeError(
            f"render context must be a dataclass instance, got {type(context).__name__}"
        )
    output = env.get_template(template_name).render(**asdict(context))
    if not output.endswith("\n"):
        output += "\n"
    return output


# Custom filters and globals (CL-2, FR-16) are registered here when added.
# Currently no custom filters or globals are registered. Each addition
# SHALL be documented in docs/templates.md and tested in
# tests/test_render.py.
