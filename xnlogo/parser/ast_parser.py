"""Python AST to xnLogo IR translation."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

from xnlogo.ir.model import (
    AgentBehavior,
    AgentSpec,
    ExecutionContext,
    ModelSpec,
    SchedulePhase,
    StateField,
)
from xnlogo.ir.statements import IRStatement, RawStatement
from xnlogo.semantics.diagnostics import DiagnosticBag


@dataclass
class ParsedModule:
    """Result of parsing Python sources."""

    model: ModelSpec
    diagnostics: DiagnosticBag


@dataclass
class _ModuleInfo:
    path: Path
    module: ast.Module
    source: str


class Parser:
    """Parse Python source files into the xnLogo intermediate representation."""

    def __init__(self) -> None:
        self._diagnostics = DiagnosticBag()

    def parse(self, paths: Iterable[Path]) -> ParsedModule:
        """Parse a collection of Python source paths to a single ModelSpec."""
        modules = [self._parse_path(path) for path in paths]
        model = self._merge_modules(modules)
        return ParsedModule(model=model, diagnostics=self._diagnostics)

    def _parse_path(self, path: Path) -> _ModuleInfo:
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            self._diagnostics.error(f"Failed to read {path}: {exc}")
            return _ModuleInfo(path=path, module=ast.parse(""), source="")

        try:
            module = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            self._diagnostics.error(f"Syntax error in {path}: {exc.msg}")
            module = ast.parse("")

        return _ModuleInfo(path=path, module=module, source=source)

    def _merge_modules(self, modules: Iterable[_ModuleInfo]) -> ModelSpec:
        model = ModelSpec()
        for module in modules:
            analyzer = _ModuleAnalyzer(module, self._diagnostics)
            analyzer.populate(model)
        return model


class _ModuleAnalyzer(ast.NodeVisitor):
    """Populate the intermediate representation from a Python module."""

    def __init__(self, info: _ModuleInfo, diagnostics: DiagnosticBag) -> None:
        self._info = info
        self._diagnostics = diagnostics
        self._model: Optional[ModelSpec] = None

    def populate(self, model: ModelSpec) -> None:
        self._model = model
        self.visit(self._info.module)

    # ast.NodeVisitor overrides -------------------------------------------------

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Capture @agent class definitions as AgentSpec entries."""

        if not self._is_agent(node):
            return

        if self._model is None:  # safety guard
            return

        breed = self._extract_breed(node)
        agent = AgentSpec(identifier=node.name, breed=breed)
        self._populate_state_fields(agent, node)
        self._populate_behaviors(agent, node)
        self._model.agents.append(agent)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Capture interface = Interface(...) assignments."""
        if self._model is None:
            return
        
        # Check if this is an interface assignment
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "interface":
                self._extract_interface(node.value)
        
        self.generic_visit(node)

    # Helpers ------------------------------------------------------------------

    def _extract_interface(self, node: ast.AST) -> None:
        """Extract UI widgets from Interface(...) constructor call."""
        if not isinstance(node, ast.Call):
            return
        
        # Check if this is an Interface constructor
        if isinstance(node.func, ast.Name) and node.func.id == "Interface":
            # Process keyword arguments to extract widgets
            for keyword in node.keywords:
                if keyword.arg and self._model:
                    self._extract_widgets_from_keyword(keyword)
    
    def _extract_widgets_from_keyword(self, keyword: ast.keyword) -> None:
        """Extract widgets from Interface keyword arguments."""
        if not self._model:
            return
        
        arg_name = keyword.arg
        value = keyword.value
        
        # Handle single widget (view)
        if arg_name == "view" and isinstance(value, ast.Call):
            widget_xml = self._widget_to_xml_placeholder(value)
            if widget_xml:
                self._model.widgets.append(widget_xml)
        
        # Handle lists of widgets
        elif isinstance(value, ast.List):
            for element in value.elts:
                if isinstance(element, ast.Call):
                    widget_xml = self._widget_to_xml_placeholder(element)
                    if widget_xml:
                        self._model.widgets.append(widget_xml)
    
    def _widget_to_xml_placeholder(self, node: ast.Call) -> Optional[str]:
        """Convert widget constructor call to XML placeholder.
        
        The actual XML generation happens at runtime when the widget
        classes are instantiated. We store a marker here.
        """
        if isinstance(node.func, ast.Name):
            # Store widget constructor call as unparsed Python code
            # This will be evaluated later during code generation
            widget_code = self._safe_unparse(node)
            if widget_code:
                return f"<!-- WIDGET: {widget_code} -->"
        return None

    def _is_agent(self, node: ast.ClassDef) -> bool:
        for decorator in node.decorator_list:
            name = self._decorator_name(decorator)
            if name == "agent":
                return True
        return False

    def _extract_breed(self, node: ast.ClassDef) -> Optional[str]:
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and self._decorator_name(decorator.func) == "agent"
            ):
                # keyword argument takes precedence
                for keyword in decorator.keywords:
                    if keyword.arg == "breed":
                        value = self._literal_string(keyword.value)
                        if value is not None:
                            return value
                # positional argument
                if decorator.args:
                    value = self._literal_string(decorator.args[0])
                    if value is not None:
                        return value
        return None

    def _populate_state_fields(self, agent: AgentSpec, node: ast.ClassDef) -> None:
        instance_vars = self._detect_instance_variables(node)
        
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                name = stmt.target.id
                type_hint = (
                    self._safe_unparse(stmt.annotation) if stmt.annotation else None
                )
                default = self._safe_unparse(stmt.value) if stmt.value else None
                
                field = StateField(name=name, type_hint=type_hint, default=default)
                
                if name in instance_vars:
                    agent.state_fields.append(field)
                else:
                    agent.class_attributes.append(field)
    
    def _detect_instance_variables(self, node: ast.ClassDef) -> set[str]:
        instance_vars = set()
        setup_methods = {"setup_world", "setup_agents", "__init__"}
        
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name not in setup_methods:
                for body_stmt in ast.walk(stmt):
                    if isinstance(body_stmt, ast.Attribute):
                        if (isinstance(body_stmt.value, ast.Name) and 
                            body_stmt.value.id == "self"):
                            attr_name = body_stmt.attr
                            instance_vars.add(attr_name)
        
        return instance_vars

    def _populate_behaviors(self, agent: AgentSpec, node: ast.ClassDef) -> None:
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                behavior = AgentBehavior(name=stmt.name)
                behavior.statements = list(self._statements_from_function(stmt))
                behavior.schedule_phase = self._determine_schedule_phase(stmt)
                behavior.context = self._determine_context(stmt)
                agent.behaviors.append(behavior)
    
    def _determine_schedule_phase(self, func: ast.FunctionDef) -> SchedulePhase:
        if func.name.startswith("setup_"):
            return SchedulePhase.SETUP
        elif func.name in ("run_model", "go", "step"):
            return SchedulePhase.TICK
        return SchedulePhase.CUSTOM
    
    def _determine_context(self, func: ast.FunctionDef) -> ExecutionContext:
        observer_keywords = ["sprout", "create-turtles", "clear-turtles", "reset-ticks", "clear-all", "split"]
        source = self._safe_unparse(func) or ""
        
        for keyword in observer_keywords:
            if keyword in source:
                return ExecutionContext.OBSERVER
        
        if func.name == "setup_world":
            return ExecutionContext.OBSERVER
        
        if "update" in func.name or "stats" in func.name or "analysis" in func.name:
            return ExecutionContext.OBSERVER
        
        return ExecutionContext.TURTLE

    def _statements_from_function(self, func: ast.FunctionDef) -> Iterator[IRStatement]:
        for stmt in func.body:
            # use ast.unparse for consistent formatting
            source = self._safe_unparse(stmt) or ""
            yield RawStatement(source=source.strip())

    # Utility functions ---------------------------------------------------------

    def _decorator_name(self, decorator: ast.expr) -> Optional[str]:
        if isinstance(decorator, ast.Name):
            return decorator.id
        if isinstance(decorator, ast.Attribute):
            return decorator.attr
        if isinstance(decorator, ast.Call):
            return self._decorator_name(decorator.func)
        return None

    def _safe_unparse(self, node: Optional[ast.AST]) -> Optional[str]:
        if node is None:
            return None
        try:
            return ast.unparse(node)
        except AttributeError:  # pragma: no cover - Python < 3.9 fallback
            from ast import dump

            return dump(node)

    def _literal_string(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None


def iter_agent_behaviors(agent: AgentSpec) -> Iterator[AgentBehavior]:
    """Yield behaviors for a given agent."""
    yield from agent.behaviors


def iter_statements(behavior: AgentBehavior) -> Iterator[IRStatement]:
    """Yield IR statements within a behavior."""
    yield from behavior.statements
