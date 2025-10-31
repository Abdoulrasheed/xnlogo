# Python → NetLogo Translation Rules

This document describes how xnLogo translates Python code into NetLogo syntax.

## Overview

xnLogo translates Python agent behaviors into NetLogo procedures. The translation happens at two levels:

1. **Structural Level**: Agent classes → NetLogo procedures and declarations
2. **Statement Level**: Python statements → NetLogo code

## Structural Translation

### Agent Classes

**Python**:
```python
@agent
class Counter:
    count: int = 0
    
    def increment(self):
        self.count = self.count + 1
```

**NetLogo**:
```netlogo
turtles-own [count]

to counter-increment
  set count (count + 1)
end
```

### Breeds

**Python**:
```python
@agent(breed="fish")
class Fish:
    energy: float = 1.0
```

**NetLogo**:
```netlogo
breed [fish fish]
fish-own [energy]
```

### Setup and Go

Methods are automatically assigned to `setup` or `go` based on their names:

**Python**:
```python
@agent
class Bird:
    def setup(self):
        self.x = 0
    
    def move(self):  # Runs every tick
        self.x = self.x + 1
```

**NetLogo**:
```netlogo
to setup
  clear-all
  ask turtles [ bird-setup ]
  reset-ticks
end

to go
  ask turtles [ bird-move ]
  tick
end
```

## Statement Translation

### Assignment

| Python | NetLogo |
|--------|---------|
| `self.x = 5` | `set x 5` |
| `self.x = self.y` | `set x y` |
| `x = 10` | `set x 10` |

### Augmented Assignment

| Python | NetLogo |
|--------|---------|
| `self.x += 1` | `set x x + 1` |
| `self.x -= 2` | `set x x - 2` |
| `self.x *= 3` | `set x x * 3` |
| `self.x /= 4` | `set x x / 4` |

### Attribute Access

| Python | NetLogo |
|--------|---------|
| `self.count` | `count` |
| `self.energy` | `energy` |

The `self.` prefix is automatically removed for agent fields.

### Binary Operations

| Python | NetLogo |
|--------|---------|
| `self.x + self.y` | `(x + y)` |
| `self.x - 5` | `(x - 5)` |
| `self.x * 2` | `(x * 2)` |
| `self.x / 4` | `(x / 4)` |
| `self.x % 3` | `(x mod 3)` |

**Note**: Parentheses are added to preserve order of operations.

### Boolean Constants

| Python | NetLogo |
|--------|---------|
| `True` | `true` |
| `False` | `false` |

### String Constants

| Python | NetLogo |
|--------|---------|
| `"hello"` | `"hello"` |
| `'world'` | `"world"` |

Strings are preserved, with single quotes converted to double quotes.

### Numeric Constants

| Python | NetLogo |
|--------|---------|
| `42` | `42` |
| `3.14` | `3.14` |
| `-10` | `-10` |

## Unsupported Constructs

These Python features will generate **warnings** during semantic validation:

### Control Flow

****Not Yet Supported**:
- `if`/`elif`/`else` statements
- `for` loops
- `while` loops
- `match`/`case` statements

**Workaround**: Use NetLogo primitives directly (planned for future release)

### Asynchronous Code

****Not Supported**:
```python
async def move(self):
    await something()
```

**Reason**: NetLogo is synchronous

### Exception Handling

****Not Supported**:
```python
try:
    self.value = 1 / 0
except ZeroDivisionError:
    self.value = 0
```

**Reason**: NetLogo doesn't have exception handling

### Lambda Functions

****Not Supported**:
```python
squared = lambda x: x * x
```

**Workaround**: Use regular functions

### Comprehensions

****Limited Support**:
```python
# Simple comprehensions MAY work
values = [x + 1 for x in range(10)]

# Complex comprehensions will fail
values = [x + y for x in range(10) for y in range(10) if x != y]
```

### Generators

