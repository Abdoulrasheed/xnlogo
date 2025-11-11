# Architecture

This document explains the internal design of xnLogo: the compilation pipeline, intermediate representation, and code generation strategy.

## Overview

xnLogo is a Python-to-NetLogo transpiler that converts Python agent-based models into native NetLogo code. The system consists of three major subsystems:

1. **Parser**: Converts Python source into an intermediate representation
2. **Code Generator**: Transforms IR into NetLogo code
3. **Runtime**: Executes models via NetLogo's headless API (optional)

## Compilation Pipeline

The transpilation process follows a multi-stage pipeline:

### Stage 1: Python Parsing

The parser (`xnlogo/parser/ast_parser.py`) analyzes Python source files using Python's built-in `ast` module. It identifies Model subclasses and extracts their structure.

**Key Operations:**
- Locate classes that inherit from `Model`
- Extract instance variables (model state) from `__init__`
- Identify methods and categorize them by purpose (setup, go, custom procedures)
- Extract breed definitions via `breed()` calls
- Capture UI widgets from `ui()` or `widgets()` methods
- Extract documentation from `info()` methods

**Example Input:**
```python
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

The parser builds an internal model representation capturing the structure, state, and behavior.

### Stage 2: Semantic Validation

The validator (`xnlogo/semantics/checks.py`) examines the IR for errors and unsupported constructs before code generation.

**Validation Rules:**
- Check for required methods (at minimum, a setup or go method)
- Detect unsupported Python features (async/await, try/except, lambda, yield, with statements)
- Validate state field types
- Ensure breed definitions are well-formed

**Error Reporting:**
All validation errors are collected into a diagnostic bag with file locations, making it easy to identify and fix issues.

### Stage 3: Intermediate Representation

The IR (`xnlogo/ir/model.py`) provides a backend-agnostic representation of the model. This decouples parsing from code generation, enabling multiple output formats.

**Core IR Types:**
- `ModelSpec`: Complete model structure with agents, globals, patches
- `AgentSpec`: Agent breed with state fields and behaviors
- `AgentBehavior`: A procedure with its statements and scheduling phase
- `StateField`: Variable declaration with name, type, and default value
- `GlobalVar`: Model-level variable
- `PatchSpec`: Patch properties

**Design Benefits:**
- Type-safe representation (validated with dataclasses)
- Serializable for testing and debugging
- Backend-independent (could target other ABM frameworks)
- Clear separation of concerns

### Stage 4: Statement Translation

The translator (`xnlogo/codegen/netlogo_translator.py`) converts individual Python statements to NetLogo syntax using AST traversal.

**Translation Strategy:**
The translator walks Python's abstract syntax tree and generates equivalent NetLogo code based on node types. It understands NetLogo's syntax requirements, such as prefix notation for operators and the distinction between commands and reporters.

**Key Translations:**
- Attribute assignment: `self.x = 5` → `set x 5`
- Augmented assignment: `self.x += 1` → `set x (x + 1)`
- Boolean literals: `True`/`False` → `true`/`false`
- Self references: Strip `self.` prefix when accessing state
- Method calls: Convert to NetLogo procedure calls

**Local Variables:**
The translator tracks variable declarations to correctly use `let` for new local variables versus `set` for existing variables. This prevents polluting the global namespace.

### Stage 5: NetLogo Code Generation

The generator (`xnlogo/codegen/netlogo_generator.py`) orchestrates the creation of complete NetLogo files.

**Responsibilities:**
- Generate variable declarations (globals, breeds, turtles-own, patches-own)
- Create setup and go procedures
- Render custom procedures from model methods
- Generate reporter procedures
- Emit XML structure for .nlogox format
- Include UI widgets and documentation

**Code Structure:**
NetLogo code is organized into sections:
1. Declarations (globals, breeds, own variables)
2. Setup procedure
3. Go procedure (default or user-defined)
4. Custom procedures
5. Reporter procedures

**Template Engine:**
The generator uses Jinja2 templates to render the final XML structure, combining the generated NetLogo code with widget definitions and model info.

### Stage 6: Output Formats

xnLogo supports two output formats:

**nlogox (Preferred):**
XML-based format introduced in NetLogo 7. Contains NetLogo code, UI widgets, model info, and metadata in structured XML.

**nlogo (Legacy):**
Plain text format from earlier NetLogo versions. Supported for compatibility with older tools.

## Key Design Decisions

### Model Subclass Pattern

xnLogo uses Python class inheritance rather than decorators. Models extend the `Model` base class, making the API feel natural to Python developers and enabling IDE support, type checking, and documentation.

### Intermediate Representation

The IR layer decouples parsing from code generation. This design:
- Makes the codebase more maintainable
- Enables testing of each stage independently
- Allows future support for multiple backends (Mesa, Repast, etc.)
- Provides clear contracts between components

### AST-Based Translation

Using Python's `ast` module for translation provides:
- Robust parsing of all Python syntax
- Type-safe tree traversal
- No regex fragility
- Automatic handling of operator precedence

Alternative approaches (string manipulation, custom parsers) would be more error-prone and harder to maintain.

### Statement-Level Granularity

The translator works at the statement level rather than expression level. Each Python statement becomes one or more NetLogo statements. This granularity provides better error messages and easier debugging.

### Indentation Normalization

Python's `ast.get_source_segment()` preserves original indentation, which can be inconsistent for compound statements. The parser normalizes indentation by detecting the minimum indent level and adjusting all lines accordingly. This ensures extracted code can be parsed standalone.

## Runtime Integration

The runtime subsystem (`xnlogo/runtime/`) provides optional integration with NetLogo's headless API for executing models directly from Python.

**Components:**
- Session management: JVM lifecycle and workspace creation
- Command execution: Issue NetLogo commands programmatically
- Reporter evaluation: Query model state
- Telemetry collection: Stream tick-by-tick data for analysis

**Use Cases:**
- Parameter sweeps and sensitivity analysis
- Automated testing of models
- Integration with Python analysis pipelines
- Batch execution for research

## Testing Strategy

### Unit Tests
Each subsystem has focused unit tests:
- Parser tests verify IR construction from Python code
- Translator tests validate statement-level conversion
- Semantic tests check validation logic
- Compiler tests ensure end-to-end compilation

### Golden Tests
Golden tests compare generated NetLogo output against reference files. These catch regressions in code generation and document expected behavior.

### Integration Tests
End-to-end tests verify the complete pipeline from Python source to runnable NetLogo models.

## Performance Characteristics

**Compilation Speed:**
- Single-pass parsing minimizes overhead
- AST traversal is efficient (O(n) in code size)
- Template rendering is fast with Jinja2 caching

**Output Size:**
Generated NetLogo code is comparable to hand-written code. No significant bloat from transpilation.

**Runtime:**
When using the runtime integration, the JPype bridge adds minimal overhead. NetLogo's JVM handles the actual simulation with native performance.

## Module Structure

```
xnlogo/
├── parser/          # Python → IR conversion
│   ├── ast_parser.py       # Main parser
│   └── py_to_netlogo.py    # Statement translator helper
├── semantics/       # Validation
│   ├── checks.py           # Validation rules
│   └── diagnostics.py      # Error collection
├── ir/              # Intermediate representation
│   ├── model.py            # Core IR types
│   └── statements.py       # Statement types
├── codegen/         # IR → NetLogo
│   ├── netlogo_generator.py   # Main generator
│   ├── netlogo_translator.py  # Statement translation
│   └── templates/              # Jinja2 templates
├── runtime/         # Execution (optional)
│   ├── api.py              # Python API
│   ├── session.py          # NetLogo integration
│   ├── telemetry.py        # Data collection
│   └── ui.py               # Widget definitions
├── cli/             # Command-line interface
│   └── commands.py         # CLI commands
└── compiler.py      # Main entry point
```

## Extension Points

The architecture supports several extension mechanisms:

**Custom Backends:**
Implement a new code generator to target different ABM frameworks (Mesa, Repast, etc.) using the same IR.

**Additional Validations:**
Add semantic checks by extending the validation pass.

**Custom Primitives:**
Future support for NetLogo extensions could map Python functions to extension primitives.

**Analysis Tools:**
The IR can be analyzed for metrics like complexity, agent coupling, or behavior patterns.
