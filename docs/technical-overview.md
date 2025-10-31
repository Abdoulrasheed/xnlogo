# Technical Overview

## Overview

xnLogo bridges Python and NetLogo for agent-based modeling. The system provides two core capabilities:

1. **Transpilation**: Compile Python simulation logic into NetLogo code
2. **Integration**: Control NetLogo models from Python via headless API

This enables researchers and developers to write models in Python while leveraging NetLogo's simulation runtime.

## Design Goals

### Problem Statement

- NetLogo's domain-specific language lacks Python's ecosystem for data processing, machine learning, and visualization
- Python has no native agent-based simulation primitives
- Existing tools (PyNetLogo) provide control but not transpilation

### Solution Approach

xnLogo provides a compilation pipeline:
- Author models in Python using decorators (`@agent`) and type hints
- Compile to `.nlogox` format with procedures, patches, and turtle definitions
- Execute or monitor simulations via NetLogo's headless API

### Scope

**Supported**:
- Single-world NetLogo models with turtles, patches, and globals
- Deterministic and stochastic procedures
- Reporters and scheduled setup/go loops
- Python 3.10+ with type hints
- NetLogo 7 `.nlogox` XML packaging (legacy `.nlogo` supported)

**Not Yet Supported**:
- Breeds and links
- NetLogo extensions
- GUI widgets
- Custom topologies
- Raw NetLogo code blocks

**Python Subset**:
- Supported: classes, dataclasses, methods, loops, conditionals, comprehensions, `random` module
- Rejected: dynamic metaprogramming, reflection, runtime module imports

**Design Principle**: Maintain standard Python so IDE assistance, static analysis, and unit testing work without custom tooling.

## Architecture

### High-Level Pipeline

```
Python Source Code
    ↓
AST Parser
    ↓
Semantic Checks
    ↓
Intermediate Representation
    ↓
NetLogo Code Generator
    ↓
.nlogox Output
    ↓
NetLogo Runtime (optional)
```

### Modules

- **Frontend**: AST parsing, decorator discovery, semantic validation
- **IR Core**: Typed intermediate representation with scheduling semantics
- **Code Generator**: NetLogo template rendering and code generation
- **Runtime Bridge**: JVM lifecycle management, telemetry streaming, data export
- **CLI**: Command-line interface for validation, compilation, and execution

## Components

### Frontend Parser

Converts Python source to intermediate representation:

1. Parse Python using built-in `ast` module
2. Extract classes, methods, and state fields
3. Validate decorator usage and type hints
4. Build IR describing agents and behaviors

Example input:

```python
@agent
class Rabbit:
    energy: int = 10
    
    def move(self):
        self.energy -= 1
```

Intermediate representation:

```python
AgentSpec(
    identifier="Rabbit",
    state_fields=[StateField(name="energy", type_hint="int", default="10")],
    behaviors=[AgentBehavior(name="move", statements=[...])]
)
```

### Intermediate Representation

The IR abstracts simulation logic independent of NetLogo syntax:

```python
@dataclass
class AgentBehavior:
    name: str
    statements: list[IRStatement]
    schedule_phase: SchedulePhase  # SETUP, TICK, CUSTOM
    
@dataclass
class AgentSpec:
    identifier: str
    breed: Optional[str]
    state_fields: list[StateField]
    behaviors: list[AgentBehavior]
    
@dataclass
class ModelSpec:
    globals: list[GlobalVar]
    agents: list[AgentSpec]
    patches: PatchSpec
    reporters: list[Reporter]
```

The IR uses typed dataclasses for type safety and enables backend-agnostic extensions (future support for Mesa, Repast, etc.).

### Semantic Validation

Three-pass validation pipeline:

**Structural Checks**:
- Verify decorator usage on classes and methods
- Detect unsupported Python constructs
- Enforce type hints on state fields

**Behavioral Checks**:
- Validate variable references
- Enforce tick-safe operations
- Flag unexpressible side effects

**Lint and Guidance**:
- Warn about performance pitfalls (unbounded recursion, heavy allocations)
- Suggest NetLogo idioms where applicable

Diagnostics include source spans and remediation suggestions.

### Code Generator

Converts IR to NetLogo source:

- Uses Jinja2 templates for code rendering
- Generates `.nlogox` (XML) or `.nlogo` (legacy) containers
- Handles declarations: `turtles-own`, `patches-own`, `globals`
- Generates procedures: `setup`, `go`, agent behaviors
- Injects interface metadata (widgets, plots, monitors)
- Provides default widgets (setup/go buttons) unless disabled

Example output:

```netlogo
turtles-own [energy]

to setup
  clear-all
  create-turtles 10 [
    set energy 10
  ]
  reset-ticks
end

to go
  ask turtles [
    set energy energy - 1
  ]
  tick
end
```

### Runtime Integration

Python-to-NetLogo bridge via JPype:

- Manage JVM lifecycle and classpath
- Load and execute `.nlogox` models
- Stream telemetry (ticks, metrics, custom reporters)
- Export data to CSV, JSON, or pandas DataFrames

Example:

```python
from pathlib import Path
from xnlogo.runtime.session import NetLogoSession, SessionConfig

config = SessionConfig(netlogo_home=Path("/Applications/NetLogo 7.0.0"))

with NetLogoSession(config) as session:
    session.load_model(Path("model.nlogox"))
    session.command("setup")
    session.repeat("go", 100)
    
    metrics = {
        "population": session.report("count turtles"),
        "avg_energy": session.report("mean [energy] of turtles"),
    }
```

Environment variables `XNLOGO_NETLOGO_HOME` or `NETLOGO_HOME` configure the NetLogo installation path.

## Workflow

1. **Author** - Write agent models in Python with `@agent` decorator
2. **Validate** - Run `xnlogo check` for structural and semantic checks
3. **Compile** - Use `xnlogo build` to generate `.nlogox` file
4. **Execute** - Run `xnlogo run` to execute in NetLogo headless mode
5. **Analyze** - Export telemetry with `xnlogo export` for analysis

### CLI Commands

| Command | Description | Options |
|---------|-------------|---------|
| `xnlogo check <path>` | Validate without compiling | `--strict` treats warnings as errors |
| `xnlogo build <path>` | Compile to NetLogo | `--format {nlogox,nlogo}`, `--output-dir DIR`, `--no-default-widgets` |
| `xnlogo run <path>` | Execute in NetLogo | `--ticks N`, `--headless/--gui`, `--seed VALUE`, `--profile` |
| `xnlogo export <path>` | Export telemetry data | `--format {csv,json}`, `--output FILE` |

## Implementation

| Component | Technology |
|-----------|-----------|
| Parser | Python `ast`, `inspect`, `typing` |
| IR | `dataclasses`, `enum` |
| Code Generation | Jinja2, `xml.etree` |
| Runtime | JPype, NetLogo Headless API |
| CLI | Typer |
| Testing | pytest, golden file comparison |

## Extension Points

- **Multi-backend support**: Target Mesa or JSON event logs from same IR
- **Reverse translation**: Convert NetLogo models to Python classes
- **Live visualization**: Stream agent data to Python dashboards
- **Breeds and links**: Extend IR for multi-species interactions
- **Custom environments**: Map Python spatial structures to NetLogo grids
