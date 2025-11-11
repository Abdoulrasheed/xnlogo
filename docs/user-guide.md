# xnLogo User Guide

Complete guide to building NetLogo models with Python using xnLogo.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Model Basics](#model-basics)
- [Working with Agents](#working-with-agents)
- [Model Lifecycle](#model-lifecycle)
- [User Interface](#user-interface)
- [Running and Testing](#running-and-testing)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Installation

### Requirements

- Python 3.10 or higher
- pip package manager

**Optional (for running models):**
- Java 17 or higher
- NetLogo 7.0 or higher

### Install xnLogo

```bash
pip install xnlogo
```

### Verify Installation

```bash
xnlogo --version
```

Should output: `xnlogo, version 0.1.0`

## Quick Start

### Step 1: Create a Model

Create `counter.py`:

```python
from xnlogo.runtime import Model, reset_ticks, tick

class CounterModel(Model):
    """A simple counter that increments each tick."""
    
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.max_counter = 10
    
    def setup(self):
        """Initialize the model."""
        reset_ticks()
        self.counter = 0
    
    def go(self):
        """Run one step."""
        self.counter += 1
        if self.counter > self.max_counter:
            self.counter = 0
        tick()
```

### Step 2: Compile to NetLogo

```bash
xnlogo build counter.py
```

This creates `counter.nlogox` in the current directory.

### Step 3: Open in NetLogo

```bash
open counter.nlogox
# Or double-click the file
```

### Step 4: Run in NetLogo

1. Click the **setup** button
2. Click the **go** button
3. Watch the counter increment!

## Model Basics

### Model Structure

Every xnLogo model is a Python class that inherits from `Model`:

```python
from xnlogo.runtime import Model

class MyModel(Model):
    def __init__(self):
        super().__init__()
        # Initialize model state here
    
    def setup(self):
        # Setup procedure
        pass
    
    def go(self):
        # Go procedure (runs each tick)
        pass
```

### Model State

Instance variables in `__init__` become NetLogo global variables:

```python
def __init__(self):
    super().__init__()
    self.population = 100
    self.infection_rate = 0.05
    self.total_infected = 0
```

Translates to NetLogo:
```netlogo
globals [population infection_rate total_infected]
```

### Methods as Procedures

Model methods become NetLogo procedures:

```python
def increment_counter(self):
    self.counter += 1

def reset_counter(self):
    self.counter = 0
```

Generates:
```netlogo
to increment_counter
  set counter (counter + 1)
end

to reset_counter
  set counter 0
end
```

## Working with Agents

### Creating Breeds

Use the `breed()` function to define agent types:

```python
from xnlogo.runtime import Model, breed

class EcosystemModel(Model):
    def __init__(self):
        super().__init__()
        self.rabbits = breed("rabbits", "rabbit")
        self.foxes = breed("foxes", "fox")
```

This creates NetLogo breeds:
```netlogo
breed [rabbits rabbit]
breed [foxes fox]
```

### Creating Agents

Create agents using the breed's `create()` method:

```python
def setup(self):
    reset_ticks()
    
    # Create 50 rabbits
    for i in range(50):
        rabbit = self.rabbits.create(1)
        rabbit.energy = 10
        rabbit.color = "brown"
    
    # Create 10 foxes
    for i in range(10):
        fox = self.foxes.create(1)
        fox.energy = 20
        fox.color = "red"
```

### Agent Properties

Set agent properties using attribute assignment:

```python
agent = self.rabbits.create(1)
agent.energy = 10
agent.color = "brown"
agent.size = 1.5
agent.setxy(0, 0)  # Set position
```

### Iterating Over Agents

Use `all()` to get all agents of a breed:

```python
def go(self):
    # Move all rabbits
    for rabbit in self.rabbits.all():
        rabbit.forward(1)
    
    # Foxes hunt
    for fox in self.foxes.all():
        self.hunt(fox)
    
    tick()
```

### Agent Methods

Pass agents to helper methods:

```python
def hunt(self, fox):
    """Fox hunts nearby rabbits."""
    nearby = fox.in_radius(5)  # Get nearby agents
    if nearby:
        prey = nearby[0]
        prey.die()  # Remove from simulation
        fox.energy += 5
```

## Model Lifecycle

### Setup Phase

The `setup()` method initializes the model:

```python
def setup(self):
    reset_ticks()  # Reset tick counter
    
    # Clear existing agents
    for agent in self.my_breed.all():
        agent.die()
    
    # Create new agents
    for i in range(100):
        agent = self.my_breed.create(1)
        agent.initialize()
    
    # Set initial state
    self.total_count = 100
```

### Go Phase

The `go()` method runs each simulation step:

```python
def go(self):
    # Update agents
    for agent in self.agents.all():
        agent.move()
        agent.interact()
    
    # Update globals
    self.total_count = self.agents.count()
    
    # Advance time
    tick()
```

### Custom Procedures

Define helper methods for reusable logic:

```python
def move_agents(self):
    """Move all agents randomly."""
    for agent in self.agents.all():
        angle = random_float(360)
        agent.set_heading(angle)
        agent.forward(1)

def update_statistics(self):
    """Calculate model statistics."""
    self.average_energy = sum(a.energy for a in self.agents.all()) / self.agents.count()
```

## User Interface

### Adding Widgets

Define UI widgets in a `ui()` or `widgets()` method:

```python
from xnlogo.runtime import View, Button, Monitor, Slider

def ui(self):
    """Define UI widgets."""
    # View (world display)
    self.add_widget(View(
        x=385, y=10,
        width=610, height=631,
        patch_size=13.0
    ))
    
    # Setup button
    self.add_widget(Button(
        command="setup",
        x=15, y=10,
        width=150, height=60,
        forever=False
    ))
    
    # Go button
    self.add_widget(Button(
        command="go",
        x=175, y=10,
        width=150, height=60,
        forever=True  # Runs repeatedly
    ))
    
    # Monitor
    self.add_widget(Monitor(
        expression="count turtles",
        x=15, y=150,
        width=150, height=60
    ))
    
    # Slider
    self.add_widget(Slider(
        variable="population",
        min_val=0, max_val=500,
        default=100,
        x=15, y=230,
        width=310, height=40
    ))
```

### Widget Types

**View**: Displays the simulation world
```python
View(x=385, y=10, width=610, height=631, patch_size=13.0)
```

**Button**: Executes a command
```python
Button(command="setup", x=15, y=10, width=150, height=60, forever=False)
```

**Monitor**: Displays a value
```python
Monitor(expression="count turtles", x=15, y=150, width=150, height=60)
```

**Slider**: Interactive parameter control
```python
Slider(variable="speed", min_val=0, max_val=10, default=5, x=15, y=230, width=310, height=40)
```

**Switch**: Boolean toggle
```python
Switch(variable="debug_mode", default=False, x=15, y=300, width=150, height=40)
```

### Model Documentation

Add documentation with the `info()` method:

```python
def info(self):
    """Return model documentation."""
    return """
## WHAT IS IT?

This model simulates...

## HOW IT WORKS

The agents...

## HOW TO USE IT

1. Click SETUP
2. Click GO
3. Adjust sliders

## THINGS TO NOTICE

...

## EXTENDING THE MODEL

...
"""
```

## Running and Testing

### Compilation

Compile your model to NetLogo:

```bash
xnlogo build mymodel.py
```

Options:
```bash
xnlogo build mymodel.py --output-dir ./output  # Custom output directory
xnlogo build mymodel.py --format nlogo         # Legacy format
```

### Validation

Check for errors without compiling:

```bash
xnlogo check mymodel.py
```

This validates your model structure and reports errors.

### Testing Models

Test models programmatically:

```python
if __name__ == "__main__":
    model = MyModel()
    model.setup()
    
    # Run 100 steps
    for i in range(100):
        model.go()
    
    # Check results
    print(f"Final count: {model.counter}")
    assert model.counter > 0
```

## Common Patterns

### Random Movement

```python
from xnlogo.runtime import random_float

def move_randomly(self, agent):
    angle = random_float(360)
    agent.set_heading(angle)
    agent.forward(1)
```

### Nearby Interactions

```python
def interact_with_neighbors(self, agent):
    nearby = agent.in_radius(3)
    for neighbor in nearby:
        if neighbor != agent:
            # Interact with neighbor
            pass
```

### Energy-Based Behavior

```python
def consume_energy(self, agent):
    agent.energy -= 1
    if agent.energy <= 0:
        agent.die()
```

### Reproduction

```python
def reproduce(self, parent):
    if parent.energy > 50:
        child = self.agents.create(1)
        child.energy = 25
        parent.energy -= 25
        child.setxy(parent.xcor(), parent.ycor())
```

### Counting and Statistics

```python
def update_stats(self):
    self.total_agents = self.agents.count()
    self.average_energy = sum(a.energy for a in self.agents.all()) / max(1, self.total_agents)
```

## Troubleshooting

### Common Issues

**"No module named 'xnlogo'"**
- Solution: Install xnLogo with `pip install xnlogo`

**"Model class not found"**
- Ensure your class inherits from `Model`
- Check that `__init__` calls `super().__init__()`

**"breed() must be called in __init__"**
- Move all `breed()` calls to the `__init__` method

**Compilation errors**
- Run `xnlogo check yourmodel.py` for detailed diagnostics
- Check for unsupported Python features (try/except, lambda, async/await)

### Unsupported Features

xnLogo doesn't support all Python features:
- Exception handling (`try`/`except`)
- Lambda functions
- Async/await
- Generators (`yield`)
- Context managers (`with`)
- Dynamic imports

Use simple Python: classes, methods, loops, conditionals, and basic expressions.

### Getting Help

- Check examples in `examples/` directory
- Review documentation at docs/
- File issues on GitHub

## Next Steps

- Read [Architecture](architecture.md) to understand how xnLogo works
- See [Translation Rules](translation-rules.md) for Python→NetLogo conversion details
- Explore the `examples/` directory for complete models
- Try the [Technical Overview](technical-overview.md) for advanced topics
