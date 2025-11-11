"""Simple Counter Example

A minimal model demonstrating basic state tracking with a counter that
increments each tick and resets after reaching a threshold.
"""

from xnlogo.runtime import (
    Model,
    reset_ticks,
    tick,
    View,
    Button,
    Monitor,
)


class CounterModel(Model):
    """A simple counter model."""

    def __init__(self):
        super().__init__()
        
        # State
        self.counter = 0
        self.max_counter = 10

    def setup(self):
        """Initialize the model."""
        reset_ticks()
        self.counter = 0

    def go(self):
        """Run one step: increment and check for reset."""
        self.increment()
        self.check_reset()
        tick()

    def increment(self):
        """Increment the counter."""
        self.counter += 1

    def check_reset(self):
        """Reset counter if it exceeds the maximum."""
        if self.counter > self.max_counter:
            self.counter = 0

    def ui(self):
        """Define the UI widgets for the model."""
        # View
        self.add_widget(
            View(
                x=385,
                y=10,
                width=610,
                height=631,
                patch_size=13.0,
                font_size=10,
            )
        )
        
        # Setup button
        self.add_widget(
            Button(
                command="setup",
                x=15,
                y=10,
                width=355,
                height=60,
                forever=False,
                kind="Observer",
            )
        )
        
        # Go button
        self.add_widget(
            Button(
                command="go",
                x=15,
                y=80,
                width=355,
                height=60,
                forever=True,
                kind="Observer",
            )
        )
        
        # Counter monitor
        self.add_widget(
            Monitor(
                expression="counter",
                x=15,
                y=150,
                width=150,
                height=80,
                font_size=14,
                precision=0,
            )
        )
        
        # Ticks monitor
        self.add_widget(
            Monitor(
                expression="ticks",
                x=175,
                y=150,
                width=150,
                height=80,
                font_size=14,
                precision=0,
            )
        )

    def info(self):
        """Return model information and documentation."""
        return """
## WHAT IS IT?

This is a minimal example model that demonstrates basic state tracking
with a simple counter variable.

## HOW IT WORKS

- The counter starts at 0
- Each tick increments the counter by 1
- When the counter exceeds 10, it resets to 0
- The cycle continues indefinitely

## HOW TO USE IT

1. Click SETUP to initialize the counter at 0
2. Click GO to start incrementing the counter
3. Watch the COUNT monitor cycle from 0 to 10 and back

## THINGS TO NOTICE

- The counter resets automatically when it exceeds the threshold
- The TICKS monitor shows total simulation time
- The model runs continuously

## EXTENDING THE MODEL

- Add a slider to control the max_count threshold
- Create visual feedback on the view when counter resets
- Track how many times the counter has reset
- Add multiple counters with different rates

## CREDITS AND REFERENCES

Created as a minimal example for the xnLogo Python-to-NetLogo transpiler.
"""


# Entry point for running the model
if __name__ == "__main__":
    model = CounterModel()
    model.setup()
    print("Counter Model initialized!")
    print(f"Counter: {model.counter}")
