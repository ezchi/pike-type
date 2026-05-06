"""Module-level dependency graph derived from the IR.

Each ``ModuleIR`` carries cross-module references in its
``dependencies`` field. This module turns those into a flat directed
graph keyed on ``python_module_name`` and exposes cycle detection.

Distinct from ``validate.engine``'s struct-cycle detection: this graph
operates at *module* granularity, treating module → module references
as edges. A cycle here means modules A and B mutually reference each
other (or a longer chain closes), which is incompatible with topo-
sorted code generation.
"""

from __future__ import annotations

from piketype.ir.nodes import RepoIR


def build_module_graph(repo: RepoIR) -> dict[str, set[str]]:
    """Map each module's ``python_module_name`` to the set of module names it depends on."""
    graph: dict[str, set[str]] = {}
    for module in repo.modules:
        deps: set[str] = {dep.target.python_module_name for dep in module.dependencies}
        graph[module.ref.python_module_name] = deps
    return graph


def detect_module_cycles(repo: RepoIR) -> list[list[str]]:
    """Return every back-edge cycle in the module dependency graph.

    Each cycle is a list of ``python_module_name`` strings, starting
    and ending at the cycle's entry point. Empty list if acyclic.
    """
    graph = build_module_graph(repo)
    cycles: list[list[str]] = []
    visited: set[str] = set()
    on_stack: set[str] = set()
    stack: list[str] = []

    def dfs(node: str) -> None:
        visited.add(node)
        on_stack.add(node)
        stack.append(node)
        for nxt in sorted(graph.get(node, set())):
            if nxt in on_stack:
                idx = stack.index(nxt)
                cycle = list(stack[idx:]) + [nxt]
                cycles.append(cycle)
            elif nxt not in visited:
                dfs(nxt)
        stack.pop()
        on_stack.discard(node)

    for node in sorted(graph):
        if node not in visited:
            dfs(node)
    return cycles
