# Technical Overview

## Overview

xnLogo is a Python-to-NetLogo compiler that enables writing agent-based models in Python and running them in NetLogo. The system provides a complete toolchain from Python source code to executable NetLogo models.

## Design Goals

### Problem Statement

NetLogo excels at agent-based simulation with excellent spatial primitives and visualization, but its domain-specific language lacks Python's ecosystem for data processing, machine learning, testing, and modern development tools. Python has rich libraries and tooling but no native agent-based simulation runtime.

### Solution Approach

xnLogo bridges this gap through compilation rather than integration:
- Write models in Python using standard class syntax
- Compile to NetLogo `.nlogox` format with full procedure and agent definitions
- Execute in NetLogo's proven simulation runtime
- Optionally control NetLogo from Python via headless API

This approach preserves Python's development experience while leveraging NetLogo's simulation capabilities.

## Architecture

xnLogo uses a multi-stage compilation pipeline to transform Python code into NetLogo models.

### Compilation Pipeline

The compilation process consists of six stages:

**Stage 1: Source Parsing**
Parse Python source code into an Abstract Syntax Tree using Python's built-in `ast` module. Extract model class definitions, methods, and state variables.

**Stage 2: Semantic Analysis**
Validate the Python code follows xnLogo's constraints. Check for unsupported language features, validate breed definitions, ensure proper Model inheritance, and verify method signatures.

**Stage 3: IR Construction**
Build an Intermediate Representation that captures model structure independent of both Python and NetLogo syntax. The IR represents agents, behaviors, state, and scheduling semantics in a platform-neutral format.

**Stage 4: Statement Translation**
Translate individual Python statements into NetLogo equivalents. Convert assignments, expressions, control flow, and method calls using a visitor pattern over the Python AST.

**Stage 5: Code Generation**
Generate complete NetLogo source code from the IR using Jinja2 templates. Produce breed definitions, state declarations, procedures, and any UI widget definitions.

**Stage 6: Packaging**
Package the generated NetLogo code into `.nlogox` (XML) or `.nlogo` (legacy) format with metadata, version information, and widget layout.

### Key Components

**Frontend: Parser and Validator**
The frontend handles Python source code. The AST parser (`xnlogo.parser.ast_parser`) extracts model structure, while the semantic validator (`xnlogo.semantics`) checks for errors and unsupported features before compilation proceeds.

**Core: Intermediate Representation**
The IR (`xnlogo.ir`) provides a typed, platform-neutral model representation. Using Python dataclasses, it defines agents, behaviors, state fields, and scheduling semantics. This abstraction enables future backends beyond NetLogo.

**Backend: Code Generator**
The code generator (`xnlogo.codegen.netlogo_generator`) transforms IR into NetLogo code. Template-based generation ensures consistent output format and makes it easy to extend or modify NetLogo output patterns.

**Runtime: NetLogo Integration**
The runtime bridge (`xnlogo.runtime`) provides optional Python control over NetLogo execution. Using JPype to interface with NetLogo's JVM-based headless API, it enables programmatic model execution, telemetry collection, and data export.

**CLI: Command Interface**
The command-line interface (`xnlogo.cli`) provides user-facing commands for validation, compilation, execution, and data export. Built with Typer, it offers a clean, documented command structure.

## Supported Python Features

xnLogo supports a pragmatic subset of Python designed for agent-based modeling:

**Classes and State**
- Model subclasses defining simulation structure
- Instance variables for agent and global state
- Type hints for documentation (not enforced at runtime)

**Methods and Behaviors**
- Instance methods become NetLogo procedures
- `setup()` and `go()` methods map to standard NetLogo lifecycle
- Custom methods for reusable logic

**Control Flow**
- If/elif/else conditionals
- For loops over ranges and sequences
- While loops with conditions
- Return statements

**Expressions**
- Arithmetic operators (+, -, *, /, %, **)
- Comparison operators (<, <=, >, >=, ==, !=)
- Boolean operators (and, or, not)
- Attribute access, method calls, subscripts

**Built-in Functions**
- Math functions (abs, round, max, min, sum)
- Sequence functions (len, range, sorted)
- Type conversions (int, float, str, bool)
- Output functions (print)

**Data Structures**
- Lists with indexing, slicing, and common methods
- Dictionaries for agent property access patterns
- Simple tuples (converted to lists)

**Agent Features**
- Breed definitions via `breed()` function
- Agent creation and property access
- Spatial operations (movement, sensing)
- Agent lifecycle (creation, destruction)

## Unsupported Features

The following Python features are not supported as they don't map cleanly to NetLogo:

