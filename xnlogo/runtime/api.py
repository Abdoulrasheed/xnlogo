"""runtime api for agent-based modeling.

transpiles python agent definitions to netlogo and executes via runtime.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable, Type, TypeVar, Any, Optional

T = TypeVar("T")


# ============================================================================
# Model Class - Clean Entry Point
# ============================================================================


class Model:
    """Base class for agent-based models. Subclass this to create your model."""

    def __init__(self):
        """Initialize the model."""
        self._breeds = {}
        self._globals = {}
        self._setup_called = False
        self._ui_widgets = []  # Store UI widget definitions
        self._ui_info = ""  # Store info tab content

    def setup(self) -> None:
        """Override this to define model initialization."""
        pass

    def step(self) -> None:
        """Override this to define what happens each tick."""
        pass

    def reset(self) -> None:
        """Reset the model to initial state."""
        clear_all()
        reset_ticks()
        self.setup()

    def run(self, steps: int = 100) -> None:
        """Run the model for a number of steps."""
        if not self._setup_called:
            self.reset()
            self._setup_called = True

        for _ in range(steps):
            self.step()
            tick()

    def ui(self) -> None:
        """Override this to define the UI layout. Called during transpilation."""
        pass

    def info(self) -> str:
        """Override this to provide model documentation for the Info tab."""
        return ""

    def add_widget(self, widget: "UIWidget") -> None:
        """Add a UI widget to the model interface."""
        self._ui_widgets.append(widget)

    def set_info(self, info_text: str) -> None:
        """Set the Info tab content."""
        self._ui_info = info_text


# ============================================================================
# Model Structure API
# ============================================================================


class Globals:
    """Define global variables for the NetLogo model."""

    def __init__(self, **variables):
        """Initialize globals with name-value pairs."""
        self._variables = variables
        self._procedures = {}  # Store procedures defined on this object
        for name, value in variables.items():
            setattr(self, name, value)

    def procedure(self, fn: Callable) -> Callable:
        """Register an observer procedure (decorator for methods)."""
        self._procedures[fn.__name__] = fn
        fn._xnlogo_context = "observer"
        return fn

    def setup(self, fn: Callable) -> Callable:
        """Shorthand for setup procedure."""
        return self.procedure(fn)

    def step(self, fn: Callable) -> Callable:
        """Shorthand for go/step procedure."""
        return self.procedure(fn)

    def __repr__(self) -> str:
        return f"Globals({', '.join(f'{k}={v!r}' for k, v in self._variables.items())})"


def globals(**variables) -> Globals:
    """Declare global variables for the model.

    Example:
        model = globals(
            population=1000,
            infection_rate=0.35,
            total_deaths=0
        )

        @model.setup
        def initialize():
            model.population = 1000
    """
    return Globals(**variables)


class Breed:
    """Define a turtle breed."""

    def __init__(self, name: str, singular: str | None = None, **own_variables):
        """Initialize a breed.

        Args:
            name: Plural name of the breed (e.g., "people")
            singular: Singular name (e.g., "person"), defaults to name[:-1]
            **own_variables: Instance variables for this breed
        """
        self.name = name
        self.singular = singular or (name[:-1] if name.endswith("s") else name)
        self._own_variables = own_variables
        self._behaviors = {}  # Store turtle procedures
        for var_name, value in own_variables.items():
            setattr(self, var_name, value)

    def behavior(self, fn: Callable) -> Callable:
        """Register a turtle behavior (decorator for methods).

        Example:
            @people.behavior
            def move():
                me.move_forward()
        """
        self._behaviors[fn.__name__] = fn
        fn._xnlogo_context = "turtle"
        fn._xnlogo_breed = self.name
        return fn

    def create(self, n: int, action: Callable | None = None) -> None:
        """Create n new agents of this breed.

        Example:
            people.create(100, lambda: (
                me.set_color("blue"),
                me.set_size(1.5)
            ))
        """
        sprout(n, action)

    def all(self) -> AgentSet:
        """Get all agents of this breed."""
        return breed_agentset(self.name)

    def __repr__(self) -> str:
        return f"Breed({self.name!r}, singular={self.singular!r})"


def breed(name: str, singular: str | None = None, **own_variables) -> Breed:
    """Declare a turtle breed with its own variables.

    Example:
        people = breed("people", "person",
            infected_time=0,
            antibodies=0,
            group="",
            isolating=False
        )
    """
    return Breed(name, singular, **own_variables)


class World:
    """World configuration."""

    def __init__(
        self,
        min_pxcor: int = -50,
        max_pxcor: int = 50,
        min_pycor: int = -50,
        max_pycor: int = 50,
        wrapping_x: bool = True,
        wrapping_y: bool = True,
        patch_size: float = 13.0,
    ):
        """Configure the world dimensions and behavior."""
        self.min_pxcor = min_pxcor
        self.max_pxcor = max_pxcor
        self.min_pycor = min_pycor
        self.max_pycor = max_pycor
        self.wrapping_x = wrapping_x
        self.wrapping_y = wrapping_y
        self.patch_size = patch_size


def world(
    min_pxcor: int = -50,
    max_pxcor: int = 50,
    min_pycor: int = -50,
    max_pycor: int = 50,
    wrapping_x: bool = True,
    wrapping_y: bool = True,
    patch_size: float = 13.0,
) -> World:
    """Configure world dimensions.

    Example:
        w = world(min_pxcor=-50, max_pxcor=50, min_pycor=-50, max_pycor=50)
    """
    return World(
        min_pxcor, max_pxcor, min_pycor, max_pycor, wrapping_x, wrapping_y, patch_size
    )


def observer(fn: Callable) -> Callable:
    fn._xnlogo_context = "observer"
    return fn


def turtle(fn: Callable) -> Callable:
    fn._xnlogo_context = "turtle"
    return fn


def patch(fn: Callable) -> Callable:
    fn._xnlogo_context = "patch"
    return fn


def agent(
    cls: Type[T] | None = None, **kwargs
) -> Type[T] | Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        cls._xnlogo_agent = True
        cls._xnlogo_kwargs = kwargs
        return cls

    if cls is None:
        return decorator
    else:
        return decorator(cls)


def run(source_file: Path | str, steps: int = 100, headless: bool = True) -> None:
    """compile and execute python model in netlogo."""
    from xnlogo.compiler import build_artifact
    from xnlogo.runtime.session import NetLogoSession, SessionConfig

    source_path = Path(source_file)
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        result, artifact_path = build_artifact(
            source_path, fmt="nlogox", output_dir=tmp_path
        )

        if result.diagnostics.has_errors():
            for diag in result.diagnostics.errors:
                print(f"Error: {diag.message}")
            raise RuntimeError("Compilation failed. See errors above.")

        if artifact_path is None:
            raise RuntimeError("Failed to generate NetLogo artifact")

        config = SessionConfig(headless=headless)
        with NetLogoSession(config) as session:
            session.load_model(artifact_path)
            session.command("setup")
            session.repeat("go", steps)

            try:
                tick_count = session.report("ticks")
                turtle_count = session.report("count turtles")
                print(
                    f"Simulation completed: {tick_count} ticks, {turtle_count} turtles"
                )
            except Exception:
                pass


# ============================================================================
# NetLogo Primitive Functions (Stubs for transpilation)
# These are placeholder implementations that get transpiled to NetLogo code
# ============================================================================


# World & Observer Primitives
def clear_all() -> None:
    """Clear the world and reset all agents."""
    pass


def clear_turtles() -> None:
    """Remove all turtles."""
    pass


def clear_patches() -> None:
    """Reset all patches to default state."""
    pass


def clear_drawing() -> None:
    """Clear all pen drawings."""
    pass


def reset_ticks() -> None:
    """Reset the tick counter to zero."""
    pass


def tick() -> None:
    """Advance the tick counter by one."""
    pass


def ticks() -> int:
    """Get the current tick count."""
    return 0


# Agentset Primitives
def turtles() -> AgentSet:
    """Get the agentset of all turtles."""
    return AgentSet("turtles")


def patches() -> AgentSet:
    """Get the agentset of all patches."""
    return AgentSet("patches")


def links() -> AgentSet:
    """Get the agentset of all links."""
    return AgentSet("links")


def breed_agentset(name: str) -> AgentSet:
    """Get the agentset of a specific breed."""
    return AgentSet(f"breed:{name}")


def other(agentset: Any) -> Any:
    """Get all agents except the caller."""
    pass


def self_agent() -> Any:
    """Get the agent executing this code."""
    pass


def myself() -> Any:
    """Get the agent that asked this agent to execute code."""
    pass


# ============================================================================
# Pythonic Agentset API (abstracts NetLogo complexity)
# ============================================================================


class AgentSet:
    """Pythonic wrapper for NetLogo agentsets."""

    def __init__(self, _type: str = "turtles"):
        self._type = _type
        self._filters = []

    def filter(self, **conditions) -> "AgentSet":
        """Filter agents by conditions.

        Examples:
            turtles().filter(color="red", infected=True)
            patches().filter(pcolor__gt=5)  # pcolor > 5
            turtles().filter(energy__lte=10)  # energy <= 10
        """
        new_set = AgentSet(self._type)
        new_set._filters = self._filters.copy()
        new_set._filters.append(conditions)
        return new_set

    def sample(self, n: int) -> "AgentSet":
        """Randomly select n agents."""
        return n_of(n, self)

    def one(self) -> Any:
        """Randomly select one agent."""
        return one_of(self)

    def min_by(self, attribute: str) -> Any:
        """Get agent with minimum value of attribute."""
        return min_one_of(self, attribute)

    def max_by(self, attribute: str) -> Any:
        """Get agent with maximum value of attribute."""
        return max_one_of(self, attribute)

    def count(self) -> int:
        """Count agents in this set."""
        return count(self)

    def any(self) -> bool:
        """Check if any agents exist."""
        return any_agents(self)

    def all(self, condition: str) -> bool:
        """Check if all agents satisfy condition."""
        return all_agents(self, condition)

    def nearby(self, distance: float) -> "AgentSet":
        """Get agents within distance (turtle context)."""
        return in_radius(distance)

    def in_cone(self, distance: float, angle: float) -> "AgentSet":
        """Get agents in cone of vision (turtle context)."""
        return in_cone(distance, angle)

    def do(self, action: Callable) -> None:
        """Execute action for each agent (pythonic ask)."""
        ask(self, action)

    def __iter__(self):
        """Make agentset iterable (for future expansion)."""
        return iter([])


# Agentset Selection (low-level, used internally)
def n_of(n: int, agentset: Any) -> Any:
    """Randomly select n agents from the agentset."""
    pass


def one_of(agentset: Any) -> Any:
    """Randomly select one agent from the agentset."""
    pass


def max_one_of(agentset: Any, reporter: str) -> Any:
    """Select the agent with the maximum value."""
    pass


def min_one_of(agentset: Any, reporter: str) -> Any:
    """Select the agent with the minimum value."""
    pass


def max_n_of(n: int, agentset: Any, reporter: str) -> Any:
    """Select the n agents with the highest values."""
    pass


def min_n_of(n: int, agentset: Any, reporter: str) -> Any:
    """Select the n agents with the lowest values."""
    pass


def with_expr(agentset: Any, condition: str) -> Any:
    """Filter agentset by condition."""
    pass


# Agentset Queries
def count(agentset: Any) -> int:
    """Count the number of agents in the agentset."""
    return 0


def any_agents(agentset: Any) -> bool:
    """Check if agentset has any agents."""
    return False


def all_agents(agentset: Any, condition: str) -> bool:
    """Check if all agents satisfy condition."""
    return False


# Commands
def ask(agentset: Any, commands: Callable) -> None:
    """Execute commands for each agent in the agentset."""
    pass


# ============================================================================
# Pythonic Turtle/Patch API (context-aware)
# ============================================================================


class Agent:
    """Represents the current turtle/patch in turtle/patch context."""

    def move_forward(self, distance: float = 1) -> None:
        """Move forward by distance."""
        forward(distance)

    def move_back(self, distance: float = 1) -> None:
        """Move backward by distance."""
        back(distance)

    def turn_left(self, angle: float) -> None:
        """Turn left by angle degrees."""
        left(angle)

    def turn_right(self, angle: float) -> None:
        """Turn right by angle degrees."""
        right(angle)

    def face_towards(self, target: Any) -> None:
        """Turn to face target."""
        face(target)

    def move_to(self, x: float, y: float) -> None:
        """Move to coordinates."""
        setxy(x, y)

    def distance_to(self, target: Any) -> float:
        """Get distance to target."""
        return distance(target)

    def die(self) -> None:
        """Remove this agent."""
        die()

    @property
    def x(self) -> float:
        """Get x coordinate."""
        return xcor()

    @property
    def y(self) -> float:
        """Get y coordinate."""
        return ycor()

    @property
    def heading(self) -> float:
        """Get heading."""
        return heading()

    @property
    def patch(self) -> Any:
        """Get patch at current location."""
        return patch_here()

    def neighbors_within(self, distance: float) -> AgentSet:
        """Get agents within distance."""
        return other(turtles()).nearby(distance)


me = Agent()


def create_turtles(n: int, action: Callable | None = None) -> None:
    """Create n turtles and optionally execute action for each.

    Example:
        create_turtles(100, lambda: me.set_color("blue"))
    """
    pass


def randomly_distribute(agentset: AgentSet, action: Callable | None = None) -> None:
    """Distribute agents randomly across patches.

    Example:
        randomly_distribute(patches().sample(50), lambda: people.create(1))
    """
    ask(agentset, action if action else lambda: None)


def every_patch(action: Callable) -> None:
    """Execute action for every patch.

    Example:
        every_patch(lambda: me.set_pcolor("green"))
    """
    ask(patches(), action)


def every_turtle(action: Callable) -> None:
    """Execute action for every turtle.

    Example:
        every_turtle(lambda: me.move_forward())
    """
    ask(turtles(), action)


def sprout(n: int, commands: Optional[Callable] = None) -> None:
    """Create n new turtles on this patch."""
    pass


def hatch(n: int, commands: Optional[Callable] = None) -> None:
    """Create n clones of this turtle."""
    pass


def die() -> None:
    """Remove this agent from the simulation."""
    pass


# Movement
def forward(distance: float) -> None:
    """Move forward by distance."""
    pass


def fd(distance: float) -> None:
    """Alias for forward."""
    pass


def back(distance: float) -> None:
    """Move backward by distance."""
    pass


def bk(distance: float) -> None:
    """Alias for back."""
    pass


def left(angle: float) -> None:
    """Turn left by angle degrees."""
    pass


def lt(angle: float) -> None:
    """Alias for left."""
    pass


def right(angle: float) -> None:
    """Turn right by angle degrees."""
    pass


def rt(angle: float) -> None:
    """Alias for right."""
    pass


def face(agent: Any) -> None:
    """Turn to face the specified agent."""
    pass


def facexy(x: float, y: float) -> None:
    """Turn to face the coordinates."""
    pass


def setxy(x: float, y: float) -> None:
    """Move to the specified coordinates."""
    pass


def move_to(agent: Any) -> None:
    """Move to the same location as the agent."""
    pass


# Patch Navigation
def patch_here() -> Any:
    """Get the patch at the turtle's current location."""
    pass


