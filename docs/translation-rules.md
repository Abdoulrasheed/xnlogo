# Python → NetLogo Translation Rules

Complete reference for how xnLogo translates Python code into NetLogo.

## Overview

xnLogo translates Python models into NetLogo code at two levels:

1. **Structural Translation**: Model classes → NetLogo declarations and procedures
2. **Statement Translation**: Python statements → NetLogo code

This document describes both levels in detail.

## Structural Translation

### Model Classes

**Python**:
```python
from xnlogo.runtime import Model, reset_ticks, tick

class CounterModel(Model):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.max_value = 100
    
    def setup(self):
        reset_ticks()
        self.counter = 0
    
    def go(self):
        self.counter += 1
        tick()
```

**NetLogo**:
```netlogo
globals [counter max_value]

to setup
  reset-ticks
  set counter 0
end

to go
  set counter (counter + 1)
  tick
end
```

Instance variables in `__init__` become NetLogo globals. Methods become procedures.

### Breed Definitions

**Python**:
```python
from xnlogo.runtime import Model, breed

class EcosystemModel(Model):
    def __init__(self):
        super().__init__()
        self.rabbits = breed("rabbits", "rabbit")
        self.foxes = breed("foxes", "fox")
    
    def setup(self):
        for i in range(50):
            rabbit = self.rabbits.create(1)
            rabbit.energy = 10
```

**NetLogo**:
```netlogo
breed [rabbits rabbit]
breed [foxes fox]

rabbits-own [energy]
foxes-own []

to setup
  repeat 50 [
    create-rabbits 1 [
      set energy 10
    ]
  ]
end
```

The `breed()` function creates NetLogo breed declarations. Agent properties become breed-owned variables.

### Methods as Procedures

All model methods become NetLogo procedures:

**Python**:
```python
def increment_counter(self):
    self.counter += 1

def reset_counter(self):
    self.counter = 0

def double_counter(self):
    self.counter = self.counter * 2
```

**NetLogo**:
```netlogo
to increment-counter
  set counter (counter + 1)
end

to reset-counter
  set counter 0
end

to double-counter
  set counter (counter * 2)
end
```

Method names are converted from snake_case to kebab-case.

## Statement Translation

### Variable Assignment

| Python | NetLogo |
|--------|---------|
| `self.x = 5` | `set x 5` |
| `self.x = self.y` | `set x y` |
| `x = 10` | `let x 10` (local) or `set x 10` (global) |
| `self.x = self.y + 1` | `set x (y + 1)` |

The `self.` prefix is removed for model and agent fields.

### Augmented Assignment

| Python | NetLogo |
|--------|---------|
| `self.x += 1` | `set x (x + 1)` |
| `self.x -= 2` | `set x (x - 2)` |
| `self.x *= 3` | `set x (x * 3)` |
| `self.x /= 4` | `set x (x / 4)` |
| `self.x %= 5` | `set x (x mod 5)` |
| `self.x **= 2` | `set x (x ^ 2)` |

### Conditionals

**If Statement**:
```python
if self.energy > 0:
    self.move()
```
```netlogo
if (energy > 0) [
  move
]
```

**If-Else Statement**:
```python
if self.energy > 10:
    self.reproduce()
else:
    self.search_food()
```
```netlogo
ifelse (energy > 10) [
  reproduce
] [
  search-food
]
```

**Elif Chain**:
```python
if self.energy > 50:
    self.status = "healthy"
elif self.energy > 20:
    self.status = "ok"
else:
    self.status = "low"
```
```netlogo
ifelse (energy > 50) [
  set status "healthy"
] [
  ifelse (energy > 20) [
    set status "ok"
  ] [
    set status "low"
  ]
]
```

### Loops

**For Loop with Range**:
```python
for i in range(10):
    self.counter += 1
```
```netlogo
repeat 10 [
  set counter (counter + 1)
]
```

**For Loop with List**:
```python
for agent in self.agents.all():
    agent.move()
```
```netlogo
ask agents [
  move
]
```

**While Loop**:
```python
while self.counter < 100:
    self.counter += 1
```
```netlogo
while [counter < 100] [
  set counter (counter + 1)
]
```

### Return Statements

**Return from Procedure**:
```python
def check_condition(self):
    if self.x > 10:
        return
    self.x += 1
```
```netlogo
to check-condition
  if (x > 10) [
    stop
  ]
  set x (x + 1)
end
```

**Return Value (Reporter)**:
```python
def calculate_sum(self):
    return self.x + self.y
```
```netlogo
to-report calculate-sum
  report (x + y)
end
```

