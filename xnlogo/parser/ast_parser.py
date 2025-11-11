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
    GlobalVar,
    ModelSpec,
    SchedulePhase,
    StateField,
)
from xnlogo.ir.statements import IRStatement, RawStatement
from xnlogo.parser.py_to_netlogo import PythonToNetLogoConverter
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
        """Capture Model subclasses and breed definitions."""

        if self._model is None:  # safety guard
            return

        # Check if this is a Model subclass
        if self._is_model_subclass(node):
            self._populate_model_from_class(node)
            return

        if self._is_agent(node):
            self._diagnostics.error(
                "@agent decorator is no longer supported. "
                "Please use Model subclass instead. "
                "See examples/global_pandemic_complete.py for reference."
            )
            return

    def visit_Assign(self, node: ast.Assign) -> None:
        """Capture interface = Interface(...) assignments."""
        if self._model is None:
            return

        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "interface":
                self._extract_interface(node.value)

        self.generic_visit(node)

    def _extract_interface(self, node: ast.AST) -> None:
        if not isinstance(node, ast.Call):
            return

        if isinstance(node.func, ast.Name) and node.func.id == "Interface":
            for keyword in node.keywords:
                if keyword.arg and self._model:
                    self._extract_widgets_from_keyword(keyword)

    def _extract_widgets_from_keyword(self, keyword: ast.keyword) -> None:
        if not self._model:
            return

        arg_name = keyword.arg
        value = keyword.value

        if arg_name == "view" and isinstance(value, ast.Call):
            widget_xml = self._widget_to_xml_placeholder(value)
            if widget_xml:
                self._model.widgets.append(widget_xml)

        elif isinstance(value, ast.List):
            for element in value.elts:
                if isinstance(element, ast.Call):
                    widget_xml = self._widget_to_xml_placeholder(element)
                    if widget_xml:
                        self._model.widgets.append(widget_xml)

    def _widget_to_xml_placeholder(self, node: ast.Call) -> Optional[str]:
        if isinstance(node.func, ast.Name):
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

    def _is_model_subclass(self, node: ast.ClassDef) -> bool:
        """Check if class inherits from Model."""
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Model":
                return True
            if isinstance(base, ast.Attribute) and base.attr == "Model":
                return True
        return False

    def _populate_model_from_class(self, node: ast.ClassDef) -> None:
        """Extract globals, breeds, and behaviors from a Model subclass."""
        if not self._model:
            return

        # Extract from __init__ method
        init_method = self._find_method(node, "__init__")
        if init_method:
            self._extract_globals_from_init(init_method)
            self._extract_breeds_from_init(init_method)

        # Extract UI widgets from ui() method
        ui_method = self._find_method(node, "ui")
        if ui_method:
            self._extract_widgets_from_ui_method(ui_method)

        # Extract info documentation from info() method
        info_method = self._find_method(node, "info")
        if info_method:
            self._extract_info_from_method(info_method)

        # Extract observer and turtle procedures from methods
        for stmt in node.body:
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip special Model methods
                if stmt.name in (
                    "__init__",
                    "setup",
                    "step",
                    "reset",
                    "run",
                    "ui",
                    "info",
                ):
                    continue

                # Count parameters (excluding 'self')
                param_count = len(stmt.args.args) - 1

                # Turtle procedures have exactly 1 extra parameter (self + turtle)
                if param_count == 1:
                    self._extract_turtle_procedure(stmt)
                # Observer procedures have 0 or more extra parameters (but not 1)
                else:
                    self._extract_observer_procedure(stmt)

    def _find_method(self, node: ast.ClassDef, name: str) -> Optional[ast.FunctionDef]:
        """Find a method by name in a class."""
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == name:
                return stmt
        return None

    def _extract_globals_from_init(self, init_method: ast.FunctionDef) -> None:
        """Extract global variables from self.variable assignments in __init__."""
        if not self._model:
            return

        for stmt in ast.walk(init_method):
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute):
                        if (
                            isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            var_name = target.attr
                            default = self._safe_unparse(stmt.value)

                            # Skip breed assignments
                            if isinstance(stmt.value, ast.Call):
                                if (
                                    isinstance(stmt.value.func, ast.Name)
                                    and stmt.value.func.id == "breed"
                                ):
                                    continue

                            # Skip if it's calling super().__init__()
                            if isinstance(stmt.value, ast.Call) and isinstance(
                                stmt.value.func, ast.Attribute
                            ):
                                if isinstance(stmt.value.func.value, ast.Call):
                                    continue

                            self._model.globals.append(
                                GlobalVar(name=var_name, default=default)
                            )

    def _extract_breeds_from_init(self, init_method: ast.FunctionDef) -> None:
        """Extract breed definitions from self.breed_name = breed(...) calls."""
        if not self._model:
            return

        for stmt in ast.walk(init_method):
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute):
                        if (
                            isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            # Check if RHS is a breed(...) call
                            if isinstance(stmt.value, ast.Call):
                                if (
                                    isinstance(stmt.value.func, ast.Name)
                                    and stmt.value.func.id == "breed"
                                ):
                                    self._extract_breed_spec(stmt.value)

    def _extract_breed_spec(self, call: ast.Call) -> None:
        """Extract AgentSpec from a breed(...) call."""
        if not self._model:
            return

        # breed("plural", "singular", var1=default1, var2=default2, ...)
        if len(call.args) < 2:
            return

        plural = self._literal_string(call.args[0])
        singular = self._literal_string(call.args[1])

        if not plural:
            return

        # Create agent spec
        agent = AgentSpec(
            identifier=plural.capitalize(), breed=plural, singular=singular
        )

        # Extract own variables from keyword arguments
        for keyword in call.keywords:
            if keyword.arg:
                field = StateField(
                    name=keyword.arg, default=self._safe_unparse(keyword.value)
                )
                agent.state_fields.append(field)

        self._model.agents.append(agent)

    def _extract_observer_procedure(self, func: ast.FunctionDef) -> None:
        """Extract observer procedure from a method."""
        if not self._model:
            return

        # Find the breed this belongs to (if any)
        # For now, we'll create a pseudo-agent for observer procedures
        observer_agent = self._get_or_create_observer_agent()

        # Extract parameter names (excluding 'self')
        parameters = [arg.arg for arg in func.args.args if arg.arg != "self"]

        behavior = AgentBehavior(name=func.name, parameters=parameters)
        behavior.statements = list(self._statements_from_model_method(func))
        behavior.schedule_phase = self._determine_schedule_phase(func)
        behavior.context = ExecutionContext.OBSERVER
        observer_agent.behaviors.append(behavior)

    def _extract_turtle_procedure(self, func: ast.FunctionDef) -> None:
        """Extract turtle procedure from a method that takes a turtle parameter."""
        if not self._model or not self._model.agents:
            return

        # Find the first non-Observer agent (i.e., the actual turtle breed)
        target_agent = None
        for agent in self._model.agents:
            if agent.identifier != "Observer":
                target_agent = agent
                break

        if not target_agent:
            # If no turtle breed exists yet, create a default "Turtles" agent
            target_agent = AgentSpec(identifier="Turtles", breed="turtles")
            self._model.agents.append(target_agent)

        behavior = AgentBehavior(name=func.name)
        behavior.statements = list(self._statements_from_model_method(func))
        behavior.schedule_phase = SchedulePhase.TICK
        behavior.context = ExecutionContext.TURTLE
        target_agent.behaviors.append(behavior)

    def _get_or_create_observer_agent(self) -> AgentSpec:
        """Get or create a pseudo-agent for observer procedures."""
        if not self._model:
            raise RuntimeError("Model not initialized")

        # Look for existing observer agent
        for agent in self._model.agents:
            if agent.identifier == "Observer":
                return agent

        # Create new observer agent
        observer = AgentSpec(identifier="Observer", breed=None)
        self._model.agents.insert(0, observer)
        return observer

    def _extract_widgets_from_ui_method(self, ui_method: ast.FunctionDef) -> None:
        """Extract UI widgets from Model.ui() method by finding add_widget() calls."""
        if not self._model:
            return

        # Track plot widgets to collect their pens
        plot_widgets = {}

        # Walk through the method body sequentially to preserve order
        for stmt in ui_method.body:
            # Check for plot variable assignment: population_plot = Plot(...)
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and isinstance(
                        stmt.value, ast.Call
                    ):
                        if (
                            isinstance(stmt.value.func, ast.Name)
                            and stmt.value.func.id == "Plot"
                        ):
                            # This is a plot assignment
                            plot_var_name = target.id
                            plot_dict = self._extract_widget_dict(stmt.value)
                            if plot_dict:
                                plot_dict["pens"] = []
                                plot_widgets[plot_var_name] = plot_dict

            # Check for plot.add_pen(...) calls
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Attribute):
                    # Check if this is plot_var.add_pen(PlotPen(...))
                    if (
                        isinstance(call.func.value, ast.Name)
                        and call.func.attr == "add_pen"
                        and call.args
                    ):
                        plot_var = call.func.value.id
                        if plot_var in plot_widgets and call.args:
                            pen_node = call.args[0]
                            if isinstance(pen_node, ast.Call) and isinstance(
                                pen_node.func, ast.Name
                            ):
                                if pen_node.func.id == "PlotPen":
                                    pen_dict = self._extract_pen_dict(pen_node)
                                    if pen_dict:
                                        plot_widgets[plot_var]["pens"].append(pen_dict)

                    # Check if this is self.add_widget(...)
                    elif (
                        isinstance(call.func.value, ast.Name)
                        and call.func.value.id == "self"
                        and call.func.attr == "add_widget"
                    ):
                        if call.args:
                            widget_arg = call.args[0]
                            # Check if it's a plot variable reference
                            if (
                                isinstance(widget_arg, ast.Name)
                                and widget_arg.id in plot_widgets
                            ):
                                # Add the plot with its pens
                                self._model.widgets.append(plot_widgets[widget_arg.id])
                            else:
                                # Regular widget
                                widget_dict = self._extract_widget_dict(widget_arg)
                                if widget_dict:
                                    self._model.widgets.append(widget_dict)

    def _extract_pen_dict(self, node: ast.Call) -> Optional[dict]:
        """Extract pen information from a PlotPen constructor call."""
        pen_dict = {}

        # Extract keyword arguments
        for keyword in node.keywords:
            if keyword.arg:
                value = self._safe_eval_value(keyword.value)
                pen_dict[keyword.arg] = value

        return pen_dict if pen_dict else None

    def _extract_widget_dict(self, node: ast.AST) -> Optional[dict]:
        """Extract widget information from a widget constructor call."""
        if not isinstance(node, ast.Call):
            return None

        widget_type = None
        if isinstance(node.func, ast.Name):
            widget_type = node.func.id

        if not widget_type:
            return None

        # Build a dictionary of widget properties
        widget_dict = {"type": widget_type, "args": {}}

        # Extract keyword arguments
        for keyword in node.keywords:
            if keyword.arg:
                # Try to evaluate the value
                value = self._safe_eval_value(keyword.value)
                widget_dict["args"][keyword.arg] = value

        # For Plot widgets, check if there are pen definitions via add_pen() calls
        if widget_type == "Plot":
            # Store the plot node for later pen extraction
            widget_dict["_plot_node"] = node

        return widget_dict

    def _safe_eval_value(self, node: ast.AST) -> any:
        """Safely evaluate AST node to get the value."""
        try:
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Str):
                return node.s
            elif isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.NameConstant):
                return node.value
            elif isinstance(node, (ast.List, ast.Tuple)):
                return [self._safe_eval_value(elt) for elt in node.elts]
            elif isinstance(node, ast.UnaryOp):
                if isinstance(node.op, ast.USub):
                    operand = self._safe_eval_value(node.operand)
                    if operand is not None:
                        return -operand
            else:
                # For complex expressions, return the unparsed source
                return self._safe_unparse(node)
        except Exception:
            return self._safe_unparse(node)
        return None

    def _extract_info_from_method(self, info_method: ast.FunctionDef) -> None:
        """Extract info documentation from Model.info() method."""
        if not self._model:
            return

        # Look for a return statement with a string
        for stmt in info_method.body:
            if isinstance(stmt, ast.Return) and stmt.value:
                if isinstance(stmt.value, ast.Constant) and isinstance(
                    stmt.value.value, str
                ):
                    # Store the info text in the model
                    self._model.info_text = stmt.value.value
                    return
                elif isinstance(stmt.value, ast.Str):
                    self._model.info_text = stmt.value.s
                    return

    def _statements_from_model_method(
        self, func: ast.FunctionDef
    ) -> Iterator[IRStatement]:
        """Extract statements from a Model method, converting Python to NetLogo."""
        # Collect parameter names (excluding 'self') - these represent the agent context
        context_params = set()
        if func.args.args:
            for arg in func.args.args[1:]:  # Skip 'self'
                context_params.add(arg.arg)

        converter = PythonToNetLogoConverter(context_params=context_params)

        # Detect guard clause pattern: if not condition: return at start of function
        has_guard_clause = False
        guard_condition = None
        start_idx = 0

        for i, stmt in enumerate(func.body):
            # Skip docstrings
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                start_idx = i + 1
                continue

            # Check if this is a guard clause: if not X: return
            if (
                i == start_idx
                and isinstance(stmt, ast.If)
                and not stmt.orelse
                and len(stmt.body) == 1
                and isinstance(stmt.body[0], ast.Return)
                and stmt.body[0].value is None
            ):
                has_guard_clause = True
                # Extract the positive condition (invert the not)
                if isinstance(stmt.test, ast.UnaryOp) and isinstance(
                    stmt.test.op, ast.Not
                ):
                    guard_condition = stmt.test.operand
                else:
                    # Create a Not node to invert the condition
                    guard_condition = ast.UnaryOp(op=ast.Not(), operand=stmt.test)
                start_idx = i + 1
                break
            else:
                break

        # If we have a guard clause, wrap the rest in if block
        if has_guard_clause and guard_condition:
            # Convert guard condition to NetLogo
            guard_netlogo = converter._convert_expr(guard_condition)
            yield RawStatement(source=f"if {guard_netlogo} [", is_netlogo=True)

            # Process remaining statements with increased indent
            converter.indent_level += 1
            for stmt in func.body[start_idx:]:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    continue
                netlogo_code = converter.convert(stmt)
                if netlogo_code and netlogo_code.strip():
                    yield RawStatement(source=netlogo_code, is_netlogo=True)
            converter.indent_level -= 1

            yield RawStatement(source="]", is_netlogo=True)
        else:
            # No guard clause, process normally
            for stmt in func.body:
                # Skip docstrings
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                    continue

                # Convert the statement to NetLogo-compatible code using AST converter
                netlogo_code = converter.convert(stmt)
                if netlogo_code and netlogo_code.strip():
                    yield RawStatement(source=netlogo_code, is_netlogo=True)

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
                        if (
                            isinstance(body_stmt.value, ast.Name)
                            and body_stmt.value.id == "self"
                        ):
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
        observer_keywords = [
            "sprout",
            "create-turtles",
            "clear-turtles",
            "reset-ticks",
            "clear-all",
            "split",
        ]
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
        except AttributeError:
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
