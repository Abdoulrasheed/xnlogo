"""UI components API for xnlogo models.

Gradio-inspired declarative API for defining NetLogo interface widgets.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class View:
    """Main visualization view of the NetLogo world."""

    x: int = 765
    y: int = 0
    width: int = 510
    height: int = 510
    min_pxcor: int = -50
    max_pxcor: int = 50
    min_pycor: int = -50
    max_pycor: int = 50
    patch_size: float = 5.0
    frame_rate: float = 20.0
    wrapping_allowed_x: bool = True
    wrapping_allowed_y: bool = True
    show_tick_counter: bool = True
    tick_counter_label: str = "ticks"
    font_size: int = 10
    update_mode: int = 1  # 0=continuous, 1=on-ticks

    def to_xml(self) -> str:
        """Generate NetLogo XML for view widget."""
        return f'''<view x="{self.x}" wrappingAllowedX="{str(self.wrapping_allowed_x).lower()}" y="{self.y}" frameRate="{self.frame_rate}" minPycor="{self.min_pycor}" height="{self.height}" showTickCounter="{str(self.show_tick_counter).lower()}" patchSize="{self.patch_size}" fontSize="{self.font_size}" wrappingAllowedY="{str(self.wrapping_allowed_y).lower()}" width="{self.width}" tickCounterLabel="{self.tick_counter_label}" maxPycor="{self.max_pycor}" updateMode="{self.update_mode}" maxPxcor="{self.max_pxcor}" minPxcor="{self.min_pxcor}"></view>'''


@dataclass
class Button:
    """Button widget for executing commands."""

    command: str
    x: int = 10
    y: int = 10
    width: int = 90
    height: int = 30
    forever: bool = False
    kind: str = "Observer"  # Observer, Turtle, Patch
    disable_until_ticks: bool = False

    def to_xml(self) -> str:
        """Generate NetLogo XML for button widget."""
        return f'''<button x="{self.x}" y="{self.y}" height="{self.height}" disableUntilTicks="{str(self.disable_until_ticks).lower()}" forever="{str(self.forever).lower()}" kind="{self.kind}" width="{self.width}">{self.command}</button>'''


@dataclass
class Switch:
    """Boolean switch widget."""

    variable: str
    x: int = 10
    y: int = 10
    width: int = 150
    height: int = 40
    default: bool = False
    label: Optional[str] = None

    def to_xml(self) -> str:
        """Generate NetLogo XML for switch widget."""
        display_label = self.label or self.variable
        return f'''<switch x="{self.x}" y="{self.y}" height="{self.height}" on="{str(self.default).lower()}" variable="{self.variable}" width="{self.width}" display="{display_label}"></switch>'''


@dataclass
class Slider:
    """Numeric slider widget."""

    variable: str
    min_value: float = 0.0
    max_value: float = 100.0
    default: float = 50.0
    step: float = 1.0
    x: int = 10
    y: int = 10
    width: int = 150
    height: int = 40
    label: Optional[str] = None
    units: Optional[str] = None

    def to_xml(self) -> str:
        """Generate NetLogo XML for slider widget."""
        display_label = self.label or self.variable
        units_str = f' units="{self.units}"' if self.units else ""
        return f'''<slider x="{self.x}" y="{self.y}" height="{self.height}" min="{self.min_value}" max="{self.max_value}" default="{self.default}" step="{self.step}" variable="{self.variable}" width="{self.width}" display="{display_label}"{units_str}></slider>'''


@dataclass
class Monitor:
    """Display widget for showing values."""

    variable: Optional[str] = None
    expression: Optional[str] = None
    label: Optional[str] = None
    x: int = 10
    y: int = 10
    width: int = 100
    height: int = 60
    precision: int = 17
    font_size: int = 11

    def to_xml(self) -> str:
        """Generate NetLogo XML for monitor widget."""
        if self.expression:
            # Monitor with custom expression
            display_attr = f' display="{self.label}"' if self.label else ""
            return f'''<monitor x="{self.x}" precision="{self.precision}" y="{self.y}" height="{self.height}" fontSize="{self.font_size}" width="{self.width}"{display_attr}><![CDATA[{self.expression}]]></monitor>'''
        else:
            # Simple variable monitor
            return f'''<monitor x="{self.x}" precision="{self.precision}" y="{self.y}" height="{self.height}" fontSize="{self.font_size}" width="{self.width}">{self.variable}</monitor>'''


@dataclass
class PlotPen:
    """A pen within a plot for drawing specific data."""

    name: str
    color: str = "black"  # NetLogo color name or RGB
    mode: int = 0  # 0=line, 1=bar, 2=point
    interval: float = 1.0
    update: str = ""
    setup: str = ""

    def to_xml(self) -> str:
        """Generate NetLogo XML for plot pen."""
        # Convert color names to NetLogo color codes
        color_map = {
            "black": "-16777216",
            "white": "-1",
            "gray": "-7500403",
            "red": "-2674135",
            "orange": "-8053223",
            "brown": "-16449023",
            "yellow": "-1184463",
            "green": "-10899396",
            "lime": "-13840069",
            "turquoise": "-11221820",
            "cyan": "-11033397",
            "sky": "-7858428",
            "blue": "-13345367",
            "violet": "-8630108",
            "magenta": "-5825686",
            "pink": "-2064490",
        }
        color_code = color_map.get(self.color.lower(), self.color)

        return f'''<pen interval="{self.interval}" mode="{self.mode}" display="{self.name}" color="{color_code}" legend="true">
        <setup>{self.setup}</setup>
        <update><![CDATA[{self.update}]]></update>
      </pen>'''


@dataclass
class Plot:
    """2D plot widget for visualization."""

    title: str
    x: int = 10
    y: int = 10
    width: int = 400
    height: int = 250
    x_axis: str = "time"
    y_axis: str = "value"
    x_min: float = 0.0
    x_max: float = 10.0
    y_min: float = 0.0
    y_max: float = 10.0
    auto_plot_x: bool = True
    auto_plot_y: bool = True
    legend: bool = True
    pens: List[PlotPen] = field(default_factory=list)

    def to_xml(self) -> str:
        """Generate NetLogo XML for plot widget."""
        pens_xml = "\n      ".join(pen.to_xml() for pen in self.pens)

        return f'''<plot x="{self.x}" autoPlotX="{str(self.auto_plot_x).lower()}" yMax="{self.y_max}" autoPlotY="{str(self.auto_plot_y).lower()}" yAxis="{self.y_axis}" y="{self.y}" xMin="{self.x_min}" height="{self.height}" legend="{str(self.legend).lower()}" xMax="{self.x_max}" yMin="{self.y_min}" width="{self.width}" xAxis="{self.x_axis}" display="{self.title}">
      <setup></setup>
      <update></update>
      {pens_xml}
    </plot>'''


@dataclass
class Chooser:
    """Dropdown chooser widget."""

    variable: str
    choices: List[str]
    default: int = 0
    x: int = 10
    y: int = 10
    width: int = 150
    height: int = 40
    label: Optional[str] = None

    def to_xml(self) -> str:
        """Generate NetLogo XML for chooser widget."""
        display_label = self.label or self.variable
        choices_str = " ".join(f'"{choice}"' for choice in self.choices)
        return f'''<chooser x="{self.x}" y="{self.y}" height="{self.height}" variable="{self.variable}" width="{self.width}" display="{display_label}">
      <choices>{choices_str}</choices>
      <default>{self.default}</default>
    </chooser>'''


@dataclass
class TextBox:
    """Text input/output widget."""

    variable: Optional[str] = None
    text: str = ""
    x: int = 10
    y: int = 10
    width: int = 300
    height: int = 100
    font_size: int = 12
    color: str = "black"
    transparent: bool = False

    def to_xml(self) -> str:
        """Generate NetLogo XML for textbox widget."""
        return f'''<textbox x="{self.x}" y="{self.y}" height="{self.height}" fontSize="{self.font_size}" width="{self.width}" color="{self.color}" transparent="{str(self.transparent).lower()}">{self.text}</textbox>'''


@dataclass
class Interface:
    """Complete interface specification for a NetLogo model.

    Gradio-inspired container for all UI widgets.

    Example:
        interface = Interface(
            view=View(width=600, height=600),
            buttons=[
                Button(label="setup", x=10, y=10),
                Button(label="go", x=110, y=10, forever=True),
            ],
            sliders=[
                Slider(variable="population", min_value=0, max_value=500, default=100),
            ],
            monitors=[
                Monitor(variable="count turtles"),
            ],
        )
    """

    title: str = "Agent-Based Model"
    view: Optional[View] = None
    buttons: List[Button] = field(default_factory=list)
    switches: List[Switch] = field(default_factory=list)
    sliders: List[Slider] = field(default_factory=list)
    monitors: List[Monitor] = field(default_factory=list)
    plots: List[Plot] = field(default_factory=list)
    choosers: List[Chooser] = field(default_factory=list)
    textboxes: List[TextBox] = field(default_factory=list)

    def to_widget_list(self) -> List[str]:
        """Convert all widgets to XML strings for compilation."""
        widgets: List[str] = []

        if self.view:
            widgets.append(self.view.to_xml())

        for widget_list in [
            self.plots,
            self.buttons,
            self.switches,
            self.sliders,
            self.monitors,
            self.choosers,
            self.textboxes,
        ]:
            for widget in widget_list:
                widgets.append(widget.to_xml())

        return widgets


# Convenience exports
__all__ = [
    "View",
    "Button",
    "Switch",
    "Slider",
    "Monitor",
    "Plot",
    "PlotPen",
    "Chooser",
    "TextBox",
    "Interface",
]
