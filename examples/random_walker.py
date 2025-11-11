"""Random Walk Example - Agent-Based Model

A simple random walk simulation where a turtle wanders around the world,
bouncing off the edges. This demonstrates basic turtle movement and 
boundary checking.
"""

from xnlogo.runtime import (
    Model,
    breed,
    reset_ticks,
    tick,
    random_float,
    View,
    Button,
    Monitor,
)


class RandomWalkModel(Model):
    """A simple random walk model with one turtle."""

    def __init__(self):
        super().__init__()
        
        # Parameters
        self.step_size = 1.0
        self.max_coordinate = 16
        
        # Define walker breed
        self.walkers = breed("walkers", "walker")

    def setup(self):
        """Initialize the model."""
        reset_ticks()
        
        # Clear existing walkers
        for walker in self.walkers.all():
            walker.die()
        
        # Create one walker at center
        walker = self.walkers.create(1)
        walker.setxy(0, 0)
        walker.color = "red"
        walker.size = 2

    def go(self):
        """Run one step of the simulation."""
        for walker in self.walkers.all():
            self.walk(walker)
            self.bounce(walker)
        tick()

    def walk(self, walker):
        """Move the walker one step in a random direction."""
        # Random angle between 0 and 360
        angle = random_float(360)
        walker.set_heading(angle)
        walker.forward(self.step_size)

    def bounce(self, walker):
        """Bounce walker off edges by wrapping to opposite side."""
        # Get current position
        x = walker.xcor()
        y = walker.ycor()
        
        # Wrap x coordinate
        if x > self.max_coordinate:
            walker.setxy(-self.max_coordinate, y)
        if x < -self.max_coordinate:
            walker.setxy(self.max_coordinate, y)
        
        # Wrap y coordinate
        x = walker.xcor()  # Refresh x in case it was wrapped
        if y > self.max_coordinate:
            walker.setxy(x, -self.max_coordinate)
        if y < -self.max_coordinate:
            walker.setxy(x, self.max_coordinate)

    def widgets(self):
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
        
        # Monitor for walker count
        self.add_widget(
            Monitor(
                expression="count walkers",
                x=15,
                y=150,
                width=150,
                height=50,
                font_size=11,
                precision=0,
            )
        )
        
        # Monitor for tick count
        self.add_widget(
            Monitor(
                expression="ticks",
                x=175,
                y=150,
                width=150,
                height=50,
                font_size=11,
                precision=0,
            )
        )

    def info(self):
        """Return model information and documentation."""
        return """
## WHAT IS IT?

This is a simple random walk model where a single turtle (walker) moves randomly 
around the world. When it reaches the edge, it wraps around to the opposite side.

## HOW IT WORKS

At each time step:
1. The walker chooses a random heading (0-360 degrees)
2. Moves forward by a fixed step size
3. If it crosses a boundary, it wraps to the opposite edge

## HOW TO USE IT

1. Click SETUP to create a walker at the center
2. Click GO to start the random walk
3. Watch as the walker wanders around the world

## THINGS TO NOTICE

- The walker's path is completely random
- Over time, it explores most of the world
- The wrapping creates a toroidal (donut-shaped) world

## THINGS TO TRY

- Change the step_size parameter to make the walker move faster/slower
- Add more walkers to see multiple random walks
- Track the walker's position over time

## EXTENDING THE MODEL

- Add a pen-down feature to trace the walker's path
- Create multiple walkers with different colors
- Add obstacles that the walker must avoid
- Track statistics like distance traveled

## NETLOGO FEATURES

This model demonstrates:
- Basic turtle creation and movement
- Random number generation
- Boundary wrapping
- Simple agent-based modeling

## CREDITS AND REFERENCES

Created as an example for the xnLogo Python-to-NetLogo transpiler.
"""


# Entry point for running the model
if __name__ == "__main__":
    model = RandomWalkModel()
    model.setup()
    print("Random Walk Model initialized!")
    print(f"Walkers: {model.walkers.count()}")
