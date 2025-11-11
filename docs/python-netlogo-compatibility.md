# Python ↔ NetLogo Feature Compatibility

Complete reference for which Python features are supported in xnLogo and how they map to NetLogo.

## Status Legend

- **✅ Supported** — Fully implemented and tested
- **🟡 Partial** — Implemented with limitations
- **🔮 Planned** — Not yet implemented but on roadmap
- **❌ Not Applicable** — No NetLogo equivalent, won't be implemented

## 1. Basic Statements

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| Assignment | `set var value` | ✅ | `x = 5` → `set x 5` |
| Augmented Assignment | `set var (var op value)` | ✅ | `x += 1` → `set x (x + 1)` |
| Multiple Assignment | Multiple `set` | ❌ | `x = y = 5` doesn't translate |
| Tuple Unpacking | N/A | ❌ | `a, b = (1, 2)` not supported |
| Pass Statement | Empty line | ✅ | Silently ignored |
| Del Statement | N/A | ❌ | Memory managed automatically |
| Return Statement | `stop` / `report` | ✅ | `return` → `stop`, `return x` → `report x` |

## 2. Control Flow

### Conditionals

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| if | `if condition [ ... ]` | ✅ | Full support |
| if/else | `ifelse condition [ ... ] [ ... ]` | ✅ | Full support |
| elif | Nested ifelse | ✅ | Translated to nested ifelse |
| Ternary operator | `ifelse-value` | 🔮 | `x if cond else y` planned |
| match/case | N/A | ❌ | Python 3.10+, no NetLogo equivalent |

### Loops

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| for (range) | `repeat n [ ... ]` | ✅ | `for i in range(10)` → `repeat 10` |
| for (list) | `foreach` / `ask` | ✅ | Depends on context |
| while | `while [ condition ] [ ... ]` | ✅ | Direct mapping |
| break | `stop` | 🟡 | Works but limited in nested contexts |
| continue | N/A | ❌ | No direct equivalent |
| for/else | N/A | ❌ | No equivalent concept |

## 3. Operators

### Arithmetic

| Python | NetLogo | Status | Notes |
|--------|---------|:------:|-------|
| `+` | `+` | ✅ | Addition |
| `-` | `-` | ✅ | Subtraction |
| `*` | `*` | ✅ | Multiplication |
| `/` | `/` | ✅ | Division (always float) |
| `//` | `floor (a / b)` | ✅ | Floor division |
| `%` | `mod` | ✅ | Modulo |
| `**` | `^` | ✅ | Exponentiation |
| `@` | N/A | ❌ | Matrix multiplication |

### Comparison

| Python | NetLogo | Status | Notes |
|--------|---------|:------:|-------|
| `==` | `=` | ✅ | Equality |
| `!=` | `!=` | ✅ | Inequality |
| `<` | `<` | ✅ | Less than |
| `<=` | `<=` | ✅ | Less than or equal |
| `>` | `>` | ✅ | Greater than |
| `>=` | `>=` | ✅ | Greater than or equal |
| `is` | `=` | 🟡 | Identity treated as equality |
| `is not` | `!=` | 🟡 | Identity treated as inequality |
| `in` | `member?` | 🔮 | Planned for lists |
| `not in` | `not member?` | 🔮 | Planned for lists |

### Logical

| Python | NetLogo | Status | Notes |
|--------|---------|:------:|-------|
| `and` | `and` | ✅ | Logical AND |
| `or` | `or` | ✅ | Logical OR |
| `not` | `not` | ✅ | Logical NOT |

### Bitwise

| Python | NetLogo | Status | Notes |
|--------|---------|:------:|-------|
| `&`, `\|`, `^`, `~`, `<<`, `>>` | N/A | ❌ | No bitwise operators in NetLogo |

## 4. Built-in Functions

### Math Functions

