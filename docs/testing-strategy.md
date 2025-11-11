# xnLogo Testing Strategy

## Overview

xnLogo has a comprehensive testing strategy with multiple layers of validation to ensure correctness and quality.

## Test Types

### 1. Unit Tests

**Location**: `tests/test_*.py` (various files)

- **Translator tests** (`test_translator.py`): 62 tests validating Python→NetLogo translation
  - Assignments, operators, control flow
  - For/while loops, ternary operators
  - List operations, membership operators
  - Method calls, built-in functions
  
- **Parser tests** (`test_parser.py`): Tests for Python AST parsing
  
- **Compiler tests** (`test_compiler.py`): End-to-end compilation tests

- **CLI tests** (`test_cli_export.py`): Command-line interface tests

### 2. Syntax Validation Tests

**Location**: `tests/test_syntax_validation.py`

Tests that ensure:
- Module-level Python syntax errors are caught
- Behavior-level Python syntax errors are caught
- Clear error messages are provided to users

### 3. Golden Reference Tests

**Location**: `tests/test_golden.py`

**Purpose**: Regression testing - ensures generated output doesn't change unexpectedly

**How it works**:
1. Source `.py` files in `tests/data/` are compiled
2. Generated `.nlogox` is compared against golden reference in `tests/data/golden/`
3. XML is normalized before comparison to ignore formatting differences

**Current golden tests**:
- `simple_agent.nlogox` - Basic model with state variables
- `agent_with_conditionals.nlogox` - If/else conditional statements
- `multi_breed.nlogox` - Multiple breed definitions
- `complex_agent.nlogox` - Advanced features (operators, built-ins, nested conditions)

### 4. NetLogo Validity Tests

**Location**: `tests/test_netlogo_validity.py`

**Purpose**: Validate that generated NetLogo code is syntactically valid

**Validation checks**:
- Balanced brackets `[ ]`
- Balanced parentheses `( )`
- No Python syntax leaks (`self.`, `def`, `class`, `import`)
- No Python-only operators (e.g., `==` should become `=`)
- All golden reference files are valid NetLogo code

**Tests**:
- Individual validity tests for each test model
- Comprehensive golden files validity test

## Test Coverage

**Total tests**: 85

**Coverage breakdown**:
- Translator: 62 tests
- Golden reference: 4 tests
- NetLogo validity: 6 tests
- Syntax validation: 2 tests
- Other (parser, compiler, CLI): ~11 tests

## Git Strategy for Test Files

### Files Committed to Git:

**Source files** (`tests/data/*.py`) - Test inputs
```
tests/data/simple_agent.py
tests/data/agent_with_conditionals.py
tests/data/multi_breed.py
tests/data/complex_agent.py
tests/data/agent_with_loops.py
tests/data/invalid_syntax.py
tests/data/invalid_behavior_syntax.py
tests/data/valid_behavior_syntax.py
```

**Golden reference files** (`tests/data/golden/*.nlogox`) - Expected outputs
```
tests/data/golden/simple_agent.nlogox
tests/data/golden/agent_with_conditionals.nlogox
tests/data/golden/multi_breed.nlogox
tests/data/golden/complex_agent.nlogox
```

**Test code** (`tests/test_*.py`) - Test implementations

**Examples** (`examples/*.py`, `examples/*.nlogox`) - Documentation/demos

### Files Ignored (in .gitignore):

**Generated artifacts** (`tests/data/*.nlogox`) - Can be regenerated
```gitignore
# Generated test artifacts (but keep golden reference files)
tests/data/*.nlogox
!tests/data/golden/*.nlogox
```

## Running Tests

### All tests:
```bash
pytest tests/
```

### Specific test category:
```bash
pytest tests/test_translator.py      # Translator unit tests
pytest tests/test_golden.py          # Golden reference tests
pytest tests/test_netlogo_validity.py # NetLogo syntax validation
pytest tests/test_syntax_validation.py # Python syntax validation
```

### With coverage:
```bash
pytest tests/ --cov=xnlogo --cov-report=html
```

### Verbose output:
```bash
pytest tests/ -v
```

## Updating Golden Reference Files

When translator behavior changes intentionally:

1. Verify the changes are correct
2. Rebuild the test models:
   ```bash
   xnlogo build tests/data/simple_agent.py
   xnlogo build tests/data/agent_with_conditionals.py
   xnlogo build tests/data/multi_breed.py
   xnlogo build tests/data/complex_agent.py
   ```

3. Copy new output to golden directory:
   ```bash
   cp tests/data/simple_agent.nlogox tests/data/golden/
   # ... repeat for other files
   ```

4. Run golden tests to verify:
   ```bash
   pytest tests/test_golden.py -v
   ```

5. Commit the updated golden files

## Best Practices

1. **Add tests for new features** - Every new translator feature should have unit tests
2. **Update golden files carefully** - Only update when translation intentionally changes
3. **Run all tests before commit** - Ensure nothing breaks
4. **Keep test data minimal** - Only commit necessary test files
5. **Validate NetLogo output** - Use validity tests to catch syntax errors early

## Future Improvements

- [ ] Add integration tests with actual NetLogo runtime
- [ ] Add performance benchmarks
- [ ] Increase test coverage to 90%+
- [ ] Add property-based testing for translator
- [ ] Test with real-world NetLogo models
