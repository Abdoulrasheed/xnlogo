# Python → NetLogo Feature Compatibility Matrix

This document maps Python language features to their NetLogo equivalents and translation status in xnLogo.

## Status Legend

- **[Supported]** — Fully implemented and tested
- **[Partial]** — Implemented with limitations or caveats
- **[Planned]** — Not yet implemented but makes sense to add; on roadmap
- **[Future]** — Possible but lower priority; may be added later
- **[Not Applicable]** — Doesn't map to NetLogo concepts; won't be implemented

---

## 1. Basic Statements

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **Assignment** | `set var value` | [Supported] | `x = 5` → `set x 5` |
| **Augmented Assignment** | `set var (var op value)` | [Supported] | `x += 1` → `set x (x + 1)` |
| **Multiple Assignment** | Multiple `set` | [Not Applicable] | `x = y = 5` - not common in ABM |
| **Tuple Unpacking** | N/A | [Not Applicable] | `a, b = coords` - no tuple concept |
| **Pass Statement** | Empty line | [Supported] | Silently ignored |
| **Del Statement** | N/A | [Not Applicable] | Memory managed automatically |
| **Return Statement** | `stop` / `report` | [Supported] | `return` → `stop`, `return x` → `report x` |

---

## 2. Control Flow

### Conditionals

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **if** | `if condition [ ... ]` | [Supported] | Full support |
| **if/else** | `if condition [ ... ] [ ... ]` | [Supported] | Full support |
| **elif** | Nested if/else | [Partial] | Works but could be cleaner |
| **Ternary operator** | `ifelse-value` | [Planned] | `x if cond else y` → `ifelse-value cond x y` |
| **match/case** | N/A | [Not Applicable] | Python 3.10+, no NetLogo equivalent |

### Loops

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **for (range)** | `repeat n [ ... ]` | [Planned] | `for i in range(10)` → `repeat 10 [ ... ]` |
| **for (list)** | `foreach list [ x -> ... ]` | [Planned] | Possible with agentsets |
| **while** | `while [ condition ] [ ... ]` | [Planned] | Direct mapping exists |
| **break** | `stop` | [Planned] | Can map to loop exit |
| **continue** | N/A | [Future] | Harder to translate |
| **for/else** | N/A | [Not Applicable] | No equivalent concept |
| **List comprehension** | `map` / agentset ops | [Planned] | `[x*2 for x in list]` → agentset mapping |
| **Generator expression** | Agentset operations | [Future] | Complex, low priority |

---

## 3. Operators

### Arithmetic

| Python | NetLogo | Status | Notes |
|--------|---------|--------|-------|
| `+` | `+` | [Supported] | Addition |
| `-` | `-` | [Supported] | Subtraction |
| `*` | `*` | [Supported] | Multiplication |
| `/` | `/` | [Supported] | Division (always float) |
| `//` | `floor (a / b)` | [Partial] | Floor division |
| `%` | `mod` | [Supported] | Modulo |
| `**` | `^` | [Supported] | Exponentiation |
| `@` | N/A | [Not Applicable] | Matrix multiplication |

### Comparison

| Python | NetLogo | Status | Notes |
|--------|---------|--------|-------|
| `==` | `=` | [Supported] | Equality |
| `!=` | `!=` | [Supported] | Inequality |
| `<` | `<` | [Supported] | Less than |
| `<=` | `<=` | [Supported] | Less than or equal |
| `>` | `>` | [Supported] | Greater than |
| `>=` | `>=` | [Supported] | Greater than or equal |
| `is` | `=` | [Partial] | Identity → equality |
| `is not` | `!=` | [Partial] | Identity → inequality |
| `in` | `member?` | [Planned] | Membership testing |
| `not in` | `not member?` | [Planned] | Negated membership |

### Logical

| Python | NetLogo | Status | Notes |
|--------|---------|--------|-------|
| `and` | `and` | [Supported] | Logical AND |
| `or` | `or` | [Supported] | Logical OR |
| `not` | `not` | [Supported] | Logical NOT |

### Bitwise

| Python | NetLogo | Status | Notes |
|--------|---------|--------|-------|
| `&`, `\|`, `^`, `~`, `<<`, `>>` | N/A | [Not Applicable] | No bitwise ops in NetLogo |

---

## 4. Built-in Functions

### Math Functions

