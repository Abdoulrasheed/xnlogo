# Architecture

This document explains how xnLogo works internally - the compilation pipeline, runtime integration, and key design decisions.

## High-Level Overview

```
┌─────────────────────┐
│  Python Source Code │
│  (@agent classes)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   AST Parser        │
│  - Parse decorators │
│  - Extract classes  │
│  - Extract methods  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Semantic Checks    │
│  - Validate types   │
│  - Check constructs │
│  - Emit diagnostics │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Intermediate Rep   │
│  (AgentSpec, IR)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Python→NetLogo     │
│  Translator         │
│  - AST walking      │
│  - Statement conv.  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  NetLogo Generator  │
│  - Structure gen    │
│  - Template render  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  .nlogox Output     │
│  (XML + NetLogo)    │
└─────────────────────┘
```

## Pipeline Stages

### 1. AST Parsing (`xnlogo/parser/ast_parser.py`)

**Purpose**: Convert Python source files into an Intermediate Representation (IR)

**Key Classes**:
- `Parser` - Main entry point for parsing
- `_ModuleAnalyzer` - AST visitor that extracts agent definitions

**Process**:
1. Read Python source files
2. Parse using Python's `ast` module
3. Visit `ClassDef` nodes decorated with `@agent`
4. Extract state fields (class variables with type hints)
5. Extract behaviors (methods → `AgentBehavior`)
6. **Normalize indentation** - Extract raw statement source and dedent
7. Build `AgentSpec` objects

**Key Innovation**: Indentation normalization handles compound statements (try/except, if/for) that have inconsistent indentation in the raw AST source.

```python
def _statements_from_function(self, func: ast.FunctionDef) -> Iterator[IRStatement]:
    for stmt in func.body:
        source = ast.get_source_segment(self._info.source, stmt)
        # Normalize indentation by finding min indent of continuation lines
        lines = source.split('\n')
        # ... dedent logic ...
        yield RawStatement(source=normalized)
```

### 2. Semantic Validation (`xnlogo/semantics/checks.py`)

**Purpose**: Catch errors and unsupported constructs before code generation

**Validation Passes**:

**Structural Checks** (`run_structural_checks`):
- Ensure at least one agent is defined
- Check for duplicate behavior names
- Validate decorator usage

**Behavioral Checks** (`run_behavioral_checks`):
- Detect unsupported Python constructs:
  - `async`/`await`
  - `lambda` functions
  - `try`/`except` blocks
  - Complex comprehensions
  - `yield`/generators
  - `with` statements
  - `import` statements
  - Nested classes

**Implementation**:
```python
def _check_unsupported_constructs(agent, behavior, diagnostics):
    for statement in behavior.statements:
        tree = ast.parse(statement.source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                unsupported_nodes.add("try/except")
            # ... more checks ...
```

### 3. Intermediate Representation (`xnlogo/ir/`)

**Purpose**: Backend-agnostic representation of the agent-based model

**Key Data Classes**:

```python
@dataclass
class StateField:
    name: str
    type_hint: str | None
    default: str | None

@dataclass
class AgentBehavior:
    name: str
    statements: list[IRStatement]
    schedule_phase: SchedulePhase = SchedulePhase.TICK

@dataclass
class AgentSpec:
    identifier: str
    breed: str | None = None
    state_fields: list[StateField] = field(default_factory=list)
    behaviors: list[AgentBehavior] = field(default_factory=list)

@dataclass
class ModelSpec:
    agents: list[AgentSpec] = field(default_factory=list)
    globals: list[GlobalVar] = field(default_factory=list)
    patches: PatchSpec = field(default_factory=PatchSpec)
    reporters: list[Reporter] = field(default_factory=list)
    random_seed_strategy: SeedConfig = field(default_factory=SeedConfig)
```

**Design Principles**:
- Typed with dataclasses for mypy validation
- Serializable for debugging/testing
- Backend-agnostic (could target Mesa, Repast, etc.)

### 4. Python→NetLogo Translation (`xnlogo/codegen/netlogo_translator.py`)

**Purpose**: Convert individual Python statements to NetLogo syntax

**Key Class**: `NetLogoTranslator(ast.NodeVisitor)`

**Translation Rules**:

| Python | NetLogo |
|--------|---------|
| `self.count = 0` | `set count 0` |
| `self.x = self.x + 1` | `set x (x + 1)` |
| `self.x += 1` | `set x x + 1` |
| `True` / `False` | `true` / `false` |
| `self.field` | `field` |

**AST Visitor Pattern**:
```python
def visit_Assign(self, node: ast.Assign) -> str:
    if isinstance(target, ast.Attribute):
        if target.value.id == "self":
            field_name = target.attr
            value_expr = self.visit(node.value)
            return f"set {field_name} {value_expr}"
```

