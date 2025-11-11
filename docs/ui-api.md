# UI Widget API Reference# xnlogo UI API



Complete reference for creating NetLogo user interfaces in xnLogo using the `ui()` method.Gradio-inspired declarative API for creating NetLogo interface widgets.



## Overview## Overview



xnLogo provides a declarative API for defining NetLogo interface widgets. Define your UI in a `ui()` or `widgets()` method, and xnLogo generates the appropriate NetLogo XML during compilation.The UI API allows you to define your NetLogo model's user interface directly in Python using a familiar declarative syntax inspired by Gradio. All widgets are converted to NetLogo XML during compilation.



## Basic Usage## Quick Start



Define widgets in your model's `ui()` method:```python

from xnlogo import agent

```pythonfrom xnlogo.runtime.ui import Interface, View, Button, Switch, Monitor, Plot, PlotPen

from xnlogo.runtime import Model, View, Button, Monitor, Slider

@agent

class MyModel(Model):class MyAgent:

    def __init__(self):    population: int = 100

        super().__init__()    # ... agent code ...

        self.population = 100

    interface = Interface(

    def setup(self):    title="My Model",

        # Setup code    view=View(width=600, height=600),

        pass    buttons=[

            Button(label="setup", x=10, y=10),

    def go(self):        Button(label="go", x=110, y=10, forever=True),

        # Go code    ],

        pass    monitors=[

            Monitor(variable="population", x=10, y=60),

    def ui(self):    ],

        """Define the user interface.""")

        # World view```

        self.add_widget(View(

            x=385, y=10,## Components

            width=610, height=631,

            patch_size=13.0### Interface

        ))

        Main container for all UI elements.

        # Setup button

        self.add_widget(Button(```python

            command="setup",Interface(

            x=15, y=10,    title: str = "Agent-Based Model",

            width=150, height=60    view: Optional[View] = None,

        ))    buttons: List[Button] = [],

            switches: List[Switch] = [],

        # Go button (runs continuously)    sliders: List[Slider] = [],

        self.add_widget(Button(    monitors: List[Monitor] = [],

            command="go",    plots: List[Plot] = [],

            x=175, y=10,    choosers: List[Chooser] = [],

            width=150, height=60,    textboxes: List[TextBox] = [],

            forever=True)

        ))```

        

        # Population monitor### View

        self.add_widget(Monitor(

            expression="population",The main 2D visualization window showing the NetLogo world.

            x=15, y=150,

            width=150, height=60```python

        ))View(

            x: int = 765,

        # Population slider    y: int = 0,

        self.add_widget(Slider(    width: int = 510,

            variable="population",    height: int = 510,

            min_val=0,    min_pxcor: int = -50,

            max_val=500,    max_pxcor: int = 50,

            default=100,    min_pycor: int = -50,

            x=15, y=230,    max_pycor: int = 50,

            width=310, height=40    patch_size: float = 5.0,

        ))    frame_rate: float = 20.0,

```    show_tick_counter: bool = True,

    tick_counter_label: str = "ticks",

## Widget Types)

```

### View

### Button

The main 2D visualization window displaying the NetLogo world.

Execute commands when clicked.

**Constructor**:

```python```python

View(Button(

    x: int = 385,    label: str,               # Command name to execute

    y: int = 10,    x: int = 10,

    width: int = 610,    y: int = 10,

    height: int = 631,    width: int = 90,

    patch_size: float = 13.0,    height: int = 30,

    min_pxcor: int = None,  # Calculated from width if not set    forever: bool = False,    # True for continuous execution

    max_pxcor: int = None,  # Calculated from width if not set    kind: str = "Observer",   # "Observer", "Turtle", or "Patch"

    min_pycor: int = None,  # Calculated from height if not set)

    max_pycor: int = None,  # Calculated from height if not set```

    wrap_x: bool = False,

    wrap_y: bool = False,**Example:**

    show_tick_counter: bool = True,```python

    tick_counter_label: str = "ticks",Button(label="setup", x=10, y=10, forever=False)

    frame_rate: float = 30.0Button(label="go", x=110, y=10, forever=True)

)```

```

### Switch

**Example**:

```pythonBoolean on/off toggle.

self.add_widget(View(

    x=385, y=10,```python

    width=610, height=631,Switch(

    patch_size=13.0,    variable: str,            # Global variable name

    min_pxcor=-23, max_pxcor=23,    x: int = 10,

    min_pycor=-23, max_pycor=23,    y: int = 10,

    wrap_x=True,    width: int = 150,

    wrap_y=True    height: int = 40,

))    default: bool = False,

```    label: Optional[str] = None,  # Display label (defaults to variable name)

)

### Button```



Execute NetLogo commands when clicked.**Example:**

```python

**Constructor**:Switch(variable="social_distancing", x=15, y=100, default=False)

```python```

Button(

    command: str,           # Command name to execute### Slider

    x: int = 10,

    y: int = 10,Numeric value selector.

    width: int = 90,

    height: int = 30,```python

    forever: bool = False,  # True for continuous executionSlider(

    display: str = None,    # Display label (defaults to command)    variable: str,

    kind: str = "Observer"  # "Observer", "Turtle", or "Patch"    min_value: float = 0.0,

)    max_value: float = 100.0,

```    default: float = 50.0,

    step: float = 1.0,

**Examples**:    x: int = 10,

```python    y: int = 10,

# One-time setup button    width: int = 150,

self.add_widget(Button(    height: int = 40,

    command="setup",    label: Optional[str] = None,

    x=15, y=10,    units: Optional[str] = None,

    width=150, height=60)

))```



# Continuous go button**Example:**

self.add_widget(Button(```python

    command="go",Slider(

    x=175, y=10,    variable="infection_rate",

    width=150, height=60,    min_value=0.0,

    forever=True    max_value=100.0,

))    default=35.0,

    step=1.0,

# Custom label    units="%",

self.add_widget(Button()

    command="initialize",```

    display="Initialize Model",

    x=15, y=80,### Monitor

    width=150, height=60

))Display computed values or variables.

```

```python

### MonitorMonitor(

    variable: Optional[str] = None,      # Simple variable monitor

Display a computed value or variable.    expression: Optional[str] = None,    # NetLogo expression to evaluate

    label: Optional[str] = None,         # Display label for expressions

**Constructor**:    x: int = 10,

```python    y: int = 10,

Monitor(    width: int = 100,

    expression: str,        # NetLogo expression to display    height: int = 60,

    x: int = 10,    precision: int = 17,

    y: int = 10,    font_size: int = 11,

    width: int = 100,)

    height: int = 60,```

    label: str = None,      # Display label (defaults to expression)

    precision: int = 17,    # Decimal places**Examples:**

    font_size: int = 11```python

)# Simple variable

```Monitor(variable="total_deaths", x=100, y=50)



**Examples**:# Expression with label

```pythonMonitor(

# Simple variable    expression="count turtles with [infected_time > 0]",

self.add_widget(Monitor(    label="Currently Infected",

    expression="population",    x=200, y=50,

    x=15, y=150,)

    width=150, height=60```

))

### Plot

# Computed value with label

self.add_widget(Monitor(2D line/bar/point plots for time series data.

    expression="count turtles",

    label="Total Agents",```python

    x=175, y=150,Plot(

    width=150, height=60    title: str,

))    x: int = 10,

    y: int = 10,

# Complex expression    width: int = 400,

self.add_widget(Monitor(    height: int = 250,

    expression="count turtles with [infected? = true]",    x_axis: str = "time",

    label="Infected",    y_axis: str = "value",

    x=15, y=220,    auto_plot_x: bool = True,

    width=150, height=60,    auto_plot_y: bool = True,

    precision=0    legend: bool = True,

))    pens: List[PlotPen] = [],

```)

```

### Slider

**PlotPen:**

Interactive numeric parameter control.```python

PlotPen(

**Constructor**:    name: str,                # Legend label

```python    color: str = "black",     # Color name or code

Slider(    mode: int = 0,            # 0=line, 1=bar, 2=point

    variable: str,          # Global variable name    interval: float = 1.0,

    min_val: float = 0.0,    update: str = "",         # NetLogo code to plot data

    max_val: float = 100.0,    setup: str = "",          # Optional setup code

    default: float = 50.0,)

    step: float = 1.0,```

    x: int = 10,

    y: int = 10,**Example:**

    width: int = 150,```python

    height: int = 40,Plot(

    label: str = None,      # Display label (defaults to variable)    title="Population Dynamics",

    units: str = None       # Units label (e.g., "%", "degrees")    x=10, y=10,

)    width=750, height=225,

```    x_axis="Time",

    y_axis="Count",

**Examples**:    pens=[

```python        PlotPen(

# Integer slider            name="Infected",

self.add_widget(Slider(            color="orange",

    variable="population",            update="plot count turtles with [infected_time > 0]",

    min_val=0,        ),

    max_val=500,        PlotPen(

    default=100,            name="Immune",

    step=1,            color="brown",

    x=15, y=230,            update="plot count turtles with [antibodies > 0]",

    width=310, height=40        ),

))    ],

)

# Float slider with units```

self.add_widget(Slider(

    variable="infection_rate",### Chooser

    min_val=0.0,

    max_val=1.0,Dropdown selector for discrete options.

    default=0.35,

    step=0.01,```python

    label="Infection Rate",Chooser(

    units="%",    variable: str,

    x=15, y=280,    choices: List[str],

    width=310, height=40    default: int = 0,         # Index of default choice

))    x: int = 10,

    y: int = 10,

# Angle slider    width: int = 150,

self.add_widget(Slider(    height: int = 40,

    variable="rotation_angle",    label: Optional[str] = None,

    min_val=0,)

    max_val=360,```

    default=0,

    step=1,**Example:**

    units="degrees",```python

    x=15, y=330,Chooser(

    width=310, height=40    variable="scenario",

))    choices=["baseline", "intervention", "lockdown"],

```    default=0,

    x=10, y=100,

### Switch)

```

Boolean on/off toggle.

### TextBox

**Constructor**:

```pythonDisplay static or dynamic text.

Switch(

    variable: str,          # Global variable name```python

    x: int = 10,TextBox(

    y: int = 10,    text: str = "",

    width: int = 150,    x: int = 10,

    height: int = 40,    y: int = 10,

    default: bool = False,    width: int = 300,

    label: str = None       # Display label (defaults to variable)    height: int = 100,

)    font_size: int = 12,

```    color: str = "black",

    transparent: bool = False,

**Examples**:)

```python```

# Simple switch

self.add_widget(Switch(**Example:**

    variable="social_distancing",```python

    x=15, y=100,TextBox(

    width=150, height=40    text="Model Instructions:\n1. Click setup\n2. Adjust parameters\n3. Click go",

))    x=10, y=500,

    width=300, height=80,

# With custom label)

self.add_widget(Switch(```

    variable="debug_mode",

    label="Enable Debug Output",## Color Names

    default=True,

    x=15, y=150,Supported color names for plots and widgets:

    width=150, height=40

))- `black`, `white`, `gray`

```- `red`, `orange`, `brown`, `yellow`

- `green`, `lime`, `turquoise`, `cyan`, `sky`, `blue`

### Chooser- `violet`, `magenta`, `pink`



Dropdown selector for discrete options.You can also use NetLogo color codes (e.g., `"-8053223"` for orange).



**Constructor**:## Complete Example

```python

Chooser(```python

    variable: str,              # Global variable namefrom xnlogo import agent

    choices: List[str],         # List of optionsfrom xnlogo.runtime.ui import (

    default: int = 0,           # Index of default choice    Interface, View, Button, Switch, Slider, 

    x: int = 10,    Monitor, Plot, PlotPen

    y: int = 10,)

    width: int = 150,

    height: int = 40,@agent

    label: str = None           # Display label (defaults to variable)class Person:

)    infected: bool = False

```    immunity: int = 0

    

**Examples**:    infection_rate: float = 0.35

```python    recovery_time: int = 14

# Simple chooser    

self.add_widget(Chooser(    def setup(self):

    variable="scenario",        self.infected = False

    choices=["baseline", "intervention", "lockdown"],        self.immunity = 0

    default=0,    

    x=15, y=380,    def step(self):

    width=150, height=40        # Model logic here

))        pass



# With custom labelinterface = Interface(

self.add_widget(Chooser(    title="Disease Spread Model",

    variable="initial_state",    

    choices=["random", "clustered", "grid"],    view=View(

    label="Initial Agent Distribution",        width=600, height=600,

    default=1,        min_pxcor=-30, max_pxcor=30,

    x=15, y=430,        min_pycor=-30, max_pycor=30,

    width=150, height=40    ),

))    

```    buttons=[

        Button(label="setup", x=10, y=10, width=80),

### Plot        Button(label="go", x=100, y=10, width=80, forever=True),

    ],

2D line/bar/point plots for time series data.    

    sliders=[

**Constructor**:        Slider(

```python            variable="infection_rate",

Plot(            min_value=0.0, max_value=1.0,

    title: str,            default=0.35, step=0.01,

    x: int = 10,            x=10, y=60,

    y: int = 10,            label="Infection Rate",

    width: int = 400,        ),

    height: int = 250,    ],

    x_label: str = "time",    

    y_label: str = "value",    switches=[

    x_min: float = 0.0,        Switch(

    x_max: float = 10.0,            variable="social_distancing",

    y_min: float = 0.0,            x=10, y=120,

    y_max: float = 10.0,            default=False,

    auto_plot_on: bool = True,        ),

    legend_on: bool = True,    ],

    pens: List[PlotPen] = []    

)    monitors=[

```        Monitor(variable="count turtles", label="Total", x=10, y=180),

        Monitor(

**PlotPen Constructor**:            expression="count turtles with [infected]",

```python            label="Infected",

PlotPen(            x=120, y=180,

    name: str,              # Legend label        ),

    color: int = 0,         # NetLogo color code    ],

    mode: int = 0,          # 0=line, 1=bar, 2=point    

    interval: float = 1.0,    plots=[

    setup_code: str = "",   # Code to run on setup        Plot(

    update_code: str = ""   # Code to run each update            title="Disease Progress",

)            x=10, y=260,

```            width=400, height=200,

            pens=[

**Examples**:                PlotPen(

```python                    name="Infected",

from xnlogo.runtime import Plot, PlotPen                    color="red",

                    update="plot count turtles with [infected]",

# Simple time series                ),

self.add_widget(Plot(                PlotPen(

    title="Population Over Time",                    name="Immune",

    x=10, y=10,                    color="green",

    width=750, height=225,                    update="plot count turtles with [immunity > 0]",

    x_label="Time",                ),

    y_label="Count",            ],

    pens=[        ),

        PlotPen(    ],

            name="Population",)

            color=5,  # Green```

            update_code="plot count turtles"

        )## Notes

    ]

))- The `interface` variable must be defined at module level (not inside classes or functions)

