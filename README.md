# xnLogo

A Python-to-NetLogo transpiler and integration toolkit for agent-based modeling.

## Overview

xnLogo enables researchers and developers to write agent-based simulations in Python and compile them to NetLogo. The system provides transpilation (Python to NetLogo code generation) and runtime integration (controlling NetLogo models from Python).

Write models using Python's syntax and tooling, then execute them in NetLogo's simulation environment.

## Installation

```bash
pip install xnlogo
```

Requirements:
- Python 3.10 or later
- NetLogo 7.0 or later (for running compiled models)
- Java 17 or later (for runtime integration)

## Quick Start

Create `counter.py`:

```python
from xnlogo import agent

@agent
class Counter:
    count: int = 0
    
    def increment(self):
        self.count = self.count + 1
    
    def reset(self):
        self.count = 0
```

Compile to NetLogo:

```bash
xnlogo build counter.py
```

This generates `counter.nlogox` which can be opened in NetLogo 7.

## Features

- **Agent-based modeling** - Define agents with state and behaviors using Python classes
- **Semantic validation** - Detect unsupported constructs before compilation
- **NetLogo 7 support** - Generate `.nlogox` files (legacy `.nlogo` also supported)
- **Runtime integration** - Run simulations and collect telemetry from Python
- **Type annotations** - Use Python type hints for agent state fields
- **CLI tools** - Complete command-line interface for validation, compilation, and execution

## Command-Line Interface

| Command | Purpose |
|---------|---------|
| `xnlogo check <path>` | Validate Python code without compiling |
| `xnlogo build <path>` | Compile to NetLogo format |
| `xnlogo run <path>` | Execute simulation in NetLogo |
| `xnlogo export <path>` | Export telemetry data to CSV/JSON |

## Example: Flocking Model

```python
from xnlogo import agent

@agent
class Boid:
    speed: float = 1.0
    heading: float = 0.0
    
    def setup(self):
        self.speed = 0.5 + self.random_float(0.5)
        self.heading = self.random_float(360)
    
    def flock(self):
        neighbors = self.nearby_agents(self, Boid, radius=3)
        if neighbors:
            avg_heading = sum(n.heading for n in neighbors) / len(neighbors)
            turn = (avg_heading - self.heading) * 0.05
            self.heading = self.heading + turn
        self.forward(self.speed)
```

Compile and run:

```bash
xnlogo build flocking.py
xnlogo run flocking.py --ticks 100
```

## Runtime Integration

Execute models and collect data from Python:

```python
from pathlib import Path
from xnlogo.runtime.session import NetLogoSession, SessionConfig

config = SessionConfig(netlogo_home=Path("/Applications/NetLogo 7.0.0"))

with NetLogoSession(config) as session:
    session.load_model(Path("flocking.nlogox"))
    session.command("setup")
    session.repeat("go", 100)
    
    population = session.report("count turtles")
    avg_speed = session.report("mean [speed] of turtles")
```

## Documentation

- [User Guide](docs/user-guide.md) - Detailed usage and examples
- [Architecture](docs/architecture.md) - System design and internals
- [Translation Rules](docs/translation-rules.md) - Python to NetLogo conversion reference
- [Python-NetLogo Compatibility](docs/python-netlogo-compatibility.md) - Feature compatibility matrix

## Project Status

xnLogo is under active development. Core features are stable:

- Agent parsing and compilation
- Python-to-NetLogo statement translation
- Semantic validation
- Runtime integration
- NetLogo 7 `.nlogox` output

Advanced NetLogo features (breeds, links, extensions) are in progress.

## License

MIT License

## Acknowledgments

Built on [NetLogo](https://ccl.northwestern.edu/netlogo/) by Uri Wilensky and the CCL at Northwestern University.