def patch_at(dx: float, dy: float) -> Any:
    """Get the patch at relative coordinates."""
    pass


def patch_ahead(distance: float) -> Any:
    """Get the patch ahead at the specified distance."""
    pass


def neighbors() -> Any:
    """Get the 8 surrounding patches."""
    pass


def neighbors4() -> Any:
    """Get the 4 surrounding patches."""
    pass


# Spatial Queries
def in_radius(distance: float) -> Any:
    """Get agents within the specified radius."""
    pass


def in_cone(distance: float, angle: float) -> Any:
    """Get agents in a cone of vision."""
    pass


def distance(agent: Any) -> float:
    """Get distance to the specified agent."""
    return 0.0


def towards(agent: Any) -> float:
    """Get heading towards the specified agent."""
    return 0.0


def distance_xy(x: float, y: float) -> float:
    """Get distance to coordinates."""
    return 0.0


def towards_xy(x: float, y: float) -> float:
    """Get heading towards coordinates."""
    return 0.0


# Turtle Queries
def xcor() -> float:
    """Get the turtle's x coordinate."""
    return 0.0


def ycor() -> float:
    """Get the turtle's y coordinate."""
    return 0.0


def heading() -> float:
    """Get the turtle's heading."""
    return 0.0


def color() -> Any:
    """Get the agent's color."""
    pass


