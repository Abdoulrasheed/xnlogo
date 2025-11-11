"""Test statements that might be valid in context but invalid when parsed alone."""

from xnlogo.runtime import Model, breed, reset_ticks, tick


class WalkerModel(Model):
    def __init__(self):
        super().__init__()
        self.walkers = breed("walkers", "walker")

    def setup(self):
        """Initialize walker."""
        reset_ticks()
        for i in range(5):
            walker = self.walkers.create(1)
            walker.position = 0

    def go(self):
        for walker in self.walkers.all():
            self.move(walker)
        tick()

    def move(self, walker):
        """Move forward."""
        # This is a complete valid statement
        walker.position += 1
