# xnLogo User Guide

Complete guide to building NetLogo models with Python.

## Table of Contents

- [Installation](#installation)
- [Your First Model](#your-first-model)
- [Agent Basics](#agent-basics)
- [Working with Breeds](#working-with-breeds)
- [Model Lifecycle](#model-lifecycle)
- [Running Models](#running-models)
- [Telemetry and Data Export](#telemetry-and-data-export)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Installation

### Requirements

- Python 3.10+
- Java 17+ (for NetLogo runtime)
- NetLogo 7.0+ (optional, for viewing models)

### Install xnLogo

```bash
pip install xnlogo
```

### Verify Installation

```bash
xnlogo --version
```

Should output: `xnlogo, version 0.1.0`

## Your First Model

### Step 1: Create a Python File

Create `random_walker.py`:

```python
from xnlogo import agent

@agent
class Walker:
    x: float = 0.0
    y: float = 0.0
    
    def setup(self):
        # Initialize position at origin
        self.x = 0.0
        self.y = 0.0
    
    def move(self):
        # Random walk
        self.x = self.x + 0.1
        self.y = self.y - 0.1
```

### Step 2: Build the Model

```bash
xnlogo build random_walker.py
```

Creates `random_walker.nlogox` in the current directory.

### Step 3: Open in NetLogo

```bash
open random_walker.nlogox
# Or double-click the file in Finder/Explorer
```

### Step 4: Run in NetLogo GUI

1. Click **Setup** button
2. Click **Go** button
3. Watch turtles move!

## Agent Basics

### Defining Fields

Fields become `turtles-own` variables in NetLogo:

```python
@agent
class Bird:
    energy: float = 1.0     # Initial energy
    age: int = 0            # Age in ticks
    alive: bool = True      # Status flag
```

Translates to:
```netlogo
turtles-own [energy age alive]
```

### Field Types

Type hints are for documentation (NetLogo is dynamically typed):

| Python Type | NetLogo Use |
|-------------|-------------|
| `int` | Numeric values |
| `float` | Numeric values |
| `bool` | `true`/`false` |
| `str` | String literals |

### Methods

Methods become NetLogo procedures:

```python
@agent
class Counter:
    count: int = 0
    
    def increment(self):
        self.count = self.count + 1
    
    def reset(self):
        self.count = 0
```

Generates:
```netlogo
to counter-increment
  set count (count + 1)
end

to counter-reset
  set count 0
end
```

## Working with Breeds

### Single Breed

Use the `breed` parameter:

```python
@agent(breed="fish")
class Fish:
    energy: float = 1.0
```

Creates:
```netlogo
breed [fish fish]
fish-own [energy]
```

### Multiple Breeds

Define multiple agent classes:

```python
@agent(breed="shark")
class Shark:
    speed: float = 2.0

@agent(breed="fish")
class Fish:
    speed: float = 1.0
```

## Model Lifecycle

### Setup vs. Go

xnLogo automatically organizes methods:

```python
@agent
class Bird:
    def setup(self):
        # Runs once during setup
        self.x = 0
    
    def move(self):
        # Runs every tick during go
        self.x = self.x + 1
    
    def check_bounds(self):
        # Also runs every tick
        pass
```

- Methods named `setup` → Called in NetLogo's `setup`
- All other methods → Called in NetLogo's `go`

### Execution Order

**Setup Phase**:
1. `clear-all`
2. Instantiate turtles (configured in NetLogo GUI)
3. Call all `*-setup` procedures
4. `reset-ticks`

**Go Phase** (every tick):
1. Call all non-setup procedures
2. `tick`

## Running Models

### Command-Line Execution

Run without opening NetLogo GUI:

```bash
xnlogo run random_walker.nlogox --ticks 100
```

Options:
- `--ticks N`: Run for N ticks
- `--headless`: Don't show GUI (useful for batch runs)
- `--seed N`: Set random seed for reproducibility

### Interactive Mode

```bash
xnlogo run random_walker.nlogox
```

Opens NetLogo GUI where you can:
- Manually click Setup/Go
- Adjust speed slider
- Inspect agent variables
- Create plots/monitors

### Python Runtime

Run directly from Python:

```python
from xnlogo.runtime import Session

# Create session
session = Session("random_walker.nlogox")

# Setup model
session.setup()

# Run 100 ticks
for _ in range(100):
    session.go()

# Get data
data = session.get_turtle_data()
print(data)

# Clean up
session.close()
```

## Telemetry and Data Export

### Automatic Telemetry

xnLogo tracks agent states automatically:

```python
session = Session("my_model.nlogox")
session.setup()

for tick in range(100):
    session.go()
    # Data is collected automatically
```

### Export to JSON

```bash
xnlogo export my_model.nlogox --format json --output results.json --ticks 100
```

**Output** (`results.json`):
```json
{
  "ticks": 100,
  "agents": [
    {"tick": 0, "agent_id": 0, "x": 0.0, "y": 0.0},
    {"tick": 1, "agent_id": 0, "x": 0.1, "y": -0.1},
    ...
  ]
}
```

### Export to CSV

```bash
xnlogo export my_model.nlogox --format csv --output results.csv --ticks 100
```

**Output** (`results.csv`):
```csv
tick,agent_id,x,y
0,0,0.0,0.0
1,0,0.1,-0.1
...
```

### Using Telemetry Data

```python
from xnlogo.runtime import Session
import json

session = Session("flocking.nlogox")
session.setup()

# Run simulation
for _ in range(100):
    session.go()

# Export telemetry
session.export_telemetry("output.json", format="json")

# Load and analyze
with open("output.json") as f:
    data = json.load(f)
    
# Process data
print(f"Total ticks: {data['ticks']}")
print(f"Total agent states: {len(data['agents'])}")
```

## Common Patterns

### Random Initialization

```python
@agent
class Particle:
    vx: float = 0.0
    vy: float = 0.0
    
    def setup(self):
        # Note: random functions not yet supported
        # Set in NetLogo GUI or use runtime API
        pass
```

**Workaround**: Initialize in NetLogo:
```netlogo
to particle-setup
  set vx random-float 2.0 - 1.0  ; Range: -1.0 to 1.0
  set vy random-float 2.0 - 1.0
end
```

### Boundary Checking

```python
@agent
class Wanderer:
    x: float = 0.0
    max_x: float = 10.0
    
    def move(self):
        self.x = self.x + 0.5
    
    def wrap(self):
        # TODO: Add if statement support
        pass
```

**Current Workaround**: Use NetLogo primitives:
```netlogo
to wanderer-wrap
  if x > max_x [ set x x - max_x ]
end
```

### Energy Depletion

```python
@agent
class Creature:
    energy: float = 10.0
    
    def consume_energy(self):
        self.energy = self.energy - 0.1
    
    def check_alive(self):
        # TODO: if energy <= 0, set alive to false
        pass
```

### Multiple Behaviors

```python
@agent
class Bird:
    x: float = 0.0
    
    def flock(self):
        # Flocking behavior
        pass
    
    def avoid_predators(self):
        # Avoidance behavior
        pass
    
    def find_food(self):
        # Foraging behavior
        pass
```

All three methods run every tick in `go`.

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'xnlogo'`

**Solution**:
```bash
pip install --upgrade xnlogo
# Or if developing:
pip install -e .
```

### Build Warnings

**Problem**: `Warning: unsupported construct 'if statement'`

**Explanation**: xnLogo doesn't yet translate all Python constructs.

**Solution**: 
1. Check [translation-rules.md](translation-rules.md) for supported features
2. Use NetLogo code directly for unsupported constructs
3. Wait for future releases (or contribute!)

### NetLogo Not Found

**Problem**: `xnlogo run` fails with Java errors

**Solution**:
```bash
# Check Java installation
java -version  # Should be 17+

# Install Java if needed (macOS)
brew install openjdk@17

# Set JAVA_HOME
export JAVA_HOME=$(/usr/libexec/java_home -v 17)
```

### Generated Code Issues

**Problem**: NetLogo code doesn't work as expected

**Solution**:
1. Run `xnlogo check my_model.py` to validate
2. Open `.nlogox` in text editor and inspect `<code>` section
3. Compare with [translation-rules.md](translation-rules.md)
4. File an issue on GitHub with:
   - Your Python code
   - Expected NetLogo output
   - Actual generated code

### Telemetry Data Missing

**Problem**: `export_telemetry()` produces empty data

**Solution**:
- Ensure you called `session.setup()` before `session.go()`
- Check that model has agents (turtles created)
- Verify you're running `go()` at least once

### Type Errors

**Problem**: Python type checker complains about agent fields

**Explanation**: Type hints are for documentation only.

**Solution**: xnLogo doesn't enforce types - ignore type checker warnings or use `# type: ignore`.

## Next Steps

- **Examples**: See [examples/](../examples/) for complete models
- **Translation Reference**: [translation-rules.md](translation-rules.md)
- **Architecture**: [architecture.md](architecture.md)
- **API Docs**: [api-reference.md](api-reference.md) _(coming soon)_

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourorg/xnlogo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourorg/xnlogo/discussions)
- **Email**: support@xnlogo.dev _(if available)_