def size() -> float:
    """Get the turtle's size."""
    return 1.0


def shape() -> str:
    """Get the turtle's shape."""
    return "default"


def label() -> Any:
    """Get the agent's label."""
    pass


def hidden() -> bool:
    """Check if the turtle is hidden."""
    return False


# Patch Queries
def pxcor() -> int:
    """Get the patch's x coordinate."""
    return 0


def pycor() -> int:
    """Get the patch's y coordinate."""
    return 0


def pcolor() -> Any:
    """Get the patch's color."""
    pass


def plabel() -> Any:
    """Get the patch's label."""
    pass


# World Queries
def max_pxcor() -> int:
    """Get the maximum patch x coordinate."""
    return 50


def max_pycor() -> int:
    """Get the maximum patch y coordinate."""
    return 50


def min_pxcor() -> int:
    """Get the minimum patch x coordinate."""
    return -50


def min_pycor() -> int:
    """Get the minimum patch y coordinate."""
    return -50


def world_width() -> int:
    """Get the world width in patches."""
    return 101


def world_height() -> int:
    """Get the world height in patches."""
    return 101


# Setters
def set_color(value: Any) -> None:
    """Set the agent's color."""
    pass


def set_heading(value: float) -> None:
    """Set the turtle's heading."""
    pass