**Dynamic Features**
- Runtime imports and module loading
- Reflection and metaprogramming
- Dynamic class creation
- exec/eval statements

**Advanced Control Flow**
- Exception handling (try/except/finally)
- Context managers (with statements)
- Generators and yield
- Async/await and coroutines

**Advanced Functions**
- Lambda expressions (planned for future)
- Decorators (except compile-time Model marker)
- Closures with captured state
- *args and **kwargs

**Object-Oriented**
- Class inheritance (beyond Model base class)
- Multiple inheritance
- Properties and descriptors
- Magic methods (except `__init__`)
- Static and class methods

These limitations keep the compiler tractable and ensure generated NetLogo code is maintainable and performant.

## API Design

### Model Definition

Models inherit from the `Model` base class:

```python
from xnlogo.runtime import Model, reset_ticks, tick

class CounterModel(Model):
    def __init__(self):
        super().__init__()
        self.counter = 0
    
    def setup(self):
        reset_ticks()
        self.counter = 0
    
    def go(self):
        self.counter += 1
        tick()
```

Instance variables in `__init__` become NetLogo globals. Methods become procedures.

### Breed Definition

Create agent types using the `breed()` function:

```python
from xnlogo.runtime import breed

class EcosystemModel(Model):
    def __init__(self):
        super().__init__()
        self.rabbits = breed("rabbits", "rabbit")
        self.foxes = breed("foxes", "fox")
```

Breed instances provide creation and querying methods.

### UI Definition

Define widgets using the `ui()` or `widgets()` method:

```python
from xnlogo.runtime import View, Button, Monitor, Slider

def ui(self):
    self.add_widget(View(x=385, y=10, width=610, height=631))
    self.add_widget(Button(command="setup", x=15, y=10, width=150, height=60))
    self.add_widget(Button(command="go", x=175, y=10, width=150, height=60, forever=True))
    self.add_widget(Monitor(expression="count turtles", x=15, y=150))
    self.add_widget(Slider(variable="population", min_val=0, max_val=500, x=15, y=230))
```

Widget definitions are declarative and generate NetLogo XML interface metadata.

### Model Documentation

Provide model documentation via the `info()` method:

```python
def info(self):
    return """
## WHAT IS IT?

This model simulates...

## HOW TO USE IT

1. Click setup
2. Click go
"""
```

## Intermediate Representation

The IR uses typed Python dataclasses to represent model structure:

**Core IR Types**

`ModelSpec`: Top-level model representation
- Global variables and their types
- Agent breeds and their specifications
- Patch specifications
- Reporter functions
- Metadata (title, author, version)

`BreedSpec`: Agent type definition
- Breed name and singular form
- State fields owned by the breed
- Behavior methods
- Parent breed (for future inheritance)

`BehaviorSpec`: Method representation
- Behavior name and parameters
- Translated NetLogo statements
- Schedule phase (setup, go, custom)
- Return type information

`StateField`: Variable declaration
- Field name and identifier
- Type hint (for documentation)
- Default value expression
- Scope (global, breed-owned, patch-owned)

**Statement IR**

The IR includes typed representations for all statement forms:
- Assignments and augmented assignments
- Conditionals (if/elif/else)
- Loops (for, while)
- Method calls and returns
- Expressions (operators, comparisons, literals)

This typed IR enables validation, optimization passes, and alternative backends.

## Code Generation

Code generation uses Jinja2 templates with NetLogo-specific filters and utilities.

**Template Structure**

Templates are organized by output section:
- `declarations.j2`: Breed and state declarations
- `procedures.j2`: Procedure definitions
- `setup.j2`: Setup procedure structure
- `go.j2`: Go procedure structure
- `widgets.j2`: UI widget XML

**Generation Process**

1. Load appropriate template for target format (nlogox or nlogo)
2. Render declarations section with breed and state information
3. Generate procedure definitions from behavior specs
4. Inject setup and go procedures with proper scheduling
5. Generate widget XML if UI definitions exist
6. Package into target format with metadata

**Output Formats**

`.nlogox` (default): XML-based format introduced in NetLogo 7.0. Structured, easy to parse, supports all NetLogo features.

`.nlogo` (legacy): Plain text format from NetLogo 6.x and earlier. Still supported for compatibility but less structured.

## Runtime Integration

The runtime module enables Python-side control of compiled NetLogo models:

**Session Management**

Create and manage NetLogo execution sessions:
```python
from xnlogo.runtime.session import NetLogoSession, SessionConfig

config = SessionConfig(netlogo_home=Path("/path/to/NetLogo"))
with NetLogoSession(config) as session:
    session.load_model(Path("model.nlogox"))
    session.command("setup")
    session.repeat("go", 100)
```