****Not Supported**:
```python
def count_up(self):
    yield 1
    yield 2
```

### With Statements

****Not Supported**:
```python
with open("file.txt") as f:
    data = f.read()
```

### Import Statements

****Not Supported**:
```python
import math
from random import randint
```

**Reason**: NetLogo has its own module system

### Nested Classes

****Not Supported**:
```python
class Outer:
    class Inner:
        pass
```

## Advanced Features

### Globals

**Python**:
```python
@agent(globals={"speed": "float", "max-energy": "float"})
class Bird:
    def setup(self):
        self.globals["speed"] = 1.5
```

**NetLogo**:
```netlogo
globals [speed max-energy]

to bird-setup
  set speed 1.5
end
```

### Patches

**Python**:
```python
@agent(patches={"food": "float", "water": "float"})
class Environment:
    def setup(self):
        self.patches.ask("set food random-float 1.0")
```

**NetLogo**:
```netlogo
patches-own [food water]

to environment-setup
  ask patches [ set food random-float 1.0 ]
end
```

### Turtles (Agent Instances)

**Python**:
```python
@agent(turtles={"age": "int"})
class Creature:
    def setup(self):
        self.turtles.create(50, ["initialize"])
```

**NetLogo**:
```netlogo
to creature-setup
  create-turtles 50 [
    creature-initialize
  ]
end
```

## Type Hints

Type hints are used for documentation but not enforced:

```python
@agent
class Bird:
    x: int = 0        # Generates: turtles-own [x]
    y: float = 0.0    # Type hint is informational only
    alive: bool = True
```

**NetLogo** (types are not declared):
```netlogo
turtles-own [x y alive]
```

## Translation Process

1. **Parse**: Python AST → IR (Intermediate Representation)
2. **Validate**: Check for unsupported constructs
3. **Translate**: Each statement through AST visitor
4. **Generate**: Combine into NetLogo file structure
5. **Emit**: Write `.nlogox` XML file

## Debugging Translation

### Check Mode

Validate without compiling:
```bash
xnlogo check my_model.py
```

Shows warnings about unsupported constructs.

### Build with Verbose Output

```bash
xnlogo build my_model.py --verbose
```

### Inspect Generated Code

The `.nlogox` file is XML. View the NetLogo code:

```bash
# Extract code section
grep -A 100 '<code>' my_model.nlogox
```

Or open in NetLogo and view the Code tab.

## Examples

### Complete Translation

**Python** (`counter.py`):
```python
from xnlogo import agent

@agent
class Counter:
    count: int = 0
    max_count: int = 10
    
    def increment(self):
        if self.count < self.max_count:  # Note: if not yet supported
            self.count = self.count + 1
    
    def reset(self):
        self.count = 0
    
    def double(self):
        self.count = self.count * 2
```

**NetLogo** (`counter.nlogox`):
```netlogo
turtles-own [count max_count]

to setup
  clear-all
  ; TODO: instantiate Counter
  reset-ticks
end

to go
  ask turtles [ counter-increment ]
  ask turtles [ counter-reset ]
  ask turtles [ counter-double ]
  tick
end

to counter-increment
  ; if statement not yet translated
  set count (count + 1)
end

to counter-reset
  set count 0
end

to counter-double
  set count (count * 2)
end
```

## Future Enhancements

Planned translation features:

- [ ] `if`/`else` statements
- [ ] `for` loops (map to `repeat` or `ask`)
- [ ] `while` loops
- [ ] Method calls (`self.move()`)
- [ ] List operations
- [ ] Dictionary operations
- [ ] Comparison operators (`>`, `<`, `==`, etc.)
- [ ] Logical operators (`and`, `or`, `not`)

## Getting Help

If you encounter translation issues:

1. Run `xnlogo check` to see validation errors
2. Check this guide for supported constructs
3. Look at [examples/](../examples/) for working models
4. Open an issue on GitHub with your Python code