def set_size(value: float) -> None:
    """Set the turtle's size."""
    pass


def set_shape(value: str) -> None:
    """Set the turtle's shape."""
    pass


def set_label(value: Any) -> None:
    """Set the agent's label."""
    pass


def set_pcolor(value: Any) -> None:
    """Set the patch's color."""
    pass


def set_plabel(value: Any) -> None:
    """Set the patch's label."""
    pass


def set_var(name: str, value: Any) -> None:
    """Set a variable value (generic setter)."""
    pass


# Random Number Generators
def random(n: float) -> float:
    """Random float from 0 to n (exclusive)."""
    return 0.0


def random_float(n: float) -> float:
    """Random float from 0 to n (exclusive)."""
    return 0.0


def random_int(n: int) -> int:
    """Random integer from 0 to n (inclusive)."""
    return 0


def random_xcor() -> float:
    """Random x coordinate."""
    return 0.0


def random_ycor() -> float:
    """Random y coordinate."""
    return 0.0


def random_pxcor() -> int:
    """Random patch x coordinate."""
    return 0


def random_pycor() -> int:
    """Random patch y coordinate."""
    return 0


# Link Primitives
def create_link_to(turtle: Any) -> None:
    """Create a link to the specified turtle."""
    pass


def create_link_from(turtle: Any) -> None:
    """Create a link from the specified turtle."""
    pass