**Command Execution**

Execute NetLogo commands and reporter expressions:
```python
session.command("setup")
session.command("ask turtles [ fd 1 ]")
population = session.report("count turtles")
average_energy = session.report("mean [energy] of turtles")
```

**Data Collection**

Stream telemetry and export simulation data:
```python
# Collect time series
metrics = []
for _ in range(100):
    session.command("go")
    metrics.append({
        "tick": session.report("ticks"),
        "population": session.report("count turtles"),
        "energy": session.report("mean [energy] of turtles")
    })

# Export to pandas
import pandas as pd
df = pd.DataFrame(metrics)
df.to_csv("results.csv")
```

**Configuration**

Configure NetLogo runtime via environment variables:
- `XNLOGO_NETLOGO_HOME`: NetLogo installation directory
- `NETLOGO_HOME`: Alternative environment variable name
- Or pass explicitly to `SessionConfig`

## Testing Strategy

xnLogo uses multiple testing approaches:

**Unit Tests**
Test individual components in isolation. Translator tests validate statement conversion. Parser tests verify AST extraction. Semantic tests check validation logic.

**Golden Reference Tests**
Compare generated NetLogo code against known-good reference outputs. Ensures compilation output remains consistent across changes. Uses normalized XML comparison to ignore formatting differences.

**Validation Tests**
Verify generated NetLogo code is syntactically valid. Check for balanced brackets and parentheses. Ensure no Python syntax leaks into output. Validate generated code against NetLogo's parser.

**Integration Tests**
Test complete workflows from Python source to NetLogo execution. Verify models compile and run correctly. Check telemetry collection and data export.

## Performance Considerations

**Compilation Performance**
Compilation is typically fast (under 1 second for most models). The bottleneck is usually Jinja2 template rendering. For large models with many procedures, consider splitting into multiple breeds or simplifying procedure structure.

**Runtime Performance**
Generated NetLogo code performs comparably to hand-written NetLogo. The compiler generates idiomatic NetLogo patterns. No runtime overhead from Python - the Python code is fully compiled away.

**Memory Usage**
Memory usage is proportional to model size and AST complexity. The IR is lightweight and uses dataclasses efficiently. For very large models, compilation memory usage may be noticeable but is typically not a concern.

## Extension Points

The architecture supports several extension possibilities:

**Alternative Backends**
The IR abstraction enables targeting other agent-based frameworks. Potential targets include Mesa (Python ABM framework), Repast (Java ABM toolkit), or custom JSON event logs for replay.

**Optimization Passes**
Insert optimization passes between IR construction and code generation. Potential optimizations include dead code elimination, constant folding, loop unrolling, and spatial query optimization.

**Language Features**
Extend supported Python features by adding new statement translators and IR types. The visitor pattern makes adding new constructs straightforward.

**Static Analysis**
Build additional analysis passes over the IR. Potential analyses include performance linting, spatial complexity analysis, determinism checking, and model verification.

**Reverse Compilation**
Develop NetLogo-to-Python translator to import existing NetLogo models. Would parse NetLogo code, construct IR, and generate Python Model classes.

## Implementation Technologies

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Parser | Python `ast` module | Standard library, robust, well-documented |
| IR | `dataclasses` | Type-safe, immutable, minimal boilerplate |
| Code Generation | Jinja2 | Powerful templating, NetLogo-friendly syntax |
| Runtime | JPype | Mature JVM bridge, NetLogo Java API access |
| CLI | Typer | Modern CLI framework, automatic help generation |
| Testing | pytest | Standard Python testing, excellent plugin ecosystem |
| Type Checking | mypy | Catches type errors, improves code quality |
| Validation | Custom AST visitors | Full control over error messages and checks |

## Future Directions

**Short Term**
- Lambda expression support for functional patterns
- Enhanced list comprehensions
- More built-in function support
- Performance optimization passes

**Medium Term**
- Link support for network models
- NetLogo extension integration
- Live visualization from Python
- Model parameter sweeps and batch execution

**Long Term**
- Multiple backend support (Mesa, Repast)
- Reverse compilation (NetLogo to Python)
- Advanced static analysis and verification
- Interactive debugging with NetLogo

## Conclusion

xnLogo provides a complete toolchain for agent-based modeling in Python. The multi-stage compilation pipeline preserves Python's development experience while generating efficient, idiomatic NetLogo code. The architecture is designed for extensibility, maintainability, and future growth.