- Widget positions are in pixels from top-left corner

# Multiple series- All widgets are optional - you can use any combination

self.add_widget(Plot(- Default setup/go buttons are added automatically unless you provide custom buttons

    title="Disease Dynamics",- Widget evaluation happens at compile time, so all parameters must be static values

    x=10, y=250,
    width=750, height=225,
    pens=[
        PlotPen(
            name="Susceptible",
            color=105,  # Blue
            update_code="plot count turtles with [status = \"susceptible\"]"
        ),
        PlotPen(
            name="Infected",
            color=15,  # Red
            update_code="plot count turtles with [status = \"infected\"]"
        ),
        PlotPen(
            name="Recovered",
            color=55,  # Green
            update_code="plot count turtles with [status = \"recovered\"]"
        )
    ]
))
```

### TextBox

Display static or dynamic text.

**Constructor**:
```python
TextBox(
    text: str = "",
    x: int = 10,
    y: int = 10,
    width: int = 300,
    height: int = 100,
    font_size: int = 12,
    color: int = 0,         # NetLogo color code
    transparent: bool = False
)
```

**Examples**:
```python
# Instructions
self.add_widget(TextBox(
    text="Instructions:\n1. Click setup\n2. Adjust parameters\n3. Click go",
    x=10, y=500,
    width=300, height=80,
    font_size=11
))