def create_links_to(agentset: Any) -> None:
    """Create links to all turtles in agentset."""
    pass


def create_links_from(agentset: Any) -> None:
    """Create links from all turtles in agentset."""
    pass


def my_links() -> Any:
    """Get all links connected to this turtle."""
    pass


def my_in_links() -> Any:
    """Get all links pointing to this turtle."""
    pass


def my_out_links() -> Any:
    """Get all links from this turtle."""
    pass


def link_neighbors() -> Any:
    """Get turtles linked to this turtle."""
    pass


def in_link_neighbors() -> Any:
    """Get turtles with links pointing to this turtle."""
    pass


def out_link_neighbors() -> Any:
    """Get turtles this turtle has links to."""
    pass


# Color Utilities
def scale_color(color: Any, number: float, range_min: float, range_max: float) -> Any:
    """Scale a color based on a number within a range."""
    pass


def shade_of(color1: Any, color2: Any) -> bool:
    """Check if two colors are shades of the same base color."""
    return False


# Math & Logic
def abs_val(n: float) -> float:
    """Absolute value."""
    return 0.0


def acos(n: float) -> float:
    """Arc cosine."""
    return 0.0


def asin(n: float) -> float:
    """Arc sine."""
    return 0.0


def atan(x: float, y: float) -> float:
    """Arc tangent of y/x."""
    return 0.0


def cos(angle: float) -> float:
    """Cosine."""
    return 0.0


def sin(angle: float) -> float:
    """Sine."""
    return 0.0


