"""Convert IR into NetLogo artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from xnlogo.codegen.netlogo_translator import translate_statement
from xnlogo.ir.model import (
    AgentBehavior,
    AgentSpec,
    ExecutionContext,
    ModelSpec,
    Reporter,
    SchedulePhase,
)
from xnlogo.ir.statements import RawStatement

_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(default=False),
    trim_blocks=True,
    lstrip_blocks=True,
)


@dataclass
class BuildOptions:
    format: str = "nlogox"
    default_widgets: bool = True


class NetLogoGenerator:
    """Emit NetLogo output from the intermediate representation."""

    def __init__(self, model: ModelSpec, options: BuildOptions | None = None) -> None:
        self.model = model
        self.options = options or BuildOptions()

    def render(self) -> str:
        """Render the NetLogo code body."""
        blocks: list[list[str]] = []

        # Declarations
        header = self._render_declarations()
        if header:
            blocks.append(header)

        # Main procedures
        blocks.append(self._render_setup())
        blocks.append(self._render_go())

        # Reporters
        for reporter in self.model.reporters:
            reporter_block = self._render_reporter(reporter)
            if reporter_block:
                blocks.append(reporter_block)

        for agent in self.model.agents:
            for behavior in agent.behaviors:
                if behavior.schedule_phase == SchedulePhase.CUSTOM:
                    blocks.append(self._render_behavior(agent, behavior))

        return "\n\n".join("\n".join(block) for block in blocks if block).strip() + "\n"

    def widgets(self) -> List[str]:
        """Return serialized widget XML snippets."""
        widgets: List[str] = []
        for widget in self.model.widgets:
            if isinstance(widget, str):
                # Check if this is a widget placeholder comment
                if widget.startswith("<!-- WIDGET:") and widget.endswith("-->"):
                    # Extract and evaluate the widget code
                    widget_code = widget[12:-4].strip()  # Remove <!-- WIDGET: and -->
                    evaluated_widget = self._evaluate_widget(widget_code)
                    if evaluated_widget:
                        widgets.append(evaluated_widget)
                else:
                    widgets.append(widget)
        if self.options.default_widgets:
            widgets.extend(_default_widgets())
        return widgets
    
    def _evaluate_widget(self, widget_code: str) -> Optional[str]:
        """Evaluate widget constructor code and generate XML."""
        try:
            # Import the UI module
            from xnlogo.runtime import ui
            
            # Create a safe namespace for evaluation
            namespace = {
                'View': ui.View,
                'Button': ui.Button,
                'Switch': ui.Switch,
                'Slider': ui.Slider,
                'Monitor': ui.Monitor,
                'Plot': ui.Plot,
                'PlotPen': ui.PlotPen,
                'Chooser': ui.Chooser,
                'TextBox': ui.TextBox,
            }
            
            # Evaluate the widget constructor
            widget_obj = eval(widget_code, namespace)
            
            # Generate XML from the widget object
            if hasattr(widget_obj, 'to_xml'):
                return widget_obj.to_xml()
        except Exception as e:
            # Log error but continue - widget will be skipped
            import sys
            print(f"Warning: Failed to evaluate widget '{widget_code}': {e}", file=sys.stderr)
        
        return None

    def emit(self) -> str:
        template_name = (
            "base.nlogox.xml.j2" if self.options.format == "nlogox" else "base.nlogo.j2"
        )
        template = _TEMPLATE_ENV.get_template(template_name)
        return template.render(code=self.render(), widgets=self.widgets())

    # Internal helpers ---------------------------------------------------------

    def _render_declarations(self) -> list[str]:
        """Render globals, patches-own, breeds, and turtles-own declarations."""
        lines: list[str] = []

        all_globals = list(self.model.globals)
        for agent in self.model.agents:
            for class_attr in agent.class_attributes:
                from xnlogo.ir.model import GlobalVar
                all_globals.append(GlobalVar(name=class_attr.name, default=class_attr.default))

        if all_globals:
            globals_list = " ".join(g.name for g in all_globals)
            if globals_list:
                lines.append(f"globals [{globals_list}]")

        if self.model.patches.state_fields:
            patch_fields = " ".join(
                field.name for field in self.model.patches.state_fields
            )
            if patch_fields:
                lines.append(f"patches-own [{patch_fields}]")

        for agent in self.model.agents:
            if agent.breed:
                breed_decl = self._render_breed(agent)
                if breed_decl:
                    lines.append(breed_decl)
                state_decl = self._render_agent_state(agent)
                if state_decl:
                    lines.append(state_decl)
            else:
                state_names = " ".join(field.name for field in agent.state_fields)
                if state_names:
                    lines.append(f"turtles-own [{state_names}]")

        return lines

    def _render_breed(self, agent: AgentSpec) -> str | None:
        """Render breed declaration for a specialized agent."""
        if not agent.breed:
            return None
        plural = agent.breed
        singular = agent.identifier.lower().replace(" ", "-")
        return f"breed [{plural} {singular}]"

    def _render_agent_state(self, agent: AgentSpec) -> str | None:
        """Render state fields for a breed."""
        if not agent.state_fields:
            return None
        state_fields = " ".join(field.name for field in agent.state_fields)
        if not state_fields:
            return None
        return f"{agent.breed}-own [{state_fields}]"

    def _render_setup(self) -> List[str]:
        lines = ["to setup", "  clear-all"]

        seed_cfg = self.model.random_seed_strategy
        if seed_cfg.strategy == "fixed" and seed_cfg.value is not None:
            lines.append(f"  random-seed {seed_cfg.value}")

        for agent in self.model.agents:
            lines.append(f"  ; TODO: instantiate {agent.identifier}")

        for agent in self.model.agents:
            for behavior in agent.behaviors:
                if (behavior.schedule_phase == SchedulePhase.SETUP and 
                    behavior.context == ExecutionContext.OBSERVER):
                    lines.append(f"  {behavior.name}")
        
        for agent in self.model.agents:
            turtle_setups = [
                b for b in agent.behaviors
                if b.schedule_phase == SchedulePhase.SETUP and
                   b.context == ExecutionContext.TURTLE
            ]
            if turtle_setups:
                target = agent.breed or "turtles"
                lines.append(f"  ask {target} [")
                for behavior in turtle_setups:
                    for statement in behavior.statements:
                        if isinstance(statement, RawStatement):
                            agent_fields = {field.name for field in agent.state_fields}
                            translated = translate_statement(statement.source, agent_fields)
                            lines.append(f"    {translated}")
                lines.append("  ]")

        lines.append("  reset-ticks")
        lines.append("end")
        return lines

    def _render_go(self) -> List[str]:
        lines = ["to go"]
        
        for agent in self.model.agents:
            turtle_behaviors = [
                b for b in agent.behaviors 
                if b.schedule_phase == SchedulePhase.TICK and 
                   b.context == ExecutionContext.TURTLE
            ]
            
            if turtle_behaviors:
                target = agent.breed or "turtles"
                lines.append(f"  ask {target} [")
                for behavior in turtle_behaviors:
                    for statement in behavior.statements:
                        if isinstance(statement, RawStatement):
                            agent_fields = {field.name for field in agent.state_fields}
                            translated = translate_statement(statement.source, agent_fields)
                            lines.append(f"    {translated}")
                lines.append("  ]")
        
        for agent in self.model.agents:
            for behavior in agent.behaviors:
                if behavior.context == ExecutionContext.OBSERVER:
                    if "update" in behavior.name or "stats" in behavior.name:
                        lines.append(f"  {behavior.name}")
        
        lines.append("  tick")
        lines.append("end")
        return lines

    def _render_behavior(self, agent: AgentSpec, behavior: AgentBehavior) -> List[str]:
        lines = [f"to {self._behavior_procedure(agent, behavior)}"]

        agent_fields = {field.name for field in agent.state_fields}

        for statement in behavior.statements:
            if isinstance(statement, RawStatement):
                translated = translate_statement(statement.source, agent_fields)
                lines.append(f"  {translated}")
            else:  # pragma: no cover - future extensions
                lines.append("  ; unsupported statement")
        lines.append("end")
        return lines

    def _render_reporter(self, reporter: Reporter) -> list[str]:
        """Render a to-report procedure."""
        name = reporter.name.lower().replace(" ", "-")
        if not name:
            return []
        lines = [f"to-report {name}"]
        expression = reporter.expression.strip()
        if expression:
            lines.append(f"  report {expression}")
        else:
            lines.append("  report 0")
        lines.append("end")
        return lines

    def _behavior_procedure(self, agent: AgentSpec, behavior: AgentBehavior) -> str:
        if behavior.context == ExecutionContext.OBSERVER:
            return behavior.name
        
        if agent.breed:
            return f"{agent.breed}-{behavior.name}"
        
        return behavior.name


def _default_widgets() -> List[str]:
    """XML markup for default setup/go buttons."""
    return [
        """
    <button x="10" y="10" height="30" width="90" forever="false" kind="Observer">setup</button>
        """.strip(),
        """
    <button x="110" y="10" height="30" width="90" forever="true" kind="Observer">go</button>
        """.strip(),
    ]