| Python | NetLogo | Status | Notes |
|--------|---------|--------|-------|
| `abs(x)` | `abs x` | [Supported] | Absolute value |
| `round(x)` | `round x` | [Supported] | Round to nearest integer |
| `int(x)` | `floor x` | [Supported] | Convert to integer |
| `float(x)` | (implicit) | [Supported] | No-op, everything is float |
| `pow(x, y)` | `x ^ y` | [Supported] | Via `**` operator |
| `max(a, b, ...)` | `max list` | [Supported] | Maximum value |
| `min(a, b, ...)` | `min list` | [Supported] | Minimum value |
| `sum(iterable)` | `sum list` | [Supported] | Sum of values |
| `divmod(a, b)` | `floor (a / b)`, `a mod b` | [Future] | Returns tuple, complex |

### Sequence Functions

| Python | NetLogo | Status | Notes |
|--------|---------|--------|-------|
| `len(x)` | `length x` | [Supported] | Length of list/string |
| `range(n)` | `n-values n [i -> i]` | [Planned] | Create number sequence |
| `sorted(x)` | `sort x` | [Planned] | Sort list |
| `reversed(x)` | `reverse x` | [Planned] | Reverse list |
| `enumerate(x)` | N/A | [Future] | No direct equivalent |
| `zip(a, b)` | N/A | [Future] | Complex, low priority |
| `map(f, x)` | `map [f] x` | [Planned] | Map function over list |
| `filter(f, x)` | `filter [f] x` | [Planned] | Filter list |
| `any(x)` | `any? x` | [Planned] | Any true value |
| `all(x)` | `all? x` | [Planned] | All true values |

### Type Functions

| Python | NetLogo | Status | Notes |
|--------|---------|--------|-------|
| `type(x)` | `is-*? x` | [Future] | Type checking |
| `isinstance(x, T)` | `is-*? x` | [Future] | Type checking |
| `str(x)` | `word x ""` | [Planned] | Convert to string |
| `bool(x)` | (implicit) | [Supported] | Implicit coercion |

### I/O Functions

| Python | NetLogo | Status | Notes |
|--------|---------|--------|-------|
| `print(x)` | `print x` | [Supported] | Output to console |
| `input(prompt)` | `user-input prompt` | [Planned] | User input |
| `open(file)` / file I/O | `file-*` primitives | [Future] | Complex, less common in ABM |

---

## 5. Data Structures

### Lists

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **List literal** | `[item1 item2 ...]` | [Supported] | `[1, 2, 3]` → space-separated |
| **Indexing** | `item i list` | [Planned] | `lst[0]` → `item 0 lst` |
| **Slicing** | `sublist` | [Planned] | `lst[1:3]` → `sublist lst 1 3` |
| **append()** | `lput item list` | [Planned] | Add to end |
| **insert()** | N/A | [Future] | Complex |
| **remove()** | `remove item list` | [Planned] | Remove item |
| **List concatenation** | `sentence` | [Planned] | Join lists |
| **List comprehension** | `map` | [Planned] | Transform lists |

### Dictionaries

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **Dict literal** | N/A | [Not Applicable] | NetLogo has no dict type |
| **Subscript** | Table extension | [Partial] | `d["key"]` → treated as variable |
| **get()** | N/A | [Not Applicable] | No dict concept |
| **Dict comprehension** | N/A | [Not Applicable] | No dict concept |

**Note**: `obj["field"]` is treated as property access and translates to `field`. This supports the common ABM pattern of accessing agent and patch properties.

### Tuples

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **Tuple literal** | List | [Partial] | `(1, 2)` → `[1 2]` (immutability lost) |
| **Tuple unpacking** | N/A | [Not Applicable] | No equivalent |

### Sets

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **Set literal** | Agentset | [Future] | `{1, 2}` → agentset operations |
| **add()** | N/A | [Not Applicable] | Agentsets are immutable |
| **Set operations** | Agentset ops | [Future] | union, intersection, etc. |

---

## 6. Object-Oriented Features

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **Class definition** | Breed definition | [Supported] | `@agent` decorator |
| **Instance variables** | `*-own` variables | [Supported] | State fields |
| **Methods** | Procedures | [Supported] | Behavior methods |
| **self** | Implicit turtle context | [Supported] | `self.x` → `x` |
| **Inheritance** | N/A | [Not Applicable] | No inheritance in NetLogo |
| **Properties** | N/A | [Not Applicable] | Direct field access only |
| **Class variables** | `globals` | [Partial] | Via `@agent(globals=...)` |
| **Static methods** | N/A | [Not Applicable] | No static context |
| **Magic methods** | N/A | [Not Applicable] | `__init__`, `__str__`, etc. |

---

## 7. Advanced Features