def tan(angle: float) -> float:
    """Tangent."""
    return 0.0


def exp(n: float) -> float:
    """e raised to the power of n."""
    return 0.0


def ln(n: float) -> float:
    """Natural logarithm."""
    return 0.0


def log(n: float, base: float) -> float:
    """Logarithm with specified base."""
    return 0.0


def sqrt(n: float) -> float:
    """Square root."""
    return 0.0


def ceiling(n: float) -> int:
    """Round up."""
    return 0


def floor(n: float) -> int:
    """Round down."""
    return 0


def round_val(n: float) -> int:
    """Round to nearest integer."""
    return 0


def precision(n: float, places: int) -> float:
    """Round to specified decimal places."""
    return 0.0


def remainder(n: float, divisor: float) -> float:
    """Remainder of division."""
    return 0.0


def mod(n: float, divisor: float) -> float:
    """Modulo operation."""
    return 0.0


# List Operations
def length(lst: list) -> int:
    """Get list length."""
    return 0


def item(index: int, lst: list) -> Any:
    """Get item at index."""
    pass


def first(lst: list) -> Any:
    """Get first item."""
    pass


def last(lst: list) -> Any:
    """Get last item."""
    pass


def but_first(lst: list) -> list:
    """Get all but first item."""
    return []


def but_last(lst: list) -> list:
    """Get all but last item."""
    return []


def empty(lst: list) -> bool:
    """Check if list is empty."""
    return True


def member(item: Any, lst: list) -> bool:
    """Check if item is in list."""
    return False


def position(item: Any, lst: list) -> int:
    """Get position of item in list."""
    return -1


def remove(item: Any, lst: list) -> list:
    """Remove item from list."""
    return []


def remove_duplicates(lst: list) -> list:
    """Remove duplicate items."""
    return []


def reverse(lst: list) -> list:
    """Reverse list."""
    return []


def sort(lst: list) -> list:
    """Sort list."""
    return []


def shuffle(lst: list) -> list:
    """Randomly shuffle list."""
    return []


# String Operations
def word(*args: Any) -> str:
    """Concatenate arguments into a word."""
    return ""


def is_string(value: Any) -> bool:
    """Check if value is a string."""
    return False


def is_number(value: Any) -> bool:
    """Check if value is a number."""
    return False


def is_boolean(value: Any) -> bool:
    """Check if value is a boolean."""
    return False


def is_list(value: Any) -> bool:
    """Check if value is a list."""
    return False


def is_agent(value: Any) -> bool:
    """Check if value is an agent."""
    return False


def is_agentset(value: Any) -> bool:
    """Check if value is an agentset."""
    return False


def is_patch(value: Any) -> bool:
    """Check if value is a patch."""
    return False


def is_turtle(value: Any) -> bool:
    """Check if value is a turtle."""
    return False


def is_link(value: Any) -> bool:
    """Check if value is a link."""
    return False


# I/O Operations
def print_msg(message: Any) -> None:
    """Print a message to the command center."""
    pass


def show(message: Any) -> None:
    """Show a message with the agent's identifier."""
    pass


def write(message: Any) -> None:
    """Write to output without newline."""
    pass


def type_msg(message: Any) -> None:
    """Type to output without newline or spaces."""
    pass


# Timing
def timer() -> float:
    """Get elapsed time since timer was reset."""
    return 0.0


def reset_timer() -> None:
    """Reset the timer to zero."""
    pass


# Display
def display() -> None:
    """Update the view immediately."""
    pass


def no_display() -> None:
    """Suspend view updates."""
    pass


# ============================================================================
# UI Widget Classes
# ============================================================================


class UIWidget:
    """Base class for all UI widgets."""

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class View(UIWidget):
    """NetLogo world view widget."""

    def __init__(
        self,
        x: int = 765,
        y: int = 0,
        width: int = 510,
        height: int = 510,
        min_pxcor: int = -50,
        max_pxcor: int = 50,
        min_pycor: int = -50,
        max_pycor: int = 50,
        patch_size: float = 5.0,
        frame_rate: float = 20.0,
        show_tick_counter: bool = True,
        tick_counter_label: str = "ticks",
        wrapping_x: bool = True,
        wrapping_y: bool = True,
        font_size: int = 10,
        update_mode: int = 1,  # 0=continuous, 1=on ticks
    ):
        super().__init__(x, y, width, height)
        self.min_pxcor = min_pxcor
        self.max_pxcor = max_pxcor
        self.min_pycor = min_pycor
        self.max_pycor = max_pycor
        self.patch_size = patch_size
        self.frame_rate = frame_rate
        self.show_tick_counter = show_tick_counter
        self.tick_counter_label = tick_counter_label
        self.wrapping_x = wrapping_x
        self.wrapping_y = wrapping_y
        self.font_size = font_size
        self.update_mode = update_mode