| Python | NetLogo | Status | Notes |
|--------|---------|:------:|-------|
| `abs(x)` | `abs x` | ✅ | Absolute value |
| `round(x)` | `round x` | ✅ | Round to nearest integer |
| `int(x)` | `floor x` | ✅ | Convert to integer |
| `float(x)` | (implicit) | ✅ | All numbers are floats |
| `pow(x, y)` | `x ^ y` | ✅ | Via `**` operator |
| `max(...)` | `max list [...]` | ✅ | Maximum value |
| `min(...)` | `min list [...]` | ✅ | Minimum value |
| `sum(iter)` | `sum list` | ✅ | Sum of values |

### Sequence Functions

| Python | NetLogo | Status | Notes |
|--------|---------|:------:|-------|
| `len(x)` | `length x` | ✅ | Length of list/string |
| `range(n)` | `n-values n [i -> i]` | ✅ | Number sequences |
| `sorted(x)` | `sort x` | ✅ | Sort list |
| `reversed(x)` | `reverse x` | ✅ | Reverse list |
| `enumerate(x)` | N/A | ❌ | No direct equivalent |
| `zip(a, b)` | N/A | ❌ | Complex, not planned |
| `map(f, x)` | `map [f] x` | 🔮 | Planned |
| `filter(f, x)` | `filter [f] x` | 🔮 | Planned |
| `any(x)` | `any? x` | 🔮 | Planned |
| `all(x)` | `all? x` | 🔮 | Planned |

### Type Functions

| Python | NetLogo | Status | Notes |
|--------|---------|:------:|-------|
| `type(x)` | `is-*? x` | ❌ | Not prioritized |
| `isinstance(x, T)` | `is-*? x` | ❌ | Not prioritized |
| `str(x)` | `word x ""` | 🔮 | Planned |
| `bool(x)` | (implicit) | ✅ | Implicit coercion |

### I/O Functions

| Python | NetLogo | Status | Notes |
|--------|---------|:------:|-------|
| `print(x)` | `print x` | ✅ | Output to console |
| `input(prompt)` | `user-input` | ❌ | Interactive input not planned |

## 5. Data Structures

### Lists

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| List literal | `[item1 item2 ...]` | ✅ | `[1, 2, 3]` → `[1 2 3]` |
| Indexing | `item i list` | ✅ | `lst[0]` → `item 0 lst` |
| Slicing | `sublist` | ✅ | `lst[1:3]` → `sublist lst 1 3` |
| append() | `lput item list` | ✅ | Add to end |
| insert() | N/A | ❌ | Complex insertion not supported |
| remove() | `remove item list` | ✅ | Remove item |
| List concatenation | `sentence` | ✅ | Join lists |
| List comprehension | `map` | 🔮 | Planned |

### Dictionaries

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| Dict literal | N/A | ❌ | NetLogo has no dict type |
| Subscript | Property access | 🟡 | `obj["field"]` → field access |
| get() / keys() / values() | N/A | ❌ | No dict support |

**Note**: Dictionary subscript notation (`obj["field"]`) is interpreted as property access and translates to the field name directly. This supports accessing agent and patch properties.

### Tuples

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| Tuple literal | List | 🟡 | `(1, 2)` → `[1 2]` (loses immutability) |
| Tuple unpacking | N/A | ❌ | Not supported |

### Sets

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| Set literal | Agentset | ❌ | Different concept |
| Set operations | Agentset ops | ❌ | Use agentsets instead |

## 6. Object-Oriented Features

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| Class definition | Breed / Model | ✅ | `Model` subclass for models |
| Instance variables | `*-own` / `globals` | ✅ | State fields |
| Methods | Procedures | ✅ | Behavior methods |
| self | Implicit context | ✅ | `self.x` → `x` |
| Inheritance | N/A | ❌ | Only `Model` base class |
| Properties | N/A | ❌ | Direct field access only |
| Class variables | `globals` | 🟡 | Via instance variables in `__init__` |
| Static methods | N/A | ❌ | No static context |
| Magic methods | N/A | ❌ | Except `__init__` |

## 7. Advanced Features

### Exception Handling

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| try/except | `carefully` | ❌ | Not planned |
| raise | `error` | ❌ | Not planned |
| finally | N/A | ❌ | No equivalent |
| Context managers (with) | N/A | ❌ | No RAII in NetLogo |

