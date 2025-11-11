"""Test model with for and while loops."""

from xnlogo.runtime import Model, breed, reset_ticks, tick


class WalkerModel(Model):
    def __init__(self):
        super().__init__()
        self.walkers = breed("walkers", "walker")
        self.total_walkers = 0

    def setup(self):
        """Initialize walkers."""
        reset_ticks()
        self.total_walkers = 5
        
        for i in range(self.total_walkers):
            walker = self.walkers.create(1)
            walker.energy = 100
            walker.position = 0
            walker.steps_taken = 0
            # Use ternary operator (when supported)
            walker.color = 15 if walker.energy > 50 else 25

    def go(self):
        for walker in self.walkers.all():
            self.move_forward(walker)
            self.search_neighbors(walker)
        tick()

    def move_forward(self, walker):
        """Move using a for loop."""
        # Simple for loop with range
        for step in range(5):
            walker.position += 1
            walker.steps_taken += 1

    def search_neighbors(self, walker):
        """Search using while loop."""
        distance = 1
        found = False

        # While loop with condition
        while distance < 10 and not found:
            # Check if any neighbors at this distance
            neighbors = [1, 2, 3]  # Example list

            # Use in operator
            if walker.position in neighbors:
                found = True

            distance += 1

    def get_energy_level(self, walker):
        """Get energy as list index."""
        levels = [0, 25, 50, 75, 100]

        # List indexing
        index = 2
        target_energy = levels[index]

        return target_energy