class Button(UIWidget):
    """Button widget to execute commands."""

    def __init__(
        self,
        command: str,
        x: int,
        y: int,
        width: int = 100,
        height: int = 40,
        forever: bool = False,
        display: str | None = None,
        kind: str = "Observer",  # Observer or Turtle
        disable_until_ticks: bool = False,
    ):
        super().__init__(x, y, width, height)
        self.command = command
        self.forever = forever
        self.display = display or command
        self.kind = kind
        self.disable_until_ticks = disable_until_ticks


class Monitor(UIWidget):
    """Monitor widget to display values."""

    def __init__(
        self,
        expression: str,
        x: int,
        y: int,
        width: int = 100,
        height: int = 60,
        display: str | None = None,
        precision: int = 17,
        font_size: int = 11,
    ):
        super().__init__(x, y, width, height)
        self.expression = expression
        self.display = display
        self.precision = precision
        self.font_size = font_size


class Switch(UIWidget):
    """Switch widget for boolean variables."""

    def __init__(
        self,
        variable: str,
        x: int,
        y: int,
        width: int = 100,
        height: int = 40,
        default: bool = False,
        display: str | None = None,
    ):
        super().__init__(x, y, width, height)
        self.variable = variable
        self.default = default
        self.display = display or variable


class Slider(UIWidget):
    """Slider widget for numeric variables."""

    def __init__(
        self,
        variable: str,
        x: int,
        y: int,
        width: int = 150,
        height: int = 40,
        min_val: float = 0,
        max_val: float = 100,
        default: float = 50,
        step: float = 1,
        display: str | None = None,
        units: str | None = None,
        direction: str = "horizontal",  # horizontal or vertical
    ):
        super().__init__(x, y, width, height)
        self.variable = variable
        self.min_val = min_val
        self.max_val = max_val
        self.default = default
        self.step = step
        self.display = display or variable
        self.units = units
        self.direction = direction


class PlotPen:
    """Pen definition for a plot."""

    def __init__(
        self,
        name: str,
        update_code: str,
        color: int = -16777216,  # black
        mode: int = 0,  # 0=line, 1=bar, 2=point
        interval: float = 1.0,
        show_in_legend: bool = True,
        setup_code: str = "",
    ):
        self.name = name
        self.update_code = update_code
        self.color = color
        self.mode = mode
        self.interval = interval
        self.show_in_legend = show_in_legend
        self.setup_code = setup_code


class Plot(UIWidget):
    """Plot widget for graphing data."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        width: int = 400,
        height: int = 250,
        x_axis: str = "Time",
        y_axis: str = "Value",
        x_min: float = 0.0,
        x_max: float = 10.0,
        y_min: float = 0.0,
        y_max: float = 10.0,
        auto_plot_x: bool = True,
        auto_plot_y: bool = True,
        show_legend: bool = True,
        setup_code: str = "",
        update_code: str = "",
    ):
        super().__init__(x, y, width, height)
        self.name = name
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.auto_plot_x = auto_plot_x
        self.auto_plot_y = auto_plot_y
        self.show_legend = show_legend
        self.setup_code = setup_code
        self.update_code = update_code
        self.pens: list[PlotPen] = []

    def add_pen(self, pen: PlotPen) -> None:
        """Add a pen to the plot."""
        self.pens.append(pen)


class TextBox(UIWidget):
    """Text box widget for display or input."""

    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        width: int = 200,
        height: int = 100,
        font_size: int = 11,
        transparent: bool = False,
        color: int = 0,  # black
    ):
        super().__init__(x, y, width, height)
        self.text = text
        self.font_size = font_size
        self.transparent = transparent
        self.color = color