### Functional Programming

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| lambda | Anonymous reporter | 🔮 | `lambda x: x*2` → `[x -> x * 2]` |
| map() | `map` | 🔮 | Function mapping planned |
| filter() | `filter` | 🔮 | Filtering planned |
| reduce() | `reduce` | 🔮 | Reduction planned |
| Decorators | N/A | ❌ | Only `Model` inheritance |
| Generators | N/A | ❌ | No yield in NetLogo |

### Async

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| async/await | N/A | ❌ | NetLogo is synchronous |
| asyncio | N/A | ❌ | No async runtime |

### Other

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|:------:|-------|
| import | N/A | ❌ | Extensions loaded differently |
| global keyword | `globals` | ✅ | Via Model instance vars |
| nonlocal | N/A | ❌ | Flat scope |
| assert | N/A | ❌ | Not planned |

## 8. NetLogo-Specific Concepts

Features that exist in NetLogo but not Python:

| NetLogo Concept | xnLogo API | Status | Notes |
|----------------|-----------|:------:|-------|
| Breeds | `breed()` function | ✅ | Define agent types |
| Agentsets | `.all()`, `.create()` | ✅ | Query and create agents |
| ask | Iteration/methods | ✅ | Via for loops or method calls |
| Patches | Patch operations | 🟡 | Limited support |
| Links | Link operations | ❌ | Not yet supported |
| tick | `tick()` function | ✅ | Time management |
| Spatial primitives | Agent methods | ✅ | `.forward()`, `.setxy()`, etc. |

## Current Support Summary

### Fully Supported (✅)

**Control Flow**: if, if/else, elif, for (range), for (agentsets), while, return

**Operators**: All arithmetic (+, -, *, /, //, %, **), all comparison (==, !=, <, <=, >, >=), all logical (and, or, not)

**Statements**: Assignment, augmented assignment, pass

**Built-ins**: abs, round, int, float, pow, max, min, sum, len, range, sorted, reversed, print

**Data Structures**: Lists (literals, indexing, slicing, append, remove, concatenation)

**OOP**: Model classes, instance variables (globals), methods (procedures), self access

**Agent Operations**: Breed definition, agent creation, agent iteration, spatial operations

**NetLogo Integration**: tick management, agentsets, spatial primitives

### Partially Supported (🟡)

- **break**: Works but limited in nested contexts
- **is/is not**: Treated as equality/inequality
- **Tuples**: Converted to lists, lose immutability
- **Dictionaries**: Subscript syntax for property access only
- **Class variables**: Via instance variables in `__init__`
- **Patches**: Basic operations supported

### Planned (🔮)

- Ternary operator (`x if cond else y`)
- in/not in operators
- Lambda expressions
- map, filter, any, all built-ins
- String conversion (str())
- Advanced list comprehensions

### Not Applicable (❌)

- Exception handling
- Context managers
- Generators
- Async/await
- Decorators (beyond Model)
- Imports
- Bitwise operators
- Sets (as Python sets, use agentsets)
- Class inheritance (beyond Model)
- Most magic methods

## Coverage Statistics

- **Core Python for ABM**: ~85% coverage
- **General Python**: ~45% coverage
- **NetLogo concepts**: ~70% coverage

xnLogo focuses on features relevant to agent-based modeling rather than complete Python compatibility.

## Recommendations

### Use These Patterns

✅ Simple classes with `Model` inheritance
✅ Instance variables for state
✅ If/else conditionals
✅ For and while loops
✅ Basic lists and list operations
✅ Arithmetic and comparison operators
✅ Built-in math functions

### Avoid These Patterns

❌ Exception handling
❌ Generators and yield
❌ Lambda functions (for now)
❌ Complex comprehensions
❌ Python standard library imports
❌ Class inheritance
❌ Decorators (except Model)

## Getting Help

- Check [Translation Rules](translation-rules.md) for specific syntax mapping
- See [User Guide](user-guide.md) for API usage examples
- Review [examples/](../examples/) for working models
- Run `xnlogo check` to validate your code
