"""Convert IR into NetLogo artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from xnlogo.codegen.netlogo_translator import translate_statement
from xnlogo.ir.model import (
    AgentBehavior,
    AgentSpec,
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

        # Agent behaviors
        for agent in self.model.agents:
            for behavior in agent.behaviors:
                blocks.append(self._render_behavior(agent, behavior))

        return "\n\n".join("\n".join(block) for block in blocks if block).strip() + "\n"

    def widgets(self) -> List[str]:
        """Return serialized widget XML snippets."""
        widgets: List[str] = []
        for widget in self.model.widgets:
            if isinstance(widget, str):
                widgets.append(widget)
        if self.options.default_widgets:
            widgets.extend(_default_widgets())
        return widgets

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

        # global variables
        if self.model.globals:
            globals_list = " ".join(
                global_var.name for global_var in self.model.globals
            )
            if globals_list:
                lines.append(f"globals [{globals_list}]")

        # patches-own
        if self.model.patches.state_fields:
            patch_fields = " ".join(
                field.name for field in self.model.patches.state_fields
            )
            if patch_fields:
                lines.append(f"patches-own [{patch_fields}]")

        # breeds and their state
        for agent in self.model.agents:
            if agent.breed:
                breed_decl = self._render_breed(agent)
                if breed_decl:
                    lines.append(breed_decl)
                state_decl = self._render_agent_state(agent)
                if state_decl:
                    lines.append(state_decl)
            else:
                # generic turtles
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

        # random seed if configured
        seed_cfg = self.model.random_seed_strategy
        if seed_cfg.strategy == "fixed" and seed_cfg.value is not None:
            lines.append(f"  random-seed {seed_cfg.value}")

        # agent instantiation
        for agent in self.model.agents:
            lines.append(f"  ; TODO: instantiate {agent.identifier}")

        # SETUP phase behaviors
        for agent in self.model.agents:
            for behavior in agent.behaviors:
                if behavior.schedule_phase == SchedulePhase.SETUP:
                    procedure_name = self._behavior_procedure(agent, behavior)
                    target = agent.breed or "turtles"
                    lines.append(f"  ask {target} [ {procedure_name} ]")

        lines.append("  reset-ticks")
        lines.append("end")
        return lines

    def _render_go(self) -> List[str]:
        lines = ["to go"]
        for agent in self.model.agents:
            for behavior in agent.behaviors:
                if behavior.schedule_phase == SchedulePhase.TICK:
                    procedure_name = self._behavior_procedure(agent, behavior)
                    target = agent.breed or "turtles"
                    lines.append(f"  ask {target} [ {procedure_name} ]")
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
        agent_slug = agent.identifier.lower().replace(" ", "-")
        behavior_slug = behavior.name.lower().replace(" ", "-")
        return f"{agent_slug}-{behavior_slug}"


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
