"""Test agent model with for and while loops."""

from xnlogo import agent


@agent(
    breed="walker",
    state=["energy", "position", "steps_taken"],
    globals=["total_walkers"],
)
class Walker:
    """Agent that uses loops for movement."""

    def setup(self):
        """Initialize walker."""
        self.energy = 100
        self.position = 0
        self.steps_taken = 0

        # Use ternary operator
        self.color = 15 if self.energy > 50 else 25

    def move_forward(self):
        """Move using a for loop."""
        # Simple for loop with range
        for step in range(5):
            self.position += 1
            self.steps_taken += 1

    def search_neighbors(self):
        """Search using while loop."""
        distance = 1
        found = False

        # While loop with condition
        while distance < 10 and not found:
            # Check if any neighbors at this distance
            neighbors = [1, 2, 3]  # Example list

            # Use in operator
            if self.position in neighbors:
                found = True

            distance += 1

    def get_energy_level(self):
        """Get energy as list index."""
        levels = [0, 25, 50, 75, 100]

        # List indexing
        index = 2
        target_energy = levels[index]

        return target_energy