**Fallback**: If a construct can't be translated, returns Python source with `; UNPARSED:` comment

### 5. NetLogo Code Generation (`xnlogo/codegen/netlogo_generator.py`)

**Purpose**: Orchestrate complete NetLogo file generation

**Responsibilities**:
1. Generate declarations (`turtles-own`, `globals`, `breeds`, `patches-own`)
2. Create `setup` and `go` procedures
3. Render agent behaviors as NetLogo procedures
4. **Call translator** for statement-level conversion
5. Emit XML structure for `.nlogox` format

**Key Methods**:

```python
class NetLogoGenerator:
    def render(self) -> str:
        # Generates complete NetLogo code body
        
    def _render_declarations(self) -> list[str]:
        # Creates variable declarations
        
    def _render_setup(self) -> list[str]:
        # Generates setup procedure
        
    def _render_go(self) -> list[str]:
        # Generates go procedure
        
    def _render_behavior(self, agent, behavior) -> list[str]:
        # Uses translator for each statement
        agent_fields = {field.name for field in agent.state_fields}
        for statement in behavior.statements:
            translated = translate_statement(statement.source, agent_fields)
            lines.append(f"  {translated}")
```

**Template Engine**: Uses Jinja2 for XML structure (`base.nlogox.xml.j2`)

### 6. Runtime Integration (`xnlogo/runtime/`)

**Purpose**: Execute compiled models in NetLogo and collect telemetry

**Key Components**:

**SessionManager** (`session.py`):
- JVM lifecycle management via JPype
- NetLogo 7 headless API bridge
- Deterministic seed handling

**TelemetryBuffer** (`telemetry.py`):
- Streams tick-by-tick data
- Exports to pandas/CSV/JSON
- Custom reporter collection

## Design Decisions

### Why Two Separate Modules (Generator vs Translator)?

**Separation of Concerns**:
- **Generator**: High-level structure (file layout, declarations, procedures)
- **Translator**: Low-level syntax (statement conversion)

**Analogy**: Like a book publisher where:
- Generator = Layout designer (chapters, TOC, page numbers)
- Translator = Language translator (sentence-by-sentence conversion)

### Why Normalize Indentation in Parser?

Python's `ast.get_source_segment()` preserves original indentation, which can be inconsistent for compound statements:

```python
try:                      # 0 spaces
    self.value = 1 / 0   # 12 spaces
except:                   # 8 spaces
    pass                  # 12 spaces
```

When extracted, this can't be parsed standalone. Solution: find minimum indent of continuation lines and dedent uniformly.

### Why AST-Based Translation?

**Alternatives Considered**:
1. String manipulation (regex) - Too fragile
2. Full parser generator (Lark) - Overkill for Python→NetLogo

**Why AST**:
- Python's `ast` module is stable and well-maintained
- Handles all Python syntax automatically
- Provides structured tree for transformation
- Type-safe traversal with visitor pattern

### Why Intermediate Representation?

**Benefits**:
- Decouple parsing from code generation
- Enable multiple backends (Mesa, JSON, etc.)
- Type-safe transformations
- Serializable for testing (golden files)
- Easier to reason about transformations

## Testing Strategy

### Unit Tests
- `test_parser.py` - AST parsing logic
- `test_translator.py` - Python→NetLogo statement conversion
- `test_semantics.py` - Validation passes
- `test_compiler.py` - Integration tests

### Golden Tests
- `test_golden.py` - Compare generated `.nlogox` against reference files
- Catches regressions in output format
- Documents expected behavior

### Test Coverage
- 24 tests covering all major components
- Parser, translator, semantics, compiler, runtime
- Edge cases for indentation, operators, constructs

## Performance Considerations

**Compilation Speed**:
- Single-pass AST parsing
- No expensive transformations
- Jinja2 template caching

**Runtime**:
- JPype bridge adds minimal overhead
- NetLogo's JVM handles simulation
- Telemetry streaming (not batch collection)

## Future Enhancements

1. **Multi-Backend Support** - Target Mesa, Repast from same IR
2. **Incremental Compilation** - Only recompile changed agents
3. **Link Support** - Translate network/graph constructs
4. **Extension Hooks** - Allow custom NetLogo primitives
5. **Debug Info** - Map NetLogo line numbers back to Python source

## Key Files

| File | Purpose |
|------|---------|
| `parser/ast_parser.py` | Python AST → IR conversion |
| `semantics/checks.py` | Validation passes |
| `ir/model.py` | IR data structures |
| `ir/statements.py` | Statement types |
| `codegen/netlogo_translator.py` | Python→NetLogo syntax |
| `codegen/netlogo_generator.py` | File structure generation |
| `runtime/session.py` | NetLogo JVM bridge |
| `cli/commands.py` | CLI entry points |
