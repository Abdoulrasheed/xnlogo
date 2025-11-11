"""Semantic checks for NetLogo code generation compatibility."""

from __future__ import annotations

import ast
from collections import Counter
from typing import TYPE_CHECKING, Set

if TYPE_CHECKING:
    from xnlogo.ir.model import ModelSpec
    from xnlogo.semantics.diagnostics import DiagnosticBag

from xnlogo.ir.model import AgentSpec
from xnlogo.ir.statements import RawStatement


def run_structural_checks(model: ModelSpec, diagnostics: DiagnosticBag) -> None:
    """Validate high-level model structure."""
    if not model.agents:
        diagnostics.error("No agents defined. Add at least one @agent-decorated class.")
        return

    for agent in model.agents:
        if not agent.behaviors:
            diagnostics.warning(f"Agent '{agent.identifier}' has no behaviors defined.")
        _check_duplicate_behaviors(agent, diagnostics)


def run_behavioral_checks(model: ModelSpec, diagnostics: DiagnosticBag) -> None:
    """Validate behavior-level invariants."""
    for agent in model.agents:
        for behavior in agent.behaviors:
            if not behavior.statements:
                diagnostics.warning(
                    f"Behavior '{behavior.name}' in agent '{agent.identifier}' has no statements."
                )
            _check_unsupported_constructs(agent, behavior, diagnostics)


def _check_duplicate_behaviors(agent: AgentSpec, diagnostics: DiagnosticBag) -> None:
    """Ensure each behavior name is unique within an agent."""
    counter = Counter(behavior.name for behavior in agent.behaviors)
    for name, count in counter.items():
        if count > 1:
            diagnostics.error(
                f"Agent '{agent.identifier}' defines behavior '{name}' {count} times; names must be unique."
            )


def _check_unsupported_constructs(
    agent: AgentSpec, behavior, diagnostics: DiagnosticBag
) -> None:
    """Detect Python constructs that cannot be translated to NetLogo."""
    unsupported_nodes: Set[str] = set()

    for statement in behavior.statements:
        if not isinstance(statement, RawStatement):
            continue

        # Skip validation for statements that are already in NetLogo syntax
        if getattr(statement, "is_netlogo", False):
            continue

        try:
            tree = ast.parse(statement.source)
        except SyntaxError as e:
            diagnostics.error(
                f"Agent '{agent.identifier}', behavior '{behavior.name}': "
                f"Syntax error in statement: {e.msg}"
            )
            continue
        except Exception as e:
            diagnostics.warning(f"Failed to parse statement for validation: {e}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFor, ast.AsyncWith, ast.Await)):
                unsupported_nodes.add("async/await")
            elif isinstance(node, ast.Lambda):
                unsupported_nodes.add("lambda")
            elif isinstance(node, ast.Try):
                unsupported_nodes.add("try/except")
            elif isinstance(node, ast.ListComp) and _is_complex_comprehension(node):
                unsupported_nodes.add("complex list comprehension")
            elif isinstance(node, (ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                if not _is_simple_generator(node):
                    node_type = type(node).__name__
                    unsupported_nodes.add(
                        f"{node_type.replace('Comp', ' comprehension').replace('Exp', ' expression')}"
                    )
            elif isinstance(node, (ast.Yield, ast.YieldFrom)):
                unsupported_nodes.add("generator (yield)")
            elif isinstance(node, ast.With):
                unsupported_nodes.add("with statement")
            elif isinstance(node, ast.ClassDef):
                unsupported_nodes.add("nested class")
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                unsupported_nodes.add("import statement")

    for construct in sorted(unsupported_nodes):
        diagnostics.warning(
            f"Agent '{agent.identifier}', behavior '{behavior.name}': {construct} may not translate to NetLogo"
        )


def _is_complex_comprehension(node: ast.ListComp) -> bool:
    """Check if list comprehension is too complex for NetLogo translation."""
    return len(node.generators) > 1 or any(
        gen.ifs for gen in node.generators if len(gen.ifs) > 1
    )


def _is_simple_generator(node) -> bool:
    """Check if generator/comprehension is simple enough to translate."""
    if hasattr(node, "generators"):
        return len(node.generators) == 1 and len(node.generators[0].ifs) <= 1
    return False
