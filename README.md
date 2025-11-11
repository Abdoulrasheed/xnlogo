# xnLogo

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Write agent-based models in Python and export them to NetLogo.

## Installation

```bash
pip install xnlogo
```

## Quick Start

Create `counter.py`:

```python
from xnlogo.runtime import Model, reset_ticks, tick, Button, Monitor

class CounterModel(Model):
    def __init__(self):
        super().__init__()
        self.count = 0
        
    def setup(self):
        reset_ticks()
        self.count = 0
    
    def go(self):
        self.count += 1
        tick()
    
    def ui(self):
        self.add_widget(Button(command="setup", x=15, y=10, width=150, height=60))
        self.add_widget(Button(command="go", x=175, y=10, width=150, height=60, forever=True))
        self.add_widget(Monitor(expression="count", x=15, y=80, width=150, height=60))
```

Build to NetLogo:

```bash
xnlogo build counter.py
```

This generates `counter.nlogox` that can be opened in NetLogo 7.

## Features

### Core Capabilities

- **Python Models**: Write agent-based models using Python classes and methods
- **Breed System**: Define multiple agent types with `breed()` function
- **UI Widgets**: Declarative interface definition with buttons, sliders, monitors, plots
- **Semantic Validation**: Catch errors before compilation with detailed diagnostics
- **NetLogo 7 Support**: Generate modern `.nlogox` format (legacy `.nlogo` also supported)

### Supported Python Features

- Instance variables, methods, type hints
- Basic control flow (if/elif/else, while, for)
- Lists, arithmetic, comparisons, boolean logic
- Turtle graphics commands (forward, back, left, right, etc.)
- Observer commands (clear-all, reset-ticks, tick, etc.)

### Breed System

Define agent types:

```python
from xnlogo.runtime import Model, breed

Rabbit = breed("rabbit")
Fox = breed("fox")

class EcosystemModel(Model):
    def __init__(self):
        super().__init__()
        self.rabbits = []
        self.foxes = []
    
    def add_rabbit(self):
        rabbit = Rabbit()
        rabbit.energy = 10
        self.rabbits.append(rabbit)
    
    def add_fox(self):
        fox = Fox()
        fox.energy = 20
        self.foxes.append(fox)
```

## Examples

### Random Walker

```python
from xnlogo.runtime import Model, breed, reset_ticks, tick
from xnlogo.runtime import clear_all, crt, forward, right
import random

Walker = breed("walker")

class RandomWalkModel(Model):
    def setup(self):
        clear_all()
        reset_ticks()
        crt(100, Walker)
    
    def go(self):
        for walker in Walker.all():
            right(random.uniform(0, 360))
            forward(1)
        tick()
```

### Population Dynamics

```python
from xnlogo.runtime import Model, breed, reset_ticks, tick, Slider, Monitor
import random

Rabbit = breed("rabbit")

class PopulationModel(Model):
    def __init__(self):
        super().__init__()
        self.birth_rate = 0.05
        self.death_rate = 0.02
        self.rabbits = []
    
    def setup(self):
        reset_ticks()
        self.rabbits = []
        for _ in range(100):
            self.rabbits.append(Rabbit())
    
    def go(self):
        if random.random() < self.birth_rate:
            self.rabbits.append(Rabbit())
        
        if self.rabbits and random.random() < self.death_rate:
            self.rabbits.pop()
        
        tick()
    
    def ui(self):
        self.add_widget(Slider(variable="birth_rate", min_val=0, max_val=0.1, default=0.05, x=15, y=10, width=310, height=40))
        self.add_widget(Slider(variable="death_rate", min_val=0, max_val=0.1, default=0.02, x=15, y=60, width=310, height=40))
        self.add_widget(Monitor(expression="length rabbits", x=15, y=110, width=150, height=60))
```

## Documentation

- [User Guide](docs/user-guide.md) - Complete usage guide
- [Architecture](docs/architecture.md) - System design overview
- [Technical Overview](docs/technical-overview.md) - Implementation details
- [Translation Rules](docs/translation-rules.md) - Python to NetLogo mapping
- [Testing Strategy](docs/testing-strategy.md) - Testing approach

## CLI Usage

```bash
xnlogo build model.py

xnlogo build model.py --format nlogo

xnlogo build model.py --output my_model.nlogox

xnlogo run model.py --ticks 1000

xnlogo --version
```

## Requirements

- Python 3.10 or higher
- NetLogo 7.0 or higher (to run generated models)

## Project Structure

```
xnlogo/
├── runtime/
├── parser/
├── ir/
├── codegen/
├── semantics/
└── cli/
```

## Development

```bash
git clone https://github.com/yourusername/xnlogo.git
cd xnlogo

pip install -e .

pytest
```

## Limitations

- List comprehensions not yet supported
- Lambda functions limited (only in widget callbacks)
- Class inheritance only for Model subclass
- No imports from external packages in model code
- Limited string operations
- No exception handling
- No decorators
- No tuple unpacking
- No dictionary type
- No generators or yield

See [Python-NetLogo Compatibility](docs/python-netlogo-compatibility.md) for complete feature support matrix.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

- Issues: https://github.com/yourusername/xnlogo/issues
- Documentation: https://github.com/yourusername/xnlogo/docs

## Credits

Built with Python 3.10+, targeting NetLogo 7.x compatibility.