# Title
self.add_widget(TextBox(
    text="Disease Spread Model v1.0",
    x=10, y=10,
    width=300, height=40,
    font_size=14,
    transparent=True
))
```

## Widget Positioning

Widgets use absolute positioning in pixels from the top-left corner:

- **x**: Horizontal position (pixels from left)
- **y**: Vertical position (pixels from top)
- **width**: Widget width in pixels
- **height**: Widget height in pixels

**Layout Tips**:

1. Leave space for the View (typically 600x600 pixels)
2. Group related controls together
3. Standard button size: 150x60
4. Standard monitor size: 150x60
5. Standard slider size: 310x40
6. Leave 10-20 pixel margins

**Example Layout**:
```python
def ui(self):
    # View on the right
    self.add_widget(View(x=385, y=10, width=610, height=631))
    
    # Controls on the left
    # Row 1: Buttons
    self.add_widget(Button(command="setup", x=15, y=10, width=150, height=60))
    self.add_widget(Button(command="go", x=175, y=10, width=150, height=60, forever=True))
    
    # Row 2: Monitors
    self.add_widget(Monitor(expression="count turtles", x=15, y=80, width=150, height=60))
    self.add_widget(Monitor(expression="ticks", x=175, y=80, width=150, height=60))
    
    # Row 3+: Sliders
    self.add_widget(Slider(variable="population", x=15, y=150, width=310, height=40))
    self.add_widget(Slider(variable="speed", x=15, y=200, width=310, height=40))