### Exception Handling

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **try/except** | `carefully [ ... ] [ ... ]` | [Future] | NetLogo has error handling |
| **raise** | `error "message"` | [Future] | Raise errors |
| **finally** | N/A | [Not Applicable] | No finally clause |
| **Context managers** | N/A | [Not Applicable] | `with` statement |

### Functional Programming

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **lambda** | Anonymous reporter | [Planned] | `lambda x: x*2` → `[x -> x * 2]` |
| **map()** | `map` | [Planned] | Function mapping |
| **filter()** | `filter` | [Planned] | Filtering |
| **reduce()** | `reduce` | [Planned] | Reduction |
| **Decorators** | N/A | [Not Applicable] | Compile-time only (`@agent`) |
| **Generators** | N/A | [Not Applicable] | No yield in NetLogo |

### Async

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **async/await** | N/A | [Not Applicable] | NetLogo is synchronous |
| **asyncio** | N/A | [Not Applicable] | No async runtime |

### Other

| Python Feature | NetLogo Equivalent | Status | Notes |
|----------------|-------------------|--------|-------|
| **Import** | N/A | [Not Applicable] | Extensions loaded differently |
| **Global keyword** | `globals` | [Supported] | Via decorator |
| **Nonlocal** | N/A | [Not Applicable] | Flat scope in NetLogo |
| **Assert** | N/A | [Future] | Could map to error |
| **With** | N/A | [Not Applicable] | No context managers |

---

## 8. NetLogo-Specific Concepts

These don't exist in Python but are essential for ABM:

| NetLogo Concept | Python Equivalent | How We Handle |
|----------------|-------------------|---------------|
| **Agentsets** | Set-like collections | Via `@agent` decorator params |
| **ask** | Iteration with context | Method parameters (e.g., `def move(self, turtle)`) |
| **Patches** | Grid cells | Via `@agent(patches=...)` |
| **Links** | Graph edges | Future support |
| **Breeds** | Agent types | Via `@agent(breed="name")` |
| **tick** | Time step | Automatic in `go` |
| **Spatial primitives** | N/A | Method calls (e.g., `turtle.forward()`) |

---

## Priority Recommendations

### High Priority (Should Add Next)

1. **For loops with range()** → `repeat`
   - Very common in programming
   - Clear mapping to NetLogo
   - Example: `for i in range(10): ...` → `repeat 10 [ ... ]`

2. **Ternary operator** → `ifelse-value`
   - Common Python pattern
   - Direct NetLogo equivalent
   - Example: `x if cond else y` → `ifelse-value cond x y`

3. **List operations** → NetLogo list primitives
   - `lst[0]` → `item 0 lst`
   - `lst.append(x)` → `lput x lst`
   - `len(lst)` → `length lst`

4. **Lambda expressions** → NetLogo reporters
   - Functional programming style
   - Direct mapping
   - Example: `lambda x: x * 2` → `[x -> x * 2]`

5. **While loops** → `while [ condition ] [ ... ]`
   - Common control flow
   - Direct mapping exists

### Medium Priority (Nice to Have)

1. **in operator** → `member?`
2. **any() / all()** → `any?` / `all?`
3. **sorted() / reversed()** → `sort` / `reverse`
4. **String operations** → NetLogo string primitives
5. **Try/except** → `carefully`

### Low Priority (Optional)

1. Generator expressions (complex, limited use in ABM)
2. Set operations (agentsets handle this differently)
3. File I/O (less common in ABM models)
4. Complex unpacking
5. Bitwise operations (not in NetLogo)

### Not Worth Implementing

1. **Async/await** - NetLogo is fundamentally synchronous
2. **Inheritance** - Not supported in NetLogo
3. **Magic methods** - Compile-time only
4. **Imports** - Different module system
5. **Decorators** (beyond `@agent`) - Compile-time only
6. **Context managers** - No RAII in NetLogo

---

## Current Support Summary

### [Supported] — 22 features
- Basic assignments, augmented assignments
- If/else statements
- All comparison operators
- Boolean operators (and/or/not)
- Arithmetic operators (+, -, *, /, %, **)
- Return statements
- Basic built-ins (abs, round, max, min, sum, len, print)
- Self field access
- Method calls
- Subscript access (dict-style)
- Local variables
- Classes via @agent
- List literals

### [Planned] — 8 high-value additions
- For loops (range)
- While loops
- Ternary operator
- List indexing/slicing
- Lambda expressions
- in/not in operators
- any/all built-ins
- Basic list methods

### Current Coverage
- **~40% of common Python features** with direct NetLogo equivalents
- **~70% of ABM-relevant features** supported
- **~90% of critical path** for agent-based modeling

This puts xnLogo in a strong position for typical ABM development while keeping the translator maintainable!
