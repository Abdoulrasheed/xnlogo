"""Test model with multiple breeds."""

from xnlogo import agent


@agent(breed="sheep")
class Sheep:
    energy: float = 5.0
    wool: float = 0.0

    def graze(self):
        self.energy = self.energy + 0.5

    def grow_wool(self):
        if self.energy > 2:
            self.wool = self.wool + 0.1


@agent(breed="wolf")
class Wolf:
    energy: float = 10.0
    hunger: float = 0.0

    def hunt(self):
        self.hunger = self.hunger + 0.2

    def check_hunger(self):
        if self.hunger > 5:
            self.energy = self.energy - 1