## Expression Translation

### Arithmetic Operators

| Python | NetLogo |
|--------|---------|
| `x + y` | `(x + y)` |
| `x - y` | `(x - y)` |
| `x * y` | `(x * y)` |
| `x / y` | `(x / y)` |
| `x % y` | `(x mod y)` |
| `x ** y` | `(x ^ y)` |
| `-x` | `(- x)` |

Parentheses are added to preserve order of operations.

### Comparison Operators

| Python | NetLogo |
|--------|---------|
| `x == y` | `(x = y)` |
| `x != y` | `(x != y)` |
| `x < y` | `(x < y)` |
| `x <= y` | `(x <= y)` |
| `x > y` | `(x > y)` |
| `x >= y` | `(x >= y)` |

### Boolean Operators

| Python | NetLogo |
|--------|---------|
| `x and y` | `(x and y)` |
| `x or y` | `(x or y)` |
| `not x` | `(not x)` |

### Literals

**Boolean**:
- `True` → `true`
- `False` → `false`

**Numbers**:
- `42` → `42`
- `3.14` → `3.14`
- `-10` → `-10`

**Strings**:
- `"hello"` → `"hello"`
- `'world'` → `"world"` (single quotes converted to double)

**Lists**:
- `[1, 2, 3]` → `[1 2 3]` (commas removed)
- `[]` → `[]`

### Attribute Access

| Python | NetLogo |
|--------|---------|
| `self.counter` | `counter` |
| `self.energy` | `energy` |
| `agent.x` | (complex - context-dependent) |

The `self.` prefix is automatically removed for model and agent fields.

### Method Calls

**Simple Call**:
```python
self.move()
```
```netlogo
move
```

**With Arguments**:
```python
self.move_to(10, 20)
```
```netlogo
move-to 10 20
```

**Built-in Functions**:
```python
abs(self.x)
max(self.x, self.y)
len(self.items)
```
```netlogo
abs x
max x y
length items
```

### List Operations

**Indexing**:
```python
item = my_list[0]
```
```netlogo
set item (item 0 my-list)
```

**Slicing**:
```python
subset = my_list[1:3]
```
```netlogo
set subset (sublist my-list 1 3)
```

**Append**:
```python
my_list.append(item)
```
```netlogo
set my-list (lput item my-list)
```

**Length**:
```python
length = len(my_list)
```
```netlogo
set length (length my-list)
```

## Built-in Function Translation

### Math Functions

| Python | NetLogo |
|--------|---------|
| `abs(x)` | `abs x` |
| `round(x)` | `round x` |
| `int(x)` | `floor x` |
| `max(x, y)` | `max list [x y]` |
| `min(x, y)` | `min list [x y]` |
| `sum(items)` | `sum items` |

### Sequence Functions

| Python | NetLogo |
|--------|---------|
| `len(x)` | `length x` |
| `range(n)` | `n-values n [i -> i]` |
| `sorted(x)` | `sort x` |
| `reversed(x)` | `reverse x` |

### Output Functions

| Python | NetLogo |
|--------|---------|
| `print(x)` | `print x` |
| `print(x, y)` | `print (word x " " y)` |

## Agent Operations

### Creating Agents

**Python**:
```python
agent = self.rabbits.create(1)
agent.energy = 10
agent.color = "brown"
```

**NetLogo**:
```netlogo
create-rabbits 1 [
  set energy 10
  set color brown
]
```

### Iterating Over Agents

**Python**:
```python
for rabbit in self.rabbits.all():
    rabbit.energy -= 1
```

**NetLogo**:
```netlogo
ask rabbits [
  set energy (energy - 1)
]
```

### Agent Methods

**Python**:
```python
agent.forward(1)
agent.set_heading(90)
agent.setxy(0, 0)
```

**NetLogo**:
```netlogo
ask agent [
  forward 1
  set heading 90
  setxy 0 0
]
```

## Special Cases

### Random Functions

**Python**:
```python
from xnlogo.runtime import random_float, random_int

value = random_float(10.0)
number = random_int(5)
```

**NetLogo**:
```netlogo
set value random-float 10.0
set number random 5
```

### Tick Management

**Python**:
```python
from xnlogo.runtime import reset_ticks, tick

reset_ticks()  # In setup
tick()         # In go
```

**NetLogo**:
```netlogo
reset-ticks  ;; In setup
tick         ;; In go
```

### Agent Queries

**Python**:
```python
count = self.rabbits.count()
nearby = agent.in_radius(5)
```