```

## NetLogo Colors

NetLogo uses numeric color codes. Common colors:

| Color | Code | Usage |
|-------|------|-------|
| Black | 0 | Text, default |
| Gray | 5 | Neutral |
| White | 9.9 | Backgrounds |
| Red | 15 | Danger, error |
| Orange | 25 | Warning |
| Brown | 35 | Earth tones |
| Yellow | 45 | Highlight |
| Green | 55 | Success, nature |
| Lime | 65 | Bright green |
| Cyan | 85 | Water |
| Blue | 105 | Sky, data |
| Violet | 115 | Secondary |
| Magenta | 125 | Accent |
| Pink | 135 | Alternate |

You can also use intermediate values (e.g., `17.5` for a darker red).

## Complete Example

Full model with comprehensive UI:

```python
from xnlogo.runtime import (
    Model, breed, reset_ticks, tick,
    View, Button, Switch, Slider, Monitor, Plot, PlotPen, Chooser
)

class DiseaseModel(Model):
    def __init__(self):
        super().__init__()
        self.people = breed("people", "person")
        
        # Parameters
        self.initial_population = 200
        self.infection_rate = 0.35
        self.recovery_time = 14
        self.social_distancing = False
        self.intervention_strategy = "none"
        
        # Statistics
        self.total_infected = 0
        self.total_recovered = 0
    
    def setup(self):
        reset_ticks()
        # Setup logic...
    
    def go(self):
        # Simulation logic...
        tick()
    
    def ui(self):
        """Define the user interface."""
        
        # Main view
        self.add_widget(View(
            x=385, y=10,
            width=610, height=631,
            patch_size=13.0,
            min_pxcor=-23, max_pxcor=23,
            min_pycor=-23, max_pycor=23
        ))
        
        # Control buttons
        self.add_widget(Button(
            command="setup",
            x=15, y=10,
            width=150, height=60
        ))
        
        self.add_widget(Button(
            command="go",
            x=175, y=10,
            width=150, height=60,
            forever=True
        ))
        
        # Parameters
        self.add_widget(Slider(
            variable="initial_population",
            min_val=50,
            max_val=500,
            default=200,
            step=10,
            label="Initial Population",
            x=15, y=80,
            width=310, height=40
        ))
        
        self.add_widget(Slider(
            variable="infection_rate",
            min_val=0.0,
            max_val=1.0,
            default=0.35,
            step=0.01,
            label="Infection Rate",
            units="%",
            x=15, y=130,
            width=310, height=40
        ))
        
        self.add_widget(Slider(
            variable="recovery_time",
            min_val=5,
            max_val=30,
            default=14,
            step=1,
            label="Recovery Time",
            units="days",
            x=15, y=180,
            width=310, height=40
        ))
        
        # Switches
        self.add_widget(Switch(
            variable="social_distancing",
            label="Social Distancing",
            x=15, y=230,
            width=150, height=40
        ))
        
        # Chooser
        self.add_widget(Chooser(
            variable="intervention_strategy",
            choices=["none", "testing", "isolation", "vaccination"],
            label="Intervention",
            x=175, y=230,
            width=150, height=40
        ))
        
        # Monitors
        self.add_widget(Monitor(
            expression="count people",
            label="Population",
            x=15, y=290,
            width=100, height=60
        ))
        
        self.add_widget(Monitor(
            expression="count people with [infected?]",
            label="Infected",
            x=125, y=290,
            width=100, height=60
        ))
        
        self.add_widget(Monitor(
            expression="total_infected",
            label="Total Infected",
            x=235, y=290,
            width=100, height=60
        ))
        
        # Plot
        self.add_widget(Plot(
            title="Disease Progress",
            x=10, y=660,
            width=985, height=225,
            x_label="Time",
            y_label="Count",
            pens=[
                PlotPen(
                    name="Susceptible",
                    color=105,
                    update_code="plot count people with [not infected? and not recovered?]"
                ),
                PlotPen(
                    name="Infected",
                    color=15,
                    update_code="plot count people with [infected?]"
                ),
                PlotPen(
                    name="Recovered",
                    color=55,
                    update_code="plot count people with [recovered?]"
                )
            ]
        ))
