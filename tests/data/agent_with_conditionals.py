"""Test model with conditional logic."""

from xnlogo.runtime import Model, reset_ticks, tick


class SmartAgentModel(Model):
    def __init__(self):
        super().__init__()
        self.energy = 10.0
        self.x = 0.0
        self.max_energy = 20.0

    def setup(self):
        reset_ticks()
        self.energy = 10.0
        self.x = 0.0

    def go(self):
        self.consume_energy()
        self.check_alive()
        self.bound_energy()
        tick()

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
