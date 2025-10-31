"""Test agent with conditional logic."""

from xnlogo import agent


@agent
class SmartAgent:
    energy: float = 10.0
    x: float = 0.0
    max_energy: float = 20.0

    def consume_energy(self):
        self.energy = self.energy - 0.1

    def check_alive(self):
        if self.energy <= 0:
            self.x = -1
        else:
            self.x = 1

    def bound_energy(self):
        if self.energy > self.max_energy:
            self.energy = self.max_energy