```

## Alternative Method Names

You can use either `ui()` or `widgets()` as the method name - both work identically:

```python
def widgets(self):
    """Define UI widgets."""
    self.add_widget(Button(command="setup", x=15, y=10))
    # ...
```

## Notes and Limitations

1. **Widget Evaluation**: Widget definitions are evaluated at compile time. All parameters must be static values (no variables or expressions).

2. **Coordinate System**: NetLogo uses a coordinate system with (0, 0) at the top-left corner of the interface panel.

3. **Widget Order**: Widgets are rendered in the order they're added. Later widgets appear on top if they overlap.

4. **View Requirement**: Most models should have exactly one View widget to display the simulation world.

5. **Button Commands**: Button command names must match model method names or NetLogo built-in commands.

6. **Monitor Expressions**: Monitor expressions are NetLogo code, not Python. Use NetLogo syntax for complex expressions.

7. **Plot Update**: Plots update automatically during simulation when `tick` is called.

## Best Practices

1. **Organize Widgets**: Group related controls together visually
2. **Use Descriptive Labels**: Override default labels for clarity
3. **Set Sensible Ranges**: Choose slider min/max based on model requirements
4. **Monitor Key Metrics**: Display important statistics for user feedback
5. **Test Layout**: Compile and open in NetLogo to verify visual appearance
6. **Consistent Sizing**: Use similar sizes for widgets of the same type
7. **Leave Margins**: Don't place widgets right at edges or touching

## Getting Help

- See [User Guide](user-guide.md) for complete model examples
- Check [examples/](../examples/) for working models with UI
- Run `xnlogo build` to compile and test your UI
- Open compiled `.nlogox` in NetLogo to preview the interface