**NetLogo**:
```netlogo
set count (count rabbits)
set nearby (turtles in-radius 5)
```

## Unsupported Features

These Python features cannot be translated and will generate errors:

### Not Supported

**Exception Handling**:
```python
try:
    risky_operation()
except Exception:
    handle_error()
```
NetLogo doesn't have exception handling.

**Lambda Functions**:
```python
squared = lambda x: x ** 2
```
Use regular functions instead.

**Generators**:
```python
def count_up():
    yield 1
    yield 2
```
NetLogo doesn't have generators.

**Context Managers**:
```python
with open("file.txt") as f:
    data = f.read()
```
NetLogo file operations work differently.

**Imports**:
```python
import math
from random import choice
```
xnLogo provides its own runtime functions.

**Class Inheritance**:
```python
class SpecialRabbit(Rabbit):
    pass
```
Only single inheritance from `Model` is supported.

**Decorators** (except Model marker):
```python
@property
def computed_value(self):
    return self.x * 2
```
Only `Model` class inheritance is recognized.

## Type Hints

Type hints are preserved for documentation but not enforced:

**Python**:
```python
class MyModel(Model):
    def __init__(self):
        super().__init__()
        self.x: int = 0
        self.y: float = 0.0
        self.alive: bool = True
```

**NetLogo**:
```netlogo
globals [x y alive]
```

NetLogo is dynamically typed - type hints are informational only.

## Translation Process

1. **Parse**: Python AST → Internal representation
2. **Validate**: Check for unsupported constructs
3. **Translate**: Each statement via visitor pattern
4. **Generate**: Combine into NetLogo procedures
5. **Package**: Create `.nlogox` file with metadata

## Debugging Translation

### Validation

Check for errors without compiling:
```bash
xnlogo check mymodel.py
```

### Verbose Compilation

See detailed translation output:
```bash
xnlogo build mymodel.py --verbose
```

### Inspect Generated Code

Open the `.nlogox` file in NetLogo and view the Code tab to see the generated NetLogo code.

## Examples

### Complete Model Translation

**Python** (`counter.py`):
```python
from xnlogo.runtime import Model, reset_ticks, tick

class CounterModel(Model):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.max_count = 10
    
    def setup(self):
        reset_ticks()
        self.counter = 0
    
    def go(self):
        if self.counter < self.max_count:
            self.counter += 1
        else:
            self.counter = 0
        tick()
```

**NetLogo** (generated):
```netlogo
globals [counter max-count]

to setup
  reset-ticks
  set counter 0
end

to go
  ifelse (counter < max-count) [
    set counter (counter + 1)
  ] [
    set counter 0
  ]
  tick
end
```

### Agent-Based Model

**Python** (`ecosystem.py`):
```python
from xnlogo.runtime import Model, breed, reset_ticks, tick

class EcosystemModel(Model):
    def __init__(self):
        super().__init__()
        self.rabbits = breed("rabbits", "rabbit")
    
    def setup(self):
        reset_ticks()
        for i in range(50):
            rabbit = self.rabbits.create(1)
            rabbit.energy = 10
            rabbit.setxy(random_float(20) - 10, random_float(20) - 10)
    
    def go(self):
        for rabbit in self.rabbits.all():
            rabbit.energy -= 1
            if rabbit.energy <= 0:
                rabbit.die()
            else:
                rabbit.forward(1)
        tick()
```

**NetLogo** (generated):
```netlogo
breed [rabbits rabbit]

rabbits-own [energy]

to setup
  clear-all
  reset-ticks
  repeat 50 [
    create-rabbits 1 [
      set energy 10
      setxy (random-float 20 - 10) (random-float 20 - 10)
    ]
  ]
end

to go
  ask rabbits [
    set energy (energy - 1)
    ifelse (energy <= 0) [
      die
    ] [
      forward 1
    ]
  ]
  tick
end
```

## Tips for Writing Translatable Code

1. **Use simple Python**: Stick to basic control flow and expressions
2. **Avoid Python-specific patterns**: Don't rely on Python's advanced features
3. **Test frequently**: Compile often to catch translation issues early
4. **Read generated code**: Check the NetLogo output to understand translation
5. **Follow examples**: Use the examples in `examples/` directory as templates

## Getting Help

- Run `xnlogo check` to validate your code
- Check the [User Guide](user-guide.md) for API usage
- Review [examples/](../examples/) for working models
- See [Python-NetLogo Compatibility](python-netlogo-compatibility.md) for feature support
