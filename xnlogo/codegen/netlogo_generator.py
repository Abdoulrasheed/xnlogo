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

        # Check if user has defined their own go method
        user_go_behavior = None
        for agent in self.model.agents:
            for behavior in agent.behaviors:
                if (
                    behavior.name == "go"
                    and behavior.schedule_phase == SchedulePhase.TICK
                    and behavior.context == ExecutionContext.OBSERVER
                ):
                    user_go_behavior = (agent, behavior)
                    break
            if user_go_behavior:
                break

        if user_go_behavior:
            # Render user's go method as the main go procedure
            blocks.append(
                self._render_behavior(user_go_behavior[0], user_go_behavior[1])
            )
        else:
            # Render default go procedure
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
                elif (
                    behavior.schedule_phase == SchedulePhase.SETUP
                    and behavior.context == ExecutionContext.OBSERVER
                ):
                    blocks.append(self._render_behavior(agent, behavior))
                elif (
                    behavior.schedule_phase == SchedulePhase.TICK
                    and behavior.context == ExecutionContext.OBSERVER
                    and behavior.name != "go"
                ):
                    blocks.append(self._render_behavior(agent, behavior))
                elif (
                    behavior.schedule_phase == SchedulePhase.TICK
                    and behavior.context == ExecutionContext.TURTLE
                ):
                    blocks.append(self._render_behavior(agent, behavior))

        return "\n\n".join("\n".join(block) for block in blocks if block).strip() + "\n"

    def widgets(self) -> List[str]:
        """Return serialized widget XML snippets."""
        widgets: List[str] = []
        for widget in self.model.widgets:
            if isinstance(widget, dict):
                # Convert dictionary widget to XML
                widget_xml = self._widget_dict_to_xml(widget)
                if widget_xml:
                    widgets.append(widget_xml)
            elif isinstance(widget, str):
                # Check if this is a widget placeholder comment
                if widget.startswith("<!-- WIDGET:") and widget.endswith("-->"):
                    # Extract and evaluate the widget code
                    widget_code = widget[12:-4].strip()  # Remove <!-- WIDGET: and -->
                    evaluated_widget = self._evaluate_widget(widget_code)
                    if evaluated_widget:
                        widgets.append(evaluated_widget)
                else:
                    widgets.append(widget)
        if self.options.default_widgets and not widgets:
            widgets.extend(_default_widgets())
        return widgets

    def _widget_dict_to_xml(self, widget_dict: dict) -> Optional[str]:
        """Convert a widget dictionary to NetLogo XML."""
        widget_type = widget_dict.get("type")
        args = widget_dict.get("args", {})

        if widget_type == "View":
            return self._generate_view_xml(args)
        elif widget_type == "Button":
            return self._generate_button_xml(args)
        elif widget_type == "Monitor":
            return self._generate_monitor_xml(args)
        elif widget_type == "Switch":
            return self._generate_switch_xml(args)
        elif widget_type == "Slider":
            return self._generate_slider_xml(args)
        elif widget_type == "Plot":
            return self._generate_plot_xml(args, widget_dict)
        elif widget_type == "TextBox":
            return self._generate_textbox_xml(args)

        return None

    def _generate_view_xml(self, args: dict) -> str:
        """Generate XML for View widget."""
        x = args.get("x", 210)
        y = args.get("y", 10)
        width = args.get("width", 510)
        height = args.get("height", 510)
        min_pxcor = args.get("min_pxcor", -16)
        max_pxcor = args.get("max_pxcor", 16)
        min_pycor = args.get("min_pycor", -16)
        max_pycor = args.get("max_pycor", 16)
        patch_size = args.get("patch_size", 13.0)
        font_size = args.get("font_size", 10)
        frame_rate = args.get("frame_rate", 30.0)
        wrapping_x = args.get("wrapping_x", True)
        wrapping_y = args.get("wrapping_y", True)
        show_tick_counter = args.get("show_tick_counter", True)
        tick_counter_label = args.get("tick_counter_label", "ticks")
        update_mode = args.get("update_mode", 0)

        wrapping_x_str = "true" if wrapping_x else "false"
        wrapping_y_str = "true" if wrapping_y else "false"
        show_tick_str = "true" if show_tick_counter else "false"

        return (
            f'<view x="{x}" wrappingAllowedX="{wrapping_x_str}" y="{y}" '
            f'frameRate="{frame_rate}" minPycor="{min_pycor}" height="{height}" '
            f'showTickCounter="{show_tick_str}" patchSize="{patch_size}" '
            f'fontSize="{font_size}" wrappingAllowedY="{wrapping_y_str}" '
            f'width="{width}" tickCounterLabel="{tick_counter_label}" '
            f'maxPycor="{max_pycor}" updateMode="{update_mode}" '
            f'maxPxcor="{max_pxcor}" minPxcor="{min_pxcor}"></view>'
        )

    def _generate_button_xml(self, args: dict) -> str:
        """Generate XML for Button widget."""
        command = args.get("command", "")
        x = args.get("x", 10)
        y = args.get("y", 10)
        width = args.get("width", 100)
        height = args.get("height", 30)
        forever = args.get("forever", False)
        kind = args.get("kind", "Observer")
        disable_until_ticks = args.get("disable_until_ticks", False)

        forever_str = "true" if forever else "false"
        disable_str = "true" if disable_until_ticks else "false"

        return (
            f'<button x="{x}" y="{y}" height="{height}" '
            f'disableUntilTicks="{disable_str}" forever="{forever_str}" '
            f'kind="{kind}" width="{width}">{command}</button>'
        )

    def _generate_monitor_xml(self, args: dict) -> str:
        """Generate XML for Monitor widget."""
        expression = args.get("expression", "")
        x = args.get("x", 10)
        y = args.get("y", 10)
        width = args.get("width", 100)
        height = args.get("height", 60)
        precision = args.get("precision", 17)
        font_size = args.get("font_size", 11)
        display = args.get("display")

        if display:
            return (
                f'<monitor x="{x}" precision="{precision}" y="{y}" '
                f'height="{height}" fontSize="{font_size}" width="{width}" '
                f'display="{display}"><![CDATA[{expression}]]></monitor>'
            )
        else:
            return (
                f'<monitor x="{x}" precision="{precision}" y="{y}" '
                f'height="{height}" fontSize="{font_size}" '
                f'width="{width}">{expression}</monitor>'
            )

    def _generate_switch_xml(self, args: dict) -> str:
        """Generate XML for Switch widget."""
        variable = args.get("variable", "")
        x = args.get("x", 10)
        y = args.get("y", 10)
        width = args.get("width", 100)
        height = args.get("height", 40)
        default = args.get("default", False)
        display = args.get("display", variable)

        default_str = "true" if default else "false"

        return (
            f'<switch x="{x}" y="{y}" height="{height}" on="{default_str}" '
            f'variable="{variable}" width="{width}" display="{display}"></switch>'
        )

    def _generate_slider_xml(self, args: dict) -> str:
        """Generate XML for Slider widget."""
        variable = args.get("variable", "")
        x = args.get("x", 10)
        y = args.get("y", 10)
        width = args.get("width", 150)
        height = args.get("height", 40)
        min_val = args.get("min_val", 0)
        max_val = args.get("max_val", 100)
        default = args.get("default", 50)
        step = args.get("step", 1)
        units = args.get("units", "")
        direction = args.get("direction", "horizontal")
        display = args.get("display", variable)

        direction_str = "HORIZONTAL" if direction == "horizontal" else "VERTICAL"

        return (
            f'<slider x="{x}" y="{y}" height="{height}" variable="{variable}" '
            f'min="{min_val}" max="{max_val}" default="{default}" step="{step}" '
            f'units="{units}" direction="{direction_str}" width="{width}" '
            f'display="{display}"></slider>'
        )

    def _generate_plot_xml(self, args: dict, widget_dict: dict) -> str:
        """Generate XML for Plot widget."""
        name = args.get("name", "plot")
        x = args.get("x", 10)
        y = args.get("y", 10)
        width = args.get("width", 400)
        height = args.get("height", 250)
        x_axis = args.get("x_axis", "Time")
        y_axis = args.get("y_axis", "Value")
        x_min = args.get("x_min", 0.0)
        x_max = args.get("x_max", 10.0)
        y_min = args.get("y_min", 0.0)
        y_max = args.get("y_max", 10.0)
        auto_plot_x = args.get("auto_plot_x", True)
        auto_plot_y = args.get("auto_plot_y", True)
        show_legend = args.get("show_legend", True)

        auto_x_str = "true" if auto_plot_x else "false"
        auto_y_str = "true" if auto_plot_y else "false"
        legend_str = "true" if show_legend else "false"

        xml = (
            f'<plot x="{x}" autoPlotX="{auto_x_str}" yMax="{y_max}" '
            f'autoPlotY="{auto_y_str}" yAxis="{y_axis}" y="{y}" '
            f'xMin="{x_min}" height="{height}" legend="{legend_str}" '
            f'xMax="{x_max}" yMin="{y_min}" width="{width}" '
            f'xAxis="{x_axis}" display="{name}">\n'
        )
        xml += "      <setup></setup>\n"
        xml += "      <update></update>\n"

        # Add pens from widget_dict (not args!)
        pens = widget_dict.get("pens", [])
        for pen in pens:
            xml += self._generate_plot_pen_xml(pen)

        xml += "    </plot>"
        return xml

    def _generate_plot_pen_xml(self, pen_dict: dict) -> str:
        """Generate XML for PlotPen."""
        name = pen_dict.get("name", "default")
        update_code = pen_dict.get("update_code", "")
        color = pen_dict.get("color", -16777216)
        mode = pen_dict.get("mode", 0)
        interval = pen_dict.get("interval", 1.0)
        show_in_legend = pen_dict.get("show_in_legend", True)

        legend_str = "true" if show_in_legend else "false"

        return (
            f'      <pen interval="{interval}" mode="{mode}" display="{name}" '
            f'color="{color}" legend="{legend_str}">\n'
            f"        <setup></setup>\n"
            f"        <update><![CDATA[{update_code}]]></update>\n"
            f"      </pen>\n"
        )

    def _generate_textbox_xml(self, args: dict) -> str:
        """Generate XML for TextBox widget."""
        text = args.get("text", "")
        x = args.get("x", 10)
        y = args.get("y", 10)
        width = args.get("width", 200)
        height = args.get("height", 100)
        font_size = args.get("font_size", 11)
        transparent = args.get("transparent", False)
        color = args.get("color", 0)

        transparent_str = "true" if transparent else "false"

        return (
            f'<textBox x="{x}" y="{y}" height="{height}" width="{width}" '
            f'fontSize="{font_size}" transparent="{transparent_str}" '
            f'color="{color}">{text}</textBox>'
        )

    def _evaluate_widget(self, widget_code: str) -> Optional[str]:
        """Evaluate widget constructor code and generate XML."""
        try:
            # Import the UI module
            from xnlogo.runtime import ui

            # Create a safe namespace for evaluation
            namespace = {
                "View": ui.View,
                "Button": ui.Button,
                "Switch": ui.Switch,
                "Slider": ui.Slider,
                "Monitor": ui.Monitor,
                "Plot": ui.Plot,
                "PlotPen": ui.PlotPen,
                "Chooser": ui.Chooser,
                "TextBox": ui.TextBox,
            }

            # Evaluate the widget constructor
            widget_obj = eval(widget_code, namespace)

            # Generate XML from the widget object
            if hasattr(widget_obj, "to_xml"):
                return widget_obj.to_xml()
        except Exception as e:
            # Log error but continue - widget will be skipped
            import sys

            print(
                f"Warning: Failed to evaluate widget '{widget_code}': {e}",
                file=sys.stderr,
            )

        return None

    def emit(self) -> str:
        template_name = (
            "base.nlogox.xml.j2" if self.options.format == "nlogox" else "base.nlogo.j2"
        )
        template = _TEMPLATE_ENV.get_template(template_name)
        return template.render(
            code=self.render(), widgets=self.widgets(), info_text=self.model.info_text
        )

    def _render_declarations(self) -> list[str]:
        """Render globals, patches-own, breeds, and turtles-own declarations."""
        lines: list[str] = []

        all_globals = list(self.model.globals)
        for agent in self.model.agents:
            for class_attr in agent.class_attributes:
                from xnlogo.ir.model import GlobalVar

                all_globals.append(
                    GlobalVar(name=class_attr.name, default=class_attr.default)
                )

        widget_globals = set()
        for widget_dict in self.model.widgets:
            widget_type = widget_dict.get("type", "")
            if widget_type in ("Switch", "Slider"):
                args = widget_dict.get("args", {})
                variable = args.get("variable")
                if variable:
                    widget_globals.add(variable)

        filtered_globals = [g for g in all_globals if g.name not in widget_globals]

        if filtered_globals:
            globals_list = " ".join(g.name for g in filtered_globals)
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

        if agent.breed.lower() == "turtles":
            return None

        plural = agent.breed
        singular = (
            agent.singular
            if agent.singular
            else agent.identifier.lower().replace(" ", "-")
        )

        if singular == plural:
            if plural.endswith("s"):
                singular = plural[:-1]
            else:
                singular = plural + "-one"

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
            for behavior in agent.behaviors:
                if (
                    behavior.schedule_phase == SchedulePhase.SETUP
                    and behavior.context == ExecutionContext.OBSERVER
                ):
                    lines.append(f"  {behavior.name}")

        for agent in self.model.agents:
            turtle_setups = [
                b
                for b in agent.behaviors
                if b.schedule_phase == SchedulePhase.SETUP
                and b.context == ExecutionContext.TURTLE
            ]
            if turtle_setups:
                target = agent.breed or "turtles"
                lines.append(f"  ask {target} [")
                for behavior in turtle_setups:
                    for statement in behavior.statements:
                        if isinstance(statement, RawStatement):
                            agent_fields = {field.name for field in agent.state_fields}
                            if getattr(statement, "is_netlogo", False):
                                translated = statement.source
                            else:
                                translated = translate_statement(
                                    statement.source, agent_fields
                                )
                            lines.append(f"    {translated}")
                lines.append("  ]")

        lines.append("  reset-ticks")
        lines.append("end")
        return lines

    def _render_go(self) -> List[str]:
        lines = ["to go"]

        for agent in self.model.agents:
            turtle_behaviors = [
                b
                for b in agent.behaviors
                if b.schedule_phase == SchedulePhase.TICK
                and b.context == ExecutionContext.TURTLE
            ]

            if turtle_behaviors:
                target = agent.breed or "turtles"
                lines.append(f"  ask {target} [")
                for behavior in turtle_behaviors:
                    for statement in behavior.statements:
                        if isinstance(statement, RawStatement):
                            agent_fields = {field.name for field in agent.state_fields}
                            if getattr(statement, "is_netlogo", False):
                                translated = statement.source
                            else:
                                translated = translate_statement(
                                    statement.source, agent_fields
                                )
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
        procedure_name = self._behavior_procedure(agent, behavior)
        if behavior.parameters:
            params_str = " ".join(behavior.parameters)
            signature = f"to {procedure_name} [{params_str}]"
        else:
            signature = f"to {procedure_name}"

        lines = [signature]

        agent_fields = {field.name for field in agent.state_fields}

        all_source = "\n".join(
            stmt.source
            for stmt in behavior.statements
            if isinstance(stmt, RawStatement) and not getattr(stmt, "is_netlogo", False)
        )

        from xnlogo.codegen.netlogo_translator import NetLogoTranslator

        translator = NetLogoTranslator()
        translator.agent_fields = agent_fields
        if all_source.strip():
            try:
                import ast

                tree = ast.parse(all_source)
                translator._analyze_local_variables(tree)
            except SyntaxError:
                pass

        for statement in behavior.statements:
            if isinstance(statement, RawStatement):
                if getattr(statement, "is_netlogo", False):
                    translated = statement.source
                else:
                    translated = translator.translate(statement.source, agent_fields)
                lines.append(f"  {translated}")
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
        return behavior.name


def _default_widgets() -> List[str]:
    return [
        '<button x="10" y="10" height="30" width="90" forever="false" kind="Observer">setup</button>',
        '<button x="110" y="10" height="30" width="90" forever="true" kind="Observer">go</button>',
    ]
